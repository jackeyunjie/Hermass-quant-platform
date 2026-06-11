# Codex 派工：Kimi K13 软启动准备度复核与首批传播包

## 背景

K12 已输出 GitHub 成熟化计划，判定当前 `NOT_READY_TO_PROMOTE`。Codex 判断下一步不应直接 public launch，应先做私域/熟人软启动复核。因此安排 Kimi 执行 K13 任务。

## 派工内容

- 任务：K13 GitHub 软启动准备度复核与首批传播包
- 任务文件：`agents/KIMI_NEXT_TASK_SOFT_LAUNCH_READINESS_OUTREACH_PACK.md`
- 输出文件：`data/research/conversations/agent-runs/2026-06-11-kimi-soft-launch-readiness-outreach-pack.md`

## Codex 判断

- GitHub P0 成熟化（README、LICENSE、Topics、Description、examples 等）应由 Codex 在 Kimi 输出 K13 前完成并推送。
- K13 的任务不是等 P0 全部完成后再做，而是提前准备软启动 readiness 复核和传播包，以便 P0 完成后立即启动。
- KIMI2 数据审计尚未完成，任何传播都必须继续标注 `light_stub`，不能宣称真实回测能力。

## 验收要求

- 给出 soft launch readiness verdict：`NOT_READY` / `PRIVATE_SOFT_LAUNCH_READY` / `PUBLIC_SOFT_LAUNCH_READY` / `PUBLIC_LAUNCH_READY`
- 复核 README、Quickstart、License、Description、Topics、examples、disclaimer 和 `light_stub` 标注
- 定义本轮软启动边界：允许触达谁、不允许触达谁、可以说什么、不能说什么
- 输出首批 20 人目标人群模板（不包含真实个人隐私）
- 输出中文/英文私信、朋友圈、X/LinkedIn、GitHub pinned issue 等合规文案
- 给出 7 天反馈收集计划、成功标准、停止标准和红旗反馈
- 输出软启动前后 Codex 工程 backlog
- 按 K10 同步纪律输出 GitHub / Obsidian handoff

## 下一步

Kimi 完成 K13 后，Codex 根据 verdict 决定是否启动私域软启动。
