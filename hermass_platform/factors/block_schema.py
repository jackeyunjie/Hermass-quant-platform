"""BlockSpec metadata schema."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from hermass_platform.factors.source_schema import EvidenceLevel


class BlockType(str, Enum):
    """Block type."""

    SIGNAL = "signal"
    ENTRY = "entry"
    EXIT = "exit"
    ORDER = "order"
    FILTER = "filter"
    MONEY_MANAGEMENT = "money_management"
    ROBUSTNESS = "robustness"
    REPORT_COLUMN = "report_column"
    PROCESSOR = "processor"


class ContextRequirement(str, Enum):
    """Block context requirement."""

    NONE = "none"
    POSITION = "position"
    PORTFOLIO = "portfolio"
    BACKTEST = "backtest"
    ORDER_BOOK = "order_book"


class ParameterMode(str, Enum):
    """Parameter space mode."""

    CHOICE = "choice"
    RANGE = "range"
    FIXED = "fixed"


class ParameterSpec(BaseModel):
    """Block parameter specification."""

    name: str = Field(..., min_length=1)
    param_type: str = Field(
        ...,
        pattern="^(factor_ref|integer|float|boolean|string|enum|datetime|list)$",
    )
    description: Optional[str] = Field(None)
    default: Optional[Any] = Field(None)
    required: bool = Field(True)

    # Type-specific constraints
    enum_values: Optional[List[Union[str, int, float]]] = Field(None)
    range_min: Optional[Union[int, float]] = Field(None)
    range_max: Optional[Union[int, float]] = Field(None)
    factor_scope: Optional[List[str]] = Field(None)

    @model_validator(mode="after")
    def _check_type_constraints(self) -> "ParameterSpec":
        if self.param_type == "enum" and not self.enum_values:
            raise ValueError("enum type must provide enum_values")
        if self.param_type in ("integer", "float"):
            if self.range_min is not None and self.range_max is not None:
                if self.range_min > self.range_max:
                    raise ValueError("range_min cannot be greater than range_max")
        return self


class ParameterSpace(BaseModel):
    """Parameter search space."""

    mode: ParameterMode
    choices: Optional[List[Any]] = Field(None)
    min: Optional[Union[int, float]] = Field(None)
    max: Optional[Union[int, float]] = Field(None)
    step: Optional[Union[int, float]] = Field(None)

    @model_validator(mode="after")
    def _check_mode(self) -> "ParameterSpace":
        if self.mode == ParameterMode.CHOICE and not self.choices:
            raise ValueError("choice mode must provide choices")
        if self.mode == ParameterMode.RANGE:
            if self.min is None or self.max is None:
                raise ValueError("range mode must provide min and max")
            if self.min > self.max:
                raise ValueError("min cannot be greater than max")
        return self


class BlockSpec(BaseModel):
    """Block metadata specification."""

    # === Basic fields ===
    block_id: str = Field(..., min_length=1, max_length=128)
    block_type: BlockType
    name: str = Field(..., min_length=1, max_length=256)
    name_en: Optional[str] = Field(None)
    description: Optional[str] = Field(None)

    # === Input / Output ===
    input_factor_types: List[str] = Field(default_factory=list)
    input_factor_refs: Optional[List[str]] = Field(None)
    parameters: Dict[str, ParameterSpec] = Field(default_factory=dict)
    parameter_space: Dict[str, ParameterSpace] = Field(default_factory=dict)

    # === Weight & Enable ===
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    enabled: bool = Field(True)

    # === Data dependencies ===
    required_tables: List[str] = Field(default_factory=list)
    required_columns: List[str] = Field(default_factory=list)
    required_context: List[ContextRequirement] = Field(default_factory=list)

    # === DSL / Preview ===
    preview_support: str = Field(
        default="fully_supported",
        pattern="^(fully_supported|partial|not_supported)$",
    )
    dsl_output: Optional[str] = Field(None)
    robustness_role: Optional[str] = Field(None)
    market_scope: List[str] = Field(default_factory=list)

    # === Lifecycle ===
    status: str = Field(
        default="research",
        pattern="^(research|candidate|validated|production|deprecated)$",
    )
    version: str = Field(default="0.1.0", pattern=r"^\d+\.\d+\.\d+$")

    # === Source & Evidence (new) ===
    source_refs: List[str] = Field(default_factory=list)
    methodology_refs: Optional[List[str]] = Field(None)
    evidence_level: EvidenceLevel = EvidenceLevel.E0
    evidence_id: Optional[str] = Field(None)
    generation_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    production_gate: str = Field(
        default="blocked",
        pattern="^(blocked|candidate|approved|deprecated)$",
    )
    robustness_tests: List[str] = Field(default_factory=list)

    # === Optional ===
    tags: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    unsupported_parts: Optional[List[str]] = Field(None)

    @field_validator("source_refs")
    @classmethod
    def _source_refs_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("source_refs must have at least one source reference")
        return v

    @field_validator("generation_weight", "weight")
    @classmethod
    def _weight_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("weight / generation_weight must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def _parameter_space_subset(self) -> "BlockSpec":
        """parameter_space must be a subset of parameters."""
        for key in self.parameter_space:
            if key not in self.parameters:
                raise ValueError(
                    f"parameter_space key '{key}' not found in parameters"
                )
        return self

    @model_validator(mode="after")
    def _derive_production_gate(self) -> "BlockSpec":
        """Derive production_gate from evidence_level."""
        if self.status == "deprecated":
            self.production_gate = "deprecated"
            return self

        if self.evidence_level in (
            EvidenceLevel.E0,
            EvidenceLevel.E1,
            EvidenceLevel.E2,
            EvidenceLevel.E3,
        ):
            self.production_gate = "blocked"
        elif self.evidence_level == EvidenceLevel.E4:
            self.production_gate = "candidate"
        elif self.evidence_level in (EvidenceLevel.E5, EvidenceLevel.E6):
            self.production_gate = "approved"
        else:
            self.production_gate = "blocked"
        return self
