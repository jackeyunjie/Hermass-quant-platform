# SQX Local Block Inventory Study

## Scope And Guardrails

Source inspected:

- `/Applications/StrategyQuantXB143.app/Contents/Resources/internal/extend/Snippets/SQ`
- `/Applications/StrategyQuantXB143.app/Contents/Resources/custom_indicators`

Method:

- Directory and filename inventory only.
- No decompilation.
- No copying proprietary source bodies.
- Use observed categories and names as architectural inspiration for Hermass metadata.

## High-Level Inventory

Observed local SQX snippet categories:

| Category | Approx Files | Hermass Mapping |
|---|---:|---|
| `Blocks` | 548 | signal/condition/price/time/order/action blocks |
| `ExitMethods` | 5 | exit blocks |
| `MoneyManagement` | 12 | sizing/risk blocks |
| `MonteCarlo` | 11 | robustness blocks |
| `WhatIf` | 15 | robustness / sensitivity blocks |
| `TradingOptions` | 8 | execution constraints |
| `TradeAnalysis` | 26 | performance analysis blocks |
| `Columns` | 161 | metric/report columns |
| `Stats` | 7 | report/stat templates |
| `Calculators` | 7 | rolling/stat calculators |
| `Negater` | 15 | logical inverse / condition transform |
| `Internal` | 33 | strategy/rule/block abstractions |

## Observed Block Families

### Strategy Control

Examples by filename:

- Market position state: long/short/flat/not long/not short.
- Order state: pending exists, pending does not exist, last order was, bars since order open/closed.
- Account state: balance, equity.
- PnL state: open/closed PnL in money/pips.
- SL/PT state: order stop loss, order profit target.

Hermass implication:

- Add `position_context` and `account_context` as first-class block requirements.
- Separate strategy-control blocks from pure factor conditions.
- In A-share MVP, most strategy-control blocks are backtest-only, not preview-only.

### Comparisons

Examples by filename:

- Greater/lower/equal/not equal.
- Crosses above/below.
- Rising/falling.
- Above/below moving average.
- Count comparisons.
- Percentile comparisons.
- AND/OR/NOT.

Hermass implication:

- Generic factor conditions are the right abstraction:
  - `factor_threshold`
  - `factor_cross`
  - `factor_slope`
  - `factor_count`
  - `factor_percentile`
  - `condition_group`
  - `condition_not`

### Bar And Time

Examples by filename:

- Current date/time/hour/minute/month/day-of-week.
- Bar date/time/hour/minute/month/day-of-week.
- First/last week of month.
- First/last trading day of month.
- Is bar open.

Hermass A-share mapping:

- Trading session filter.
- Month-end / week-end rebalance.
- Open/close auction constraints.
- Earnings/calendar-event windows in future.

### Price

Examples by filename:

- OHLC.
- Daily/weekly/monthly OHLC.
- Session OHLC.
- Bid/Ask/Spread.
- Heiken Ashi OHLC.
- Volume.

Hermass mapping:

- Multi-timeframe OHLCV values.
- Session fields are useful for minute data later.
- Bid/ask/spread mostly non-MVP for A-share daily but useful for execution realism.

### Candle Patterns

Examples by filename:

- Doji.
- Hammer.
- Shooting Star.
- Bullish/Bearish Engulfing.
- Dark Cloud.
- Piercing Line.

Hermass mapping:

- Add as pattern factors, not core MVP.
- Must evaluate with IC/stratified returns before production exposure.

### Exit Methods

Examples by filename:

- StopLoss.
- ProfitTarget.
- TrailingStop.
- MoveSL2BE.
- ExitAfterBars.

Hermass mapping:

- Existing `stop_loss_pct` and `take_profit_pct` are only first layer.
- Need:
  - `atr_trailing_stop`
  - `chandelier_exit`
  - `exit_after_bars`
  - `break_even_stop`
  - `state_invalidation_exit`

### Trading Options

Examples by filename:

- Exit at end of day.
- Exit on Friday.
- Limit time range.
- Max trades per day.
- Min/max SL/PT.
- Max distance from market.
- Use initial SL/PT.

Hermass A-share mapping:

- T+1 constraints.
- No intraday sell for same-day buy.
- Rebalance time windows.
- Max trades per day.
- Max distance from reference price.
- Min/max stop/take-profit boundaries.

### Money Management

Examples by filename:

- Fixed size.
- Fixed amount.
- Risk fixed pct of account.
- ATR risk-based sizing.
- Stockpicker fixed amount/risk pct.
- Martingale-like sizing.

Hermass mapping:

- MVP should support conservative sizing only:
  - fixed percent.
  - fixed amount.
  - ATR risk-based.
  - volatility targeting.
- Martingale should be explicitly forbidden by red lines unless research-only.

### Monte Carlo / What If

Examples by filename:

- Randomize history data.
- Randomize OHLC.
- Randomize spread/slippage.
- Randomly skip trades.
- Randomize strategy parameters.
- Randomize starting bar.
- Take every second trade.
- Exclude biggest/worst trades.
- Exclude shorts.
- Remove pending trades.
- By hours/days/months.

Hermass mapping:

- Robustness blocks should be first-class:
  - parameter jitter.
  - random trade skip.
  - slippage/tax stress.
  - history perturbation.
  - date/time segmentation.
  - remove top winners / worst losers.
  - symbol/industry/state split.

### Trade Analysis / Columns / Stats

Examples by filename:

- Profit/loss by year/month/day/hour/weekday.
- Trades by duration.
- Long/short trade counts and PnL.
- MAE/MFE.
- Drawdown.
- Stagnation.
- Payout ratio.
- Fitness IS/OOS.

Hermass mapping:

- Backtest report should include:
  - MAE/MFE.
  - stagnation.
  - payoff/payout ratio.
  - trade duration distribution.
  - regime/state split.
  - IS/OOS fitness.
  - strategy acceptance throughput later.

## Custom Indicator Inventory

Observed MT5 custom indicators include:

- Trend: `SqADX`, `SqAroon`, `SqGannHiLo`, `SqSuperTrend`, `SqIchimoku`, `SqParabolicSAR`, `SqVortex`.
- Moving average variants: `SqHullMovingAverage`, `SqKAMA`, `SqTEMA`.
- Volatility/range: `SqATR`, `SqTrueRange`, `SqBBWidthRatio`, `SqKeltnerChannel`, `SqUlcerIndex`.
- Momentum/oscillator: `SqCCI`, `SqROC`, `SqStochastic`, `SqWPR`, `SqQQE`, `SqSchaffTrendCycle`, `SqLaguerreRSI`, `SqWaveTrend`, `SqReflex`.
- Price levels/patterns: `SqPivots`, `SqFibo`, `SqFractal`, `SqHeikenAshi`, highest/lowest variants.
- Volume/session: `SqAvgVolume`, `SqVWAP`, `SqSessionOHLC`.
- Other: `CommercialsIndex`, `DeMarker`, `SqBullsPower`, `SqBearsPower`, `SqEfficiencyRatio`, `SqSRPercentRank`.

Hermass implication:

- Technical factor catalog should start with these families.
- Do not import MQL code. Reimplement formulas independently or use transparent Polars/DuckDB formulas.
- Any indicator with ambiguous proprietary formula should be marked `research` until independently specified.

## Hermass Priority Derived From SQX

### Must Add To Block Library F0

- `signal_compare`
- `signal_cross`
- `signal_rising_falling`
- `signal_percentile`
- `time_filter`
- `price_source`
- `exit_stop_loss`
- `exit_take_profit`
- `exit_trailing_stop`
- `exit_after_bars`
- `sizing_fixed_pct`
- `sizing_atr_risk`
- `robustness_parameter_jitter`
- `robustness_random_skip_trades`
- `robustness_slippage_stress`

### Must Add To Factor Catalog F1

- RSI.
- ROC.
- CCI.
- Stochastic.
- Williams %R.
- ADX / DI.
- Aroon.
- ATR / true range.
- BB width / percent b.
- Keltner Channel.
- SuperTrend.
- VWAP deviation.
- Hull MA / KAMA.
- Heiken Ashi.
- highest/lowest N.
- PercentRank.
- Ulcer Index.

### Must Add To Backtest Report Later

- MAE/MFE.
- trade duration.
- stagnation.
- PnL by month/weekday/state.
- IS/OOS fitness.
- robustness summary.

## A-Share Adaptation Notes

SQX is cross-market and heavily FX/futures oriented. Hermass must adapt:

- Replace pips with percent/ticks/RMB.
- Add T+1.
- Add limit-up/limit-down fill constraints.
- Add ST/new-stock filters.
- Add stamp tax/commission.
- Add liquidity filters.
- Add split by market state and industry.

## Next Steps

1. Kimi should use this inventory to produce a 120+ block candidate table.
2. Qoder should turn this into `BlockSpec` / `BlockRegistry`.
3. Codex should implement F0 metadata registry before any large formula implementation.
