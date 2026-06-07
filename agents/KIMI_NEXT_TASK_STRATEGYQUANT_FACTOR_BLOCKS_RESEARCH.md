# Kimi Next Task: StrategyQuant X B143 Factor And Block Research

请先读取：

1. `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
2. `docs/STRATEGYQUANT_XB143_REFERENCE_MODEL.md`
3. `agents/KIMI_NEXT_TASK_FACTOR_LIBRARY_RESEARCH.md`
4. `AGENTS.md`

## 背景

用户明确希望“最全因子库”，并指出可以参考 StrategyQuant X B143。Codex 已将目标升级为 Factor + Block Library。

## 你的任务

研究 StrategyQuant X 风格 building blocks，并转成 Hermass 可落地的 A 股因子/信号/入场/退出/订单/稳健性 block 清单。

## 必须输出

### 1. StrategyQuant X 可借鉴点

输出：

- building blocks 结构。
- 参数空间。
- 权重/百分比生成机制。
- snippets/custom indicators 思路。
- B143 AI/robustness/fill realism 对 Hermass 的启发。

### 2. 最全 Block 清单

至少输出 120 个候选 block，分组：

- Signal Blocks。
- Indicator Blocks。
- Entry Blocks。
- Exit Blocks。
- Filter Blocks。
- Order/Execution Blocks。
- Robustness Blocks。
- A-share-specific Blocks。
- Hermass State Blocks。

每个 block 至少包含：

- `block_id`
- 中文名
- block_type
- 数据依赖
- 参数空间
- 是否适合 A 股日频
- 是否适合 MVP+
- 风险

### 3. 因子与 block 的关系

说明：

- 哪些是 factor。
- 哪些是 signal block。
- 哪些是 strategy construction block。
- 哪些只能用于 robustness，不应进 DSL。

### 4. 高配优先级

输出三层：

- 必须先做。
- 高价值但后做。
- 暂不做。

### 5. A 股适配风险

必须覆盖：

- 涨跌停。
- T+1。
- 停牌。
- ST。
- 印花税/佣金。
- 流动性。
- 复权。
- 幸存者偏差。

## 输出文件

写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-strategyquant-factor-blocks.md`

## 输出格式

```markdown
# Kimi StrategyQuant Factor Blocks Research

## StrategyQuant Lessons

## Block Taxonomy

## Candidate Block Table

## Factor Vs Block Boundary

## Priority

## A Share Adaptation Risks

## Next Steps For Qoder And Codex
```
