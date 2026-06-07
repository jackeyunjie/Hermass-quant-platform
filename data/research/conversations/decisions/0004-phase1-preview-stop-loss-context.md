# 0004 Phase 1 Preview Stop Loss Context

## 背景

Qoder 的 Phase 1 设计建议将 `stop_loss_pct` 声明为依赖 `positions` 表，并在 Preview 阶段拒绝非 MVP 表。该设计在抽象上合理，但与 MVP 验收冲突。

MVP 同时要求：

- 策略必须包含止损。
- 合法策略必须能做条件预览。

如果 `stop_loss_pct` 导致 Preview 整体拒绝，那么所有合规策略都会被拒绝。

## 决策

Phase 1 Preview 不因 `stop_loss_pct` 依赖持仓上下文而整体拒绝。

实现规则：

- `stop_loss_pct` 保留为 exit 条件。
- Registry 可声明其需要 position context，但不将其视为 MVP blocked table。
- Mock preview 对 stop loss 返回 deterministic 估算。
- DuckDB preview 中，entry/filter 条件和静态 exit 条件可计算 hit_count；需要持仓上下文的 exit 条件标记为 `preview_status="requires_backtest_context"`。
- 完整止损命中由 Phase 2 backtest/positions 模拟负责。

## 理由

这样既保留“止损必须存在”的安全红线，又不破坏 Phase 1 的 preview 可用性。

## 下一步

Codex 在实现 `ConditionSpec` metadata 时增加上下文字段，例如：

- `required_columns`
- `required_tables`
- `context_requirements`
- `preview_support`

避免简单用 table whitelist/blocklist 决定所有条件是否可 preview。
