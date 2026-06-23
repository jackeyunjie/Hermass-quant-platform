# Codex State Cube 架构定位审计与文档固化

## 背景

用户在审计 Phase 2 Light Backtest hardening 结果时提出关键架构结论：

> State 系统应作为应用层与风控层的核心，建立在更广泛的数据基座之上。

本记录固化该结论，并更新相关工程文档。

## 已执行工作

### 1. 测试环境验证

- `pyproject.toml` 的 `[tool.hatch.build.targets.wheel]` 配置已存在，构建正常。
- `uv run pytest hermass_platform/strategy_lab/tests -q` → **278 passed, 0 failed**。
- `uv run python scripts/run_strategy_lab_mvp_e2e_acceptance.py` → **5/5 cases passed**。
- `data/p116_foundation.duckdb` 与 `data/state_cube.duckdb` 仍不存在 → real baseline 继续阻塞。

### 2. 架构决策记录

新增：

- `data/research/conversations/decisions/0015-state-cube-architectural-positioning.md`

要点：

- 明确三层架构：L1 Data Foundation（更广泛基座） → L0.5 State / Regime Cube → L3 Application & Risk-Control。
- State Cube 不再是 L0 Raw Input，而是从 L0 推导的应用/风控层核心抽象。
- Foundation DB 必须能独立支撑 `include_state=false` 的回测。
- State Cube 承担 regime filter、volume-state composite、持仓/出场证据、Risk Guardian 输入等角色。

### 3. 设计文档

新增：

- `docs/design/DATA_FOUNDATION_AND_STATE_CUBE_ARCHITECTURE.md`

内容覆盖：

- 三层模型图。
- 分层理由（独立验证、风控输入、证据分层）。
- 模块映射表。
- Backtest with State 数据流图。
- Non-goals 与 migration notes。

### 4. 现有文档更新

- `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
  - 将 State Cube 从 `L0 Raw Inputs` 移出。
  - 新增 `L0.5 State / Regime Layer` 小节。
- `docs/FACTOR_SOURCE_TAXONOMY.md`
  - 在 `S10: Hermass Native Sources` 中明确 State Cube 是应用层与风控层核心。
- `docs/TASK_ALLOCATION.md`
  - 在 `C18` 状态更新中追加架构审计结论与新增文档引用。
- `docs/product/VISION_MILESTONES_AND_KEY_ASSUMPTIONS.md`
  - 更新 M1 状态：5 个 hardening blocker 已解决；真实 DB 仍阻塞。

## 当前状态

- 所有文档更新已完成。
- 代码层面无破坏性修改。
- 测试与 E2E acceptance 保持通过。
- 真实数据基线仍等待 `data/p116_foundation.duckdb` 与 `data/state_cube.duckdb`。

## 下一步

1. Kimi 按新分层区分 `foundation_db readiness` gate 与 `state_cube readiness` gate。
2. Qoder 在条件注册表中把 State 相关条件标记为 `layer: l0.5_state`。
3. Codex 在后续 Risk Guardian 实现中优先复用 State Cube。
4. 真实 DB 就绪后运行 `benchmarks/validate_real_data.py` 完成 M2 real baseline gate。

## 参考

- `data/research/conversations/decisions/0015-state-cube-architectural-positioning.md`
- `docs/design/DATA_FOUNDATION_AND_STATE_CUBE_ARCHITECTURE.md`
- `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
- `docs/FACTOR_SOURCE_TAXONOMY.md`
- `docs/TASK_ALLOCATION.md`
- `docs/product/VISION_MILESTONES_AND_KEY_ASSUMPTIONS.md`
