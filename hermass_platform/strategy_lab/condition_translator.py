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
