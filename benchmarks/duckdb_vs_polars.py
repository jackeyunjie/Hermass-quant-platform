#!/usr/bin/env python3
"""Benchmark: DuckDB-only vs DuckDB + Polars for simple signal generation.

DuckDB-only covers a simple MA golden cross signal in SQL.
DuckDB+Polars loads data via DuckDB and computes the signal with Polars.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb
import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
from _synthetic import create_synthetic_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DuckDB vs Polars Signal Generation Benchmark"
    )
    parser.add_argument("--db-path", type=str, default="data/p116_foundation.duckdb")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--repeats", type=int, default=5)
    return parser.parse_args()


def benchmark_mode(
    universe_n: int,
    mode: str,
    db_path: str,
    repeats: int,
    is_synthetic: bool,
) -> list[dict]:
    con = duckdb.connect(db_path)
    times = []
    try:
        for run_index in range(repeats):
            t0 = time.perf_counter()
            if mode == "duckdb_only":
                _ = con.execute(
                    f"""
                    WITH signals AS (
                        SELECT symbol, date,
                               (ma_5 > ma_20 AND
                                LAG(ma_5) OVER w <= LAG(ma_20) OVER w
                               )::INTEGER AS entry
                        FROM daily_bars
                        WHERE symbol IN (
                            SELECT DISTINCT symbol FROM daily_bars LIMIT {universe_n}
                        )
                        WINDOW w AS (PARTITION BY symbol ORDER BY date)
                    )
                    SELECT * FROM signals WHERE entry = 1
                    """
                ).pl()
            else:  # duckdb_load_polars
                df = con.execute(
                    f"""
                    SELECT symbol, date, ma_5, ma_20
                    FROM daily_bars
                    WHERE symbol IN (
                        SELECT DISTINCT symbol FROM daily_bars LIMIT {universe_n}
                    )
                    """
                ).pl()
                entry_expr = (
                    (pl.col("ma_5") > pl.col("ma_20"))
                    & (
                        pl.col("ma_5").shift(1).over("symbol")
                        <= pl.col("ma_20").shift(1).over("symbol")
                    )
                )
                result = df.with_columns(entry_expr.alias("entry")).filter(
                    pl.col("entry")
                )
                _ = result.shape
            t1 = time.perf_counter()
            times.append(t1 - t0)
    finally:
        con.close()

    times_sorted = sorted(times)
    p50 = statistics.median(times)
    p95 = (
        times_sorted[int(len(times_sorted) * 0.95)]
        if len(times_sorted) > 1
        else times_sorted[0]
    )

    records = []
    for run_index, elapsed in enumerate(times):
        records.append(
            {
                "benchmark_name": "duckdb_vs_polars",
                "mode": mode,
                "universe_n": universe_n,
                "days": 252,
                "run_index": run_index,
                "elapsed_s": round(elapsed, 6),
                "p50_s": round(p50, 6),
                "p95_s": round(p95, 6),
                "data_source": "synthetic" if is_synthetic else "real",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "notes": "",
            }
        )
    return records


def main() -> None:
    args = parse_args()
    db_path = args.db_path
    if args.synthetic:
        db_path = create_synthetic_db(symbols=5000, days=252)

    output_path = (
        args.output
        or f"outputs/benchmarks/duckdb_vs_polars_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    for universe_n in [500, 2000, 5000]:
        for mode in ["duckdb_only", "duckdb_load_polars"]:
            records = benchmark_mode(
                universe_n,
                mode,
                db_path,
                args.repeats,
                args.synthetic,
            )
            all_records.extend(records)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(all_records)} records to {output_path}")


if __name__ == "__main__":
    main()
