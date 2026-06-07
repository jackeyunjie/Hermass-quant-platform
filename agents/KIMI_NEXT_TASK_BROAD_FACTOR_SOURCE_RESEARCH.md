# Kimi Next Task: Broad Factor Source Research

请先读取：

1. `docs/FACTOR_SOURCE_TAXONOMY.md`
2. `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
3. `docs/SQX_LOCAL_BLOCK_INVENTORY.md`
4. `AGENTS.md`

## 背景

因子库来源要从 SQX 扩展到非常广泛的交易轮胎/轮廓、量化公司网站、AI 量化项目、基本面、消息面、心理面、资金流、订单流和交易大咖方法论。

## 你的任务

输出跨来源的 200+ factor/block 候选清单，并按证据等级和 A 股可落地性分类。

## 来源范围

必须覆盖：

- StrategyQuant X / strategy generators。
- Qlib / Alpha158 / Alpha360 / open quant frameworks。
- AQR / BlackRock / MSCI / Barra / Research Affiliates 等机构因子。
- academic empirical factors。
- fundamental factors。
- news/event/sentiment factors。
- money flow / order flow / microstructure。
- trader methodology：Wyckoff、Darvas、Minervini VCP、CANSLIM、Livermore、Turtle、O'Neil、Weinstein 等。
- behavioral / psychology factors。
- Hermass native state/agent/industry-chain factors。

## 必须输出

### 1. Source Map

按 source_type 输出来源图谱。

### 2. Candidate Table

至少 200 条候选，字段：

- `id`
- 中文名
- source_type
- category
- factor_or_block
- data_dependency
- evidence_level 初始估计
- A 股可得性
- future_leakage_risk
- compute_cost
- MVP+ / research / later
- notes

### 3. Trader Methodology Translation

至少拆 8 个交易大咖/流派方法论：

- setup
- trigger
- invalidation
- risk
- review
- converted_blocks

### 4. Priority Recommendation

输出：

- 先做 30 个。
- 后做 70 个。
- research backlog。

### 5. Data Acquisition Gap

明确还缺哪些数据：

- 财报。
- 新闻/公告。
- 研报。
- 社媒/搜索。
- level-2/order flow。
- 资金流。

## 输出文件

写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-broad-factor-source-research.md`

## 输出格式

```markdown
# Broad Factor Source Research

## Source Map

## Candidate Factor And Block Table

## Trader Methodology Translation

## Priority Recommendation

## Data Acquisition Gap

## Risks

## Next Steps For Qoder And Codex
```
