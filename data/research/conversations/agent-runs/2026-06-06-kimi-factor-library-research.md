# Kimi Factor Library Research

> Agent: Kimi Research Engineer  
> Date: 2026-06-06  
> Trigger: `agents/KIMI_NEXT_TASK_FACTOR_LIBRARY_RESEARCH.md`  
> Scope: 高配因子库优先级、数据依赖、评估框架、三阶段路线  
> References: `FACTOR_LIBRARY_EXPANSION_PLAN.md`, `TASK_ALLOCATION.md`, `0002-kimi-performance-data-architecture.md`

---

## Mature Project Lessons

### Qlib (Microsoft)

| 借鉴点 | Hermass 落地策略 |
|---|---|
| Alpha158 / Alpha360 标准特征集 | 吸收可解释、低未来函数风险的特征；不全部照搬 158/360 个 |
| DataHandler 统一加载/处理/归一化 | 建立 `factor_library` 模块，每个因子声明 metadata + 计算函数 + 依赖列 |
| Processor 缺失值/标准化/横截面处理 | winsorize / zscore / rank / industry_neutralize 作为 factor processors |
| Dataset 构建 (特征+标签) | 标签为 forward return，特征为 lag-1 因子值，防未来函数 |

**关键约束：** Qlib 的 Alpha 特征部分存在未来函数风险（如使用当日 close 计算标签）。Hermass 必须严格区分特征计算日和标签日。

### QuantConnect LEAN

| 借鉴点 | Hermass 落地策略 |
|---|---|
| Indicator 抽象: ingest data point -> produce value | factor registry 采用同样抽象，每个 factor 是 `update(bar) -> value` |
| 100+ 技术指标覆盖 | 优先实现 F1 的 26 个，逐步扩展至 50+ |
| 指标可复用、可组合 | 通过 `factor_threshold` / `factor_rank` / `factor_cross` 通用 DSL 条件组合 |
| 多时间框架支持 | State Cube (MN1/W1/D1/H4/H1) 作为原生多周期支持 |

### Alphalens

| 借鉴点 | Hermass 落地策略 |
|---|---|
| 因子评估 = 计算 + 评估 | 每个候选因子必须跑 IC/分层收益/多空收益/换手 |
| 分位数组合收益 tear sheet | 新增 Factor Evaluation 模块，输出 HTML/Markdown 报告 |
| 因子收益衰减分析 | 记录 factor IC 随时间衰减，作为 production gate 输入 |

### StrategyQuant X / Build 143

| 借鉴点 | Hermass 落地策略 |
|---|---|
| Building blocks 不只是指标 | Factor + Block Library：信号块、入场块、出场块、订单块、稳健性块 |
| 参数空间 + 权重 + 校准 | 每个 block 声明 parameter_space、weight、适用市场 |
| AI 生成策略 + 稳健性测试 | AI 只能组合已注册 block，生成后必须经过 Preview/Backtest/Walk-forward |
| B143 更真实的 limit fill | 预留 A 股 T+1/涨跌停/印花税/佣金模型接口 |

### TA-Lib / pandas-ta

| 借鉴点 | Hermass 落地策略 |
|---|---|
| 成熟技术指标公式 | 公式参考，但独立用 Polars/DuckDB 实现 |
| 避免引入 TA-Lib 依赖 | 减少外部依赖，保持计算透明可控 |
| 注意 proprietary formula | 黑箱指标标记为 `research` 直到独立验证 |

---

## Factor Taxonomy

### L1: Technical Factors (技术指标层)

| 子类 | 代表因子 | 计算复杂度 | A股可得性 |
|---|---|---|---|
| 趋势 | MA/EMA/MACD/ADX/SuperTrend/Donchian | 低 | 高 |
| 动量 | RSI/ROC/CCI/Stochastic/Williams%R | 低 | 高 |
| 波动 | ATR/BB/Bollinger Bandwidth/Historical Vol | 低 | 高 |
| 量价 | Volume Ratio/OBV/MFI/VWAP/Accum-Dist | 低-中 | 高 |
| 形态 | Gap/Breakout/Pullback/VCP/Limit-up streak | 中 | 高 |

### L2: Cross-Sectional Factors (横截面层)

| 子类 | 代表因子 | 计算复杂度 | A股可得性 |
|---|---|---|---|
| 收益率排名 | return_5d/10d/20d/60d/120d_rank | 低 | 高 |
| 相对强弱 | industry_rs / market_rs | 中 | 高 |
| 风险指标 | beta / idiosyncratic_vol / correlation | 中 | 高 |
| 流动性 | turnover / amihud / liquidity_rank | 低 | 高 |
| 标准化处理 | winsorize / zscore / rank_pct / industry_neutral | 低 | 高 |

### L3: Fundamental Factors (基本面层)

| 子类 | 代表因子 | 计算复杂度 | A股可得性 | 未来函数风险 |
|---|---|---|---|---|
| 估值 | PE/PB/PS/EV-EBITDA/Dividend Yield | 低 | 中-高 | **高** |
| 盈利 | ROE/ROA/ROIC/Gross Margin/Net Margin | 低 | 中-高 | **高** |
| 成长 | Revenue/EPS/Cashflow growth YoY | 低 | 中-高 | **高** |
| 质量 | Accruals/Cashflow quality/Earnings stability | 低 | 中 | **高** |
| 杠杆 | Debt ratio/Interest coverage/Current ratio | 低 | 中 | **高** |
| 资本配置 | Buyback yield/R&D intensity/Capex intensity | 低 | 低-中 | **高** |

> **L3 关键约束：** 所有基本面因子必须使用 `announcement_date` 对齐，严禁使用 `fiscal_period_end`。未解决此机制前，全部 L3 因子 `production_gate=blocked`。

### L4: Money Flow & Microstructure (资金流与微观结构)

| 子类 | 代表因子 | 计算复杂度 | A股可得性 |
|---|---|---|---|
| 主力资金流 | 主力净流入/大单净流入/连续净流入天数 | 低 | 高（黑狼） |
| 细分资金流 | 中单/小单净流入/主动买卖比 | 低 | 高（黑狼） |
| 资金流强度 | 资金流/成交额/行业资金排名 | 低 | 高 |
| 流动性 | Turnover/Amihud/Bid-ask proxy | 低 | 高 |
| 微观结构 | L2 order imbalance / Tick rule pressure | **高** | **低**（需授权） |

### L5: Hermass-Specific Factors (差异化层)

| 子类 | 代表因子 | 计算复杂度 | A股可得性 |
|---|---|---|---|
| State Cube | MN1/W1/D1/H4/H1 state | 中 | 高（自有） |
| 多周期共振 | 共振数/State transition/EF width | 低-中 | 高 |
| 边界系统 | Boundary distance/Support-Resistance distance | 低 | 高 |
| Agent Memory | Historical accuracy/Signal degradation | 低 | 中（需积累） |
| 产业链 | 上游/下游强度/产业链共振/行业扩散 | 中 | 中（需构建） |

---

## Priority Factor Table

共 55 个候选因子，按优先级分层。

### Tier 1: MVP+ Ready (F1 已有 + 立即扩展，20个)

| factor_id | 中文名 | category | level | data_dependency | window | compute_engine | precompute | mvp_plus | risks |
|---|---|---|---|---|---|---|---|---|---|
| rsi_14 | RSI 14 | technical_momentum | L1 | daily_bars.close | 14 | polars | YES | YES | 无 |
| macd_hist | MACD Histogram | technical_trend | L1 | daily_bars.close | 26/12/9 | polars | YES | YES | 无 |
| adx_14 | ADX 14 | technical_trend | L1 | daily_bars.HLC | 14 | polars | YES | YES | warmup 期长 |
| atr_14 | ATR 14 | technical_volatility | L1 | daily_bars.HLC | 14 | polars | YES | YES | 无 |
| supertrend | SuperTrend | technical_trend | L1 | daily_bars.HLC | 10 | polars | YES | YES | 递归逻辑 |
| bb_position | Bollinger Position | technical_volatility | L1 | daily_bars.close | 20 | polars | YES | YES | 无 |
| bb_bandwidth | Bollinger Bandwidth | technical_volatility | L1 | daily_bars.close | 20 | polars | YES | YES | 无 |
| roc_10 | ROC 10 | technical_momentum | L1 | daily_bars.close | 10 | polars | YES | YES | 无 |
| volume_ratio | Volume Ratio | volume_price | L1 | daily_bars.volume | 20 | polars | YES | YES | 无 |
| turnover_rate | Turnover Rate | volume_price | L1 | daily_bars.volume, shares | 1 | polars | YES | YES | shares 需历史值 |
| return_5d_rank | 5日收益率排名 | cross_sectional | L2 | daily_bars.close | 5 | polars | YES | YES | 停牌影响 |
| return_20d_rank | 20日收益率排名 | cross_sectional | L2 | daily_bars.close | 20 | polars | YES | YES | 停牌影响 |
| industry_rs_rank | 行业内相对强弱排名 | cross_sectional | L2 | daily_bars.close, industry | 20 | polars | YES | YES | 需历史行业分类 |
| volatility_20d_pct | 20日波动率百分位 | cross_sectional | L2 | daily_bars.close | 20 | polars | YES | YES | 停牌影响 |
| beta_to_index | Beta to Index | cross_sectional | L2 | daily_bars.close, index_daily | 60 | polars | YES | YES | 需指数数据 |
| main_force_net_inflow | 主力净流入 | money_flow | L4 | moneyflow_daily | 1 | polars | NO(透传) | YES | 黑狼字段对齐 |
| large_order_net_inflow | 大单净流入 | money_flow | L4 | moneyflow_daily | 1 | polars | NO(透传) | YES | 同上 |
| active_buy_sell_ratio | 主动买卖比 | money_flow | L4 | moneyflow_daily | 1 | polars | NO(透传) | YES | 同上 |
| d1_state | D1 State | hermass_state | L5 | state_cube | - | polars | NO(透传) | YES | state 定义稳定 |
| multi_timeframe_resonance | 多周期共振数 | hermass_state | L5 | state_cube | - | polars | NO(透传) | YES | state 映射需文档化 |

### Tier 2: High Value Next (F2 优先，20个)

| factor_id | 中文名 | category | level | data_dependency | window | compute_engine | precompute | mvp_plus | risks |
|---|---|---|---|---|---|---|---|---|---|
| macd_dif | MACD DIF | technical_trend | L1 | daily_bars.close | 26/12 | polars | YES | NO | 与 hist 互补 |
| macd_dea | MACD DEA | technical_trend | L1 | daily_bars.close | 26/12/9 | polars | YES | NO | 同上 |
| di_plus | DI+ | technical_trend | L1 | daily_bars.HLC | 14 | polars | YES | NO | ADX 已覆盖 |
| di_minus | DI- | technical_trend | L1 | daily_bars.HLC | 14 | polars | YES | NO | 同上 |
| aroon_up | Aroon Up | technical_trend | L1 | daily_bars.HL | 14 | polars | YES | NO | A 股有效性待验 |
| aroon_down | Aroon Down | technical_trend | L1 | daily_bars.HL | 14 | polars | YES | NO | 同上 |
| donchian_upper_20 | Donchian Upper 20 | technical_trend | L1 | daily_bars.high | 20 | polars | YES | NO | Turtle 系统组件 |
| chandelier_exit_long | Chandelier Exit Long | technical_volatility | L1 | daily_bars.HLC, atr | 22 | polars | YES | NO | 出场类 |
| obv | OBV | volume_price | L1 | daily_bars.close, volume | 1 | polars | YES | NO | 与 money_flow 重叠 |
| mfi_14 | MFI 14 | volume_price | L1 | daily_bars.HLCV | 14 | polars | YES | NO | 量价结合 |
| return_60d_rank | 60日收益率排名 | cross_sectional | L2 | daily_bars.close | 60 | polars | YES | NO | 长周期动量 |
| idiosyncratic_volatility | 特质波动率 | cross_sectional | L2 | daily_bars.close, index | 60 | polars | YES | NO | 需回归计算 |
| market_relative_strength | 全市场相对强弱 | cross_sectional | L2 | daily_bars.close, index | 20 | polars | YES | NO | 与 industry_rs 互补 |
| money_flow_intensity | 资金流强度 | money_flow | L4 | daily_bars.amount, moneyflow | 1 | polars | YES | NO | 简单 join |
| amihud_illiquidity | Amihud 非流动性 | liquidity | L4 | daily_bars.close, amount | 20 | polars | YES | NO | 停牌影响 |
| consecutive_inflow_days | 连续净流入天数 | money_flow | L4 | moneyflow_daily | 1 | polars | YES | NO | 序列计算 |
| industry_moneyflow_rank | 行业资金流排名 | money_flow | L4 | moneyflow_daily, industry | 1 | polars | YES | NO | 需行业聚合 |
| w1_state | W1 State | hermass_state | L5 | state_cube | - | polars | NO(透传) | NO | 多周期必需 |
| mn1_state | MN1 State | hermass_state | L5 | state_cube | - | polars | NO(透传) | NO | 多周期必需 |
| limit_up_sentiment_index | 涨停情绪指数 | behavioral | L2 | market_stats | 1 | polars | YES | NO | 需市场聚合表 |

### Tier 3: Research Backlog (15个)

| factor_id | 中文名 | category | level | data_dependency | window | compute_engine | precompute | mvp_plus | risks |
|---|---|---|---|---|---|---|---|---|---|
| pe_ttm | PE TTM | valuation | L3 | financial_statements, daily | TTM | polars | YES | NO | **future_leakage=high** |
| pb | PB | valuation | L3 | financial_statements, daily | 1 | polars | YES | NO | **future_leakage=high** |
| roe_ttm | ROE TTM | profitability | L3 | financial_statements | TTM | polars | YES | NO | **future_leakage=high** |
| roa_ttm | ROA TTM | profitability | L3 | financial_statements | TTM | polars | YES | NO | **future_leakage=high** |
| revenue_growth_yoy | 营收增长率 | growth | L3 | financial_statements | YoY | polars | YES | NO | **future_leakage=high** |
| profit_growth_yoy | 净利润增长率 | growth | L3 | financial_statements | YoY | polars | YES | NO | **future_leakage=high** |
| debt_ratio | 资产负债率 | leverage | L3 | financial_statements | 1 | polars | YES | NO | **future_leakage=high** |
| vcp_contraction | VCP 收缩 | pattern | L1 | daily_bars.close, volume, atr | 20 | polars | YES | NO | 形态识别精度 |
| wyckoff_spring | Wyckoff Spring | pattern | L1 | daily_bars.HLCV | 20 | polars | YES | NO | 形态识别主观性 |
| cup_and_handle | 杯柄形态 | pattern | L1 | daily_bars.close, volume | 60 | polars | YES | NO | 识别算法复杂 |
| level2_imbalance | Level-2 订单不平衡 | microstructure | L4 | level2_data | 1 | polars | NO | NO | **需 L2 数据授权** |
| tick_rule_pressure | Tick Rule 买卖压力 | microstructure | L4 | tick_data | 1 | polars | NO | NO | **需 tick 数据** |
| news_sentiment_score | 新闻情绪得分 | sentiment | L6 | news_text | 1 | mixed | NO | NO | **需 NLP 模型+数据源** |
| analyst_consensus_deviation | 一致预期偏离 | sentiment | L6 | analyst_data | 1 | polars | NO | NO | **需研报数据** |
| agent_accuracy_score | Agent 历史准确率 | hermass_agent | L5 | agent_history | 30 | polars | NO | NO | 数据积累不足 |

---

## A Share Data Availability

### 已有数据（高置信）

| 数据类型 | 来源 | 覆盖范围 | 更新频率 | 质量 |
|---|---|---|---|---|
| A 股日频 OHLCV | 黑狼 / Hermass daily | 全市场 | 日 | 高 |
| 后复权价格 | 黑狼 / Tushare | 全市场 | 日 | 高（需确认复权因子） |
| 黑狼资金流 | /wolf/money | 全市场 | 日 | 高 |
| State Cube | Hermass native | 全市场 | 日 | 高 |
| 行业分类 | 申万/中信 | 全市场 | 季 | 中（历史变更需追踪） |
| 指数行情 | 交易所 | 主要指数 | 日 | 高 |

### 部分可得（需接入）

| 数据类型 | 来源 | 覆盖范围 | 阻塞原因 |
|---|---|---|---|
| 财报基础数据 | Tushare / iFinD | 全市场 | 需 API 订阅 + announcement_date 处理 |
| 股本/流通股 | Tushare / 交易所 | 全市场 | 历史股本变更需追踪 |
| ST/停牌/涨跌停标记 | Tushare / 交易所 | 全市场 | 需整合到 daily_bars |
| 复权因子 | Tushare / 交易所 | 全市场 | 需确认与黑狼 daily 的一致性 |

### 缺失数据（中短期难获取）

| 数据类型 | 来源 | 阻塞原因 | 预计获取时间 |
|---|---|---|---|
| 新闻/公告全文 | 财经 API / 爬虫 | NLP 模型 + 数据采购成本 | M2-M3 |
| 研报数据 | 慧博 / Wind / iFinD | 需商业授权 | M3 |
| Level-2 订单簿 | 交易所 / 数据商 | 授权成本高，非日频 | M4+ |
| Tick 数据 | 交易所 / 数据商 | 授权成本高，存储大 | M4+ |
| 产业链图谱 | 自建 / 采购 | 需图谱构建 | M3-M4 |
| 社媒/股吧/雪球 | 爬虫 / 舆情服务 | 合规风险 + 信噪比低 | M3+ |

---

## Factor Evaluation Framework

### 评估维度

| 维度 | 指标 | 通过门槛 | 工具/方法 |
|---|---|---|---|
| 预测能力 | IC (Pearson) | mean > 0.02 | polars.corr |
| 预测能力 | RankIC (Spearman) | mean > 0.03 | polars.corr(method="spearman") |
| 预测稳定性 | ICIR | > 0.5 | IC_mean / IC_std |
| 分层收益 | Q5-Q1 年化收益 | > 5% | 按因子分 5 组，等权组合 |
| 多空收益 | Long-Short 年化收益 | > 3% | Top 20% - Bottom 20% |
| 换手率 | 年化换手 | < 20 倍 | 组合日频 turnover |
| 覆盖率 | 非空比例 | > 80% | 缺失率检查 |
| 缺失率 | 空值比例 | < 20% | 逐日统计 |
| 成本后收益 | 扣除双边 0.3% | > 0% | 分层收益 - 成本估计 |
| State 分层 | 各 state 下 IC | 可解释 | 按 d1_state 分组计算 IC |
| 未来函数 | 是否存在 lookahead | 必须无 | 代码审计 + 日期对齐检查 |
| 幸存者偏差 | 是否包含退市股 | 必须包含 | 历史全股票池 |

### 评估流程

```
Factor Registration (E1)
    ↓
Data Availability Check
    ↓
Future Leakage Audit
    ↓
Compute Factor Values (3+ years daily)
    ↓
IC / RankIC Calculation
    ↓
Quantile Return Spread (Q5-Q1)
    ↓
Turnover & Cost Analysis
    ↓
State Stratification
    ↓
Walk-Forward Test (optional)
    ↓
Evidence Update → E4 (candidate) / E5 (approved)
```

### 评估报告模板

```yaml
factor_id: "rsi_14"
evaluation_window: "2020-01-01 to 2025-01-01"
universe: "A_SHARE_ALL"
metrics:
  ic_mean: 0.035
  ic_std: 0.18
  icir: 0.194
  rank_ic_mean: 0.042
  rank_ic_std: 0.16
  rank_icir: 0.262
  q5_q1_annual_return: 0.08
  long_short_annual_return: 0.06
  turnover_annual: 6.5
  coverage_rate: 0.98
  missing_rate: 0.02
  cost_adjusted_return: 0.03
state_stratification:
  bullish_state_ic: 0.05
  bearish_state_ic: -0.01
  neutral_state_ic: 0.02
passed: true
failure_modes: []
validator_id: "kimi_research_engineer"
validated_at: "2026-06-06"
```

---

## Three-Stage Roadmap

### F0: Factor Registry Only (Week 1-2)

**目标：** 建立因子元数据注册表，不急着计算所有因子。

**交付：**
- `hermass_platform/factors/factor_schema.py` — Pydantic models
- `hermass_platform/factors/factor_registry.py` — 注册表 CRUD
- `hermass_platform/factors/block_schema.py` — BlockSpec models
- `hermass_platform/factors/block_registry.py` — Block 注册表
- `config/factors/factor_catalog.yaml` — Tier 1 + Tier 2 元数据
- `config/factors/block_catalog.yaml` — 核心 block 元数据
- 元数据加载测试

**验收标准：**
- [ ] 能注册/查询 factor，重复 factor_id 被拒绝
- [ ] 能注册/查询 block，重复 block_id 被拒绝
- [ ] YAML catalog 可被 loader 正确加载
- [ ] 所有 factor 有 source_refs / evidence_level / production_gate
- [ ] 所有 block 有 parameter_space 边界

### F1: Technical MVP+ (Week 3-6)

**目标：** 实现 Tier 1 的 20 个 factor 计算 + 4 个核心 exit/risk block。

**交付：**
- 20 个 factor 的 Polars 计算函数
- 预计算表 `precomputed_factors_daily`
- 4 个 block 的回测语义实现
- `factor_threshold` / `factor_rank` / `factor_percentile` 通用 DSL 条件
- 每个 factor 至少 1 个 smoke test

**新增因子（相对当前 MVP）：**
- rsi_14, macd_hist, adx_14, atr_14, supertrend, bb_position, bb_bandwidth, roc_10
- return_5d_rank, return_20d_rank, industry_rs_rank, volatility_20d_pct, beta_to_index
- main_force_net_inflow, large_order_net_inflow, active_buy_sell_ratio
- multi_timeframe_resonance

**验收标准：**
- [ ] 20 个 factor 可在 Polars 中向量化计算
- [ ] 预计算表能在 < 5s 内加载 5000×252 数据
- [ ] 每个 factor 输出与 TA-Lib/已知公式对比，误差 < 1e-6
- [ ] stop_loss_pct / take_profit_pct / atr_trailing_stop / position_size_red_line 可通过 smoke backtest

### F2: Cross-Sectional + Evaluation (Week 7-10)

**目标：** 实现 Tier 2 的 20 个 factor + Factor Evaluation 框架。

**交付：**
- 20 个 Tier 2 factor 计算函数
- Factor Evaluation 模块：IC/RankIC/分层收益/多空收益/换手/覆盖率
- 至少 10 个 factor 跑完完整评估并生成报告
- Block Library 扩展：entry/signal/filter block 各 3 个
- Walk-forward / robustness smoke 最小可用版本

**验收标准：**
- [ ] Factor Evaluation 能输出 HTML/Markdown tear sheet
- [ ] 10 个 factor 有 IC_mean / RankIC_mean / 分层收益记录
- [ ] 成本后收益不为明显负的 factor 才能进入 candidate
- [ ] 在 MN1/W1/D1 state 分层中表现可解释
- [ ] Walk-forward 至少通过 1 个简单策略

---

## Risks

| 风险 | 等级 | 描述 | 缓解 |
|---|---|---|---|
| L3 未来函数 | **高** | 基本面因子使用财报期而非公告期 | 强制 announcement_date 机制，audit 所有 L3 |
| 数据窥探 | **高** | 55 个候选中必有假阳性 | OOS + walk-forward + Bonferroni 校正 |
| 过拟合 | **高** | 参数空间过大导致 block 过拟合 | 限制 parameter_space 边界，强制稳健性测试 |
| 数据源不稳定 | 中 | 黑狼资金流字段定义可能变更 | 字段映射表 + 数据质量检查 |
| 计算成本爆炸 | 中 | 55+ factor 同时预计算压力大 | 按需懒计算，P0 优先预计算 |
| A 股特性差异 | 中 | 海外经典因子在 A 股失效 | 每个因子必须跑 A 股 IC/分层 |
| 行业分类历史 | 中 | 行业变更导致历史回测偏差 | 使用 effective_date 对齐 |
| 停牌/涨跌停 | 中 | 信号在不可交易日触发 | T+1 约束 + limit_up_filter |
| 复权不一致 | 中 | 前后复权混用导致收益率错误 | 强制后复权，复权因子同步存储 |
| 幸存者偏差 | 高 | 回测只包含现存股票 | 历史全股票池，包含退市/ST |

---

## Next Steps For Qoder And Codex

### For Qoder

1. **FactorSpec / BlockSpec 定稿**
   - 确认 Tier 1 的 20 个 factor 的 schema
   - 确认 4 个 exit/risk block 的 schema
   - 确认 `factor_threshold` / `factor_rank` / `factor_percentile` 通用 DSL 条件设计

2. **YAML Catalog 模板**
   - `config/factors/factor_catalog.yaml` — 包含 55 个 factor 元数据
   - `config/factors/block_catalog.yaml` — 包含核心 block 元数据

3. **Factor Evaluation Schema**
   - 评估报告的数据结构
   - metric_refs 的存储和查询方式

### For Codex

1. **F0: Registry 实现**
   - 按 Qoder spec 实现 `hermass_platform/factors/` 模块
   - 实现 YAML loader 和 registry CRUD
   - 实现 evidence gate / future leakage gate 校验

2. **F1: 计算函数实现**
   - 20 个 Tier 1 factor 的 Polars 计算函数
   - 预计算表 pipeline
   - 4 个 block 的回测语义

3. **F2: 评估框架**
   - Factor Evaluation 模块
   - IC/分层收益/成本分析
   - 报告生成（HTML/Markdown）

4. **测试**
   - 每个 factor 至少 1 个 smoke test（与 TA-Lib 对比）
   - 每个 block 至少 1 个组合 smoke backtest
   - 评估框架测试

---

> End of Factor Library Research. 55 candidate factors across 5 tiers. Ready for F0 registry implementation.
