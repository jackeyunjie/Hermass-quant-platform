# Kimi Next Task: Factor Catalog Curation

你是 Hermass 项目的 Research Engineer。本轮任务不是继续扩大候选数量，而是把已经收集的 278 条 factor/block 候选压缩成可执行的 F0/F1/F2 因子与 Block 目录草案。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `docs/FACTOR_SOURCE_TAXONOMY.md`
- `docs/FACTOR_BLOCK_LIBRARY_DESIGN_PRINCIPLES.md`
- `data/research/conversations/decisions/0008-broad-factor-source-evidence-governance.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-broad-factor-source-research.md`
- `agents/FACTOR_SOURCE_SCHEMA.md`

## 目标

把广义候选库整理成三层：

- F0: Source Catalog，先把来源治理清楚。
- F1: MVP+ Catalog，优先进入代码注册表和 DSL/Preview 的 30 个 factor/block。
- F2: Candidate Catalog，下一批 70 个可研究/可实现候选。

重点是“清晰、完备、灵活”：

- 清晰：每个条目必须说明它是什么、依赖什么数据、是否能预览、为什么入选。
- 完备：覆盖技术指标、横截面、资金流、Hermass Native、Exit/Risk、Robustness。
- 灵活：不要把候选写死成单一指标，要保留参数空间和 Block 组合可能性。

## 输出文件

写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-factor-catalog-curation.md`

## 输出结构

### 1. F0 Source Catalog YAML Draft

给出至少 10 个 source YAML 草案，必须包含：

- `sqx_b143_local`
- `qlib`
- `quantconnect_lean`
- `talib_pandasta`
- `aqr`
- `blackrock_factor`
- `academic_empirical`
- `blackwolf_moneyflow`
- `hermass_state_cube`
- `hermass_agent_memory`

每个 source 至少包含：

- `source_id`
- `source_type`
- `name`
- `url_or_local_ref`
- `reliability`
- `license_notes`
- `applicable_markets`
- `tags`
- `notes`

### 2. F1 MVP+ Catalog: 30 Items

从 278 个候选中筛出 30 个最适合进入 MVP+ 的 factor/block。

必须覆盖：

- Technical indicator factors。
- Cross-sectional factors。
- Money flow / liquidity factors。
- Hermass native state factors。
- Exit / risk blocks。
- Robustness smoke blocks。

每个条目必须包含：

- `id`
- `name`
- `factor_or_block`
- `category`
- `source_refs`
- `evidence_level`
- `data_availability`
- `future_leakage_risk`
- `required_tables`
- `required_columns`
- `compute_engine`
- `preview_support`
- `dsl_exposure`
- `production_gate`
- `reason_selected`

### 3. F2 Candidate Catalog: 70 Items

给出下一批 70 个候选，字段同 F1，但允许：

- 数据暂不完整。
- evidence 低于生产准入。
- compute cost 偏高。

每个候选必须标注进入 F2 而不是 F1 的原因。

### 4. Research Backlog

把剩余候选按 source_type 分组：

- 每组数量。
- 代表性条目。
- 暂不进入 F1/F2 的主要原因。

### 5. Selection Principles

总结本轮筛选规则，至少覆盖：

- A 股数据可得性。
- 未来函数风险。
- 计算成本。
- 是否适配当前 DSL/Preview/Light Backtest。
- 是否提高策略族覆盖面。
- 是否能作为 Hermass 自有优势。

### 6. Data Gap Notes

列出 F1/F2 里仍缺的数据，按阻塞程度分：

- Blocker。
- Important。
- Nice-to-have。

## 验收标准

- F0 至少 10 个 source。
- F1 精确 30 个条目。
- F2 精确 70 个条目。
- 每个 F1 条目必须有 production_gate。
- `future_leakage_risk=high` 的条目不得进入 F1。
- `data_availability=unavailable` 的条目不得进入 F1。
- 明确哪些条目可直接进入 Qoder registry 规格。

## 禁止事项

- 不要实现代码。
- 不要生成超过 100 个 F1/F2 条目。
- 不要把未经证据治理的交易理念直接标为 production。
- 不要复制 StrategyQuant 源码或本地文件内容，只能做目录级、概念级、功能级归纳。
