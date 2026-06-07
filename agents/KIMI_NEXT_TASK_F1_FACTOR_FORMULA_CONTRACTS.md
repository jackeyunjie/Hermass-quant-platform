# Kimi Next Task: F1 Factor Formula And Data Contracts

你是 Hermass 项目的 Research Engineer。本轮任务不再扩大候选库，而是把 F1 MVP+ 的 26 个 factor 和 4 个 block 转成可实现的数据/公式契约。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-factor-catalog-curation.md`
- `agents/SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`
- `data/research/conversations/decisions/0009-factor-catalog-registry-accepted.md`
- `docs/FACTOR_BLOCK_LIBRARY_DESIGN_PRINCIPLES.md`
- `docs/FACTOR_SOURCE_TAXONOMY.md`

## 目标

把 F1 的 30 个 MVP+ 条目转成 Codex 可实现的 formula/data contracts。

必须覆盖：

- 26 个 Factor Registry 条目。
- 4 个 Block Registry 条目。
- 2 个需要额外 DSL 设计的 F1 block 给出接口建议，但不要求完整实现。

## 输出文件

写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-f1-factor-formula-contracts.md`

## 输出结构

### 1. Canonical Field Mapping

列出每张表的字段契约：

- `daily_bars`
- `moneyflow_daily`
- `state_cube`
- `index_daily`
- `industry`
- `account_context`
- `position_context`
- `backtest_output`

每个字段给出：

- canonical column name。
- 数据类型。
- 是否可为空。
- 单位。
- 是否允许未来数据。
- 来源说明。

### 2. F1 Factor Formula Contracts

对 26 个 factor 逐个给出：

- `factor_id`
- `display_name`
- `input_tables`
- `input_columns`
- `output_column`
- `output_dtype`
- `window`
- `formula_plain_text`
- `polars_expr_hint`
- `duckdb_expr_hint`
- `precompute_recommended`
- `preview_supported`
- `future_leakage_check`
- `edge_cases`
- `acceptance_examples`

必须包含这 26 个：

```text
rsi_14, macd_hist, adx_14, atr_14, supertrend, bb_position, bb_bandwidth,
roc_10, volume_ratio, turnover_rate,
return_5d_rank, return_20d_rank, industry_rs_rank, volatility_20d_pct, beta_to_index,
main_force_net_inflow, large_order_net_inflow, active_buy_sell_ratio, money_flow_intensity, amihud_illiquidity,
d1_state, w1_state, mn1_state, multi_timeframe_resonance
```

如果发现数量不是 26，必须显式指出原因。

### 3. F1 Block Contracts

对 4 个 block 给出：

- `block_id`
- `block_type`
- `context_requirements`
- `required_inputs`
- `parameters`
- `preview_support`
- `backtest_semantics`
- `risk_notes`

必须包含：

- `stop_loss_pct`
- `take_profit_pct`
- `atr_trailing_stop`
- `position_size_red_line`

### 4. Extra DSL Design Notes

给出以下两个 block 的接口建议：

- `factor_threshold_signal`
- `robustness_parameter_jitter`

要求说明：

- 为什么暂不直接实现。
- 需要新增哪些 DSL 参数类型。
- 最小可用接口长什么样。

### 5. Precompute Priority

把 F1 factors 分为：

- P0 必须预计算。
- P1 建议预计算。
- P2 可按需计算。

说明原因：计算成本、使用频率、是否跨截面、是否依赖外部表。

### 6. Data Quality Gates

为每个表给出最小质量门槛：

- 缺失率。
- 日期连续性。
- 股票池覆盖率。
- 停牌/涨跌停处理。
- 复权价格要求。

## 验收标准

- 26 个 factor 都有公式契约。
- 4 个 block 都有执行语义。
- 每个 factor 至少有 Polars expression hint。
- 明确哪些 factor 需要预计算。
- 明确哪些公式不得使用未来数据。
- 不实现代码。

## 禁止事项

- 不要新增 F1 之外的新 factor。
- 不要把基本面因子提前解锁。
- 不要把 `future_leakage_risk=high` 的内容写成可生产。
- 不要复制 StrategyQuant 源码。
