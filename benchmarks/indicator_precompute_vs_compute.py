#!/usr/bin/env python3
"""Benchmark: Indicator precomputed vs computed on the fly.

Compares reading a precomputed `ma_20` column vs computing it via
DuckDB window function.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = args.db_path
    if args.synthetic:
        db_path = create_synthetic_db(symbols=5000, days=252)

    con = duckdb.connect(db_path)
    try:
        rows = con.execute("SELECT COUNT(*) FROM daily_bars").fetchone()[0]
        symbols = con.execute(
            "SELECT COUNT(DISTINCT symbol) FROM daily_bars"
        ).fetchone()[0]
        days = rows // symbols if symbols else 0

        # Compute ma_20 via window function
        import time

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
        elapsed_compute = time.perf_counter() - t0

        # Read precomputed ma_20
        t0 = time.perf_counter()
        _ = con.execute("""
            SELECT symbol, date, ma_20 FROM daily_bars
        """).pl()
        elapsed_read = time.perf_counter() - t0
    finally:
        con.close()

    ratio = elapsed_compute / elapsed_read if elapsed_read > 0 else None

    output_path = (
        args.output
        or f"outputs/benchmarks/indicator_precompute_vs_compute_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    records = [
        {
            "benchmark_name": "indicator_precompute_vs_compute",
            "mode": "compute_window",
            "universe_n": symbols,
            "days": days,
            "run_index": 0,
            "elapsed_s": round(elapsed_compute, 6),
            "p50_s": round(elapsed_compute, 6),
            "p95_s": round(elapsed_compute, 6),
            "data_source": "synthetic" if args.synthetic else "real",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "notes": f"total_rows={rows}",
        },
        {
            "benchmark_name": "indicator_precompute_vs_compute",
            "mode": "read_precomputed",
            "universe_n": symbols,
            "days": days,
            "run_index": 0,
            "elapsed_s": round(elapsed_read, 6),
            "p50_s": round(elapsed_read, 6),
            "p95_s": round(elapsed_read, 6),
            "data_source": "synthetic" if args.synthetic else "real",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "notes": f"total_rows={rows}, ratio_compute_vs_read={ratio}",
        },
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {output_path}")


if __name__ == "__main__":
    main()
