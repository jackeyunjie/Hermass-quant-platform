#!/usr/bin/env python3
"""Validate real DuckDB data before running benchmarks.

Checks foundation DB and state cube DB for required tables, columns,
row counts, date ranges, and indexes.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import date, datetime
from pathlib import Path

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
            # expressions comes as a string like "[a, b]" or "[date]"
            cols = []
            if expressions and isinstance(expressions, str):
                inner = expressions.strip().strip("[]")
                if inner:
                    cols = [c.strip().strip('"').strip("'") for c in inner.split(",")]
            idx_map[idx_name] = cols
    except Exception as e:
        # DuckDB older versions may not support duckdb_indexes()
        idx_map["__error__"] = [str(e)]
    return idx_map


def _validate_foundation(db_path: str, output: dict) -> None:
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

        if row_count < 1_000_000:
            output["foundation"]["warnings"].append(
                f"daily_bars row_count ({row_count}) below 1,000,000 threshold"
            )
        if symbol_count < 5000:
            output["foundation"]["warnings"].append(
                f"daily_bars symbol_count ({symbol_count}) below 5,000 threshold"
            )

        if date_min is not None and date_max is not None:
            try:
                dmin = date.fromisoformat(str(date_min))
                dmax = date.fromisoformat(str(date_max))
                span_days = (dmax - dmin).days + 1
                if span_days < 240:
                    output["foundation"]["warnings"].append(
                        f"daily_bars date span ({span_days} days) below 240 threshold"
                    )
            except Exception:
                pass
    finally:
        con.close()


def _validate_state_cube(db_path: str, output: dict) -> None:
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

        if row_count < 1_000_000:
            output["state_cube"]["warnings"].append(
                f"state_cube row_count ({row_count}) below 1,000,000 threshold"
            )
        if symbol_count < 5000:
            output["state_cube"]["warnings"].append(
                f"state_cube symbol_count ({symbol_count}) below 5,000 threshold"
            )

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

    output: dict = {
        "ok": True,
        "foundation_db": args.foundation_db,
        "state_cube_db": args.state_cube_db,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
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
        _validate_foundation(args.foundation_db, output)

    if _check_db_exists(args.state_cube_db, "State Cube", output):
        _validate_state_cube(args.state_cube_db, output)

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
