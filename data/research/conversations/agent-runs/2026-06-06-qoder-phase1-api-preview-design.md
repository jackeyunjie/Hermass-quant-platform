# 2026-06-06 Qoder Phase 1 API Preview Design

## 输入

Qoder 基于 `agents/QODER_NEXT_TASK_PHASE1_API_PREVIEW.md` 完成 Phase 1 设计。

## 输出摘要

交付文件：

- `agents/PHASE1_API_PREVIEW_DESIGN.md`

设计覆盖：

- 字段依赖前移到 `ConditionSpec`。
- `api_models.py`
- `storage.py`
- `audit.py`
- `preview_service.py`
- `web/strategy_lab_routes.py`
- `migrations/strategy_lab/001_init.sql`
- 5 个 API 端点请求/响应结构。
- 4 张 MVP 表 DDL。
- 4 个测试文件、共 24 个测试点。

## Codex 复核

采纳：

- `ConditionSpec` 增加 `required_columns` / `required_tables` 的方向正确。
- Registry 作为条件元数据权威，Translator 负责实例化表达式。
- Phase 1 DDL 只保留策略、版本、回测、审计四张表。
- Web 层不放业务逻辑。
- Preview 前必须校验 DSL 和红线。
- SQL preview 禁止 `SELECT *`。

需修正：

- Qoder 建议 `stop_loss_pct` required_tables 包含 `positions` 并在 MVP Preview 中拒绝。
- 这会导致所有合规策略（必须有止损）都无法 preview，违反 MVP 验收目标。

Codex 裁决：

- `stop_loss_pct` 不应在 Phase 1 Preview 中触发整体拒绝。
- 它应标记为 `requires_position_context` 或 `preview_mode="backtest_only"`。
- Mock preview 可返回 deterministic 估算。
- DuckDB preview 只对 entry/filter 和可静态判断的 exit 条件做 hit_count；stop loss 留到 backtest/positions 上下文。

## 下一步

1. Codex 实现 Phase 1 时按上述裁决修正 Qoder 设计。
2. 如需 Qoder 继续参与，让其输出修订版 `ConditionSpec` metadata schema。
3. Phase 1 实现顺序：registry metadata -> API models -> DDL/storage -> audit -> preview service -> routes。
