"""Condition Translator - DSL conditions to DuckDB SQL / Polars expressions.

Pure function translation. No LLM involvement. No code execution.
All translations are deterministic and auditable.

Usage:
    registry = ConditionRegistry.default()
    result = translate_condition(condition, registry, dialect="duckdb")
    print(result.sql_expr)  # DuckDB WHERE clause fragment
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .condition_registry import ConditionRegistry
from .dsl_schema import ConditionBlock, StrategyDSL


# ---------------------------------------------------------------------------
# Translation Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TranslationResult:
    """Result of translating a condition to executable form.

    Attributes:
        sql_expr: DuckDB SQL expression fragment (or None if unsupported).
        polars_expr: Polars expression string (or None if unsupported).
        required_columns: Column names needed from data source.
        required_tables: Table names needed from data source.
    """

    sql_expr: str | None
    polars_expr: str | None
    required_columns: list[str]
    required_tables: list[str]


# ---------------------------------------------------------------------------
# Translator Functions
# ---------------------------------------------------------------------------

def translate_condition(
    condition: ConditionBlock,
    registry: ConditionRegistry,
    dialect: Literal["duckdb", "polars"] = "duckdb",
) -> TranslationResult:
    """Translate a single condition block to target dialect.

    Args:
        condition: The condition block to translate.
        registry: Condition registry for validation.
        dialect: Target translation dialect.

    Returns:
        TranslationResult with expression and metadata.

    Raises:
        KeyError: If condition_type is not registered.
        ValueError: If dialect is not supported for this condition.
    """
    spec = registry.get(condition.condition_type)
    params = condition.params

    # Dispatch to translator
    translator_map = {
        "ma_golden_cross": _translate_ma_golden_cross,
        "ma_death_cross": _translate_ma_death_cross,
        "price_cross_ma": _translate_price_cross_ma,
        "state_hex_in": _translate_state_hex_in,
        "state_ef_count": _translate_state_ef_count,
        "volume_ratio": _translate_volume_ratio,
        "industry_include": _translate_industry_include,
        "industry_exclude": _translate_industry_exclude,
        "stop_loss_pct": _translate_stop_loss_pct,
        "take_profit_pct": _translate_take_profit_pct,
        "limit_up_filter": _translate_limit_up_filter,
        # SQX Expansion
        "rsi_threshold": _translate_rsi_threshold,
        "macd_cross": _translate_macd_cross,
        "bollinger_breakout": _translate_bollinger_breakout,
        "ma_bullish_alignment": _translate_ma_bullish_alignment,
        "price_above_ma": _translate_price_above_ma,
        "atr_trailing_stop": _translate_atr_trailing_stop,
        "exit_after_bars": _translate_exit_after_bars,
        "indicator_reversal_exit": _translate_indicator_reversal_exit,
        "liquidity_filter": _translate_liquidity_filter,
        "volatility_filter": _translate_volatility_filter,
        "time_filter": _translate_time_filter,
        "st_new_stock_filter": _translate_st_new_stock_filter,
        "max_position_pct": _translate_max_position_pct,
        "max_drawdown_stop": _translate_max_drawdown_stop,
    }

    translator = translator_map.get(condition.condition_type)
    if translator is None:
        raise ValueError(
            f"No translator implemented for condition type: {condition.condition_type}"
        )

    return translator(params, dialect)


def translate_strategy_where(
    dsl: StrategyDSL,
    registry: ConditionRegistry,
    section: Literal["entry", "exit", "filters"] = "entry",
    dialect: Literal["duckdb", "polars"] = "duckdb",
) -> TranslationResult:
    """Translate an entire strategy section to a combined expression.

    Args:
        dsl: The strategy DSL.
        registry: Condition registry.
        section: Which section to translate.
        dialect: Target dialect.

    Returns:
        TranslationResult with combined expression.
    """
    conditions = getattr(dsl, section)
    if not conditions:
        return TranslationResult(
            sql_expr="1=1" if dialect == "duckdb" else "pl.lit(True)",
            polars_expr="pl.lit(True)" if dialect == "polars" else None,
            required_columns=[],
            required_tables=[],
        )

    results: list[TranslationResult] = []
    for cond in conditions:
        results.append(translate_condition(cond, registry, dialect))

    # Combine expressions with logic operators
    if dialect == "duckdb":
        exprs = [r.sql_expr for r in results if r.sql_expr]
        logics = [c.logic for c in conditions]
        combined = _combine_duckdb(exprs, logics)
    else:
        exprs = [r.polars_expr for r in results if r.polars_expr]
        logics = [c.logic for c in conditions]
        combined = _combine_polars(exprs, logics)

    all_columns = []
    all_tables = []
    for r in results:
        all_columns.extend(r.required_columns)
        all_tables.extend(r.required_tables)

    return TranslationResult(
        sql_expr=combined if dialect == "duckdb" else None,
        polars_expr=combined if dialect == "polars" else None,
        required_columns=list(dict.fromkeys(all_columns)),
        required_tables=list(dict.fromkeys(all_tables)),
    )


# ---------------------------------------------------------------------------
# Combine Helpers
# ---------------------------------------------------------------------------

def _combine_duckdb(exprs: list[str], logics: list[str]) -> str:
    """Combine DuckDB expressions with logic operators."""
    if not exprs:
        return "1=1"
    if len(exprs) == 1:
        return exprs[0]

    parts = [f"({exprs[0]})"]
    for i in range(1, len(exprs)):
        op = logics[i] if i < len(logics) else "and"
        parts.append(f"{op.upper()} ({exprs[i]})")
    return " ".join(parts)


def _combine_polars(exprs: list[str], logics: list[str]) -> str:
    """Combine Polars expressions with logic operators."""
    if not exprs:
        return "pl.lit(True)"
    if len(exprs) == 1:
        return exprs[0]

    parts = [f"({exprs[0]})"]
    for i in range(1, len(exprs)):
        op = logics[i] if i < len(logics) else "and"
        method = "&" if op == "and" else "|"
        parts.append(f"{method} ({exprs[i]})")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Individual Condition Translators
# ---------------------------------------------------------------------------

# -- Moving Average Conditions --------------------------------------------


def _translate_ma_golden_cross(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """MA Golden Cross: fast MA crosses above slow MA."""
    fast = params["fast_period"]
    slow = params["slow_period"]
    col_fast = f"ma_{fast}"
    col_slow = f"ma_{slow}"

    if dialect == "duckdb":
        window = "PARTITION BY symbol ORDER BY date"
        sql = (
            f"({col_fast} > {col_slow} AND "
            f"lag({col_fast}) OVER ({window}) <= lag({col_slow}) OVER ({window}))"
        )
    else:
        sql = None

    if dialect == "polars":
        polars = (
            f'(pl.col("{col_fast}") > pl.col("{col_slow}")) & '
            f'(pl.col("{col_fast}").shift(1) <= pl.col("{col_slow}").shift(1))'
        )
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_fast, col_slow],
        required_tables=["daily_bars"],
    )


def _translate_ma_death_cross(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """MA Death Cross: fast MA crosses below slow MA."""
    fast = params["fast_period"]
    slow = params["slow_period"]
    col_fast = f"ma_{fast}"
    col_slow = f"ma_{slow}"

    if dialect == "duckdb":
        window = "PARTITION BY symbol ORDER BY date"
        sql = (
            f"({col_fast} < {col_slow} AND "
            f"lag({col_fast}) OVER ({window}) >= lag({col_slow}) OVER ({window}))"
        )
    else:
        sql = None

    if dialect == "polars":
        polars = (
            f'(pl.col("{col_fast}") < pl.col("{col_slow}")) & '
            f'(pl.col("{col_fast}").shift(1) >= pl.col("{col_slow}").shift(1))'
        )
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_fast, col_slow],
        required_tables=["daily_bars"],
    )


def _translate_price_cross_ma(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Price crosses above/below a moving average."""
    timeframe = params["timeframe"]
    ma_period = params["ma_period"]
    direction = params["direction"]
    col_price = f"close_{timeframe.lower()}"
    col_ma = f"ma_{ma_period}_{timeframe.lower()}"

    if direction == "above":
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col_price} > {col_ma} AND "
                f"lag({col_price}) OVER ({window}) <= lag({col_ma}) OVER ({window}))"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col_price}") > pl.col("{col_ma}")) & '
                f'(pl.col("{col_price}").shift(1) <= pl.col("{col_ma}").shift(1))'
            )
        else:
            polars = None
    else:  # below
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col_price} < {col_ma} AND "
                f"lag({col_price}) OVER ({window}) >= lag({col_ma}) OVER ({window}))"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col_price}") < pl.col("{col_ma}")) & '
                f'(pl.col("{col_price}").shift(1) >= pl.col("{col_ma}").shift(1))'
            )
        else:
            polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_price, col_ma],
        required_tables=["daily_bars"],
    )


# -- State Conditions -----------------------------------------------------


def _translate_state_hex_in(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """State hex value is in allowed set."""
    timeframe = params["timeframe"]
    values = params["values"]
    col = f"state_hex_{timeframe.lower()}"

    if dialect == "duckdb":
        vals = ", ".join(f"'{v}'" for v in values)
        sql = f"{col} IN ({vals})"
    else:
        sql = None

    if dialect == "polars":
        vals_repr = repr(values)
        polars = f'pl.col("{col}").is_in({vals_repr})'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["state_cube"],
    )


def _translate_state_ef_count(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """EF count comparison."""
    operator = params["operator"]
    value = params["value"]
    col = "ef_count"

    if dialect == "duckdb":
        sql = f"{col} {operator} {value}"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col}") {operator} {value}'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["state_cube"],
    )


# -- Volume Conditions ----------------------------------------------------


def _translate_volume_ratio(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Volume ratio compared to lookback average."""
    lookback = params["lookback"]
    operator = params["operator"]
    value = params["value"]
    col_vol = "volume"
    col_avg = f"volume_ma_{lookback}"

    if dialect == "duckdb":
        sql = f"(CAST({col_vol} AS DOUBLE) / NULLIF({col_avg}, 0)) {operator} {value}"
    else:
        sql = None

    if dialect == "polars":
        polars = (
            f'(pl.col("{col_vol}").cast(pl.Float64) / '
            f'pl.col("{col_avg}").replace(0, None)) {operator} {value}'
        )
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_vol, col_avg],
        required_tables=["daily_bars"],
    )


# -- Industry Filters -----------------------------------------------------


def _translate_industry_include(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Industry is in include list."""
    values = params["values"]
    col = "industry"

    if dialect == "duckdb":
        vals = ", ".join(f"'{v}'" for v in values)
        sql = f"{col} IN ({vals})"
    else:
        sql = None

    if dialect == "polars":
        vals_repr = repr(values)
        polars = f'pl.col("{col}").is_in({vals_repr})'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["stock_info"],
    )


def _translate_industry_exclude(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Industry is NOT in exclude list."""
    values = params["values"]
    col = "industry"

    if dialect == "duckdb":
        vals = ", ".join(f"'{v}'" for v in values)
        sql = f"{col} NOT IN ({vals})"
    else:
        sql = None

    if dialect == "polars":
        vals_repr = repr(values)
        polars = f'~pl.col("{col}").is_in({vals_repr})'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["stock_info"],
    )


# -- Risk Conditions ------------------------------------------------------


def _translate_stop_loss_pct(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Stop loss: exit when loss exceeds percentage."""
    value = params["value"]
    threshold = 1.0 - value
    col_price = "close"
    col_entry = "entry_price"

    if dialect == "duckdb":
        sql = f"{col_price} <= {col_entry} * {threshold}"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col_price}") <= pl.col("{col_entry}") * {threshold}'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_price, col_entry],
        required_tables=["daily_bars", "positions"],
    )


def _translate_take_profit_pct(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Take profit: exit when profit exceeds percentage."""
    value = params["value"]
    threshold = 1.0 + value
    col_price = "close"
    col_entry = "entry_price"

    if dialect == "duckdb":
        sql = f"{col_price} >= {col_entry} * {threshold}"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col_price}") >= pl.col("{col_entry}") * {threshold}'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_price, col_entry],
        required_tables=["daily_bars", "positions"],
    )


# -- Market Filters -------------------------------------------------------


def _translate_limit_up_filter(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Filter limit-up (涨停) stocks."""
    allow = params["allow"]
    col = "is_limit_up"

    if dialect == "duckdb":
        sql = f"{col} = {str(allow).upper()}"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col}") == {str(allow).lower()}'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["daily_bars"],
    )


# ---------------------------------------------------------------------------
# SQX-INSPIRED EXPANSION TRANSLATORS
# ---------------------------------------------------------------------------

# -- Oscillator Entry Conditions --------------------------------------------


def _translate_rsi_threshold(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """RSI threshold comparison."""
    period = params["period"]
    operator = params["operator"]
    value = params["value"]
    col = f"rsi_{period}"

    if dialect == "duckdb":
        sql = f"{col} {operator} {value}"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col}") {operator} {value}'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["daily_bars"],
    )


def _translate_macd_cross(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """MACD line crosses signal line."""
    fast = params["fast"]
    slow = params["slow"]
    signal = params["signal"]
    direction = params["direction"]
    col_macd = f"macd_{fast}_{slow}"
    col_signal = f"macd_signal_{fast}_{slow}_{signal}"

    if direction == "bullish":
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col_macd} > {col_signal} AND "
                f"lag({col_macd}) OVER ({window}) <= lag({col_signal}) OVER ({window}))"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col_macd}") > pl.col("{col_signal}")) & '
                f'(pl.col("{col_macd}").shift(1) <= pl.col("{col_signal}").shift(1))'
            )
        else:
            polars = None
    else:  # bearish
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col_macd} < {col_signal} AND "
                f"lag({col_macd}) OVER ({window}) >= lag({col_signal}) OVER ({window}))"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col_macd}") < pl.col("{col_signal}")) & '
                f'(pl.col("{col_macd}").shift(1) >= pl.col("{col_signal}").shift(1))'
            )
        else:
            polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_macd, col_signal],
        required_tables=["daily_bars"],
    )


def _translate_bollinger_breakout(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Price breaks Bollinger Band."""
    period = params["period"]
    std_dev = params["std_dev"]
    direction = params["direction"]
    col_close = "close"
    col_upper = f"bb_upper_{period}_{std_dev}"
    col_lower = f"bb_lower_{period}_{std_dev}"

    if direction == "upper":
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col_close} > {col_upper} AND "
                f"lag({col_close}) OVER ({window}) <= lag({col_upper}) OVER ({window}))"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col_close}") > pl.col("{col_upper}")) & '
                f'(pl.col("{col_close}").shift(1) <= pl.col("{col_upper}").shift(1))'
            )
        else:
            polars = None
    else:  # lower
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col_close} < {col_lower} AND "
                f"lag({col_close}) OVER ({window}) >= lag({col_lower}) OVER ({window}))"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col_close}") < pl.col("{col_lower}")) & '
                f'(pl.col("{col_close}").shift(1) >= pl.col("{col_lower}").shift(1))'
            )
        else:
            polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_close, col_upper, col_lower],
        required_tables=["daily_bars"],
    )


# -- Trend/MA Variants ------------------------------------------------------


def _translate_ma_bullish_alignment(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Multiple MAs in bullish alignment."""
    ma_periods = params["ma_periods"]
    cols = [f"ma_{p}" for p in ma_periods]

    if len(cols) < 2:
        raise ValueError("ma_periods must have at least 2 elements")

    if dialect == "duckdb":
        conditions = []
        for i in range(len(cols) - 1):
            conditions.append(f"{cols[i]} > {cols[i + 1]}")
        sql = " AND ".join(conditions)
    else:
        sql = None

    if dialect == "polars":
        conditions = []
        for i in range(len(cols) - 1):
            conditions.append(f'(pl.col("{cols[i]}") > pl.col("{cols[i + 1]}"))')
        polars = " & ".join(conditions)
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=cols,
        required_tables=["daily_bars"],
    )


def _translate_price_above_ma(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Price above MA for N consecutive bars."""
    ma_period = params["ma_period"]
    consecutive_bars = params.get("consecutive_bars", 1)
    col_price = "close"
    col_ma = f"ma_{ma_period}"

    if dialect == "duckdb":
        if consecutive_bars == 1:
            sql = f"{col_price} > {col_ma}"
        else:
            # For N consecutive bars, we check current and N-1 lags
            parts = [f"{col_price} > {col_ma}"]
            window = "PARTITION BY symbol ORDER BY date"
            for i in range(1, consecutive_bars):
                parts.append(f"lag({col_price}, {i}) OVER ({window}) > lag({col_ma}, {i}) OVER ({window})")
            sql = " AND ".join(parts)
    else:
        sql = None

    if dialect == "polars":
        if consecutive_bars == 1:
            polars = f'(pl.col("{col_price}") > pl.col("{col_ma}"))'
        else:
            parts = [f'(pl.col("{col_price}") > pl.col("{col_ma}"))']
            for i in range(1, consecutive_bars):
                parts.append(f'(pl.col("{col_price}").shift({i}) > pl.col("{col_ma}").shift({i}))')
            polars = " & ".join(parts)
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_price, col_ma],
        required_tables=["daily_bars"],
    )


# -- Advanced Exit Conditions -----------------------------------------------


def _translate_atr_trailing_stop(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """ATR trailing stop (Chandelier-style)."""
    atr_period = params["atr_period"]
    multiplier = params["multiplier"]
    col_close = "close"
    col_high = "high"
    col_atr = f"atr_{atr_period}"

    if dialect == "duckdb":
        # Stop = highest_high_since_entry - multiplier * ATR
        sql = f"{col_close} <= (max_high_since_entry - {multiplier} * {col_atr})"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col_close}") <= (pl.col("max_high_since_entry") - {multiplier} * pl.col("{col_atr}"))'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_close, col_high, col_atr],
        required_tables=["daily_bars", "positions"],
    )


def _translate_exit_after_bars(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Exit after holding N bars."""
    max_bars = params["max_bars"]
    col = "bars_since_entry"

    if dialect == "duckdb":
        sql = f"{col} >= {max_bars}"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col}") >= {max_bars}'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["positions"],
    )


def _translate_indicator_reversal_exit(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Exit when indicator reverses from extreme."""
    indicator = params["indicator"]
    period = params["period"]
    direction = params["direction"]
    col = f"{indicator}_{period}"

    if direction == "overbought":
        # Exit when indicator was above extreme and now falling
        if indicator == "rsi":
            threshold = 70
        elif indicator == "cci":
            threshold = 100
        else:  # macd
            threshold = 0
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col} < {threshold} AND "
                f"lag({col}) OVER ({window}) >= {threshold})"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col}") < {threshold}) & '
                f'(pl.col("{col}").shift(1) >= {threshold})'
            )
        else:
            polars = None
    else:  # oversold
        if indicator == "rsi":
            threshold = 30
        elif indicator == "cci":
            threshold = -100
        else:  # macd
            threshold = 0
        if dialect == "duckdb":
            window = "PARTITION BY symbol ORDER BY date"
            sql = (
                f"({col} > {threshold} AND "
                f"lag({col}) OVER ({window}) <= {threshold})"
            )
        else:
            sql = None
        if dialect == "polars":
            polars = (
                f'(pl.col("{col}") > {threshold}) & '
                f'(pl.col("{col}").shift(1) <= {threshold})'
            )
        else:
            polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["daily_bars"],
    )


# -- Enhanced Filter Conditions ---------------------------------------------


def _translate_liquidity_filter(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Filter by minimum turnover."""
    min_turnover = params["min_turnover"]
    col = "amount"

    if dialect == "duckdb":
        sql = f"{col} >= {min_turnover}"
    else:
        sql = None

    if dialect == "polars":
        polars = f'pl.col("{col}") >= {min_turnover}'
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col],
        required_tables=["daily_bars"],
    )


def _translate_volatility_filter(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Filter by volatility level (ATR/close ratio)."""
    atr_period = params["atr_period"]
    operator = params["operator"]
    threshold_pct = params["threshold_pct"]
    col_atr = f"atr_{atr_period}"
    col_close = "close"

    if dialect == "duckdb":
        sql = f"(CAST({col_atr} AS DOUBLE) / NULLIF({col_close}, 0)) {operator} {threshold_pct}"
    else:
        sql = None

    if dialect == "polars":
        polars = (
            f'(pl.col("{col_atr}").cast(pl.Float64) / '
            f'pl.col("{col_close}").replace(0, None)) {operator} {threshold_pct}'
        )
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_atr, col_close],
        required_tables=["daily_bars"],
    )


def _translate_time_filter(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Filter by trading time windows."""
    month_range = params.get("month_range", [])
    day_of_week = params.get("day_of_week", [])
    exclude_holidays = params.get("exclude_holidays", True)

    conditions = []
    if month_range:
        months = ", ".join(str(m) for m in month_range)
        conditions.append(f"month IN ({months})")
    if day_of_week:
        days = ", ".join(str(d) for d in day_of_week)
        conditions.append(f"day_of_week IN ({days})")
    if exclude_holidays:
        conditions.append("is_holiday = FALSE")

    if dialect == "duckdb":
        if conditions:
            sql = " AND ".join(conditions)
        else:
            sql = "1=1"
    else:
        sql = None

    if dialect == "polars":
        if conditions:
            # Simplified polars representation
            polars = " & ".join(f'pl.col("{c.split()[0]}") {c.split()[1]} {c.split()[2]}' for c in conditions)
        else:
            polars = "pl.lit(True)"
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=["month", "day_of_week", "is_holiday"],
        required_tables=["daily_bars"],
    )


def _translate_st_new_stock_filter(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Filter out ST and new stocks."""
    exclude_st = params.get("exclude_st", True)
    max_listing_days = params.get("max_listing_days", 60)

    conditions = []
    if exclude_st:
        conditions.append("is_st = FALSE")
    if max_listing_days is not None:
        conditions.append(f"days_since_listing >= {max_listing_days}")

    if dialect == "duckdb":
        if conditions:
            sql = " AND ".join(conditions)
        else:
            sql = "1=1"
    else:
        sql = None

    if dialect == "polars":
        if conditions:
            polars_parts = []
            if exclude_st:
                polars_parts.append('(pl.col("is_st") == False)')
            if max_listing_days is not None:
                polars_parts.append(f'(pl.col("days_since_listing") >= {max_listing_days})')
            polars = " & ".join(polars_parts) if polars_parts else "pl.lit(True)"
        else:
            polars = "pl.lit(True)"
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=["is_st", "days_since_listing"],
        required_tables=["stock_info"],
    )


# -- Risk / Money Management ------------------------------------------------


def _translate_max_position_pct(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Max position percentage (red-line enforced, no SQL translation)."""
    # This is a meta-condition enforced by red-line validator, not translated to SQL
    return TranslationResult(
        sql_expr="1=1",
        polars_expr="pl.lit(True)",
        required_columns=[],
        required_tables=[],
    )


def _translate_max_drawdown_stop(
    params: dict, dialect: Literal["duckdb", "polars"]
) -> TranslationResult:
    """Emergency stop on portfolio drawdown."""
    value = params["value"]
    col_equity = "portfolio_equity"
    col_peak = "portfolio_peak"

    if dialect == "duckdb":
        sql = f"({col_equity} / NULLIF({col_peak}, 0)) <= {1.0 - value}"
    else:
        sql = None

    if dialect == "polars":
        polars = (
            f'(pl.col("{col_equity}") / pl.col("{col_peak}").replace(0, None)) '
            f'<= {1.0 - value}'
        )
    else:
        polars = None

    return TranslationResult(
        sql_expr=sql,
        polars_expr=polars,
        required_columns=[col_equity, col_peak],
        required_tables=["portfolio"],
    )
