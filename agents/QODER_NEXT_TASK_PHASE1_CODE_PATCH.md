# Qoder Next Task: Phase 1 Code Patch

请先读取：

1. `AGENTS.md`
2. `docs/TASK_ALLOCATION.md`
3. `agents/PHASE1_IMPLEMENTATION_PATCH_SPEC.md`
4. `data/research/conversations/decisions/0006-phase1-preview-metadata-design.md`
5. `hermass_platform/strategy_lab/condition_registry.py`
6. `hermass_platform/strategy_lab/condition_translator.py`
7. `hermass_platform/strategy_lab/dsl_validator.py`
8. `hermass_platform/strategy_lab/tests/`

## 背景

Phase 1 metadata/preview 设计已定稿。现在不要再写方案，请直接实现第一批代码补丁。

核心裁决：

- `preview_support` 是 Preview 路由权威。
- `required_tables` 不用于简单 blocklist。
- `stop_loss_pct` / `take_profit_pct` 是 `requires_backtest_context`，不能让整体 Preview 失败。
- Web 层暂不实现，先完成 strategy_lab service 层。

## 你的任务

实现 Phase 1 第一批代码，范围严格限定如下。

## 必须修改/新增文件

### 1. 修改 `hermass_platform/strategy_lab/condition_registry.py`

实现：

- `PreviewSupport` enum。
- `ContextRequirement` enum。
- `ConditionSpec` 增加：
  - `required_columns`
  - `required_tables`
  - `context_requirements`
  - `preview_support`
  - `preview_notes`
- 更新 11 个 MVP 条件的 metadata。

关键断言：

- `stop_loss_pct.required_tables == ["daily_bars"]`
- `ContextRequirement.POSITION in stop_loss_pct.context_requirements`
- `stop_loss_pct.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT`
- `take_profit_pct` 同上。

### 2. 新增 `hermass_platform/strategy_lab/api_models.py`

实现 Pydantic 模型：

- `ConditionPreviewItem`
- `SectionPreviewItem`
- `PreviewOverallItem`
- `PreviewRequest`
- `PreviewResponse`
- `ValidateStrategyRequest`
- `ValidateStrategyResponse`
- `GenerateStrategyRequest`
- `GenerateStrategyResponse`
- `BacktestRequest`
- `BacktestResponse`
- `GetBacktestResponse`

要求：

- `trace_id` 自动生成。
- Preview 支持 condition/section 级 `preview_support` 和 `has_context_required`。
- 所有模型可 JSON 序列化。

### 3. 新增 `hermass_platform/strategy_lab/preview_service.py`

实现：

- `PreviewService`
- `MockDataProvider`
- `PreviewResult` 或直接复用 api_models。

要求：

- `preview(dsl, data_source="mock")` 先调用 `validate_dsl`。
- 红线失败时不执行查询。
- `PreviewSupport.UNSUPPORTED` 才导致整体失败。
- `REQUIRES_BACKTEST_CONTEXT` 不导致整体失败。
- mock preview deterministic。
- SQL preview 不含 `SELECT *`。
- DuckDB provider 可以先是可注入 stub，不要求真实 DB 完整实现。

### 4. 新增/修改测试

必须新增或修改：

- `hermass_platform/strategy_lab/tests/test_condition_registry.py`
- `hermass_platform/strategy_lab/tests/test_api_models.py`
- `hermass_platform/strategy_lab/tests/test_preview_service.py`

至少覆盖：

- 所有 MVP condition 都有 `preview_support`。
- `stop_loss_pct` 不包含 `positions` table。
- 合法 DSL 含 `stop_loss_pct` 时 mock preview 整体通过。
- 合法 DSL 含 `stop_loss_pct` 时 condition 标记 `requires_backtest_context`。
- unsupported condition 整体失败。
- 红线失败时 preview 拒绝。
- SQL preview 不包含 `SELECT *`。

## 不做什么

- 不实现 storage/audit/DDL/Web routes。
- 不实现真实 LLM。
- 不实现真实回测。
- 不改 benchmark。
- 不把业务逻辑放到 Web 层。

## 验收命令

Codex 后续必须能运行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/condition_registry.py hermass_platform/strategy_lab/api_models.py hermass_platform/strategy_lab/preview_service.py
```

## 输出记录

完成后写入：

`data/research/conversations/agent-runs/2026-06-06-qoder-phase1-code-patch.md`

格式：

```markdown
# Qoder Phase 1 Code Patch

## Implemented Files

## Tests Added

## Validation Commands

## Design Choices

## Risks

## Next Steps For Codex
```
