"""FactorSpec metadata schema."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from hermass_platform.factors.source_schema import EvidenceLevel


class FactorLevel(str, Enum):
    """Factor computation level."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"


class FactorFrequency(str, Enum):
    """Factor frequency."""

    D1 = "D1"
    H4 = "H4"
    H1 = "H1"
    M30 = "M30"
    M15 = "M15"
    M5 = "M5"
    M1 = "M1"
    TICK = "TICK"


class FactorDirection(str, Enum):
    """Factor direction interpretation."""

    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"
    NEUTRAL = "neutral"


class FactorStatus(str, Enum):
    """Factor status."""

    RESEARCH = "research"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


class ComputeEngine(str, Enum):
    """Compute engine."""

    POLARS = "polars"
    DUCKDB = "duckdb"
    PANDAS = "pandas"
    NUMPY = "numpy"
    SQL = "sql"


class PreviewSupport(str, Enum):
    """Preview support level."""

    FULLY_SUPPORTED = "fully_supported"
    PARTIAL = "partial"
    NOT_SUPPORTED = "not_supported"


class DslExposure(str, Enum):
    """DSL exposure status."""

    NONE = "none"
    CANDIDATE = "candidate"
    EXPOSED = "exposed"


class DataAvailability(str, Enum):
    """Data availability."""

    PENDING = "pending"
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    REQUIRES_LICENSE = "requires_license"


class FutureLeakageRisk(str, Enum):
    """Future leakage risk."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MITIGATED = "mitigated"


class ProductionGate(str, Enum):
    """Production gate."""

    BLOCKED = "blocked"
    CANDIDATE = "candidate"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class FactorSpec(BaseModel):
    """Factor metadata specification."""

    # === Basic fields ===
    factor_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=256)
    name_en: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    category: str = Field(..., min_length=1)
    level: str = Field(..., pattern="^(L0|L1|L2|L3|L4|L5|L6)$")
    frequency: str = Field(..., pattern="^(D1|H4|H1|M30|M15|M5|M1|TICK)$")

    # === Data dependencies ===
    inputs: List[str] = Field(default_factory=list)
    required_tables: List[str] = Field(default_factory=list)
    required_columns: List[str] = Field(default_factory=list)
    output_type: str = Field(
        ..., pattern="^(numeric|boolean|categorical|string|datetime|vector)$"
    )

    # === Computation properties ===
    window: Optional[int] = Field(None, ge=1)
    direction: str = Field(..., pattern="^(higher_better|lower_better|neutral)$")
    normalization: List[str] = Field(default_factory=list)
    neutralization: List[str] = Field(default_factory=list)
    compute_engine: ComputeEngine = ComputeEngine.POLARS

    # === DSL / Preview ===
    preview_support: PreviewSupport = PreviewSupport.FULLY_SUPPORTED
    dsl_exposure: DslExposure = DslExposure.NONE

    # === Lifecycle ===
    status: FactorStatus = FactorStatus.RESEARCH
    version: str = Field(default="0.1.0", pattern=r"^\d+\.\d+\.\d+$")

    # === Source & Evidence (new) ===
    source_refs: List[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel = EvidenceLevel.E0
    evidence_id: Optional[str] = Field(None)
    data_availability: DataAvailability = DataAvailability.PENDING
    future_leakage_risk: FutureLeakageRisk = FutureLeakageRisk.NONE
    a_share_notes: str = Field(..., min_length=1)
    production_gate: ProductionGate = ProductionGate.BLOCKED

    # === Optional ===
    tags: List[str] = Field(default_factory=list)
    compute_params: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_refs")
    @classmethod
    def _source_refs_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("source_refs must have at least one source reference")
        return v

    @field_validator("a_share_notes")
    @classmethod
    def _a_share_notes_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("a_share_notes cannot be empty")
        return v

    @model_validator(mode="after")
    def _derive_production_gate(self) -> "FactorSpec":
        """Derive production_gate from evidence/data/leakage/status."""
        gate = derive_factor_gate(
            evidence_level=self.evidence_level,
            validation_status="passed",
            data_availability=self.data_availability,
            future_leakage_risk=self.future_leakage_risk,
            status=self.status,
        )
        self.production_gate = gate
        return self


def derive_factor_gate(
    evidence_level: EvidenceLevel,
    validation_status: str,
    data_availability: DataAvailability,
    future_leakage_risk: FutureLeakageRisk,
    status: FactorStatus,
) -> ProductionGate:
    """Derive factor production_gate based on business rules.

    Rules:
    - deprecated -> deprecated
    - validation_status=failed -> blocked
    - future_leakage_risk=high -> blocked
    - data_availability in (unavailable, requires_license) -> blocked
    - E0-E3 -> blocked
    - E4 + passed -> candidate
    - E5/E6 + passed -> approved
    """
    if status == FactorStatus.DEPRECATED:
        return ProductionGate.DEPRECATED

    if validation_status == "failed":
        return ProductionGate.BLOCKED

    if future_leakage_risk == FutureLeakageRisk.HIGH:
        return ProductionGate.BLOCKED

    if data_availability in (DataAvailability.UNAVAILABLE, DataAvailability.REQUIRES_LICENSE):
        return ProductionGate.BLOCKED

    if evidence_level in (EvidenceLevel.E0, EvidenceLevel.E1, EvidenceLevel.E2, EvidenceLevel.E3):
        return ProductionGate.BLOCKED

    if evidence_level == EvidenceLevel.E4:
        if validation_status == "passed":
            return ProductionGate.CANDIDATE
        return ProductionGate.BLOCKED

    if evidence_level in (EvidenceLevel.E5, EvidenceLevel.E6):
        if validation_status == "passed":
            return ProductionGate.APPROVED
        return ProductionGate.BLOCKED

    return ProductionGate.BLOCKED
