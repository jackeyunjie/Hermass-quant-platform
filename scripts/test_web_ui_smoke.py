"""Web UI smoke test for Hermass Strategy Lab.

Uses FastAPI TestClient to verify the 3 pages and core user journey
without starting a real server. Does not require real DB.
"""

from __future__ import annotations

import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

# Use temp DBs for smoke tests so we don't pollute project outputs
_tmpdir = tempfile.mkdtemp(prefix="hermass_web_smoke_")
os.environ.setdefault("STRATEGY_LAB_STORAGE_DB", os.path.join(_tmpdir, "storage.duckdb"))
os.environ.setdefault("STRATEGY_LAB_AUDIT_DB", os.path.join(_tmpdir, "audit.duckdb"))

from web.main import app  # noqa: E402


client = TestClient(app)


@contextmanager
def temporary_env(**updates: str):
    """Temporarily override environment variables for a test."""
    original = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _write_readiness_file(tmp_path: Path, verdict: str) -> Path:
    path = tmp_path / "data_readiness_status.json"
    if verdict == "READY":
        path.write_text(
            """
            {
              "verdict": "READY",
              "validation_ok": true,
              "foundation_db": {"exists": true},
              "ui_display": {"zh": "真实数据基线已就绪，可切换 light_real_v1 模式。"},
              "next_steps": []
            }
            """,
            encoding="utf-8",
        )
    else:
        path.write_text(
            """
            {
              "verdict": "NOT_READY",
              "validation_ok": false,
              "foundation_db": {"exists": false},
              "ui_display": {"zh": "真实数据基线尚未就绪，当前仅支持 synthetic / light_stub 模式。"},
              "next_steps": ["生成真实数据基线"]
            }
            """,
            encoding="utf-8",
        )
    return path


def test_home_page() -> None:
    readiness_dir = Path(tempfile.mkdtemp(prefix="hermass_web_readiness_"))
    readiness_path = _write_readiness_file(readiness_dir, "READY")
    with temporary_env(DATA_READINESS_STATUS_PATH=str(readiness_path)):
        response = client.get("/")
    assert response.status_code == 200
    assert "不构成投资建议" in response.text
    assert "light_real_v1" in response.text
    assert "READY" in response.text
    assert "真实数据基线已就绪" in response.text


def test_home_page_not_ready_fallback() -> None:
    readiness_dir = Path(tempfile.mkdtemp(prefix="hermass_web_readiness_"))
    readiness_path = _write_readiness_file(readiness_dir, "NOT_READY")
    with temporary_env(DATA_READINESS_STATUS_PATH=str(readiness_path)):
        response = client.get("/")
    assert response.status_code == 200
    assert "light_stub" in response.text
    assert "NOT_READY" in response.text
    assert "真实数据基线尚未就绪" in response.text


def test_structuring_valid_sample() -> None:
    response = client.post(
        "/strategy-lab/structuring",
        data={
            "strategy_id": "ma5_cross_ma20_stop_8",
            "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
        },
    )
    assert response.status_code == 200
    assert "trace_id" in response.text
    assert "通过" in response.text
    assert "RL_EXIT_MUST_HAVE_STOP_LOSS" not in response.text


def test_structuring_over_position_red_line() -> None:
    response = client.post(
        "/strategy-lab/structuring",
        data={
            "strategy_id": "over_position_test",
            "natural_language": "MA5上穿MA20买入，跌破MA10卖出，仓位30%",
        },
    )
    assert response.status_code == 200
    assert "RL_MAX_POSITION" in response.text
    assert "拒绝" in response.text


def test_structuring_missing_stop_loss() -> None:
    response = client.post(
        "/strategy-lab/structuring",
        data={
            "strategy_id": "missing_stop_loss_test",
            "natural_language": "MA5上穿MA20买入，跌破MA10卖出",
        },
    )
    assert response.status_code == 200
    assert "RL_EXIT_MUST_HAVE_STOP_LOSS" in response.text


def test_full_journey() -> None:
    # 1. Structuring
    response = client.post(
        "/strategy-lab/structuring",
        data={
            "strategy_id": "ma5_cross_ma20_stop_8",
            "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
        },
    )
    assert response.status_code == 200
    html = response.text
    # Extract trace_id from banner

    match = re.search(r"<code>([a-f0-9\-]+)</code>", html)
    assert match, "trace_id not found in structuring response"
    trace_id = match.group(1)

    # 2. Preview
    response = client.post(
        "/strategy-lab/diagnosis/run",
        data={
            "trace_id": trace_id,
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
            "stage": "preview",
        },
    )
    assert response.status_code == 200
    assert "Preview 结果" in response.text

    # 3. Backtest (will be stub because no real DB)
    response = client.post(
        "/strategy-lab/diagnosis/run",
        data={
            "trace_id": trace_id,
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
            "stage": "backtest",
        },
    )
    assert response.status_code == 200
    assert "Backtest 结果" in response.text
    assert "light_stub" in response.text or "light_real_v1" in response.text

    # 4. Evidence
    response = client.get(f"/strategy-lab/evidence?trace_id={trace_id}")
    assert response.status_code == 200
    assert "Audit Timeline" in response.text
    assert "generation" in response.text
    assert "validation" in response.text
    assert "preview" in response.text
    assert "backtest" in response.text


def test_readiness_ready_shows_light_real_v1_on_diagnosis_page() -> None:
    """Explicit assertion: when readiness is READY, diagnosis/backtest page
    shows light_real_v1 as the default run mode on first visit (no prior backtest)."""
    readiness_dir = Path(tempfile.mkdtemp(prefix="hermass_web_rd_diag_"))
    readiness_path = _write_readiness_file(readiness_dir, "READY")
    with temporary_env(DATA_READINESS_STATUS_PATH=str(readiness_path)):
        # After structuring, visit diagnosis page without running backtest first
        response = client.post(
            "/strategy-lab/structuring",
            data={
                "strategy_id": "readiness_diag_test",
                "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
            },
        )
        html = response.text
        match = re.search(r"<code>([a-f0-9\-]+)</code>", html)
        assert match, "trace_id not found"
        trace_id = match.group(1)

        # Directly visit evidence/diagnosis page (no stored backtest yet)
        response = client.get(f"/strategy-lab/evidence?trace_id={trace_id}")
        assert response.status_code == 200
        # When READY and no stored backtest, default_run_tag should be light_real_v1
        assert "light_real_v1" in response.text


def test_readiness_not_ready_shows_light_stub_on_diagnosis_page() -> None:
    """Explicit assertion: when readiness is NOT_READY, diagnosis page
    defaults to light_stub on first visit."""
    readiness_dir = Path(tempfile.mkdtemp(prefix="hermass_web_rd_nd_"))
    readiness_path = _write_readiness_file(readiness_dir, "NOT_READY")
    with temporary_env(DATA_READINESS_STATUS_PATH=str(readiness_path)):
        response = client.post(
            "/strategy-lab/structuring",
            data={
                "strategy_id": "not_ready_diag_test",
                "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
            },
        )
        html = response.text
        match = re.search(r"<code>([a-f0-9\-]+)</code>", html)
        assert match, "trace_id not found"
        trace_id = match.group(1)

        response = client.get(f"/strategy-lab/evidence?trace_id={trace_id}")
        assert response.status_code == 200
        assert "light_stub" in response.text


if __name__ == "__main__":
    test_home_page()
    print("✅ home page")

    test_home_page_not_ready_fallback()
    print("✅ home page NOT_READY fallback")

    test_readiness_ready_shows_light_real_v1_on_diagnosis_page()
    print("✅ READY diagnosis shows light_real_v1 by default")

    test_readiness_not_ready_shows_light_stub_on_diagnosis_page()
    print("✅ NOT_READY diagnosis shows light_stub by default")

    test_structuring_valid_sample()
    print("✅ structuring valid sample")

    test_structuring_over_position_red_line()
    print("✅ structuring over-position red line")

    test_structuring_missing_stop_loss()
    print("✅ structuring missing stop loss")

    test_full_journey()
    print("✅ full journey")

    print("\nAll Web UI smoke tests passed.")
