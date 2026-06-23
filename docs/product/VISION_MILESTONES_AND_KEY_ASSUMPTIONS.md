# Hermass Vision, Milestones, And Key Assumptions

## 背景

本文件参考 S 级私董会的成长逻辑，重新定义 Hermass 的愿景、里程碑和关键假设。

S 级私董会给我们的可迁移经验不是“做活动”，而是：

- 用分层加速场匹配不同成熟度的问题。
- 用公共契约约束参与者预期和行为。
- 用案主机制让真实问题成为系统输入。
- 用标准流程、角色分工和复盘沉淀共同体资产。
- 不把系统做成一次性消费品，而做成长期协作网络。

Hermass 对应的核心判断：

> Hermass 不是自动荐股工具，也不是交易机器人，而是 AI 原生的量化策略研究共同体与审计系统。

## 愿景

Hermass 要成为个人和小团队的 AI 量化研究操作系统：

中文策略想法可以被结构化，研究假设可以被验证，风险红线不可绕过，回测和证据可以被审计，Agent 和人类围绕同一套 DSL、数据和证据持续迭代。

一句话定位：

> 把投资者的策略想法，变成可验证、可审计、可复盘、可协作的研究资产。

## 不做什么

- 不做自动荐股。
- 不做买卖建议。
- 不做收益承诺。
- 不做真实下单。
- 不做资金托管。
- 不执行用户或 LLM 生成的 Python 策略代码。
- 不把 mock、synthetic、`light_stub` 或未过真实 baseline 的指标包装成真实绩效。

## 借鉴 S 级私董会的产品结构

S 级私董会把人按问题成熟度和参与强度分为 S1/S2/S3/S4。Hermass 也不应该一上来服务所有人，而应按研究成熟度分层。

| S 级私董会机制 | Hermass 映射 | 目标 |
|---|---|---|
| S1 路演私董会：讲清业务，问清业务 | H1 Strategy Structuring Lab | 让用户把策略讲清楚，形成合法 DSL |
| S2 问题私董会：梳理真问题，出口式咨询 | H2 Strategy Diagnosis Lab | 用红线、preview、audit 找到策略问题 |
| S3 全案私董会：ABCD 假设全案梳理 | H3 Strategy Evidence Lab | 围绕策略假设、数据、回测、交易证据做全案研究 |
| S4 战略私董会：复杂战略决策 | H4 Portfolio Governance Lab | 面向多策略、多周期、多 Agent 的组合治理 |

关键原则：

- 不是 H 数字越高越好，而是越匹配当前问题越有效。
- 所有层级都必须遵守 DSL-first、red-line-first、audit-first。
- H4 之前不做真实交易和投资建议。

## 用户分层

### H1 Strategy Structuring Lab

适合：

- 有策略想法但说不清楚的人。
- 想把中文想法转成结构化 DSL 的用户。
- 需要训练“策略表达基本功”的研究者。

核心交付：

- 中文输入。
- DSL v2。
- 人类可读解释。
- schema/Pydantic 校验。
- 红线结果。

成功标准：

- 用户能在 3 分钟内把一个策略想法变成合法 DSL。
- 缺少止损、仓位过大等错误能被明确指出。

### H2 Strategy Diagnosis Lab

适合：

- 已有策略结构，但不知道哪里不严谨的人。
- 需要快速判断条件是否可预览、是否命中、是否缺数据的人。

核心交付：

- 条件命中预览。
- preview support / context requirement。
- red-line failure reason。
- audit timeline。

成功标准：

- 用户能知道一个策略为什么不能进入回测。
- 用户能知道哪些条件是 fully supported，哪些需要 backtest context。

### H3 Strategy Evidence Lab

适合：

- 愿意用真实数据、回测、交易证据来验证策略假设的人。
- 能接受策略不是“灵感”，而是“假设-证据-复盘”循环的人。

核心交付：

- `light_real_v1`。
- 交易明细。
- entry/exit/hold event evidence。
- 多周期 state 和指标快照。
- data readiness / benchmark gate。

成功标准：

- 每一笔交易都能解释“为什么进、为什么出、当时状态是什么”。
- 回测结果能追溯到数据版本、DSL 版本和 trace_id。

### H4 Portfolio Governance Lab

适合：

- 已经有多个策略、多个市场状态、多个 Agent 观点需要治理的人。
- 需要组合层风险、版本对比、策略淘汰和复盘机制的人。

核心交付：

- 多策略组合视图。
- Agent Debate DAG。
- Risk Guardian 常驻反方。
- 策略版本树。
- 组合级审计和复盘。

成功标准：

- 用户能知道哪些策略在什么市场状态下有效或失效。
- Agent 输出不能绕过数据证据和红线检查。

## 里程碑

### M0: MVP 信任底座

目标：

证明“中文策略输入 -> DSL -> 校验 -> 红线 -> preview -> stub backtest -> audit”是确定性可运行链路。

当前状态：

- 已完成。
- MVP acceptance：`5/5 cases passed`。
- Strategy Lab tests：最新本地为 `278 passed, 1 warning`。

里程碑门槛：

- 3 个冻结中文策略样例稳定通过。
- 2 个红线失败样例稳定拒绝。
- 每次 generation / validation / preview / backtest 都有 audit。

### M1: Synthetic Real-Light Baseline

目标：

证明 `light_real_v1` 在 synthetic fixture 下能完成非 stub 回测，并生成 trades / metrics / evidence 的工程链路。

当前状态：

- 首版实现已完成。
- Qoder hardening 5 个 blocker 已由 Codex 修复。
- 允许 internal synthetic smoke release；真实 DB 就绪前不可对外宣称为真实绩效。

已解决 blocker：

- ✅ real mode 缺 DB 时返回 `BT_DATA_DB_NOT_FOUND` + `status=failed`，不再静默 fallback stub。
- ✅ 多 symbol 日期级执行语义改为 `date ASC, symbol ASC` 排序，保证组合权益曲线正确。
- ✅ real E2E 的 trade/event evidence 可落库。
- ✅ `volume_ratio OR volume_ma_N` provider 契约闭合。
- ✅ API 截断元数据（`daily_curve_total_count`、`trades_truncated`）已加入 `BacktestResponse`。

持续阻塞：

- `data/p116_foundation.duckdb` 不存在。
- `data/state_cube.duckdb` 不存在。
- 真实 benchmark gate（5000 symbols x 252 days）未跑。

### M2: Real Data Baseline

目标：

在真实本地 DuckDB 上跑通 5000 symbols x 252 trading days 的 validation + benchmark gate。

当前状态：

- 阻塞。
- `data/p116_foundation.duckdb` 不存在。
- `data/state_cube.duckdb` 不存在。

门槛：

- `validate_real_data.py`：`ok=true`，`errors=[]`。
- Light Backtest total P50 < 20s。
- Light Backtest total P95 < 30s。
- Data load P95 < 10s。
- Signal generation P95 < 12s。
- Equity + metrics P95 < 8s。
- Peak memory < 4096MB。
- Failure count = 0。

### M3: Controlled Pilot

目标：

允许 5-20 个受控用户使用 Hermass 做研究，不公开商业化。

门槛：

- 真实 baseline 或明确标注的 synthetic/stub 边界。
- 用户签收免责声明。
- UI/报告显著标注 not investment advice。
- 所有报告含 trace_id、data_cutoff_date、mode、risk_flags。
- 试点用户理解“研究工具，不是交易建议”。

### M4: Public Beta

目标：

面向更广泛用户开放研究工具，但仍不提供投资建议和真实交易。

门槛：

- 至少 5000 symbols x 3 years。
- 数据 freshness <= 7 calendar days。
- license_status 允许 public beta。
- 幸存者偏差、复权、停牌退市、涨跌停、未来函数全部有显式处理。
- 有 SECURITY.md、CI、release notes、用户协议、免责声明。

### M5: Research Community / Quant Private Board

目标：

形成围绕策略研究的长期共同体，而不是一次性工具。

机制：

- H1/H2/H3/H4 分层研究场。
- 案主机制：用户提交一个真实策略假设作为案。
- NPC/Agent 角色：Risk Guardian、Backtest Critic、Strategy Designer、Review Agent。
- 结营复盘：策略假设是否被验证、是否失败、失败原因是否沉淀。
- 贡献记录：高质量 DSL、数据修复、因子验证、benchmark 结果进入项目资产。

## 关键假设

### H-A: 用户真的需要“把策略讲清楚”

假设：

很多用户不是缺回测工具，而是缺少把策略想法结构化表达的能力。

验证方式：

- 10 个目标用户中至少 7 个能在首次使用中提交中文策略。
- 至少 5 个用户认为 DSL 结构化比直接写代码更容易开始。

失败信号：

- 用户持续要求直接荐股或买卖点。
- 用户不愿意看 DSL，只想要收益率。

### H-B: 红线检查能建立信任，而不是增加摩擦

假设：

强制止损、仓位上限和审计会让高质量用户更信任系统。

验证方式：

- 试点用户对红线拒绝的理解率 >= 80%。
- 被拒绝策略中至少 50% 能被用户按提示修正。

失败信号：

- 用户觉得红线是“平台不够聪明”。
- 用户要求跳过红线。

### H-C: Audit 是核心资产

假设：

研究用户真正需要的是“我为什么这么改、当时数据是什么、结果如何”的可追溯链路。

验证方式：

- 试点用户会查看 audit timeline。
- 用户会引用 trace_id 讨论策略版本。

失败信号：

- 用户只看最终指标，不关心过程。
- audit 无法帮助定位错误或复盘。

### H-D: 真实交易证据比漂亮指标更重要

假设：

当用户看到每笔 entry/exit 的多周期 state、指标快照和触发条件后，会更愿意相信系统。

验证方式：

- 试点用户能解释至少 3 笔交易的进出理由。
- 用户会基于 evidence 修改策略，而不是只调参数追收益。

失败信号：

- 用户只要求提高收益率。
- evidence 看不懂或无助于决策。

### H-E: 分层研究场比单一产品更适合成长

假设：

像 S 级私董会一样，用户需要按成熟度进入不同场域，而不是所有人用同一个入口。

验证方式：

- H1 用户主要关心表达和 DSL。
- H2 用户主要关心诊断和 preview。
- H3 用户主要关心证据和真实回测。
- H4 用户主要关心组合治理。

失败信号：

- 用户群需求高度混杂，分层无法解释差异。
- 每个层级都想要同一个“荐股按钮”。

### H-F: 社区贡献可以形成数据和方法论飞轮

假设：

高质量用户愿意贡献策略样例、数据质量反馈、因子验证和 benchmark 结果。

验证方式：

- 每 10 个试点用户至少产生 3 条可沉淀贡献。
- 每周至少有 1 条贡献进入 docs / examples / tests / decisions。

失败信号：

- 用户只消费结果，不贡献反馈。
- 贡献无法标准化沉淀。

## 当前最高优先级

1. 修复 Qoder hardening review 中的 real baseline blockers。
2. 准备真实 DB baseline 数据。
3. 明确 synthetic release、real baseline release、pilot/public beta 的边界。
4. 在 README 中更新 Phase 2 当前状态，避免继续写 `light_stub` 已是唯一回测形态。
5. 设计 H1/H2/H3/H4 的用户进入诊断表和公共契约。

## 项目契约

Hermass 的公共契约应继承 S 级私董会的精神，但换成量化研究语境：

1. 我理解 Hermass 是策略研究工具，不是投资建议服务。
2. 我不会把系统输出当作买卖指令。
3. 我接受所有策略必须经过 DSL、红线、preview/backtest 和 audit。
4. 我不会要求跳过止损、仓位、审计等安全约束。
5. 我会区分 stub、synthetic、real baseline 和 production 数据。
6. 我提交的数据和策略样例必须有合法来源。
7. 我愿意围绕事实、假设、证据和复盘讨论策略。
8. 我理解回测不代表未来收益。
9. 我不会用 Hermass 进行募资、荐股、带单或误导他人交易。
10. 我愿意把高质量研究沉淀为共同体资产。

## 北极星指标

短期北极星：

> 每周新增可审计策略研究闭环数。

定义：

一次闭环必须包含 DSL、validation、red_line_result、preview/backtest、audit trace。

中期北极星：

> 每周新增可复盘交易证据数。

定义：

一条交易证据必须包含 entry/exit/hold event、triggered_conditions、timeframe_states、indicator_snapshot。

长期北极星：

> 被真实用户复用的策略研究资产数。

定义：

被不同用户复用、改造、引用或进入 examples/tests/docs 的 DSL、因子、数据契约或复盘模板。
