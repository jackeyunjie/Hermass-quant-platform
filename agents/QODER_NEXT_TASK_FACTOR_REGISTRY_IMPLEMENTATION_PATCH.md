# Qoder Next Task: Factor Registry Implementation Patch

你是 Hermass 项目的 Architect/Implementer。本轮任务是按已采纳规格实现 Source/Evidence/Factor/Block Registry 的第一版代码补丁。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `agents/FACTOR_SOURCE_SCHEMA.md`
- `agents/SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`
- `data/research/conversations/decisions/0009-factor-catalog-registry-accepted.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-factor-catalog-curation.md`

如果 Kimi 已输出以下文件，也必须读取：

- `data/research/conversations/agent-runs/2026-06-06-kimi-f1-factor-formula-contracts.md`

## 关键裁决

`source_type` 必须以 `agents/FACTOR_SOURCE_SCHEMA.md` 为 canonical。

必须使用：

```text
strategy_generator
open_quant_framework
institutional_factor
academic_literature
fundamental_data
news_sentiment
money_flow
trader_methodology
behavioral_factor
hermass_native
```

不要使用以下漂移命名：

```text
institutional_factor_research
academic_empirical
fundamental
news_event_sentiment
money_flow_microstructure
behavioral_psychology
```

## 目标

实现 metadata registry，不实现因子计算。

## 必须新增文件

```text
hermass_platform/factors/__init__.py
hermass_platform/factors/exceptions.py
hermass_platform/factors/source_schema.py
hermass_platform/factors/factor_schema.py
hermass_platform/factors/block_schema.py
hermass_platform/factors/registry.py
hermass_platform/factors/catalog_loader.py
hermass_platform/factors/tests/__init__.py
hermass_platform/factors/tests/test_source_schema.py
hermass_platform/factors/tests/test_factor_schema.py
hermass_platform/factors/tests/test_block_schema.py
hermass_platform/factors/tests/test_registry.py
hermass_platform/factors/tests/test_catalog_loader.py
hermass_platform/factors/tests/test_integration.py
config/factors/source_catalog.yaml
config/factors/factor_catalog.yaml
config/factors/block_catalog.yaml
config/factors/evidence_catalog.yaml
```

## 实现范围

### 1. Schema

实现 Pydantic v2 models：

- `FactorSource`
- `Evidence`
- `MetricRef`
- `FactorSpec`
- `BlockSpec`
- `ParameterSpec`
- `ParameterSpace`

### 2. Registry

实现：

- `SourceRegistry`
- `FactorRegistry`
- `BlockRegistry`
- `EvidenceRegistry`
- `RegistryValidator`

最小 API：

- `register`
- `get`
- `list_all`
- `list_by_type`
- `list_by_category`
- `list_by_status`
- `validate_source_refs`
- `validate_evidence_gate`
- `validate_no_future_leakage`
- `list_production_ready`

### 3. Catalog Loader

实现 YAML 加载：

- source catalog。
- factor catalog。
- block catalog。
- evidence catalog。

YAML 格式可以参考 `agents/SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`，但必须使用 canonical source_type。

### 4. Minimal Catalog

从 Kimi F0/F1 中抽取：

- 至少 10 个 sources。
- 至少 10 个 factors。
- 至少 10 个 blocks。
- 至少 10 个 evidence records。

F1 中 26 个 factor 不要求本轮全部进 YAML，但 schema 必须能容纳。

## 业务规则

必须硬编码并测试：

- E0-E3 -> `blocked`。
- E4 -> `candidate`。
- E5/E6 -> `approved`。
- `future_leakage_risk=high` -> `blocked`。
- `data_availability=unavailable` -> `blocked`。
- 未注册 `source_refs` -> 拒绝。
- `list_production_ready()` 只返回 `approved`。
- registry 不做因子计算、不回测、不调 Web API。

## 测试要求

至少 35 个 pytest 测试点。

必须覆盖：

- canonical source_type 枚举。
- 漂移 source_type 被拒绝。
- FactorSource 必填字段。
- Evidence level gate。
- FactorSpec production_gate 自动推导。
- BlockSpec production_gate 自动推导。
- Future leakage 拒绝。
- Data unavailable 拒绝。
- source_refs 不存在拒绝。
- YAML catalog 加载。
- `list_production_ready()` 过滤。
- Exit/Risk block 的 `REQUIRES_BACKTEST_CONTEXT` 不导致整体拒绝。

## 验收命令

使用项目 Python 环境运行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/factors/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/factors/*.py
```

## 明确不做

- 不实现 RSI/MACD/ADX 等具体计算。
- 不改 Strategy Lab DSL。
- 不改 FastAPI。
- 不做真实回测。
- 不抓取网页。
- 不导入 StrategyQuant 源码。

## 输出要求

完成后回复：

- 新增/修改文件列表。
- 测试数量和通过结果。
- 未实现边界。
- 是否发现与现有 Strategy Lab 的接口冲突。
