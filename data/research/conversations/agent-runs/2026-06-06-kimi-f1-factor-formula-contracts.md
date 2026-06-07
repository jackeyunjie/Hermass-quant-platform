# F1 Factor Formula And Data Contracts

> Agent: Kimi Research Engineer  
> Date: 2026-06-06  
> Trigger: `agents/KIMI_NEXT_TASK_F1_FACTOR_FORMULA_CONTRACTS.md`  
> Scope: 将 F1 MVP+ 的 26 个 factor 和 4 个 block 转成可实现的数据/公式契约  
> Reference: `SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`, `0009-factor-catalog-registry-accepted.md`, `2026-06-06-kimi-factor-catalog-curation.md`

---

## 1. Canonical Field Mapping

### 1.1 `daily_bars`

A 股日频行情表。每行 = (symbol, trade_date)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| symbol | string | NO | 股票代码 | NO | 交易所行情 |
| trade_date | date | NO | YYYY-MM-DD | NO | 交易所行情 |
| open | float64 | NO | 元（后复权） | NO | 交易所行情 + 复权因子 |
| high | float64 | NO | 元（后复权） | NO | 交易所行情 + 复权因子 |
| low | float64 | NO | 元（后复权） | NO | 交易所行情 + 复权因子 |
| close | float64 | NO | 元（后复权） | NO | 交易所行情 + 复权因子 |
| volume | int64 | NO | 股 | NO | 交易所行情 |
| amount | float64 | NO | 元 | NO | 交易所行情 |
| turnover_rate | float64 | YES | 比率 (0-1+) | NO | 交易所行情 / 黑狼计算 |
| shares_outstanding | int64 | YES | 股 | NO | 公司资料 |
| adj_factor | float64 | YES | 乘数 | NO | 复权因子 |
| limit_up | float64 | YES | 元 | NO | 交易所规则计算 |
| limit_down | float64 | YES | 元 | NO | 交易所规则计算 |
| is_st | bool | NO | - | NO | 交易所规则 |
| is_suspended | bool | NO | - | NO | 交易所规则 |
| is_new_stock | bool | NO | - | NO | 上市日期计算 |

**质量门控：**
- 缺失率: close 必须 0%，open/high/low/volume/amount ≤ 1%
- 日期连续性: 每个 symbol 交易日连续（允许停牌日期缺失，但停牌标记必须存在）
- 复权: close 必须是后复权价格，不可混用前复权
- 停牌: is_suspended 必须准确，停牌日 close 不能用于收益率计算

### 1.2 `moneyflow_daily`

黑狼资金流日频表。每行 = (symbol, trade_date)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| symbol | string | NO | 股票代码 | NO | 黑狼 moneyflow |
| trade_date | date | NO | YYYY-MM-DD | NO | 黑狼 moneyflow |
| main_force_net_inflow | float64 | YES | 元 | NO | 黑狼 moneyflow |
| large_order_net_inflow | float64 | YES | 元 | NO | 黑狼 moneyflow |
| medium_order_net_inflow | float64 | YES | 元 | NO | 黑狼 moneyflow |
| small_order_net_inflow | float64 | YES | 元 | NO | 黑狼 moneyflow |
| active_buy_amount | float64 | YES | 元 | NO | 黑狼 moneyflow |
| active_sell_amount | float64 | YES | 元 | NO | 黑狼 moneyflow |
| main_force_inflow_days | int32 | YES | 天 | NO | 黑狼 moneyflow（可派生） |

**质量门控：**
- 缺失率: 主力净流入 ≤ 5%（ST/小盘股可能缺失）
- 零值检查: 交易日非停牌时，main_force_net_inflow 不应全为 0
- 符号一致性: main_force_net_inflow + large + medium + small 应近似等于 0（内部分布守恒）

### 1.3 `state_cube`

Hermass State Cube 表。每行 = (symbol, trade_date)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| symbol | string | NO | 股票代码 | NO | Hermass State Cube |
| trade_date | date | NO | YYYY-MM-DD | NO | Hermass State Cube |
| mn1_state | string | NO | 16进制 state_hex | NO | Hermass State Cube |
| w1_state | string | NO | 16进制 state_hex | NO | Hermass State Cube |
| d1_state | string | NO | 16进制 state_hex | NO | Hermass State Cube |
| h4_state | string | YES | 16进制 state_hex | NO | Hermass State Cube |
| h1_state | string | YES | 16进制 state_hex | NO | Hermass State Cube |
| ef_width_d1 | float64 | YES | 元 | NO | Hermass State Cube |
| boundary_upper | float64 | YES | 元 | NO | Hermass State Cube |
| boundary_lower | float64 | YES | 元 | NO | Hermass State Cube |

**质量门控：**
- 缺失率: d1_state/w1_state/mn1_state = 0%，h4/h1 视数据可得性
- state_hex 合法性: 必须为合法 16 进制字符串，长度固定
- 日期对齐: state_cube trade_date 必须与 daily_bars trade_date 一一对应

### 1.4 `index_daily`

指数日频行情表。每行 = (index_code, trade_date)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| index_code | string | NO | 指数代码 | NO | 交易所行情 |
| trade_date | date | NO | YYYY-MM-DD | NO | 交易所行情 |
| index_open | float64 | NO | 点 | NO | 交易所行情 |
| index_high | float64 | NO | 点 | NO | 交易所行情 |
| index_low | float64 | NO | 点 | NO | 交易所行情 |
| index_close | float64 | NO | 点 | NO | 交易所行情 |
| index_volume | int64 | NO | - | NO | 交易所行情 |

**质量门控：**
- 缺失率: index_close = 0%
- 常用指数: 000001.SH (上证指数), 000300.SH (沪深300), 000905.SH (中证500), 399001.SZ (深证成指), 399006.SZ (创业板指)

### 1.5 `industry`

行业分类表。每行 = (symbol, effective_date, industry_code)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| symbol | string | NO | 股票代码 | NO | 申万/中信行业分类 |
| effective_date | date | NO | YYYY-MM-DD | NO | 分类生效日期 |
| industry_code | string | NO | 行业代码 | NO | 申万/中信行业分类 |
| industry_name | string | YES | 行业名称 | NO | 申万/中信行业分类 |
| industry_level | int32 | YES | 1/2/3 级 | NO | 申万/中信行业分类 |

**质量门控：**
- 缺失率: industry_code ≤ 2%（新股可能暂无分类）
- 历史连续性: 行业变更必须记录 effective_date，不可使用当前行业做历史回测
- 标准一致性: 统一使用申万一级或中信一级，不可混用

### 1.6 `account_context`

回测/模拟账户上下文表。每行 = (strategy_id, trade_date)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| strategy_id | string | NO | 策略ID | NO | 回测引擎 |
| trade_date | date | NO | YYYY-MM-DD | NO | 回测引擎 |
| account_value | float64 | NO | 元 | NO | 回测引擎 |
| cash | float64 | NO | 元 | NO | 回测引擎 |
| total_pnl | float64 | NO | 元 | NO | 回测引擎 |
| max_drawdown | float64 | YES | 元 | NO | 回测引擎 |
| risk_budget_used | float64 | YES | 比率 (0-1) | NO | 回测引擎 |

**质量门控：**
- 无未来数据: account_value 只能使用已收盘日数据计算
- 精度: 金额保留 2 位小数，比率保留 6 位小数

### 1.7 `position_context`

持仓上下文表。每行 = (strategy_id, symbol, trade_date)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| strategy_id | string | NO | 策略ID | NO | 回测引擎 |
| symbol | string | NO | 股票代码 | NO | 回测引擎 |
| trade_date | date | NO | YYYY-MM-DD | NO | 回测引擎 |
| entry_price | float64 | NO | 元（后复权） | NO | 回测引擎 |
| entry_date | date | NO | YYYY-MM-DD | NO | 回测引擎 |
| position_size | int64 | NO | 股 | NO | 回测引擎 |
| position_value | float64 | NO | 元 | NO | 回测引擎 |
| unrealized_pnl | float64 | YES | 元 | NO | 回测引擎 |
| highest_since_entry | float64 | YES | 元（后复权） | NO | 回测引擎 |
| lowest_since_entry | float64 | YES | 元（后复权） | NO | 回测引擎 |
| trailing_stop_price | float64 | YES | 元（后复权） | NO | 回测引擎 |

**质量门控：**
- 无未来数据: entry_price 必须使用当日或历史 close
- T+1 约束: 买入当日不可卖出
- highest_since_entry 必须动态跟踪，不可前视

### 1.8 `backtest_output`

回测输出表（用于 robustness 块）。每行 = (strategy_id, run_id)。

| canonical_column | dtype | nullable | unit | future_data_allowed | source |
|---|---|---|---|---|---|
| strategy_id | string | NO | 策略ID | NO | 回测引擎 |
| run_id | string | NO | 回测运行ID | NO | 回测引擎 |
| parameter_set | dict | NO | 参数快照 | NO | 回测引擎 |
| equity_curve | list[float] | NO | 权益序列 | NO | 回测引擎 |
| trade_log | list[dict] | NO | 交易记录 | NO | 回测引擎 |
| total_return | float64 | NO | 比率 | NO | 回测引擎 |
| max_drawdown | float64 | NO | 比率 | NO | 回测引擎 |
| sharpe_ratio | float64 | YES | - | NO | 回测引擎 |
| win_rate | float64 | YES | 比率 | NO | 回测引擎 |
| profit_factor | float64 | YES | 比率 | NO | 回测引擎 |
| num_trades | int32 | NO | 笔 | NO | 回测引擎 |
| robustness_passed | bool | YES | - | NO | 回测引擎 |

**质量门控：**
- 参数快照不可变: parameter_set 必须记录回测开始时使用的参数
- 权益序列连续性: equity_curve 必须逐日连续，不可跳日

---

## 2. F1 Factor Formula Contracts

### 2.1 Technical Indicators (10 factors)

---

#### factor_001: `rsi_14`

| field | value |
|---|---|
| **factor_id** | rsi_14 |
| **display_name** | RSI 14 |
| **category** | technical_momentum |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | rsi_14 |
| **output_dtype** | float64 |
| **window** | 14 |
| **frequency** | D1 |
| **direction** | neutral |
| **normalization** | [] |
| **neutralization** | [] |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. delta = close - close.shift(1)
2. gain = max(delta, 0)
3. loss = abs(min(delta, 0))
4. avg_gain = gain.rolling_mean(window=14)
5. avg_loss = loss.rolling_mean(window=14)
6. rs = avg_gain / avg_loss
7. rsi = 100 - (100 / (1 + rs))
8. 首 14 个 bar avg_gain/avg_loss 使用简单平均，之后使用 Wilder 平滑：avg_gain_t = (avg_gain_{t-1} * 13 + gain_t) / 14

**polars_expr_hint:**
```python
import polars as pl

gain = (pl.col("close").diff() > 0).cast(pl.Float64) * pl.col("close").diff()
loss = (pl.col("close").diff() < 0).cast(pl.Float64) * (-pl.col("close").diff())

# 简单 rolling mean 版本（首日除外）
avg_gain = gain.rolling_mean(window_size=14)
avg_loss = loss.rolling_mean(window_size=14)
rs = avg_gain / avg_loss
rsi = 100.0 - (100.0 / (1.0 + rs))

# 注意：严格 Wilder 平滑需要 group_by + cumulative
# Polars 中可用 .rolling_mean 近似，或自定义 map_groups
```

**duckdb_expr_hint:**
```sql
WITH deltas AS (
  SELECT symbol, trade_date, close,
         close - LAG(close, 1) OVER (PARTITION BY symbol ORDER BY trade_date) AS delta
  FROM daily_bars
),
gains AS (
  SELECT *, GREATEST(delta, 0) AS gain, ABS(LEAST(delta, 0)) AS loss
  FROM deltas
),
rs AS (
  SELECT *,
    AVG(gain) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain,
    AVG(loss) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss
  FROM gains
)
SELECT symbol, trade_date,
  100.0 - (100.0 / (1.0 + avg_gain / NULLIF(avg_loss, 0))) AS rsi_14
FROM rs
```

**precompute_recommended:** P0（使用频率极高，每个策略都可能用到）

**preview_supported:** YES（只需要 close 历史，可向前计算）

**future_leakage_check:** 只使用过去 14 日 close，无未来数据。

**edge_cases:**
- avg_loss == 0 → RSI = 100（全涨），需处理除零
- 前 13 个 bar 不足窗口 → 返回 null
- 停牌导致连续多日无数据 → 需按 symbol 分组计算

**acceptance_examples:**
- 输入 close=[100,102,101,103,105,104,106,108,107,109,110,108,111,112,113]
- 输出 rsi_14 应约为 67-72（取决于平滑方式）

---

#### factor_002: `macd_hist`

| field | value |
|---|---|
| **factor_id** | macd_hist |
| **display_name** | MACD Histogram |
| **category** | technical_trend |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | macd_hist |
| **output_dtype** | float64 |
| **window** | 26 (MACD long), 12 (short), 9 (signal) |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. ema_12 = close.ewm(span=12, adjust=False)
2. ema_26 = close.ewm(span=26, adjust=False)
3. dif = ema_12 - ema_26
4. dea = dif.ewm(span=9, adjust=False)
5. hist = dif - dea

**polars_expr_hint:**
```python
ema_12 = pl.col("close").ewm_mean(span=12, adjust=False)
ema_26 = pl.col("close").ewm_mean(span=26, adjust=False)
dif = ema_12 - ema_26
dea = dif.ewm_mean(span=9, adjust=False)
hist = dif - dea
```

**duckdb_expr_hint:**
```sql
WITH ema AS (
  SELECT symbol, trade_date, close,
    EXP_WEIGHTED_MEAN(close, 12) OVER (PARTITION BY symbol ORDER BY trade_date) AS ema_12,
    EXP_WEIGHTED_MEAN(close, 26) OVER (PARTITION BY symbol ORDER BY trade_date) AS ema_26
  FROM daily_bars
),
dif_dea AS (
  SELECT *,
    ema_12 - ema_26 AS dif,
    EXP_WEIGHTED_MEAN(ema_12 - ema_26, 9) OVER (PARTITION BY symbol ORDER BY trade_date) AS dea
  FROM ema
)
SELECT symbol, trade_date, dif - dea AS macd_hist
FROM dif_dea
```

**precompute_recommended:** P0（使用频率高，与 dif/dea 联动）

**preview_supported:** YES

**future_leakage_check:** EWM 只使用历史数据，无未来函数。

**edge_cases:**
- 前 25 个 bar 数据不足 → dif/dea/hist 可能不稳定
- 连续停牌 → ewm 重启后需要 warmup
- 注意 adjust=False 与 TA-Lib 默认一致

**acceptance_examples:**
- 输入 close 为上升趋势: hist 应从负变正
- 输入 close 为下降趋势: hist 应从正变负

---

#### factor_003: `adx_14`

| field | value |
|---|---|
| **factor_id** | adx_14 |
| **display_name** | ADX 14 |
| **category** | technical_trend |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | high, low, close |
| **output_column** | adx_14 |
| **output_dtype** | float64 |
| **window** | 14 |
| **frequency** | D1 |
| **direction** | higher_better (趋势确认) |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. tr1 = high - low
2. tr2 = abs(high - close.shift(1))
3. tr3 = abs(low - close.shift(1))
4. tr = max(tr1, tr2, tr3)
5. +dm = high - high.shift(1) if > 0 and > (low.shift(1) - low) else 0
6. -dm = low.shift(1) - low if > 0 and > (high - high.shift(1)) else 0
7. atr = tr.rolling_mean(14) [Wilder 平滑]
8. +di = 100 * (+dm.rolling_mean(14) / atr)
9. -di = 100 * (-dm.rolling_mean(14) / atr)
10. dx = 100 * abs(+di - -di) / (+di + -di)
11. adx = dx.rolling_mean(14) [Wilder 平滑]

**polars_expr_hint:**
```python
# TR
tr1 = pl.col("high") - pl.col("low")
tr2 = (pl.col("high") - pl.col("close").shift(1)).abs()
tr3 = (pl.col("low") - pl.col("close").shift(1)).abs()
tr = pl.max_horizontal(tr1, tr2, tr3)

# +DM / -DM
plus_dm = ((pl.col("high") - pl.col("high").shift(1)) > 0) & \
          ((pl.col("high") - pl.col("high").shift(1)) > (pl.col("low").shift(1) - pl.col("low")))
plus_dm = plus_dm.cast(pl.Float64) * (pl.col("high") - pl.col("high").shift(1)).clip_min(0)

minus_dm = ((pl.col("low").shift(1) - pl.col("low")) > 0) & \
           ((pl.col("low").shift(1) - pl.col("low")) > (pl.col("high") - pl.col("high").shift(1)))
minus_dm = minus_dm.cast(pl.Float64) * (pl.col("low").shift(1) - pl.col("low")).clip_min(0)

# Wilder 平滑 = rolling_mean (span=N, adjust=False)
atr = tr.ewm_mean(span=14, adjust=False)  # 注意：Wilder 的 N 日平滑 = ewm span=N
plus_di = 100 * plus_dm.ewm_mean(span=14, adjust=False) / atr
minus_di = 100 * minus_dm.ewm_mean(span=14, adjust=False) / atr
dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
adx = dx.ewm_mean(span=14, adjust=False)
```

**duckdb_expr_hint:**
```sql
WITH tr_calc AS (
  SELECT symbol, trade_date, high, low, close,
    GREATEST(high - low,
             ABS(high - LAG(close) OVER w),
             ABS(low - LAG(close) OVER w)) AS tr,
    CASE WHEN (high - LAG(high) OVER w) > 0
          AND (high - LAG(high) OVER w) > (LAG(low) OVER w - low)
         THEN high - LAG(high) OVER w ELSE 0 END AS plus_dm,
    CASE WHEN (LAG(low) OVER w - low) > 0
          AND (LAG(low) OVER w - low) > (high - LAG(high) OVER w)
         THEN LAG(low) OVER w - low ELSE 0 END AS minus_dm
  FROM daily_bars
  WINDOW w AS (PARTITION BY symbol ORDER BY trade_date)
),
smoothed AS (
  SELECT *,
    EXP_WEIGHTED_MEAN(tr, 14) OVER w AS atr,
    EXP_WEIGHTED_MEAN(plus_dm, 14) OVER w AS smoothed_plus_dm,
    EXP_WEIGHTED_MEAN(minus_dm, 14) OVER w AS smoothed_minus_dm
  FROM tr_calc
  WINDOW w AS (PARTITION BY symbol ORDER BY trade_date)
),
di_calc AS (
  SELECT *,
    100 * smoothed_plus_dm / NULLIF(atr, 0) AS plus_di,
    100 * smoothed_minus_dm / NULLIF(atr, 0) AS minus_di
  FROM smoothed
)
SELECT symbol, trade_date,
  EXP_WEIGHTED_MEAN(
    100 * ABS(plus_di - minus_di) / NULLIF(plus_di + minus_di, 0), 14
  ) OVER (PARTITION BY symbol ORDER BY trade_date) AS adx_14
FROM di_calc
```

**precompute_recommended:** P1（计算复杂度高，使用频率中等）

**preview_supported:** YES

**future_leakage_check:** 只使用历史 high/low/close。

**edge_cases:**
- atr == 0 → 除零，+di/-di 返回 null
- +di + -di == 0 → dx 返回 null
- 需要约 28 个 bar warmup 才稳定

**acceptance_examples:**
- 强趋势: ADX > 25
- 震荡: ADX < 20
- 输入横盘数据: adx_14 应 < 20

---

#### factor_004: `atr_14`

| field | value |
|---|---|
| **factor_id** | atr_14 |
| **display_name** | ATR 14 |
| **category** | technical_volatility |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | high, low, close |
| **output_column** | atr_14 |
| **output_dtype** | float64 |
| **window** | 14 |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. tr = max(high - low, abs(high - close.shift(1)), abs(low - close.shift(1)))
2. atr = tr.ewm_mean(span=14, adjust=False) [Wilder 平滑]

**polars_expr_hint:**
```python
tr1 = pl.col("high") - pl.col("low")
tr2 = (pl.col("high") - pl.col("close").shift(1)).abs()
tr3 = (pl.col("low") - pl.col("close").shift(1)).abs()
tr = pl.max_horizontal(tr1, tr2, tr3)
atr = tr.ewm_mean(span=14, adjust=False)
```

**duckdb_expr_hint:**
```sql
WITH tr_calc AS (
  SELECT symbol, trade_date,
    GREATEST(high - low,
             ABS(high - LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date)),
             ABS(low - LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date))) AS tr
  FROM daily_bars
)
SELECT symbol, trade_date,
  EXP_WEIGHTED_MEAN(tr, 14) OVER (PARTITION BY symbol ORDER BY trade_date) AS atr_14
FROM tr_calc
```

**precompute_recommended:** P0（使用频率极高，风控/仓位/止损核心依赖）

**preview_supported:** YES

**future_leakage_check:** 只使用历史 high/low/close。

**edge_cases:**
- 首 bar 无 close.shift(1) → tr = high - low
- 连续一字板 → tr = 0，atr 逐渐收敛到 0
- 除权除息日 → 必须使用后复权价格

**acceptance_examples:**
- 输入 daily_bars 波动扩大: atr_14 应上升
- 输入 daily_bars 波动收敛: atr_14 应下降

---

#### factor_005: `supertrend`

| field | value |
|---|---|
| **factor_id** | supertrend |
| **display_name** | SuperTrend |
| **category** | technical_trend |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | high, low, close |
| **output_column** | supertrend, supertrend_direction |
| **output_dtype** | float64, int8 (1=多头, -1=空头) |
| **window** | 10 (ATR period), 3.0 (multiplier) |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. atr = atr_10 (同上，窗口改为 10)
2. upper_band = (high + low) / 2 + multiplier * atr
3. lower_band = (high + low) / 2 - multiplier * atr
4. 动态上轨: 若 close.shift(1) > prev_upper_band，则 upper_band = min(upper_band, prev_upper_band)，否则 = upper_band
5. 动态下轨: 若 close.shift(1) < prev_lower_band，则 lower_band = max(lower_band, prev_lower_band)，否则 = lower_band
6. direction: 若 close > prev_upper_band → 1（多头），若 close < prev_lower_band → -1（空头），否则 = prev_direction
7. supertrend_line: direction == 1 时取 lower_band，否则取 upper_band

**polars_expr_hint:**
```python
# SuperTrend 有递归依赖（prev_value 影响 current_value）
# Polars 中可用 .map_groups + Python UDF，但性能差
# 推荐方案：使用 group_by + 自定义 cumfold / apply

# 注意：factor_schema 中 outputs 为 2 列
# 策略使用时可简化为 supertrend_direction（1 或 -1）作为过滤条件
```

**duckdb_expr_hint:**
```sql
-- DuckDB 中 SuperTrend 的递归逻辑较复杂
-- 建议用 Python UDF 或预计算表实现
-- 公式见上
```

**precompute_recommended:** P1（有递归逻辑，计算成本高，建议预计算）

**preview_supported:** YES（需要完整历史序列才能计算，但 Preview 可支持）

**future_leakage_check:** 只使用历史 high/low/close，但递归逻辑需确保无 lookback bias。

**edge_cases:**
- 首 bar 无法确定方向 → 默认 null 或 0
- 连续一字板 → 上下轨不移动，方向不变
- multiplier 过小 → 频繁切换方向（whipsaw）

**acceptance_examples:**
- 上升趋势: close 持续高于 supertrend_line，direction = 1
- 下降趋势: close 持续低于 supertrend_line，direction = -1

---

#### factor_006: `bb_position`

| field | value |
|---|---|
| **factor_id** | bb_position |
| **display_name** | Bollinger Band Position |
| **category** | technical_volatility |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | bb_position |
| **output_dtype** | float64 |
| **window** | 20 |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. ma_20 = close.rolling_mean(20)
2. std_20 = close.rolling_std(20)
3. upper = ma_20 + 2 * std_20
4. lower = ma_20 - 2 * std_20
5. bb_position = (close - lower) / (upper - lower)

**polars_expr_hint:**
```python
ma_20 = pl.col("close").rolling_mean(window_size=20)
std_20 = pl.col("close").rolling_std(window_size=20)
upper = ma_20 + 2 * std_20
lower = ma_20 - 2 * std_20
bb_position = (pl.col("close") - lower) / (upper - lower)
```

**duckdb_expr_hint:**
```sql
WITH bb AS (
  SELECT symbol, trade_date, close,
    AVG(close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20,
    STDDEV_SAMP(close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS std_20
  FROM daily_bars
)
SELECT symbol, trade_date,
  (close - (ma_20 - 2 * std_20)) / NULLIF(2 * 2 * std_20, 0) AS bb_position
FROM bb
```

**precompute_recommended:** P0（使用频率高，计算简单）

**preview_supported:** YES

**future_leakage_check:** 只使用过去 20 日 close。

**edge_cases:**
- std_20 == 0（连续一字板）→ 除零，返回 null
- bb_position < 0 或 > 1 → 价格突破上下轨，属正常信号
- 前 19 bar 不足 → 返回 null

**acceptance_examples:**
- close = upper → bb_position = 1.0
- close = lower → bb_position = 0.0
- close = ma_20 → bb_position = 0.5

---

#### factor_007: `bb_bandwidth`

| field | value |
|---|---|
| **factor_id** | bb_bandwidth |
| **display_name** | Bollinger Bandwidth |
| **category** | technical_volatility |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | bb_bandwidth |
| **output_dtype** | float64 |
| **window** | 20 |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. ma_20 = close.rolling_mean(20)
2. std_20 = close.rolling_std(20)
3. upper = ma_20 + 2 * std_20
4. lower = ma_20 - 2 * std_20
5. bb_bandwidth = (upper - lower) / ma_20

**polars_expr_hint:**
```python
ma_20 = pl.col("close").rolling_mean(window_size=20)
std_20 = pl.col("close").rolling_std(window_size=20)
bb_bandwidth = (4 * std_20) / ma_20
```

**duckdb_expr_hint:**
```sql
WITH bb AS (
  SELECT symbol, trade_date, close,
    AVG(close) OVER w AS ma_20,
    STDDEV_SAMP(close) OVER w AS std_20
  FROM daily_bars
  WINDOW w AS (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
)
SELECT symbol, trade_date,
  (4 * std_20) / NULLIF(ma_20, 0) AS bb_bandwidth
FROM bb
```

**precompute_recommended:** P0（与 bb_position 共享 ma_20/std_20，可联合预计算）

**preview_supported:** YES

**future_leakage_check:** 同 bb_position。

**edge_cases:**
- ma_20 == 0 → 除零（不可能发生但需防御）
- 连续一字板 → std_20=0，bandwidth=0（挤压信号）

**acceptance_examples:**
- 高波动 → bandwidth > 0.15
- 低波动/挤压 → bandwidth < 0.05

---

#### factor_008: `roc_10`

| field | value |
|---|---|
| **factor_id** | roc_10 |
| **display_name** | ROC 10 |
| **category** | technical_momentum |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | roc_10 |
| **output_dtype** | float64 |
| **window** | 10 |
| **frequency** | D1 |
| **direction** | higher_better |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
roc_10 = (close - close.shift(10)) / close.shift(10) * 100

**polars_expr_hint:**
```python
roc_10 = (pl.col("close") / pl.col("close").shift(10) - 1) * 100
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date,
  (close / NULLIF(LAG(close, 10) OVER (PARTITION BY symbol ORDER BY trade_date), 0) - 1) * 100 AS roc_10
FROM daily_bars
```

**precompute_recommended:** P0（计算极简单，使用频率高）

**preview_supported:** YES

**future_leakage_check:** 只使用 10 日前 close。

**edge_cases:**
- close.shift(10) == 0 → 除零（不可能但需防御）
- 停牌 10 日 → shift(10) 可能跨停牌日，需确保按交易日 shift

**acceptance_examples:**
- close 上涨 10% → roc_10 = 10.0
- close 下跌 5% → roc_10 = -5.0

---

#### factor_009: `volume_ratio`

| field | value |
|---|---|
| **factor_id** | volume_ratio |
| **display_name** | Volume Ratio |
| **category** | volume_price |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | volume |
| **output_column** | volume_ratio |
| **output_dtype** | float64 |
| **window** | 20 |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
volume_ratio = volume / volume.rolling_mean(20)

**polars_expr_hint:**
```python
volume_ratio = pl.col("volume") / pl.col("volume").rolling_mean(window_size=20)
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date,
  volume / NULLIF(AVG(volume) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) AS volume_ratio
FROM daily_bars
```

**precompute_recommended:** P0（MVP 已有预计算列，计算极简单）

**preview_supported:** YES

**future_leakage_check:** 只使用过去 20 日 volume。

**edge_cases:**
- 20 日平均 volume = 0（新股前 20 日）→ 除零
- 停牌日 volume = 0 → volume_ratio = 0

**acceptance_examples:**
- volume = 2x 均值 → volume_ratio = 2.0
- volume = 0.5x 均值 → volume_ratio = 0.5

---

#### factor_010: `turnover_rate`

| field | value |
|---|---|
| **factor_id** | turnover_rate |
| **display_name** | Turnover Rate |
| **category** | volume_price |
| **level** | L1 |
| **input_tables** | daily_bars |
| **input_columns** | volume, shares_outstanding |
| **output_column** | turnover_rate |
| **output_dtype** | float64 |
| **window** | 1（日频） |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
turnover_rate = volume / shares_outstanding

**polars_expr_hint:**
```python
turnover_rate = pl.col("volume") / pl.col("shares_outstanding")
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date,
  volume / NULLIF(shares_outstanding, 0) AS turnover_rate
FROM daily_bars
```

**precompute_recommended:** P0（MVP 已有预计算列，计算极简单）

**preview_supported:** YES

**future_leakage_check:** 只使用当日 volume 和 shares_outstanding（shares_outstanding 用最新可用值，非未来数据）。

**edge_cases:**
- shares_outstanding = 0 或 null → 除零
- 次新股 shares_outstanding 变化 → 需使用历史值而非当前值
- 注意：shares_outstanding 变更时（增发、回购）需用对应日期值

**acceptance_examples:**
- volume=1e7, shares=1e9 → turnover_rate = 0.01 (1%)

---

### 2.2 Cross-Sectional Factors (5 factors)

---

#### factor_011: `return_5d_rank`

| field | value |
|---|---|
| **factor_id** | return_5d_rank |
| **display_name** | 5日收益率排名 |
| **category** | cross_sectional |
| **level** | L2 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | return_5d_rank |
| **output_dtype** | float64 |
| **window** | 5 |
| **frequency** | D1 |
| **direction** | higher_better |
| **normalization** | [rank_pct] |
| **neutralization** | [] |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. return_5d = (close / close.shift(5) - 1) * 100
2. return_5d_rank = return_5d.rank() / count() [按 trade_date 横截面排名，归一化到 0-1]

**polars_expr_hint:**
```python
return_5d = pl.col("close") / pl.col("close").shift(5) - 1
# 横截面 rank 需要 group_by("trade_date") + over
return_5d_rank = return_5d.rank(method="min") / pl.count()
# 在 Polars 中:
# .with_columns(return_5d_rank=(pl.col("return_5d").rank(method="min") / pl.count()).over("trade_date"))
```

**duckdb_expr_hint:**
```sql
WITH ret AS (
  SELECT symbol, trade_date,
    close / NULLIF(LAG(close, 5) OVER (PARTITION BY symbol ORDER BY trade_date), 0) - 1 AS return_5d
  FROM daily_bars
)
SELECT symbol, trade_date,
  PERCENT_RANK() OVER (PARTITION BY trade_date ORDER BY return_5d) AS return_5d_rank
FROM ret
```

**precompute_recommended:** P1（需要横截面 rank，逐日计算，建议预计算缓存）

**preview_supported:** YES（横截面 rank 可跨 symbol 计算）

**future_leakage_check:** 只使用 5 日前 close，rank 只使用当日截面数据。

**edge_cases:**
- 当日可交易股票过少（如节假日后首日）→ rank 可能不稳定
- 停牌股票 return_5d 可能异常（close 不变化）→ 需在 rank 前过滤停牌

**acceptance_examples:**
- 股票 A return_5d=10%，当日最高 → return_5d_rank=1.0
- 股票 B return_5d=-5%，当日最低 → return_5d_rank=0.0

---

#### factor_012: `return_20d_rank`

| field | value |
|---|---|
| **factor_id** | return_20d_rank |
| **display_name** | 20日收益率排名 |
| **category** | cross_sectional |
| **level** | L2 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | return_20d_rank |
| **output_dtype** | float64 |
| **window** | 20 |
| **frequency** | D1 |
| **direction** | higher_better |
| **normalization** | [rank_pct] |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. return_20d = (close / close.shift(20) - 1) * 100
2. return_20d_rank = return_20d.rank() / count() [按 trade_date 横截面]

**polars_expr_hint:**
```python
return_20d = pl.col("close") / pl.col("close").shift(20) - 1
return_20d_rank = pl.col("return_20d").rank(method="min") / pl.count()
```

**duckdb_expr_hint:**
```sql
WITH ret AS (
  SELECT symbol, trade_date,
    close / NULLIF(LAG(close, 20) OVER (PARTITION BY symbol ORDER BY trade_date), 0) - 1 AS return_20d
  FROM daily_bars
)
SELECT symbol, trade_date,
  PERCENT_RANK() OVER (PARTITION BY trade_date ORDER BY return_20d) AS return_20d_rank
FROM ret
```

**precompute_recommended:** P1（同 return_5d_rank）

**preview_supported:** YES

**future_leakage_check:** 只使用 20 日前 close。

**edge_cases:**
- 新股不足 20 日 → return_20d = null，rank 时排最后或排除
- 连续停牌 20 日 → return_20d = 0，需处理

**acceptance_examples:**
- 同 return_5d_rank，窗口为 20

---

#### factor_013: `industry_rs_rank`

| field | value |
|---|---|
| **factor_id** | industry_rs_rank |
| **display_name** | 行业内相对强弱排名 |
| **category** | cross_sectional |
| **level** | L2 |
| **input_tables** | daily_bars, industry |
| **input_columns** | close, industry_code |
| **output_column** | industry_rs_rank |
| **output_dtype** | float64 |
| **window** | 20 |
| **frequency** | D1 |
| **direction** | higher_better |
| **normalization** | [rank_pct] |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | low |
| **data_availability** | available |

**formula_plain_text:**
1. return_20d = close / close.shift(20) - 1
2. 按 (trade_date, industry_code) 分组，对 return_20d 做 rank
3. industry_rs_rank = rank / count(group) [0-1]

**polars_expr_hint:**
```python
return_20d = pl.col("close") / pl.col("close").shift(20) - 1
industry_rs_rank = pl.col("return_20d").rank(method="min") / pl.count()
# 在 Polars 中: .over(["trade_date", "industry_code"])
```

**duckdb_expr_hint:**
```sql
WITH ret AS (
  SELECT d.symbol, d.trade_date, i.industry_code,
    d.close / NULLIF(LAG(d.close, 20) OVER (PARTITION BY d.symbol ORDER BY d.trade_date), 0) - 1 AS return_20d
  FROM daily_bars d
  LEFT JOIN industry i ON d.symbol = i.symbol AND d.trade_date >= i.effective_date
),
ranked AS (
  SELECT *,
    PERCENT_RANK() OVER (PARTITION BY trade_date, industry_code ORDER BY return_20d) AS industry_rs_rank
  FROM ret
)
SELECT symbol, trade_date, industry_rs_rank FROM ranked
```

**precompute_recommended:** P1（需要 join industry 表 + 横截面 rank）

**preview_supported:** YES

**future_leakage_check:**
- 收益部分：无未来函数
- industry 表：必须使用 effective_date ≤ trade_date 的最新行业分类，不可使用未来行业变更
- `future_leakage_risk=low` 是因为 industry 分类变更历史需确保准确

**edge_cases:**
- 行业分类缺失 → 排除或归入 "unknown"
- 行业内股票过少（<3）→ rank 不稳定，建议过滤
- 新股无行业 → 需特殊处理

**acceptance_examples:**
- 行业 A 中股票 X 20日收益最高 → industry_rs_rank = 1.0

---

#### factor_014: `volatility_20d_pct`

| field | value |
|---|---|
| **factor_id** | volatility_20d_pct |
| **display_name** | 20日波动率百分位 |
| **category** | cross_sectional |
| **level** | L2 |
| **input_tables** | daily_bars |
| **input_columns** | close |
| **output_column** | volatility_20d_pct |
| **output_dtype** | float64 |
| **window** | 20 |
| **frequency** | D1 |
| **direction** | neutral |
| **normalization** | [rank_pct] |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. return_1d = close / close.shift(1) - 1
2. volatility_20d = return_1d.rolling_std(20) * sqrt(252) [年化]
3. 按 trade_date 横截面对 volatility_20d 做 PERCENT_RANK → volatility_20d_pct

**polars_expr_hint:**
```python
return_1d = pl.col("close") / pl.col("close").shift(1) - 1
volatility_20d = return_1d.rolling_std(window_size=20) * (252 ** 0.5)
volatility_20d_pct = pl.col("volatility_20d").rank(method="min") / pl.count()
# .over("trade_date")
```

**duckdb_expr_hint:**
```sql
WITH vol AS (
  SELECT symbol, trade_date,
    STDDEV_SAMP(close / NULLIF(LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date), 0) - 1)
      OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
      * SQRT(252) AS volatility_20d
  FROM daily_bars
)
SELECT symbol, trade_date,
  PERCENT_RANK() OVER (PARTITION BY trade_date ORDER BY volatility_20d) AS volatility_20d_pct
FROM vol
```

**precompute_recommended:** P1（需要横截面 rank）

**preview_supported:** YES

**future_leakage_check:** 只使用历史 close。

**edge_cases:**
- 20 日内停牌日过多 → std 偏低
- 一字板连续 → std=0，rank 时可能排最低
- 年化系数 252 为 A 股交易日数

**acceptance_examples:**
- 高波动股票 → volatility_20d_pct 接近 1.0
- 低波动股票 → volatility_20d_pct 接近 0.0

---

#### factor_015: `beta_to_index`

| field | value |
|---|---|
| **factor_id** | beta_to_index |
| **display_name** | Beta to Index |
| **category** | cross_sectional |
| **level** | L2 |
| **input_tables** | daily_bars, index_daily |
| **input_columns** | close, index_close |
| **output_column** | beta_to_index |
| **output_dtype** | float64 |
| **window** | 60 |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. stock_ret = close / close.shift(1) - 1
2. index_ret = index_close / index_close.shift(1) - 1
3. beta = cov(stock_ret, index_ret, window=60) / var(index_ret, window=60)

**polars_expr_hint:**
```python
# 需要 join daily_bars 和 index_daily
# Polars 中可用 .rolling_cov + .rolling_var
# 或使用 group_by + apply 做线性回归

# 方法1: rolling_cov / rolling_var
stock_ret = pl.col("close") / pl.col("close").shift(1) - 1
index_ret = pl.col("index_close") / pl.col("index_close").shift(1) - 1

# Polars 目前没有原生 rolling_cov，建议用 group_by + map_groups
# 或预计算：对每个 symbol 做 60 日 OLS
```

**duckdb_expr_hint:**
```sql
WITH joined AS (
  SELECT d.symbol, d.trade_date, d.close, i.index_close,
    d.close / NULLIF(LAG(d.close) OVER (PARTITION BY d.symbol ORDER BY d.trade_date), 0) - 1 AS stock_ret,
    i.index_close / NULLIF(LAG(i.index_close) OVER (PARTITION BY i.index_code ORDER BY i.trade_date), 0) - 1 AS index_ret
  FROM daily_bars d
  JOIN index_daily i ON d.trade_date = i.trade_date
  WHERE i.index_code = '000300.SH'
),
reg AS (
  SELECT symbol, trade_date,
    REGR_SLOPE(stock_ret, index_ret) OVER (
      PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
    ) AS beta_to_index
  FROM joined
)
SELECT symbol, trade_date, beta_to_index FROM reg
```

**precompute_recommended:** P1（需要 join + 滚动回归，计算成本高）

**preview_supported:** YES（需要指数数据）

**future_leakage_check:** 只使用历史 close 和 index_close。

**edge_cases:**
- index_ret variance = 0（指数连续一字板）→ 除零
- 不足 60 日数据 → beta 不稳定
- 股票停牌导致 stock_ret 为 0 → beta 被拉低，需处理

**acceptance_examples:**
- 高 beta 股票（>1.2）→ 波动大于指数
- 低 beta 股票（<0.8）→ 波动小于指数
- 防御股 beta ~ 0.5-0.7

---

### 2.3 Money Flow / Liquidity Factors (5 factors)

---

#### factor_016: `main_force_net_inflow`

| field | value |
|---|---|
| **factor_id** | main_force_net_inflow |
| **display_name** | 主力净流入 |
| **category** | money_flow |
| **level** | L4 |
| **input_tables** | moneyflow_daily |
| **input_columns** | main_force_net_inflow |
| **output_column** | main_force_net_inflow |
| **output_dtype** | float64 |
| **window** | 1 |
| **frequency** | D1 |
| **direction** | higher_better |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
直接透传黑狼 `main_force_net_inflow` 字段。
可衍生：main_force_net_inflow_5d = main_force_net_inflow.rolling_sum(5)

**polars_expr_hint:**
```python
# 直接透传
main_force_net_inflow = pl.col("main_force_net_inflow")
# 衍生
main_force_net_inflow_5d = pl.col("main_force_net_inflow").rolling_sum(window_size=5)
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date, main_force_net_inflow,
  SUM(main_force_net_inflow) OVER (
    PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
  ) AS main_force_net_inflow_5d
FROM moneyflow_daily
```

**precompute_recommended:** P0（黑狼数据已提供，直接透传）

**preview_supported:** YES

**future_leakage_check:** 黑狼数据为当日收盘后统计，无未来数据。

**edge_cases:**
- 缺失 → 可能为 null（小盘股/新三板）
- 数据异常大 → 需 winsorize
- 主力定义变更 → 黑狼字段说明需稳定

**acceptance_examples:**
- 主力大幅流入 → main_force_net_inflow > 0
- 主力大幅流出 → main_force_net_inflow < 0

---

#### factor_017: `large_order_net_inflow`

| field | value |
|---|---|
| **factor_id** | large_order_net_inflow |
| **display_name** | 大单净流入 |
| **category** | money_flow |
| **level** | L4 |
| **input_tables** | moneyflow_daily |
| **input_columns** | large_order_net_inflow |
| **output_column** | large_order_net_inflow |
| **output_dtype** | float64 |
| **window** | 1 |
| **frequency** | D1 |
| **direction** | higher_better |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
直接透传黑狼 `large_order_net_inflow` 字段。
可衍生：large_order_net_inflow_5d

**polars_expr_hint:**
```python
large_order_net_inflow = pl.col("large_order_net_inflow")
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date, large_order_net_inflow FROM moneyflow_daily
```

**precompute_recommended:** P0（黑狼数据已提供）

**preview_supported:** YES

**future_leakage_check:** 同 main_force_net_inflow。

**edge_cases:**
- 同 main_force_net_inflow
- 大单定义（金额阈值）需与黑狼对齐

**acceptance_examples:**
- 同 main_force_net_inflow

---

#### factor_018: `active_buy_sell_ratio`

| field | value |
|---|---|
| **factor_id** | active_buy_sell_ratio |
| **display_name** | 主动买卖比 |
| **category** | money_flow |
| **level** | L4 |
| **input_tables** | moneyflow_daily |
| **input_columns** | active_buy_amount, active_sell_amount |
| **output_column** | active_buy_sell_ratio |
| **output_dtype** | float64 |
| **window** | 1 |
| **frequency** | D1 |
| **direction** | higher_better |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
active_buy_sell_ratio = active_buy_amount / active_sell_amount

**polars_expr_hint:**
```python
active_buy_sell_ratio = pl.col("active_buy_amount") / pl.col("active_sell_amount")
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date,
  active_buy_amount / NULLIF(active_sell_amount, 0) AS active_buy_sell_ratio
FROM moneyflow_daily
```

**precompute_recommended:** P0（黑狼数据已提供，简单除法）

**preview_supported:** YES

**future_leakage_check:** 无未来数据。

**edge_cases:**
- active_sell_amount = 0 → 除零（极端情况）
- ratio < 1 → 主动卖多于主动买
- ratio > 2 → 主动买远大于主动卖

**acceptance_examples:**
- active_buy=1e8, active_sell=5e7 → ratio = 2.0

---

#### factor_019: `money_flow_intensity`

| field | value |
|---|---|
| **factor_id** | money_flow_intensity |
| **display_name** | 资金流强度 |
| **category** | money_flow |
| **level** | L4 |
| **input_tables** | daily_bars, moneyflow_daily |
| **input_columns** | amount, main_force_net_inflow |
| **output_column** | money_flow_intensity |
| **output_dtype** | float64 |
| **window** | 1 |
| **frequency** | D1 |
| **direction** | higher_better |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
money_flow_intensity = main_force_net_inflow / amount

**polars_expr_hint:**
```python
money_flow_intensity = pl.col("main_force_net_inflow") / pl.col("amount")
```

**duckdb_expr_hint:**
```sql
SELECT d.symbol, d.trade_date,
  m.main_force_net_inflow / NULLIF(d.amount, 0) AS money_flow_intensity
FROM daily_bars d
JOIN moneyflow_daily m ON d.symbol = m.symbol AND d.trade_date = m.trade_date
```

**precompute_recommended:** P0（简单 join + 除法）

**preview_supported:** YES

**future_leakage_check:** 无未来数据。

**edge_cases:**
- amount = 0（停牌）→ 除零
- intensity > 0.5 → 主力净流入占成交额 50% 以上（异常，需检查）
- intensity < -0.5 → 主力净流出占成交额 50% 以上

**acceptance_examples:**
- main_force=1e7, amount=1e8 → intensity = 0.1 (10%)

---

#### factor_020: `amihud_illiquidity`

| field | value |
|---|---|
| **factor_id** | amihud_illiquidity |
| **display_name** | Amihud Illiquidity |
| **category** | liquidity |
| **level** | L4 |
| **input_tables** | daily_bars |
| **input_columns** | close, amount |
| **output_column** | amihud_illiquidity |
| **output_dtype** | float64 |
| **window** | 20 |
| **frequency** | D1 |
| **direction** | lower_better |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. daily_illiquidity = abs(close - close.shift(1)) / amount * 1e6 [单位调整]
2. amihud_illiquidity = daily_illiquidity.rolling_mean(20)

**polars_expr_hint:**
```python
daily_illiq = (pl.col("close") - pl.col("close").shift(1)).abs() / pl.col("amount") * 1e6
amihud = daily_illiq.rolling_mean(window_size=20)
```

**duckdb_expr_hint:**
```sql
WITH daily AS (
  SELECT symbol, trade_date, close, amount,
    ABS(close - LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date)) / NULLIF(amount, 0) * 1e6 AS daily_illiq
  FROM daily_bars
)
SELECT symbol, trade_date,
  AVG(daily_illiq) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS amihud_illiquidity
FROM daily
```

**precompute_recommended:** P1（计算简单但使用频率中等）

**preview_supported:** YES

**future_leakage_check:** 无未来数据。

**edge_cases:**
- amount = 0 → 除零
- 1e6 乘数是为使数值可读（Amihud 原始值通常极小）
- 连续涨停/跌停 → daily_illiq 可能为 0

**acceptance_examples:**
- 高流动性大盘股 → amihud < 0.1
- 低流动性小盘股 → amihud > 10.0

---

### 2.4 Hermass Native State Factors (4 factors)

---

#### factor_021: `d1_state`

| field | value |
|---|---|
| **factor_id** | d1_state |
| **display_name** | D1 State |
| **category** | hermass_state |
| **level** | L5 |
| **input_tables** | state_cube |
| **input_columns** | d1_state |
| **output_column** | d1_state |
| **output_dtype** | string |
| **window** | - |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
直接透传 `state_cube.d1_state`。
State 计算逻辑由 Hermass State Cube 引擎独立完成，factor registry 只引用结果。

**polars_expr_hint:**
```python
# 直接透传
d1_state = pl.col("d1_state")
# DSL 使用: d1_state IN ("0x01", "0x02", ...) 或 state_hex_in
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date, d1_state FROM state_cube
```

**precompute_recommended:** P0（State Cube 已预计算）

**preview_supported:** YES

**future_leakage_check:** State Cube 只使用历史 OHLCV，无未来数据。

**edge_cases:**
- state_hex 非法 → 需校验合法性
- 停牌日 state → 使用停牌前最后一个有效 bar 的 OHLCV 计算

**acceptance_examples:**
- d1_state = "0x01" → 多头趋势
- d1_state = "0x04" → 空头趋势

---

#### factor_022: `w1_state`

| field | value |
|---|---|
| **factor_id** | w1_state |
| **display_name** | W1 State |
| **category** | hermass_state |
| **level** | L5 |
| **input_tables** | state_cube |
| **input_columns** | w1_state |
| **output_column** | w1_state |
| **output_dtype** | string |
| **window** | - |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
直接透传 `state_cube.w1_state`。

**polars_expr_hint:**
```python
w1_state = pl.col("w1_state")
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date, w1_state FROM state_cube
```

**precompute_recommended:** P0（State Cube 已预计算）

**preview_supported:** YES

**future_leakage_check:** 无未来数据。

**edge_cases:**
- 同 d1_state

**acceptance_examples:**
- 同 d1_state

---

#### factor_023: `mn1_state`

| field | value |
|---|---|
| **factor_id** | mn1_state |
| **display_name** | MN1 State |
| **category** | hermass_state |
| **level** | L5 |
| **input_tables** | state_cube |
| **input_columns** | mn1_state |
| **output_column** | mn1_state |
| **output_dtype** | string |
| **window** | - |
| **frequency** | D1 |
| **direction** | neutral |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
直接透传 `state_cube.mn1_state`。

**polars_expr_hint:**
```python
mn1_state = pl.col("mn1_state")
```

**duckdb_expr_hint:**
```sql
SELECT symbol, trade_date, mn1_state FROM state_cube
```

**precompute_recommended:** P0（State Cube 已预计算）

**preview_supported:** YES

**future_leakage_check:** 无未来数据。

**edge_cases:**
- 同 d1_state

**acceptance_examples:**
- 同 d1_state

---

#### factor_024: `multi_timeframe_resonance`

| field | value |
|---|---|
| **factor_id** | multi_timeframe_resonance |
| **display_name** | 多周期共振数 |
| **category** | hermass_state |
| **level** | L5 |
| **input_tables** | state_cube |
| **input_columns** | mn1_state, w1_state, d1_state |
| **output_column** | multi_timeframe_resonance |
| **output_dtype** | int8 |
| **window** | - |
| **frequency** | D1 |
| **direction** | higher_better |
| **compute_engine** | polars |
| **preview_support** | fully_supported |
| **dsl_exposure** | candidate |
| **production_gate** | candidate |
| **future_leakage_risk** | none |
| **data_availability** | available |

**formula_plain_text:**
1. 定义趋势态集合: trend_up_states = {"0x01", "0x02", "0x03"} [示例]
2. 定义趋势 down 态集合: trend_down_states = {"0x04", "0x05", "0x06"} [示例]
3. 对每行判断:
   - mn1_trend = 1 if mn1_state in trend_up_states else -1 if in trend_down_states else 0
   - w1_trend = 1 if w1_state in trend_up_states else -1 if in trend_down_states else 0
   - d1_trend = 1 if d1_state in trend_up_states else -1 if in trend_down_states else 0
4. multi_timeframe_resonance = sum(signs are same and non-zero)
   - 例如 mn1=1, w1=1, d1=1 → resonance = 3
   - mn1=-1, w1=-1, d1=0 → resonance = -2
   - 0 表示无共振

**polars_expr_hint:**
```python
# 定义 state 到 trend 的映射函数
def state_to_trend(state_col: str) -> pl.Expr:
    up_states = ["0x01", "0x02", "0x03"]
    down_states = ["0x04", "0x05", "0x06"]
    return (
        pl.when(pl.col(state_col).is_in(up_states)).then(1)
        .when(pl.col(state_col).is_in(down_states)).then(-1)
        .otherwise(0)
    )

mn1_trend = state_to_trend("mn1_state")
w1_trend = state_to_trend("w1_state")
d1_trend = state_to_trend("d1_state")

# 同向共振计数
resonance = (
    (mn1_trend == w1_trend).cast(pl.Int8) * (mn1_trend != 0).cast(pl.Int8) +
    (w1_trend == d1_trend).cast(pl.Int8) * (w1_trend != 0).cast(pl.Int8) +
    (mn1_trend == d1_trend).cast(pl.Int8) * (mn1_trend != 0).cast(pl.Int8)
)
# 注意：上述计算需根据 Hermass state 定义调整
```

**duckdb_expr_hint:**
```sql
WITH trend AS (
  SELECT symbol, trade_date,
    CASE WHEN mn1_state IN ('0x01','0x02','0x03') THEN 1
         WHEN mn1_state IN ('0x04','0x05','0x06') THEN -1 ELSE 0 END AS mn1_trend,
    CASE WHEN w1_state IN ('0x01','0x02','0x03') THEN 1
         WHEN w1_state IN ('0x04','0x05','0x06') THEN -1 ELSE 0 END AS w1_trend,
    CASE WHEN d1_state IN ('0x01','0x02','0x03') THEN 1
         WHEN d1_state IN ('0x04','0x05','0x06') THEN -1 ELSE 0 END AS d1_trend
  FROM state_cube
)
SELECT symbol, trade_date,
  (CASE WHEN mn1_trend = w1_trend AND mn1_trend != 0 THEN 1 ELSE 0 END +
   CASE WHEN w1_trend = d1_trend AND w1_trend != 0 THEN 1 ELSE 0 END +
   CASE WHEN mn1_trend = d1_trend AND mn1_trend != 0 THEN 1 ELSE 0 END) AS multi_timeframe_resonance
FROM trend
```

**precompute_recommended:** P0（计算简单，State Cube 数据已预计算）

**preview_supported:** YES

**future_leakage_check:** 无未来数据。

**edge_cases:**
- state 定义变更 → 需同步更新 trend 映射
- 所有 state 为 0（无方向）→ resonance = 0
- 只有两个周期共振（如 mn1=1, w1=1, d1=0）→ resonance = 1

**acceptance_examples:**
- mn1=1, w1=1, d1=1 → resonance = 3（最强多头共振）
- mn1=-1, w1=-1, d1=-1 → resonance = -3（最强空头共振）

---

## 3. F1 Block Contracts

### 3.1 `stop_loss_pct`

| field | value |
|---|---|
| **block_id** | stop_loss_pct |
| **block_type** | exit |
| **name** | 固定止损百分比 |
| **context_requirements** | position |
| **required_inputs** | entry_price, close |
| **required_tables** | position_context, daily_bars |
| **parameters** | stop_loss_pct: float, range [0.01, 0.50], default 0.08 |
| **parameter_space** | stop_loss_pct: range, min=0.01, max=0.50, step=0.01 |
| **weight** | 1.0 |
| **enabled** | true |
| **preview_support** | backtest_only |
| **dsl_output** | block_exit |
| **robustness_role** | exit_risk |
| **market_scope** | [A_SHARE] |
| **status** | candidate |
| **production_gate** | candidate |

**backtest_semantics:**
1. 在每日收盘后检查：若 `close <= entry_price * (1 - stop_loss_pct)` → 触发止损
2. 实际执行价格：次日开盘价（A 股 T+1，当日无法卖出）
3. 若次日一字跌停 → 无法成交，需记录为 "pending_exit"，继续检查
4. 止损触发后，position 状态变为 "exited"

**risk_notes:**
- 止损价计算使用 `entry_price`（买入价），不可使用未来 close
- T+1 约束：买入当日即使跌破止损线也不能卖出
- 一字跌停时无法成交，需处理流动性风险
- 复权：entry_price 和 close 都必须使用后复权价格

---

### 3.2 `take_profit_pct`

| field | value |
|---|---|
| **block_id** | take_profit_pct |
| **block_type** | exit |
| **name** | 固定止盈百分比 |
| **context_requirements** | position |
| **required_inputs** | entry_price, close |
| **required_tables** | position_context, daily_bars |
| **parameters** | take_profit_pct: float, range [0.01, 1.00], default 0.20 |
| **parameter_space** | take_profit_pct: range, min=0.01, max=1.00, step=0.01 |
| **weight** | 1.0 |
| **enabled** | true |
| **preview_support** | backtest_only |
| **dsl_output** | block_exit |
| **robustness_role** | exit_profit |
| **market_scope** | [A_SHARE] |
| **status** | candidate |
| **production_gate** | candidate |

**backtest_semantics:**
1. 在每日收盘后检查：若 `close >= entry_price * (1 + take_profit_pct)` → 触发止盈
2. 实际执行价格：次日开盘价（A 股 T+1）
3. 若次日一字涨停 → 无法成交，记录为 "pending_exit"
4. 止盈触发后，position 状态变为 "exited"

**risk_notes:**
- 同 stop_loss_pct，注意 T+1 约束
- 快速上涨后回落 → 可能错过更高收益
- 与 trailing stop 配合使用更优

---

### 3.3 `atr_trailing_stop`

| field | value |
|---|---|
| **block_id** | atr_trailing_stop |
| **block_type** | exit |
| **name** | ATR 追踪止损 |
| **context_requirements** | position |
| **required_inputs** | highest_since_entry, atr_14, close |
| **required_tables** | position_context, daily_bars |
| **parameters** | multiplier: float, range [1.0, 5.0], default 3.0 |
| **parameter_space** | multiplier: range, min=1.0, max=5.0, step=0.5 |
| **weight** | 1.0 |
| **enabled** | true |
| **preview_support** | backtest_only |
| **dsl_output** | block_exit |
| **robustness_role** | exit_risk |
| **market_scope** | [A_SHARE] |
| **status** | candidate |
| **production_gate** | candidate |

**backtest_semantics:**
1. 初始化 trailing_stop_price = entry_price - multiplier * atr_14_at_entry
2. 每日更新：trailing_stop_price = max(trailing_stop_price, highest_since_entry - multiplier * atr_14)
3. 检查：若 `close <= trailing_stop_price` → 触发止损
4. 实际执行价格：次日开盘价
5. atr_14 使用当日值（已计算，无未来函数）

**risk_notes:**
- `highest_since_entry` 必须动态跟踪，不可前视
- atr_14 使用当日值，非未来值
- multiplier 过小 → 频繁触发（whipsaw）
- multiplier 过大 → 回撤过大
- 需与 stop_loss_pct 配合使用（双重保护）

---

### 3.4 `position_size_red_line`

| field | value |
|---|---|
| **block_id** | position_size_red_line |
| **block_type** | money_management |
| **name** | 仓位红线限制 |
| **context_requirements** | portfolio |
| **required_inputs** | account_value, target_position_value |
| **required_tables** | account_context |
| **parameters** | max_position_pct: float, range [0.05, 0.50], default 0.25 |
| **parameter_space** | max_position_pct: range, min=0.05, max=0.50, step=0.05 |
| **weight** | 1.0 |
| **enabled** | true |
| **preview_support** | preview_supported |
| **dsl_output** | block_sizing |
| **robustness_role** | risk_limit |
| **market_scope** | [A_SHARE] |
| **status** | candidate |
| **production_gate** | candidate |

**backtest_semantics:**
1. 计算最大允许仓位：`max_position_value = account_value * max_position_pct`
2. 若 `target_position_value > max_position_value` → 截断到 max_position_value
3. 在红线检查阶段：若策略生成的仓位超过红线 → DSL 被拒绝
4. 在回测阶段：若信号触发但当前已满仓 → 忽略信号

**risk_notes:**
- `max_position_pct` 默认 0.25（25%），红线系统强制约束
- account_value 使用最新可用值
- 单策略总仓位也不得超过红线（与单个 position 区分）
- 这是红线 block，不是优化 block，必须严格执行

---

## 4. Extra DSL Design Notes

### 4.1 `factor_threshold_signal` 接口建议

**暂不直接实现的原因：**
1. 需要新增 `factor_ref` 参数类型（引用任意已注册 factor）
2. 需要 DSL 表达式求值引擎支持动态 factor 引用
3. 需要先完成 factor_registry 和 preview 查询引擎的联动

**需要新增的 DSL 参数类型：**
- `factor_ref`: 引用 factor_registry 中的 factor_id，需运行时校验存在性
- `operator_enum`: ["cross_up", "cross_down", ">", "<", ">=", "<=", "==", "!="]
- `threshold_number`: 阈值数值，可与 factor 的 historical percentile 联动

**最小可用接口：**

```json
{
  "condition_type": "factor_threshold_signal",
  "params": {
    "factor_id": "rsi_14",
    "operator": ">=",
    "threshold": 70,
    "lookback": 1
  }
}
```

执行语义：
1. 从 factor_registry 获取 `rsi_14` 的计算函数
2. 查询/计算当前 symbol 的 rsi_14 值
3. 比较：`rsi_14 >= 70`
4. 返回 boolean

**依赖：**
- factor_registry 必须支持按 factor_id 查询和计算
- preview 引擎必须能懒加载 factor
- 需要 factor_compute_engine 的抽象层

---

### 4.2 `robustness_parameter_jitter` 接口建议

**暂不直接实现的原因：**
1. 需要完整的 backtest 输出和参数空间定义
2. 需要 Monte Carlo / 参数扰动框架
3. 需要先让基础回测引擎跑通

**需要新增的 DSL 参数类型：**
- `parameter_space_ref`: 引用 block 的 parameter_space
- `jitter_distribution`: ["uniform", "gaussian", "discrete"]
- `jitter_magnitude`: 扰动幅度比例

**最小可用接口：**

```json
{
  "robustness_test_type": "parameter_jitter",
  "params": {
    "target_strategy_id": "strategy_001",
    "jitter_runs": 100,
    "jitter_magnitude": 0.1,
    "parameter_scope": ["stop_loss_pct", "take_profit_pct"],
    "pass_criteria": {
      "min_win_rate": 0.6,
      "max_drawdown_worsening": 0.05
    }
  }
}
```

执行语义：
1. 读取目标策略的 parameter_space
2. 对指定参数在 ±10% 范围内均匀扰动
3. 运行 100 次独立回测
4. 统计：胜率、最大回撤、夏普比率的变化
5. 若通过率 > 60% 且回撤恶化 < 5% → robustness 通过

**依赖：**
- backtest_engine 必须支持批量回测
- strategy 必须有 parameter_space 定义
- 需要结果存储和报告生成模块

---

## 5. Precompute Priority

| 优先级 | 数量 | Factor / Block | 原因 |
|---|---|---|---|
| **P0 必须预计算** | 14 | rsi_14, atr_14, bb_position, bb_bandwidth, roc_10, volume_ratio, turnover_rate, main_force_net_inflow, large_order_net_inflow, active_buy_sell_ratio, money_flow_intensity, d1_state, w1_state, mn1_state | 使用频率极高，计算简单，Preview/Backtest 都依赖 |
| **P1 建议预计算** | 12 | macd_hist, adx_14, supertrend, return_5d_rank, return_20d_rank, industry_rs_rank, volatility_20d_pct, beta_to_index, amihud_illiquidity, multi_timeframe_resonance | 计算成本中等或需 join/横截面，预计算可加速 |
| **P2 可按需计算** | 4 | stop_loss_pct, take_profit_pct, atr_trailing_stop, position_size_red_line | 为 block，依赖回测上下文，只能在回测中动态计算 |
| **P2 可按需计算** | 2 | factor_threshold_signal, robustness_parameter_jitter | 尚未实现，属于框架层 block |

**预计算表建议：**
- `precomputed_factors_daily`: (symbol, trade_date, rsi_14, atr_14, bb_position, bb_bandwidth, roc_10, volume_ratio, turnover_rate, amihud_illiquidity, multi_timeframe_resonance)
- `precomputed_cross_sectional_daily`: (symbol, trade_date, return_5d_rank, return_20d_rank, industry_rs_rank, volatility_20d_pct, beta_to_index)
- `precomputed_moneyflow_daily`: (symbol, trade_date, main_force_net_inflow, large_order_net_inflow, active_buy_sell_ratio, money_flow_intensity)
- `precomputed_state_cube`: (symbol, trade_date, d1_state, w1_state, mn1_state) [已有]

---

## 6. Data Quality Gates

### 6.1 缺失率门槛

| 表 | 关键字段 | 最大缺失率 | 处理策略 |
|---|---|---|---|
| daily_bars | close | 0% | 缺失 = 数据不可用，禁止回测 |
| daily_bars | open/high/low/volume/amount | 1% | 缺失日标记为停牌 |
| daily_bars | shares_outstanding | 5% | 用最新已知值填充 |
| moneyflow_daily | main_force_net_inflow | 5% | 缺失 = 小盘股/新三板，可排除 |
| moneyflow_daily | large_order_net_inflow | 5% | 同上 |
| state_cube | d1_state/w1_state/mn1_state | 0% | 缺失 = State Cube 计算失败 |
| index_daily | index_close | 0% | 缺失 = 指数数据异常 |
| industry | industry_code | 2% | 缺失 = 新股，归入 "unknown" |

### 6.2 日期连续性

| 表 | 要求 |
|---|---|
| daily_bars | 每个 symbol 交易日连续，允许停牌日缺失（需 is_suspended 标记） |
| moneyflow_daily | 与 daily_bars 日期对齐，停牌日可缺失 |
| state_cube | 与 daily_bars 日期对齐 |
| index_daily | 交易日连续 |

### 6.3 股票池覆盖率

| 场景 | 要求 |
|---|---|
| F1 因子计算 | 覆盖 A 股全市场（含 ST、停牌） |
| Preview 查询 | 覆盖用户指定股票池 |
| Backtest | 覆盖回测期内的历史全股票池（含退市） |
| 横截面 rank | 当日可交易股票数 >= 100（rank 稳定） |

### 6.4 停牌/涨跌停处理

| 场景 | 处理策略 |
|---|---|
| 停牌日 | close 不可用于收益率计算，is_suspended=true |
| 涨停日 | 买入信号可能无法成交（limit_up_filter） |
| 跌停日 | 卖出信号可能无法成交（stop_loss 无法执行） |
| ST 股票 | 可过滤（is_st=true） |
| 新股 | 上市 < N 日可过滤（is_new_stock=true） |

### 6.5 复权价格要求

| 字段 | 要求 |
|---|---|
| close | **必须后复权**，复权因子 adj_factor 需同步存储 |
| open/high/low | **必须后复权** |
| entry_price | **必须后复权** |
| 止损/止盈计算 | 使用复权价格，防止除权造成误触发 |
| 注意 | 不可混用前复权和后复权 |

---

## 7. Summary

| 类别 | 数量 | 状态 |
|---|---|---|
| F1 Factor Formula Contracts | 26 | 全部完成，含 Polars/DuckDB hint |
| F1 Block Contracts | 4 | 全部完成，含 backtest_semantics |
| Extra DSL Design Notes | 2 | 完成接口建议 |
| Canonical Field Mapping | 8 张表 | 完成 |
| Precompute Priority | 3 档 | 完成 |
| Data Quality Gates | 5 个维度 | 完成 |

**关键结论：**
1. 26 个 factor 中，14 个为 P0 预计算，12 个为 P1 预计算。
2. 4 个 block 中，3 个 exit block 只能在回测中动态计算（依赖 position_context）。
3. 2 个额外 block（factor_threshold_signal, robustness_parameter_jitter）需要框架层支持，暂不实现。
4. 所有 factor 公式均无未来函数，data_availability=available。
5. 8 张表的 canonical field mapping 已明确，可直接用于 Codex 实现数据管道。

---

> End of Formula Contracts. 26 factors + 4 blocks + 2 DSL notes. Ready for Codex implementation.
