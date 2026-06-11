#!/usr/bin/env python3
"""Run Strategy Lab MVP E2E acceptance samples.

This is the project-level executable check for:
Chinese NL -> DSL v2 -> validation/red lines -> preview -> light backtest -> audit.
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

FAILURE_SAMPLES = [
    {
        "sample_id": "missing_stop_loss",
        "natural_language": "MA5上穿MA20买入，跌破MA10卖出",
        "expected_red_line": "RL_EXIT_MUST_HAVE_STOP_LOSS",
    },
    {
        "sample_id": "over_position",
        "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%，仓位30%",
        "expected_red_line": "RL_MAX_POSITION",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Hermass Strategy Lab MVP E2E acceptance samples."
    )
    parser.add_argument(
        "--output",
        default="outputs/strategy_lab/mvp_e2e_acceptance_latest.json",
        help="JSON summary output path.",
    )
    parser.add_argument(
        "--audit-db",
        default="outputs/strategy_lab/mvp_e2e_acceptance_audit.duckdb",
        help="DuckDB audit evidence path.",
    )
    parser.add_argument(
        "--storage-db",
        default="outputs/strategy_lab/mvp_e2e_acceptance_storage.duckdb",
        help="DuckDB strategy/backtest storage evidence path.",
    )
    parser.add_argument(
        "--run-id",
        default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        help="Run identifier embedded in trace_id values.",
    )
    args = parser.parse_args()

    output_path = _resolve_repo_path(args.output)
    audit_db_path = _resolve_repo_path(args.audit_db)
    storage_db_path = _resolve_repo_path(args.storage_db)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_db_path.parent.mkdir(parents=True, exist_ok=True)
    storage_db_path.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for sample in VALID_SAMPLES:
        records.append(
            _run_case(
                sample,
                args.run_id,
                str(audit_db_path),
                str(storage_db_path),
                expected_success=True,
            )
        )

    for sample in FAILURE_SAMPLES:
        records.append(
            _run_case(
                sample,
                args.run_id,
                str(audit_db_path),
                str(storage_db_path),
                expected_success=False,
            )
        )

    summary = {
        "run_id": args.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_db_path": str(audit_db_path),
        "storage_db_path": str(storage_db_path),
        "total_cases": len(records),
        "passed_cases": sum(1 for record in records if record["passed"]),
        "failed_cases": [record["sample_id"] for record in records if not record["passed"]],
        "records": records,
    }
    summary["passed"] = summary["passed_cases"] == summary["total_cases"]

    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


def _run_case(
    sample: dict[str, Any],
    run_id: str,
    audit_db_path: str,
    storage_db_path: str,
    *,
    expected_success: bool,
) -> dict[str, Any]:
    trace_id = f"acceptance-{run_id}-{sample['sample_id']}"
    result = run_mvp_e2e_sample(
        sample["natural_language"],
        sample["sample_id"],
        trace_id=trace_id,
        audit_db_path=audit_db_path,
        storage_db_path=storage_db_path,
    )

    audit_operations = [record["operation"] for record in result.audit_records]
    triggered_rules = list(result.red_line_result.get("triggered_rules", []))
    entry_types = [condition.condition_type for condition in result.dsl.entry] if result.dsl else []
    exit_types = [condition.condition_type for condition in result.dsl.exit] if result.dsl else []
    metrics = result.backtest.metrics.model_dump() if result.backtest else None

    checks = _build_checks(
        sample=sample,
        expected_success=expected_success,
        status=result.status,
        stage_reached=result.stage_reached,
        validation_passed=result.validation.passed if result.validation else None,
        red_line_passed=result.red_line_result.get("passed"),
        preview_status=result.preview.overall.overall_status if result.preview else None,
        backtest_status=result.backtest.status if result.backtest else None,
        backtest_mode=result.backtest_mode,
        audit_operations=audit_operations,
        triggered_rules=triggered_rules,
        entry_types=entry_types,
        exit_types=exit_types,
        metrics=metrics,
    )

    return {
        "sample_id": sample["sample_id"],
        "trace_id": trace_id,
        "status": result.status,
        "stage_reached": result.stage_reached,
        "validation_passed": result.validation.passed if result.validation else None,
        "red_line_result": result.red_line_result,
        "entry_types": entry_types,
        "exit_types": exit_types,
        "preview_status": result.preview.overall.overall_status if result.preview else None,
        "preview_total_estimated_hits": (
            result.preview.overall.total_estimated_hits if result.preview else None
        ),
        "backtest_status": result.backtest.status if result.backtest else None,
        "backtest_mode": result.backtest_mode if result.backtest else None,
        "backtest_metrics": metrics,
        "audit_operations": audit_operations,
        "problem_count": len(result.problem_items),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _build_checks(
    *,
    sample: dict[str, Any],
    expected_success: bool,
    status: str,
    stage_reached: str,
    validation_passed: bool | None,
    red_line_passed: bool | None,
    preview_status: str | None,
    backtest_status: str | None,
    backtest_mode: str,
    audit_operations: list[str],
    triggered_rules: list[str],
    entry_types: list[str],
    exit_types: list[str],
    metrics: dict[str, Any] | None,
) -> dict[str, bool]:
    if expected_success:
        return {
            "status_is_partial_or_success": status in {"partial", "success"},
            "stage_reached_complete": stage_reached == "complete",
            "validation_passed": validation_passed is True,
            "red_line_passed": red_line_passed is True,
            "preview_ran": preview_status in {"partial", "success"},
            "backtest_ran_as_stub": backtest_status in {"partial", "success"}
            and backtest_mode == "light_stub",
            "audit_order": audit_operations
            == ["generation", "validation", "preview", "backtest"],
            "entry_types_match": entry_types == sample["expected_entry"],
            "exit_types_match": exit_types == sample["expected_exit"],
            "core_metrics_present": _has_core_metrics(metrics),
        }

    return {
        "status_failed": status == "failed",
        "stage_reached_validation": stage_reached == "validation",
        "validation_failed": validation_passed is False,
        "red_line_failed": red_line_passed is False,
        "expected_red_line_triggered": sample["expected_red_line"] in triggered_rules,
        "audit_order": audit_operations == ["generation", "validation"],
        "preview_skipped": preview_status is None,
        "backtest_skipped": backtest_status is None,
    }


def _has_core_metrics(metrics: dict[str, Any] | None) -> bool:
    if metrics is None:
        return False
    required = {
        "total_return",
        "annual_return",
        "max_drawdown",
        "sharpe_ratio",
        "win_rate",
        "profit_factor",
        "trade_count",
    }
    return required.issubset(metrics)


def _resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


if __name__ == "__main__":
    raise SystemExit(main())
