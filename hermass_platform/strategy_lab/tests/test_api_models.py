"""Tests for api_models.py - API request/response models."""

from __future__ import annotations

import pytest

from hermass_platform.strategy_lab.api_models import (
    ConditionPreviewItem,
    PreviewOverallItem,
    PreviewRequest,
    PreviewResponse,
    SectionPreviewItem,
    ValidateStrategyRequest,
    ValidateStrategyResponse,
    ValidationErrorItem,
    GenerateStrategyRequest,
    GenerateStrategyResponse,
    BacktestRequest,
    BacktestResponse,
    GetBacktestResponse,
)
from hermass_platform.strategy_lab.condition_registry import PreviewSupport
from hermass_platform.strategy_lab.dsl_generator import create_ma_crossover_strategy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_dsl():
    return create_ma_crossover_strategy("test_api")


# ---------------------------------------------------------------------------
# Preview Models Tests
# ---------------------------------------------------------------------------

class TestConditionPreviewItem:
    def test_creation(self) -> None:
        item = ConditionPreviewItem(
            condition_type="ma_golden_cross",
            params={"fast_period": 5, "slow_period": 20},
            preview_support=PreviewSupport.FULLY_SUPPORTED.value,
            estimated_hits=42,
        )
        assert item.condition_type == "ma_golden_cross"
        assert item.estimated_hits == 42
        assert item.has_context_required is False

    def test_context_required(self) -> None:
        item = ConditionPreviewItem(
            condition_type="stop_loss_pct",
            params={"value": 0.08},
            preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT.value,
            has_context_required=True,
            estimated_hits=360,
            notes="Requires backtest context",
        )
        assert item.has_context_required is True
        assert item.preview_support == "requires_backtest_context"

    def test_json_serializable(self) -> None:
        item = ConditionPreviewItem(
            condition_type="test",
            estimated_hits=10,
        )
        data = item.model_dump()
        assert data["condition_type"] == "test"
        assert data["estimated_hits"] == 10


class TestSectionPreviewItem:
    def test_creation(self) -> None:
        section = SectionPreviewItem(
            section="entry",
            conditions=[
                ConditionPreviewItem(
                    condition_type="ma_golden_cross",
                    estimated_hits=42,
                )
            ],
            total_estimated_hits=42,
        )
        assert section.section == "entry"
        assert len(section.conditions) == 1
        assert section.has_context_required is False

    def test_with_context_required(self) -> None:
        section = SectionPreviewItem(
            section="exit",
            conditions=[
                ConditionPreviewItem(
                    condition_type="stop_loss_pct",
                    preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT.value,
                    has_context_required=True,
                    estimated_hits=360,
                )
            ],
            has_context_required=True,
        )
        assert section.has_context_required is True


class TestPreviewOverallItem:
    def test_success(self) -> None:
        overall = PreviewOverallItem(
            overall_status="success",
            total_sections=3,
            total_estimated_hits=100,
        )
        assert overall.overall_status == "success"
        assert overall.sections_with_context_required == 0

    def test_partial(self) -> None:
        overall = PreviewOverallItem(
            overall_status="partial",
            total_sections=3,
            sections_with_context_required=1,
            errors=[],
        )
        assert overall.overall_status == "partial"


class TestPreviewRequest:
    def test_creation(self, sample_dsl) -> None:
        req = PreviewRequest(dsl=sample_dsl)
        assert req.data_source == "mock"
        assert req.trace_id != ""
        assert len(req.trace_id) > 0

    def test_trace_id_auto_generated(self, sample_dsl) -> None:
        req1 = PreviewRequest(dsl=sample_dsl)
        req2 = PreviewRequest(dsl=sample_dsl)
        assert req1.trace_id != req2.trace_id

    def test_custom_trace_id(self, sample_dsl) -> None:
        req = PreviewRequest(dsl=sample_dsl, trace_id="custom-123")
        assert req.trace_id == "custom-123"


class TestPreviewResponse:
    def test_creation(self) -> None:
        resp = PreviewResponse(
            trace_id="test-trace",
            overall=PreviewOverallItem(overall_status="success"),
            sections=[
                SectionPreviewItem(
                    section="entry",
                    conditions=[
                        ConditionPreviewItem(condition_type="ma_golden_cross")
                    ],
                )
            ],
        )
        assert resp.trace_id == "test-trace"
        assert resp.dsl_version == "strategy_dsl_v2"
        assert resp.input_hash != ""  # Auto-computed

    def test_failed_response(self) -> None:
        resp = PreviewResponse(
            trace_id="test-trace",
            overall=PreviewOverallItem(
                overall_status="failed",
                errors=["Validation failed"],
            ),
            errors=["Validation failed"],
        )
        assert resp.overall.overall_status == "failed"
        assert len(resp.errors) == 1

    def test_json_serializable(self) -> None:
        resp = PreviewResponse(
            trace_id="t1",
            overall=PreviewOverallItem(overall_status="success"),
        )
        data = resp.model_dump()
        assert data["trace_id"] == "t1"
        assert data["dsl_version"] == "strategy_dsl_v2"


# ---------------------------------------------------------------------------
# Validation Models Tests
# ---------------------------------------------------------------------------

class TestValidateStrategyRequest:
    def test_creation(self, sample_dsl) -> None:
        req = ValidateStrategyRequest(dsl=sample_dsl)
        assert req.dsl is not None
        assert len(req.levels) == 4  # All validation levels

    def test_custom_levels(self, sample_dsl) -> None:
        from hermass_platform.strategy_lab.dsl_validator import ValidationLevel
        req = ValidateStrategyRequest(
            dsl=sample_dsl,
            levels=[ValidationLevel.RED_LINE],
        )
        assert len(req.levels) == 1


class TestValidationErrorItem:
    def test_creation(self) -> None:
        err = ValidationErrorItem(
            level="red_line",
            code="RL_MAX_POSITION",
            message="Max position exceeded",
            path="risk.max_position_pct",
        )
        assert err.level == "red_line"
        assert err.path == "risk.max_position_pct"


class TestValidateStrategyResponse:
    def test_creation(self) -> None:
        resp = ValidateStrategyResponse(
            trace_id="t1",
            passed=True,
            level="structure",
        )
        assert resp.passed is True
        assert resp.red_line_result == {}


# ---------------------------------------------------------------------------
# Generation Models Tests
# ---------------------------------------------------------------------------

class TestGenerateStrategyRequest:
    def test_creation(self) -> None:
        req = GenerateStrategyRequest(
            natural_language="MA5上穿MA20买入",
            strategy_id="ma_cross_v1",
        )
        assert req.natural_language == "MA5上穿MA20买入"
        assert req.strategy_id == "ma_cross_v1"
        assert req.trace_id != ""

    def test_invalid_strategy_id(self) -> None:
        with pytest.raises(ValueError):
            GenerateStrategyRequest(
                natural_language="test",
                strategy_id="Invalid-ID",  # Contains uppercase and hyphen
            )


class TestGenerateStrategyResponse:
    def test_creation(self, sample_dsl) -> None:
        resp = GenerateStrategyResponse(
            trace_id="t1",
            dsl=sample_dsl,
        )
        assert resp.dsl is not None
        assert len(resp.errors) == 0

    def test_failed_generation(self) -> None:
        resp = GenerateStrategyResponse(
            trace_id="t1",
            errors=["Generation failed"],
        )
        assert resp.dsl is None


# ---------------------------------------------------------------------------
# Backtest Models Tests
# ---------------------------------------------------------------------------

class TestBacktestRequest:
    def test_creation(self, sample_dsl) -> None:
        req = BacktestRequest(
            dsl=sample_dsl,
            start_date="2020-01-01",
            end_date="2023-12-31",
        )
        assert req.start_date == "2020-01-01"
        assert req.trace_id != ""


class TestBacktestResponse:
    def test_creation(self) -> None:
        resp = BacktestResponse(
            trace_id="t1",
            status="success",
        )
        assert resp.status == "success"
        assert resp.metrics.total_trades is None


class TestGetBacktestResponse:
    def test_creation(self) -> None:
        resp = GetBacktestResponse(
            trace_id="t1",
            status="success",
            created_at="2024-01-01T00:00:00Z",
        )
        assert resp.created_at == "2024-01-01T00:00:00Z"
        assert resp.dsl_snapshot is None
