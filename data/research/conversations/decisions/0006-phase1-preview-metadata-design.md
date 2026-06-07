# 0006 Phase 1 Preview Metadata Design

## 背景

Qoder 已交付 `agents/PHASE1_IMPLEMENTATION_PATCH_SPEC.md`，修正了原 Phase 1 设计中 `stop_loss_pct` 会阻塞 Preview 的问题。

## 决策

Phase 1 实现采用 Qoder 修订后的 metadata 设计：

- `required_columns`
- `required_tables`
- `context_requirements`
- `preview_support`
- `preview_notes`

Preview 路由决策以 `preview_support` 为唯一权威字段。

支持状态：

- `fully_supported`
- `mock_only`
- `requires_backtest_context`
- `unsupported`

`stop_loss_pct` 和 `take_profit_pct`：

- `required_tables=["daily_bars"]`
- `context_requirements=["position"]`
- `preview_support="requires_backtest_context"`
- 不阻塞整体 Preview。

## 理由

该设计区分了静态数据依赖和运行时持仓上下文依赖，避免所有合规策略因必须包含止损而无法 Preview。

## 下一步

Codex 按以下顺序实现：

1. 修改 `condition_registry.py`。
2. 保持 `condition_translator.py` 职责不变。
3. 实现 `api_models.py`。
4. 实现 DDL 和 `storage.py`。
5. 实现 `audit.py`。
6. 实现 `preview_service.py`。
7. 实现 Web 路由。
