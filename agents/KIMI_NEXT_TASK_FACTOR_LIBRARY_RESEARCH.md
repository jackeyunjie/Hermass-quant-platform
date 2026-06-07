# Kimi Next Task: High-End Factor Library Research

请先读取：

1. `AGENTS.md`
2. `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
3. `docs/TASK_ALLOCATION.md`
4. `data/research/conversations/decisions/0002-kimi-performance-data-architecture.md`

## 背景

用户要求“因子库极大扩展，高配，借鉴成熟项目”。当前 MVP 因子只够基础策略，需要向成熟平台级因子库演进。

## 你的任务

请研究成熟项目和 A 股可落地约束，输出高配因子库优先级和数据依赖，不要写代码。

## 必须参考的成熟项目方向

- Qlib：Alpha158 / Alpha360 / DataHandler / Processor。
- QuantConnect LEAN：大规模技术指标库与 indicator abstraction。
- Alphalens：IC、分层收益、factor tear sheet。
- TA-Lib / pandas-ta：技术指标分类。

## 必须输出

### 1. 因子分类体系

按以下层级输出：

- L1 technical。
- L2 cross-sectional。
- L3 fundamental。
- L4 money flow / microstructure。
- L5 Hermass-specific。

### 2. 因子优先级表

至少给出 50 个候选因子，字段包括：

- `factor_id`
- 中文名
- category
- 数据依赖
- 计算窗口
- compute_engine: duckdb / polars / mixed
- 是否可预计算
- 是否进入 MVP+
- 风险：未来函数、缺失率、计算成本、数据源不稳定

### 3. A 股数据可得性

明确哪些因子当前可能已有数据，哪些需要额外数据源：

- OHLCV。
- State Cube。
- market_assets。
- 黑狼资金流。
- 基本面。
- 行业/概念。

### 4. 因子评估方法

设计 Factor Evaluation：

- IC / RankIC。
- ICIR。
- 分层收益。
- 多空收益。
- 换手。
- 覆盖率。
- 缺失率。
- 成本后收益。
- State 分层表现。

### 5. 近期 3 阶段路线

输出：

- F0 registry only。
- F1 technical MVP+。
- F2 cross-sectional + evaluation。

每阶段不超过 4 周，给出验收标准。

## 输出文件

写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-factor-library-research.md`

## 输出格式

```markdown
# Kimi Factor Library Research

## Mature Project Lessons

## Factor Taxonomy

## Priority Factor Table

## A Share Data Availability

## Factor Evaluation Framework

## Three-Stage Roadmap

## Risks

## Next Steps For Qoder And Codex
```

## 不做什么

- 不要求一次性实现 50 个因子。
- 不把未评估因子直接暴露给生产 DSL。
- 不引入外部大型依赖。
- 不做真实交易。
