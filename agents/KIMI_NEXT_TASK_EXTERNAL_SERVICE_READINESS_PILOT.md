# Kimi Next Task: External Service Readiness And Pilot Plan

你是 Hermass AI Quant Platform 的 Kimi Research Engineer。本轮任务是基于 Codex 当前裁决，评估 Hermass 是否可以对外提供服务，并输出一个可执行的“邀请制研究试点”方案。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md`
- `data/research/conversations/project-docs/final-implementation-plan-summary.md`
- `docs/TASK_ALLOCATION.md`
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`
- `scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- `data/research/conversations/agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md`
- `agents/KIMI_NEXT_TASK_PRODUCT_SCOPE_SERVICE_BOUNDARY.md`
- `agents/KIMI_NEXT_TASK_GITHUB_OBSIDIAN_SYNC_DISCIPLINE.md`
- `data/research/conversations/decisions/0010-external-service-readiness.md`

## 外部监管参考

你不是律师，不能给法律意见；但必须把服务边界设计为低风险，并标明需要法律/合规复核。

参考资料：

- SEC Investor.gov 对 investment adviser 的说明：如果为了报酬、作为业务向他人提供证券投资建议或证券报告/分析，可能进入 investment adviser 范畴。
- SEC Investor.gov 对证券法律的说明：美国证券法体系强调披露、防欺诈和受监管主体。
- FINRA Rule 2210：面向公众的金融沟通应公平、平衡，不得误导。

如果目标市场包含中国大陆、香港或其他地区，你必须单独列为“需要本地律师确认”的合规问题，不得自行判定合规。

## Codex 当前判断

当前结论：

**可以对外提供服务，但只能做受控、邀请制、研究用途试点；不能公开商业化开放。**

允许：

- 邀请制 Demo。
- 策略研究/回测实验服务。
- 中文策略转 DSL 的结构化服务。
- 红线检查、条件预览、Light Backtest 研究演示。
- 审计记录与策略版本化说明。
- 面向熟人、内部团队、合作研究用户的私测。

不允许：

- 不提供“买/卖”投资建议。
- 不保证收益。
- 不做真实下单。
- 不托管资金。
- 不开放用户 Python 策略代码执行。
- 不把 `light_stub` 或未充分验证的回测包装成真实绩效。
- 不作为自动荐股或自动交易系统宣传。

## 本轮目标

输出一份外部服务准备度与试点方案，回答：

1. 当前能对外提供什么服务？
2. 当前不能对外提供什么服务？
3. 邀请制试点用户是谁？
4. 试点前必须补哪些工程、合规、文案、数据和运营条件？
5. 如何证明试点没有越界成投资建议或真实交易？
6. 什么时候可以从邀请制试点升级到更公开的 beta？

## 必须输出

### 1. Service Readiness Verdict

给出明确结论，只允许三类之一：

- `NO_GO`: 不能对外。
- `CONTROLLED_PILOT_ONLY`: 只能邀请制试点。
- `PUBLIC_BETA_READY`: 可公开 beta。

按当前 Codex 裁决，默认应为 `CONTROLLED_PILOT_ONLY`。如果你认为不是，必须给出非常具体的证据。

### 2. Allowed Services

列出当前允许对外提供的服务，并对每项标注：

- 用户任务。
- 系统能力。
- 输出物。
- 必须展示的免责声明。
- 是否需要审计记录。
- 是否能收费。

### 3. Prohibited Services

列出当前禁止提供的服务，并说明原因：

- 投资建议。
- 荐股/买卖点承诺。
- 真实下单。
- 资金托管。
- 自动交易。
- 用户 Python 策略执行。
- 未经验证的 LLM 生成代码执行。
- 把 stub/样例回测包装成真实绩效。

### 4. Pilot User Profile

定义邀请制试点用户：

- 允许邀请的用户类型。
- 不允许邀请的用户类型。
- 用户进入试点前需要确认的前提。
- 用户需要签收/确认的风险提示。

### 5. Pilot Service Flow

给出完整试点流程：

1. 用户提交中文策略想法。
2. 系统生成 DSL 和人类解释。
3. 系统执行 red-line 检查。
4. 系统展示 preview。
5. 系统执行 Light Backtest。
6. 系统输出报告。
7. 系统写入 audit。
8. 用户决定是否修改策略。

每一步都必须写清：

- 用户看到什么。
- 系统内部做什么。
- 是否出现投资建议风险。
- 如何避免越界。
- 是否必须落库审计。

### 6. External Copy And Disclaimer

输出对外服务文案：

- 允许使用的一句话介绍。
- 允许使用的一段服务说明。
- 禁止使用的宣传话术。
- 回测结果免责声明。
- AI/Agent 输出免责声明。
- 风险提示最低文案。

### 7. Engineering Go/No-Go Checklist

列出试点前必须满足的工程检查：

- MVP acceptance command 通过。
- 所有输出标注 research / paper / non-advice。
- `light_stub` 或 mock 结果不得出现在外部报告中，除非明显标注为演示。
- 每次生成/校验/预览/回测都有 `trace_id` 和 audit。
- 禁止用户上传或执行 Python 代码。
- 用户输入、DSL、报告、审计记录可追踪。
- 错误信息不能泄露内部路径、token 或数据库结构。

### 8. Compliance And Legal Review Checklist

列出需要律师/合规确认的问题：

- 服务是否构成投资顾问/证券投资咨询。
- 是否可以收费。
- 是否可以面向不特定公众。
- 文案是否可能被理解为投资建议。
- 用户协议、免责声明、隐私政策、数据授权。
- 目标市场为中国/美国/香港/其他地区时的差异。

### 9. Upgrade Criteria

定义从邀请制试点升级到 public beta 的条件：

- 真实 Light Backtest 替代 stub。
- 服务文案通过合规复核。
- 至少 N 个试点用户完成闭环。
- 所有试点记录可审计。
- 故障/误解/投诉有处理机制。
- GitHub/Obsidian 同步纪律执行。

### 10. First Pilot Plan

给出第一轮最小试点计划：

- 试点人数。
- 用户来源。
- 时间范围。
- 只开放哪些功能。
- 不开放哪些功能。
- 成功标准。
- 停止标准。
- 试点后复盘模板。

## 输出文件

请写入：

`data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`

## 输出格式

```markdown
# External Service Readiness And Pilot Plan

## Service Readiness Verdict

## Allowed Services

## Prohibited Services

## Pilot User Profile

## Pilot Service Flow

## External Copy And Disclaimer

## Engineering Go/No-Go Checklist

## Compliance And Legal Review Checklist

## Upgrade Criteria

## First Pilot Plan

## Risks

## Next Steps For Codex
```

## 验收标准

- 结论明确，不含模糊话术。
- 默认结论为 `CONTROLLED_PILOT_ONLY`，除非有证据支持升级或降级。
- 所有服务边界都能映射到用户任务和系统能力。
- 禁止项明确覆盖投资建议、真实下单、资金托管、自动交易和代码执行。
- 包含对外文案与免责声明。
- 包含工程 go/no-go checklist。
- 包含合规/法律复核 checklist。
- 包含第一轮试点计划。
- 产出后更新 Obsidian，并按 K10 同步纪律给出 GitHub handoff。

## 不做什么

- 不给法律意见。
- 不承诺合规。
- 不新增代码。
- 不新增真实交易能力。
- 不包装为自动荐股或自动赚钱产品。
- 不把 `light_stub` 当作真实绩效。
- 不替 Codex 做最终上线决策。
