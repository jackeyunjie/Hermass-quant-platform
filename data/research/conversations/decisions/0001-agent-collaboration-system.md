# 0001 Agent Collaboration System

## 背景

项目已有最终实施方案，但范围大，涉及 Qoder、Kimi、Codex 多类能力。需要建立统一协作规则，避免每个 Agent 各自扩展导致 MVP 失焦。

## 决策

建立项目级 `AGENTS.md`，并创建三个项目 Agent：

- Codex Orchestrator：统筹、实现、验收。
- Qoder Architect：DSL、架构、API、Agent DAG。
- Kimi Research Engineer：性能、数据、产业链、研究 sandbox。

同时建立项目内 Obsidian Vault 和项目内 Skill 骨架。

## 理由

MVP 的关键路径是确定性工程链路，而不是 Agent 数量。需要把研究、架构、实现分层，统一由 Codex 统筹收敛。

## 下一步

1. 让 Qoder 输出 DSL v2 MVP Schema。
2. 让 Kimi 输出 Light Backtest 性能基准方案。
3. Codex 基于两者启动 Phase 0 工程骨架。
