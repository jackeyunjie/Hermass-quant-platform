# Qoder Next Task: Block Library Architecture

请先读取：

1. `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
2. `docs/STRATEGYQUANT_XB143_REFERENCE_MODEL.md`
3. `agents/QODER_NEXT_TASK_FACTOR_LIBRARY_ARCHITECTURE.md`
4. `hermass_platform/strategy_lab/condition_registry.py`
5. `AGENTS.md`

## 背景

Hermass 因子库方向已经升级为 Factor + Block Library。参考 StrategyQuant X B143，不只需要指标，还需要 signal/entry/exit/order/robustness blocks。

## 你的任务

设计 Block Library 架构，要求 Codex 可以直接实现 F0 metadata registry。

## 必须输出

### 1. BlockSpec Schema

字段必须包括：

- block_id
- block_type
- name
- description
- input_factor_types
- parameters
- parameter_space
- weight
- enabled
- required_tables
- required_columns
- required_context
- preview_support
- dsl_output
- robustness_role
- market_scope
- status
- version

### 2. BlockRegistry API

设计：

- register
- get
- list_by_type
- list_enabled
- list_dsl_output
- validate_parameter_space
- validate_market_scope
- validate_no_unsafe_context

### 3. Catalog YAML

设计 `config/factors/block_catalog.yaml` 示例，至少包含：

- 3 个 signal block。
- 2 个 entry block。
- 2 个 exit block。
- 2 个 filter block。
- 2 个 robustness block。

### 4. 与 DSL 的关系

说明：

- block 如何输出 DSL condition。
- block 如何组合成 strategy template。
- AI 生成策略时如何只能选择已注册 block。

### 5. 测试设计

至少 20 个测试点。

## 输出文件

写入：

`agents/BLOCK_LIBRARY_ARCHITECTURE.md`

## 输出格式

```markdown
# Block Library Architecture

## BlockSpec

## BlockRegistry API

## Catalog YAML

## DSL Integration

## Strategy Generation Constraints

## Tests

## Implementation Order
```
