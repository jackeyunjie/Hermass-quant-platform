# Broad Factor Source Research

> Agent: Kimi Research Engineer  
> Date: 2026-06-06  
> Trigger: `agents/KIMI_NEXT_TASK_BROAD_FACTOR_SOURCE_RESEARCH.md`  
> References: `FACTOR_SOURCE_TAXONOMY.md`, `FACTOR_LIBRARY_EXPANSION_PLAN.md`, `SQX_LOCAL_BLOCK_INVENTORY.md`, `AGENTS.md`

---

## Source Map

按 `source_type` 分层，共 10 大来源类型，覆盖从策略生成器到 Hermass 自有数据的完整谱系。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Hermass Factor Source Map                          │
├─────────┬──────────────────────────────┬────────────────────────────────────┤
│ Layer   │ Source Type                  │ Representative / Key Content       │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S1      │ strategy_generator           │ StrategyQuant X / B143, AlgoWizard │
│         │                              │ genetic builders, snippet blocks   │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S2      │ open_quant_framework         │ Qlib Alpha158/360, Zipline, Lean,  │
│         │                              │ Backtrader, vectorbt, pandas-ta    │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S3      │ institutional_factor_research│ AQR, BlackRock, MSCI/Barra,        │
│         │                              │ Research Affiliates, Robeco, DFA   │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S4      │ academic_empirical           │ Fama-French, time-series momentum, │
│         │                              │ QMJ, BAB, accrual anomaly, PEAD    │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S5      │ fundamental                  │ Valuation, Profitability, Growth,  │
│         │                              │ Quality, Leverage, Capital alloc   │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S6      │ news_event_sentiment         │ News, announcement, research rpt,  │
│         │                              │ social media, search heat,舆情     │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S7      │ money_flow_microstructure    │ 主力/大单/中单/小单, 主动买卖,      │
│         │                              │ Amihud, spread proxy, L2 imbalance │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S8      │ trader_methodology           │ Wyckoff, Darvas, Minervini VCP,    │
│         │                              │ CANSLIM, Livermore, Turtle, O'Neil │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S9      │ behavioral_psychology        │ Overreaction, underreaction,       │
│         │                              │ herding, panic, crowdedness,       │
│         │                              │ limit-up sentiment                 │
├─────────┼──────────────────────────────┼────────────────────────────────────┤
│ S10     │ hermass_native               │ State Cube, EF width, boundary,    │
│         │                              │ multi-timeframe resonance, Agent   │
│         │                              │ Memory, industry chain propagation │
└─────────┴──────────────────────────────┴────────────────────────────────────┘
```

### 来源 -> Hermass 层级映射

| Source Type | Hermass Level | 处理原则 |
|---|---|---|
| strategy_generator | L6 Block Library | metadata + DSL 重新表达，不复制源码 |
| open_quant_framework | L1-L2 Factor Catalog | 技术指标进 registry，处理思想进 processors |
| institutional_factor_research | L2-L3 Factor Library | 必须有经济含义、数据依赖、评估方法 |
| academic_empirical | Research Catalog | 先进 research，审查未来函数后再评估 |
| fundamental | L3 Fundamental | 处理财报滞后，禁止用未来财报 |
| news_event_sentiment | L4 Event/Sentiment | 记录来源/时间戳/置信度，LLM 只做结构化抽取 |
| money_flow_microstructure | L4 Microstructure | A 股优先黑狼资金流，日频先做 money flow |
| trader_methodology | L6 Block Library | 拆成 observable blocks (setup/trigger/invalidation/risk/review) |
| behavioral_psychology | L2-L4 Cross-Sectional | 转成可观测 proxy |
| hermass_native | L5 Differentiation | 差异化护城河，与传统 factor 组合评估 |

---

## Candidate Factor And Block Table

共 228 条候选 factor / block，按 source_type 分组。

### S1: Strategy Generator (SQX / AlgoWizard / Genetic Builders)

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s1_001 | 指标上穿阈值信号 | strategy_generator | signal | block | 任意 numeric factor | E1 | 高 | 无 | 低 | MVP+ | SQX signal_compare/cross 泛化 |
| s1_002 | 指标下穿阈值信号 | strategy_generator | signal | block | 任意 numeric factor | E1 | 高 | 无 | 低 | MVP+ | 同上 |
| s1_003 | 指标金叉另一指标 | strategy_generator | signal | block | 2 个 numeric factors | E1 | 高 | 无 | 低 | MVP+ | MA 金叉/死叉泛化到任意 factor |
| s1_004 | 指标上升趋势 | strategy_generator | signal | block | 任意 numeric factor | E1 | 高 | 无 | 低 | MVP+ | rising/falling N bars |
| s1_005 | 指标下降趋势 | strategy_generator | signal | block | 任意 numeric factor | E1 | 高 | 无 | 低 | MVP+ | 同上 |
| s1_006 | 价格突破高点 | strategy_generator | signal | block | high, close | E1 | 高 | 无 | 低 | MVP+ | breakout N bar high |
| s1_007 | 价格跌破低点 | strategy_generator | signal | block | low, close | E1 | 高 | 无 | 低 | MVP+ | breakdown N bar low |
| s1_008 | 波动率收缩 | strategy_generator | signal | block | ATR/BB width | E1 | 高 | 无 | 低 | MVP+ | volatility contraction N bars |
| s1_009 | 波动率扩张 | strategy_generator | signal | block | ATR/BB width | E1 | 高 | 无 | 低 | MVP+ | volatility expansion |
| s1_010 | 多时间框架共振确认 | strategy_generator | signal | block | same factor on D1/W1/MN1 | E2 | 高 | 无 | 中 | MVP+ | multi-timeframe agreement |
| s1_011 | 趋势状态确认 | strategy_generator | signal | block | state_hex, ADX | E2 | 高 | 无 | 低 | MVP+ | trend regime confirmation |
| s1_012 | 市价入场 | strategy_generator | entry | block | close | E1 | 高 | 无 | 低 | MVP+ | market entry at next open |
| s1_013 | 限价入场 | strategy_generator | entry | block | close, limit_price | E1 | 高 | 无 | 低 | MVP+ | limit entry with fill model |
| s1_014 | 回撤入场 | strategy_generator | entry | block | close, pullback_pct | E1 | 高 | 无 | 低 | MVP+ | pullback to MA/support |
| s1_015 | 突破入场 | strategy_generator | entry | block | high, close, volume | E1 | 高 | 无 | 低 | MVP+ | breakout entry on volume |
| s1_016 | 反向入场 | strategy_generator | entry | block | close, oversold_factor | E2 | 高 | 无 | 低 | research | mean-reversion entry |
| s1_017 | 时间/时段约束入场 | strategy_generator | entry | block | datetime | E1 | 高 | 无 | 低 | later | session constrained |
| s1_018 | 固定止损出场 | strategy_generator | exit | block | close, entry_price | E1 | 高 | 无 | 低 | MVP+ | fixed stop loss pct |
| s1_019 | 固定止盈出场 | strategy_generator | exit | block | close, entry_price | E1 | 高 | 无 | 低 | MVP+ | fixed take profit pct |
| s1_020 | ATR 追踪止损 | strategy_generator | exit | block | close, atr | E2 | 高 | 无 | 低 | MVP+ | ATR trailing stop |
| s1_021 | Chandelier 出场 | strategy_generator | exit | block | close, high, atr | E2 | 高 | 无 | 低 | MVP+ | chandelier exit |
| s1_022 | 指标条件出场 | strategy_generator | exit | block | any numeric factor | E1 | 高 | 无 | 低 | MVP+ | indicator exit e.g. RSI>80 |
| s1_023 | 时间出场 | strategy_generator | exit | block | bar_count | E1 | 高 | 无 | 低 | MVP+ | exit after N bars |
| s1_024 | 波动率出场 | strategy_generator | exit | block | ATR, volatility | E2 | 高 | 无 | 低 | research | volatility expansion exit |
| s1_025 | 状态失效出场 | strategy_generator | exit | block | state_hex | E2 | 高 | 无 | 低 | MVP+ | regime invalidation exit |
| s1_026 | 分批出场 | strategy_generator | exit | block | position_size | E1 | 高 | 无 | 低 | later | partial exit at targets |
| s1_027 | 市价订单 | strategy_generator | order | block | close | E1 | 高 | 无 | 低 | MVP+ | market order |
| s1_028 | 限价订单 | strategy_generator | order | block | close, limit_price | E1 | 高 | 无 | 低 | MVP+ | limit order |
| s1_029 | 止损订单 | strategy_generator | order | block | close, stop_price | E1 | 高 | 无 | 低 | MVP+ | stop order |
| s1_030 | 止损限价订单 | strategy_generator | order | block | close, stop, limit | E1 | 高 | 无 | 低 | later | stop-limit order |
| s1_031 | 滑点/佣金/印花税模型 | strategy_generator | order | block | fill_price | E1 | 高 | 无 | 低 | MVP+ | slippage + commission + tax |
| s1_032 |  Walk-Forward 稳健块 | strategy_generator | robustness | block | equity_curve | E3 | 高 | 无 | 中 | later | walk-forward split |
| s1_033 | 参数抖动稳健块 | strategy_generator | robustness | block | parameters | E3 | 高 | 无 | 中 | later | parameter jitter |
| s1_034 | 随机跳过交易稳健块 | strategy_generator | robustness | block | trade_log | E3 | 高 | 无 | 中 | later | random trade skip |
| s1_035 | 执行降级稳健块 | strategy_generator | robustness | block | fill_quality | E3 | 高 | 无 | 中 | later | random execution degradation |
| s1_036 | 滑点压力稳健块 | strategy_generator | robustness | block | slippage | E3 | 高 | 无 | 低 | later | spread/slippage stress |
| s1_037 | 市场状态分割稳健块 | strategy_generator | robustness | block | state_hex | E3 | 高 | 无 | 中 | later | market regime split |
| s1_038 | 品种分割稳健块 | strategy_generator | robustness | block | symbol | E3 | 高 | 无 | 中 | later | symbol split test |
| s1_039 | 日期分割稳健块 | strategy_generator | robustness | block | date | E3 | 高 | 无 | 中 | later | date split OOS |
| s1_040 | 状态分割稳健块 | strategy_generator | robustness | block | state_hex | E3 | 高 | 无 | 中 | later | state split OOS |
| s1_041 | Monte Carlo 权益扰动 | strategy_generator | robustness | block | equity_curve | E3 | 高 | 无 | 中 | later | MC equity perturbation |
| s1_042 | 固定仓位比例 | strategy_generator | sizing | block | account_value | E1 | 高 | 无 | 低 | MVP+ | fixed pct sizing |
| s1_043 | 固定金额仓位 | strategy_generator | sizing | block | account_value | E1 | 高 | 无 | 低 | MVP+ | fixed amount sizing |
| s1_044 | ATR 风险仓位 | strategy_generator | sizing | block | atr, account_value | E2 | 高 | 无 | 低 | MVP+ | ATR risk-based sizing |
| s1_045 | 波动率目标仓位 | strategy_generator | sizing | block | volatility, account_value | E2 | 高 | 无 | 低 | research | volatility targeting |
| s1_046 | 信号百分比比较 | strategy_generator | signal | block | numeric factor | E1 | 高 | 无 | 低 | MVP+ | percentile comparison |
| s1_047 | 逻辑与或组合 | strategy_generator | signal | block | boolean signals | E1 | 高 | 无 | 低 | MVP+ | AND/OR/NOT condition group |
| s1_048 | 条件计数 | strategy_generator | signal | block | boolean signals | E1 | 高 | 无 | 低 | MVP+ | count of true over N bars |
| s1_049 | 条件否定 | strategy_generator | signal | block | boolean signal | E1 | 高 | 无 | 低 | MVP+ | NOT transform |
| s1_050 | Heiken Ashi 趋势 | strategy_generator | signal | block | HA open/close | E2 | 高 | 无 | 低 | research | HA-based trend signal |

### S2: Open Quant Framework (Qlib / Alpha158 / Alpha360 / Zipline / Lean / Backtrader)

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s2_001 | Alpha158 标准特征集 | open_quant_framework | cross_sectional | factor | OHLCV | E2 | 高 | 无 | 高 | research | Qlib Alpha158 158 features |
| s2_002 | Alpha360 标准特征集 | open_quant_framework | cross_sectional | factor | OHLCV | E2 | 高 | 无 | 高 | research | Qlib Alpha360 360 features |
| s2_003 | 5日收益率排名 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 低 | MVP+ | return_5d_rank |
| s2_004 | 10日收益率排名 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 低 | MVP+ | return_10d_rank |
| s2_005 | 20日收益率排名 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 低 | MVP+ | return_20d_rank |
| s2_006 | 60日收益率排名 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 低 | MVP+ | return_60d_rank |
| s2_007 | 120日收益率排名 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 中 | research | return_120d_rank |
| s2_008 | 行业内相对强弱排名 | open_quant_framework | cross_sectional | factor | close, industry | E2 | 高 | 无 | 中 | MVP+ | industry relative strength |
| s2_009 | 全市场相对强弱排名 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 中 | MVP+ | market relative strength |
| s2_010 | 波动率分位数 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 低 | MVP+ | volatility percentile |
| s2_011 | 市值 Beta | open_quant_framework | cross_sectional | factor | close, index_close | E2 | 高 | 无 | 中 | MVP+ | beta to market index |
| s2_012 | 特质波动率 | open_quant_framework | cross_sectional | factor | close, index_close | E2 | 高 | 无 | 中 | research | idiosyncratic volatility |
| s2_013 | 市场相关性 | open_quant_framework | cross_sectional | factor | close, index_close | E2 | 高 | 无 | 中 | research | correlation to market |
| s2_014 | 流动性风险排名 | open_quant_framework | cross_sectional | factor | volume, amount | E2 | 高 | 无 | 低 | MVP+ | liquidity risk proxy |
| s2_015 | 回撤排名 | open_quant_framework | cross_sectional | factor | close | E2 | 高 | 无 | 低 | MVP+ | drawdown rank |
| s2_016 | Winsorize 去极值 | open_quant_framework | processor | block | any factor | E1 | 高 | 无 | 低 | MVP+ | winsorization |
| s2_017 | Z-Score 标准化 | open_quant_framework | processor | block | any factor | E1 | 高 | 无 | 低 | MVP+ | zscore normalization |
| s2_018 | Robust Z-Score | open_quant_framework | processor | block | any factor | E1 | 高 | 无 | 低 | MVP+ | median-based robust zscore |
| s2_019 | 排名百分比 | open_quant_framework | processor | block | any factor | E1 | 高 | 无 | 低 | MVP+ | rank percentile |
| s2_020 | 行业中性化 | open_quant_framework | processor | block | any factor, industry | E2 | 高 | 无 | 中 | MVP+ | industry neutralization |
| s2_021 | 市场 Beta 中性化 | open_quant_framework | processor | block | any factor, beta | E2 | 高 | 无 | 中 | research | market beta neutralization |
| s2_022 | MACD DIF | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | MACD line |
| s2_023 | MACD DEA | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | MACD signal |
| s2_024 | MACD Hist | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | MACD histogram |
| s2_025 | RSI 14 | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | relative strength index |
| s2_026 | ADX 14 | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | MVP+ | average directional index |
| s2_027 | DI+ / DI- | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | research | directional movement |
| s2_028 | ATR 14 | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | MVP+ | average true range |
| s2_029 | NATR 14 | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | MVP+ | normalized ATR |
| s2_030 | Aroon Up/Down | open_quant_framework | technical | factor | high, low | E2 | 高 | 无 | 低 | research | aroon oscillator |
| s2_031 | SuperTrend | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | MVP+ | supertrend indicator |
| s2_032 | Donchian Channel Upper | open_quant_framework | technical | factor | high | E2 | 高 | 无 | 低 | research | donchian upper |
| s2_033 | Donchian Channel Lower | open_quant_framework | technical | factor | low | E2 | 高 | 无 | 低 | research | donchian lower |
| s2_034 | ROC | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | rate of change |
| s2_035 | ROCP | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | rate of change pct |
| s2_036 | Momentum N | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | price momentum |
| s2_037 | CCI 20 | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | research | commodity channel index |
| s2_038 | Williams %R | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | research | williams percent range |
| s2_039 | Stochastic K | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | research | stochastic %K |
| s2_040 | Stochastic D | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | research | stochastic %D |
| s2_041 | TRIX | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | research | triple exponential avg |
| s2_042 | Bollinger Bandwidth | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | BB bandwidth |
| s2_043 | Bollinger %B | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | BB percent b |
| s2_044 | 历史波动率 20D | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | historical volatility |
| s2_045 | Parkinson 波动率 | open_quant_framework | technical | factor | high, low | E2 | 高 | 无 | 低 | research | Parkinson volatility |
| s2_046 | Garman-Klass 波动率 | open_quant_framework | technical | factor | OHLC | E2 | 高 | 无 | 低 | research | Garman-Klass volatility |
| s2_047 | Rogers-Satchell 波动率 | open_quant_framework | technical | factor | OHLC | E2 | 高 | 无 | 低 | research | Rogers-Satchell volatility |
| s2_048 | 波动率百分位 | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | MVP+ | volatility percentile N days |
| s2_049 | Chandelier Exit Long | open_quant_framework | technical | factor | high, low, close, atr | E2 | 高 | 无 | 低 | MVP+ | chandelier exit level |
| s2_050 | 成交量比率 | open_quant_framework | volume_price | factor | volume | E2 | 高 | 无 | 低 | MVP+ | volume ratio |
| s2_051 | 成交额比率 | open_quant_framework | volume_price | factor | amount | E2 | 高 | 无 | 低 | MVP+ | amount ratio |
| s2_052 | OBV | open_quant_framework | volume_price | factor | close, volume | E2 | 高 | 无 | 低 | MVP+ | on-balance volume |
| s2_053 | MFI | open_quant_framework | volume_price | factor | high, low, close, volume | E2 | 高 | 无 | 低 | research | money flow index |
| s2_054 | VWAP 偏离 | open_quant_framework | volume_price | factor | OHLCV | E2 | 高 | 无 | 中 | research | VWAP deviation |
| s2_055 | 累积派发线 | open_quant_framework | volume_price | factor | high, low, close, volume | E2 | 高 | 无 | 低 | research | accumulation/distribution |
| s2_056 | Chaikin Money Flow | open_quant_framework | volume_price | factor | high, low, close, volume | E2 | 高 | 无 | 低 | research | CMF |
| s2_057 | 换手率 | open_quant_framework | volume_price | factor | volume, shares_outstanding | E2 | 高 | 无 | 低 | MVP+ | turnover rate |
| s2_058 | 跳空上涨 | open_quant_framework | pattern | factor | open, high, low, close | E2 | 高 | 无 | 低 | research | gap up |
| s2_059 | 跳空下跌 | open_quant_framework | pattern | factor | open, high, low, close | E2 | 高 | 无 | 低 | research | gap down |
| s2_060 | 突破形态 | open_quant_framework | pattern | factor | high, close, volume | E2 | 高 | 无 | 低 | MVP+ | breakout pattern |
| s2_061 | 回撤形态 | open_quant_framework | pattern | factor | close, ma | E2 | 高 | 无 | 低 | research | pullback pattern |
| s2_062 | VCP 收缩 | open_quant_framework | pattern | factor | close, volume, ATR | E2 | 高 | 无 | 低 | MVP+ | volatility contraction pattern |
| s2_063 | 涨停连板数 | open_quant_framework | pattern | factor | close, limit_up_price | E2 | 高 | 无 | 低 | MVP+ | limit-up streak count |
| s2_064 | K线形态组 | open_quant_framework | pattern | factor | OHLC | E2 | 高 | 无 | 低 | later | candlestick pattern group |
| s2_065 | Hull MA | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | research | Hull moving average |
| s2_066 | KAMA | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | research | Kaufman adaptive MA |
| s2_067 | TEMA | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | research | triple EMA |
| s2_068 | Ichimoku 云 | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 中 | later | Ichimoku cloud |
| s2_069 | Parabolic SAR | open_quant_framework | technical | factor | high, low | E2 | 高 | 无 | 低 | later | parabolic SAR |
| s2_070 | Vortex Indicator | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | later | vortex indicator |
| s2_071 | Keltner Channel | open_quant_framework | technical | factor | close, high, low | E2 | 高 | 无 | 低 | research | keltner channel |
| s2_072 | Ulcer Index | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | research | ulcer index |
| s2_073 | QQE | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | later | quantitative qualitative estimation |
| s2_074 | Schaff Trend Cycle | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | later | STC |
| s2_075 | Laguerre RSI | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | later | Laguerre RSI |
| s2_076 | WaveTrend | open_quant_framework | technical | factor | close, high, low | E2 | 高 | 无 | 低 | later | WaveTrend oscillator |
| s2_077 | Reflex | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | later | reflex indicator |
| s2_078 | Bulls Power | open_quant_framework | technical | factor | high, close, EMA | E2 | 高 | 无 | 低 | later | bulls power |
| s2_079 | Bears Power | open_quant_framework | technical | factor | low, close, EMA | E2 | 高 | 无 | 低 | later | bears power |
| s2_080 | DeMarker | open_quant_framework | technical | factor | high, low | E2 | 高 | 无 | 低 | later | DeMarker indicator |
| s2_081 | Efficiency Ratio | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | later | efficiency ratio |
| s2_082 | SR Percent Rank | open_quant_framework | technical | factor | close | E2 | 高 | 无 | 低 | later | support/resistance percent rank |
| s2_083 | Pivot Points | open_quant_framework | technical | factor | high, low, close | E2 | 高 | 无 | 低 | later | pivot levels |
| s2_084 | Fibonacci Retracement | open_quant_framework | technical | factor | high, low | E2 | 高 | 无 | 低 | later | fibo levels |
| s2_085 | Fractal | open_quant_framework | technical | factor | high, low | E2 | 高 | 无 | 低 | later | fractal pattern |



### S3: Institutional Factor Research (AQR / BlackRock / MSCI / Barra / Research Affiliates)

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s3_001 | 价值因子 | institutional_factor_research | style | factor | PB, PE, PS | E3 | 高 | 低 | 低 | MVP+ | Value (低 PB/PE/PS) |
| s3_002 | 动量因子 | institutional_factor_research | style | factor | close | E3 | 高 | 无 | 低 | MVP+ | Momentum (过去 12M 排除最近 1M) |
| s3_003 | 质量因子 | institutional_factor_research | style | factor | ROE, accruals, leverage | E3 | 高 | 低 | 低 | MVP+ | Quality (ROE 稳定、低应计) |
| s3_004 | 低波动因子 | institutional_factor_research | style | factor | close | E3 | 高 | 无 | 低 | MVP+ | Low volatility / defensive |
| s3_005 | 规模因子 | institutional_factor_research | style | factor | market_cap | E3 | 高 | 无 | 低 | MVP+ | Size (小市值效应) |
| s3_006 | 收益因子 | institutional_factor_research | style | factor | dividend_yield | E3 | 高 | 低 | 低 | research | Yield / dividend yield |
| s3_007 | 成长因子 | institutional_factor_research | style | factor | revenue_growth, profit_growth | E3 | 高 | 低 | 低 | MVP+ | Growth |
| s3_008 | 多因子动态配置 | institutional_factor_research | style | block | multiple factors | E3 | 高 | 无 | 高 | later | Dynamic factor allocation |
| s3_009 | Barra 风格因子 | institutional_factor_research | risk_model | factor | multiple | E3 | 中 | 低 | 高 | later | Barra style factors 需数据授权 |
| s3_010 | AQR 质量减垃圾 | institutional_factor_research | style | factor | profitability, growth, safety, payout | E3 | 高 | 低 | 中 | research | Quality Minus Junk (QMJ) |
| s3_011 | 股息增长因子 | institutional_factor_research | style | factor | dividend_history | E3 | 高 | 低 | 低 | later | Dividend growth |
| s3_012 | 盈利稳定性因子 | institutional_factor_research | style | factor | earnings_history | E3 | 高 | 低 | 低 | research | Earnings stability |

### S4: Academic / Empirical Factor Literature

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s4_001 | Fama-French 三因子 | academic_empirical | style | factor | market_cap, PB, close | E4 | 高 | 低 | 低 | research | SMB, HML, Mkt-RF |
| s4_002 | Fama-French 五因子 | academic_empirical | style | factor | market_cap, PB, profitability, investment | E4 | 高 | 低 | 中 | later | 加 RMW, CMA |
| s4_003 | 时间序列动量 | academic_empirical | momentum | factor | close | E4 | 高 | 无 | 低 | MVP+ | Time-series momentum |
| s4_004 | 截面动量 | academic_empirical | momentum | factor | close | E4 | 高 | 无 | 低 | MVP+ | Cross-sectional momentum |
| s4_005 | 质量减垃圾 QMJ | academic_empirical | quality | factor | multiple fundamentals | E4 | 高 | 低 | 中 | research | Quality Minus Junk |
| s4_006 | 低 Beta / 赌空 Beta | academic_empirical | risk | factor | close, index_close | E4 | 高 | 无 | 中 | research | Betting-Against-Beta |
| s4_007 | 应计异象 | academic_empirical | quality | factor | accruals, earnings | E4 | 高 | 低 | 低 | research | Accrual anomaly |
| s4_008 | 盈利公告后漂移 | academic_empirical | event | factor | earnings, close | E4 | 高 | 低 | 低 | research | PEAD |
| s4_009 | 反转因子 | academic_empirical | mean_reversion | factor | close | E4 | 高 | 无 | 低 | MVP+ | Short-term reversal |
| s4_010 | 长期反转 | academic_empirical | mean_reversion | factor | close | E4 | 高 | 无 | 低 | research | Long-term reversal |
| s4_011 | 波动率溢价 | academic_empirical | risk | factor | close | E3 | 高 | 无 | 低 | research | Volatility premium |
| s4_012 | 流动性溢价 | academic_empirical | risk | factor | volume, amount | E3 | 高 | 无 | 低 | research | Liquidity premium |

### S5: Fundamental Factors

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s5_001 | PE TTM | fundamental | valuation | factor | price, earnings_ttm | E2 | 高 | 中 | 低 | MVP+ | 需用公告日期防未来函数 |
| s5_002 | PB | fundamental | valuation | factor | price, book_value | E2 | 高 | 中 | 低 | MVP+ | 同上 |
| s5_003 | PS TTM | fundamental | valuation | factor | price, revenue_ttm | E2 | 高 | 中 | 低 | research | 需公告日期对齐 |
| s5_004 | EV/EBITDA | fundamental | valuation | factor | EV, EBITDA | E2 | 中 | 中 | 低 | later | 债务数据可得性影响 |
| s5_005 | 股息率 | fundamental | valuation | factor | dividend, price | E2 | 高 | 低 | 低 | research | Dividend yield |
| s5_006 | ROE TTM | fundamental | profitability | factor | net_profit, equity | E2 | 高 | 中 | 低 | MVP+ | 需公告日期 |
| s5_007 | ROA TTM | fundamental | profitability | factor | net_profit, assets | E2 | 高 | 中 | 低 | MVP+ | 同上 |
| s5_008 | ROIC | fundamental | profitability | factor | NOPAT, invested_capital | E2 | 中 | 中 | 低 | research | 投入资本回报率 |
| s5_009 | 毛利率 TTM | fundamental | profitability | factor | gross_profit, revenue | E2 | 高 | 中 | 低 | MVP+ | Gross margin |
| s5_010 | 净利率 TTM | fundamental | profitability | factor | net_profit, revenue | E2 | 高 | 中 | 低 | MVP+ | Net margin |
| s5_011 | 营业利润率 TTM | fundamental | profitability | factor | operating_profit, revenue | E2 | 高 | 中 | 低 | research | Operating margin |
| s5_012 | 营业收入增长率 | fundamental | growth | factor | revenue_history | E2 | 高 | 中 | 低 | MVP+ | Revenue growth YoY |
| s5_013 | 净利润增长率 | fundamental | growth | factor | net_profit_history | E2 | 高 | 中 | 低 | MVP+ | Net profit growth YoY |
| s5_014 | EPS 增长率 | fundamental | growth | factor | EPS_history | E2 | 高 | 中 | 低 | research | EPS growth YoY |
| s5_015 | 经营现金流增长率 | fundamental | growth | factor | OCF_history | E2 | 高 | 中 | 低 | research | Cash flow growth |
| s5_016 | 现金流质量 | fundamental | quality | factor | OCF, net_profit | E2 | 高 | 中 | 低 | research | Operating cash flow quality |
| s5_017 | 应计项 | fundamental | quality | factor | accruals, assets | E2 | 高 | 中 | 低 | research | Accruals / assets |
| s5_018 | 盈利稳定性 | fundamental | quality | factor | earnings_history | E2 | 高 | 中 | 低 | research | Earnings stability (std) |
| s5_019 | 资产负债率 | fundamental | leverage | factor | total_debt, total_assets | E2 | 高 | 中 | 低 | MVP+ | Debt ratio |
| s5_020 | 利息覆盖倍数 | fundamental | leverage | factor | EBIT, interest_expense | E2 | 高 | 中 | 低 | research | Interest coverage |
| s5_021 | 流动比率 | fundamental | leverage | factor | current_assets, current_liabilities | E2 | 高 | 中 | 低 | research | Current ratio |
| s5_022 | 速动比率 | fundamental | leverage | factor | quick_assets, current_liabilities | E2 | 高 | 中 | 低 | research | Quick ratio |
| s5_023 | 回购收益率 | fundamental | capital_allocation | factor | buyback, market_cap | E2 | 中 | 中 | 低 | later | Buyback yield |
| s5_024 | 研发支出占比 | fundamental | capital_allocation | factor | R&D, revenue | E2 | 高 | 中 | 低 | research | R&D intensity |
| s5_025 | 资本支出占比 | fundamental | capital_allocation | factor | capex, revenue | E2 | 高 | 中 | 低 | research | Capex intensity |

### S6: News / Event / Sentiment

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s6_001 | 新闻情绪得分 | news_event_sentiment | sentiment | factor | news_text | E1 | 中 | 低 | 高 | later | 需 NLP 模型 + 新闻源 |
| s6_002 | 公告情绪得分 | news_event_sentiment | sentiment | factor | announcement_text | E1 | 中 | 低 | 高 | later | 公告情感分析 |
| s6_003 | 研报情绪得分 | news_event_sentiment | sentiment | factor | research_report_text | E1 | 低 | 低 | 高 | later | 研报情感分析，数据稀缺 |
| s6_004 | 社媒情绪得分 | news_event_sentiment | sentiment | factor | social_media_text | E1 | 中 | 低 | 高 | later | 微博/雪球/股吧等 |
| s6_005 | 搜索热度 | news_event_sentiment | sentiment | factor | search_volume_index | E1 | 中 | 低 | 中 | later | 百度指数等代理 |
| s6_006 | 舆情热度 | news_event_sentiment | sentiment | factor | news_count, social_count | E1 | 中 | 低 | 中 | later | 舆情总量 proxy |
| s6_007 | 业绩预告事件 | news_event_sentiment | event | block | earnings_forecast | E2 | 高 | 低 | 低 | research | 业绩预告 Surprise |
| s6_008 | 并购事件 | news_event_sentiment | event | block | M&A_announcement | E2 | 中 | 低 | 低 | later | M&A event factor |
| s6_009 | 减持事件 | news_event_sentiment | event | block | insider_sell | E2 | 高 | 低 | 低 | research | 大股东减持 |
| s6_010 | 回购事件 | news_event_sentiment | event | block | buyback_announcement | E2 | 高 | 低 | 低 | research | 公司回购 |
| s6_011 | 监管处罚事件 | news_event_sentiment | event | block | regulatory_penalty | E2 | 高 | 低 | 低 | research | 监管函/处罚 |
| s6_012 | 订单/合同事件 | news_event_sentiment | event | block | contract_order | E2 | 中 | 低 | 低 | later | 重大合同公告 |
| s6_013 | 产品发布事件 | news_event_sentiment | event | block | product_launch | E2 | 中 | 低 | 低 | later | 新产品发布 |
| s6_014 | 涨跌停情绪 | news_event_sentiment | behavioral | factor | limit_up_count, limit_down_count | E2 | 高 | 无 | 低 | MVP+ | 市场整体涨停情绪 |
| s6_015 | 连板情绪 | news_event_sentiment | behavioral | factor | consecutive_limit_up | E2 | 高 | 无 | 低 | MVP+ | 最高连板数 proxy |
| s6_016 | 情绪分歧度 | news_event_sentiment | sentiment | factor | sentiment_bull_bear_ratio | E1 | 中 | 低 | 中 | later | 多空情绪分化 |

### S7: Money Flow / Order Flow / Microstructure

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s7_001 | 主力净流入 | money_flow_microstructure | money_flow | factor | 黑狼主力净流入 | E2 | 高 | 无 | 低 | MVP+ | 优先使用黑狼数据 |
| s7_002 | 大单净流入 | money_flow_microstructure | money_flow | factor | 黑狼大单数据 | E2 | 高 | 无 | 低 | MVP+ | 大单净流入 |
| s7_003 | 中单净流入 | money_flow_microstructure | money_flow | factor | 黑狼中单数据 | E2 | 高 | 无 | 低 | research | 中单净流入 |
| s7_004 | 小单净流入 | money_flow_microstructure | money_flow | factor | 黑狼小单数据 | E2 | 高 | 无 | 低 | research | 小单净流入 |
| s7_005 | 主动买入/卖出比 | money_flow_microstructure | money_flow | factor | 黑狼主买主卖 | E2 | 高 | 无 | 低 | MVP+ | 主动买卖比率 |
| s7_006 | 行业资金流排名 | money_flow_microstructure | money_flow | factor | 行业主力净流入 | E2 | 高 | 无 | 低 | MVP+ | 行业资金强弱 |
| s7_007 | 连续净流入天数 | money_flow_microstructure | money_flow | factor | 主力净流入序列 | E2 | 高 | 无 | 低 | MVP+ | consecutive inflow days |
| s7_008 | 资金流强度 | money_flow_microstructure | money_flow | factor | 主力净流入, amount | E2 | 高 | 无 | 低 | MVP+ | 净流入 / 成交额 |
| s7_009 | 资金扩散度 | money_flow_microstructure | money_flow | factor | 多行业资金流 | E2 | 高 | 无 | 中 | research | 行业资金扩散强度 |
| s7_010 | 换手率 | money_flow_microstructure | liquidity | factor | volume, shares | E2 | 高 | 无 | 低 | MVP+ | Turnover rate |
| s7_011 | Amihud 非流动性 | money_flow_microstructure | liquidity | factor | close, amount | E2 | 高 | 无 | 低 | research | Amihud illiquidity |
| s7_012 | 买卖价差代理 | money_flow_microstructure | liquidity | factor | high, low, close | E2 | 高 | 无 | 低 | research | Bid-ask spread proxy |
| s7_013 | 成交量集中度 | money_flow_microstructure | liquidity | factor | volume distribution | E2 | 高 | 无 | 低 | research | Volume concentration |
| s7_014 | Level-2 订单不平衡 | money_flow_microstructure | microstructure | factor | L2 order book | E1 | 低 | 无 | 高 | later | 需 L2 数据 |
| s7_015 | Tick Rule 买卖压力 | money_flow_microstructure | microstructure | factor | tick data | E1 | 低 | 无 | 高 | later | 需 tick 数据 |
| s7_016 | 成交额强度 | money_flow_microstructure | volume_price | factor | amount | E2 | 高 | 无 | 低 | MVP+ | amount intensity |
| s7_017 | 涨停封单量 | money_flow_microstructure | microstructure | factor | L1 data | E2 | 中 | 无 | 低 | research | 涨停板封单 proxy |
| s7_018 | 开盘跳空资金 | money_flow_microstructure | money_flow | factor | open, close, money_flow | E2 | 高 | 无 | 低 | research | 跳空伴随的资金特征 |

### S8: Trader Methodology (Blocks)

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s8_001 | Wyckoff 吸筹区检测 | trader_methodology | setup | block | close, volume, range | E2 | 高 | 无 | 中 | research | Wyckoff accumulation schematics |
| s8_002 | Wyckoff 派发区检测 | trader_methodology | setup | block | close, volume, range | E2 | 高 | 无 | 中 | research | Wyckoff distribution schematics |
| s8_003 | Wyckoff 弹簧测试 | trader_methodology | trigger | block | close, low, volume | E2 | 高 | 无 | 低 | research | spring / upthrust test |
| s8_004 | Darvas Box 上沿突破 | trader_methodology | setup+trigger | block | close, high | E2 | 高 | 无 | 低 | research | Darvas box breakout |
| s8_005 | Darvas Box 下沿跌破 | trader_methodology | invalidation | block | close, low | E2 | 高 | 无 | 低 | research | Darvas box breakdown |
| s8_006 | Minervini VCP 收缩 | trader_methodology | setup | block | close, volume, ATR | E2 | 高 | 无 | 低 | MVP+ | volatility contraction pattern |
| s8_007 | Minervini 相对强弱过滤 | trader_methodology | setup | block | close, market_close | E2 | 高 | 无 | 低 | MVP+ | relative strength rank |
| s8_008 | Minervini 趋势模板 | trader_methodology | setup | block | close, ma_50, ma_150, ma_200 | E2 | 高 | 无 | 低 | MVP+ | trend template (price>MA50>MA150>MA200) |
| s8_009 | CANSLIM C 当前季度盈利 | trader_methodology | setup | block | earnings | E2 | 高 | 中 | 低 | research | current quarterly EPS |
| s8_010 | CANSLIM A 年度盈利增长 | trader_methodology | setup | block | earnings_history | E2 | 高 | 中 | 低 | research | annual earnings growth |
| s8_011 | CANSLIM N 新产品/管理/高点 | trader_methodology | setup | block | close, high, news | E1 | 中 | 低 | 低 | later | new products/management/highs |
| s8_012 | CANSLIM S 供给与需求 | trader_methodology | setup | block | volume, shares | E2 | 高 | 无 | 低 | research | supply and demand (volume, float) |
| s8_013 | CANSLIM L 领军股 | trader_methodology | setup | block | relative_strength | E2 | 高 | 无 | 低 | research | leader or laggard |
| s8_014 | CANSLIM I 机构持股 | trader_methodology | setup | block | institutional_holdings | E1 | 低 | 低 | 低 | later | institutional sponsorship |
| s8_015 | CANSLIM M 市场方向 | trader_methodology | setup | block | index_close, state_hex | E2 | 高 | 无 | 低 | MVP+ | market direction |
| s8_016 | Livermore 关键点突破 | trader_methodology | trigger | block | close, pivot_high | E2 | 高 | 无 | 低 | research | pivotal point breakout |
| s8_017 | Livermore 自然回撤线 | trader_methodology | invalidation | block | close, pivot_low | E2 | 高 | 无 | 低 | research | natural reaction line |
| s8_018 | Turtle 20日突破入场 | trader_methodology | trigger | block | close, high_20 | E2 | 高 | 无 | 低 | MVP+ | 20-day breakout entry |
| s8_019 | Turtle 10日跌破出场 | trader_methodology | exit | block | close, low_10 | E2 | 高 | 无 | 低 | MVP+ | 10-day breakdown exit |
| s8_020 | Turtle ATR 仓位 | trader_methodology | risk | block | atr, account_value | E2 | 高 | 无 | 低 | MVP+ | 2% ATR risk sizing |
| s8_021 | O'Neil 相对强弱 | trader_methodology | setup | block | close, index_close | E2 | 高 | 无 | 低 | MVP+ | O'Neil RS rating |
| s8_022 | Weinstein 阶段分析 | trader_methodology | setup | block | close, ma_30 | E2 | 高 | 无 | 低 | research | stage 1-4 classification |
| s8_023 | Weinstein 阶段 2 确认 | trader_methodology | trigger | block | close, ma_30, volume | E2 | 高 | 无 | 低 | research | stage 2 advance confirmation |
| s8_024 | Bollinger 挤压突破 | trader_methodology | setup+trigger | block | BB_width, close | E2 | 高 | 无 | 低 | MVP+ | Bollinger squeeze breakout |
| s8_025 | Mark Douglas 风险纪律 | trader_methodology | risk | block | position_size, risk_pct | E1 | 高 | 无 | 低 | later | risk discipline block (rule-based) |
| s8_026 | 杯柄形态检测 | trader_methodology | setup | block | close, volume | E2 | 高 | 无 | 中 | research | cup-and-handle pattern |
| s8_027 | 双底形态检测 | trader_methodology | setup | block | close, volume | E2 | 高 | 无 | 中 | research | double bottom pattern |
| s8_028 | 平台突破检测 | trader_methodology | setup+trigger | block | close, high, consolidation_range | E2 | 高 | 无 | 低 | MVP+ | consolidation breakout |
| s8_029 | 吸筹量增价稳 | trader_methodology | setup | block | close, volume, range | E2 | 高 | 无 | 低 | research | volume accumulation proxy |
| s8_030 | 放量突破确认 | trader_methodology | trigger | block | close, volume, volume_ma | E2 | 高 | 无 | 低 | MVP+ | volume-confirmed breakout |

### S9: Behavioral / Psychology Factors

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s9_001 | 过度反应因子 | behavioral_psychology | mean_reversion | factor | close, return_1d | E2 | 高 | 无 | 低 | research | 大跌后反弹 proxy |
| s9_002 | 反应不足因子 | behavioral_psychology | momentum | factor | close, earnings_surprise | E2 | 高 | 无 | 低 | research | 公告后慢反应 proxy |
| s9_003 | 追涨杀跌拥挤度 | behavioral_psychology | crowdedness | factor | return_20d, volume | E2 | 高 | 无 | 低 | research | herding proxy |
| s9_004 | 恐慌抛售量 | behavioral_psychology | sentiment | factor | close, volume, return_1d | E2 | 高 | 无 | 低 | research | volume capitulation |
| s9_005 | 涨停情绪指数 | behavioral_psychology | sentiment | factor | limit_up_count, total_stocks | E2 | 高 | 无 | 低 | MVP+ | market limit-up sentiment |
| s9_006 | 连板情绪指数 | behavioral_psychology | sentiment | factor | max_consecutive_limit_up | E2 | 高 | 无 | 低 | MVP+ | max streak sentiment |
| s9_007 | 一致预期偏离 | behavioral_psychology | sentiment | factor | analyst_consensus, actual | E1 | 低 | 低 | 中 | later | consensus deviation |
| s9_008 | 亏损厌恶支撑压力 | behavioral_psychology | technical | factor | close, volume_at_price | E2 | 高 | 无 | 中 | research | volume profile support/resistance |
| s9_009 | 散户净流入反向 | behavioral_psychology | contrarian | factor | 小单净流入 | E2 | 高 | 无 | 低 | research | retail flow as contrarian |
| s9_010 | 情绪分歧度 | behavioral_psychology | sentiment | factor | limit_up_count, limit_down_count | E2 | 高 | 无 | 低 | MVP+ | up/down sentiment divergence |
| s9_011 | 波动率恐慌指数代理 | behavioral_psychology | sentiment | factor | close, return_1d_std | E2 | 高 | 无 | 低 | research | A-share VIX proxy |
| s9_012 | 创新高/新低比率 | behavioral_psychology | breadth | factor | close, high_252, low_252 | E2 | 高 | 无 | 低 | MVP+ | new high/new low ratio |

### S10: Hermass Native Sources

| id | 中文名 | source_type | category | factor_or_block | data_dependency | evidence_level | A股可得性 | future_leakage_risk | compute_cost | MVP+ / research / later | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s10_001 | MN1 State | hermass_native | state | factor | OHLCV MN1 | E3 | 高 | 无 | 中 | MVP+ | 月周期 state_hex |
| s10_002 | W1 State | hermass_native | state | factor | OHLCV W1 | E3 | 高 | 无 | 中 | MVP+ | 周周期 state_hex |
| s10_003 | D1 State | hermass_native | state | factor | OHLCV D1 | E3 | 高 | 无 | 中 | MVP+ | 日周期 state_hex |
| s10_004 | H4 State | hermass_native | state | factor | OHLCV H4 | E3 | 高 | 无 | 中 | later | 4小时 state_hex |
| s10_005 | H1 State | hermass_native | state | factor | OHLCV H1 | E3 | 高 | 无 | 中 | later | 1小时 state_hex |
| s10_006 | 多周期共振数 | hermass_native | state | factor | MN1/W1/D1/H4/H1 state | E3 | 高 | 无 | 中 | MVP+ | multi-timeframe resonance count |
| s10_007 | State 转换 | hermass_native | state | factor | state_hex sequence | E3 | 高 | 无 | 低 | research | state transition detection |
| s10_008 | EF 宽度 | hermass_native | state | factor | MN1/W1/D1/H4/H1 EF | E3 | 高 | 无 | 中 | MVP+ | expected fluctuation width |
| s10_009 | 边界距离 | hermass_native | state | factor | close, boundary | E3 | 高 | 无 | 低 | MVP+ | distance to boundary |
| s10_010 | 支撑阻力距离 | hermass_native | state | factor | close, SR_levels | E3 | 高 | 无 | 低 | research | distance to S/R |
| s10_011 | Agent 历史准确率 | hermass_native | agent | factor | agent_prediction_history | E2 | 高 | 无 | 低 | later | agent historical accuracy |
| s10_012 | 策略结果评分 | hermass_native | agent | factor | strategy_outcome_history | E2 | 高 | 无 | 低 | later | strategy outcome score |
| s10_013 | 信号衰减评分 | hermass_native | agent | factor | signal_history, decay_model | E1 | 高 | 无 | 低 | later | signal degradation score |
| s10_014 | 上游行业强度 | hermass_native | industry_chain | factor | upstream_industry_states | E2 | 高 | 无 | 中 | later | upstream strength |
| s10_015 | 下游行业强度 | hermass_native | industry_chain | factor | downstream_industry_states | E2 | 高 | 无 | 中 | later | downstream strength |
| s10_016 | 产业链共振 | hermass_native | industry_chain | factor | upstream+downstream_states | E2 | 高 | 无 | 中 | later | industry chain resonance |
| s10_017 | 行业扩散强度 | hermass_native | industry_chain | factor | industry_state_propagation | E2 | 高 | 无 | 中 | later | industry diffusion strength |
| s10_018 | 用户策略历史偏好 | hermass_native | user | factor | user_strategy_history | E1 | 高 | 无 | 低 | later | user preference proxy |

---

## Summary Statistics

| source_type | count |
|---|---|
| strategy_generator (S1) | 50 |
| open_quant_framework (S2) | 85 |
| institutional_factor_research (S3) | 12 |
| academic_empirical (S4) | 12 |
| fundamental (S5) | 25 |
| news_event_sentiment (S6) | 16 |
| money_flow_microstructure (S7) | 18 |
| trader_methodology (S8) | 30 |
| behavioral_psychology (S9) | 12 |
| hermass_native (S10) | 18 |
| **Total** | **278** |

> 目标 200+，实际产出 278 条候选 factor/block，覆盖 10 大来源类型。



---

## Trader Methodology Translation

将 10 个交易大咖/流派方法论拆解为 observable blocks。

### 1. Wyckoff Method

```json
{
  "methodology_id": "wyckoff",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["accumulation_or_distribution_zone", "trading_range_identified", "volume_drying_up"],
    "trigger": ["spring_test", "upthrust_test", "jump_across_creek"],
    "invalidation": ["breakdown_below_support", "volume_expansion_on_decline", "failed_test"],
    "risk": ["stop_below_spring_low", "position_size_limit_20pct", "no_entry_mid_range"],
    "review": ["check_volume_signature", "verify_phase_transition", "compare_to_index"]
  },
  "converted_blocks": [
    "wyckoff_accumulation_detection",
    "wyckoff_distribution_detection",
    "spring_test_trigger",
    "upthrust_test_trigger",
    "volume_drying_up_filter",
    "volume_expansion_confirm",
    "range_support_level",
    "range_resistance_level"
  ]
}
```

### 2. Darvas Box

```json
{
  "methodology_id": "darvas_box",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["price_in_box_range", "volume_increasing", "ignore_price_below_box"],
    "trigger": ["close_above_box_top_on_volume", "new_high_in_box_sequence"],
    "invalidation": ["close_below_box_bottom", "3_days_below_box"],
    "risk": ["stop_loss_below_box_bottom", "position_size_limit_20pct"],
    "review": ["box_sequence_count", "volume_trend_in_box", "sector_relative_strength"]
  },
  "converted_blocks": [
    "darvas_box_top",
    "darvas_box_bottom",
    "darvas_box_breakout_entry",
    "darvas_box_breakdown_exit",
    "volume_increasing_in_box",
    "box_sequence_counter"
  ]
}
```

### 3. Mark Minervini SEPA / VCP

```json
{
  "methodology_id": "minervini_vcp",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["trend_template_satisfied", "relative_strength_rank_top_10pct", "vcp_contraction_detected", "base_count_1_to_3"],
    "trigger": ["pivot_point_breakout_on_volume", "volume_150pct_of_avg"],
    "invalidation": ["failed_breakout_retrace_50pct", "close_below_50ma", "volume_dry_up_on_rise"],
    "risk": ["stop_loss_below_pivot_or_8pct", "position_size_limit_25pct", "no_chasing_5pct_above_pivot"],
    "review": ["post_trade_vcp_quality", "RS_rank_at_entry", "base_count_accuracy"]
  },
  "converted_blocks": [
    "trend_filter_ma_stack",
    "relative_strength_rank",
    "vcp_contraction_detector",
    "base_count_filter",
    "pivot_point_breakout",
    "volume_expansion_150pct",
    "stop_loss_pivot_or_pct",
    "no_chase_extended_filter"
  ]
}
```

### 4. William O'Neil CANSLIM

```json
{
  "methodology_id": "canslim",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["C_current_q_eps_growth_25pct+", "A_annual_eps_growth_25pct+", "N_new_product_or_high", "S_supply_demand_small_float", "L_leader_not_laggard", "I_institutional_sponsorship", "M_market_in_uptrend"],
    "trigger": ["breakout_from_sound_base_on_volume", "pocket_pivot_volume_spike"],
    "invalidation": ["breakdown_below_50ma", "failed_base_breakout", "market_correction"],
    "risk": ["stop_loss_7_to_8pct", "pyramid_up_not_down", "max_position_25pct"],
    "review": ["base_quality_score", "RS_at_breakout", "volume_pattern_score"]
  },
  "converted_blocks": [
    "current_quarter_eps_growth",
    "annual_eps_growth",
    "new_high_or_news_proxy",
    "supply_demand_float_proxy",
    "leader_relative_strength",
    "institutional_sponsorship_proxy",
    "market_uptrend_filter",
    "base_breakout_volume_confirm",
    "pocket_pivot_detector"
  ]
}
```

### 5. Jesse Livermore Pivotal Points

```json
{
  "methodology_id": "livermore",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["trend_established", "natural_rally_or_reaction_completed", "consolidation_near_high"],
    "trigger": ["breakout_above_pivotal_point", "volume_on_breakout"],
    "invalidation": ["close_below_natural_reaction_low", "reversal_line_violated", "2_days_below_pivot"],
    "risk": ["stop_below_reaction_low", "reduce_on_6pct_adverse_move", "no_avg_down"],
    "review": ["pivotal_point_accuracy", "trend_continuation_rate", "volume_confirmation_rate"]
  },
  "converted_blocks": [
    "pivotal_point_high",
    "pivotal_point_low",
    "natural_reaction_low",
    "natural_rally_high",
    "pivotal_breakout_entry",
    "reversal_line_exit",
    "no_average_down_rule"
  ]
}
```

### 6. Turtle Trading System

```json
{
  "methodology_id": "turtle",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["price_above_200ma_long", "price_below_200ma_short", "20day_range_defined"],
    "trigger": ["long_breakout_20day_high", "short_breakdown_20day_low", "55day_system2_breakout"],
    "invalidation": ["long_10day_low_exit", "short_10day_high_exit", "2N_adverse_move"],
    "risk": ["1pct_risk_per_trade", "ATR_20_position_sizing", "max_4_units", "corr_limit_4_units"],
    "review": ["win_rate_by_regime", "MAE_MFE_distribution", "skip_trade_cost"]
  },
  "converted_blocks": [
    "trend_filter_200ma",
    "donchian_20_upper",
    "donchian_20_lower",
    "donchian_55_upper",
    "donchian_55_lower",
    "donchian_10_upper",
    "donchian_10_lower",
    "atr_20_risk_sizing",
    "unit_limit_4",
    "correlation_unit_limit"
  ]
}
```

### 7. William O'Neil Relative Strength

```json
{
  "methodology_id": "oneil_rs",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["RS_rating_above_80", "price_within_25pct_of_52w_high", "market_in_confirmed_uptrend"],
    "trigger": ["breakout_from_base_on_volume", "RS_line_new_high_before_price"],
    "invalidation": ["RS_rating_drops_below_70", "price_below_50ma", "distribution_volume_pattern"],
    "risk": ["stop_loss_7_to_8pct", "never_let_profit_turn_to_loss", "pyramid_on_strength"],
    "review": ["RS_at_entry_vs_exit", "base_types_performance", "market_timing_accuracy"]
  },
  "converted_blocks": [
    "rs_rating_80_filter",
    "price_near_52w_high_filter",
    "rs_line_new_high",
    "distribution_volume_pattern",
    "base_breakout_volume",
    "pyramid_on_strength_rule"
  ]
}
```

### 8. Stan Weinstein Stage Analysis

```json
{
  "methodology_id": "weinstein_stage",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["stage_1_base_identified", "price_near_30week_ma", "volume_contracting", "sector_in_stage_2"],
    "trigger": ["price_crosses_above_30week_ma_on_volume", "RS_line_breaks_downtrend"],
    "invalidation": ["price_returns_below_30week_ma", "volume_dry_up", "sector_enters_stage_4"],
    "risk": ["stop_below_base_low_or_30ma", "position_size_per_stage", "no_stage_3_entries"],
    "review": ["stage_classification_accuracy", "sector_stage_alignment", "30ma_slope_change_rate"]
  },
  "converted_blocks": [
    "stage_1_base_detector",
    "stage_2_advance_detector",
    "stage_3_top_detector",
    "stage_4_decline_detector",
    "price_above_30wma",
    "volume_contracting_in_base",
    "sector_stage_filter",
    "rs_line_breakout"
  ]
}
```

### 9. Bollinger Volatility Squeeze

```json
{
  "methodology_id": "bollinger_squeeze",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["bb_width_at_lowest_6_months", "price_consolidating", "volume_decreasing"],
    "trigger": ["price_breaks_above_upper_band_on_volume", "bb_width_expansion"],
    "invalidation": ["price_closes_back_inside_band", "volume_fails_on_breakout", "width_continues_contracting"],
    "risk": ["stop_loss_at_middle_band", "position_size_normal", "avoid_low_volume_expansion"],
    "review": ["squeeze_duration_vs_performance", "volume_confirmation_rate", "false_breakout_rate"]
  },
  "converted_blocks": [
    "bb_width_lowest_120d",
    "bb_width_expansion",
    "bb_breakout_upper",
    "bb_breakdown_lower",
    "volume_on_bb_breakout",
    "middle_band_stop"
  ]
}
```

### 10. Mark Douglas Trading Psychology / Risk Discipline

```json
{
  "methodology_id": "mark_douglas_discipline",
  "source_type": "trader_methodology",
  "components": {
    "setup": ["edge_defined", "risk_per_trade_defined", "total_risk_budget_defined"],
    "trigger": ["setup_meets_all_criteria", "no_emotional_override"],
    "invalidation": ["risk_budget_exceeded", "consecutive_losses_3", "emotional_state_alert"],
    "risk": ["1_to_2pct_risk_per_trade", "max_6pct_total_risk", "never_move_stop_away", "accept_risk_before_entry"],
    "review": ["expectancy_calculation", "execution_quality_score", "emotional_override_log"]
  },
  "converted_blocks": [
    "risk_per_trade_limit",
    "total_risk_budget_limit",
    "consecutive_loss_cooldown",
    "stop_loss_immutable_rule",
    "expectancy_tracker",
    "execution_quality_audit"
  ]
}
```

---

## Priority Recommendation

### 先做 30 个 (Phase F0-F1: MVP+ 就绪)

优先标准：A 股数据可得性高、无未来函数、计算成本低、覆盖最广需求。

| 优先级 | id | 中文名 | 来源 | 理由 |
|---|---|---|---|---|
| 1 | s2_025 | RSI 14 | S2 | 最通用动量指标，DSL 可直接暴露 |
| 2 | s2_028 | ATR 14 | S2 | 风控和仓位计算核心 |
| 3 | s2_022 | MACD DIF | S2 | 趋势动量组合指标 |
| 4 | s2_023 | MACD DEA | S2 | MACD 信号线 |
| 5 | s2_024 | MACD Hist | S2 | MACD 柱状图 |
| 6 | s2_026 | ADX 14 | S2 | 趋势强度确认 |
| 7 | s2_031 | SuperTrend | S2 | 趋势跟踪出场 |
| 8 | s2_042 | Bollinger Bandwidth | S2 | 波动率收缩/扩张 |
| 9 | s2_043 | Bollinger %B | S2 | 价格在布林带位置 |
| 10 | s2_034 | ROC | S2 | 简单动量 |
| 11 | s2_044 | 历史波动率 20D | S2 | 波动率基准 |
| 12 | s2_050 | 成交量比率 | S2 | MVP 已有，扩展 |
| 13 | s2_051 | 成交额比率 | S2 | 量价确认 |
| 14 | s2_052 | OBV | S2 | 资金流向经典指标 |
| 15 | s2_057 | 换手率 | S2 | A 股流动性核心指标 |
| 16 | s2_003 | 5日收益率排名 | S2 | 横截面动量 |
| 17 | s2_005 | 20日收益率排名 | S2 | 中周期动量 |
| 18 | s2_008 | 行业内相对强弱排名 | S2 | 行业相对强弱 |
| 19 | s2_011 | 市值 Beta | S2 | 风险敞口测量 |
| 20 | s2_016 | Winsorize 去极值 | S2 | 因子处理必需 |
| 21 | s2_017 | Z-Score 标准化 | S2 | 因子处理必需 |
| 22 | s2_019 | 排名百分比 | S2 | 因子处理必需 |
| 23 | s3_001 | 价值因子 | S3 | 经典风格因子 |
| 24 | s3_002 | 动量因子 | S3 | 经典风格因子 |
| 25 | s3_003 | 质量因子 | S3 | 经典风格因子 |
| 26 | s3_005 | 规模因子 | S3 | A 股小市值效应显著 |
| 27 | s7_001 | 主力净流入 | S7 | A 股特色，黑狼数据已有 |
| 28 | s7_002 | 大单净流入 | S7 | A 股特色资金流 |
| 29 | s7_005 | 主动买入/卖出比 | S7 | 资金流向方向 |
| 30 | s8_024 | Bollinger 挤压突破 | S8 | 经典波动率突破策略 |

### 后做 70 个 (Phase F2-F3: 扩展层)

按类别分组：

**技术因子扩展 (20个)**
s2_027 DI+ / DI-, s2_029 NATR, s2_030 Aroon, s2_032 Donchian Upper, s2_033 Donchian Lower, s2_037 CCI, s2_038 Williams %R, s2_039 Stochastic K, s2_040 Stochastic D, s2_041 TRIX, s2_045 Parkinson 波动率, s2_046 Garman-Klass 波动率, s2_047 Rogers-Satchell 波动率, s2_048 波动率百分位, s2_053 MFI, s2_055 累积派发线, s2_056 Chaikin Money Flow, s2_058 跳空上涨, s2_059 跳空下跌, s2_060 突破形态

**横截面/处理 (10个)**
s2_004 10日收益率排名, s2_006 60日收益率排名, s2_007 120日收益率排名, s2_009 全市场相对强弱, s2_010 波动率分位数, s2_012 特质波动率, s2_013 市场相关性, s2_014 流动性风险排名, s2_015 回撤排名, s2_020 行业中性化

**出场/风控 Blocks (10个)**
s1_020 ATR 追踪止损, s1_021 Chandelier 出场, s1_025 状态失效出场, s1_044 ATR 风险仓位, s8_018 Turtle 20日突破入场, s8_019 Turtle 10日跌破出场, s8_020 Turtle ATR 仓位, s2_049 Chandelier Exit Long, s1_023 时间出场, s1_024 波动率出场

**基本面因子 (15个)**
s5_001 PE TTM, s5_002 PB, s5_006 ROE TTM, s5_007 ROA TTM, s5_009 毛利率, s5_010 净利率, s5_012 营收增长率, s5_013 净利润增长率, s5_019 资产负债率, s5_003 PS TTM, s5_004 EV/EBITDA, s5_005 股息率, s5_008 ROIC, s5_011 营业利润率, s5_014 EPS 增长率

**资金流/微观结构 (10个)**
s7_003 中单净流入, s7_004 小单净流入, s7_006 行业资金流排名, s7_007 连续净流入天数, s7_008 资金流强度, s7_009 资金扩散度, s7_010 换手率, s7_011 Amihud, s7_012 买卖价差代理, s7_016 成交额强度

**行为/情绪 (5个)**
s9_003 追涨杀跌拥挤度, s9_004 恐慌抛售量, s9_008 亏损厌恶支撑压力, s9_009 散户净流入反向, s9_012 创新高/新低比率

### Research Backlog (剩余 178 个)

按优先级排序：

1. **学术因子验证** (s4_001-s4_012)：需要先构建完整的数据管道和评估框架，再逐个验证 IC 和分层收益。
2. **新闻/事件/情绪** (s6_001-s6_016)：数据获取成本高，NLP 模型训练需要专门资源。
3. **Hermass Native 扩展** (s10_011-s10_018)：Agent Memory 和产业链数据需要先有数据积累。
4. **复杂形态识别** (s2_061-s2_064, s8_026-s8_028)：需要更复杂的算法和更多测试。
5. **Level-2 / Tick 因子** (s7_014-s7_015)：需要高频数据授权。
6. **稳健性 Blocks** (s1_032-s1_041)：需要策略生成器框架完成后才能落地。
7. **高级技术指标** (s2_065-s2_085)：大部分为研究阶段，IC 验证后再决定。
8. **机构因子扩展** (s3_006-s3_012)：需要更多数据对齐工作。

---

## Data Acquisition Gap

### 已有数据 (黑狼 / Hermass 现有)

| 数据类型 | 状态 | 来源 |
|---|---|---|
| A 股日频 OHLCV | 已有 | 黑狼 / Hermass daily release |
| 黑狼资金流 (主力/大单/中单/小单/主买主卖) | 已有 | 黑狼 moneyflow |
| State Cube (MN1/W1/D1/H4/H1) | 已有 | Hermass native |
| 行业/概念分类 | 已有 | 申万/中信/概念 |

### 缺失数据及获取路径

| 缺失数据 | 优先级 | 获取路径 | 成本/难度 | 阻塞因子 |
|---|---|---|---|---|
| **财报数据** (PE/PB/ROE/营收等) | P0 | iFinD / Tushare / Wind API | 中 | s5_001-s5_025 全部基本面因子 |
| **财报公告日期** | P0 | 同上 | 低 | 防未来函数必需 |
| **新闻/公告全文** | P1 | 爬虫 / 采购 / 财经 API | 高 | s6_001-s6_006 情绪因子 |
| **研报数据** | P1 | 慧博 / 萝卜投研 API | 高 | s6_003 研报情绪, s9_007 一致预期 |
| **社媒/股吧/雪球** | P1 | 爬虫 / 舆情服务 | 高 | s6_004 社媒情绪 |
| **搜索热度** | P2 | 百度指数 API / 代理 | 中 | s6_005 搜索热度 |
| **Level-2 订单簿** | P2 | 交易所 / 数据商 | 很高 | s7_014 L2 不平衡, s7_015 Tick Rule |
| **Tick 数据** | P2 | 交易所 / 数据商 | 很高 | s7_015 Tick Rule |
| **机构持仓** | P2 | 季报披露 / 数据商 | 中 | s8_014 CANSLIM I |
| **融资融券余额** | P2 | Tushare / 交易所 | 低 | 可新增情绪 proxy |
| **期权隐含波动率** | P3 | 上交所 / 数据商 | 中 | A 股 VIX proxy |
| **产业链图谱** | P3 | 自建 / 采购 | 高 | s10_014-s10_017 产业链因子 |
| **分析师一致预期** | P2 | Wind / iFinD | 高 | s9_007 一致预期偏离 |
| **股东户数/散户持仓** | P2 | 季报 / 数据商 | 中 | s9_009 散户反向因子 proxy |
| **大宗交易数据** | P2 | 交易所 / Tushare | 低 | 可新增资金异动因子 |
| **龙虎榜数据** | P2 | 交易所 / 爬虫 | 低 | 可新增机构行为因子 |
| **IPO / 次新股信息** | P1 | Tushare / 交易所 | 低 | 交易约束过滤 |
| **ST / 停牌 / 涨跌停状态** | P1 | Tushare / 交易所 | 低 | 交易约束过滤 |

### 数据获取时间线建议

| 阶段 | 时间 | 数据 | 解锁因子数 |
|---|---|---|---|
| Phase 0 (现在) | W1-W2 | 财报基础数据 (PE/PB/ROE/营收) | ~25 |
| Phase 1 | W3-W4 | 公告日期精确对齐 + 财报质量处理 | ~25 |
| Phase 2 | M2 | 新闻/公告情绪 (基础 NLP) | ~10 |
| Phase 3 | M3 | 社媒/搜索热度 + 龙虎榜 + 大宗 | ~10 |
| Phase 4 | M4+ | Level-2 / Tick + 产业链图谱 | ~15 |

---

## Risks

| 风险 | 等级 | 描述 | 缓解措施 |
|---|---|---|---|
| 未来函数 | 高 | 基本面因子使用财报期而非公告期 | 强制使用 announcement_date，审核所有基本面因子 |
| 幸存者偏差 | 高 | 回测只包含现存股票 | 使用历史全股票池，包含退市/ST |
| 数据窥探 (Data Snooping) | 高 | 278 个候选中必有假阳性 | 强制 out-of-sample + walk-forward + Bonferroni 校正 |
| 过拟合 | 高 | 交易方法论拆成 block 后参数过多 | 限制参数空间，强制稳健性测试 |
| 数据质量 | 中 | 黑狼资金流可能存在异常值 | 加入数据质量检查模块 |
| 计算成本爆炸 | 中 | 278 个因子同时计算 Polars/DuckDB 压力大 | 按需懒计算，预计算热点因子 |
| 情绪因子噪音 | 中 | NLP 情绪得分信噪比低 | 不单独进入生产，只作为 composite 输入 |
| A 股特性差异 | 中 | 海外经典因子在 A 股可能失效 | 每个因子必须跑 A 股 IC/分层收益 |
| 链上依赖循环 | 低 | Block 之间可能形成循环依赖 | Block registry 做 DAG 检测 |
| 回测前视偏差 | 高 | 行业分类、市值等使用当日值而非滞后值 | 所有横截面处理使用 lag-1 数据 |

---

## Next Steps For Qoder And Codex

### For Qoder (架构师)

1. **Factor Metadata Schema 定稿**
   - 基于本表的 `factor_id`, `source_type`, `category`, `level`, `frequency`, `inputs`, `required_tables`, `output_type`, `window`, `direction`, `neutralization`, `normalization`, `compute_engine`, `preview_support`, `dsl_exposure`, `status`, `version`
   - 输出到 `hermass_platform/factors/factor_schema.py`

2. **Block Metadata Schema 定稿**
   - 基于 S1/S8 的 block 定义，`block_id`, `block_type`, `parameters`, `parameter_space`, `weight`, `required_context`
   - 输出到 `hermass_platform/factors/block_schema.py`

3. **DSL 通用条件扩展**
   - `factor_threshold`, `factor_rank`, `factor_percentile`, `factor_cross`, `factor_trend`, `factor_regime_filter`, `factor_composite_score`
   - `block_signal`, `block_exit`, `block_order`

4. **Trader Methodology Block 映射**
   - 将本报告 10 个 methodology JSON 转换为 `BlockSpec` 注册表条目

### For Codex (统筹/实现)

1. **F0: Factor Registry 实现**
   - `hermass_platform/factors/factor_registry.py` — 加载本表前 30 个 MVP+ 因子
   - `hermass_platform/factors/block_registry.py` — 加载核心 block
   - `config/factors/factor_catalog.yaml` — YAML 版候选表前 30
   - `config/factors/block_catalog.yaml` — YAML 版核心 block

2. **数据管道优先**
   - 先接入财报基础数据 (PE/PB/ROE)，解锁 25 个基本面因子
   - 实现 `announcement_date` 防未来函数机制

3. **测试与验收**
   - 每个 MVP+ 因子至少一个 smoke test
   - 每个 block 至少一个组合 smoke backtest
   - Factor registry 加载测试
   - Block registry 参数空间边界测试

4. **Obsidian Vault 记录**
   - 将本报告摘要写入 `data/research/conversations/agent-runs/2026-06-06-kimi-broad-factor-source-research.md`
   - 记录决策：先做 30，后做 70，research backlog 178

### 验收标准

- [ ] Factor registry 能加载 30 个 MVP+ 因子元数据，无异常
- [ ] Block registry 能加载 20 个核心 block 元数据，无异常
- [ ] 每个 factor 有完整的 `inputs`, `required_tables`, `future_leakage_risk` 声明
- [ ] 每个 block 有 `parameter_space` 边界声明
- [ ] YAML catalog 可人工编辑，可被 registry 加载
- [ ] 至少 3 个 trader methodology 被转换为 block 组合并通过 smoke test

---

> End of Report. Total candidates: 278 factors/blocks across 10 source types.
