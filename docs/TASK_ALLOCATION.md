# Agent Task Allocation

## 当前总目标

把最终实施方案压缩成 Phase 0/1 MVP，并建立可复用协作机制。

新增战略目标：
- 扩展高配因子库，但先做 Factor Registry 和评估闭环，不直接堆未验证因子。
- 因子/Block 库设计原则：重点清晰、准备完备、架构灵活。
- 因子来源必须广泛覆盖成熟项目、机构研究、基本面、消息面、心理面、资金流、订单流和交易方法论，并通过 evidence level 管理。

## Qoder 任务

### Q1: DSL v2 MVP Schema

交付：
- `strategy_id/name/schema_version/entry/filters/exit/risk/evaluation/execution/provenance` 字段定义。
- Pydantic 模型草案。
- JSON Schema 草案。
- 10 条合法/非法样例。

验收：
- 缺少 `exit` 拒绝。
- 缺少止损拒绝。
- `max_position_pct > 0.25` 拒绝。

状态：已完成，Codex 已复核。

复核证据：
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`
- 结果：110 passed, 1 warning。
- `py_compile` 通过。
- AC1/AC2/AC3 烟测通过。

### Q2: 条件注册表 MVP

交付：
- P0 条件类型列表。
- 每个条件的参数 schema。
- 条件是否可用于 entry/filter/exit。
- 对应 DuckDB 字段依赖。

验收：
- 至少覆盖 MA 交叉、State、Volume、Industry、Stop Loss。

状态：已完成，Codex 已复核。

已覆盖：
- `ma_golden_cross`
- `ma_death_cross`
- `price_cross_ma`
- `state_hex_in`
- `state_ef_count`
- `volume_ratio`
- `industry_include`
- `industry_exclude`
- `stop_loss_pct`
- `take_profit_pct`
- `limit_up_filter`

### Q3: Strategy Lab API MVP

交付：
- `/generate`
- `/validate`
- `/preview`
- `/backtest`
- `/backtest/{id}`

验收：
- 每个 API 有请求/响应 schema。
- 每个 API 标注业务逻辑所在 service 文件。

状态：Qoder 已完成 Phase 1 设计，Codex 已复核，待实现。

交付：
- `agents/PHASE1_API_PREVIEW_DESIGN.md`

采纳结论：
- `ConditionSpec` 应增加字段/表依赖元数据。
- Phase 1 只建 `user_strategies`、`strategy_versions`、`strategy_backtests`、`strategy_audit_log`。
- Web 路由只做参数解析和 service 调用。
- Preview 必须先过 DSL 校验和红线检查，禁止 `SELECT *`。

需修正后再实现：
- Qoder 设计中把 `stop_loss_pct` 依赖 `positions` 并在 MVP Preview 中拒绝，这会破坏“合法止损策略可预览”的 MVP 链路。
- Codex 裁决：`stop_loss_pct` 在 Phase 1 Preview 中不应导致整体拒绝；应标记为 `requires_position_context`，在 mock 模式给 deterministic 估算，在 DuckDB preview 中只预览 entry/filter，exit stop loss 留给 backtest/positions 上下文。

下一轮任务：
- `agents/QODER_NEXT_TASK_PHASE1_IMPLEMENTATION_PATCH.md`

状态更新：
- Qoder 已完成 patch spec，文件：`agents/PHASE1_IMPLEMENTATION_PATCH_SPEC.md`。
- Codex 采纳 `preview_support/context_requirements` 作为 Phase 1 实现基础。
- Phase 1 实现下一步可启动。

下一轮任务 2：
- `agents/QODER_NEXT_TASK_PHASE1_CODE_PATCH.md`

### Q4: 2026-06-08 MVP E2E 样例 Contract

交付：
- 冻结 3 个中文策略样例。
- 为每个样例给出期望 DSL v2 完整 JSON。
- 定义本周中文输入到 DSL 的确定性映射规则。
- 定义 E2E runner 的 service-level 接口。
- 定义 Light Backtest 本周最小指标口径。
- 定义同一 `trace_id` 下的 audit operation 顺序。
- 定义主链路问题清单模板。

验收：
- Codex 能按 contract 实现 `中文策略输入 -> DSL -> 校验 -> Preview -> Light Backtest -> Audit` 的样例级 runner。
- `MA5上穿MA20买入，跌破MA10卖出，止损8%` 能生成合法 DSL。
- 缺少止损和仓位超过 25% 的样例能被红线拒绝并留下 audit。
- 3 个样例能在 mock preview 下稳定返回命中数量。
- Light Backtest 允许本周使用 stub/light_mock，但必须写入 storage 和 audit，且不得伪装成真实绩效。

下一轮任务：
- `agents/QODER_NEXT_TASK_2026_06_08_E2E_SAMPLES.md`

## Kimi 任务

### K1: Light Backtest 性能基准

交付：
- DuckDB/Polars 分工建议。
- 基准测试数据规模。
- P50/P95 指标。
- 最小 benchmark 脚本设计。

验收：
- 能回答 5000 品种 252 天 <30s 是否可行。

状态：已完成研究方案，等待可运行 benchmark 脚本和真实基线数据。

采纳结论：
- Phase 2 默认采用 DuckDB 取数 + Polars 信号/权益曲线/绩效指标。
- Light Backtest <30s 现实，但必须避免 Python 逐行循环。
- `filter_first` 作为信号稀疏策略的默认优化方向。

### K2: Foundation DB 指标预计算建议

交付：
- MVP 必需预计算指标。
- 查询字段清单。
- 缓存策略。

验收：
- 能支持 P0 条件注册表，不需要运行时重复计算所有 MA。

状态：已完成研究方案，进入 MVP 数据要求。

采纳结论：
- 预计算 `ma_5/10/20/60`、`bb_position`、`atr_14`、`volume_ratio`、`adx_14`、`d1_state/w1_state/mn1_state`。
- 非标准 MA 参数进入后续动态缓存 backlog，不进入 MVP。

### K3: 产业链 Agent 最小版本

交付：
- 不依赖完整知识图谱的产业链数据结构。
- 行业/概念/上下游映射表设计。
- Agent 输入输出 contract。

验收：
- 能在 Phase 3 作为只读 Agent 接入，不影响 Phase 1/2。

状态：已完成研究方案，放入 Phase 3。

采纳结论：
- 先用静态 JSON 行业链映射 + State Cube 聚合。
- Kuzu 知识图谱、LLM 动态抽取、产业链因果推理全部进入 research backlog。

### K4: 可运行 Benchmark 脚本

交付：
- `benchmarks/light_backtest_perf.py`
- `benchmarks/indicator_precompute_vs_compute.py`
- `benchmarks/duckdb_vs_polars.py`
- `benchmarks/state_cube_query.py`

验收：
- 输出 JSONL 到 `outputs/benchmarks/`。
- 每个 benchmark 至少记录 P50/P95、数据规模、硬件、执行时间拆分。
- 真实数据不可用时，先提供 synthetic fixture，但标注不可作为最终性能承诺。

状态：新增任务。

状态：已完成，Codex 已复核。

交付：
- `benchmarks/light_backtest_perf.py`
- `benchmarks/indicator_precompute_vs_compute.py`
- `benchmarks/duckdb_vs_polars.py`
- `benchmarks/state_cube_query.py`
- `benchmarks/_synthetic.py`
- `benchmarks/README.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-benchmark-scripts.md`

复核命令：
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --output outputs/benchmarks/light_backtest_synthetic.jsonl`
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --output outputs/benchmarks/indicator_synthetic.jsonl`
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --output outputs/benchmarks/duckdb_vs_polars_synthetic.jsonl`
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --output outputs/benchmarks/state_cube_synthetic.jsonl`

复核结果：
- 4 个脚本均顺序运行通过。
- JSONL 字段完整。
- 注意：初次复核发现并行运行会竞争同一个 synthetic DuckDB 临时文件；Codex 已修复为进程级唯一临时库路径。

### K5: 真实数据 Benchmark Runbook

交付：
- 真实数据前置体检流程。
- `benchmarks/validate_real_data.py` 脚本规格。
- Phase 2 hot path gates。
- CI/本地验收策略。
- 对现有 benchmark 的改进建议。

验收：
- 能指导 Codex 在 `p116_foundation.duckdb` 和 `state_cube.duckdb` 就绪后跑出真实基线。
- 明确 synthetic smoke 与 real benchmark 的区别。

状态：已完成 runbook，已演进为 Phase 3 handoff。

状态更新：
- Kimi 已完成 runbook，文件：`data/research/conversations/agent-runs/2026-06-06-kimi-real-data-benchmark-runbook.md`。
- Codex 采纳 Hot Path Gates 作为 Phase 2 性能验收基线。
- 后续需实现 `benchmarks/validate_real_data.py`，并改进 benchmark 分阶段计时、`--symbols/--days/--runs` 参数。
- 已演进为 Phase 3 真实数据 baseline handoff，任务文件：`agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`。

下一轮任务：
- `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`

### K6: 高配因子库研究

交付：
- 50+ 候选因子优先级。
- A 股数据可得性。
- 因子评估框架。
- F0/F1/F2 路线。

验收：
- 明确哪些因子进入 MVP+，哪些进入 research backlog。
- 每个候选因子有数据依赖和风险。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_FACTOR_LIBRARY_RESEARCH.md`

状态更新：
- Kimi 已完成，文件：`data/research/conversations/agent-runs/2026-06-06-kimi-factor-library-research.md`。
- 输出：55 个候选因子，Tier 1 MVP+ Ready 20 个、Tier 2 High Value Next 20 个、Tier 3 Research Backlog 15 个。
- Codex 采纳为早期高配因子库研究资产；后续以更严格的 F1 30 条目录和 registry gate 为工程落地准绳。

### K7: StrategyQuant X B143 Block 研究

交付：
- 120+ 候选 block。
- Factor vs Block 边界。
- A 股适配风险。
- 高配优先级。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_STRATEGYQUANT_FACTOR_BLOCKS_RESEARCH.md`

### K8: 广义因子来源研究

交付：
- 200+ factor/block 候选。
- 来源图谱。
- 交易方法论拆解。
- 数据缺口。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_BROAD_FACTOR_SOURCE_RESEARCH.md`

状态更新：
- Kimi 已完成，文件：`data/research/conversations/agent-runs/2026-06-06-kimi-broad-factor-source-research.md`。
- 候选数：278 条 factor/block。
- Codex 裁决：进入 research catalog，不直接进入 production DSL。

下一轮任务：
- `agents/KIMI_NEXT_TASK_FACTOR_CATALOG_CURATION.md`

### K9: 产品最终目标与服务边界澄清

交付：
- `agents/KIMI_NEXT_TASK_PRODUCT_SCOPE_SERVICE_BOUNDARY.md`
- `data/research/conversations/agent-runs/2026-06-10-kimi-product-scope-service-boundary.md`

验收：
- 明确最终产品不是自动荐股/自动交易系统，而是 DSL-first 的 AI 量化策略实验与审计平台。
- 明确 P0/P1/P2 用户，以及非目标用户。
- 明确 MVP Services、P1 Services、Explicit Non-Services。
- 明确 P0 用户 MVP journey，每一步包含用户看到什么、系统内部做什么、失败提示和审计要求。
- 明确服务文案红线，避免回测结果或 Agent 评审被误解为收益承诺或投资建议。
- 明确工程影响：哪些 API/UI/audit 字段必须优先，哪些 Kimi 研究成果进入 backlog 而不阻塞 MVP。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_PRODUCT_SCOPE_SERVICE_BOUNDARY.md`

### K10: GitHub 与 Obsidian 及时同步纪律

交付：
- `agents/KIMI_NEXT_TASK_GITHUB_OBSIDIAN_SYNC_DISCIPLINE.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-github-obsidian-sync-discipline.md`

验收：
- 明确哪些内容应同步 GitHub，哪些内容不得进 GitHub。
- 明确哪些内容应同步 Obsidian Vault，哪些内容不得进 Vault。
- 给出每次 Kimi 交付后的 GitHub sync checklist 与 Obsidian sync checklist。
- 给出 Kimi 无 GitHub push 权限时的 handoff 模板。
- 对当前工作区做一次同步审计，分类未提交文件并标注建议提交/忽略/补记录事项。
- 不把 `outputs/`、临时 DuckDB、缓存或敏感凭据作为同步交付物。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_GITHUB_OBSIDIAN_SYNC_DISCIPLINE.md`

状态更新：
- Kimi 已完成同步纪律文档，文件：`data/research/conversations/agent-runs/2026-06-11-kimi-github-obsidian-sync-discipline.md`。
- Codex 初步复核：文档包含 Sync Policy、GitHub/Obsidian checklist、cadence、handoff template 和当前 dirty worktree 同步审计。
- 审计结论采纳：`outputs/` 已被 `.gitignore` 覆盖；`6月8日工作计划.MD` 建议不提交；`dsl_schema.py` 约束放宽已在 `2026-06-08-codex-mvp-e2e-runner-acceptance.md` 记录 follow-up review。

### K11: 对外服务准备度与邀请制试点方案

Codex 判断：
- 当前可以对外提供服务，但只能做受控、邀请制、研究用途试点。
- 当前不能公开商业化开放，不能提供投资建议、自动荐股、真实下单、资金托管或收益承诺。

交付：
- `agents/KIMI_NEXT_TASK_EXTERNAL_SERVICE_READINESS_PILOT.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`
- `data/research/conversations/decisions/0010-external-service-readiness.md`

验收：
- 给出明确 readiness verdict，默认应为 `CONTROLLED_PILOT_ONLY`。
- 列出当前允许对外提供的服务和明确禁止服务。
- 定义邀请制试点用户画像、进入前提和风险确认。
- 给出试点服务流程，每一步说明用户看到什么、系统做什么、是否有投资建议风险、如何避免越界、是否审计。
- 给出对外介绍文案、禁止宣传话术、回测免责声明、AI/Agent 输出免责声明、风险提示最低文案。
- 给出工程 go/no-go checklist 和法律/合规复核 checklist。
- 给出从邀请制试点升级到 public beta 的条件。
- 给出第一轮最小试点计划。
- 按 K10 同步纪律写入 Obsidian 并提供 GitHub handoff。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_EXTERNAL_SERVICE_READINESS_PILOT.md`

状态更新：
- Kimi 已完成外部服务准备度与试点方案，文件：`data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`。
- Kimi 结论：`CONTROLLED_PILOT_ONLY`，当前只允许 5 人/2 周的邀请制研究试点，禁止公开商业化、投资建议、真实下单、资金托管、自动交易和收益承诺。
- Codex 采纳方向：公开增长前必须先解决 service boundary、免责声明、真实 Light Backtest 与 GitHub 开源成熟度。

### K12: GitHub 多星增长与开源成熟度计划

Codex 判断：
- 当前 GitHub stars 为 `0`，仓库公开但不具备自然增长条件。
- 先完成仓库成熟化，再做 soft launch；禁止刷星、买星或用投资收益话术引流。

交付：
- `agents/KIMI_NEXT_TASK_GITHUB_STARS_GROWTH_PLAN.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-github-stars-growth-plan.md`

验收：
- 给出 star readiness verdict，默认应为 `NOT_READY_TO_PROMOTE`。
- 审计当前仓库首页、README、license、topics、demo、quickstart、roadmap、disclaimer、release 等缺口。
- 定义合规安全的开源定位：DSL-first、red-line-first、audit-first、not investment advice、no real trading。
- 输出 P0/P1/P2 GitHub improvement backlog。
- 给出 README rewrite outline，能直接交给 Codex 实施。
- 给出 repository description、topics、license 选项和 release 建议。
- 给出保守 star targets：0->5、5->20、20->100、100+。
- 给出 soft launch plan 和 compliance-safe copy。
- 按 K10 同步纪律写入 Obsidian 并提供 GitHub handoff。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_GITHUB_STARS_GROWTH_PLAN.md`

### KIMI2-1: 数据刷新 / 补充 / 替换必要性审计

Codex 判断：
- MVP 样例级链路可以继续使用 deterministic mock / synthetic preview，不因真实数据缺口阻塞。
- 真实 Light Backtest、邀请制试点、GitHub demo 和 public beta 前，必须完成数据新鲜度、覆盖率、偏差、授权和 `light_stub` 标注审计。
- 当前不应默认“换数据源”，应逐类判断 `freeze`、`refresh`、`supplement`、`replace` 或 `defer`。

交付：
- `agents/KIMI2_NEXT_TASK_DATA_REFRESH_REPLACEMENT_AUDIT.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi2-data-refresh-replacement-audit.md`

验收：
- 给出总 verdict：`NO_CHANGE_FREEZE` / `REFRESH_REQUIRED` / `SUPPLEMENT_REQUIRED` / `REPLACE_REQUIRED` / `MIXED`。
- 盘点 `p116_foundation.duckdb`、`state_cube.duckdb`、`market_assets.duckdb`、Blackwolf daily、Blackwolf moneyflow、factor registry、synthetic fixture、mock preview 和 `light_stub` 输出。
- 对每类数据给出 `freeze` / `refresh` / `supplement` / `replace` / `defer` 决策矩阵。
- 明确哪些数据缺口阻塞 MVP、Phase 2 真实回测、邀请制试点、public beta。
- 给出真实 Light Backtest 前的数据契约和验证命令。
- 覆盖数据过旧、未来函数、复权口径、幸存者偏差、停牌退市、行业分类漂移、授权风险和 mock 被误解风险。
- 按 K10 同步纪律输出 GitHub / Obsidian handoff。

状态：已完成审计，结论为真实 DB 缺失阻塞 real baseline，不阻塞 MVP/Web UI。

状态更新：
- Kimi 已完成审计，文件：`data/research/conversations/agent-runs/2026-06-11-kimi2-data-refresh-replacement-audit.md`。
- 结论：`data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 均不存在；real baseline 继续阻塞，MVP stub/synthetic path 与 Phase 3 Web UI 不受影响。
- 已演进为 Phase 3 真实数据 baseline handoff，任务文件：`agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`。

任务文件：
- `agents/KIMI2_NEXT_TASK_DATA_REFRESH_REPLACEMENT_AUDIT.md`
- `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`

### K13: GitHub 软启动准备度复核与首批传播包

Codex 判断：
- GitHub P0 成熟化已完成并推送：README、Apache-2.0 LICENSE、Topics、Description、examples、Issue templates、CONTRIBUTING 均已落地。
- 当前 stars 仍为 `0`，下一步不应直接 public launch，应先做私域/熟人软启动复核。
- KIMI2 数据审计尚未完成，因此任何传播都必须继续标注 `light_stub`，不能宣称真实回测能力。

交付：
- `agents/KIMI_NEXT_TASK_SOFT_LAUNCH_READINESS_OUTREACH_PACK.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-soft-launch-readiness-outreach-pack.md`

验收：
- 给出 soft launch readiness verdict：`NOT_READY` / `PRIVATE_SOFT_LAUNCH_READY` / `PUBLIC_SOFT_LAUNCH_READY` / `PUBLIC_LAUNCH_READY`。
- 复核 README、Quickstart、License、Description、Topics、examples、Issue templates、CONTRIBUTING、disclaimer 和 `light_stub` 标注。
- 定义本轮软启动边界：允许触达谁、不允许触达谁、可以说什么、不能说什么。
- 输出首批 20 人目标人群模板，不包含真实个人隐私。
- 输出中文/英文私信、朋友圈、X/LinkedIn、GitHub pinned issue 等合规文案。
- 给出 7 天反馈收集计划、成功标准、停止标准和红旗反馈。
- 输出软启动前后 Codex 工程 backlog，包括 demo、release、CI、badge、SECURITY.md 等。
- 按 K10 同步纪律输出 GitHub / Obsidian handoff。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_SOFT_LAUNCH_READINESS_OUTREACH_PACK.md`

### K14: 交易证据大数据库性能与聚合方案

Codex 判断：
- 策略大数据库必须先从交易证据库开始，记录每笔交易 entry/hold/exit 的多周期状态、指标快照和触发条件。
- 当前最小 storage schema 已落地，但大规模查询、JSON 展开、物化视图和聚合方案需要 Kimi 评估。

交付：
- `agents/KIMI_NEXT_TASK_TRADE_EVIDENCE_DATABASE_PERFORMANCE.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-trade-evidence-database-performance.md`

验收：
- 给出 1 万、10 万、100 万、1000 万事件规模假设。
- 定义按 strategy/trace/state/condition/indicator 查询的 P50/P95 目标。
- 比较 JSON 保留、宽表展开、物化视图的取舍。
- 给出 DuckDB/Polars 分工、索引、分区和 benchmark 脚本建议。
- 明确 Phase 2 / Phase 3 落地顺序。

状态：新增任务。

任务文件：
- `agents/KIMI_NEXT_TASK_TRADE_EVIDENCE_DATABASE_PERFORMANCE.md`

### K15: 真实数据下载与 DuckDB 构建

Codex 判断：
- 前两轮 Kimi 数据审计已确认 `data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 均不存在。
- Phase 3 Web UI 已落地，主线已切换到真实数据 baseline handoff。
- Kimi 本轮必须不再停留在审计/判断，而是实际下载数据、计算指标、构建两个 DuckDB 文件。

交付：
- `agents/KIMI_NEXT_TASK_DATA_DOWNLOAD_AND_BUILD.md`
- `data/p116_foundation.duckdb`（不提交 Git）
- `data/state_cube.duckdb`（不提交 Git）
- `outputs/benchmarks/data_readiness_status.json`
- `data/research/conversations/agent-runs/2026-06-19-kimi-data-download-build.md`

验收：
- 原始行情来源明确（黑狼或 AKShare/baostock 等免费备选），说明复权口径、数据覆盖范围和授权状态。
- `data/p116_foundation.duckdb` 包含 `daily_bars` 表，至少 5000 标的、252 交易日，必需列全部齐全。
- `data/state_cube.duckdb` 包含 `state_cube` 表，D1/W1/MN1 state 三周期均可查询。
- `benchmarks/validate_real_data.py` 通过（exit 0，`ok=true`，`errors=[]`）。
- `outputs/benchmarks/data_readiness_status.json` verdict 为 `READY` 或给出明确的 `PARTIAL` / `NOT_READY` 原因及 `next_steps`。
- `light_backtest_perf.py` 和 `gate_summary.py` 通过（若 validation 通过）。
- 所有产出物均有 handoff 记录。

状态：已完成。

Kimi 交付摘要（2026-06-19）：
- 数据源：黑狼（Blackwolf），复用 `blackwolf_ashare_daily_mm_format_20180515_20260618.zip`
- `data/p116_foundation.duckdb`：8,591,347 行，5,536 品种，1964 交易日，2018-05-15 ~ 2026-06-18
- `data/state_cube.duckdb`：8,591,347 行，5,536 品种
- `data_readiness_status.json`：verdict=READY，staleness_days=0
- `validate_real_data.py`：PASS，ok=true，errors=[]
- `light_backtest_perf`：5000×252 full_polars P50=1.97s，P95=2.12s（远低于 20s gate）
- `gate_summary`：PASS（8/8 gates）
- 回归：278 strategy_lab + 7 web_ui_smoke + 8 real_backtest_integration = 293 passed

Codex 集成验证（2026-06-19）：
- Web UI data_readiness 对接验证通过
- light_real_v1 默认切换生效：READY 时 diagnosis/evidence 页默认显示 light_real_v1
- 新增 2 个 smoke 端到端用例：`test_readiness_ready_shows_light_real_v1_on_diagnosis_page`、`test_readiness_not_ready_shows_light_stub_on_diagnosis_page`
- 全量测试通过：278 + 7 + 8 = 293 passed

任务文件：
- `agents/KIMI_NEXT_TASK_DATA_DOWNLOAD_AND_BUILD.md`
- `data/research/conversations/agent-runs/2026-06-19-kimi-data-download-and-build-run.md`

## Codex 任务

### C1: 项目协作资产

交付：
- `AGENTS.md`
- `agents/` 三个 Agent prompt。
- Obsidian Vault。
- 项目内 Skill。

验收：
- 新 Agent 可按文件快速接手项目。

### C2: Phase 0 工程骨架

交付：
- `hermass_platform/strategy_lab/` 骨架。
- DSL schema。
- condition registry。
- validator。
- migration SQL。
- 最小测试。

验收：
- py_compile 通过。
- DSL 合法/非法测试通过。

新增要求：
- condition registry 字段依赖必须覆盖 Kimi 采纳的预计算列。
- validator 要禁止需要未声明字段的条件进入回测。

状态：已实现并复核，但保留两个下一步修正点。

复核结果：
- 110 个 strategy_lab 测试通过。
- 8 个源文件 py_compile 通过。
- 最小 DSL 构造、校验、翻译烟测通过。

待修正：
- `pyproject.toml` 引用 `README.md` 的风险已修复。
- 条件注册表目前没有显式字段依赖属性，字段依赖由 translator 返回；后续 Phase 1/2 应考虑把字段依赖前移到 registry，便于 preview/backtest 提前拒绝非 MVP 字段。

### C5: 下一轮 Agent 派工

交付：
- `agents/QODER_NEXT_TASK_PHASE1_API_PREVIEW.md`
- `agents/KIMI_NEXT_TASK_BENCHMARKS.md`

验收：
- Qoder 有明确 Phase 1 API/Preview/DDL 任务。
- Kimi 有明确 benchmark 脚本任务。
- 两份提示词都包含验收命令或输出结构。

状态：已完成。

### C6: 下一轮 Agent 派工 2

交付：
- `agents/QODER_NEXT_TASK_PHASE1_IMPLEMENTATION_PATCH.md`
- `agents/KIMI_NEXT_TASK_REAL_DATA_BENCHMARK_RUNBOOK.md`

验收：
- Qoder 任务明确要求修正 stop loss preview context。
- Kimi 任务明确要求真实数据 runbook 和 Phase 2 hot path gates。

状态：已完成。

### C7: 下一轮 Agent 派工 3

交付：
- `agents/QODER_NEXT_TASK_PHASE1_CODE_PATCH.md`
- `agents/KIMI_NEXT_TASK_VALIDATE_AND_BENCHMARK_PATCH.md`

验收：
- Qoder 任务要求直接实现 Phase 1 metadata/api_models/preview_service 第一批代码。
- Kimi 任务要求直接实现 `validate_real_data.py` 和 benchmark CLI/分阶段计时改进。

状态：已完成。

状态更新：
- Qoder 已完成 Phase 1 API model / preview service 补丁，文件：`data/research/conversations/agent-runs/2026-06-06-qoder-phase1-code-patch.md`。
- Codex 已复核并修正两点：`PreviewService.input_hash` 改为 DSL 内容哈希；`ConditionSpec.resolve_required_columns()` 对齐 translator 字段名。
- 验收：`/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`，162 passed。
- 验收：`/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py`，通过。

下一轮任务：
- `agents/QODER_NEXT_TASK_PHASE1_DUCKDB_PREVIEW_STORAGE_AUDIT.md`

### C7.1: Phase 1 DuckDB Preview / Storage / Audit 派工

交付：
- `agents/QODER_NEXT_TASK_PHASE1_DUCKDB_PREVIEW_STORAGE_AUDIT.md`

验收：
- Qoder 实现真实 DuckDB preview provider，至少覆盖 MA、volume、limit_up、state 条件。
- Qoder 实现最小 `storage.py` 和 `audit.py`，支持 trace_id/input_hash/output_hash/red_line_result 落库。
- `stop_loss_pct` / `take_profit_pct` 继续不阻塞 preview，只标记 requires backtest context。

状态：已完成派工。

状态更新：
- Qoder 已完成实现记录，文件：`data/research/conversations/agent-runs/2026-06-07-qoder-phase1-duckdb-preview-storage-audit.md`。
- Codex 已复核并修正 DuckDB Preview SQL：窗口函数使用 `PARTITION BY symbol ORDER BY date`，QUALIFY 子查询使用 `SELECT 1`，不允许 `SELECT *`。
- 新增 `hermass_platform/strategy_lab/storage.py`、`hermass_platform/strategy_lab/audit.py` 和 DuckDB preview/storage/audit 测试。
- 验收：`/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`，188 passed。
- 验收：`/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py`，通过。

### C8: 高配因子库派工

交付：
- `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
- `agents/KIMI_NEXT_TASK_FACTOR_LIBRARY_RESEARCH.md`
- `agents/QODER_NEXT_TASK_FACTOR_LIBRARY_ARCHITECTURE.md`
- `data/research/conversations/decisions/0007-factor-library-expansion-direction.md`

验收：
- 高配因子库方向进入项目决策。
- Kimi/Qoder 有明确下一步。

状态：已完成。

### C9: StrategyQuant X B143 参考模型派工

交付：
- `docs/STRATEGYQUANT_XB143_REFERENCE_MODEL.md`
- `agents/KIMI_NEXT_TASK_STRATEGYQUANT_FACTOR_BLOCKS_RESEARCH.md`
- `agents/QODER_NEXT_TASK_BLOCK_LIBRARY_ARCHITECTURE.md`

验收：
- StrategyQuant X B143 的 building-block 思路进入项目资产。
- 因子库升级为 Factor + Block Library。

状态：已完成。

### C10: 因子/Block 库设计准则

交付：
- `docs/FACTOR_BLOCK_LIBRARY_DESIGN_PRINCIPLES.md`

验收：
- 明确重点清晰、准备完备、架构灵活。
- 明确 F0/F1/F2 落地顺序。
- 明确不盲目复制 SQX 548 blocks。

状态：已完成。

### C11: 广义因子来源治理

交付：
- `docs/FACTOR_SOURCE_TAXONOMY.md`
- `agents/KIMI_NEXT_TASK_BROAD_FACTOR_SOURCE_RESEARCH.md`
- `agents/QODER_NEXT_TASK_FACTOR_SOURCE_SCHEMA.md`

验收：
- 因子来源分类进入项目资产。
- evidence level 进入后续 schema 设计。

状态：已完成。

状态更新：
- Qoder 已完成 source/evidence schema，文件：`agents/FACTOR_SOURCE_SCHEMA.md`。
- Codex 已新增决策 `0008-broad-factor-source-evidence-governance.md`。

### C12: Factor Catalog / Registry 派工

交付：
- `agents/KIMI_NEXT_TASK_FACTOR_CATALOG_CURATION.md`
- `agents/QODER_NEXT_TASK_SOURCE_FACTOR_REGISTRY_CODE.md`

验收：
- Kimi 把 278 个广义候选压缩为 F0 source catalog、F1 30 个 MVP+ 条目、F2 70 个候选条目。
- Qoder 输出 Source/Evidence/Factor/Block registry 代码规格，明确 schema、registry API、YAML catalog 和测试计划。
- evidence gate、future leakage gate、data availability gate 明确进入工程规则。

状态：已完成。

状态更新：
- Kimi 已完成目录压缩，文件：`data/research/conversations/agent-runs/2026-06-06-kimi-factor-catalog-curation.md`。
- 结果：F0 12 sources、F1 30 items、F2 70 items、Research Backlog 178 items。
- Qoder 已完成 registry 代码规格，文件：`agents/SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`。
- Codex 裁决：采纳，但实现时 `source_type` 必须以 `agents/FACTOR_SOURCE_SCHEMA.md` 为 canonical，修正 Qoder spec 中的命名漂移。

### C13: Factor Formula / Registry Implementation 派工

交付：
- `agents/KIMI_NEXT_TASK_F1_FACTOR_FORMULA_CONTRACTS.md`
- `agents/QODER_NEXT_TASK_FACTOR_REGISTRY_IMPLEMENTATION_PATCH.md`
- `data/research/conversations/decisions/0009-factor-catalog-registry-accepted.md`

验收：
- Kimi 输出 F1 26 个 factor 的公式、输入列、输出列、Polars/DuckDB hint、预计算优先级。
- Qoder 实现 `hermass_platform/factors/` registry 第一版代码和 YAML catalogs。
- registry 测试覆盖 canonical source_type、evidence gate、future leakage gate、data availability gate、source_refs 校验。

状态：已完成派工。

状态更新：
- Kimi 已完成 F1 公式和数据契约，文件：`data/research/conversations/agent-runs/2026-06-06-kimi-f1-factor-formula-contracts.md`。
- Qoder 已实现 `hermass_platform/factors/` registry、`config/factors/*.yaml` catalogs 和测试。
- Codex 复核并修正 `EvidenceRegistry` 重复 evidence 异常类型，新增 `DuplicateEvidenceError`。
- 验收：`/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/factors/tests -q`，57 passed。
- 验收：`/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/factors/*.py`，通过。

### C14: Strategy Lab MVP E2E 验收入口

交付：
- `scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- `data/research/conversations/agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md`

验收：
- 3 个冻结中文策略样例全部走通 generation -> validation -> preview -> backtest。
- 缺少止损样例触发 `RL_EXIT_MUST_HAVE_STOP_LOSS`，且不执行 preview/backtest。
- 仓位 30% 样例触发 `RL_MAX_POSITION`，且不执行 preview/backtest。
- 每个样例保留同一 `trace_id` 下的 audit 记录。

状态：已完成。

复核命令：
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py --run-id final`
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`

复核结果：
- E2E acceptance：5/5 cases passed。
- Strategy Lab tests：197 passed, 1 warning。

### C15: GitHub 成熟化 P0/P1 基础资产

交付：
- `README.md`
- `CONTRIBUTING.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `docs/github/METADATA_RECOMMENDATIONS.md`
- `examples/strategy_lab/sample_ma_5_20_stop_8.json`
- `examples/strategy_lab/sample_state_volume_stop_8_take_15.json`
- `examples/strategy_lab/sample_ma_state_limit_filter.json`
- `hermass_platform/strategy_lab/tests/test_examples.py`
- `data/research/conversations/agent-runs/2026-06-11-codex-github-maturity-p0.md`

验收：
- README 能在 30 秒内说明项目是 DSL-first、red-line-first、audit-first 的策略研究框架。
- README Quickstart 不使用本机绝对 Python 路径。
- README 明确 `light_stub` 不是真实绩效，不提供投资建议、不荐股、不交易。
- 3 个公开 example DSL 文件能通过 `StrategyDSL` 和 `validate_dsl` 校验。
- GitHub Issue 模板和 CONTRIBUTING 明确禁止投资建议、真实交易、收益承诺。
- GitHub Description、Topics、License 的建议写入文档；用户已确认 Apache-2.0。

状态：已完成。Apache-2.0 已确认并落地，GitHub Description / Topics 已通过 GitHub API 更新。

复核命令：
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_examples.py -q`

复核结果：
- Strategy Lab tests：198 passed, 1 warning。
- E2E acceptance：5/5 cases passed。
- Example DSL tests：1 passed, 1 warning。

### C16: 交易证据库 MVP

交付：
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `data/research/conversations/decisions/0011-trade-evidence-database.md`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/tests/test_storage.py`
- `agents/QODER_NEXT_TASK_TRADE_EVIDENCE_BACKTEST_CONTRACT.md`
- `agents/KIMI_NEXT_TASK_TRADE_EVIDENCE_DATABASE_PERFORMANCE.md`

验收：
- 新增 `strategy_trades` 和 `strategy_trade_events` 表。
- 支持保存交易摘要。
- 支持保存 entry/exit/hold 事件证据。
- 事件证据能保存多周期 state、指标快照和触发条件 JSON。
- 支持按 `strategy_id` / `trace_id` 查询交易，按 `trade_id` 查询事件。

状态：新增并实现最小 schema，待复核。

下一轮任务：
- Qoder 设计真实 Light Backtest 写入交易证据的接口契约。
- Kimi 设计交易证据大数据库性能与聚合方案。

### C17: Phase 2 Light Backtest 推进派工

交付：
- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md`
- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-light-backtest-dispatch.md`

验收：
- Qoder 输出真实 Light Backtest 的可实现 contract，覆盖模块边界、接口签名、DSL 条件语义、DuckDB/Polars 分工、交易规则、审计/storage 写入和测试清单。
- Kimi 输出真实数据契约与性能门禁，覆盖 benchmark 能力缺口、`validate_real_data.py` 后续改进、5000 symbols x 252 days hot path gates、数据风险和同步 handoff。
- Codex 保持 MVP baseline 可运行，并记录当前验收命令。

状态：Qoder/Kimi 已回传，Codex 已采纳为 Phase 2 实现输入。

状态更新：
- Qoder 已完成 `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md` 和 `data/research/conversations/agent-runs/2026-06-11-qoder-phase2-light-backtest-contract.md`。
- Kimi 已完成 `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md` 和 `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-data-perf-gates.md`。
- Codex 裁决：采用 `backtest_adapter.py` facade + `backtest_models.py` / `backtest_data_provider.py` / `light_backtest_engine.py` / `backtest_metrics.py` 的模块拆分；真实回测模式标识固定为 `light_real_v1`。
- Codex 裁决：Kimi 的 Hot Path Gates 阻塞 Phase 2 real backtest 发布、真实指标试点升级、GitHub 真实指标 demo 和 public beta，但不阻塞 Phase 0/1 mock/stub 验收。
- Codex 裁决：`state_hex_d1` vs `d1_state` 字段分歧由 Phase 2 provider 做 alias 归一，registry/translator 不在本轮破坏性修改。

下一轮实现任务：
- Codex 第一批实现 `backtest_models.py`、`backtest_data_provider.py`、`light_backtest_engine.py` 和 synthetic integration fixture。
- Codex 扩展 `benchmarks/validate_real_data.py` P0 checks，并新增 gate summary。
- Qoder 后续只审阅 contract 偏差，不扩展 Agent Debate。
- Kimi 后续只跟进真实 DB baseline 和性能风险，不阻塞 stub MVP。

当前基线：
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`
- 结果：200 passed, 1 warning。
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- 结果：5/5 cases passed。
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py benchmarks/*.py`
- 结果：通过。

实现状态更新：
- Phase 2 Real Light Backtest 第一版已实现，新增 `backtest_models.py`、`backtest_data_provider.py`、`light_backtest_engine.py`、`backtest_metrics.py`、`backtest_evidence.py`。
- 已改造 `backtest_adapter.py`、`api_models.py`、`e2e_runner.py`、`storage.py` 和 `__init__.py`。
- 已新增 provider / engine / metrics / evidence / integration 测试。
- Codex 复核时补两处 contract 防线：`BacktestAdapter.run_backtest()` 入口强制 `validate_dsl()`，红线失败不读 DuckDB、不写 trades；`DuckDBBacktestDataProvider` 改为白名单列裁剪，不再使用 `SELECT *` 读取行情/状态表。
- 真实 DB baseline 未运行，原因：当前 workspace 缺少 `data/p116_foundation.duckdb` 和 `data/state_cube.duckdb`。

实现复核命令：
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`
- 结果：278 passed, 1 warning。
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- 结果：5/5 cases passed。
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py benchmarks/*.py`
- 结果：通过。

复核记录：
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-light-backtest-implementation-review.md`

### C18: Phase 2 Real Baseline 与 Hardening 派工

交付：
- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md`
- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_HARDENING_REVIEW.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-real-baseline-hardening-dispatch.md`

验收：
- Kimi 输出真实 DB baseline readiness/runbook，明确 `data/p116_foundation.duckdb`、`data/state_cube.duckdb` 是否存在；存在则给出可运行 gate 命令，不存在则给出最小数据准备 handoff。
- Qoder 输出 Phase 2 Light Backtest hardening review，按 blocker / acceptable / backlog 分类审计当前实现与 contract 的偏差。
- 两份输出都必须明确不阻塞 MVP stub 链路，不扩展 Agent Debate / Paper Trading / 真实下单。

状态：Kimi/Qoder 已回传，Codex 已采纳为下一轮 hardening 输入。

当前 Codex 裁决：
- Kimi 下一步只负责真实 DB baseline readiness，不改代码。
- Qoder 下一步只负责 hardening 审阅与任务清单，不改代码。
- Codex 暂不启动新的实现，先收敛 review 和真实数据准备状态。

状态更新：
- Kimi 已完成 `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md` 和 `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-db-baseline-run.md`。
- Kimi 结论：`data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 均不存在；real baseline 继续阻塞，MVP stub/synthetic path 不受影响。
- Qoder 已完成 `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_HARDENING_REVIEW.md` 和 `data/research/conversations/agent-runs/2026-06-11-qoder-phase2-light-backtest-hardening-review.md`。
- Qoder 结论：`light_real_v1` 只可作为 internal synthetic smoke；real baseline release 不可发布，blockers 包括真实 DB 缺失、real mode 缺 DB fallback、日期级多 symbol 执行语义、trade/event evidence 落库、`volume_ratio OR volume_ma_N` 契约和真实 benchmark gate 未跑。

下一轮 Codex hardening 优先级：
1. real mode 传入不存在 DB 时返回 `light_real_v1 failed`，不得静默 fallback `light_stub`。
2. 打通 real E2E 的 trade/event evidence 落库。
3. 修正多 symbol 日期级执行语义。
4. 闭合 `volume_ratio OR volume_ma_N` provider 契约。
5. 真实 DB 就绪后再跑 Kimi real baseline gate。

状态更新 (2026-06-19)：
- Codex 已完成全部 5 个 Qoder hardening blocker 修复：
  - ✅ Blocker 1: `backtest_adapter.py` - real mode 缺 DB 返回 `BT_DATA_DB_NOT_FOUND` + `status=failed`，不再静默降级。
  - ✅ Blocker 2: `light_backtest_engine.py` + `backtest_data_provider.py` - 排序改为 `date ASC, symbol ASC`，保证多 symbol 日期级组合权益语义。
  - ✅ Blocker 3: `backtest_adapter.py` (BacktestResult.signal_frame) + `e2e_runner.py` (_persist_trades_and_events) - trade/event evidence 从 real E2E path 可靠落库。
  - ✅ Blocker 4: `backtest_data_provider.py` - volume_ma_N 缺失时可用 volume_ratio 替代，两者都缺失才 failed。
  - ✅ Backlog E: `api_models.py` + `e2e_runner.py` - BacktestResponse 新增 `daily_curve_total_count` 和 `trades_truncated` 截断元数据。
  - ✅ Backlog F: tradability hardening 已内建于 engine `_generate_trades()` 的 limit_down blocked exit + evidence builder 的 `hold` 事件类型。
- 附加修复：
  - `pyproject.toml`: 添加 `[tool.hatch.build.targets.wheel]` 修复 hatchling 构建配置。
  - `backtest_data_provider.py`: `pl.from_arrow(result.arrow())` → `pl.DataFrame(rows, schema=columns, orient="row")` 消除 pyarrow 依赖。
- 测试基线：278 passed, 0 failed。E2E acceptance 5/5。
- 架构审计：Codex 已采纳“State 系统作为应用层与风控层的核心，建立在更广泛的数据基座之上”的结论，并记录为决策 `0015` 和 `docs/design/DATA_FOUNDATION_AND_STATE_CUBE_ARCHITECTURE.md`。

### C19: 愿景、里程碑与关键假设

交付：
- `docs/product/VISION_MILESTONES_AND_KEY_ASSUMPTIONS.md`
- `data/research/conversations/decisions/0013-vision-milestones-key-assumptions.md`

验收：
- 参考 S 级私董会的分层加速场、公共契约、案主机制和长期共同体逻辑。
- 明确 Hermass 不是荐股、交易、收益承诺工具。
- 定义 H1/H2/H3/H4 四层策略研究场。
- 定义 M0-M5 里程碑，并把当前 Phase 2 blockers 纳入现实边界。
- 定义可验证关键假设和失败信号。

状态：已完成。

### C20: Phase 3 Web UI 与真实数据 Baseline 并行派工

交付：
- `agents/QODER_NEXT_TASK_PHASE3_WEB_UI_CONTRACT.md`
- `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`
- `data/research/conversations/agent-runs/2026-06-18-codex-phase3-web-ui-dispatch.md`
- `data/research/conversations/decisions/0016-phase3-web-ui-real-baseline-split.md`

验收：
- Qoder 输出 Phase 3 Web UI 工程契约，只包含 3 个页面：Strategy Structuring、Strategy Diagnosis、Evidence Lab。
- Web 技术边界固定为 FastAPI + Jinja2；路由只做参数解析、调用 service、返回模板。
- 必须复用现有服务契约：`GenerateStrategyRequest/Response`、`ValidateStrategyRequest/Response`、`PreviewRequest/Response`、`BacktestRequest/Response`。
- UI 必须显式暴露运行标签：`synthetic`、`light_stub`、`light_real_v1`，以及 `not investment advice` 免责声明。
- UI 验收不依赖真实 DB：3 个冻结中文样例跑通 `generate -> validate -> preview -> backtest`。
- 缺止损、仓位超过 25% 的 DSL 能在 UI 显示红线拒绝原因。
- 每一步展示 `trace_id`；Evidence Lab 能按 `trace_id` 拉出 generation / validation / preview / backtest 记录。
- Qoder 输出文件级 contract：`web/main.py`、`web/strategy_lab_routes.py`、`web/templates/...`、`web/static/...`。
- Qoder 输出明确 Non-MVP Items：不做 SPA/前后端分离、不做前端状态管理框架、不做 Agent Debate、不做 Paper Trading、不做真正实时行情接入。
- Kimi 输出真实数据 baseline handoff：校验 `data/p116_foundation.duckdb`、校验 `data/state_cube.duckdb`、跑 `benchmarks/validate_real_data.py`、产出 `outputs/benchmarks/data_readiness_status.json` 和 baseline 结果。
- Kimi 不碰 Web，不阻塞 Phase 3 Web 开发。

状态：Qoder contract 已回传，Codex 已完成 Phase 3 Web UI 实现。

实现交付：
- `web/main.py`：FastAPI 入口、静态资源、Jinja2 模板、环境变量配置。
- `web/strategy_lab_routes.py`：3 个页面的 GET/POST 路由，调用现有 service，不直接读写 DuckDB。
- `web/templates/base.html/index.html/structuring.html/diagnosis.html/evidence.html`：统一布局 + 3 个页面模板。
- `web/static/style.css`：最小可用样式。
- `hermass_platform/strategy_lab/storage.py`：新增 `get_strategy_version_by_trace_id()`，扩展 `list_trade_events()` 支持 `trace_id` 查询。
- `pyproject.toml`：新增 `jinja2>=3.1`、`python-multipart>=0.0.9`，`packages` 增加 `web`。
- `scripts/test_web_ui_smoke.py`：基于 FastAPI TestClient 的冒烟测试。
- `web/data_readiness.py`：只读读取 `outputs/benchmarks/data_readiness_status.json`，缺省返回 NOT_READY。

Data Readiness 展示位：
- 所有页面顶部 header 显示数据基线 verdict（READY / PARTIAL / NOT_READY）。
- 首页显示 readiness 中文说明与 next_steps。
- Web UI 不自行判断 DB 存在性，只读取 Kimi 产出的 JSON；缺失时按 contract 显示 NOT_READY。

实现复核：
- `uv run pytest hermass_platform/strategy_lab/tests -q` → 278 passed, 0 failed。
- `uv run python scripts/run_strategy_lab_mvp_e2e_acceptance.py` → 5/5 passed。
- `uv run python scripts/test_web_ui_smoke.py` → ✅ home page / structuring valid sample / structuring over-position red line / structuring missing stop loss / full journey，全部通过。
- `uv run python -m py_compile hermass_platform/strategy_lab/*.py web/*.py scripts/test_web_ui_smoke.py` → OK。

启动命令：
```bash
uv run uvicorn web.main:app --reload --port 8000
```

Codex 当前裁决：
- Phase 3 Web UI 主线已实现；真实数据 baseline 仍为独立 Kimi handoff，不互相阻塞。
- Web 层是薄层，业务逻辑全部留在 `hermass_platform/strategy_lab/`。
- 真实 DB 缺失继续阻塞 `light_real_v1` 默认发布和真实指标试点，但不阻塞 Web UI mock/synthetic 验收。
- Web UI 后续应读取 Kimi 产出的 `data_readiness_status.json`，向用户显示当前真实数据 readiness 状态。

### C3: Phase 1 API 与预览

交付：
- Strategy Lab API。
- preview service。
- 审计日志。

验收：
- 10 条中文策略中至少 8 条生成合法 DSL。

### C4: Phase 2 Backtest 骨架

交付：
- `backtest/dsl_runner.py`
- `backtest/engine.py`
- `backtest/metrics.py`
- `benchmarks/` 基准脚本入口。

验收：
- DuckDB 只做列裁剪取数和可选预过滤。
- Polars 负责信号生成、权益曲线、绩效指标。
- 禁止 `apply(lambda row: ...)` 和 Python 逐行循环出现在热路径。
- benchmark 输出写入 `outputs/benchmarks/`。

状态：待 Phase 0/1 后启动。

## 冲突处理

当 Qoder 追求架构完整性、Kimi 追求性能研究、Codex 追求 MVP 交付发生冲突时，默认先保证 MVP 可运行。
