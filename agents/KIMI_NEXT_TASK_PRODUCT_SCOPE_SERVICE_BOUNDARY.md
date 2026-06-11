# Kimi Next Task: Product Scope And Service Boundary

你是 Hermass AI Quant Platform 的 Kimi Research Engineer。本轮任务不是继续扩因子库、不是继续研究前沿模型，也不是设计更多 Agent；本轮任务是把项目最终目标、目标用户、只提供哪些服务、明确不提供哪些服务重新收敛成一份可执行的产品边界文档。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md`
- `data/research/conversations/project-docs/final-implementation-plan-summary.md`
- `docs/TASK_ALLOCATION.md`
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`
- `data/research/conversations/agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md`
- `agents/KIMI_RESEARCH_ENGINEER_PROMPT.md`

## 背景

当前项目已经有可运行的 MVP 验收入口：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

这条链路已经覆盖：

`中文策略输入 -> DSL v2 -> 校验 -> 红线 -> Preview -> Light Backtest -> Audit`

现在最大风险不是能力不足，而是项目范围继续扩大，导致服务对象和交付边界变模糊。你需要从用户价值、数据/性能约束、服务可验证性三个角度，帮 Codex 把产品边界重新钉死。

## 本轮目标

输出一份产品边界澄清文档，回答四个问题：

1. 我们最终到底要交付什么？
2. 用户是谁，不是谁？
3. 平台只提供哪些服务？
4. 平台明确不提供哪些服务？

你的输出必须能指导后续工程取舍：凡是不服务这些用户和这些服务边界的需求，都进入 backlog 或直接拒绝。

## Codex 当前裁决口径

请以此为默认裁决口径，不要另开主线：

- 最终产品是 DSL-first 的 AI 量化策略实验与审计平台，不是自动荐股软件。
- 第一目标用户是有一定交易认知、想把策略系统化的个人投资者和小型量化团队，不是零基础小白，也不是大型机构 OMS/EMS 用户。
- MVP 只交付策略研究闭环：中文策略输入、DSL 校验、红线、预览、轻量回测、报告、审计。
- Paper Trading、真实交易、完整 Agent Debate、TS-FM、RAG-KG、复杂产业链推理都不是当前服务。
- 所有策略必须通过 DSL 和红线，不接受用户 Python 代码，不执行 LLM 生成代码。

## 必须输出

### 1. Final Product Statement

用 3 层话术描述最终目标：

- 一句话版本：给内部 Agent 快速对齐。
- 一段话版本：给产品/工程协作使用。
- 非营销版说明：明确它不是“自动赚钱/自动荐股/真实交易”工具。

### 2. Target Users

按优先级定义目标用户，至少包含：

- P0 用户：进阶散户 / 主观交易者，已有 3-5 年交易经验，想把策略纪律化。
- P1 用户：小型私募或小团队研究员，有数据/编程基础，想快速验证想法。
- P2 用户：量化学习者，主要用于学习和模拟实验。

每类用户必须说明：

- 他们已有能力。
- 他们的核心痛点。
- 我们能帮他们完成的任务。
- 我们不替他们做的事情。
- 成功使用的最低前提。

同时列出非目标用户：

- 完全零基础、只想要买卖点的人。
- 期待保证收益的人。
- 需要真实自动下单和交易托管的人。
- 大型机构级订单执行/组合风控系统用户。

### 3. Service Boundary

把服务拆成三层：

#### MVP Services: 必须提供

至少覆盖：

- 中文策略输入到 DSL v2。
- DSL Schema/Pydantic 校验。
- 红线检查：止损、仓位、执行确认等。
- 条件命中预览。
- Light Backtest 核心指标。
- 策略报告与审计落库。
- 用户可读解释：把机器 DSL 翻译成人能理解的说明。

#### P1 Services: 可延后提供

至少覆盖：

- 参数编辑器。
- 策略版本 diff。
- 更完整的 backtest report / tearsheet。
- 更高配的 factor/block registry。
- 手动触发的 Agent 评审摘要。

#### Explicit Non-Services: 当前不提供

至少覆盖：

- 不保证收益。
- 不提供投资建议结论式“买/卖”承诺。
- 不做真实下单。
- 不托管资金。
- 不允许用户提交 Python 策略代码执行。
- 不做未经验证的 LLM 生成代码执行。
- 不在 MVP 中提供完整 Agent Debate、Paper Trading、TS-FM、RAG-KG、实时数据流。

### 4. User Journey For MVP

给出 P0 用户的一条最小旅程：

1. 用户输入中文策略。
2. 系统生成 DSL。
3. 用户看到 DSL 人类解释。
4. 系统校验并红线检查。
5. 系统展示条件命中预览。
6. 系统运行 Light Backtest。
7. 系统输出报告和审计记录。
8. 用户决定是否修改策略。

每一步请标注：

- 用户看到什么。
- 系统内部做什么。
- 失败时如何提示。
- 是否需要审计。

### 5. Acceptance Criteria

定义产品边界是否清晰的验收标准，必须能转成 Codex 后续检查项。

至少包含：

- 任一新需求能被分类为 MVP / P1 / Backlog / Reject。
- 任一服务能说明对应用户和用户任务。
- 任一输出不能被误解为保证收益或直接投资建议。
- 任一策略执行前必须有 DSL、红线、audit。
- MVP E2E acceptance command 仍是当前主验收入口。

### 6. Service Copy Guardrails

给出面向用户的文案红线，至少包含：

- 禁止说什么。
- 应该怎么说。
- 回测结果如何免责声明。
- Agent 评审如何免责声明。
- 风险提示最低文案。

### 7. Implementation Implications

请输出对工程的直接影响：

- 哪些 API / UI 必须优先。
- 哪些字段必须进入 audit。
- 哪些功能应从当前路线中降级或移出 MVP。
- 哪些 Kimi 研究成果只作为 backlog，不应阻塞 MVP。

## 输出文件

请写入：

`data/research/conversations/agent-runs/2026-06-10-kimi-product-scope-service-boundary.md`

## 输出格式

```markdown
# Product Scope And Service Boundary

## Final Product Statement

## Target Users

## Non-Target Users

## MVP Services

## P1 Services

## Explicit Non-Services

## MVP User Journey

## Acceptance Criteria

## Service Copy Guardrails

## Implementation Implications

## Risks

## Next Steps For Codex
```

## 不做什么

- 不新增代码。
- 不设计新 Agent DAG。
- 不继续扩因子库。
- 不引入新数据源。
- 不做竞品长篇研究。
- 不把产品包装成自动荐股、自动赚钱或自动交易系统。
- 不推翻当前 `中文策略输入 -> DSL -> 校验 -> 红线 -> Preview -> Light Backtest -> Audit` 主链路。
