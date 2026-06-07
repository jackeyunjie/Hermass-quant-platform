# 0009 因子目录与 Registry 采纳裁决

## 文件用途

这是 Codex 的项目裁决记录，不是给 Kimi 或 Qoder 的提示词。

它放在 `data/research/conversations/decisions/`，表示这是一条进入项目长期记忆的架构决策：

- 记录 Kimi 的因子目录压缩结果是否采纳。
- 记录 Qoder 的 registry 规格是否采纳。
- 固定下一步实现时必须遵守的边界。
- 防止后续 Agent 忘记已经裁决过的命名、准入和实现范围。

对应关系：

- Kimi 交付：`data/research/conversations/agent-runs/2026-06-06-kimi-factor-catalog-curation.md`
- Qoder 交付：`agents/SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`
- 下一步 Kimi 提示词：`agents/KIMI_NEXT_TASK_F1_FACTOR_FORMULA_CONTRACTS.md`
- 下一步 Qoder 提示词：`agents/QODER_NEXT_TASK_FACTOR_REGISTRY_IMPLEMENTATION_PATCH.md`

## 背景

Hermass 因子库扩展不能停留在“最全候选列表”。Kimi 已将 278 条广义 factor/block 候选压缩为 F0/F1/F2 目录草案；Qoder 已输出 Source/Evidence/Factor/Block Registry 代码规格。

## 决策

采纳 Kimi 的 F0/F1/F2 分层作为下一阶段因子库治理输入：

- F0: 12 个 source catalog 草案。
- F1: 30 个 MVP+ factor/block。
- F2: 70 个 candidate。
- Research Backlog: 178 个长期研究项。

采纳 Qoder 的 registry 架构作为实现输入：

- `hermass_platform/factors/source_schema.py`
- `hermass_platform/factors/factor_schema.py`
- `hermass_platform/factors/block_schema.py`
- `hermass_platform/factors/registry.py`
- `hermass_platform/factors/catalog_loader.py`
- `config/factors/*.yaml`

实现时必须修正一个命名漂移：`source_type` 以 `agents/FACTOR_SOURCE_SCHEMA.md` 为 canonical，不采用 Qoder spec 中改写后的枚举名。

Canonical `source_type`：

- `strategy_generator`
- `open_quant_framework`
- `institutional_factor`
- `academic_literature`
- `fundamental_data`
- `news_sentiment`
- `money_flow`
- `trader_methodology`
- `behavioral_factor`
- `hermass_native`

## 理由

Kimi 的目录压缩解决了范围失控问题：F1 只有 30 个，且没有 `future_leakage_risk=high` 和 `data_availability=unavailable` 条目。

Qoder 的 registry spec 解决了治理落地问题：Evidence gate、future leakage gate、data availability gate、source_refs 校验都能进入代码规则。

保持 canonical source_type 可以避免 YAML catalog、Pydantic enum、registry loader 三处出现不兼容。

## 下一步

1. Kimi 输出 F1 factor formula/data contract，明确 26 个 factor 的公式、输入列、输出列、Polars/DuckDB 计算建议。
2. Qoder 输出 registry implementation patch，按 canonical source_type 实现 schema、registry、catalog loader、tests。
3. Codex 复核并落地代码，只提交通过测试的 registry 基础设施。
