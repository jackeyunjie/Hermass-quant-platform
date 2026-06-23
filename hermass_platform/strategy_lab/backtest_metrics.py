"""Backtest Metrics - Core performance metric computation.

Computes standard quantitative metrics from daily equity curves and
trade records. All metrics use daily-bar granularity.

Design constraints:
    - Pure functions, no side effects.
    - Returns dict compatible with storage JSON column.
    - Handles edge cases (zero trades, single day, etc.).
"""

from __future__ import annotations

import math

import polars as pl


def compute_light_metrics(
    daily_curve: pl.DataFrame,
    trades: pl.DataFrame,
    initial_capital: float,
) -> dict[str, float | int | None]:
    """Compute core Light Backtest metrics.

    Args:
        daily_curve: DataFrame with columns ``date``, ``portfolio_value``,
            ``daily_return``. Must be sorted by date ascending.
        trades: DataFrame with columns ``pnl``, ``pnl_pct``,
            ``entry_date``, ``exit_date``, ``shares``, ``total_cost``.
            One row per closed trade.
        initial_capital: Starting portfolio value.

    Returns:
        Dict with all standard metric keys. Values are None when
        insufficient data (e.g. zero trades).
    """
    result: dict[str, float | int | None] = {
        "total_return": None,
        "annual_return": None,
        "max_drawdown": None,
        "sharpe_ratio": None,
        "win_rate": None,
        "profit_factor": None,
        "trade_count": 0,
        "total_trades": 0,
        "avg_holding_days": None,
        "turnover": None,
        "cost_total": None,
    }

    # Guard: empty curve
    if daily_curve.is_empty():
        return result

    n_days = len(daily_curve)
    final_value = daily_curve["portfolio_value"][-1]

    # Total return
    if initial_capital > 0:
        result["total_return"] = (final_value - initial_capital) / initial_capital
    else:
        result["total_return"] = 0.0

    # Annual return (assume 252 trading days)
    if n_days > 1 and initial_capital > 0 and final_value > 0:
        annual_factor = 252.0 / (n_days - 1)
        total_return = result["total_return"]
        if total_return > -1.0:
            result["annual_return"] = (1.0 + total_return) ** annual_factor - 1.0
        else:
            result["annual_return"] = -1.0

    # Max drawdown
    result["max_drawdown"] = _compute_max_drawdown(daily_curve)

    # Sharpe ratio (annualized, assume risk-free rate = 0)
    result["sharpe_ratio"] = _compute_sharpe(daily_curve)

    # Trade-based metrics
    if trades is not None and not trades.is_empty():
        n_trades = len(trades)
        result["trade_count"] = n_trades
        result["total_trades"] = n_trades

        # Win rate
        if "pnl" in trades.columns:
            wins = (trades["pnl"] > 0).sum()
            result["win_rate"] = wins / n_trades if n_trades > 0 else None

        # Profit factor
        if "pnl" in trades.columns:
            gross_profit = trades.filter(pl.col("pnl") > 0)["pnl"].sum()
            gross_loss = abs(trades.filter(pl.col("pnl") < 0)["pnl"].sum())
            if gross_loss > 0:
                result["profit_factor"] = gross_profit / gross_loss
            elif gross_profit > 0:
                result["profit_factor"] = float("inf")
            else:
                result["profit_factor"] = 0.0

        # Average holding days
        if "entry_date" in trades.columns and "exit_date" in trades.columns:
            try:
                entry_dates = pl.col("entry_date").str.to_date("%Y-%m-%d")
                exit_dates = pl.col("exit_date").str.to_date("%Y-%m-%d")
                holding_days = (exit_dates - entry_dates).dt.total_days()
                avg_days = holding_days.mean()
                result["avg_holding_days"] = float(avg_days) if avg_days is not None else None
            except Exception:
                result["avg_holding_days"] = None

        # Turnover (total traded notional / initial capital)
        if "entry_price" in trades.columns and "shares" in trades.columns:
            total_notional = (trades["entry_price"] * trades["shares"]).sum()
            result["turnover"] = float(total_notional) / initial_capital if initial_capital > 0 else None

        # Total cost
        if "total_cost" in trades.columns:
            result["cost_total"] = float(trades["total_cost"].sum())

    return result


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _compute_max_drawdown(daily_curve: pl.DataFrame) -> float | None:
    """Compute maximum drawdown from daily portfolio value curve."""
    if daily_curve.is_empty() or len(daily_curve) < 2:
        return None

    values = daily_curve["portfolio_value"].to_list()
    peak = values[0]
    max_dd = 0.0

    for v in values:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (v - peak) / peak
            if dd < max_dd:
                max_dd = dd

    return max_dd


def _compute_sharpe(daily_curve: pl.DataFrame) -> float | None:
    """Compute annualized Sharpe ratio from daily returns."""
    if daily_curve.is_empty() or len(daily_curve) < 2:
        return None

    returns = daily_curve["daily_return"]

    # Filter out NaN
    returns = returns.drop_nulls()
    if len(returns) < 2:
        return None

    mean_ret = returns.mean()
    std_ret = returns.std()

    if std_ret is None or std_ret == 0.0:
        return 0.0 if mean_ret == 0.0 else None

    # Annualize: sqrt(252) * mean / std
    sharpe = math.sqrt(252.0) * mean_ret / std_ret
    return sharpe
