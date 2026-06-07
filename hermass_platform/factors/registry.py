"""Unified metadata registry.

SourceRegistry / FactorRegistry / BlockRegistry / EvidenceRegistry
with cross-registry validation.
"""

from typing import Dict, List, Optional

from hermass_platform.factors.block_schema import BlockSpec
from hermass_platform.factors.exceptions import (
    BlockNotFoundError,
    DuplicateBlockError,
    DuplicateEvidenceError,
    DuplicateFactorError,
    DuplicateSourceError,
    FactorNotFoundError,
    SourceNotFoundError,
)
from hermass_platform.factors.factor_schema import (
    DataAvailability,
    FactorSpec,
    FutureLeakageRisk,
    ProductionGate,
)
from hermass_platform.factors.source_schema import (
    Evidence,
    EvidenceLevel,
    FactorSource,
)


class SourceRegistry:
    """Source registry."""

    def __init__(self) -> None:
        self._sources: Dict[str, FactorSource] = {}

    def register(self, source: FactorSource) -> FactorSource:
        if source.source_id in self._sources:
            raise DuplicateSourceError(
                f"source_id '{source.source_id}' already exists"
            )
        self._sources[source.source_id] = source
        return source

    def get(self, source_id: str) -> Optional[FactorSource]:
        return self._sources.get(source_id)

    def require(self, source_id: str) -> FactorSource:
        src = self._sources.get(source_id)
        if src is None:
            raise SourceNotFoundError(f"source_id '{source_id}' not found")
        return src

    def list_all(self) -> List[FactorSource]:
        return list(self._sources.values())

    def list_by_type(self, source_type: str) -> List[FactorSource]:
        return [
            s for s in self._sources.values() if s.source_type.value == source_type
        ]

    def list_by_market(self, market: str) -> List[FactorSource]:
        return [
            s
            for s in self._sources.values()
            if any(m.value == market for m in s.applicable_markets)
        ]

    def list_by_reliability(self, reliability: str) -> List[FactorSource]:
        return [
            s for s in self._sources.values() if s.reliability.value == reliability
        ]


class EvidenceRegistry:
    """Evidence registry."""

    def __init__(self) -> None:
        self._evidence: Dict[str, Evidence] = {}

    def register(self, evidence: Evidence) -> Evidence:
        if evidence.evidence_id in self._evidence:
            raise DuplicateEvidenceError(
                f"evidence_id '{evidence.evidence_id}' already exists"
            )
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    def get(self, evidence_id: str) -> Optional[Evidence]:
        return self._evidence.get(evidence_id)

    def list_all(self) -> List[Evidence]:
        return list(self._evidence.values())

    def list_by_target(self, target_id: str) -> List[Evidence]:
        return [e for e in self._evidence.values() if e.target_id == target_id]

    def list_by_level(self, level: str) -> List[Evidence]:
        return [
            e for e in self._evidence.values() if e.evidence_level.value == level
        ]

    def list_by_status(self, status: str) -> List[Evidence]:
        return [
            e for e in self._evidence.values() if e.validation_status.value == status
        ]


class FactorRegistry:
    """Factor registry."""

    def __init__(self) -> None:
        self._factors: Dict[str, FactorSpec] = {}

    def register(self, factor: FactorSpec) -> FactorSpec:
        if factor.factor_id in self._factors:
            raise DuplicateFactorError(
                f"factor_id '{factor.factor_id}' already exists"
            )
        self._factors[factor.factor_id] = factor
        return factor

    def get(self, factor_id: str) -> Optional[FactorSpec]:
        return self._factors.get(factor_id)

    def require(self, factor_id: str) -> FactorSpec:
        f = self._factors.get(factor_id)
        if f is None:
            raise FactorNotFoundError(f"factor_id '{factor_id}' not found")
        return f

    def list_all(self) -> List[FactorSpec]:
        return list(self._factors.values())

    def list_by_category(self, category: str) -> List[FactorSpec]:
        return [f for f in self._factors.values() if f.category == category]

    def list_by_status(self, status: str) -> List[FactorSpec]:
        return [f for f in self._factors.values() if f.status.value == status]

    def list_by_level(self, level: str) -> List[FactorSpec]:
        return [f for f in self._factors.values() if f.level == level]

    def list_dsl_exposed(self) -> List[FactorSpec]:
        return [
            f
            for f in self._factors.values()
            if f.dsl_exposure.value in ("candidate", "exposed")
        ]

    def list_production_ready(self) -> List[FactorSpec]:
        return [
            f
            for f in self._factors.values()
            if f.production_gate == ProductionGate.APPROVED
        ]

    def validate_source_refs(self, source_registry: SourceRegistry) -> List[str]:
        """Validate all factor source_refs exist in source_registry."""
        errors: List[str] = []
        for factor in self._factors.values():
            for ref in factor.source_refs:
                if source_registry.get(ref) is None:
                    errors.append(
                        f"factor '{factor.factor_id}' references unknown source '{ref}'"
                    )
        return errors

    def validate_evidence_gate(self) -> List[str]:
        """Validate evidence gate rules."""
        errors: List[str] = []
        for factor in self._factors.values():
            if (
                factor.production_gate == ProductionGate.APPROVED
                and factor.evidence_level not in (EvidenceLevel.E5, EvidenceLevel.E6)
            ):
                errors.append(
                    f"factor '{factor.factor_id}' production_gate=approved "
                    f"but evidence_level={factor.evidence_level}"
                )
        return errors

    def validate_no_future_leakage(self) -> List[str]:
        """Validate future leakage risk."""
        errors: List[str] = []
        for factor in self._factors.values():
            if factor.future_leakage_risk == FutureLeakageRisk.HIGH:
                errors.append(
                    f"factor '{factor.factor_id}' future_leakage_risk=high"
                )
        return errors

    def validate_data_availability(self) -> List[str]:
        """Validate data availability."""
        errors: List[str] = []
        for factor in self._factors.values():
            if factor.data_availability == DataAvailability.UNAVAILABLE:
                errors.append(
                    f"factor '{factor.factor_id}' data_availability=unavailable"
                )
        return errors


class BlockRegistry:
    """Block registry."""

    def __init__(self) -> None:
        self._blocks: Dict[str, BlockSpec] = {}

    def register(self, block: BlockSpec) -> BlockSpec:
        if block.block_id in self._blocks:
            raise DuplicateBlockError(
                f"block_id '{block.block_id}' already exists"
            )
        self._blocks[block.block_id] = block
        return block

    def get(self, block_id: str) -> Optional[BlockSpec]:
        return self._blocks.get(block_id)

    def require(self, block_id: str) -> BlockSpec:
        b = self._blocks.get(block_id)
        if b is None:
            raise BlockNotFoundError(f"block_id '{block_id}' not found")
        return b

    def list_all(self) -> List[BlockSpec]:
        return list(self._blocks.values())

    def list_by_type(self, block_type: str) -> List[BlockSpec]:
        return [b for b in self._blocks.values() if b.block_type.value == block_type]

    def list_by_category(self, category: str) -> List[BlockSpec]:
        return self.list_by_type(category)

    def list_by_status(self, status: str) -> List[BlockSpec]:
        return [b for b in self._blocks.values() if b.status == status]

    def list_enabled(self) -> List[BlockSpec]:
        return [b for b in self._blocks.values() if b.enabled]

    def list_dsl_output(self, dsl_output: str) -> List[BlockSpec]:
        return [b for b in self._blocks.values() if b.dsl_output == dsl_output]

    def list_production_ready(self) -> List[BlockSpec]:
        return [b for b in self._blocks.values() if b.production_gate == "approved"]

    def validate_source_refs(self, source_registry: SourceRegistry) -> List[str]:
        errors: List[str] = []
        for block in self._blocks.values():
            for ref in block.source_refs:
                if source_registry.get(ref) is None:
                    errors.append(
                        f"block '{block.block_id}' references unknown source '{ref}'"
                    )
        return errors

    def validate_factor_refs(self, factor_registry: FactorRegistry) -> List[str]:
        """Validate block factor refs exist in factor_registry."""
        errors: List[str] = []
        for block in self._blocks.values():
            refs = block.input_factor_refs or []
            for ref in refs:
                if factor_registry.get(ref) is None:
                    errors.append(
                        f"block '{block.block_id}' references unknown factor '{ref}'"
                    )
        return errors

    def validate_parameter_space(self) -> List[str]:
        """Validate parameter space boundaries."""
        errors: List[str] = []
        for block in self._blocks.values():
            for name, space in block.parameter_space.items():
                param = block.parameters.get(name)
                if param is None:
                    errors.append(
                        f"block '{block.block_id}' parameter_space '{name}' "
                        f"has no matching parameter"
                    )
                    continue
                if space.mode.value == "range":
                    if param.range_min is not None and space.min < param.range_min:
                        errors.append(
                            f"block '{block.block_id}' '{name}' space.min {space.min} "
                            f"< param.range_min {param.range_min}"
                        )
                    if param.range_max is not None and space.max > param.range_max:
                        errors.append(
                            f"block '{block.block_id}' '{name}' space.max {space.max} "
                            f"> param.range_max {param.range_max}"
                        )
        return errors

    def validate_market_scope(self) -> List[str]:
        """Validate market_scope is non-empty."""
        errors: List[str] = []
        for block in self._blocks.values():
            if not block.market_scope:
                errors.append(f"block '{block.block_id}' market_scope is empty")
        return errors

    def validate_no_unsafe_context(self) -> List[str]:
        """Warn about blocks requiring backtest context.

        Does not block, only returns warnings.
        """
        warnings: List[str] = []
        for block in self._blocks.values():
            from hermass_platform.factors.block_schema import ContextRequirement

            if ContextRequirement.BACKTEST in block.required_context:
                warnings.append(
                    f"block '{block.block_id}' requires BACKTEST context, "
                    f"Preview may be limited"
                )
        return warnings


class RegistryValidator:
    """Cross-registry unified validator."""

    def __init__(
        self,
        source_registry: SourceRegistry,
        factor_registry: FactorRegistry,
        block_registry: BlockRegistry,
        evidence_registry: Optional[EvidenceRegistry] = None,
    ) -> None:
        self.source_registry = source_registry
        self.factor_registry = factor_registry
        self.block_registry = block_registry
        self.evidence_registry = evidence_registry or EvidenceRegistry()

    def validate_all(self) -> Dict[str, List[str]]:
        """Run all cross-registry validations."""
        return {
            "factor_source_refs": self.factor_registry.validate_source_refs(
                self.source_registry
            ),
            "block_source_refs": self.block_registry.validate_source_refs(
                self.source_registry
            ),
            "block_factor_refs": self.block_registry.validate_factor_refs(
                self.factor_registry
            ),
            "factor_evidence_gate": self.factor_registry.validate_evidence_gate(),
            "factor_future_leakage": self.factor_registry.validate_no_future_leakage(),
            "factor_data_availability": self.factor_registry.validate_data_availability(),
            "block_parameter_space": self.block_registry.validate_parameter_space(),
            "block_market_scope": self.block_registry.validate_market_scope(),
            "block_backtest_context_warnings": self.block_registry.validate_no_unsafe_context(),
        }

    def list_production_ready_factors(self) -> List[FactorSpec]:
        return self.factor_registry.list_production_ready()

    def list_production_ready_blocks(self) -> List[BlockSpec]:
        return self.block_registry.list_production_ready()
