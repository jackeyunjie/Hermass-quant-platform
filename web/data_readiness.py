"""Read-only data readiness status loader for the Web UI.

Reads `outputs/benchmarks/data_readiness_status.json` produced by Kimi's
real-data baseline handoff. If the file is missing or malformed, returns a
safe NOT_READY default that matches the contract shape.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _default_readiness_path() -> Path:
    """Resolve readiness JSON path from env at call time."""
    return Path(
        os.getenv(
            "DATA_READINESS_STATUS_PATH",
            "outputs/benchmarks/data_readiness_status.json",
        )
    )


def _not_ready_default() -> dict[str, Any]:
    """Return a NOT_READY status when the readiness file is absent."""
    return {
        "as_of_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "verdict": "NOT_READY",
        "foundation_db": {
            "exists": False,
            "path": "data/p116_foundation.duckdb",
        },
        "state_cube_db": {
            "exists": False,
            "path": "data/state_cube.duckdb",
        },
        "validation_result_path": None,
        "validation_ok": False,
        "validation_errors": [
            "data/p116_foundation.duckdb not found",
            "data/state_cube.duckdb not found",
        ],
        "ui_display": {
            "zh": "真实数据基线尚未就绪，当前仅支持 synthetic / light_stub 模式。",
            "en": "Real data baseline not ready; synthetic / light_stub modes only.",
        },
        "next_steps": [
            "生成或接入 data/p116_foundation.duckdb",
            "生成或接入 data/state_cube.duckdb",
            "重新运行 benchmarks/validate_real_data.py",
        ],
    }


def load_data_readiness(
    path: Path | None = None,
) -> dict[str, Any]:
    """Load data readiness status from JSON.

    Returns a NOT_READY default if the file is missing or cannot be parsed.
    """
    target = path or _default_readiness_path()
    if not target.exists():
        return _not_ready_default()

    try:
        with target.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        default = _not_ready_default()
        default["validation_errors"] = [
            f"Failed to parse {target}",
        ]
        default["ui_display"]["zh"] = "数据 readiness 文件损坏，当前仅支持 synthetic / light_stub 模式。"
        default["ui_display"]["en"] = "Data readiness file is corrupted; synthetic / light_stub modes only."
        return default

    # Basic shape guard: ensure required fields exist
    if not isinstance(data, dict):
        return _not_ready_default()

    data.setdefault("verdict", "NOT_READY")
    data.setdefault(
        "ui_display",
        {
            "zh": "真实数据基线状态未知，当前仅支持 synthetic / light_stub 模式。",
            "en": "Real data baseline status unknown; synthetic / light_stub modes only.",
        },
    )
    return data


def readiness_badge_class(verdict: str) -> str:
    """Map readiness verdict to CSS badge class."""
    verdict = (verdict or "").upper()
    if verdict == "READY":
        return "success"
    if verdict == "PARTIAL":
        return "partial"
    return "failed"


def default_backtest_run_tag(
    readiness: dict[str, Any] | None = None,
) -> str:
    """Return the default backtest mode implied by current readiness."""
    status = readiness or load_data_readiness()
    verdict = str(status.get("verdict", "NOT_READY")).upper()
    validation_ok = bool(status.get("validation_ok", False))
    foundation_exists = bool(status.get("foundation_db", {}).get("exists", False))
    if verdict == "READY" and validation_ok and foundation_exists:
        return "light_real_v1"
    return "light_stub"
