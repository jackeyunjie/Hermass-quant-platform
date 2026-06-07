# Qoder Next Task: Phase 1 Implementation Patch Spec

请先读取：

1. `AGENTS.md`
2. `docs/TASK_ALLOCATION.md`
3. `agents/PHASE1_API_PREVIEW_DESIGN.md`
4. `data/research/conversations/decisions/0004-phase1-preview-stop-loss-context.md`
5. `hermass_platform/strategy_lab/condition_registry.py`
6. `hermass_platform/strategy_lab/condition_translator.py`
7. `hermass_platform/strategy_lab/dsl_validator.py`

## 背景

Qoder 的 Phase 1 设计已被采纳，但 Codex 做了一个关键裁决：

`stop_loss_pct` 不能因为需要持仓上下文就让 Phase 1 Preview 整体拒绝。MVP 要求策略必须有止损，也要求合法策略可 preview。

因此，Phase 1 实现必须区分：

- 数据源依赖：`required_columns` / `required_tables`
- 执行上下文依赖：如 position context
- Preview 支持状态：fully_supported / mock_only / requires_backtest_context / unsupported

## 你的任务

请交付一份可直接给 Codex 实现的补丁规格，修订 Phase 1 设计中的 metadata、Preview 规则和测试断言。

## 必须输出

### 1. `ConditionSpec` 修订方案

请给出 dataclass 最终字段：

- `required_columns`
- `required_tables`
- `context_requirements`
- `preview_support`
- 你认为必要的其他字段

并给出所有 11 个 MVP 条件的 metadata 表。

必须覆盖：

- `ma_golden_cross`
- `ma_death_cross`
- `price_cross_ma`
- `state_hex_in`
- `state_ef_count`
- `volume_ratio`
- `industry_include`
- `industry_exclude`
- `stop_loss_pct`
- `take_profit_pct`
- `limit_up_filter`

### 2. Preview 支持规则

请明确：

- 哪些条件在 mock preview 中 fully supported。
- 哪些条件在 DuckDB preview 中 fully supported。
- 哪些条件需要 `requires_backtest_context`。
- 遇到 unsupported 条件时如何返回错误。
- `stop_loss_pct` 如何返回 section-level preview，而不让整体 preview 失败。

### 3. API/Service 实现细节

请为以下文件输出函数签名和关键逻辑：

- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/preview_service.py`
- `hermass_platform/strategy_lab/audit.py`
- `hermass_platform/strategy_lab/storage.py`
- `migrations/strategy_lab/001_init.sql`

重点：

- PreviewResponse 需要支持 section/condition 级状态。
- Audit 需要记录 `trace_id/dsl_version/input_hash/output_hash/red_line_result`。
- Storage 只做参数化 SQL，不做业务校验。

### 4. 测试修订

请列出需要新增/修改的测试，必须包含：

- 合法 DSL 含 `stop_loss_pct` 时，mock preview 整体通过。
- 合法 DSL 含 `stop_loss_pct` 时，DuckDB preview 不整体失败，stop loss condition 标记为 `requires_backtest_context`。
- 真正 unsupported condition 才整体失败。
- SQL preview 不包含 `SELECT *`。
- Preview 前红线失败时不执行查询。
- Audit 写入完整必要字段。

### 5. 实现顺序

请输出 Codex 应按什么顺序改文件，避免大范围返工。

## 输出格式

```markdown
# Phase 1 Implementation Patch Spec

## ConditionSpec Final Shape

## MVP Condition Metadata

## Preview Semantics

## API And Service Patch Details

## Storage And DDL Patch Details

## Tests To Add Or Change

## Implementation Order

## Risks
```

## 不做什么

- 不写完整回测引擎。
- 不调用 LLM。
- 不做 Agent Debate。
- 不做 Paper Trading。
- 不把 `stop_loss_pct` 当成 Preview blocked condition。
