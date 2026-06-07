# Hermass Factor Source Taxonomy

## 目标

Hermass 因子库来源不能只依赖 SQX。高配因子库必须吸收：

- 成熟策略生成器。
- 传统量化因子研究。
- 量化公司/资管公司的公开研究。
- AI 量化项目。
- 基本面、消息面、心理面。
- 资金流、订单流、微观结构。
- 交易大咖的方法论。
- Hermass 自有 State / Agent Memory / 产业链数据。

核心要求：

每个来源都要被转成可验证的 factor/block，而不是停留在故事或口号。

## 来源分层

### S1: Strategy Generators

代表：

- StrategyQuant X / B143。
- AlgoWizard / SQX snippets。
- genetic/random strategy builders。

可吸收内容：

- signal blocks。
- entry blocks。
- exit blocks。
- order blocks。
- robustness blocks。
- parameter space。
- block weighting。
- strategy databank。

Hermass 处理：

- 进入 Block Library。
- 不复制源码。
- 不执行外部 snippets。
- 用 metadata + DSL 重新表达。

### S2: Open Quant Frameworks

代表：

- Qlib / Alpha158 / Alpha360。
- Zipline / Pipeline。
- Backtrader。
- Lean / QuantConnect indicators。
- vectorbt。
- pandas-ta / TA-Lib。

可吸收内容：

- 技术指标。
- 因子工程。
- 数据 handler。
- processor。
- backtest/event abstractions。

Hermass 处理：

- 技术指标进入 factor catalog。
- 数据处理思想进入 processors。
- 不引入不必要的大型依赖。

### S3: Institutional Factor Research

代表：

- AQR。
- BlackRock / iShares。
- MSCI / Barra。
- Research Affiliates。
- Robeco / Dimensional / Man Group。

核心风格因子：

- Value。
- Momentum。
- Quality。
- Low volatility / defensive。
- Size。
- Carry。
- Yield。
- Growth。
- Multifactor / dynamic factor allocation。

Hermass 处理：

- 进入 L2/L3 factor library。
- 必须有经济含义、数据依赖和评估方法。
- 与 A 股可得数据对齐。

### S4: Academic / Empirical Factor Literature

代表：

- Fama-French。
- time-series momentum。
- cross-sectional momentum。
- quality minus junk。
- low beta / betting-against-beta。
- accrual anomaly。
- post-earnings announcement drift。

Hermass 处理：

- 进入 research catalog。
- 先做可得性和未来函数审查。
- 再做 IC/分层收益。

### S5: Fundamental Factors

分类：

- Valuation：PE/PB/PS/EV/EBITDA/dividend yield。
- Profitability：ROE/ROA/ROIC/gross margin/net margin。
- Growth：revenue/profit/EPS/cashflow growth。
- Quality：cashflow quality/accruals/earnings stability。
- Leverage：debt ratio/interest coverage/current ratio。
- Capital allocation：buyback/dividend/capex/R&D。

Hermass 处理：

- 进入 L3。
- 必须处理财报滞后和公告日期。
- 禁止使用未来财报。

### S6: News / Event / Sentiment

分类：

- 新闻情绪。
- 公告情绪。
- 研报情绪。
- 社媒/社区情绪。
- 搜索热度。
- 舆情热度。
- 事件类型：业绩预告、并购、减持、回购、监管处罚、订单、产品发布。

Hermass 处理：

- 进入 event/sentiment factors。
- 必须记录来源、时间戳、置信度。
- LLM 只做结构化抽取，不直接给交易建议。

### S7: Money Flow / Order Flow / Microstructure

分类：

- 主力净流入。
- 大单/中单/小单。
- 主买/主卖。
- 资金流连续性。
- 行业资金扩散。
- 换手率。
- 成交额强度。
- Amihud illiquidity。
- bid/ask/spread proxy。
- level-2 order imbalance。
- tick rule buy/sell pressure。

Hermass 处理：

- A 股优先使用黑狼资金流。
- 日频先做 money flow。
- 分钟/tick 后做 order flow。

### S8: Trader Methodology

代表方法论：

- Wyckoff。
- Darvas Box。
- Minervini VCP。
- CANSLIM。
- Livermore trend/pivotal points。
- Turtle trend following。
- O'Neil relative strength。
- Weinstein stage analysis。
- Bollinger volatility squeeze。
- Mark Douglas / trading psychology risk discipline。

Hermass 处理：

- 不把方法论原样当因子。
- 拆成 observable blocks：
  - setup。
  - trigger。
  - invalidation。
  - risk rule。
  - position sizing。
  - review rule。

### S9: Behavioral / Psychology Factors

分类：

- 过度反应。
- 不足反应。
- 追涨杀跌。
- 恐慌抛售。
- 拥挤度。
- 一致预期偏离。
- 涨停情绪。
- 连板情绪。
- 亏损厌恶导致的支撑/压力。

Hermass 处理：

- 转成可观测 proxy：
  - limit-up count。
  - drawdown panic。
  - volume capitulation。
  - sentiment divergence。
  - crowdedness。

### S10: Hermass Native Sources

分类：

- State Cube。
- EF width。
- Boundary distance。
- multi-timeframe resonance。
- Agent Memory outcome。
- Industry chain propagation。
- user strategy history。

Hermass 处理：

- 作为差异化护城河。
- 与传统 factor 做组合和对比评估。

## Evidence Level

每个 factor/block 需要证据等级：

- `E0`: idea only。
- `E1`: known literature / public framework。
- `E2`: data available and computable。
- `E3`: IC/stratified return passed。
- `E4`: backtest passed。
- `E5`: walk-forward / robustness passed。
- `E6`: paper trading validated。

生产 DSL 只允许：

- `E4+` 进入候选。
- `E5+` 进入 production。

## Factor Record Template

```json
{
  "factor_id": "quality_roe_ttm",
  "source_type": "institutional_factor_research",
  "source_refs": ["quality", "profitability"],
  "category": "fundamental_quality",
  "evidence_level": "E1",
  "data_availability": "pending",
  "inputs": ["roe_ttm", "report_date"],
  "future_leakage_risk": "high_until_report_date_handled",
  "a_share_notes": "must use announcement date, not fiscal period end",
  "dsl_exposure": "none",
  "status": "research"
}
```

## Methodology Translation Template

```json
{
  "methodology_id": "minervini_vcp",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["trend_up", "relative_strength_high", "volatility_contraction"],
    "trigger": ["breakout_on_volume"],
    "invalidation": ["failed_breakout", "stop_loss_pct"],
    "risk": ["position_size_limit", "no_chasing_extended"],
    "review": ["post_trade_review"]
  },
  "converted_blocks": [
    "trend_filter_ma_stack",
    "relative_strength_rank",
    "vcp_contraction",
    "breakout_entry",
    "volume_expansion",
    "stop_loss_pct"
  ]
}
```

## Immediate Next Step

1. Kimi 输出跨来源 200+ factor/block 候选。
2. Qoder 设计 source/evidence metadata schema。
3. Codex 实现 source registry 和 factor/block catalog loader。
