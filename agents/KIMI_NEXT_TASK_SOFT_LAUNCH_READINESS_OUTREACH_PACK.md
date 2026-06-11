# Kimi Next Task: Soft Launch Readiness Review And First Outreach Pack

你是 Hermass AI Quant Platform 的 Kimi Research Engineer。本轮任务是判断当前仓库是否具备私域软启动条件，并输出一套可直接使用的首批传播素材包。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `README.md`
- `docs/TASK_ALLOCATION.md`
- `data/research/conversations/decisions/0010-external-service-readiness.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-github-stars-growth-plan.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi2-data-refresh-replacement-audit.md`（如已存在）
- `agents/KIMI_NEXT_TASK_GITHUB_STARS_GROWTH_PLAN.md`

## 背景

K12 已输出 GitHub 成熟化计划，判定当前 `NOT_READY_TO_PROMOTE`。Codex 判断：

- GitHub P0 成熟化（README、LICENSE、Topics、Description、examples 等）应由 Codex 在 Kimi 输出 K13 前完成并推送。
- K13 的任务不是等 P0 全部完成后再做，而是提前准备软启动 readiness 复核和传播包，以便 P0 完成后立即启动。
- KIMI2 数据审计尚未完成，任何传播都必须继续标注 `light_stub`，不能宣称真实回测能力。
- 当前 stars 仍为 `0`，下一步不应直接 public launch，应先做私域/熟人软启动复核。

## 本轮目标

输出一份软启动准备度复核与首批传播包，回答：

1. 当前是否具备私域软启动条件？
2. README、Quickstart、License、Description、Topics、examples、disclaimer 和 `light_stub` 标注是否足够？
3. 首批可以触达谁、不能触达谁？
4. 可以说什么、不能说什么？
5. 首批传播文案（中文/英文私信、朋友圈、X/LinkedIn、GitHub pinned issue）是什么？
6. 7 天反馈收集计划是什么？

## 必须输出

### 1. Soft Launch Readiness Verdict

给出明确判断，只允许以下之一：

- `NOT_READY`：任何软启动都不应开始。
- `PRIVATE_SOFT_LAUNCH_READY`：可以开始向熟人/私域小规模传播。
- `PUBLIC_SOFT_LAUNCH_READY`：可以开始向技术社区公开分享。
- `PUBLIC_LAUNCH_READY`：可以面向公众大规模推广。

默认应为 `PRIVATE_SOFT_LAUNCH_READY` 或 `NOT_READY`。如果认为更高，必须给出证据。

### 2. Repository Readiness Checklist

复核以下项目，标注是否满足软启动要求：

| 检查项 | 状态 | 备注 |
|--------|------|------|
| README 30 秒讲清 | | |
| Quickstart 3 分钟可运行 | | |
| License (Apache-2.0) | | |
| Description 准确无拼写 | | |
| Topics >= 5 个 | | |
| examples/ 目录有样例 | | |
| Issue templates | | |
| CONTRIBUTING.md | | |
| Disclaimer 醒目 | | |
| `light_stub` 标注不可跳过 | | |
| Release v0.1.0 | | |
| Badges | | |

### 3. Outreach Boundary

定义本轮软启动边界：

**允许触达**：
- 内部团队成员
- 熟人/朋友（有技术或量化背景）
- 合作研究用户

**不允许触达**：
- 无投资经验的普通公众
- 期望获得交易信号的用户
- 通过公开链接自注册的用户

**允许说**：
- 策略结构化研究工具
- 中文策略转 DSL
- 红线检查、条件预览
- 审计追踪
- 当前为研究演示，回测为 stub

**禁止说**：
- 投资建议、荐股、买卖点
- 收益承诺、稳赚、跑赢大盘
- 自动交易、一键下单
- 回测收益率（stub 指标为占位符）

### 4. First 20 Outreach Template

输出首批 20 人目标人群模板（不包含真实个人隐私）：

| # | 人群类型 | 触达渠道 | 预期反馈 |
|---|----------|----------|----------|
| 1-5 | 内部团队 | 私聊 | 技术反馈 |
| 6-10 | 熟人（技术背景）| 微信/私信 | README 清晰度 |
| 11-15 | 熟人（量化兴趣）| 微信/私信 | 策略表达是否自然 |
| 16-20 | 技术社区熟人 | Twitter/X/LinkedIn | 项目定位理解 |

### 5. Outreach Copy Pack

输出以下文案：

#### A. 中文私信模板

```
【私信标题】

【正文】

【免责声明】
```

#### B. 英文私信模板

```
[Subject]

[Body]

[Disclaimer]
```

#### C. 朋友圈/中文社群短帖

```
```

#### D. X/LinkedIn 短帖

```
```

#### E. GitHub Pinned Issue 文案

```markdown
# Welcome to Hermass Research Pilot

...
```

### 6. 7-Day Feedback Plan

| 天数 | 动作 | 目标 |
|------|------|------|
| Day 1 | 发送首批 5 人 | 收集初始反馈 |
| Day 2-3 | 根据反馈调整文案 | 优化表述 |
| Day 4 | 扩展至 10 人 | 验证调整效果 |
| Day 5-6 | 收集结构化反馈 | 填写反馈表 |
| Day 7 | 复盘 | 判断是否继续扩展 |

### 7. Success / Stop Criteria

**成功标准**：
- 5 人完成 star
- 0 人误解为投资建议
- 收集 >=3 条可执行改进建议

**停止标准**：
- 任何人表示将基于输出做真实交易
- 任何人质疑合规性
- 连续 2 天无新增 star

**红旗反馈**（出现任一需立即暂停）：
- "这是荐股软件吗？"
- "回测收益率是真的吗？"
- "能自动下单吗？"

### 8. Engineering Backlog For Codex

列出软启动前后 Codex 需要完成的工程任务：

- [ ] Demo GIF/截图
- [ ] CI/GitHub Actions
- [ ] SECURITY.md
- [ ] CODE_OF_CONDUCT.md
- [ ] Changelog
- [ ] 真实 Light Backtest 替换 stub

## 输出文件

请写入：

`data/research/conversations/agent-runs/2026-06-11-kimi-soft-launch-readiness-outreach-pack.md`

## 输出格式

```markdown
# Soft Launch Readiness Review And First Outreach Pack

## Soft Launch Readiness Verdict

## Repository Readiness Checklist

## Outreach Boundary

## First 20 Outreach Template

## Outreach Copy Pack

## 7-Day Feedback Plan

## Success / Stop Criteria

## Engineering Backlog For Codex

## Risks

## Handoff For GitHub Sync
```

## 验收标准

- 结论明确，不含模糊话术。
- 默认 verdict 为 `PRIVATE_SOFT_LAUNCH_READY` 或 `NOT_READY`。
- 每类文案都有合规检查，不含禁止话术。
- 首批 20 人模板不包含真实个人隐私。
- 7 天计划可执行，有明确的成功/停止标准。
- 按 K10 同步纪律输出 GitHub / Obsidian handoff。

## 不做什么

- 不 public launch。
- 不宣称真实回测能力。
- 不越界投资建议。
- 不刷星、不买星。
- 不泄露个人隐私。
