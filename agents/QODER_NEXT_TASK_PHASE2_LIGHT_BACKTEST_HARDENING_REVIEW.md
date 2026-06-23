# Qoder Next Task: Phase 2 Light Backtest Hardening Review

你是 Hermass AI Quant Platform 的 Qoder Architect。本轮任务不是继续扩展架构，也不是实现代码，而是审阅 Phase 2 Light Backtest 第一版实现与原 contract 的偏差，并把下一轮 Codex hardening 工作压缩成可执行任务。

## 必读上下文

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md` 中 C17 / C18
- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-light-backtest-implementation-review.md`
- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/backtest_data_provider.py`
- `hermass_platform/strategy_lab/light_backtest_engine.py`
- `hermass_platform/strategy_lab/backtest_metrics.py`
- `hermass_platform/strategy_lab/backtest_evidence.py`
- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`

## 总结论

当前实现可以作为 `light_real_v1` 的 synthetic smoke baseline，但不能发布为 Phase 2 real baseline。

可采纳的部分：

- `BacktestAdapter.run_backtest()` 已在 facade 入口重新执行 `validate_dsl()`，红线失败时不进入 provider/engine。
- `DuckDBBacktestDataProvider` 已从 `SELECT *` 收敛到基于 schema discovery 的白名单列选择。
- Synthetic fixture 下已能返回非 stub 的 `light_real_v1` 结果。
- E2E response 已对 `daily_curve` 和 `trades` 做 100 条截断，避免 synthetic 响应无限增长。

阻塞 real baseline 的部分：

- real 模式下 trade/event evidence 不能可靠落库：adapter 返回的 `BacktestResult` 没有暴露 `signal_frame`，但 `e2e_runner._persist_trades_and_events()` 依赖 `bt_result.signal_frame`。
- engine 交易执行仍是 `df.to_dicts()` 后 Python row loop，且输入排序是 `symbol,date`，会破坏多 symbol 的日期级组合权益、现金约束和 daily return 语义。
- 如果传入的 `foundation_db` 路径不存在，adapter 会静默降级为 `light_stub`，不应出现在 real baseline。
- `volume_ratio` contract 是 `volume_ratio OR volume_ma_{lookback}`，当前 provider/registry 请求链路更偏向 `volume_ma_{lookback}`，存在有 `volume_ratio` 但无 `volume_ma_N` 时失败或误判的风险。
- 真实 DB baseline 与 Kimi hot path gate 尚未运行。

## 偏差审计清单

| 主题 | 当前实现 | 原 contract 要求 | 判定 | 下一步 |
|---|---|---|---|---|
| adapter 入口红线 | `BacktestAdapter.run_backtest()` 调用 `validate_dsl()`，失败返回 `status="failed"`，不读 DuckDB | backtest 内部必须重新 validation/red-line，红线失败不读 DuckDB、不运行 engine、不写 trades | synthetic MVP 可接受 | 保留。补 direct adapter 测试，确保 provider 不被调用 |
| real/stub 模式边界 | `foundation_db is None` 或路径不存在都会回落 `light_stub` | `light_stub` 不得伪装真实绩效；real 输入缺数据应 failed | real baseline blocker | 传入非空 `foundation_db` 但不存在时返回 `mode="light_real_v1"`, `status="failed"`, `BT_DATA_DB_NOT_FOUND` |
| provider 列裁剪 | 已按 base columns、optional risk columns、DSL required columns、state aliases 选择列；表名固定 | DuckDB 按日期、universe、required_columns 做列裁剪，不拼接用户表名/列名 | synthetic MVP 可接受 | 加 query/column assertions，防止 `SELECT *` 回归 |
| provider `volume_ratio` | registry 声明 `volume_ma_{lookback}`；provider 不保证 `volume_ratio` 作为等价替代 | 优先 `volume_ratio`，否则用 `volume_ma_{lookback}`，两者都无才 failed | real baseline blocker | 明确 required-column alternate group：`volume_ratio OR volume_ma_N` |
| state alias | `state_hex_d1/w1/mn1` 会归一为 `d1_state/w1_state/mn1_state` | provider 负责 `state_hex_*` 与 normalized state key 归一 | acceptable | 保留并加 state filter integration assertion |
| engine Python row loop | signal 是 Polars，`_generate_trades()` 使用 `df.to_dicts()` 逐行处理 | Phase 2 hot path 必须避免 Python 逐行循环 | acceptable for synthetic MVP, blocker for real hot path | 先改成按交易日 batch 的确定性执行；性能向量化进入 real baseline backlog |
| engine 执行排序 | `build_signal_frame()` 和 provider 都按 `symbol,date` 排序，trade loop 逐 symbol 跑完整区间 | 同日多个 symbol 按 symbol 升序处理；组合权益必须按日期推进 | real baseline blocker | 改为 `date,symbol` 执行；daily curve 一天一个点 |
| trade/evidence 落库 | E2E 尝试用 `bt_result.signal_frame` 构造 evidence，但 adapter result 没有该字段；fallback 只能写 trade record，不能写 event evidence | `strategy_trades` 和 `strategy_trade_events` 必须按 trace 写入并可查询 | real baseline blocker | adapter 暴露 execution artifacts 或 evidence builder 改吃 trades+frame；新增 real E2E persistence test |
| evidence builder | 单测使用人工 frame；真实 engine frame 的 entry/exit row 字段可能不足，closed trade 可能被 dedupe 成 open | 每笔 entry/exit/stop/take/hold 都要有事件证据 | real baseline blocker | 用真实 engine frame 写 evidence regression tests，再修字段传递 |
| API response 大小 | E2E 对 `daily_curve`/`trades` 截断到 100；无 `truncated` / `total_count` / `trades_path` | Web API 可返回摘要，完整记录以 storage 为准 | acceptable for synthetic MVP, real backlog | 增加 truncation metadata 和 storage reference |
| 同日冲突 | 同一 row 内先 exit 再 entry，`exited_today` 阻止同日重入 | 已持仓先 exit，刚 exit 同日不再 entry | partially acceptable | 加 date-batched same-day fixture；多 symbol 排序修复后重测 |
| 停牌 | `is_suspended` 阻止 entry/exit；持仓仍按 close 更新市值 | 停牌不允许买卖；close 缺失时 forward-fill 前收并 warning | real backlog | 增加 close 缺失 fixture、forward-fill/warning |
| 跌停 | `is_limit_down` 会阻止卖出，但 `blocked_exit_reason` 未进入 completed frame/evidence，未写 hold event/warning | 跌停阻塞 exit 时记录 blocked reason，仓位延续，可写 hold event | real baseline backlog, pilot blocker | 保留仓位延续；补 `blocked_exit_reason` 列、warning、hold evidence |
| 成本模型 | commission、stamp duty、slippage、min commission 已实现；buy/sell fill price也调整 slippage | A 股默认成本模型，费用拆分进入 metrics/evidence | acceptable for synthetic MVP | 加 golden tests；明确 slippage 是否同时进 fill price 和 cost_total |
| unsupported timeframe | `price_cross_ma` 非 D1 返回 false | Phase 2 Light 非 D1 应 failed，建议 `BT_UNSUPPORTED_TIMEFRAME` | real backlog | 在 adapter/engine 前置检查 unsupported timeframe |
| metrics | core metrics 已有；daily equity 依赖 row loop 输出 | 指标基于日期级 equity curve 和 closed trades | synthetic only | 日期级执行修复后重算 metrics golden case |
| audit/storage | E2E 写 backtest audit 和 `strategy_backtests`；adapter direct 不写 audit/storage | service/API 直接调用时也要 validation/backtest audit | real backlog | 收敛到 service boundary；adapter 保持纯 facade |

## 分类裁决

### Blocker for Phase 2 real baseline

- real 模式缺 DB 时静默降级为 `light_stub`。
- 多 symbol 日期级执行顺序错误，导致现金、组合权益、daily return 不可信。
- trade/event evidence 不能从 adapter/E2E real path 可靠落库。
- `volume_ratio` 的等价列契约未闭合。
- 真实 DB baseline 和 benchmark smoke 未运行。

### Acceptable for synthetic MVP

- 交易生成使用 Python row loop，只要结果明确标注为 synthetic smoke，不声称真实性能。
- API response 只做 100 条截断，暂不返回完整分页元数据。
- `light_stub` 继续作为无 DB 的 Phase 0/1 compatibility path。
- 成本模型按当前默认参数运行，但暂不对外宣称精确撮合。
- 停牌/跌停只覆盖最小 tradability 行为，不作为 synthetic release gate。

### Phase 2 real baseline backlog

- 按 `date,symbol` batch 执行，后续再向 Polars/vectorized hot path 收敛。
- `run_light_backtest_service()` / `get_backtest_service()` service boundary。
- API response metadata：`daily_curve_total_count`、`trades_total_count`、`daily_curve_truncated`、`trades_truncated`、`trades_path` 或 storage reference。
- `strategy_trade_events` 按 `trace_id` 查询。
- unsupported timeframe 明确 failed。
- limit-down blocked exit 的 hold evidence。
- suspended day close 缺失 forward-fill 与 warning。
- real DB data quality gate 和 hot path benchmark。

## Codex 下一步实现/修复任务

### Task A: real mode 不得静默降级为 stub

文件：

- `hermass_platform/strategy_lab/backtest_adapter.py`

接口：

- `BacktestAdapter.run_backtest(config: BacktestConfig) -> BacktestResult`
- `run_dsl_backtest(..., foundation_db: Path | None, ...) -> BacktestResult`

要求：

- `foundation_db is None`：保持 `light_stub` compatibility。
- `foundation_db is not None and not exists`：返回 `mode="light_real_v1"`、`status="failed"`、`risk_flags` 包含 `BT_DATA_DB_NOT_FOUND`，不得返回 `STUB_BACKTEST`。
- validation/red-line 失败仍优先于 provider/engine。

测试名：

- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py::TestRealLightBacktestIntegration::test_missing_real_db_does_not_fallback_to_stub`
- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py::TestRealLightBacktestIntegration::test_red_line_blocks_provider_load`

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py -q
```

### Task B: 暴露 real execution artifact 并打通 trade/event evidence 落库

文件：

- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/backtest_models.py`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `hermass_platform/strategy_lab/backtest_evidence.py`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/tests/test_backtest_evidence.py`
- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`

接口：

- `BacktestResult.signal_frame: pl.DataFrame | None = None` 或等价 internal artifact 字段。
- `build_trade_records(signal_frame: pl.DataFrame, dsl: StrategyDSL, trace_id: str) -> list[dict[str, Any]]`
- `build_trade_event_evidence(signal_frame: pl.DataFrame, dsl: StrategyDSL, trace_id: str) -> list[dict[str, Any]]`
- `StrategyLabStorage.list_trade_events(trade_id: str | None = None, trace_id: str | None = None) -> list[TradeEventEvidence]`

要求：

- E2E real mode 有 closed trade 时，至少写入一条 `strategy_trades` 和 entry/exit event evidence。
- stop loss 写 `event_type="stop_loss"`，take profit 写 `event_type="take_profit"`。
- blocked limit-down exit 写 `event_type="hold"` 或明确 warning。
- `_persist_trades_and_events()` 不得吞掉所有异常；测试环境下 persistence failure 必须失败。

测试名：

- `test_e2e_real_mode_persists_trade_records_and_events`
- `test_trade_events_can_be_listed_by_trace_id`
- `test_closed_trade_from_engine_frame_is_not_misclassified_as_open`
- `test_limit_down_blocked_exit_writes_hold_event`

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest \
  hermass_platform/strategy_lab/tests/test_backtest_evidence.py \
  hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py -q
```

### Task C: 修正多 symbol 日期级执行语义

文件：

- `hermass_platform/strategy_lab/light_backtest_engine.py`
- `hermass_platform/strategy_lab/tests/test_light_backtest_engine.py`
- `hermass_platform/strategy_lab/tests/test_backtest_metrics.py`

接口：

- `LightBacktestEngine._generate_trades(df: pl.DataFrame, dsl: StrategyDSL, config: BacktestConfig) -> tuple[pl.DataFrame, list[TradeSummary]]`
- `LightBacktestEngine._compute_equity(df: pl.DataFrame, initial_capital: float) -> pl.DataFrame`

要求：

- trade execution order is `date ASC, symbol ASC`。
- 每个交易日先处理当天全部 exit，再处理当天 entry，或明确保持 contract 的 same-symbol exit-before-entry 且保证组合现金正确。
- `daily_curve` 每个 date 仅一条，`daily_return` 是 date-level return。
- `target_notional = previous_day_portfolio_value * max_position_pct`。
- 资金不足跳过入场并记录 `BT_INSUFFICIENT_CASH_SKIP` warning。

测试名：

- `test_multi_symbol_execution_is_date_then_symbol`
- `test_daily_curve_has_one_point_per_date`
- `test_same_day_exit_then_no_reentry_same_symbol`
- `test_insufficient_cash_skip_records_warning`

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_light_backtest_engine.py hermass_platform/strategy_lab/tests/test_backtest_metrics.py -q
```

### Task D: provider 补齐 `volume_ratio OR volume_ma_N` 契约

文件：

- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/backtest_data_provider.py`
- `hermass_platform/strategy_lab/tests/test_backtest_data_provider.py`
- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`

接口：

- `MarketDataRequest.required_columns: list[str]`
- `DuckDBBacktestDataProvider.load(request: MarketDataRequest) -> MarketDataBundle`

要求：

- `volume_ratio` condition 优先使用 `volume_ratio`。
- 若无 `volume_ratio` 但有 `volume_ma_{lookback}`，engine 可计算 ratio。
- 两者都缺失时 failed，错误包含 `BT_MISSING_REQUIRED_COLUMN`。
- 不为了 volume condition 运行时补算任意 `volume_ma_N`。

测试名：

- `test_volume_ratio_column_satisfies_volume_condition_without_volume_ma`
- `test_volume_ma_fallback_satisfies_volume_condition`
- `test_missing_volume_ratio_and_volume_ma_fails`

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_backtest_data_provider.py -q
```

### Task E: API response 摘要与 storage reference

文件：

- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `hermass_platform/strategy_lab/tests/test_api_models.py`
- `hermass_platform/strategy_lab/tests/test_e2e_runner.py`

接口：

- `BacktestResponse`

建议新增字段：

```python
daily_curve_total_count: int | None = None
trades_total_count: int | None = None
daily_curve_truncated: bool = False
trades_truncated: bool = False
trades_path: str | None = None
```

要求：

- Web/E2E response 仍只返回摘要。
- 完整 trades/events 以 storage 为准。
- 截断时 response 明确告诉调用方。

测试名：

- `test_backtest_response_reports_truncation_metadata`
- `test_e2e_backtest_response_caps_daily_curve_and_trades`

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_api_models.py hermass_platform/strategy_lab/tests/test_e2e_runner.py -q
```

### Task F: tradability hardening

文件：

- `hermass_platform/strategy_lab/light_backtest_engine.py`
- `hermass_platform/strategy_lab/backtest_evidence.py`
- `hermass_platform/strategy_lab/tests/test_light_backtest_engine.py`
- `hermass_platform/strategy_lab/tests/test_backtest_evidence.py`

接口：

- `LightBacktestOutput.warnings`
- completed signal frame columns: `blocked_exit_reason`, `is_suspended`, `is_limit_down`

要求：

- suspended day 不允许买卖；close 缺失时 forward-fill 并 warning。
- limit-down 阻止卖出，仓位延续，写 `blocked_exit_reason`。
- blocked exit 至少出现在 warnings；real evidence path 写 hold event。

测试名：

- `test_suspended_missing_close_forward_fills_with_warning`
- `test_limit_down_blocks_exit_and_keeps_position`
- `test_blocked_exit_reason_survives_completed_frame`

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_light_backtest_engine.py hermass_platform/strategy_lab/tests/test_backtest_evidence.py -q
```

### Task G: real baseline smoke gate

文件：

- `benchmarks/validate_real_data.py`
- `benchmarks/light_backtest_perf.py`
- `data/research/conversations/agent-runs/`

要求：

- 若 `data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 存在，先跑数据验证，再跑 synthetic benchmark smoke。
- 若真实 DB 不存在，记录 blocked reason，不伪造 real baseline。

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/validation.json
```

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py \
  --synthetic --symbols 500 --days 252 --runs 2 \
  --output outputs/benchmarks/light_backtest_phase2_smoke.jsonl
```

## 最小测试矩阵

### Unit

- `test_backtest_data_provider.py`
  - no `SELECT *` regression guard。
  - state aliases: `state_hex_d1 -> d1_state`。
  - `volume_ratio OR volume_ma_N`。
  - missing `is_limit_up` fails when `limit_up_filter` is used。
- `test_light_backtest_engine.py`
  - MA golden/death cross。
  - price cross MA D1 only。
  - stop loss/take profit priority。
  - same-day conflict。
  - date-batched multi-symbol cash/equity。
  - suspended and limit-down tradability。
  - 100-share lot rounding。
  - cost model golden values。
- `test_backtest_evidence.py`
  - closed/open trade records from real completed frame。
  - entry/exit/stop_loss/take_profit/hold event mapping。
  - indicator snapshot and timeframe states。
- `test_backtest_metrics.py`
  - date-level equity curve metrics。
  - turnover/cost_total。

### Integration

- `test_real_light_backtest_integration.py`
  - synthetic DuckDB fixture with at least 2 symbols and 30 days。
  - real `BacktestAdapter` path returns `mode="light_real_v1"`。
  - red-line failures do not read provider and do not write trades。
  - E2E real path writes `strategy_backtests` with `_mode="light_real_v1"`。
  - `strategy_trades` and `strategy_trade_events` can be queried by `trace_id`。

### E2E

- `scripts/run_strategy_lab_mvp_e2e_acceptance.py`
  - existing Phase 0/1 stub acceptance remains green。
- Add real fixture E2E case:
  - `中文策略输入 -> DSL -> validate -> preview -> light_real_v1 -> storage/audit`。
  - response is capped but storage has full records。

### Benchmark smoke

- Synthetic:
  - `benchmarks/light_backtest_perf.py --synthetic --symbols 500 --days 252 --runs 2`
  - output JSONL exists and includes elapsed seconds, rows, symbols, days, mode。
- Real data:
  - only after DB exists。
  - `benchmarks/validate_real_data.py` passes P0 data contract before any real performance claim。

## Release gate 判定

### `light_real_v1` synthetic release

判定：YES, internal synthetic only。

条件：

- 必须清晰标注 synthetic fixture/smoke，不对外宣称真实收益或真实性能。
- `light_stub` compatibility path 仍通过。
- `BacktestAdapter` red-line gate 保持有效。
- provider 不回归 `SELECT *`。
- 运行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py benchmarks/*.py
```

### `light_real_v1` real baseline release

判定：NO。

必须满足后才能改为 YES：

- 真实 DB 存在且 `validate_real_data.py` 通过。
- real mode 缺 DB 不再静默 fallback 到 stub。
- 多 symbol 日期级执行语义修复。
- `strategy_trades` 和 `strategy_trade_events` 从 E2E real path 自动写入并可按 `trace_id` 查询。
- provider 的 state/volume/tradability required columns 契约闭合。
- synthetic benchmark smoke 通过，且未把 row-loop 实现冒充 hot path gate。

### pilot / public beta

判定：NO。

pilot 条件：

- real baseline release 已 YES。
- 数据新鲜度、覆盖率、授权、缺失率、停牌/涨跌停字段质量都有审计报告。
- API response 有分页/截断元数据，完整 evidence 可追溯。
- 每次 backtest 有 trace_id、dsl_version、input_hash、output_hash、red_line_result。
- 用户界面或 API 明示结果不是投资建议。

public beta 条件：

- pilot 稳定运行后再评估。
- hot path gate 达标，真实数据 baseline 可重复。
- storage/audit 可做回放和问题追踪。
- GitHub/demo 不包含误导性真实收益宣传。

## 明确不做什么

- 不扩展 Agent Debate。
- 不做 Paper Trading。
- 不做分钟线。
- 不做 walk-forward。
- 不做真实下单或券商接口。
- 不做 LLM 生成或执行 Python 策略代码。
- 不做 short、融资融券、T+0。
- 不用 synthetic benchmark 代替真实性能承诺。
- 不为了预留接口阻塞当前确定性链路。
