#!/usr/bin/env python3
"""Validate real DuckDB data before running benchmarks.

Checks foundation DB and state cube DB for required tables, columns,
row counts, date ranges, indexes, types, uniqueness, null/range,
trading-day coverage, freshness, schema aliases, and metadata.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb

REQUIRED_FOUNDATION_COLUMNS = [
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "ma_5",
    "ma_10",
    "ma_20",
    "ma_60",
    "atr_14",
    "bb_position",
    "volume_ratio",
    "adx_14",
    "is_limit_up",
]

REQUIRED_STATE_CUBE_COLUMNS = [
    "symbol",
    "date",
    "d1_state",
    "w1_state",
    "mn1_state",
]

# Numeric columns for type checking
FOUNDATION_NUMERIC_COLUMNS = [
    "open", "high", "low", "close", "volume",
    "ma_5", "ma_10", "ma_20", "ma_60",
    "atr_14", "bb_position", "volume_ratio", "adx_14",
]

# Flag columns for type checking
FOUNDATION_FLAG_COLUMNS = ["is_limit_up", "is_limit_down", "is_suspended"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate real data DuckDB files")
    parser.add_argument(
        "--foundation-db", type=str, required=True, help="Path to p116_foundation.duckdb"
    )
    parser.add_argument(
        "--state-cube-db", type=str, required=True, help="Path to state_cube.duckdb"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to write validation JSON"
    )
    parser.add_argument(
        "--min-symbols", type=int, default=5000, help="Minimum symbol count"
    )
    parser.add_argument(
        "--min-trading-days", type=int, default=252, help="Minimum trading days per symbol"
    )
    parser.add_argument(
        "--max-staleness-days", type=int, default=30, help="Max days since last data date"
    )
    parser.add_argument(
        "--as-of-date", type=str, default=None, help="As-of date for freshness check (YYYY-MM-DD)"
    )
    return parser.parse_args()


def _check_db_exists(db_path: str, label: str, output: dict) -> bool:
    if not os.path.exists(db_path):
        output["ok"] = False
        output["errors"].append(f"{label} DB not found: {db_path}")
        return False
    return True


def _get_columns(con: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    return [
        row[0]
        for row in con.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = ?
            """,
            [table],
        ).fetchall()
    ]


def _get_column_types(con: duckdb.DuckDBPyConnection, table: str) -> dict[str, str]:
    rows = con.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = ?
        """,
        [table],
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def _get_indexes(con: duckdb.DuckDBPyConnection, table: str) -> dict[str, list[str]]:
    """Return map index_name -> list of column expressions."""
    idx_map: dict[str, list[str]] = {}
    try:
        rows = con.execute(
            """
            SELECT index_name, expressions
            FROM duckdb_indexes()
            WHERE table_name = ?
            """,
            [table],
        ).fetchall()
        for idx_name, expressions in rows:
            cols = []
            if expressions and isinstance(expressions, str):
                inner = expressions.strip().strip("[]")
                if inner:
                    cols = [c.strip().strip('"').strip("'") for c in inner.split(",")]
            idx_map[idx_name] = cols
    except Exception as e:
        idx_map["__error__"] = [str(e)]
    return idx_map


def _check_types(
    con: duckdb.DuckDBPyConnection,
    table: str,
    col_types: dict[str, str],
    output: dict,
    label: str,
) -> None:
    """Check that date/numeric/flag columns have sensible types."""
    type_errors = []

    if "date" in col_types:
        dt = col_types["date"].upper()
        if dt not in ("DATE", "TIMESTAMP", "DATETIME"):
            type_errors.append(f"'{table}.date' type is {dt}, expected DATE/TIMESTAMP")
    else:
        type_errors.append(f"'{table}.date' missing")

    for col in FOUNDATION_NUMERIC_COLUMNS:
        if col in col_types:
            ct = col_types[col].upper()
            if ct not in (
                "DOUBLE", "FLOAT", "REAL", "DECIMAL", "NUMERIC",
                "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "INT",
            ):
                type_errors.append(f"'{table}.{col}' type is {ct}, expected numeric")

    for col in FOUNDATION_FLAG_COLUMNS:
        if col in col_types:
            ct = col_types[col].upper()
            if ct not in ("BOOLEAN", "BOOL", "INTEGER", "BIGINT", "SMALLINT", "TINYINT"):
                type_errors.append(f"'{table}.{col}' type is {ct}, expected boolean/integer")

    output[label]["type_checks"] = {
        "ok": len(type_errors) == 0,
        "errors": type_errors,
    }
    if type_errors:
        output["ok"] = False
        output["errors"].extend(type_errors)


def _check_uniqueness(
    con: duckdb.DuckDBPyConnection,
    table: str,
    output: dict,
    label: str,
) -> None:
    """Check (symbol, date) uniqueness."""
    total = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    distinct = con.execute(
        f"SELECT COUNT(DISTINCT (symbol, date)) FROM {table}"
    ).fetchone()[0]
    is_unique = total == distinct
    output[label]["uniqueness_checks"] = {
        "total_rows": total,
        "distinct_symbol_date": distinct,
        "ok": is_unique,
    }
    if not is_unique:
        msg = f"{table} has duplicate (symbol, date): {total} rows vs {distinct} distinct"
        output["ok"] = False
        output["errors"].append(msg)


def _check_null_range(
    con: duckdb.DuckDBPyConnection,
    table: str,
    output: dict,
    label: str,
) -> None:
    """Check null rates and basic range constraints."""
    errors = []
    warnings = []
    columns = _get_columns(con, table)
    total = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    # close > 0
    if "close" in columns:
        bad = con.execute(
            f"SELECT COUNT(*) FROM {table} WHERE close IS NULL OR close <= 0"
        ).fetchone()[0]
        if bad > 0:
            errors.append(f"{table}: {bad}/{total} rows have close <= 0 or NULL")

    # high >= low
    if "high" in columns and "low" in columns:
        bad = con.execute(
            f"SELECT COUNT(*) FROM {table} WHERE high < low"
        ).fetchone()[0]
        if bad > 0:
            errors.append(f"{table}: {bad} rows have high < low")

    # volume >= 0
    if "volume" in columns:
        bad = con.execute(
            f"SELECT COUNT(*) FROM {table} WHERE volume IS NULL OR volume < 0"
        ).fetchone()[0]
        if bad > 0:
            errors.append(f"{table}: {bad} rows have volume < 0 or NULL")

    # Key indicator null rates
    indicator_cols = ["ma_5", "ma_10", "ma_20", "ma_60", "atr_14", "volume_ratio", "adx_14"]
    null_rates = {}
    for col in indicator_cols:
        if col in columns:
            null_count = con.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"
            ).fetchone()[0]
            rate = null_count / total if total else 0
            null_rates[col] = round(rate, 4)
            if rate > 0.05:
                warnings.append(f"{table}.{col} null rate {rate:.2%} > 5%")

    output[label]["null_range_checks"] = {
        "ok": len(errors) == 0,
        "errors": errors,
        "null_rates": null_rates,
    }
    if errors:
        output["ok"] = False
        output["errors"].extend(errors)
    output[label]["warnings"].extend(warnings)


def _check_trading_day_coverage(
    con: duckdb.DuckDBPyConnection,
    table: str,
    min_trading_days: int,
    output: dict,
    label: str,
) -> None:
    """Check per-symbol trading day coverage."""
    global_dates = con.execute(
        f"SELECT COUNT(DISTINCT date) FROM {table}"
    ).fetchone()[0]

    rows = con.execute(
        f"""
        SELECT symbol, COUNT(DISTINCT date) AS dc
        FROM {table}
        GROUP BY symbol
        ORDER BY dc ASC
        LIMIT 10
        """
    ).fetchall()

    low_coverage = []
    for sym, dc in rows:
        if dc < min_trading_days:
            low_coverage.append({"symbol": sym, "distinct_dates": dc})

    output[label]["trading_day_coverage"] = {
        "global_distinct_dates": global_dates,
        "low_coverage_symbols": low_coverage,
        "ok": len(low_coverage) == 0,
    }
    if low_coverage:
        output[label]["warnings"].append(
            f"{table}: {len(low_coverage)} symbols below {min_trading_days} trading days"
        )


def _check_freshness(
    con: duckdb.DuckDBPyConnection,
    table: str,
    as_of_date: date | None,
    max_staleness_days: int,
    output: dict,
    label: str,
) -> None:
    """Check data freshness against as-of date."""
    date_max = con.execute(f"SELECT MAX(date) FROM {table}").fetchone()[0]
    if date_max is None:
        output[label]["freshness"] = {"date_max": None, "staleness_days": None, "ok": False}
        output["ok"] = False
        output["errors"].append(f"{table}: no data for freshness check")
        return

    date_max_str = str(date_max)
    dmax = date.fromisoformat(date_max_str) if isinstance(date_max, str) else date_max
    if as_of_date is None:
        as_of_date = date.today()

    staleness = (as_of_date - dmax).days
    is_fresh = staleness <= max_staleness_days
    output[label]["freshness"] = {
        "date_max": date_max_str,
        "as_of_date": as_of_date.isoformat(),
        "staleness_days": staleness,
        "max_staleness_days": max_staleness_days,
        "ok": is_fresh,
    }
    if not is_fresh:
        output["ok"] = False
        output["errors"].append(
            f"{table}: staleness {staleness} days > threshold {max_staleness_days}"
        )


def _check_alias(
    con: duckdb.DuckDBPyConnection,
    table: str,
    output: dict,
    label: str,
) -> None:
    """Check state cube alias strategy: d1_state vs state_hex_d1 etc."""
    cols = _get_columns(con, table)
    state_aliases = {
        "d1": ("d1_state", "state_hex_d1"),
        "w1": ("w1_state", "state_hex_w1"),
        "mn1": ("mn1_state", "state_hex_mn1"),
    }
    alias_report = {}
    for tf, (primary, alt) in state_aliases.items():
        has_primary = primary in cols
        has_alt = alt in cols
        alias_report[tf] = {
            "primary": primary,
            "alt": alt,
            "primary_exists": has_primary,
            "alt_exists": has_alt,
            "ok": has_primary or has_alt,
        }
        if not (has_primary or has_alt):
            output["ok"] = False
            output["errors"].append(f"{table}: missing both {primary} and {alt}")

    output[label]["alias_checks"] = alias_report


def _check_metadata(
    con: duckdb.DuckDBPyConnection,
    db_path: str,
    output: dict,
    label: str,
) -> None:
    """Check for metadata: data_license table or metadata JSON file."""
    tables = [
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    ]

    meta = {}
    if "data_license" in tables:
        try:
            rows = con.execute("SELECT * FROM data_license LIMIT 1").fetchall()
            cols = [desc[0] for desc in con.execute("SELECT * FROM data_license LIMIT 0").description]
            if rows:
                meta["db_record"] = dict(zip(cols, rows[0]))
        except Exception as e:
            meta["db_record_error"] = str(e)
    else:
        meta["db_record"] = None

    # Look for metadata JSON next to the DB
    db_dir = Path(db_path).parent
    meta_file = db_dir / "metadata.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta["file"] = json.load(f)
        except Exception as e:
            meta["file_error"] = str(e)
    else:
        meta["file"] = None

    # Required keys for Phase 2
    required_keys = ["price_adjustment", "data_source", "license_status", "last_refresh_at"]
    found_keys = []
    source = None

    if meta.get("db_record"):
        found_keys = [k for k in required_keys if k in meta["db_record"]]
        source = "db_record"
    elif meta.get("file"):
        found_keys = [k for k in required_keys if k in meta["file"]]
        source = "file"

    missing_keys = [k for k in required_keys if k not in found_keys]
    meta["required_keys_found"] = found_keys
    meta["required_keys_missing"] = missing_keys
    meta["source"] = source

    output[label]["metadata_checks"] = meta
    if missing_keys:
        output[label]["warnings"].append(
            f"Metadata missing keys: {missing_keys}"
        )


def _validate_foundation(
    db_path: str,
    output: dict,
    min_symbols: int,
    min_trading_days: int,
    max_staleness_days: int,
    as_of_date: date | None,
) -> None:
    con = duckdb.connect(db_path)
    try:
        tables = [
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        ]

        daily_bars_exists = "daily_bars" in tables
        output["foundation"]["table_checks"]["daily_bars"] = {
            "exists": daily_bars_exists,
        }

        if not daily_bars_exists:
            output["ok"] = False
            output["errors"].append("Table 'daily_bars' not found in foundation DB")
            return

        row_count = con.execute("SELECT COUNT(*) FROM daily_bars").fetchone()[0]
        symbol_count = con.execute(
            "SELECT COUNT(DISTINCT symbol) FROM daily_bars"
        ).fetchone()[0]
        date_min, date_max = con.execute(
            "SELECT MIN(date), MAX(date) FROM daily_bars"
        ).fetchone()

        output["foundation"]["table_checks"]["daily_bars"].update(
            {
                "row_count": row_count,
                "symbol_count": symbol_count,
                "date_min": str(date_min) if date_min is not None else None,
                "date_max": str(date_max) if date_max is not None else None,
            }
        )

        columns = _get_columns(con, "daily_bars")
        for col in REQUIRED_FOUNDATION_COLUMNS:
            found = col in columns
            output["foundation"]["column_checks"][col] = found
            if not found:
                output["foundation"]["missing_required_columns"].append(col)
                output["ok"] = False
                output["errors"].append(
                    f"Missing required column '{col}' in daily_bars"
                )

        if symbol_count < min_symbols:
            output["foundation"]["warnings"].append(
                f"daily_bars symbol_count ({symbol_count}) below {min_symbols} threshold"
            )

        if date_min is not None and date_max is not None:
            try:
                dmin = date.fromisoformat(str(date_min))
                dmax = date.fromisoformat(str(date_max))
                span_days = (dmax - dmin).days + 1
                if span_days < min_trading_days:
                    output["foundation"]["warnings"].append(
                        f"daily_bars date span ({span_days} days) below {min_trading_days} threshold"
                    )
            except Exception:
                pass

        # Type checks
        col_types = _get_column_types(con, "daily_bars")
        _check_types(con, "daily_bars", col_types, output, "foundation")

        # Uniqueness
        _check_uniqueness(con, "daily_bars", output, "foundation")

        # Null / range
        _check_null_range(con, "daily_bars", output, "foundation")

        # Trading day coverage
        _check_trading_day_coverage(con, "daily_bars", min_trading_days, output, "foundation")

        # Freshness
        _check_freshness(con, "daily_bars", as_of_date, max_staleness_days, output, "foundation")

        # Metadata
        _check_metadata(con, db_path, output, "foundation")

    finally:
        con.close()


def _validate_state_cube(
    db_path: str,
    output: dict,
    min_symbols: int,
    min_trading_days: int,
    max_staleness_days: int,
    as_of_date: date | None,
) -> None:
    con = duckdb.connect(db_path)
    try:
        tables = [
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        ]

        state_cube_exists = "state_cube" in tables
        output["state_cube"]["table_checks"]["state_cube"] = {
            "exists": state_cube_exists,
        }

        if not state_cube_exists:
            output["ok"] = False
            output["errors"].append("Table 'state_cube' not found in state cube DB")
            return

        row_count = con.execute("SELECT COUNT(*) FROM state_cube").fetchone()[0]
        symbol_count = con.execute(
            "SELECT COUNT(DISTINCT symbol) FROM state_cube"
        ).fetchone()[0]
        date_min, date_max = con.execute(
            "SELECT MIN(date), MAX(date) FROM state_cube"
        ).fetchone()

        output["state_cube"]["table_checks"]["state_cube"].update(
            {
                "row_count": row_count,
                "symbol_count": symbol_count,
                "date_min": str(date_min) if date_min is not None else None,
                "date_max": str(date_max) if date_max is not None else None,
            }
        )

        columns = _get_columns(con, "state_cube")
        for col in REQUIRED_STATE_CUBE_COLUMNS:
            found = col in columns
            output["state_cube"]["column_checks"][col] = found
            if not found:
                output["state_cube"]["missing_required_columns"].append(col)
                output["ok"] = False
                output["errors"].append(
                    f"Missing required column '{col}' in state_cube"
                )

        if symbol_count < min_symbols:
            output["state_cube"]["warnings"].append(
                f"state_cube symbol_count ({symbol_count}) below {min_symbols} threshold"
            )

        # Alias checks
        _check_alias(con, "state_cube", output, "state_cube")

        # Uniqueness
        _check_uniqueness(con, "state_cube", output, "state_cube")

        # Null / range (light version: just null rates for state fields)
        _check_null_range(con, "state_cube", output, "state_cube")

        # Trading day coverage
        _check_trading_day_coverage(con, "state_cube", min_trading_days, output, "state_cube")

        # Freshness
        _check_freshness(con, "state_cube", as_of_date, max_staleness_days, output, "state_cube")

        # Metadata
        _check_metadata(con, db_path, output, "state_cube")

        idx_map = _get_indexes(con, "state_cube")
        has_date_idx = False
        has_symbol_idx = False
        date_idx_cols: list[str] = []
        symbol_idx_cols: list[str] = []

        for idx_name, cols in idx_map.items():
            if idx_name == "__error__":
                output["state_cube"]["warnings"].append(
                    f"Could not enumerate indexes: {cols[0]}"
                )
                continue
            if "date" in cols:
                has_date_idx = True
                date_idx_cols = cols
            if "symbol" in cols:
                has_symbol_idx = True
                symbol_idx_cols = cols

        output["state_cube"]["index_checks"]["idx_state_cube_date"] = {
            "exists": has_date_idx,
            "columns": date_idx_cols,
        }
        output["state_cube"]["index_checks"]["idx_state_cube_symbol"] = {
            "exists": has_symbol_idx,
            "columns": symbol_idx_cols,
        }

        if not has_date_idx:
            output["state_cube"]["warnings"].append(
                "Missing index on state_cube(date)"
            )
        if not has_symbol_idx:
            output["state_cube"]["warnings"].append(
                "Missing index on state_cube(symbol)"
            )
    finally:
        con.close()


def main() -> None:
    args = parse_args()

    as_of_date: date | None = None
    if args.as_of_date:
        as_of_date = date.fromisoformat(args.as_of_date)

    output: dict = {
        "ok": True,
        "foundation_db": args.foundation_db,
        "state_cube_db": args.state_cube_db,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "parameters": {
            "min_symbols": args.min_symbols,
            "min_trading_days": args.min_trading_days,
            "max_staleness_days": args.max_staleness_days,
            "as_of_date": args.as_of_date,
        },
        "foundation": {
            "table_checks": {},
            "column_checks": {},
            "missing_required_columns": [],
            "index_checks": {},
            "warnings": [],
        },
        "state_cube": {
            "table_checks": {},
            "column_checks": {},
            "missing_required_columns": [],
            "index_checks": {},
            "warnings": [],
        },
        "errors": [],
    }

    if _check_db_exists(args.foundation_db, "Foundation", output):
        _validate_foundation(
            args.foundation_db,
            output,
            args.min_symbols,
            args.min_trading_days,
            args.max_staleness_days,
            as_of_date,
        )

    if _check_db_exists(args.state_cube_db, "State Cube", output):
        _validate_state_cube(
            args.state_cube_db,
            output,
            args.min_symbols,
            args.min_trading_days,
            args.max_staleness_days,
            as_of_date,
        )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total_warnings = len(output["foundation"]["warnings"]) + len(
        output["state_cube"]["warnings"]
    )
    print(
        f"Validation result written to {args.output}  "
        f"ok={output['ok']} errors={len(output['errors'])} warnings={total_warnings}"
    )
    sys.exit(0 if output["ok"] else 1)


if __name__ == "__main__":
    main()
