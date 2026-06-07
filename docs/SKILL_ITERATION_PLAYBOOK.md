# Skill Iteration Playbook

## 为什么要做 Skill

本项目会反复遇到同类任务：DSL 设计、回测验收、红线检查、Agent 评审、数据刷新、复盘沉淀。把这些流程变成 Skill，可以降低上下文丢失造成的返工。

## Skill 候选清单

### hermass-dsl-builder

触发：
- 设计或修改策略 DSL。
- 增加条件类型。
- 校验中文策略生成结果。

核心流程：
- 读取 `AGENTS.md`。
- 读取 DSL schema。
- 更新 condition registry。
- 增加合法/非法测试。
- 跑 validator 验收。

### hermass-backtest-mvp

触发：
- 接入或修改回测引擎。
- 验证 Light Backtest 性能。
- 生成 backtest report。

核心流程：
- 读取 DSL。
- 翻译信号。
- 运行 Light Backtest。
- 输出 metrics、trades、state_breakdown。
- 写入 audit/trace。

### hermass-redline-review

触发：
- 策略、回测、订单、Agent 建议进入执行级路径。

核心流程：
- 检查仓位。
- 检查止损。
- 检查数据新鲜度。
- 检查 kill-switch。
- 输出 allow/warn/reject。

### hermass-agent-debate

触发：
- 回测完成后需要 Agent 评审。
- 用户要求多 Agent 辩论。

核心流程：
- 加载回测结果。
- Risk Guardian 先审。
- Critic/Trend/Macro/Industry 输出 typed JSON。
- Router 标注冲突与共振。
- 保存 AgentMemory。

## Skill 创建标准

一个 Skill 必须包含：

- 清晰触发条件。
- 最小上下文读取顺序。
- 固定输出结构。
- 验收命令或验收样例。
- 明确不做什么。

不要把长篇架构文档塞进 `SKILL.md`。详细内容放 `references/`。

## 迭代节奏

每完成一个阶段，执行一次 Skill 复盘：

1. 哪个流程重复出现？
2. 哪个流程容易被 Agent 做错？
3. 哪个流程需要项目专有知识？
4. 是否值得沉淀为 Skill？
5. Skill 是否经过至少一次真实任务验证？

## 当前优先级

先做 `hermass-quant-execution` 项目内 Skill，覆盖 MVP 执行规则。等 Phase 0 验证通过后，再拆成更细 Skill。
