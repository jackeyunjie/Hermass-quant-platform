# Kimi Next Task: GitHub Stars Growth And Open Source Maturity Plan

你是 Hermass AI Quant Platform 的 Kimi Research Engineer。本轮任务是把项目从“本地 MVP 工作区”推进到“外部开发者 30 秒能看懂、3 分钟能跑、愿意 star 的开源仓库”。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `README.md`
- `docs/TASK_ALLOCATION.md`
- `data/research/conversations/PROJECT_INDEX.md`
- `data/research/conversations/decisions/0010-external-service-readiness.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-github-obsidian-sync-discipline.md`
- `scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`

## 当前 GitHub 状态

本地 remote：

```text
origin https://github.com/jackeyunjie/Hermass-quant-platform.git
```

GitHub API 查询结果（2026-06-11）：

- Stars: `0`
- Forks: `0`
- Watchers: `0`
- Visibility: public
- License: none
- Topics: none
- Description: `AI NANTIVE Hermass quant platform`
- Latest pushed_at: `2026-06-07T02:32:57Z`

Codex 判断：

- 有机会获得更多 stars，但当前仓库不具备自然增长条件。
- 先不要急于外部宣传；必须先把仓库打磨成可理解、可运行、可信、可分享的开源项目。

## 本轮目标

输出一份 GitHub 多星增长与开源成熟度计划，回答：

1. 当前为什么 0 stars？
2. 哪些仓库基础项会阻碍 star 增长？
3. 如何把项目首页改造成可 star 的开源入口？
4. 第一阶段目标 stars 应该是多少？
5. 需要哪些内容资产、demo、话术和发布节奏？
6. 哪些内容因为外部服务边界/合规风险不能宣传？

## 必须输出

### 1. Star Readiness Verdict

给出明确判断：

- `NOT_READY_TO_PROMOTE`
- `READY_FOR_SOFT_LAUNCH`
- `READY_FOR_PUBLIC_LAUNCH`

按当前状态，默认应为 `NOT_READY_TO_PROMOTE`。如果你认为可以更高，必须给出证据。

### 2. Current Repository Audit

审计当前 GitHub 可见问题，至少覆盖：

- README 是否能 30 秒讲清项目。
- Quickstart 是否 3 分钟可运行。
- 是否有 License。
- 是否有 Topics。
- Description 是否准确。
- 是否有 Demo GIF/截图。
- 是否有 example output。
- 是否有 roadmap。
- 是否有 safety/disclaimer。
- 是否有 contribution guide。
- 是否有 release/tag。
- 本地成果是否已同步到 GitHub。

### 3. Star Growth Positioning

定义对外定位：

- 一句话定位。
- 面向开发者的价值主张。
- 面向量化研究者的价值主张。
- 与普通 backtest 框架的差异。
- 与自动荐股/交易系统的边界。

必须强调：

- DSL-first。
- Red-line first。
- Audit-first。
- Chinese strategy input to verifiable strategy research loop。
- Not investment advice。
- No real trading。

### 4. GitHub Improvement Backlog

输出一个分阶段 backlog：

#### P0: Before Any Promotion

至少包括：

- Commit 当前本地 MVP 成果。
- 修正 GitHub description 拼写。
- 添加 license。
- 添加 topics。
- 重写 README。
- 增加 Quickstart。
- 增加 MVP acceptance command。
- 增加 example input/output。
- 增加 service boundary / disclaimer。
- 增加 roadmap。

#### P1: Soft Launch

至少包括：

- Demo GIF 或截图。
- GitHub release v0.1.0。
- Issues templates。
- CONTRIBUTING.md。
- 示例策略目录。
- 可复制的一键验收命令。
- Badges。

#### P2: Public Growth

至少包括：

- 博文/长帖。
- 3 分钟 demo 视频。
- 与 DuckDB/Polars/AI Agent 社区关联的话题。
- 对比其他 quant/backtest 工具的定位文章。
- 真实 Light Backtest 后再扩大传播。

### 5. README Rewrite Outline

给出 README 新结构，必须包括：

- Project tagline。
- What it is / what it is not。
- MVP workflow diagram。
- Quickstart。
- Example Chinese strategy。
- Example DSL。
- Acceptance command。
- Current limitations。
- Roadmap。
- Safety / disclaimer。
- License。

### 6. Suggested GitHub Metadata

给出：

- Repository description。
- Topics 列表。
- Suggested license 选项（MIT / Apache-2.0 / Business Source 等）及取舍。
- Suggested release name。

不要直接决定 license；只给建议和风险。

### 7. Star Targets

给出现实目标：

- 0 -> 5 stars：需要做什么。
- 5 -> 20 stars：需要做什么。
- 20 -> 100 stars：需要做什么。
- 100+ stars：需要什么条件。

必须保守，不要夸张承诺。

### 8. Launch Plan

给出第一轮“soft launch”计划：

- 发布前 checklist。
- 目标受众。
- 发布渠道。
- 文案草案。
- 禁止宣传话术。
- 反馈收集方式。
- 成功标准。
- 停止标准。

### 9. Compliance-Safe Copy

基于 `0010-external-service-readiness.md` 和 K11 输出，给出不会越界的 GitHub/社媒文案：

- GitHub README tagline。
- X/LinkedIn 短帖。
- 中文朋友圈/社群短帖。
- 禁止使用的话术。

### 10. Next Steps For Codex

把你的计划压缩成 Codex 可执行的工程任务列表，按顺序列出文件路径和验收标准。

## 输出文件

请写入：

`data/research/conversations/agent-runs/2026-06-11-kimi-github-stars-growth-plan.md`

## 输出格式

```markdown
# GitHub Stars Growth And Open Source Maturity Plan

## Star Readiness Verdict

## Current Repository Audit

## Star Growth Positioning

## GitHub Improvement Backlog

## README Rewrite Outline

## Suggested GitHub Metadata

## Star Targets

## Launch Plan

## Compliance-Safe Copy

## Risks

## Next Steps For Codex
```

## 验收标准

- 结论明确，不含“可能会火”之类空话。
- 能解释当前为什么 0 stars。
- 明确 P0/P1/P2 改进 backlog。
- README outline 能直接交给 Codex 改写。
- GitHub metadata 可直接用于仓库设置。
- Star targets 保守且有动作条件。
- 文案不越界成投资建议、荐股、收益承诺或自动交易宣传。
- 产出后按 K10 同步纪律更新 Obsidian/GitHub handoff。

## 不做什么

- 不刷星。
- 不买星。
- 不虚假宣传。
- 不承诺收益。
- 不宣传真实交易能力。
- 不把 `light_stub` 当作真实回测能力。
- 不绕过 K10 同步纪律。
