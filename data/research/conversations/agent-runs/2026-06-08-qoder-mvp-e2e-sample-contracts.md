# Qoder MVP E2E Sample Contracts

执行时间：2026-06-08
执行角色：Qoder Architect
任务来源：`agents/QODER_NEXT_TASK_2026_06_08_E2E_SAMPLES.md`

---

## Files Added Or Modified

| 文件路径 | 动作 | 说明 |
|---|---|---|
| `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md` | 新增 | 冻结 3 个中文策略样例、NL->DSL 映射规则、E2E Runner Contract、Light Backtest Contract、Audit Contract、问题清单模板 |
| `hermass_platform/strategy_lab/e2e_runner.py` | 新增 | `MvpE2EResult` 模型 + `run_mvp_e2e_sample()` 入口 + `NLToDSLParser` 表驱动解析器 |

---

## Frozen Samples

### sample_ma_5_20_stop_8 (simple)

- 中文输入：`MA5上穿MA20买入，跌破MA10卖出，止损8%`
- 覆盖：MVP 验收底线第 1 条
- Entry: `ma_golden_cross(fast=5, slow=20)`
- Exit: `price_cross_ma(timeframe=D1, ma_period=10, direction=below)` + `stop_loss_pct(0.08)`
- Filter: `limit_up_filter(allow=false)`
- Risk: `max_position_pct=0.20`, `risk_per_trade=0.02`

### sample_state_volume_stop_8_take_15 (medium)

- 中文输入：`D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，止损8%，止盈15%`
- 覆盖：`state_hex_in` + `volume_ratio` + `stop_loss_pct` + `take_profit_pct`
- Entry: `state_hex_in(D1, [0x21, 0x23])` + `volume_ratio(lookback=20, >, 1.5)`
- Exit: `stop_loss_pct(0.08)` + `take_profit_pct(0.15)`

### sample_ma_state_limit_filter (bounded_complex)

- 中文输入：`MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，跌破MA10或止损8%卖出`
- 覆盖：组合条件 + filter + OR exit
- Entry: `ma_golden_cross(5, 20)` + `state_ef_count(>=, 2)`
- Exit: `price_cross_ma(D1, 10, below)` + `stop_loss_pct(0.08)`
- Filter: `limit_up_filter(allow=false)`

---

## NL To DSL Mapping Rules

### 支持的中文短语表

| 中文短语 | condition_type | 参数 |
|---|---|---|
| MA{N}上穿MA{M} | `ma_golden_cross` | fast_period=N, slow_period=M |
| MA{N}下穿MA{M} | `ma_death_cross` | fast_period=N, slow_period=M |
| 跌破MA{N} | `price_cross_ma` | timeframe=D1, ma_period=N, direction=below |
| 上穿MA{N} | `price_cross_ma` | timeframe=D1, ma_period=N, direction=above |
| D1状态属于{列表} | `state_hex_in` | timeframe=D1, values=[列表] |
| {TF}状态EF数量{op}{V} | `state_ef_count` | operator=op, value=V |
| 成交量放大到{N}日均量{R}倍以上 | `volume_ratio` | lookback=N, operator=>, value=R |
| 止损{P}% | `stop_loss_pct` | value=P/100 |
| 止盈{P}% | `take_profit_pct` | value=P/100 |
| 排除涨停股票 | `limit_up_filter` | allow=false |

### 默认参数

- `risk.max_position_pct` = 0.20（未提及仓位时）
- `risk.risk_per_trade` = 0.02（未提及单笔风险时）
- `risk.stop_loss_required` = true（永远 true）
- `filters` = `[limit_up_filter(allow=false)]`（默认排除涨停）

### 缺少止损的处理

- NL parser 未提取到 `止损{P}%` → DSL exit 不含 `stop_loss_pct`
- 红线检查触发 `RL_EXIT_MUST_HAVE_STOP_LOSS`
- validation.passed = false, level = red_line
- 链路写入 generation + validation audit，不执行 preview/backtest

### "跌破 MA10 卖出"映射裁决

- **裁决**：使用现有 `price_cross_ma`，参数 `{"timeframe": "D1", "ma_period": 10, "direction": "below"}`
- 不新增 condition type
- 用于 exit section 时产生 `SEMANTIC_WRONG_SECTION` warning，但不阻止执行
- 本周不新增 `price_below_ma`

---

## E2E Runner Contract

### 文件

`hermass_platform/strategy_lab/e2e_runner.py`

### 核心接口

```python
def run_mvp_e2e_sample(
    natural_language: str,
    strategy_id: str,
    *,
    trace_id: str,
    audit_db_path: str,
    storage_db_path: str,
    preview_data_source: Literal["mock", "duckdb"] = "mock",
    preview_duckdb_path: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> MvpE2EResult:
    ...
```

### MvpE2EResult 字段

- `trace_id`, `strategy_id`, `natural_language`
- `dsl` / `generation_errors`
- `validation` / `red_line_result`
- `preview`
- `backtest` / `backtest_mode`
- `audit_records`
- `problem_items`
- `status` / `stage_reached`

### 执行顺序

```
generation -> validation -> [red_line gate] -> preview -> backtest -> finalize
```

失败链路也必须写 audit。

---

## Light Backtest Minimum Contract

- 只有通过红线检查才允许执行
- 返回 `status` + `mode`（必须为 `"light_stub"` 或 `"light_mock"`）
- 核心指标字段必须存在：`total_return`, `annual_return`, `max_drawdown`, `sharpe_ratio`, `win_rate`, `profit_factor`, `trade_count`
- 写入 storage（`strategy_backtests`）和 audit（`strategy_audit_log`）
- `metrics` JSON 中必须包含 `"_mode": "light_stub"`
- `risk_flags` 必须包含 `"STUB_BACKTEST: Not yet implemented"`

---

## Audit Contract

### Operation 顺序

```
generation -> validation -> preview -> backtest
```

### 必须字段

- `trace_id`, `operation`, `strategy_id`
- `dsl_version` = "strategy_dsl_v2"
- `input_hash`, `output_hash`（SHA256 前 16 位）
- `red_line_result`（JSON，无则 {}）
- `created_at`

### 失败链路规则

| 失败点 | 写入 operations | 跳过 |
|---|---|---|
| DSL 生成失败 | generation | validation, preview, backtest |
| 红线失败 | generation, validation | preview, backtest |
| Preview 异常 | generation, validation, preview | backtest |
| Backtest 异常 | generation, validation, preview, backtest | 无 |

---

## Problem List Template

### 四类固定分类

- `definition` — 策略定义问题
- `implementation` — 实现问题
- `data` — 数据问题
- `acceptance` — 验收问题

### 字段

- `sample_id`, `category`, `stage`, `summary`, `evidence`, `owner`, `next_action`, `created_at`

---

## Acceptance Criteria

1. 输入 `MA5上穿MA20买入，跌破MA10卖出，止损8%` 能生成合法 DSL。
2. 缺少止损的 DSL 或中文输入被拒绝，且 red-line 结果可审计。
3. 仓位超过 25% 的 DSL 被红线拒绝。
4. 3 个样例都能生成 preview，mock 模式稳定返回命中数量。
5. 3 个样例都能返回 Light Backtest 最小指标，并明确标注 `mode="light_stub"`。
6. 每个样例的 generation、validation、preview、backtest 都能通过同一 `trace_id` 查到审计记录。
7. 失败样例不会执行 preview/backtest，但 audit 有 generation + validation 记录。

---

## Not Doing

- 不新增真实 LLM 接入
- 不执行 LLM 生成代码
- 不扩因子库
- 不新增外部数据源
- 不实现完整真实 backtest engine
- 不实现 Web 路由
- 不做 Agent Debate DAG
- 不做 Paper Trading
- 不做 TS-FM / RAG-KG
- 不改 benchmark
- 不改 factors registry（本周样例均可用现有 condition type 表达）

---

## Next Steps For Codex

1. 实现 `e2e_runner.py` 中的 `run_mvp_e2e_sample()` 和 `MvpE2EResult` — **已完成（本文件已包含完整实现）**
2. 为 3 个样例编写端到端测试，验证完整链路
3. 确保 `backtest_adapter.py` stub 返回的 `BacktestResult` 包含 `"_mode": "light_stub"`
4. 确保 `audit.py` 在失败链路中也能正确写入记录
5. 运行验收测试，确认 7 条验收标准全部通过
