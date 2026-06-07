# Qoder Next Task: Source/Factor/Block Registry Code Spec

你是 Hermass 项目的 Architect。本轮任务不是实现完整因子计算，而是输出可直接交给 Codex 落代码的 Source/Evidence/Factor/Block Registry 代码规格。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `agents/FACTOR_SOURCE_SCHEMA.md`
- `docs/FACTOR_SOURCE_TAXONOMY.md`
- `docs/FACTOR_BLOCK_LIBRARY_DESIGN_PRINCIPLES.md`
- `data/research/conversations/decisions/0008-broad-factor-source-evidence-governance.md`
- `agents/QODER_NEXT_TASK_FACTOR_LIBRARY_ARCHITECTURE.md`
- `agents/QODER_NEXT_TASK_BLOCK_LIBRARY_ARCHITECTURE.md`

如果 Kimi 已输出以下文件，也必须读取：

- `data/research/conversations/agent-runs/2026-06-06-kimi-factor-catalog-curation.md`

## 目标

设计一个轻量但严格的 metadata registry，让 Hermass 可以治理“最全因子库”，但不会把未经验证的因子直接暴露给生产 DSL。

本轮只做代码规格，不直接改代码。

## 输出文件

写入：

`agents/SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`

## 必须设计的模块

### 1. `hermass_platform/factors/source_schema.py`

必须定义：

- `SourceType`
- `Reliability`
- `ApplicableMarket`
- `FactorSource`
- `EvidenceLevel`
- `EvidenceType`
- `ValidationStatus`
- `FailureMode`
- `MetricRef`
- `Evidence`

要求：

- 使用 Pydantic v2。
- 枚举值必须与 `docs/FACTOR_SOURCE_TAXONOMY.md` 和 `agents/FACTOR_SOURCE_SCHEMA.md` 对齐。
- 给出字段、类型、默认值、校验规则。

### 2. `hermass_platform/factors/factor_schema.py`

必须定义：

- `FactorSpec`
- `DataAvailability`
- `FutureLeakageRisk`
- `ProductionGate`
- `FactorStatus`
- `ComputeEngine`
- `PreviewSupport`
- `DslExposure`

要求：

- `production_gate` 必须能从 evidence/data/leakage/status 推导。
- `required_tables` 和 `required_columns` 必须支持静态校验。
- 支持参数空间，但不要实现计算逻辑。

### 3. `hermass_platform/factors/block_schema.py`

必须定义：

- `BlockSpec`
- `BlockType`
- `ContextRequirement`
- `ParameterSpec`
- `ParameterSpace`

要求：

- Block 要能表达 Signal、Entry、Exit、Order、MoneyManagement、Robustness、ReportColumn。
- Block 可以引用 FactorSpec。
- Exit/Risk block 可标注 `REQUIRES_BACKTEST_CONTEXT`，但不能因此被整体拒绝。

### 4. `hermass_platform/factors/registry.py`

必须设计：

- `SourceRegistry`
- `FactorRegistry`
- `BlockRegistry`
- `EvidenceRegistry`

每个 registry 至少包含：

- `register`
- `get`
- `list_all`
- `list_by_type`
- `list_by_category`
- `list_by_status`

还必须包含跨 registry 校验：

- `validate_source_refs`
- `validate_evidence_gate`
- `validate_no_future_leakage`
- `list_production_ready`

### 5. YAML Catalog

必须设计文件格式和加载流程：

- `config/factors/source_catalog.yaml`
- `config/factors/factor_catalog.yaml`
- `config/factors/block_catalog.yaml`

每个 YAML 至少给 10 个示例条目。

## 业务规则

必须明确写入规格：

- E0-E3 默认 blocked。
- E4 只能 candidate，不得 production ready。
- E5/E6 才允许 production approved。
- `future_leakage_risk=high` 必须 blocked。
- `data_availability=unavailable` 必须 blocked。
- `source_refs` 必须全部存在。
- 未注册 source ref 必须拒绝。
- `production_ready` 只返回 approved 条目。
- registry 不做因子计算，不做回测，不调 Web API。

## 测试设计

必须给出至少 30 个 pytest 测试点，覆盖：

- Source schema 枚举和字段校验。
- Evidence gate。
- FactorSpec production_gate 推导。
- Future leakage 拒绝。
- Data unavailable 拒绝。
- source_refs 不存在拒绝。
- BlockSpec 引用 factor。
- YAML catalog 加载。
- `list_production_ready` 只返回 approved。
- Preview support 与 backtest context 的边界。

## 实施顺序

给出 Codex 可执行的实施顺序：

1. 新建 `hermass_platform/factors/` 包。
2. 写 schema。
3. 写 registry。
4. 写 YAML loader。
5. 写最小 catalog。
6. 写测试。
7. 跑验收命令。

每步必须有验收标准。

## 明确不做

本轮不要设计或实现：

- 因子数值计算。
- Alpha 回测。
- FastAPI 路由。
- LLM 生成因子。
- 自动抓取网页来源。
- 真实 StrategyQuant 代码导入。

## 输出格式

输出文档必须包含：

- File-by-file code spec。
- Pydantic model fields。
- Registry APIs。
- YAML examples。
- Test plan。
- Implementation order。
- Non-MVP exclusions。
