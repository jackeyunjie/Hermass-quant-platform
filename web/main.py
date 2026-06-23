"""Hermass Strategy Lab Web UI entry point.

Thin FastAPI layer over hermass_platform.strategy_lab services.
All business logic remains in the strategy_lab package.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Any

from . import api_routes, strategy_lab_routes
from .data_readiness import (
    default_backtest_run_tag,
    load_data_readiness,
    readiness_badge_class,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STORAGE_DB = os.getenv(
    "STRATEGY_LAB_STORAGE_DB",
    "outputs/strategy_lab/web_storage.duckdb",
)
AUDIT_DB = os.getenv(
    "STRATEGY_LAB_AUDIT_DB",
    "outputs/strategy_lab/web_audit.duckdb",
)
FOUNDATION_DB = os.getenv(
    "FOUNDATION_DB",
    "data/p116_foundation.duckdb",
)
STATE_CUBE_DB = os.getenv(
    "STATE_CUBE_DB",
    "data/state_cube.duckdb",
)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Hermass Strategy Lab",
    description="AI-native quantitative strategy research UI",
    version="0.1.0",
)

# Static assets
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Routes
app.include_router(strategy_lab_routes.router)
app.include_router(api_routes.router)


def _readiness_context() -> dict[str, Any]:
    """Build template context keys for data readiness display."""
    readiness = load_data_readiness()
    verdict = readiness.get("verdict", "NOT_READY")
    ui = readiness.get("ui_display", {})
    return {
        "readiness_verdict": verdict,
        "readiness_badge": readiness_badge_class(verdict),
        "readiness_message": ui.get("zh", ""),
        "readiness_next_steps": readiness.get("next_steps", []),
        "default_run_tag": default_backtest_run_tag(readiness),
    }


@app.get("/")
async def index(request: Request) -> "TemplateResponse":
    """Project landing page."""
    context: dict[str, Any] = {
        "request": request,
        "run_tag": _readiness_context().get("default_run_tag", "light_stub"),
        "disclaimer": (
            "本工具仅用于策略研究与技术验证，不构成投资建议。"
            "回测结果不代表未来收益。"
        ),
    }
    context.update(_readiness_context())
    return templates.TemplateResponse(
        request,
        "index.html",
        context,
    )
