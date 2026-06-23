#!/usr/bin/env python3
"""Run Strategy Lab REAL DATA E2E acceptance samples.

This is the project-level executable check for the real-data path:
Chinese NL -> DSL v2 -> validation/red lines -> preview -> light_real_v1 backtest -> audit.

Unlike the MVP acceptance script, this script explicitly requires
`data/p116_foundation.duckdb` and `data/state_cube.duckdb` and asserts
`backtest_mode == "light_real_v1"`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hermass_platform.strategy_lab.e2e_runner import run_mvp_e2e_sample  # noqa: E402


VALID_SAMPLES = [
    {
        "sample_id": "sample_ma_5_20_stop_8",
        "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
        "expected_entry": ["ma_golden_cross"],
        "expected_exit": ["price_cross_ma", "stop_loss_pct"],
    },
    {
        "sample_id": "sample_state_volume_stop_8_take_15",
        "natural_language": (
            "D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，"
            "止损8%，止盈15%"
        ),
        "expected_entry": ["state_hex_in", "volume_ratio"],
        "expected_exit": ["stop_loss_pct", "take_profit_pct"],
    },
    {
        "sample_id": "sample_ma_state_limit_filter",
        "natural_language": (
            "MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，"
            "跌破MA10或止损8%卖出"
        ),
        "expected_entry": ["ma_golden_cross", "state_ef_count"],
        "expected_exit": ["price_cross_ma", "stop_loss_pct"],
    },
]


def _resolve_repo_path(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Hermass Strategy Lab REAL DATA E2E acceptance samples."
    )
    parser.add_argument(
        "--output",
        default="outputs/strategy_lab/real_e2e_acceptance_latest.json",
        help="JSON summary output path.",
    )
    parser.add_argument(
        "--audit-db",
        default="outputs/strategy_lab/real_e2e_acceptance_audit.duckdb",
        help="DuckDB audit evidence path.",
    )
    parser.add_argument(
        "--storage-db",
        default="outputs/strategy_lab/real_e2e_acceptance_storage.duckdb",
        help="DuckDB strategy/backtest storage evidence path.",
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
    parser.add_argument(
        "--universe",
        default=None,
        help="Optional comma-separated symbol universe (default: full universe).",
    )
    parser.add_argument(
        "--run-id",
        default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        help="Run identifier embedded in trace_id values.",
    )
    args = parser.parse_args()

    foundation_db_path = _resolve_repo_path(args.foundation_db)
    state_cube_db_path = _resolve_repo_path(args.state_cube_db)

    missing: list[str] = []
    if not foundation_db_path.exists():
        missing.append(str(foundation_db_path))
    if not state_cube_db_path.exists():
        missing.append(str(state_cube_db_path))
    if missing:
        print("ERROR: required real-data databases not found:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 2

    output_path = _resolve_repo_path(args.output)
    audit_db_path = _resolve_repo_path(args.audit_db)
    storage_db_path = _resolve_repo_path(args.storage_db)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_db_path.parent.mkdir(parents=True, exist_ok=True)
    storage_db_path.parent.mkdir(parents=True, exist_ok=True)

    universe: list[str] | None = None
    if args.universe:
        universe = [s.strip() for s in args.universe.split(",") if s.strip()]

    records: list[dict[str, Any]] = []
    all_passed = True
    for sample in VALID_SAMPLES:
        trace_id = f"real-acceptance-{args.run_id}-{sample['sample_id']}"
        result = run_mvp_e2e_sample(
            sample["natural_language"],
            sample["sample_id"],
            trace_id=trace_id,
            audit_db_path=str(audit_db_path),
            storage_db_path=str(storage_db_path),
            preview_data_source="mock",
            start_date=args.start_date,
            end_date=args.end_date,
            foundation_db=str(foundation_db_path),
            state_cube_db=str(state_cube_db_path),
            universe=universe,
        )

        record = _build_record(sample, result)
        records.append(record)
        if not record["passed"]:
            all_passed = False

    summary = {
        "run_id": args.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "foundation_db": str(foundation_db_path),
        "state_cube_db": str(state_cube_db_path),
        "audit_db_path": str(audit_db_path),
        "storage_db_path": str(storage_db_path),
        "start_date": args.start_date,
        "end_date": args.end_date,
        "universe": universe,
        "total_cases": len(records),
        "passed_cases": sum(1 for r in records if r["passed"]),
        "failed_cases": [r["sample_id"] for r in records if not r["passed"]],
        "records": records,
    }
    summary["passed"] = all_passed

    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if all_passed else 1


def _build_record(sample: dict[str, Any], result: Any) -> dict[str, Any]:
    """Build acceptance record with real-mode specific checks."""
    metrics = result.backtest.metrics.model_dump() if result.backtest else None
    backtest_mode = result.backtest_mode if result.backtest else None
    backtest_status = result.backtest.status if result.backtest else None
    audit_operations = [record["operation"] for record in result.audit_records]

    # Core checks for real-data acceptance
    checks: dict[str, Any] = {
        "status_success_or_partial": result.status in ("success", "partial"),
        "stage_reached_complete": result.stage_reached == "complete",
        "validation_passed": result.validation.passed if result.validation else False,
        "red_line_passed": result.red_line_result.get("passed", False),
        "preview_status_ok": (
            result.preview is not None
            and result.preview.overall.overall_status in ("ok", "partial")
        ),
        "backtest_mode_is_light_real_v1": backtest_mode == "light_real_v1",
        "backtest_status_success_or_partial": backtest_status in ("success", "partial"),
        "metrics_present": bool(metrics) and metrics.get("total_return") is not None,
        "audit_has_generation": "generation" in audit_operations,
        "audit_has_validation": "validation" in audit_operations,
        "audit_has_preview": "preview" in audit_operations,
        "audit_has_backtest": "backtest" in audit_operations,
    }

    record_passed = all(checks.values())

    return {
        "sample_id": sample["sample_id"],
        "trace_id": result.trace_id,
        "natural_language": sample["natural_language"],
        "status": result.status,
        "stage_reached": result.stage_reached,
        "validation_passed": result.validation.passed if result.validation else None,
        "red_line_result": result.red_line_result,
        "preview_status": result.preview.overall.overall_status if result.preview else None,
        "preview_total_estimated_hits": (
            result.preview.overall.total_estimated_hits if result.preview else None
        ),
        "backtest_status": backtest_status,
        "backtest_mode": backtest_mode,
        "backtest_metrics": metrics,
        "audit_operations": audit_operations,
        "problem_count": len(result.problem_items),
        "problems": result.problem_items,
        "checks": checks,
        "passed": record_passed,
    }


if __name__ == "__main__":
    sys.exit(main())
