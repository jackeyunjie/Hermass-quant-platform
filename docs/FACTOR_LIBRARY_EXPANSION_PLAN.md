# Hermass Factor Library Expansion Plan

## 目标

把当前 MVP 条件库扩展为高配因子库，但不牺牲可测试性、可解释性和回测性能。

目标不是堆满指标名，而是形成闭环：

因子定义 -> 数据依赖 -> 计算方式 -> 存储 schema -> DSL 条件接入 -> Preview -> Backtest -> IC/分层收益/成本评估 -> 因子版本管理。

## 借鉴对象

### Qlib

借鉴点：

- 使用标准特征集合，如 Alpha158 / Alpha360。
- DataHandler 负责统一加载、处理、归一化和数据集构建。
- Processor 负责缺失值、标准化、横截面 rank/zscore 等处理。

落地到 Hermass：

- 建立 `factor_library` 模块。
- 每个因子必须有 metadata、计算函数、依赖列、窗口、频率、可用市场。
- 横截面标准化、rank、zscore、winsorize 作为 factor processors。

### QuantConnect LEAN

借鉴点：

- 指标库覆盖非常广，技术指标和形态指标超过百个。
- Indicator 抽象强调 ingest data point -> produce value。
- 指标可复用、可组合、可被策略引用。

落地到 Hermass：

- 技术指标不直接全部进入 DSL；先进入 factor registry。
- DSL 只开放经过测试、评估和性能验证的 factor condition。
- 支持 `factor_compare`、`factor_rank`、`factor_cross`、`factor_regime_filter` 等通用条件，减少为每个指标写一个 DSL 类型。

### Alphalens

借鉴点：

- 因子不只计算，还要评估。
- 关键评估包括分位数组合收益、IC、换手、因子收益 tear sheet。

落地到 Hermass：

- 新增 Factor Evaluation。
- 每个候选因子必须跑：IC/RankIC、分层收益、多空收益、换手、覆盖率、缺失率、成本后收益、市场状态分层。
- 未通过评估的因子不能进入生产 DSL。

## 当前状态

当前只有 MVP 条件库：

- 趋势：`ma_golden_cross`、`ma_death_cross`、`price_cross_ma`
- 状态：`state_hex_in`、`state_ef_count`
- 量能：`volume_ratio`
- 行业：`industry_include`、`industry_exclude`
- 风控：`stop_loss_pct`、`take_profit_pct`
- 市场过滤：`limit_up_filter`

当前 Foundation DB MVP 预计算列：

- `ma_5`
- `ma_10`
- `ma_20`
- `ma_60`
- `bb_position`
- `atr_14`
- `volume_ratio`
- `adx_14`
- `d1_state`
- `w1_state`
- `mn1_state`

结论：足够 MVP，不够高配平台。

## 高配因子库分层

### L0 Raw Inputs

必须作为底层原始输入：

- OHLCV：open/high/low/close/volume/amount。
- 交易状态：停牌、涨跌停、是否 ST、新股天数。
- 行业/概念：申万/中信行业、概念板块。
- State Cube：MN1/W1/D1/H4/H1 state、EF 宽度、边界状态。
- 资金流：主力净流入、大单/中单/小单、主动买卖。
- 基本面：估值、盈利、成长、质量、杠杆、现金流。
- 宏观/市场：指数状态、市场宽度、成交额、风险偏好。

### L1 Technical Factors

趋势：

- MA/EMA/WMA/HMA/KAMA。
- MACD/DIF/DEA/hist。
- ADX/DI+/DI-。
- Aroon。
- SuperTrend。
- Donchian Channel。

动量：

- RSI。
- ROC/ROCP。
- Momentum。
- CCI。
- Williams %R。
- Stochastic K/D/J。
- TRIX。

波动：

- ATR/NATR。
- Bollinger bandwidth/percent_b/position。
- Historical volatility。
- Parkinson/Garman-Klass/Rogers-Satchell volatility。
- Volatility percentile。
- Chandelier Exit。

量价：

- Volume ratio。
- Amount ratio。
- OBV。
- MFI。
- VWAP deviation。
- Accumulation/Distribution。
- Chaikin Money Flow。
- Turnover rate。

形态：

- Gap up/down。
- Breakout。
- Pullback。
- VCP contraction。
- Limit-up streak。
- Candlestick pattern group。

### L2 Cross-Sectional Factors

横截面强弱：

- 5/10/20/60 日收益率排名。
- 行业内相对强弱。
- 全市场相对强弱。
- State 强度排名。
- 波动率分位数。

横截面风险：

- Beta to index。
- Idiosyncratic volatility。
- Correlation to market。
- Liquidity risk。
- Drawdown rank。

标准化处理：

- winsorize。
- zscore。
- robust zscore。
- rank percentile。
- industry neutralization。
- market beta neutralization。

### L3 Fundamental Factors

估值：

- PE/PE TTM。
- PB。
- PS。
- EV/EBITDA。
- Dividend yield。

质量：

- ROE/ROA/ROIC。
- Gross margin。
- Net margin。
- Operating cash flow quality。
- Accruals。

成长：

- Revenue growth。
- Net profit growth。
- EPS growth。
- Cash flow growth。

杠杆与安全：

- Debt ratio。
- Interest coverage。
- Current ratio。
- Quick ratio。

### L4 Money Flow And Microstructure

资金流：

- 主力净流入。
- 大单净流入。
- 主动买入/卖出比。
- 行业资金流排名。
- 连续净流入天数。

流动性：

- Turnover。
- Amihud illiquidity。
- Bid-ask proxy。
- Volume concentration。

交易约束：

- 涨跌停。
- 停牌。
- ST。
- 新股/次新。
- 单日成交额下限。

### L5 Hermass-Specific Factors

State Cube：

- MN1/W1/D1/H4/H1 state。
- 多周期共振数。
- State transition。
- EF width。
- Boundary distance。
- Support/resistance distance。

Agent Memory：

- Agent historical accuracy。
- Strategy outcome score。
- Signal degradation score。

Industry Chain：

- 上游强度。
- 下游强度。
- 产业链共振。
- 行业扩散强度。

## Factor Metadata Schema

每个因子必须声明：

```json
{
  "factor_id": "return_20d_rank",
  "name": "20日收益率横截面排名",
  "category": "cross_sectional_momentum",
  "level": "L2",
  "frequency": "D1",
  "inputs": ["close"],
  "required_tables": ["daily_bars"],
  "output_type": "numeric",
  "window": 20,
  "direction": "higher_better",
  "neutralization": ["industry_optional"],
  "normalization": ["rank_pct"],
  "compute_engine": "polars",
  "preview_support": "fully_supported",
  "dsl_exposure": "candidate",
  "status": "research",
  "version": "0.1.0"
}
```

## DSL 接入策略

不要为每个因子创建一个条件类型。优先创建通用 DSL 条件：

- `factor_threshold`
- `factor_rank`
- `factor_percentile`
- `factor_cross`
- `factor_trend`
- `factor_regime_filter`
- `factor_composite_score`

示例：

```json
{
  "condition_type": "factor_rank",
  "params": {
    "factor_id": "return_20d_rank",
    "scope": "industry",
    "operator": ">=",
    "value": 0.8
  }
}
```

## 评估准入门槛

因子进入生产 DSL 前必须至少满足：

- 覆盖率 >= 80%。
- 缺失率 <= 20%。
- 至少 3 年或足够长窗口的日频数据。
- RankIC 均值、ICIR、分层收益有记录。
- 成本后收益不为明显负。
- 在 MN1/W1/D1 state 分层中表现可解释。
- 没有明显未来函数。
- 通过 data freshness 与 survivorship bias 检查。

## 分阶段实施

### Phase F0: Factor Registry

目标：

- 建立因子元数据注册表。
- 不急着计算所有因子。

交付：

- `hermass_platform/factors/factor_registry.py`
- `hermass_platform/factors/factor_schema.py`
- `config/factors/factor_catalog.yaml`
- 因子 metadata 测试。

### Phase F1: Technical MVP+

新增因子：

- `bb_position`
- `bb_bandwidth`
- `adx_14`
- `atr_14`
- `rsi_14`
- `macd_hist`
- `turnover_rate`
- `amount_ratio`
- `return_20d`
- `return_60d`
- `volatility_20d`

### Phase F2: Cross-Sectional Layer

新增：

- rank percentile。
- industry rank。
- zscore。
- winsorization。
- neutralization。

### Phase F3: Factor Evaluation

新增：

- IC/RankIC。
- 分层收益。
- 多空收益。
- 因子换手。
- State 分层表现。
- HTML/Markdown factor report。

### Phase F4: Money Flow / Fundamental

在数据源稳定后接入：

- 资金流。
- 基本面。
- 产业链。

## 给 Agent 的分工

Kimi：

- 成熟项目研究。
- 因子分类与优先级。
- 数据依赖和计算成本。
- 因子评估方法。

Qoder：

- Factor metadata schema。
- Factor registry。
- DSL 通用条件设计。
- API/Preview 接入。

Codex：

- 统筹裁剪。
- 实现代码。
- 测试、benchmark、验收。
- 写入 Obsidian 和 GitHub。

## 原则

1. 先建 registry，再扩计算。
2. 先做日频，后做分钟。
3. 先技术/横截面，后基本面/资金流。
4. 每个因子必须能解释、能测试、能评估。
5. 因子多不等于平台强，因子评估闭环才是护城河。
