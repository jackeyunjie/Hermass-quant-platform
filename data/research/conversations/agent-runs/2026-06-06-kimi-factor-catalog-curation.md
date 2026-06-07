# Factor Catalog Curation: F0 / F1 / F2

> Agent: Kimi Research Engineer  
> Date: 2026-06-06  
> Trigger: `agents/KIMI_NEXT_TASK_FACTOR_CATALOG_CURATION.md`  
> Scope: 将 278 条广义候选压缩为可执行的 F0/F1/F2 目录草案  
> Constraints:
> - F1 精确 30 条目，不得包含 `future_leakage_risk=high` 或 `data_availability=unavailable`
> - F2 精确 70 条目
> - 不生成代码，只做元数据和目录编排

---

## 1. F0 Source Catalog YAML Draft

12 个来源注册表草案，覆盖 10 大 source_type 中的核心来源。

```yaml
sources:
  - source_id: sqx_b143_local
    source_type: strategy_generator
    name: "StrategyQuant X Build 143 (Local Snippets)"
    url_or_local_ref: "/Applications/StrategyQuantXB143.app/Contents/Resources/internal/extend/Snippets/SQ"
    reliability: high
    license_notes: "商业软件。仅参考 block 分类、命名和参数空间设计思想，不复制源码，不反编译，不执行外部 snippets。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - FUTURES
      - CRYPTO
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - signal_blocks
      - entry_blocks
      - exit_blocks
      - order_blocks
      - robustness_blocks
      - money_management
    notes: "核心参考来源。提供 block weighting、parameter space、robustness test 设计范式。A 股需适配 T+1、涨跌停、印花税。"

  - source_id: qlib
    source_type: open_quant_framework
    name: "Microsoft Qlib (Alpha158 / Alpha360)"
    url_or_local_ref: "https://github.com/microsoft/qlib"
    reliability: high
    license_notes: "MIT License。可自由参考特征工程、DataHandler、Processor 设计。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - alpha_factors
      - cross_sectional
      - feature_engineering
      - data_handler
    notes: "Alpha158/360 提供标准特征集合。Hermass 只吸收可解释、低未来函数风险的特征，不全部照搬。"

  - source_id: quantconnect_lean
    source_type: open_quant_framework
    name: "QuantConnect LEAN"
    url_or_local_ref: "https://github.com/QuantConnect/Lean"
    reliability: high
    license_notes: "Apache 2.0。可参考 Indicator 抽象和指标组合模式。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - FUTURES
      - CRYPTO
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - indicators
      - algorithm_framework
      - technical_analysis
    notes: "LEAN 的 Indicator 抽象强调 ingest data point -> produce value，与 Hermass factor registry 设计目标一致。"

  - source_id: talib_pandasta
    source_type: open_quant_framework
    name: "TA-Lib / pandas-ta"
    url_or_local_ref: "https://github.com/TA-Lib/ta-lib-python / https://github.com/twopirllc/pandas-ta"
    reliability: high
    license_notes: "BSD/MIT。可参考成熟技术指标公式，需独立用 Polars/DuckDB 实现。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - FUTURES
      - CRYPTO
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - technical_indicators
      - open_source
      - formula_reference
    notes: "技术指标公式参考。Hermass 不引入 TA-Lib 依赖，公式独立实现并审计未来函数风险。"

  - source_id: aqr
    source_type: institutional_factor
    name: "AQR Capital Management Factor Research"
    url_or_local_ref: "https://www.aqr.com/Insights/Research"
    reliability: high
    license_notes: "公开研究论文，仅参考因子定义和经济含义。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - GLOBAL
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - value
      - momentum
      - quality
      - low_beta
      - carry
    notes: "核心风格因子来源。QMJ、BAB、Time-Series Momentum 等需在 A 股做本地化验证。"

  - source_id: blackrock_factor
    source_type: institutional_factor
    name: "BlackRock / iShares Factor Research"
    url_or_local_ref: "https://www.blackrock.com/us/individual/insights/factor-investing"
    reliability: high
    license_notes: "公开因子框架文档，仅参考分类和定义。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - GLOBAL
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - style_factors
      - smart_beta
      - etf_methodology
    notes: "风格因子分类（Value/Momentum/Quality/Low Vol/Size）与 MSCI/Barra 兼容度高。"

  - source_id: msci_barra
    source_type: institutional_factor
    name: "MSCI / Barra Factor Models"
    url_or_local_ref: "https://www.msci.com/factor-investing"
    reliability: high
    license_notes: "部分模型需商业授权。Hermass 仅使用公开风格因子定义，不使用 proprietary risk model。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - GLOBAL
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - risk_model
      - barra_style
      - multifactor
    notes: "Barra 风格因子用于 L2/L3 风险归因。完整 Barra 模型数据需授权，当前只使用公开可得的风格因子代理。"

  - source_id: academic_empirical
    source_type: academic_literature
    name: "Academic Empirical Factor Literature"
    url_or_local_ref: "https://papers.ssrn.com / Journal of Finance / Journal of Financial Economics"
    reliability: medium
    license_notes: "公开发表论文，可复制研究思想，但需自行验证 A 股有效性。"
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - GLOBAL
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - fama_french
      - pead
      - accrual_anomaly
      - reversal
      - bab
    notes: "学术因子普遍存在样本外衰减和区域差异。进入生产前必须跑 A 股 IC/分层收益/成本评估。"

  - source_id: blackwolf_moneyflow
    source_type: money_flow
    name: "黑狼 A-Share Moneyflow"
    url_or_local_ref: "/wolf/money (本地) / Hermass daily release"
    reliability: high
    license_notes: "项目内部数据。Hermass 优先使用的主力/大单/中单/小单/主动买卖数据源。"
    applicable_markets:
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - main_force_flow
      - large_order
      - active_buy_sell
      - a_share_microstructure
    notes: "A 股资金流核心数据源。日频可得，分钟线待评估。主力/大单定义需与黑狼字段对齐。"

  - source_id: tushare_ifind_fundamental
    source_type: fundamental_data
    name: "Tushare / iFinD Fundamental Data"
    url_or_local_ref: "https://tushare.pro / iFinD API"
    reliability: medium
    license_notes: "数据需订阅。财报数据使用时必须使用 announcement_date 防未来函数。"
    applicable_markets:
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - financial_statements
      - valuation
      - profitability
      - growth
      - quality
    notes: "基本面因子核心数据源。关键风险：财报公告滞后。所有基本面因子必须使用 announcement_date 对齐。"

  - source_id: hermass_state_cube
    source_type: hermass_native
    name: "Hermass State Cube"
    url_or_local_ref: "hermass_platform/state_cube"
    reliability: high
    license_notes: "Hermass 自有知识产权。State 计算逻辑基于 OHLCV 和指标组件。"
    applicable_markets:
      - A_SHARE
      - FUTURES
      - CRYPTO
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - state_hex
      - multi_timeframe
      - boundary_distance
      - ef_width
    notes: "Hermass 差异化护城河。MN1/W1/D1/H4/H1 state 已可用，可作为过滤条件和风险分层维度。"

  - source_id: hermass_agent_memory
    source_type: hermass_native
    name: "Hermass Agent Memory"
    url_or_local_ref: "hermass_platform/agent_memory"
    reliability: medium
    license_notes: "Hermass 自有系统。记录 Agent 预测历史、策略结果、信号衰减。"
    applicable_markets:
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - agent_accuracy
      - strategy_outcome
      - signal_degradation
      - feedback_loop
    notes: "当前数据积累不足，短期作为 research 方向。长期目标是形成差异化 feedback loop。"
```

---

## 2. F1 MVP+ Catalog: 30 Items

筛选标准：
- A 股数据可得性 = 高
- `future_leakage_risk` ∈ {none, low, mitigated}
- 计算成本 ∈ {低, 中}
- 覆盖技术指标、横截面、资金流、Hermass Native、Exit/Risk、Robustness
- 每个条目都有 `production_gate`（当前均为 `candidate` 或 `blocked`，按 evidence 规则）

| # | id | name | factor_or_block | category | source_refs | evidence_level | data_availability | future_leakage_risk | required_tables | required_columns | compute_engine | preview_support | dsl_exposure | production_gate | reason_selected |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | rsi_14 | RSI 14 | factor | technical_momentum | talib_pandasta, qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | candidate | 最通用动量指标，数据简单，已广泛验证 |
| 2 | macd_hist | MACD Histogram | factor | technical_trend | talib_pandasta, qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | candidate | 趋势动量组合，A 股常见策略组件 |
| 3 | adx_14 | ADX 14 | factor | technical_trend | talib_pandasta, quantconnect_lean | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | candidate | 趋势强度确认，过滤震荡市 |
| 4 | atr_14 | ATR 14 | factor | technical_volatility | talib_pandasta, quantconnect_lean | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | candidate | 风控和仓位计算核心 |
| 5 | supertrend | SuperTrend | factor | technical_trend | talib_pandasta, quantconnect_lean | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | candidate | 趋势跟踪出场，与 ATR 直接关联 |
| 6 | bb_position | Bollinger Position | factor | technical_volatility | talib_pandasta, qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | candidate | 当前 MVP 预计算列，无未来函数 |
| 7 | bb_bandwidth | Bollinger Bandwidth | factor | technical_volatility | talib_pandasta, qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | candidate | 波动率收缩/扩张检测 |
| 8 | roc_10 | ROC 10 | factor | technical_momentum | talib_pandasta, qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | candidate | 简单动量，计算成本低 |
| 9 | volume_ratio | Volume Ratio | factor | volume_price | talib_pandasta, qlib | E2 | available | none | daily_bars | volume | polars | fully_supported | factor_threshold | candidate | 当前 MVP 预计算列，量价确认基础 |
| 10 | turnover_rate | Turnover Rate | factor | volume_price | talib_pandasta, blackwolf_moneyflow | E2 | available | none | daily_bars | volume, shares_outstanding | polars | fully_supported | factor_threshold | candidate | A 股流动性核心指标 |
| 11 | return_5d_rank | 5日收益率排名 | factor | cross_sectional | qlib, academic_empirical | E2 | available | none | daily_bars | close | polars | fully_supported | factor_rank | candidate | 短周期横截面动量 |
| 12 | return_20d_rank | 20日收益率排名 | factor | cross_sectional | qlib, academic_empirical | E2 | available | none | daily_bars | close | polars | fully_supported | factor_rank | candidate | 中周期横截面动量 |
| 13 | industry_rs_rank | 行业内相对强弱排名 | factor | cross_sectional | qlib, quantconnect_lean | E2 | available | none | daily_bars, industry | close, industry_code | polars | fully_supported | factor_rank | candidate | 行业内选股核心指标 |
| 14 | volatility_20d_pct | 20日波动率百分位 | factor | cross_sectional | qlib, aqr | E2 | available | none | daily_bars | close | polars | fully_supported | factor_percentile | candidate | 波动率分位数，风控和择时 |
| 15 | beta_to_index | Beta to Index | factor | cross_sectional | qlib, blackrock_factor | E2 | available | none | daily_bars, index_daily | close, index_close | polars | fully_supported | factor_threshold | candidate | 风险敞口测量 |
| 16 | main_force_net_inflow | 主力净流入 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily | main_force_net_inflow | polars | fully_supported | factor_threshold | candidate | A 股特色资金流，黑狼数据已有 |
| 17 | large_order_net_inflow | 大单净流入 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily | large_order_net_inflow | polars | fully_supported | factor_threshold | candidate | A 股特色资金流 |
| 18 | active_buy_sell_ratio | 主动买卖比 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily | active_buy, active_sell | polars | fully_supported | factor_threshold | candidate | 资金流向方向 |
| 19 | money_flow_intensity | 资金流强度 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | daily_bars, moneyflow_daily | amount, main_force_net_inflow | polars | fully_supported | factor_threshold | candidate | 标准化资金流信号 |
| 20 | amihud_illiquidity | Amihud 非流动性 | factor | liquidity | academic_empirical | E2 | available | none | daily_bars | close, amount | polars | fully_supported | factor_threshold | candidate | 流动性风险 proxy |
| 21 | d1_state | D1 State | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | d1_state | polars | fully_supported | state_hex_in | candidate | Hermass 核心状态过滤条件 |
| 22 | w1_state | W1 State | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | w1_state | polars | fully_supported | state_hex_in | candidate | 多周期共振必需 |
| 23 | mn1_state | MN1 State | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | mn1_state | polars | fully_supported | state_hex_in | candidate | 长周期趋势方向 |
| 24 | multi_timeframe_resonance | 多周期共振数 | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | mn1_state, w1_state, d1_state | polars | fully_supported | factor_threshold | candidate | Hermass 特色过滤 |
| 25 | stop_loss_pct | 固定止损百分比 | block | exit_risk | sqx_b143_local | E1 | available | none | position_context | entry_price, close | - | backtest_only | block_exit | candidate | MVP 已有，必须保留 |
| 26 | take_profit_pct | 固定止盈百分比 | block | exit_risk | sqx_b143_local | E1 | available | none | position_context | entry_price, close | - | backtest_only | block_exit | candidate | MVP 已有，必须保留 |
| 27 | atr_trailing_stop | ATR 追踪止损 | block | exit_risk | sqx_b143_local, quantconnect_lean | E2 | available | none | daily_bars, position_context | high, low, close, atr | - | backtest_only | block_exit | candidate | 动态止损，与 ATR 因子联动 |
| 28 | position_size_red_line | 仓位红线限制 | block | money_management | sqx_b143_local, hermass_native | E1 | available | none | account_context | account_value, target_pct | - | preview_supported | block_sizing | candidate | 红线系统必需，仓位上限 25% |
| 29 | factor_threshold_signal | 指标阈值信号 | block | signal | sqx_b143_local, quantconnect_lean | E1 | available | none | any_factor_table | any_numeric_factor | - | fully_supported | block_signal | candidate | 通用信号块，一个 block 覆盖 50+ 因子 |
| 30 | robustness_parameter_jitter | 参数抖动稳健块 | block | robustness | sqx_b143_local | E3 | available | none | backtest_output | parameters | - | backtest_only | robustness_test | candidate | 稳健性 smoke 最小可用单元 |

### F1 分类统计

| 类别 | 数量 | 条目 |
|---|---|---|
| Technical indicator factors | 10 | rsi_14, macd_hist, adx_14, atr_14, supertrend, bb_position, bb_bandwidth, roc_10, volume_ratio, turnover_rate |
| Cross-sectional factors | 5 | return_5d_rank, return_20d_rank, industry_rs_rank, volatility_20d_pct, beta_to_index |
| Money flow / liquidity factors | 5 | main_force_net_inflow, large_order_net_inflow, active_buy_sell_ratio, money_flow_intensity, amihud_illiquidity |
| Hermass native state factors | 4 | d1_state, w1_state, mn1_state, multi_timeframe_resonance |
| Exit / risk blocks | 4 | stop_loss_pct, take_profit_pct, atr_trailing_stop, position_size_red_line |
| Signal / robustness blocks | 2 | factor_threshold_signal, robustness_parameter_jitter |
| **Total** | **30** | |



---

## 3. F2 Candidate Catalog: 70 Items

F2 候选允许：数据暂不完整、evidence 低于生产准入、计算成本偏高。每个条目标注了进入 F2 而不是 F1 的原因。

| # | id | name | factor_or_block | category | source_refs | evidence_level | data_availability | future_leakage_risk | required_tables | required_columns | compute_engine | preview_support | dsl_exposure | production_gate | reason_in_f2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | macd_dif | MACD DIF | factor | technical_trend | talib_pandasta, qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | blocked | 与 macd_hist 重复度高，F1 已覆盖核心 |
| 2 | macd_dea | MACD DEA | factor | technical_trend | talib_pandasta, qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | blocked | 同上，作为组合项延后 |
| 3 | di_plus | DI+ | factor | technical_trend | talib_pandasta | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | ADX 已覆盖趋势强度，DI+/- 作为扩展 |
| 4 | di_minus | DI- | factor | technical_trend | talib_pandasta | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | 同上 |
| 5 | natr_14 | NATR 14 | factor | technical_volatility | talib_pandasta | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | ATR 已覆盖，NATR 为标准化扩展 |
| 6 | aroon_up | Aroon Up | factor | technical_trend | talib_pandasta, quantconnect_lean | E2 | available | none | daily_bars | high, low | polars | fully_supported | factor_threshold | blocked | 技术指标扩展，IC 验证后再决定 |
| 7 | aroon_down | Aroon Down | factor | technical_trend | talib_pandasta, quantconnect_lean | E2 | available | none | daily_bars | high, low | polars | fully_supported | factor_threshold | blocked | 同上 |
| 8 | donchian_upper_20 | Donchian Upper 20 | factor | technical_trend | quantconnect_lean, sqx_b143_local | E2 | available | none | daily_bars | high | polars | fully_supported | factor_threshold | blocked | Turtle 系统组件，可与 F1  atr_trailing_stop 组合 |
| 9 | donchian_lower_20 | Donchian Lower 20 | factor | technical_trend | quantconnect_lean, sqx_b143_local | E2 | available | none | daily_bars | low | polars | fully_supported | factor_threshold | blocked | 同上 |
| 10 | chandelier_exit_long | Chandelier Exit Long | factor | technical_volatility | talib_pandasta, sqx_b143_local | E2 | available | none | daily_bars | high, low, close, atr | polars | backtest_only | block_exit | blocked | 出场扩展，先让 atr_trailing_stop 跑通 |
| 11 | cci_20 | CCI 20 | factor | technical_momentum | talib_pandasta, quantconnect_lean | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | 动量指标扩展，A 股有效性待验证 |
| 12 | williams_r_14 | Williams %R 14 | factor | technical_momentum | talib_pandasta, quantconnect_lean | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | 与 RSI 类似，避免重复优先 RSI |
| 13 | stochastic_k_14 | Stochastic %K 14 | factor | technical_momentum | talib_pandasta | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | 技术指标扩展 |
| 14 | stochastic_d_14 | Stochastic %D 14 | factor | technical_momentum | talib_pandasta | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | 同上 |
| 15 | trix_15 | TRIX 15 | factor | technical_momentum | talib_pandasta | E2 | available | none | daily_bars | close | polars | fully_supported | factor_threshold | blocked | 动量指标扩展，计算成本略高 |
| 16 | obv | OBV | factor | volume_price | talib_pandasta, qlib | E2 | available | none | daily_bars | close, volume | polars | fully_supported | factor_threshold | blocked | 资金流向 proxy，与 money_flow 因子组有重叠 |
| 17 | mfi_14 | MFI 14 | factor | volume_price | talib_pandasta | E2 | available | none | daily_bars | high, low, close, volume | polars | fully_supported | factor_threshold | blocked | 量价结合指标，待 A 股验证 |
| 18 | vwap_deviation | VWAP Deviation | factor | volume_price | quantconnect_lean | E2 | available | none | intraday_bars | close, volume | polars | limited | factor_threshold | blocked | 需要分钟线数据，日频计算是近似 |
| 19 | accumulation_distribution | Accumulation/Distribution | factor | volume_price | talib_pandasta | E2 | available | none | daily_bars | high, low, close, volume | polars | fully_supported | factor_threshold | blocked | 资金流 proxy，评估后再决定 |
| 20 | chaikin_money_flow_20 | Chaikin Money Flow 20 | factor | volume_price | talib_pandasta | E2 | available | none | daily_bars | high, low, close, volume | polars | fully_supported | factor_threshold | blocked | 量价指标扩展 |
| 21 | gap_up | Gap Up | factor | pattern | talib_pandasta, sqx_b143_local | E2 | available | none | daily_bars | open, high, low, close | polars | fully_supported | factor_threshold | blocked | 形态类，信号稀疏 |
| 22 | gap_down | Gap Down | factor | pattern | talib_pandasta, sqx_b143_local | E2 | available | none | daily_bars | open, high, low, close | polars | fully_supported | factor_threshold | blocked | 同上 |
| 23 | breakout_20d | 20日突破 | factor | pattern | sqx_b143_local, trader_methodology | E2 | available | none | daily_bars | high, close, volume | polars | fully_supported | block_entry | blocked | 方法论组件，需要 volume confirm block |
| 24 | pullback_to_ma20 | 回撤至MA20 | factor | pattern | sqx_b143_local | E2 | available | none | daily_bars | close, ma_20 | polars | fully_supported | block_entry | blocked | 入场 block 扩展 |
| 25 | vcp_contraction | VCP 收缩 | factor | pattern | trader_methodology | E2 | available | none | daily_bars | close, volume, atr | polars | fully_supported | factor_threshold | blocked | Minervini 核心，但识别算法需更多测试 |
| 26 | limit_up_streak | 涨停连板数 | factor | pattern | sqx_b143_local | E2 | available | none | daily_bars | close, limit_up_price | polars | fully_supported | factor_threshold | blocked | A 股特色，但信号稀疏 |
| 27 | return_60d_rank | 60日收益率排名 | factor | cross_sectional | qlib, academic_empirical | E2 | available | none | daily_bars | close | polars | fully_supported | factor_rank | blocked | 长周期动量，F1 已覆盖 5D/20D |
| 28 | return_120d_rank | 120日收益率排名 | factor | cross_sectional | qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_rank | blocked | 更长周期动量 |
| 29 | market_relative_strength | 全市场相对强弱 | factor | cross_sectional | qlib, blackrock_factor | E2 | available | none | daily_bars | close, market_close | polars | fully_supported | factor_rank | blocked | 与 industry_rs_rank 互补，全市场排序 |
| 30 | idiosyncratic_volatility | 特质波动率 | factor | cross_sectional | academic_empirical | E2 | available | none | daily_bars, index_daily | close, index_close | polars | fully_supported | factor_percentile | blocked | 计算成本中等，需要 beta 回归 |
| 31 | correlation_to_market | 市场相关性 | factor | cross_sectional | qlib, blackrock_factor | E2 | available | none | daily_bars, index_daily | close, index_close | polars | fully_supported | factor_threshold | blocked | 风险指标扩展 |
| 32 | liquidity_risk_rank | 流动性风险排名 | factor | cross_sectional | qlib, academic_empirical | E2 | available | none | daily_bars | volume, amount | polars | fully_supported | factor_rank | blocked | 流动性因子，与 amihud 互补 |
| 33 | drawdown_rank | 回撤排名 | factor | cross_sectional | qlib | E2 | available | none | daily_bars | close | polars | fully_supported | factor_rank | blocked | 风险指标 |
| 34 | winsorize | Winsorize 去极值 | block | processor | qlib | E1 | available | none | any_factor_table | any_numeric_factor | polars | fully_supported | factor_processor | blocked | 因子处理必需，但属于 processor 基础设施 |
| 35 | zscore | Z-Score 标准化 | block | processor | qlib | E1 | available | none | any_factor_table | any_numeric_factor | polars | fully_supported | factor_processor | blocked | 同上 |
| 36 | rank_percentile | 排名百分比 | block | processor | qlib | E1 | available | none | any_factor_table | any_numeric_factor | polars | fully_supported | factor_processor | blocked | 同上 |
| 37 | industry_neutralize | 行业中性化 | block | processor | qlib | E1 | available | none | any_factor_table, industry | any_numeric_factor, industry_code | polars | fully_supported | factor_processor | blocked | 横截面分析必需，但属于 processor |
| 38 | pe_ttm | PE TTM | factor | valuation | tushare_ifind_fundamental, aqr | E1 | partial | high | financial_statements, daily_bars | net_profit_ttm, shares, close | polars | fully_supported | factor_threshold | blocked | 数据可得但 future_leakage 高，需 announcement_date 处理 |
| 39 | pb | PB | factor | valuation | tushare_ifind_fundamental, aqr | E1 | partial | high | financial_statements, daily_bars | book_value, shares, close | polars | fully_supported | factor_threshold | blocked | 同上 |
| 40 | roe_ttm | ROE TTM | factor | profitability | tushare_ifind_fundamental, blackrock_factor | E1 | partial | high | financial_statements | net_profit_ttm, equity | polars | fully_supported | factor_threshold | blocked | 基本面核心，但需先解决公告日期 |
| 41 | roa_ttm | ROA TTM | factor | profitability | tushare_ifind_fundamental | E1 | partial | high | financial_statements | net_profit_ttm, total_assets | polars | fully_supported | factor_threshold | blocked | 同上 |
| 42 | gross_margin_ttm | 毛利率 TTM | factor | profitability | tushare_ifind_fundamental | E1 | partial | high | financial_statements | gross_profit_ttm, revenue_ttm | polars | fully_supported | factor_threshold | blocked | 同上 |
| 43 | net_margin_ttm | 净利率 TTM | factor | profitability | tushare_ifind_fundamental | E1 | partial | high | financial_statements | net_profit_ttm, revenue_ttm | polars | fully_supported | factor_threshold | blocked | 同上 |
| 44 | revenue_growth_yoy | 营收增长率 YoY | factor | growth | tushare_ifind_fundamental | E1 | partial | high | financial_statements | revenue_ttm, revenue_ttm_ly | polars | fully_supported | factor_threshold | blocked | 同上 |
| 45 | profit_growth_yoy | 净利润增长率 YoY | factor | growth | tushare_ifind_fundamental | E1 | partial | high | financial_statements | net_profit_ttm, net_profit_ttm_ly | polars | fully_supported | factor_threshold | blocked | 同上 |
| 46 | debt_ratio | 资产负债率 | factor | leverage | tushare_ifind_fundamental | E1 | partial | high | financial_statements | total_debt, total_assets | polars | fully_supported | factor_threshold | blocked | 同上 |
| 47 | medium_order_net_inflow | 中单净流入 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily | medium_order_net_inflow | polars | fully_supported | factor_threshold | blocked | 资金流细分，IC 验证后再决定 |
| 48 | small_order_net_inflow | 小单净流入 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily | small_order_net_inflow | polars | fully_supported | factor_threshold | blocked | 同上，可作为散户反向指标 |
| 49 | industry_moneyflow_rank | 行业资金流排名 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily, industry | main_force_net_inflow, industry_code | polars | fully_supported | factor_rank | blocked | 资金流横截面，计算需行业聚合 |
| 50 | consecutive_inflow_days | 连续净流入天数 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily | main_force_net_inflow | polars | fully_supported | factor_threshold | blocked | 资金流持续性信号 |
| 51 | money_flow_diffusion | 资金扩散度 | factor | money_flow | blackwolf_moneyflow | E2 | available | none | moneyflow_daily, industry | main_force_net_inflow, industry_code | polars | fully_supported | factor_threshold | blocked | 产业链/行业间资金传播 proxy |
| 52 | volume_concentration | 成交量集中度 | factor | liquidity | academic_empirical | E2 | available | none | daily_bars | volume | polars | fully_supported | factor_threshold | blocked | 微观结构 proxy，计算略复杂 |
| 53 | bid_ask_spread_proxy | 买卖价差代理 | factor | liquidity | academic_empirical | E2 | available | none | daily_bars | high, low, close | polars | fully_supported | factor_threshold | blocked | 日频 proxy，非真实 L2 spread |
| 54 | h4_state | H4 State | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | h4_state | polars | limited | state_hex_in | blocked | 分钟/小时数据稳定性待验证 |
| 55 | h1_state | H1 State | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | h1_state | polars | limited | state_hex_in | blocked | 同上 |
| 56 | state_transition | State 转换 | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | d1_state, w1_state | polars | fully_supported | factor_threshold | blocked | 状态变化检测，需要更多历史验证 |
| 57 | ef_width | EF 宽度 | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube | ef_width | polars | fully_supported | factor_threshold | blocked | Hermass 特色，需文档化后进入 F1 |
| 58 | boundary_distance | 边界距离 | factor | hermass_state | hermass_state_cube | E3 | available | none | state_cube, daily_bars | close, boundary_upper, boundary_lower | polars | fully_supported | factor_threshold | blocked | Hermass 特色，待更多策略验证 |
| 59 | limit_up_sentiment_index | 涨停情绪指数 | factor | behavioral | sqx_b143_local | E2 | available | none | daily_bars, market_stats | limit_up_count, total_stocks | polars | fully_supported | factor_threshold | blocked | 市场情绪 proxy，需要市场聚合表 |
| 60 | consecutive_limit_up_max | 最高连板数 | factor | behavioral | sqx_b143_local | E2 | available | none | daily_bars | close, limit_up_price | polars | fully_supported | factor_threshold | blocked | A 股特色，信号稀疏 |
| 61 | new_high_new_low_ratio | 新高新低比 | factor | behavioral | academic_empirical | E2 | available | none | daily_bars | close, high_252, low_252 | polars | fully_supported | factor_threshold | blocked | 市场宽度 proxy，需全市场聚合 |
| 62 | panic_volume | 恐慌抛售量 | factor | behavioral | academic_empirical | E2 | available | none | daily_bars | close, volume, return_1d | polars | fully_supported | factor_threshold | blocked | 行为因子，样本稀疏 |
| 63 | herding_proxy | 追涨杀跌拥挤度 | factor | behavioral | academic_empirical | E2 | available | none | daily_bars | return_20d, volume | polars | fully_supported | factor_threshold | blocked | 行为因子，IC 验证后再决定 |
| 64 | wyckoff_spring_entry | Wyckoff Spring 入场 | block | trader_methodology | sqx_b143_local, trader_methodology | E2 | available | none | daily_bars | close, low, volume | polars | fully_supported | block_entry | blocked | 方法论组件，形态识别精度待验证 |
| 65 | darvas_box_breakout | Darvas Box 突破 | block | trader_methodology | sqx_b143_local, trader_methodology | E2 | available | none | daily_bars | close, high, volume | polars | fully_supported | block_entry | blocked | 同上 |
| 66 | minervini_trend_template | Minervini 趋势模板 | block | trader_methodology | trader_methodology | E2 | available | none | daily_bars | close, ma_50, ma_150, ma_200 | polars | fully_supported | block_signal | blocked | 多 MA 组合，F1 已有基本 trend filter |
| 67 | minervini_rs_filter | Minervini RS 过滤 | block | trader_methodology | trader_methodology | E2 | available | none | daily_bars, index_daily | close, index_close | polars | fully_supported | block_signal | blocked | 与 F1 market_relative_strength 类似 |
| 68 | turtle_20d_breakout_entry | Turtle 20日突破入场 | block | trader_methodology | sqx_b143_local, trader_methodology | E2 | available | none | daily_bars | close, high | polars | fully_supported | block_entry | blocked | 经典入场，但 A 股 T+1 下需适配 |
| 69 | turtle_10d_breakdown_exit | Turtle 10日跌破出场 | block | trader_methodology | sqx_b143_local, trader_methodology | E2 | available | none | daily_bars | close, low | polars | backtest_only | block_exit | blocked | 与 F1 atr_trailing_stop 有重叠 |
| 70 | weinstein_stage_2_filter | Weinstein 阶段2过滤 | block | trader_methodology | trader_methodology | E2 | available | none | daily_bars | close, ma_30 | polars | fully_supported | block_signal | blocked | 阶段识别算法待验证 |

### F2 分类统计

| 类别 | 数量 |
|---|---|
| Technical indicator factors | 15 |
| Volume / pattern factors | 12 |
| Cross-sectional / processors | 8 |
| Fundamental factors | 10 |
| Money flow / liquidity | 7 |
| Hermass native | 5 |
| Behavioral / psychology | 5 |
| Trader methodology blocks | 8 |
| **Total** | **70** |



---

## 4. Research Backlog

剩余候选按 `source_type` 分组。278 条候选中，30 条进入 F1，70 条进入 F2，剩余 **178 条** 进入 Research Backlog。

### Backlog 分组统计

| source_type | 总数 | F1 | F2 | Backlog | 代表性 backlog 条目 | 暂不进入 F1/F2 的主要原因 |
|---|---|---|---|---|---|---|
| strategy_generator (S1) | 50 | 3 | 2 | 45 | robustness_random_skip_trades, robustness_slippage_stress, better_limit_fill_model | 稳健性/执行块需要策略生成器框架完成后再实现 |
| open_quant_framework (S2) | 85 | 10 | 27 | 48 | Hull MA, KAMA, TEMA, Ichimoku, Parabolic SAR, Fibonacci Retracement, Pivot Points | 技术指标重复度高或计算复杂，优先 F1/F2 更通用指标 |
| institutional_factor_research (S3) | 12 | 0 | 0 | 12 | Barra style factors, dividend growth, earnings stability | 需要基本面数据稳定 + 更多数据授权 |
| academic_empirical (S4) | 12 | 0 | 0 | 12 | Fama-French 5 factor, BAB, accrual anomaly, PEAD, volatility premium | 需先建因子评估管道，验证 A 股有效性 |
| fundamental (S5) | 25 | 0 | 9 | 16 | PS TTM, EV/EBITDA, ROIC, interest coverage, buyback yield, R&D intensity | future_leakage_risk=high，需先解决 announcement_date 机制 |
| news_event_sentiment (S6) | 16 | 0 | 0 | 16 | 新闻情绪, 公告情绪, 研报情绪, 社媒情绪, 搜索热度, 并购事件 | 数据可得性低或需 NLP 模型，成本/精度不确定 |
| money_flow_microstructure (S7) | 18 | 5 | 7 | 6 | Level-2 order imbalance, Tick Rule buy/sell pressure, 涨停封单量 | 需要 Level-2 / Tick 数据授权 |
| trader_methodology (S8) | 30 | 1 | 8 | 21 | CANSLIM A/N/S/L/I, Wyckoff accumulation, Weinstein stage 1/3/4, Bollinger squeeze, cup-and-handle | 形态识别精度待验证，部分依赖基本面/消息面数据 |
| behavioral_psychology (S9) | 12 | 0 | 5 | 7 | 过度反应, 反应不足, 一致预期偏离, 情绪分歧度, 波动率恐慌代理 | 需要更多数据或代理指标设计 |
| hermass_native (S10) | 18 | 4 | 2 | 12 | Agent Memory, Strategy Outcome, Signal Degradation, Industry Chain, User History | Agent Memory 数据积累不足；产业链数据待构建 |
| **Total** | **278** | **30** | **70** | **178** | | |

### Backlog 重点说明

**S1 Strategy Generator Blocks (45 in backlog)**
- 大部分为高级订单类型、复杂稳健性测试、Monte Carlo 模块。
- 需要 `block_registry` + `strategy_generator` 框架完成后才能落地。
- 代表：better limit fill model, limit over/under, random execution degradation, symbol split, date split, state split.

**S2 Technical Indicators (48 in backlog)**
- 大量高级/冷门指标：Ichimoku, Parabolic SAR, Vortex, QQE, Schaff Trend Cycle, Laguerre RSI, WaveTrend, Reflex, Bulls/Bears Power, DeMarker.
- 策略：先让 F1/F2 的 52 个技术指标跑通 IC/分层收益，再逐步扩展。

**S3 + S4 Institutional / Academic (24 in backlog)**
- 经典但需严格验证：Fama-French, QMJ, BAB, accrual anomaly, PEAD.
- 策略：先建 `factor_evaluation` 管道（IC/RankIC/分层收益），逐个跑 A 股证据。

**S5 + S6 Fundamental / News (25 in backlog)**
- 核心阻塞：财报 `announcement_date` 处理机制未建立；NLP 情绪数据未采购。
- 一旦数据打通，可快速从 backlog 转入 F2/F1。

**S7 Level-2 / Microstructure (6 in backlog)**
- 核心阻塞：Level-2 和 Tick 数据授权成本高。
- 策略：日频 money flow 先跑通，分钟/tick 后做。

**S8 Trader Methodology (21 in backlog)**
- 核心阻塞：形态识别算法精度、方法论主观部分无法量化。
- 策略：先做已拆解为清晰 blocks 的（VCP、Turtle、Weinstein），后续逐步补充。

**S10 Hermass Native (12 in backlog)**
- 核心阻塞：Agent Memory 需要策略运行历史积累；产业链数据需要图谱构建。
- 策略：State Cube 优先（已在 F1），Agent/产业链作为长期护城河。

---

## 5. Selection Principles

本次 F1/F2 筛选遵循以下规则：

### 5.1 A 股数据可得性

- **F1 必须** `data_availability=available`，且数据已在 Hermass/黑狼本地可得。
- **F2 允许** `data_availability=partial`，但需明确缺失字段和补齐路径。
- **Backlog** 为 `unavailable` 或需要数据授权（Level-2、研报、NLP 模型等）。

### 5.2 未来函数风险

- **F1 绝对禁止** `future_leakage_risk=high`。
- 所有基本面因子因 `future_leakage_risk=high` 被强制放入 F2/Backlog，直到 `announcement_date` 机制落地并标记为 `mitigated`。
- State Cube、技术指标、资金流因只依赖当日及历史数据，`future_leakage_risk=none`。

### 5.3 计算成本

- **F1 优先** `compute_cost=低`，可在 Polars 中向量化快速计算。
- **F2 允许** `compute_cost=中`，如 cross-sectional rank、regression-based beta、形态识别。
- **Backlog** 包含 `compute_cost=高` 的 NLP 情绪、Tick 级计算、复杂蒙特卡洛。

### 5.4 DSL / Preview / Light Backtest 适配

- **F1 优先** 可被通用 DSL 条件表达：
  - `factor_threshold` → RSI, MACD, ADX, ATR, SuperTrend, BB, ROC, volume, turnover, money flow
  - `factor_rank` → return rank, industry RS rank
  - `factor_percentile` → volatility percentile
  - `state_hex_in` → D1/W1/MN1 state
  - `block_exit` → stop_loss_pct, take_profit_pct, atr_trailing_stop
  - `block_signal` → factor_threshold_signal
- **不为每个指标写一个 DSL condition**，F1 的 26 个 factor 通过 6-8 个通用 DSL 条件表达。

### 5.5 策略族覆盖面

F1 覆盖的策略族：

| 策略族 | F1 支持因子/Block |
|---|---|
| 趋势跟踪 | adx_14, supertrend, atr_trailing_stop, d1_state, w1_state, mn1_state |
| 动量选股 | return_5d_rank, return_20d_rank, industry_rs_rank, rsi_14, macd_hist |
| 波动率交易 | bb_position, bb_bandwidth, atr_14, volatility_20d_pct |
| 资金流选股 | main_force_net_inflow, large_order_net_inflow, active_buy_sell_ratio, money_flow_intensity |
| 多周期共振 | multi_timeframe_resonance, d1_state, w1_state, mn1_state |
| 风控与退出 | stop_loss_pct, take_profit_pct, atr_trailing_stop, position_size_red_line |
| 流动性过滤 | turnover_rate, amihud_illiquidity |

### 5.6 Hermass 自有优势

- **State Cube** 占 F1 的 4/30，是多周期共振策略的核心差异化。
- **黑狼资金流** 占 F1 的 5/30，是 A 股本土数据优势。
- **通用 Signal Block** (`factor_threshold_signal`) 保证 50+ 未来因子可通过同一 DSL 条件暴露。

---

## 6. Data Gap Notes

### Blocker（阻塞 F1 扩展）

| # | 缺失数据 | 阻塞内容 | 建议行动 |
|---|---|---|---|
| 1 | 财报基础数据 (PE/PB/ROE/ROA/营收/利润) | S5 全部 25 个基本面因子无法进入 F1 | 立即接入 Tushare / iFinD 财报 API |
| 2 | 财报 `announcement_date` | 所有基本面因子存在未来函数风险 | 在数据接入时同时获取 `announcement_date` 字段 |
| 3 | 股本/流通股数据 | turnover_rate 精确计算 | 确认黑狼 daily 是否已含 shares_outstanding，否则补充 |

### Important（影响 F2 进度）

| # | 缺失数据 | 影响内容 | 建议行动 |
|---|---|---|---|
| 4 | 指数日频数据 (沪深300/中证500等) | beta_to_index, market_relative_strength, industry_rs_rank | 接入指数行情数据 |
| 5 | 行业分类历史数据 | industry_neutralize, industry_rs_rank, industry_moneyflow_rank | 获取历史行业分类表（申万/中信） |
| 6 | 分钟线 OHLCV | vwap_deviation, h4_state, h1_state | 评估接入分钟线数据的成本 |
| 7 | 市场聚合统计 (涨停数/跌停数/总股票数) | limit_up_sentiment_index, new_high_new_low_ratio | 构建每日市场统计表 |
| 8 | 复权因子 | 所有收益率计算 | 确认 close 已经是后复权，否则补充 adj_factor |

### Nice-to-have（增强 backlog）

| # | 缺失数据 | 影响内容 | 优先级 |
|---|---|---|---|
| 9 | 新闻/公告全文 | S6 新闻情绪、公告事件 | M2 |
| 10 | 研报数据 | S6 研报情绪、一致预期 | M3 |
| 11 | 社媒/股吧/雪球 | S6 社媒情绪 | M3 |
| 12 | 搜索热度 (百度指数等) | S6 搜索热度 | M4 |
| 13 | Level-2 订单簿 | S7 order imbalance, spread | M4 |
| 14 | Tick 数据 | S7 tick rule pressure | M4 |
| 15 | 产业链图谱 | S10 上游/下游/共振 | M4 |
| 16 | Agent Memory 历史 | S10 agent accuracy, outcome score | 随系统运行自然积累 |

---

## 7. For Qoder: Registry Ready Checklist

以下 F1 条目可直接进入 `FactorSpec` / `BlockSpec` registry 规格设计：

### 可直接进入 Factor Registry 的 26 个 F1 条目

```
rsi_14, macd_hist, adx_14, atr_14, supertrend, bb_position, bb_bandwidth,
roc_10, volume_ratio, turnover_rate,
return_5d_rank, return_20d_rank, industry_rs_rank, volatility_20d_pct, beta_to_index,
main_force_net_inflow, large_order_net_inflow, active_buy_sell_ratio, money_flow_intensity, amihud_illiquidity,
d1_state, w1_state, mn1_state, multi_timeframe_resonance
```

### 可直接进入 Block Registry 的 4 个 F1 条目

```
stop_loss_pct, take_profit_pct, atr_trailing_stop, position_size_red_line
```

### 需要额外 DSL 设计的 2 个 F1 Block

```
factor_threshold_signal    → 需要 factor_ref 参数类型
robustness_parameter_jitter → 需要 robustness 测试框架
```

### F2 中可提前设计 schema 但 blocked 的条目

- 全部 70 个 F2 条目可先注册为 `status: research`、`production_gate: blocked`。
- 基本面类（pe_ttm, pb, roe_ttm 等）需等 `announcement_date` 机制落地后改为 `future_leakage_risk: mitigated`。
- 方法论类 block（wyckoff_spring_entry, darvas_box_breakout 等）需等形态识别算法验证后提升 evidence。

---

## 8. Summary

| 层级 | 数量 | 核心目标 | 下一步 |
|---|---|---|---|
| **F0 Source Catalog** | 12 sources | 来源治理清晰 | Codex 实现 `source_registry.py` + `source_catalog.yaml` |
| **F1 MVP+ Catalog** | 30 items | 可立即进入代码和 DSL | Qoder 设计 `FactorSpec`/`BlockSpec`，Codex 实现 registry |
| **F2 Candidate Catalog** | 70 items | 下一批研究与实现 | 等待数据补齐/证据提升后逐步迁移 |
| **Research Backlog** | 178 items | 长期研究与扩展 | 按数据获取时间线逐步筛选 |

**关键决策：**
1. 基本面因子因 `future_leakage_risk=high` 全部被 blocking，直到 `announcement_date` 机制落地。
2. 情绪/事件类因子因数据可得性低全部留在 backlog。
3. 技术指标通过 `factor_threshold` 等 6-8 个通用 DSL 条件表达，不单独为每个指标创建 condition。
4. State Cube 和资金流作为 Hermass 差异化优势优先进入 F1。

---

> End of Curation Report. F0=12 sources, F1=30 items, F2=70 items, Backlog=178 items. Ready for Qoder registry schema and Codex implementation.
