"""Tests for factor_schema.py — 7 test points."""

import pytest

from hermass_platform.factors.factor_schema import (
    FactorSpec,
    FactorLevel,
    FactorFrequency,
    FactorStatus,
    FactorDirection,
    DataAvailability,
    FutureLeakageRisk,
    ProductionGate,
    derive_factor_gate,
    ComputeEngine,
    PreviewSupport,
    DslExposure,
)
from hermass_platform.factors.source_schema import EvidenceLevel


class TestFactorSpec:
    """4. Test FactorSpec model."""

    def test_valid_factor(self):
        f = FactorSpec(
            factor_id="test_factor",
            name="Test Factor",
            category="technical_momentum",
            level="L1",
            frequency="D1",
            inputs=["close"],
            required_tables=["daily_bars"],
            required_columns=["close"],
            output_type="numeric",
            direction="neutral",
            compute_engine=ComputeEngine.POLARS,
            preview_support=PreviewSupport.FULLY_SUPPORTED,
            dsl_exposure=DslExposure.EXPOSED,
            status=FactorStatus.VALIDATED,
            version="0.1.0",
            source_refs=["qlib_alpha158"],
            evidence_level=EvidenceLevel.E2,
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            a_share_notes="Test note",
        )
        assert f.factor_id == "test_factor"
        assert f.level == "L1"

    def test_factor_level_enum(self):
        assert FactorLevel.L1 == "L1"
        assert FactorLevel.L5 == "L5"

    def test_factor_status_enum(self):
        assert FactorStatus.PRODUCTION == "production"
        assert FactorStatus.DEPRECATED == "deprecated"

    def test_future_leakage_risk_enum(self):
        assert FutureLeakageRisk.HIGH == "high"
        assert FutureLeakageRisk.NONE == "none"


class TestDeriveFactorGate:
    """5. Test derive_factor_gate business rules."""

    def test_deprecated_status_returns_deprecated(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E5,
            validation_status="passed",
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            status=FactorStatus.DEPRECATED,
        )
        assert gate == ProductionGate.DEPRECATED

    def test_failed_validation_returns_blocked(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E5,
            validation_status="failed",
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            status=FactorStatus.VALIDATED,
        )
        assert gate == ProductionGate.BLOCKED

    def test_high_future_leakage_returns_blocked(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E5,
            validation_status="passed",
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.HIGH,
            status=FactorStatus.VALIDATED,
        )
        assert gate == ProductionGate.BLOCKED

    def test_e4_returns_candidate(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E4,
            validation_status="passed",
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            status=FactorStatus.VALIDATED,
        )
        assert gate == ProductionGate.CANDIDATE

    def test_e5_returns_approved(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E5,
            validation_status="passed",
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            status=FactorStatus.PRODUCTION,
        )
        assert gate == ProductionGate.APPROVED

    def test_e0_returns_blocked(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E0,
            validation_status="passed",
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            status=FactorStatus.RESEARCH,
        )
        assert gate == ProductionGate.BLOCKED

    def test_unavailable_data_returns_blocked(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E5,
            validation_status="passed",
            data_availability=DataAvailability.UNAVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            status=FactorStatus.VALIDATED,
        )
        assert gate == ProductionGate.BLOCKED
