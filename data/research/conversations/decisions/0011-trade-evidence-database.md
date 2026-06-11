# 0011 Trade Evidence Database

## Background

项目需要总结交易，并记录各个周期及指标在进场、出场时的状态，逐步建立可复盘的策略大数据库。

当前 Strategy Lab 已有策略版本、回测结果和审计日志，但缺少交易级与事件级证据表。

## Decision

新增两层交易证据模型：

- `strategy_trades`：交易摘要，一笔交易一行。
- `strategy_trade_events`：交易事件证据，保存 entry/hold/exit 的多周期状态、指标快照和触发条件。

先在 `StrategyLabStorage` 内实现最小 DuckDB schema 和读写接口，不直接进入真实交易或完整大数据平台。

## Reason

这种设计能同时满足：

- 交易复盘：知道每笔交易为什么进、为什么出。
- 多周期状态分析：记录 MN1/W1/D1/H4/H1 等状态。
- 指标证据保存：记录 MA、ATR、volume_ratio、state_hex 等指标快照。
- 策略迭代：后续可统计哪些状态/条件组合更有效。
- 审计一致性：通过 `trace_id` 串联 DSL、红线、preview、backtest 和交易事件。

## Next Step

短期：

- 保持最小 schema 和测试通过。
- 让 Qoder 设计 Phase 2 Backtest 写入交易证据的接口契约。
- 让 Kimi 评估大规模 trade evidence 数据库的 DuckDB/Polars 分区、索引和聚合方案。

中期：

- 真实 Light Backtest 生成 `strategy_trades` 和 `strategy_trade_events`。
- 增加 strategy outcome aggregation。

## Non-Goals

- 不接真实账户。
- 不做真实下单。
- 不提供投资建议。
- 不承诺回测收益。
