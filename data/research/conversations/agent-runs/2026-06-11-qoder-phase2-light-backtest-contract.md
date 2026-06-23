# 2026-06-11 Qoder Phase 2 Light Backtest Contract

## 背景

本轮以 Qoder Architect 身份推进 Phase 2 Real Light Backtest。当前 MVP acceptance 已通过，但 `hermass_platform/strategy_lab/backtest_adapter.py` 仍返回 `light_stub`，只证明链路、审计和落库可运行，不能作为真实回测绩效。

已阅读：

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md` Strategy Lab / Light Backtest / API 相关部分
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `data/research/conversations/decisions/0011-trade-evidence-database.md`
- `benchmarks/validate_real_data.py`
- `benchmarks/light_backtest_perf.py`
- Strategy Lab 当前代码和测试。

## 决策

新增任务规格：

- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md`

核心 contract：

- `backtest_adapter.py` 保留为 facade，不承载 provider/engine 全部实现。
- 新增 `backtest_models.py`、`backtest_data_provider.py`、`light_backtest_engine.py`、`backtest_metrics.py`，可选 `backtest_evidence.py`。
- DuckDB 只负责列裁剪、日期/universe 过滤、state join 和数据归一。
- Polars 负责信号、持仓、交易、权益曲线、指标和 evidence frame。
- Phase 2 只做 long-only daily-bar `light_real_v1`。
- Backtest 必须重新执行 `validate_dsl()`；红线失败时不得读 DuckDB、不得生成 trades。
- 复用 `StrategyLabStorage` 已有 `strategy_backtests`、`strategy_trades`、`strategy_trade_events`。
- `strategy_backtests.metrics` 写 `_mode="light_real_v1"`，避免与 `light_stub` 混淆。

## 理由

`storage.py` 已经具备交易摘要和事件证据表，没必要为 Phase 2 做大规模 DDL。把 provider、engine、metrics 拆开，可以让每层单测更直接：

- provider 测缺列、取数、列名归一。
- engine 测交易语义和冲突规则。
- metrics 测指标口径。
- evidence 测 trade/event JSON contract。

这种拆分也符合当前项目原则：先交付确定性链路，再考虑 Agent 包装。

## 关键语义

覆盖的 P0/P1 条件语义：

- `ma_golden_cross`: `ma_fast[t] > ma_slow[t]` 且前一日未上穿。
- `price_cross_ma`: D1 close 上穿/下穿 MA，可用于 entry 或 exit。
- `stop_loss_pct`: 持仓后 close 跌破 `entry_price * (1 - value)`。
- `take_profit_pct`: 持仓后 close 达到 `entry_price * (1 + value)`。
- `state_hex_in`: MN1/W1/D1 state in values。
- `volume_ratio`: 优先使用预计算 `volume_ratio`，否则使用 `volume_ma_{lookback}`，不动态补算。
- `limit_up_filter`: `allow=false` 时排除涨停入场。

交易规则：

- long-only。
- close 成交，费用模型沿用 `CostModel`。
- 每个 symbol 同时最多一笔仓位。
- 100 股 lot rounding。
- 同日多个 exit：stop loss > take profit > price cross MA > MA death cross。
- 已持仓时同日先 exit，且 exit 后同日不再 entry。
- 停牌不交易，跌停阻塞卖出，涨停 filter 阻止买入。

## 审计与落库

正常 E2E 顺序仍为：

1. `generation`
2. `validation`
3. `preview`
4. `backtest`

直接 backtest API 调用时至少写：

1. `validation`
2. `backtest`

Backtest storage 要求：

- 每次完成或失败都写 `strategy_backtests`。
- 真实 light 写 `_mode="light_real_v1"`。
- 每笔交易写 `strategy_trades`。
- 每个 entry/exit/stop/take/blocked hold 写 `strategy_trade_events`。

## 下一步

建议实现顺序：

1. 新增 backtest contract models 和 synthetic integration fixture。
2. 实现 DuckDB provider。
3. 实现 Polars signal frame。
4. 实现 position/trade/equity/metrics。
5. 接入 storage trades/events。
6. 接入 audit 和 E2E runner real mode。
7. 跑 `hermass_platform/strategy_lab/tests` 全量测试。

## 不做

- 不做 Agent Debate。
- 不做 Paper Trading。
- 不做真实下单。
- 不做 LLM 策略代码执行。
- 不做 full backtest、walk-forward、HTML tearsheet。
- 不做分钟线或盘中路径推断。
- 不把 synthetic benchmark 当真实性能承诺。
