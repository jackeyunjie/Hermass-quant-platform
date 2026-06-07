# 0003 Qoder Phase 0 Accepted With Followups

## 背景

Qoder 已完成 Phase 0 DSL 工程实现，并报告 110 个测试通过。Codex 已在本地复核。

## 决策

接受 Qoder 的 Phase 0 实现作为当前 DSL MVP 基础。

已接受模块：

- DSL Schema。
- Condition Registry。
- Condition Translator。
- DSL Validator。
- DSL Generator stub。
- Backtest Adapter stub。
- 4 组测试文件。

## 理由

核心 MVP 验收已成立：

- 合法 MA 策略可构造、校验、翻译。
- 缺少止损会被拒绝。
- 仓位超过 25% 会被 Pydantic 拒绝。
- 110 个测试通过。
- 源文件编译通过。

## 风险

- 当前测试在 pyenv Python 3.11.12 下通过，默认 `python3` 没有 pytest。
- 字段依赖还没有进入 registry，只在 translator 结果中体现。
- 回测适配器仍是 stub，不能代表 Phase 2 可用。

已处理：

- 已补 `README.md`，避免 `pyproject.toml` readme 引用导致后续构建失败。

## 下一步

1. 让 Qoder 基于 Kimi 结论修订字段依赖设计。
2. Codex 开始整理 Phase 1 API/Preview/DB migration。
