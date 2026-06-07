"""Source / Evidence metadata schema.

All enums and Pydantic v2 models.
Canonical source_type per decision 0009.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(str, Enum):
    """Canonical factor source types (decision 0009)."""

    STRATEGY_GENERATOR = "strategy_generator"
    OPEN_QUANT_FRAMEWORK = "open_quant_framework"
    INSTITUTIONAL_FACTOR = "institutional_factor"
    ACADEMIC_LITERATURE = "academic_literature"
    FUNDAMENTAL_DATA = "fundamental_data"
    NEWS_SENTIMENT = "news_sentiment"
    MONEY_FLOW = "money_flow"
    TRADER_METHODOLOGY = "trader_methodology"
    BEHAVIORAL_FACTOR = "behavioral_factor"
    HERMASS_NATIVE = "hermass_native"


class Reliability(str, Enum):
    """Source reliability level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class ApplicableMarket(str, Enum):
    """Applicable markets."""

    A_SHARE = "A_SHARE"
    US_EQUITY = "US_EQUITY"
    GLOBAL = "GLOBAL"
    FUTURES = "FUTURES"
    CRYPTO = "CRYPTO"
    ETF = "ETF"
    INDEX = "INDEX"


class EvidenceLevel(str, Enum):
    """Evidence level E0-E6."""

    E0 = "E0"  # idea only
    E1 = "E1"  # known literature / public framework
    E2 = "E2"  # data available and computable
    E3 = "E3"  # IC/stratified return passed
    E4 = "E4"  # backtest passed
    E5 = "E5"  # walk-forward / robustness passed
    E6 = "E6"  # paper trading validated


class EvidenceType(str, Enum):
    """Evidence type."""

    LITERATURE = "literature"
    WHITE_PAPER = "white_paper"
    ACADEMIC_PAPER = "academic_paper"
    BOOK = "book"
    BACKTEST = "backtest"
    WALK_FORWARD = "walk_forward"
    PRODUCTION_RUN = "production_run"
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"
    THEORETICAL = "theoretical"


class ValidationStatus(str, Enum):
    """Validation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"


class EvidenceStatus(str, Enum):
    """Evidence record status."""

    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXPIRED = "expired"


class FailureMode(str, Enum):
    """Known failure modes."""

    HIGH_TURNOVER = "high_turnover"
    DATA_SNOOPING = "data_snooping"
    REGIME_DEPENDENT = "regime_dependent"
    LIQUIDITY_BIAS = "liquidity_bias"
    SURVIVORSHIP_BIAS = "survivorship_bias"
    LOOKAHEAD_RISK = "lookahead_risk"
    SHORT_SAMPLE = "short_sample"
    COST_SENSITIVE = "cost_sensitive"
    CROWDING_RISK = "crowding_risk"
    STRUCTURAL_BREAK = "structural_break"


class MetricRef(BaseModel):
    """Validation metric reference."""

    metric: Optional[str] = Field(None, description="Metric name, e.g. RankIC_mean, ICIR")
    metric_name: Optional[str] = Field(None, description="Alias for metric")
    value: Optional[float] = Field(None, description="Metric value")
    threshold: Optional[float] = Field(None, description="Pass threshold")
    window: Optional[str] = Field(None, description="Test window, e.g. 2020-2025")
    period: Optional[str] = Field(None, description="Alias for window")
    universe: Optional[str] = Field(None, description="Universe, e.g. A_SHARE_ALL")
    passed: bool = Field(False, description="Whether threshold is met")

    @model_validator(mode="after")
    def _sync_metric_name(self) -> "MetricRef":
        if self.metric_name and not self.metric:
            self.metric = self.metric_name
        if self.period and not self.window:
            self.window = self.period
        return self


class Evidence(BaseModel):
    """Evidence record."""

    evidence_id: str = Field(..., min_length=1, max_length=128)
    target_id: str = Field("", description="Associated factor_id or block_id")
    source_id: Optional[str] = Field(None, description="Alias for target_id (legacy)")
    target_type: str = Field(default="factor", pattern="^(factor|block)$")
    evidence_level: EvidenceLevel
    evidence_type: EvidenceType
    description: Optional[str] = Field(None)
    metric_refs: List[MetricRef] = Field(default_factory=list)
    metrics: Optional[List[MetricRef]] = Field(None, description="Alias for metric_refs (legacy)")
    validation_status: ValidationStatus
    status: Optional[str] = Field(None, description="Alias for validation_status (legacy)")
    date: Optional[str] = Field(None, description="Evidence date string")
    last_validated_at: Optional[datetime] = Field(None)
    failure_modes: List[FailureMode] = Field(default_factory=list)
    validator_id: Optional[str] = Field(None, description="Validator identifier")
    validation_report_url: Optional[str] = Field(None)
    url: Optional[str] = Field(None, description="Reference URL")
    notes: Optional[str] = Field(None)

    @model_validator(mode="after")
    def _sync_legacy_fields(self) -> "Evidence":
        if self.source_id and not self.target_id:
            self.target_id = self.source_id
        if self.metrics and not self.metric_refs:
            self.metric_refs = self.metrics
        if self.status and not self.validation_status:
            self.validation_status = ValidationStatus(self.status)
        return self


class FactorSource(BaseModel):
    """Factor source record."""

    source_id: str = Field(..., min_length=1, max_length=128)
    source_type: SourceType
    name: str = Field(..., min_length=1, max_length=256)
    name_en: Optional[str] = Field(None)
    url_or_local_ref: Optional[str] = Field(None, min_length=1)
    url: Optional[str] = Field(None, description="Alias for url_or_local_ref (legacy)")
    description: Optional[str] = Field(None)
    reliability: Reliability = Reliability.UNVERIFIED
    license_notes: str = Field(default="unknown", min_length=1)
    applicable_markets: List[ApplicableMarket] = Field(default_factory=list)
    imported_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None)

    @model_validator(mode="after")
    def _sync_legacy_fields(self) -> "FactorSource":
        if self.url and not self.url_or_local_ref:
            self.url_or_local_ref = self.url
        return self

    @field_validator("applicable_markets")
    @classmethod
    def _markets_not_empty(cls, v: List[ApplicableMarket]) -> List[ApplicableMarket]:
        if not v:
            raise ValueError("applicable_markets must have at least one market")
        return v
