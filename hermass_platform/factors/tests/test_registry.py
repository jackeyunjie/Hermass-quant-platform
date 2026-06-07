"""Tests for registry.py — 10 test points."""

import pytest

from hermass_platform.factors.registry import (
    SourceRegistry,
    FactorRegistry,
    BlockRegistry,
    EvidenceRegistry,
    RegistryValidator,
)
from hermass_platform.factors.source_schema import FactorSource, SourceType, Evidence, EvidenceType, EvidenceLevel, ValidationStatus
from hermass_platform.factors.factor_schema import FactorSpec, FactorStatus, DataAvailability, FutureLeakageRisk, ProductionGate
from hermass_platform.factors.block_schema import BlockSpec, BlockType, ParameterSpec, ParameterSpace, ParameterMode, ContextRequirement
from hermass_platform.factors.exceptions import (
    DuplicateEvidenceError,
    SourceNotFoundError,
    FactorNotFoundError,
    BlockNotFoundError,
    RegistryValidationError,
)


class TestSourceRegistry:
    """10. Test SourceRegistry."""

    def test_register_and_get(self):
        reg = SourceRegistry()
        src = FactorSource(
            source_id="src_1",
            name="Source 1",
            source_type=SourceType.OPEN_QUANT_FRAMEWORK,
            applicable_markets=["A_SHARE"],
        )
        reg.register(src)
        assert reg.get("src_1") == src

    def test_get_not_found_returns_none(self):
        reg = SourceRegistry()
        assert reg.get("nonexistent") is None

    def test_require_not_found_raises(self):
        reg = SourceRegistry()
        with pytest.raises(SourceNotFoundError):
            reg.require("nonexistent")

    def test_list_sources(self):
        reg = SourceRegistry()
        reg.register(FactorSource(
            source_id="s1", name="S1",
            source_type=SourceType.ACADEMIC_LITERATURE,
            applicable_markets=["A_SHARE"],
        ))
        reg.register(FactorSource(
            source_id="s2", name="S2",
            source_type=SourceType.FUNDAMENTAL_DATA,
            applicable_markets=["A_SHARE"],
        ))
        assert len(reg.list_all()) == 2


class TestFactorRegistry:
    """11. Test FactorRegistry."""

    def test_register_and_get(self):
        reg = FactorRegistry()
        f = FactorSpec(
            factor_id="f1",
            name="F1",
            category="technical",
            level="L1",
            frequency="D1",
            inputs=["close"],
            required_tables=["daily_bars"],
            required_columns=["close"],
            output_type="numeric",
            direction="neutral",
            compute_engine="polars",
            preview_support="fully_supported",
            dsl_exposure="exposed",
            status=FactorStatus.VALIDATED,
            version="0.1.0",
            source_refs=["src1"],
            evidence_level=EvidenceLevel.E2,
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            a_share_notes="test",
        )
        reg.register(f)
        assert reg.get("f1") == f

    def test_list_by_status(self):
        reg = FactorRegistry()
        reg.register(FactorSpec(
            factor_id="f1", name="F1",
            category="technical", level="L1", frequency="D1",
            inputs=["close"], required_tables=["daily_bars"],
            required_columns=["close"], output_type="numeric",
            direction="neutral", compute_engine="polars",
            preview_support="fully_supported", dsl_exposure="exposed",
            status=FactorStatus.VALIDATED, version="0.1.0",
            source_refs=["src_a"], evidence_level=EvidenceLevel.E2,
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            a_share_notes="test",
        ))
        result = reg.list_by_status("validated")
        assert len(result) == 1

    def test_list_production_ready(self):
        reg = FactorRegistry()
        reg.register(FactorSpec(
            factor_id="f1", name="F1",
            category="technical", level="L1", frequency="D1",
            inputs=["close"], required_tables=["daily_bars"],
            required_columns=["close"], output_type="numeric",
            direction="neutral", compute_engine="polars",
            preview_support="fully_supported", dsl_exposure="exposed",
            status=FactorStatus.PRODUCTION, version="1.0.0",
            source_refs=["src1"], evidence_level=EvidenceLevel.E5,
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            a_share_notes="test",
        ))
        approved = reg.list_production_ready()
        assert len(approved) == 1


class TestBlockRegistry:
    """12. Test BlockRegistry."""

    def test_register_and_get(self):
        reg = BlockRegistry()
        b = BlockSpec(
            block_id="b1",
            block_type=BlockType.SIGNAL,
            name="B1",
            description="Test block",
            input_factor_types=["numeric"],
            parameters={},
            parameter_space={},
            weight=1.0,
            enabled=True,
            required_context=[ContextRequirement.NONE],
            market_scope=["A_SHARE"],
            status="validated",
            version="0.1.0",
            source_refs=["src1"],
            evidence_level=EvidenceLevel.E2,
            production_gate="candidate",
        )
        reg.register(b)
        assert reg.get("b1") == b

    def test_get_by_type(self):
        reg = BlockRegistry()
        reg.register(BlockSpec(
            block_id="b1", block_type=BlockType.SIGNAL,
            name="B1", description="Test",
            input_factor_types=["numeric"], parameters={}, parameter_space={},
            weight=1.0, enabled=True,
            required_context=[ContextRequirement.NONE],
            market_scope=["A_SHARE"], status="validated",
            version="0.1.0", source_refs=["src1"],
            evidence_level=EvidenceLevel.E2, production_gate="candidate",
        ))
        reg.register(BlockSpec(
            block_id="b2", block_type=BlockType.EXIT,
            name="B2", description="Test",
            input_factor_types=["numeric"], parameters={}, parameter_space={},
            weight=1.0, enabled=True,
            required_context=[ContextRequirement.BACKTEST],
            market_scope=["A_SHARE"], status="validated",
            version="0.1.0", source_refs=["src1"],
            evidence_level=EvidenceLevel.E2, production_gate="candidate",
        ))
        signals = reg.list_by_type("signal")
        assert len(signals) == 1
        exits = reg.list_by_type("exit")
        assert len(exits) == 1


class TestEvidenceRegistry:
    """13. Test EvidenceRegistry."""

    def test_register_and_list_by_target(self):
        reg = EvidenceRegistry()
        ev = Evidence(
            evidence_id="ev1",
            target_id="fac1",
            target_type="factor",
            evidence_type=EvidenceType.BACKTEST,
            evidence_level=EvidenceLevel.E2,
            validation_status=ValidationStatus.PASSED,
        )
        reg.register(ev)
        result = reg.list_by_target("fac1")
        assert len(result) == 1
        assert result[0].evidence_id == "ev1"

    def test_duplicate_evidence_raises_specific_error(self):
        reg = EvidenceRegistry()
        ev = Evidence(
            evidence_id="ev1",
            target_id="fac1",
            target_type="factor",
            evidence_type=EvidenceType.BACKTEST,
            evidence_level=EvidenceLevel.E2,
            validation_status=ValidationStatus.PASSED,
        )
        reg.register(ev)
        with pytest.raises(DuplicateEvidenceError):
            reg.register(ev)


class TestRegistryValidator:
    """14. Test RegistryValidator cross-registry validation."""

    def test_validate_all_ok(self):
        src_reg = SourceRegistry()
        src_reg.register(FactorSource(
            source_id="src1", name="S1",
            source_type=SourceType.OPEN_QUANT_FRAMEWORK,
            applicable_markets=["A_SHARE"],
        ))
        fac_reg = FactorRegistry()
        fac_reg.register(FactorSpec(
            factor_id="f1", name="F1",
            category="technical", level="L1", frequency="D1",
            inputs=["close"], required_tables=["daily_bars"],
            required_columns=["close"], output_type="numeric",
            direction="neutral", compute_engine="polars",
            preview_support="fully_supported", dsl_exposure="exposed",
            status=FactorStatus.VALIDATED, version="0.1.0",
            source_refs=["src1"], evidence_level=EvidenceLevel.E2,
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            a_share_notes="test",
        ))
        validator = RegistryValidator(src_reg, fac_reg, BlockRegistry(), EvidenceRegistry())
        result = validator.validate_all()
        # source_refs should pass
        assert result["factor_source_refs"] == []

    def test_validate_source_refs_missing(self):
        src_reg = SourceRegistry()
        fac_reg = FactorRegistry()
        fac_reg.register(FactorSpec(
            factor_id="f1", name="F1",
            category="technical", level="L1", frequency="D1",
            inputs=["close"], required_tables=["daily_bars"],
            required_columns=["close"], output_type="numeric",
            direction="neutral", compute_engine="polars",
            preview_support="fully_supported", dsl_exposure="exposed",
            status=FactorStatus.VALIDATED, version="0.1.0",
            source_refs=["missing_src"], evidence_level=EvidenceLevel.E2,
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            a_share_notes="test",
        ))
        validator = RegistryValidator(src_reg, fac_reg, BlockRegistry(), EvidenceRegistry())
        result = validator.validate_all()
        assert len(result["factor_source_refs"]) == 1
        assert "missing_src" in result["factor_source_refs"][0]

    def test_validate_future_leakage_detected(self):
        src_reg = SourceRegistry()
        fac_reg = FactorRegistry()
        fac_reg.register(FactorSpec(
            factor_id="f1", name="F1",
            category="fundamental", level="L3", frequency="D1",
            inputs=["eps"], required_tables=["financial"],
            required_columns=["eps"], output_type="numeric",
            direction="higher_better", compute_engine="polars",
            preview_support="partial", dsl_exposure="none",
            status=FactorStatus.RESEARCH, version="0.1.0",
            source_refs=["src1"], evidence_level=EvidenceLevel.E1,
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.HIGH,
            a_share_notes="test",
        ))
        validator = RegistryValidator(src_reg, fac_reg, BlockRegistry(), EvidenceRegistry())
        result = validator.validate_all()
        assert len(result["factor_future_leakage"]) == 1
