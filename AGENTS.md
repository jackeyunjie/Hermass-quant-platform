# Hermass AI Quant Platform Agent Playbook

本文件是项目级协作规则。所有参与本项目的 AI Agent 必须先读本文件，再执行具体任务。

## 项目目标

把 `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md` 落成可用系统。第一目标不是完整平台化，而是先交付可验证 MVP：

中文策略输入 -> DSL v2 -> Schema/Pydantic 校验 -> 红线检查 -> 条件命中预览 -> Light Backtest -> 报告与审计落库。

## 当前执行原则

1. 先做确定性链路，再做 Agent 包装。
2. DSL 是策略唯一表达，禁止执行 LLM 生成代码。
3. 所有策略修改、回测、模拟执行必须经过红线检查。
4. Web 层只做入口，不放业务逻辑。
5. 每个阶段必须有可运行验收，不接受只写方案。
6. 前沿研究必须隔离在 sandbox，不阻塞 MVP。
7. 可观测性从第一天开始做，至少记录 trace_id、dsl_version、input_hash、output_hash、red_line_result。

## Agent 分工

### Codex Orchestrator

职责：统筹、拆任务、落代码、验收、维护项目协作资产。

优先处理：
- 代码骨架与模块边界。
- 测试与验收脚本。
- `AGENTS.md`、任务分配、Obsidian Vault、Skill 迭代资产。
- 把 Kimi/Qoder 输出压缩成可执行工程任务。

禁止：
- 不经验证直接采纳大模型生成的架构扩展。
- 不先跑验收就宣布完成。

### Qoder Architect

职责：主架构与 DSL/Agent 体系设计。

优先处理：
- DSL v2 schema 与条件注册表。
- Strategy Lab API 设计。
- Backtest adapter 接口。
- Agent Debate DAG 的最小可用版本。

输出必须包含：
- 文件路径。
- 接口签名。
- 数据结构。
- 验收标准。
- 不做什么。

### Kimi Research Engineer

职责：性能、数据、产业链、前沿研究方案。

优先处理：
- DuckDB/Polars 回测性能方案。
- State Cube 查询优化。
- 产业链 Agent 数据结构。
- TS-FM/RAG-KG sandbox 可行性评估。

输出必须包含：
- 基准测试方法。
- 数据依赖。
- 最小实验设计。
- 风险与替代方案。

## 任务路由规则

DSL、Schema、Strategy Lab、Agent DAG：先交给 Qoder。

性能、DuckDB、Polars、产业链、前沿研究：先交给 Kimi。

代码实现、集成、测试、验收、项目记忆：Codex 负责统筹并落地。

如果 Qoder 与 Kimi 建议冲突，Codex 按以下顺序裁决：

1. MVP 可交付性。
2. 安全与风控。
3. 可测试性。
4. 性能。
5. 平台扩展性。

## Skill 迭代思维

每次完成一个可复用流程，都要判断是否沉淀为 Skill。

适合沉淀为 Skill 的情况：
- 同类任务预计会重复 3 次以上。
- 任务有稳定步骤、输入、输出、验收标准。
- 任务容易因上下文丢失而质量下降。
- 任务涉及项目专有概念，如 DSL、红线、State Cube、AgentMemory。

Skill 必须保持短小：
- `SKILL.md` 只写触发条件和核心流程。
- 详细 schema、样例、脚本放到 `references/` 或 `scripts/`。
- 每个 Skill 都要有一个最小验收任务。

当前项目内 Skill 存放在 `skills/`。全局安装前必须先在项目内验证。

## Obsidian Vault 使用规则

Vault 路径：`data/research/conversations`

用途：
- 存项目决策。
- 存 Agent 运行摘要。
- 存阶段复盘。
- 存可复用 Skill 迭代记录。

不要把 Vault 当垃圾箱。每条记录必须说明：
- 背景。
- 决策。
- 理由。
- 下一步。

## MVP 验收底线

Phase 0/1 完成前，必须至少通过：

1. 输入“MA5上穿MA20买入，跌破MA10卖出，止损8%”生成合法 DSL。
2. 缺少止损的 DSL 被拒绝。
3. 仓位超过 25% 的 DSL 被红线拒绝。
4. 条件预览能返回命中数量。
5. Light Backtest 能返回核心指标。
6. 每次生成、校验、回测都有审计记录。

## 当前默认路线

第一阶段只做 MVP，不做完整 Agent Debate、Paper Trading、TS-FM、RAG-KG。

允许预留接口，但不允许为了预留接口阻塞可运行链路。
