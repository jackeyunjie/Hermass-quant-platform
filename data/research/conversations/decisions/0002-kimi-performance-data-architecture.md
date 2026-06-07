# 0002 Kimi Performance And Data Architecture

## 背景

Kimi Research Engineer 已按 `agents/KIMI_RESEARCH_ENGINEER_PROMPT.md` 完成优先问题研究，记录在 `data/research/conversations/agent-runs/2026-06-06-kimi-research-engineer-priority-questions.md`。

需要把研究结论转成项目决策，避免后续实现时重新争论 DuckDB/Polars 分工、预计算指标和 State Cube 查询规范。

## 决策

Phase 2 回测引擎默认采用：

- DuckDB：数据加载、列裁剪、预计算指标读取、可选 `filter_first` 预过滤。
- Polars：信号生成、权益曲线、持仓模拟、绩效指标。
- StrategyLab.duckdb：报告、交易明细、指标与 trace 落库。

Foundation DB MVP 需要优先支持这些预计算列：

- `ma_5`
- `ma_10`
- `ma_20`
- `ma_60`
- `bb_position`
- `atr_14`
- `volume_ratio`
- `adx_14`
- `d1_state`
- `w1_state`
- `mn1_state`

State Cube 查询进入 MVP 规范：

- 禁止 `SELECT *`。
- 必须列裁剪。
- 对 `date` 和 `symbol` 建索引。
- 最近 5 个交易日状态允许 LRU 内存缓存。

产业链 Agent 最小版放入 Phase 3：

- 静态 JSON 行业链映射。
- State Cube 聚合评分。
- Kuzu KG、LLM 动态抽取、因果推理进入 research backlog。

## 理由

该分工兼顾性能和可维护性。DuckDB 适合数据湖查询与窗口指标，Polars 适合复杂条件组合、分组向量计算和权益曲线。完整 KG 和 TS-FM 目前会分散 MVP 资源，应隔离到 research sandbox。

## 风险

- `<30s` 只是研究判断，仍需真实 benchmark 验证。
- 如果热路径出现 Python row loop，性能目标会失效。
- Foundation DB 若缺少预计算列，Phase 2 会被迫运行时计算，影响验收。

## 下一步

1. Codex 更新任务分配，把 Kimi 结论转成 Phase 2 工程约束。
2. Qoder 在 DSL 条件注册表中声明字段依赖。
3. Kimi 补充可运行 benchmark 脚本并输出 JSONL。
4. Codex 在 Phase 2 实现时强制热路径不使用 Python 逐行循环。
