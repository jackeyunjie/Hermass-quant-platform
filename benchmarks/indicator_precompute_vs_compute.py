#!/usr/bin/env python3
"""Benchmark: Indicator precomputed vs computed on the fly.

Compares reading a precomputed `ma_20` column vs computing it via
DuckDB window function.
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

sys.path.insert(0, str(Path(__file__).parent))
from _synthetic import create_synthetic_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Indicator Precompute vs Compute Benchmark"
    )
    parser.add_argument("--db-path", type=str, default="data/p116_foundation.duckdb")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--runs", type=int, default=5, help="Repeat runs")
    parser.add_argument(
        "--symbols", type=str, default="5000", help="Symbol count for synthetic data"
    )
    parser.add_argument("--days", type=int, default=252, help="Days for synthetic data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = args.db_path
    symbols = int(args.symbols.split(",")[0].strip())
    if args.synthetic:
        db_path = create_synthetic_db(symbols=symbols, days=args.days)

    con = duckdb.connect(db_path)
    try:
        rows = con.execute("SELECT COUNT(*) FROM daily_bars").fetchone()[0]
        symbol_count = con.execute(
            "SELECT COUNT(DISTINCT symbol) FROM daily_bars"
        ).fetchone()[0]
        days = rows // symbol_count if symbol_count else 0
    finally:
        con.close()

    compute_times: list[float] = []
    read_times: list[float] = []

    for _ in range(args.runs):
        con = duckdb.connect(db_path)
        try:
            t0 = time.perf_counter()
            _ = con.execute("""
                SELECT symbol, date,
                       AVG(close) OVER (
                           PARTITION BY symbol
                           ORDER BY date
                           ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                       ) AS ma_20
                FROM daily_bars
            """).pl()
            compute_times.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            _ = con.execute("""
                SELECT symbol, date, ma_20 FROM daily_bars
            """).pl()
            read_times.append(time.perf_counter() - t0)
        finally:
            con.close()

    compute_p50 = statistics.median(compute_times)
    compute_p95 = sorted(compute_times)[int(len(compute_times) * 0.95)] if len(compute_times) > 1 else compute_times[0]
    read_p50 = statistics.median(read_times)
    read_p95 = sorted(read_times)[int(len(read_times) * 0.95)] if len(read_times) > 1 else read_times[0]

    ratio = compute_times[0] / read_times[0] if read_times[0] > 0 else None

    output_path = (
        args.output
        or f"outputs/benchmarks/indicator_precompute_vs_compute_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    records = []
    for run_index in range(args.runs):
        records.append(
            {
                "benchmark_name": "indicator_precompute_vs_compute",
                "mode": "compute_window",
                "universe_n": symbol_count,
                "days": days,
                "run_index": run_index,
                "elapsed_s": round(compute_times[run_index], 6),
                "p50_s": round(compute_p50, 6),
                "p95_s": round(compute_p95, 6),
                "data_source": "synthetic" if args.synthetic else "real",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "notes": f"total_rows={rows}",
            }
        )
        records.append(
            {
                "benchmark_name": "indicator_precompute_vs_compute",
                "mode": "read_precomputed",
                "universe_n": symbol_count,
                "days": days,
                "run_index": run_index,
                "elapsed_s": round(read_times[run_index], 6),
                "p50_s": round(read_p50, 6),
                "p95_s": round(read_p95, 6),
                "data_source": "synthetic" if args.synthetic else "real",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "notes": f"total_rows={rows}, ratio_compute_vs_read={ratio}",
            }
        )

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {output_path}")


if __name__ == "__main__":
    main()
