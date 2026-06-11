# Kimi Next Task: Trade Evidence Database Performance And Aggregation Plan

你是 Hermass AI Quant Platform 的 Kimi Research Engineer。本轮任务是评估交易证据大数据库的规模、性能和聚合方案。

## 必读上下文

- `AGENTS.md`
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `data/research/conversations/decisions/0011-trade-evidence-database.md`
- `hermass_platform/strategy_lab/storage.py`
- `benchmarks/README.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-real-data-benchmark-runbook.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi2-data-refresh-replacement-audit.md`（如不存在，记录为 pending）

## 背景

我们要总结交易，记录进场/出场时的多周期状态和指标快照，逐步建立策略大数据库。

当前最小 schema 已落地，但大规模查询、JSON 展开、聚合和分区策略尚未设计。

## 任务

请评估交易证据库在 1 万、10 万、100 万、1000 万事件规模下的 DuckDB/Polars 方案，并输出可执行 benchmark 计划。

## 必须输出

1. 数据规模假设。
2. 写入吞吐要求。
3. 查询场景：
   - 按 strategy_id 查询交易。
   - 按 trace_id 查证据。
   - 按 MN1/W1/D1/H4/H1 state 聚合收益。
   - 按 condition_type 聚合胜率/盈亏比。
   - 按 indicator bucket 聚合表现。
4. JSON 字段保留 vs 展开宽表的取舍。
5. DuckDB 表设计、索引、物化视图建议。
6. Polars 离线聚合建议。
7. benchmark 脚本设计。
8. P50/P95 目标。
9. 数据授权和隐私风险。
10. Phase 2 / Phase 3 落地顺序。

## 输出文件

`data/research/conversations/agent-runs/2026-06-11-kimi-trade-evidence-database-performance.md`

## 不做什么

- 不下载真实数据。
- 不承诺性能，必须以 benchmark 为准。
- 不接真实交易账户。
- 不提供投资建议。
