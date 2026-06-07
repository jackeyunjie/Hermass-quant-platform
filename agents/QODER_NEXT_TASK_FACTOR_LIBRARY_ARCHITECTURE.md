# Qoder Next Task: Factor Library Architecture

请先读取：

1. `AGENTS.md`
2. `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
3. `agents/PHASE1_IMPLEMENTATION_PATCH_SPEC.md`
4. `hermass_platform/strategy_lab/condition_registry.py`
5. `hermass_platform/strategy_lab/dsl_schema.py`

## 背景

当前 Strategy DSL 条件库只够 MVP。用户要求高配因子库，Codex 已确定方向：先建立 Factor Registry 和 metadata schema，再逐步计算和评估。

## 你的任务

请输出 Factor Library 的工程架构设计，要求 Codex 可以直接按设计实现 F0。

## 必须输出

### 1. 模块结构

设计：

- `hermass_platform/factors/factor_schema.py`
- `hermass_platform/factors/factor_registry.py`
- `hermass_platform/factors/factor_processors.py`
- `hermass_platform/factors/factor_evaluator.py`
- `hermass_platform/factors/factor_catalog_loader.py`
- `config/factors/factor_catalog.yaml`
- `hermass_platform/factors/tests/`

### 2. Factor Metadata Schema

必须包含：

- factor_id
- name
- category
- level
- frequency
- inputs
- required_tables
- output_type
- window
- direction
- normalization
- neutralization
- compute_engine
- preview_support
- dsl_exposure
- status
- version

### 3. Factor Registry API

设计接口：

- register
- get
- list_all
- list_by_category
- list_by_status
- list_dsl_exposed
- validate_dependencies
- validate_no_future_leakage_metadata

### 4. DSL 接入设计

设计通用条件：

- `factor_threshold`
- `factor_rank`
- `factor_percentile`
- `factor_cross`
- `factor_composite_score`

说明如何避免为每个因子创建一个 condition_type。

### 5. F0 测试设计

至少 20 个测试点，覆盖：

- metadata 校验。
- catalog 加载。
- 重复 factor_id 拒绝。
- required_tables 校验。
- DSL exposure 状态。
- future leakage metadata 检查。

### 6. F0 实现顺序

给 Codex 的实现步骤，必须小步可验收。

## 输出文件

写入：

`agents/FACTOR_LIBRARY_ARCHITECTURE.md`

## 输出格式

```markdown
# Factor Library Architecture

## Module Structure

## Factor Metadata Schema

## Registry API

## Catalog YAML Design

## DSL Integration

## Tests

## Implementation Order

## Non-MVP Items
```

## 不做什么

- 不实现 50 个因子的计算。
- 不引入 TA-Lib 依赖。
- 不改回测引擎。
- 不把未评估因子暴露给生产 DSL。
