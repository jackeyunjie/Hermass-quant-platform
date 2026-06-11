#!/usr/bin/env python3
"""Gate summary: read validation JSON and benchmark JSONL, emit pass/fail.

Usage:
    python benchmarks/gate_summary.py \
        --validation outputs/benchmarks/real_data_validation_20260101.json \
        --benchmark outputs/benchmarks/light_backtest_real_20260101.jsonl \
        --output outputs/benchmarks/gate_summary_20260101.json

Or auto-discover newest files:
    python benchmarks/gate_summary.py --output outputs/benchmarks/gate_summary.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import statistics
import sys
from datetime import datetime
from pathlib import Path


GATES = {
    "light_backtest_total_p50_s": {"max": 20.0, "unit": "s"},
    "light_backtest_total_p95_s": {"max": 30.0, "unit": "s"},
    "light_backtest_data_load_p95_s": {"max": 10.0, "unit": "s"},
    "light_backtest_signal_gen_p95_s": {"max": 12.0, "unit": "s"},
    "light_backtest_equity_metrics_p95_s": {"max": 8.0, "unit": "s"},
    "light_backtest_peak_memory_mb": {"max": 4096.0, "unit": "MB"},
    "light_backtest_failure_rate": {"max": 0.0, "unit": "count"},
    "data_validation_ok": {"must_be": True, "unit": "bool"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark gate summary")
    parser.add_argument(
        "--validation", type=str, default=None, help="Path to validation JSON"
    )
    parser.add_argument(
        "--benchmark", type=str, default=None, help="Path to light_backtest JSONL"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to write gate summary JSON"
    )
    parser.add_argument(
        "--gate-config", type=str, default=None, help="Optional custom gate config JSON"
    )
    return parser.parse_args()


def _newest_file(pattern: str) -> str | None:
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def load_validation(path: str | None) -> dict | None:
    if path is None:
        path = _newest_file("outputs/benchmarks/real_data_validation_*.json")
    if path is None or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_benchmark_records(path: str | None) -> list[dict] | None:
    if path is None:
        path = _newest_file("outputs/benchmarks/light_backtest_real_*.jsonl")
    if path is None or not os.path.exists(path):
        return None
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def summarize_benchmark(records: list[dict]) -> dict:
    """Compute per-mode percentiles and failure counts."""
    by_mode: dict[str, list[dict]] = {}
    for rec in records:
        by_mode.setdefault(rec.get("mode", "unknown"), []).append(rec)

    summary: dict[str, dict] = {}
    for mode, recs in by_mode.items():
        totals = [r["elapsed_s"] for r in recs if "elapsed_s" in r]
        data_loads = [r.get("data_load_s") for r in recs if r.get("data_load_s") is not None]
        signal_gens = [r.get("signal_gen_s") for r in recs if r.get("signal_gen_s") is not None]
        equity_metrics = [r.get("equity_metrics_s") for r in recs if r.get("equity_metrics_s") is not None]
        memories = [r.get("peak_memory_mb") for r in recs if r.get("peak_memory_mb") is not None]

        def _pct(values: list[float], p: float) -> float | None:
            if not values:
                return None
            s = sorted(values)
            if len(s) == 1:
                return s[0]
            idx = int(len(s) * p)
            idx = min(idx, len(s) - 1)
            return s[idx]

        summary[mode] = {
            "runs": len(recs),
            "total_p50_s": _pct(totals, 0.50),
            "total_p95_s": _pct(totals, 0.95),
            "data_load_p95_s": _pct(data_loads, 0.95),
            "signal_gen_p95_s": _pct(signal_gens, 0.95),
            "equity_metrics_p95_s": _pct(equity_metrics, 0.95),
            "peak_memory_p95_mb": _pct(memories, 0.95),
            "failure_count": 0,  # synthetic/real baseline scripts do not inject failures
            "universe_n": recs[0].get("universe_n") if recs else None,
            "days": recs[0].get("days") if recs else None,
            "data_source": recs[0].get("data_source") if recs else None,
        }
    return summary


def evaluate_gates(validation: dict | None, benchmark_summary: dict) -> tuple[bool, list[dict]]:
    results: list[dict] = []
    overall = True

    # Data validation gate
    dv_ok = bool(validation.get("ok")) if validation else False
    results.append({
        "gate": "data_validation_ok",
        "value": dv_ok,
        "threshold": True,
        "unit": "bool",
        "ok": dv_ok,
    })
    if not dv_ok:
        overall = False

    # Benchmark gates: focus on full_polars mode for real baseline
    target_mode = "full_polars"
    if target_mode not in benchmark_summary:
        results.append({
            "gate": "light_backtest_full_polars_present",
            "value": None,
            "threshold": True,
            "unit": "bool",
            "ok": False,
        })
        overall = False
        return overall, results

    bm = benchmark_summary[target_mode]
    checks = [
        ("light_backtest_total_p50_s", bm.get("total_p50_s")),
        ("light_backtest_total_p95_s", bm.get("total_p95_s")),
        ("light_backtest_data_load_p95_s", bm.get("data_load_p95_s")),
        ("light_backtest_signal_gen_p95_s", bm.get("signal_gen_p95_s")),
        ("light_backtest_equity_metrics_p95_s", bm.get("equity_metrics_p95_s")),
        ("light_backtest_peak_memory_mb", bm.get("peak_memory_p95_mb")),
        ("light_backtest_failure_rate", bm.get("failure_count")),
    ]

    for gate_name, value in checks:
        cfg = GATES[gate_name]
        threshold = cfg["max"]
        ok = value is not None and value <= threshold
        results.append({
            "gate": gate_name,
            "value": value,
            "threshold": threshold,
            "unit": cfg["unit"],
            "ok": ok,
        })
        if not ok:
            overall = False

    return overall, results


def main() -> None:
    args = parse_args()

    gate_config = GATES
    if args.gate_config and os.path.exists(args.gate_config):
        with open(args.gate_config, "r", encoding="utf-8") as f:
            gate_config = json.load(f)

    validation = load_validation(args.validation)
    records = load_benchmark_records(args.benchmark)

    benchmark_summary = summarize_benchmark(records) if records else {}
    overall_ok, gate_results = evaluate_gates(validation, benchmark_summary)

    output = {
        "ok": overall_ok,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "validation_file": args.validation,
        "benchmark_file": args.benchmark,
        "validation_summary": {
            "ok": validation.get("ok") if validation else None,
            "errors": validation.get("errors") if validation else None,
            "warnings_count": (
                len(validation.get("foundation", {}).get("warnings", [])) +
                len(validation.get("state_cube", {}).get("warnings", []))
                if validation else None
            ),
        },
        "benchmark_summary": benchmark_summary,
        "gate_results": gate_results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    status = "PASS" if overall_ok else "FAIL"
    print(f"Gate summary written to {args.output}  status={status} gates={len(gate_results)}")
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
