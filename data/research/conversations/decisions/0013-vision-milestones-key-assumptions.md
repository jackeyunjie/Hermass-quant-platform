# 0013 Vision, Milestones, And Key Assumptions

## 背景

用户要求参考 S 级私董会的成长，设计 Hermass 的愿景、里程碑和关键假设。

本次参考的 S 级私董会关键机制包括：

- 分层加速场，不是数字越高越好，而是越匹配越有效。
- 公共契约，不把共同体做成消费品。
- 案主机制，用真实问题驱动共创。
- 标准流程、角色分工、复盘和行为权重。
- 长期商业共同体，而不是一次性活动。

## 决策

新增产品战略文档：

- `docs/product/VISION_MILESTONES_AND_KEY_ASSUMPTIONS.md`

核心愿景：

> Hermass 要成为个人和小团队的 AI 量化研究操作系统，把投资者的策略想法变成可验证、可审计、可复盘、可协作的研究资产。

核心分层：

- H1 Strategy Structuring Lab：讲清策略，生成 DSL。
- H2 Strategy Diagnosis Lab：梳理真问题，红线/preview/audit。
- H3 Strategy Evidence Lab：真实回测、交易证据、多周期状态。
- H4 Portfolio Governance Lab：多策略、多 Agent、组合治理。

## 理由

Hermass 当前不适合被定位为“自动荐股工具”或“交易机器人”。S 级私董会的成长经验说明，高质量系统需要靠分层、契约、真实问题和长期资产沉淀，而不是靠单次消费体验。

把这个逻辑迁移到 Hermass，可以让产品路线从“做功能”升级为“建设研究共同体”，同时保持 DSL-first、red-line-first、audit-first 的工程底线。

## 下一步

1. 把 H1/H2/H3/H4 分层转成用户进入诊断表。
2. 把 Hermass 公共契约写入 pilot onboarding。
3. 在 README 中更新 Phase 2 当前状态和边界。
4. 先修 Qoder hardening review 中的 real baseline blockers。
5. 准备 Kimi 要求的真实 DB baseline 数据。
