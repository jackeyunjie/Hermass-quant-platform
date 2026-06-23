#!/usr/bin/env python3
"""DSL end-to-end performance breakdown.

Profiles `run_mvp_e2e_sample` stage-by-stage for the 3 frozen real-data
samples with full universe. Compares against the pure engine benchmark
(`light_backtest_perf.py`) to explain the 12x gap observed in M3 pilot prep.

Outputs JSON to `outputs/benchmarks/dsl_e2e_breakdown_YYYYMMDD_HHMMSS.json`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermass_platform.strategy_lab.e2e_runner import run_mvp_e2e_sample


VALID_SAMPLES = [
    {
        "sample_id": "sample_ma_5_20_stop_8",
        "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
    },
    {
        "sample_id": "sample_state_volume_stop_8_take_15",
        "natural_language": (
            "D1状态属于trending_up或bottoming，成交量放大到20日均量1.5倍以上买入，"
            "止损8%，止盈15%"
        ),
    },
    {
        "sample_id": "sample_ma_state_limit_filter",
        "natural_language": (
            "MA5上穿MA20且D1状态属于trending_up时买入，排除涨停股票，"
            "跌破MA10或止损8%卖出"
        ),
    },
]


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def main() -> int:
    parser = argparse.ArgumentParser(description="DSL E2E performance breakdown")
    parser.add_argument(
        "--output",
        default=None,
        help="JSON output path (default: outputs/benchmarks/dsl_e2e_breakdown_*.json)",
    )
    parser.add_argument(
        "--foundation-db",
        default="data/p116_foundation.duckdb",
        help="Path to p116_foundation.duckdb.",
    )
    parser.add_argument(
        "--state-cube-db",
        default="data/state_cube.duckdb",
        help="Path to state_cube.duckdb.",
    )
    parser.add_argument(
        "--start-date",
        default="2023-01-01",
        help="Backtest start date.",
    )
    parser.add_argument(
        "--end-date",
        default="2024-12-31",
        help="Backtest end date.",
    )
    args = parser.parse_args()

    foundation_db_path = _resolve(args.foundation_db)
    state_cube_db_path = _resolve(args.state_cube_db)

    if not foundation_db_path.exists() or not state_cube_db_path.exists():
        print("ERROR: required real-data databases not found", file=sys.stderr)
        print(f"  foundation: {foundation_db_path}", file=sys.stderr)
        print(f"  state_cube: {state_cube_db_path}", file=sys.stderr)
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = REPO_ROOT / "outputs" / "benchmarks"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = _resolve(args.output) if args.output else (
        output_dir / f"dsl_e2e_breakdown_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )

    audit_db = output_dir / f"dsl_e2e_breakdown_audit_{run_id}.duckdb"
    storage_db = output_dir / f"dsl_e2e_breakdown_storage_{run_id}.duckdb"

    records: list[dict[str, Any]] = []
    for sample in VALID_SAMPLES:
        trace_id = f"dsl-perf-{run_id}-{sample['sample_id']}"
        result = run_mvp_e2e_sample(
            sample["natural_language"],
            sample["sample_id"],
            trace_id=trace_id,
            audit_db_path=str(audit_db),
            storage_db_path=str(storage_db),
            preview_data_source="mock",
            start_date=args.start_date,
            end_date=args.end_date,
            foundation_db=str(foundation_db_path),
            state_cube_db=str(state_cube_db_path),
            universe=None,
            profile=True,
        )

        record = {
            "sample_id": sample["sample_id"],
            "natural_language": sample["natural_language"],
            "status": result.status,
            "stage_reached": result.stage_reached,
            "backtest_mode": result.backtest_mode,
            "stage_timings": result.stage_timings,
            "backtest_elapsed_seconds": result.backtest.elapsed_seconds if result.backtest else None,
        }
        records.append(record)
        print(f"{sample['sample_id']}: total={result.stage_timings.get('total', 0):.3f}s, "
              f"mode={result.backtest_mode}")

    summary = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "foundation_db": str(foundation_db_path),
        "state_cube_db": str(state_cube_db_path),
        "records": records,
    }

    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"\nReport written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
