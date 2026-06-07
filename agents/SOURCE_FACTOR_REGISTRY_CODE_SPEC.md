# Source / Evidence / Factor / Block Registry Code Spec

## 目标

输出可直接交给 Codex 落代码的 metadata registry 规格。本轮只做代码规格，不改代码。

---

## 模块结构

```
hermass_platform/factors/
├── __init__.py
├── source_schema.py              # Source / Evidence Pydantic models
├── factor_schema.py              # FactorSpec Pydantic model
├── block_schema.py               # BlockSpec / ParameterSpec Pydantic models
├── registry.py                   # SourceRegistry / FactorRegistry / BlockRegistry / EvidenceRegistry
├── catalog_loader.py             # YAML catalog 加载器
├── exceptions.py                 # 自定义异常
└── tests/
    ├── __init__.py
    ├── test_source_schema.py
    ├── test_factor_schema.py
    ├── test_block_schema.py
    ├── test_registry.py
    ├── test_catalog_loader.py
    └── test_integration.py

config/factors/
├── source_catalog.yaml           # 至少 10 个 sources
├── factor_catalog.yaml           # 至少 10 个 factors
├── block_catalog.yaml            # 至少 10 个 blocks
└── evidence_catalog.yaml         # 至少 10 个 evidence records
```

---

## File 1: `hermass_platform/factors/exceptions.py`

```python
"""Registry 层自定义异常."""


class RegistryError(Exception):
    """Registry 根异常."""
    pass


class DuplicateSourceError(RegistryError):
    """source_id 重复."""
    pass


class DuplicateFactorError(RegistryError):
    """factor_id 重复."""
    pass


class DuplicateBlockError(RegistryError):
    """block_id 重复."""
    pass


class SourceNotFoundError(RegistryError):
    """source_id 不存在."""
    pass


class FactorNotFoundError(RegistryError):
    """factor_id 不存在."""
    pass


class BlockNotFoundError(RegistryError):
    """block_id 不存在."""
    pass


class InvalidSourceTypeError(RegistryError):
    """source_type 不在枚举中."""
    pass


class EvidenceGateError(RegistryError):
    """证据等级不满足生产要求."""
    pass


class FutureLeakageError(RegistryError):
    """存在未来函数风险."""
    pass


class DataUnavailableError(RegistryError):
    """数据不可用."""
    pass
```

---

## File 2: `hermass_platform/factors/source_schema.py`

```python
"""Source / Evidence metadata schema.

所有枚举和 Pydantic v2 模型定义。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(str, Enum):
    """因子来源类型，与 FACTOR_SOURCE_TAXONOMY.md 对齐."""
    STRATEGY_GENERATOR = "strategy_generator"
    OPEN_QUANT_FRAMEWORK = "open_quant_framework"
    INSTITUTIONAL_FACTOR_RESEARCH = "institutional_factor_research"
    ACADEMIC_EMPIRICAL = "academic_empirical"
    FUNDAMENTAL = "fundamental"
    NEWS_EVENT_SENTIMENT = "news_event_sentiment"
    MONEY_FLOW_MICROSTRUCTURE = "money_flow_microstructure"
    TRADER_METHODOLOGY = "trader_methodology"
    BEHAVIORAL_PSYCHOLOGY = "behavioral_psychology"
    HERMASS_NATIVE = "hermass_native"


class Reliability(str, Enum):
    """来源可靠性等级."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class ApplicableMarket(str, Enum):
    """适用市场."""
    A_SHARE = "A_SHARE"
    US_EQUITY = "US_EQUITY"
    GLOBAL = "GLOBAL"
    FUTURES = "FUTURES"
    CRYPTO = "CRYPTO"
    ETF = "ETF"
    INDEX = "INDEX"


class EvidenceLevel(str, Enum):
    """证据等级 E0-E6."""
    E0 = "E0"  # idea only
    E1 = "E1"  # known literature / public framework
    E2 = "E2"  # data available and computable
    E3 = "E3"  # IC/stratified return passed
    E4 = "E4"  # backtest passed
    E5 = "E5"  # walk-forward / robustness passed
    E6 = "E6"  # paper trading validated


class EvidenceType(str, Enum):
    """证据类型."""
    LITERATURE = "literature"
    BACKTEST = "backtest"
    WALK_FORWARD = "walk_forward"
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"
    THEORETICAL = "theoretical"


class ValidationStatus(str, Enum):
    """验证状态."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"


class FailureMode(str, Enum):
    """已知失效模式."""
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
    """验证指标引用."""
    metric: str = Field(..., description="指标名称，如 RankIC_mean, ICIR, layer_return_spread")
    value: Optional[float] = Field(None, description="指标值")
    threshold: Optional[float] = Field(None, description="通过阈值")
    window: Optional[str] = Field(None, description="测试窗口，如 2020-2025")
    universe: Optional[str] = Field(None, description="测试股票池，如 A_SHARE_ALL")
    passed: bool = Field(False, description="是否通过阈值")


class Evidence(BaseModel):
    """证据记录."""
    evidence_id: str = Field(..., description="证据记录唯一标识，如 ev_quality_roe_ttm_v01")
    target_id: str = Field(..., description="关联的 factor_id 或 block_id")
    target_type: str = Field(..., pattern="^(factor|block)$")
    evidence_level: EvidenceLevel
    evidence_type: EvidenceType
    metric_refs: List[MetricRef] = Field(default_factory=list)
    validation_status: ValidationStatus
    last_validated_at: Optional[datetime] = Field(None)
    failure_modes: List[FailureMode] = Field(default_factory=list)
    validator_id: Optional[str] = Field(None, description="验证者标识")
    validation_report_url: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)


class FactorSource(BaseModel):
    """因子来源记录."""
    source_id: str = Field(..., min_length=1, max_length=128)
    source_type: SourceType
    name: str = Field(..., min_length=1, max_length=256)
    url_or_local_ref: str = Field(..., min_length=1)
    reliability: Reliability
    license_notes: str = Field(..., min_length=1)
    applicable_markets: List[ApplicableMarket] = Field(default_factory=list)
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None)

    @field_validator("applicable_markets")
    @classmethod
    def _markets_not_empty(cls, v: List[ApplicableMarket]) -> List[ApplicableMarket]:
        if not v:
            raise ValueError("applicable_markets 至少需要一个市场")
        return v
```

---

## File 3: `hermass_platform/factors/factor_schema.py`

```python
"""FactorSpec metadata schema."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from hermass_platform.factors.source_schema import (
    EvidenceLevel,
    FailureMode,
)


class FactorStatus(str, Enum):
    """因子状态."""
    RESEARCH = "research"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


class ComputeEngine(str, Enum):
    """计算引擎."""
    POLARS = "polars"
    DUCKDB = "duckdb"
    PANDAS = "pandas"
    NUMPY = "numpy"
    SQL = "sql"


class PreviewSupport(str, Enum):
    """Preview 支持程度."""
    FULLY_SUPPORTED = "fully_supported"
    PARTIAL = "partial"
    NOT_SUPPORTED = "not_supported"


class DslExposure(str, Enum):
    """DSL 暴露状态."""
    NONE = "none"
    CANDIDATE = "candidate"
    EXPOSED = "exposed"


class DataAvailability(str, Enum):
    """数据可用性."""
    PENDING = "pending"
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    REQUIRES_LICENSE = "requires_license"


class FutureLeakageRisk(str, Enum):
    """未来函数风险."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MITIGATED = "mitigated"


class ProductionGate(str, Enum):
    """生产闸门."""
    BLOCKED = "blocked"
    CANDIDATE = "candidate"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class FactorSpec(BaseModel):
    """因子元数据规格."""

    # === 基础字段 ===
    factor_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=256)
    name_en: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    category: str = Field(..., min_length=1)
    level: str = Field(..., pattern="^(L0|L1|L2|L3|L4|L5|L6)$")
    frequency: str = Field(..., pattern="^(D1|H4|H1|M30|M15|M5|M1|TICK)$")

    # === 数据依赖 ===
    inputs: List[str] = Field(default_factory=list)
    required_tables: List[str] = Field(default_factory=list)
    required_columns: List[str] = Field(default_factory=list)
    output_type: str = Field(..., pattern="^(numeric|boolean|categorical|string|datetime|vector)$")

    # === 计算属性 ===
    window: Optional[int] = Field(None, ge=1)
    direction: str = Field(..., pattern="^(higher_better|lower_better|neutral)$")
    normalization: List[str] = Field(default_factory=list)
    neutralization: List[str] = Field(default_factory=list)
    compute_engine: ComputeEngine = ComputeEngine.POLARS

    # === DSL / Preview ===
    preview_support: PreviewSupport = PreviewSupport.FULLY_SUPPORTED
    dsl_exposure: DslExposure = DslExposure.NONE

    # === 生命周期 ===
    status: FactorStatus = FactorStatus.RESEARCH
    version: str = Field(default="0.1.0", pattern=r"^\d+\.\d+\.\d+$")

    # === 来源与证据 (新增) ===
    source_refs: List[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel = EvidenceLevel.E0
    evidence_id: Optional[str] = Field(None)
    data_availability: DataAvailability = DataAvailability.PENDING
    future_leakage_risk: FutureLeakageRisk = FutureLeakageRisk.NONE
    a_share_notes: str = Field(..., min_length=1)
    production_gate: ProductionGate = ProductionGate.BLOCKED

    # === 可选 ===
    tags: List[str] = Field(default_factory=list)
    compute_params: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_refs")
    @classmethod
    def _source_refs_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("source_refs 至少需要一个来源引用")
        return v

    @field_validator("a_share_notes")
    @classmethod
    def _a_share_notes_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("a_share_notes 不能为空，必须提供 A 股适配说明")
        return v

    @model_validator(mode="after")
    def _derive_production_gate(self) -> "FactorSpec":
        """根据证据等级、数据可用性、未来函数风险推导 production_gate."""
        gate = derive_factor_gate(
            evidence_level=self.evidence_level,
            validation_status="passed",  # 默认假设已验证；实际由 EvidenceRegistry 传入
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
    """推导 factor production_gate 的业务规则.

    规则:
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
```

---

## File 4: `hermass_platform/factors/block_schema.py`

```python
"""BlockSpec metadata schema."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from hermass_platform.factors.source_schema import EvidenceLevel


class BlockType(str, Enum):
    """Block 类型."""
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
    """Block 需要的上下文."""
    NONE = "none"
    POSITION = "position"
    PORTFOLIO = "portfolio"
    BACKTEST = "backtest"
    ORDER_BOOK = "order_book"


class ParameterMode(str, Enum):
    """参数空间模式."""
    CHOICE = "choice"
    RANGE = "range"
    FIXED = "fixed"


class ParameterSpec(BaseModel):
    """Block 参数规格."""
    name: str = Field(..., min_length=1)
    param_type: str = Field(..., pattern="^(factor_ref|integer|float|boolean|string|enum|datetime|list)$")
    description: Optional[str] = Field(None)
    default: Optional[Any] = Field(None)
    required: bool = Field(True)

    # 类型相关约束
    enum_values: Optional[List[Union[str, int, float]]] = Field(None)
    range_min: Optional[Union[int, float]] = Field(None)
    range_max: Optional[Union[int, float]] = Field(None)
    factor_scope: Optional[List[str]] = Field(None)

    @model_validator(mode="after")
    def _check_type_constraints(self) -> "ParameterSpec":
        if self.param_type == "enum" and not self.enum_values:
            raise ValueError("enum 类型必须提供 enum_values")
        if self.param_type in ("integer", "float"):
            if self.range_min is not None and self.range_max is not None:
                if self.range_min > self.range_max:
                    raise ValueError("range_min 不能大于 range_max")
        return self


class ParameterSpace(BaseModel):
    """参数搜索空间."""
    mode: ParameterMode
    choices: Optional[List[Any]] = Field(None)
    min: Optional[Union[int, float]] = Field(None)
    max: Optional[Union[int, float]] = Field(None)
    step: Optional[Union[int, float]] = Field(None)

    @model_validator(mode="after")
    def _check_mode(self) -> "ParameterSpace":
        if self.mode == ParameterMode.CHOICE and not self.choices:
            raise ValueError("choice 模式必须提供 choices")
        if self.mode == ParameterMode.RANGE:
            if self.min is None or self.max is None:
                raise ValueError("range 模式必须提供 min 和 max")
            if self.min > self.max:
                raise ValueError("min 不能大于 max")
        return self


class BlockSpec(BaseModel):
    """Block 元数据规格."""

    # === 基础字段 ===
    block_id: str = Field(..., min_length=1, max_length=128)
    block_type: BlockType
    name: str = Field(..., min_length=1, max_length=256)
    name_en: Optional[str] = Field(None)
    description: Optional[str] = Field(None)

    # === 输入输出 ===
    input_factor_types: List[str] = Field(default_factory=list)
    input_factor_refs: Optional[List[str]] = Field(None)
    parameters: Dict[str, ParameterSpec] = Field(default_factory=dict)
    parameter_space: Dict[str, ParameterSpace] = Field(default_factory=dict)

    # === 权重与启用 ===
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    enabled: bool = Field(True)

    # === 数据依赖 ===
    required_tables: List[str] = Field(default_factory=list)
    required_columns: List[str] = Field(default_factory=list)
    required_context: List[ContextRequirement] = Field(default_factory=list)

    # === DSL / Preview ===
    preview_support: str = Field(default="fully_supported", pattern="^(fully_supported|partial|not_supported)$")
    dsl_output: Optional[str] = Field(None)
    robustness_role: Optional[str] = Field(None)
    market_scope: List[str] = Field(default_factory=list)

    # === 生命周期 ===
    status: str = Field(default="research", pattern="^(research|candidate|validated|production|deprecated)$")
    version: str = Field(default="0.1.0", pattern=r"^\d+\.\d+\.\d+$")

    # === 来源与证据 (新增) ===
    source_refs: List[str] = Field(default_factory=list)
    methodology_refs: Optional[List[str]] = Field(None)
    evidence_level: EvidenceLevel = EvidenceLevel.E0
    evidence_id: Optional[str] = Field(None)
    generation_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    production_gate: str = Field(default="blocked", pattern="^(blocked|candidate|approved|deprecated)$")
    robustness_tests: List[str] = Field(default_factory=list)

    # === 可选 ===
    tags: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    unsupported_parts: Optional[List[str]] = Field(None)

    @field_validator("source_refs")
    @classmethod
    def _source_refs_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("source_refs 至少需要一个来源引用")
        return v

    @field_validator("generation_weight", "weight")
    @classmethod
    def _weight_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("weight / generation_weight 必须在 0.0-1.0 之间")
        return v

    @model_validator(mode="after")
    def _parameter_space_subset(self) -> "BlockSpec":
        """parameter_space 必须是 parameters 的子集."""
        for key in self.parameter_space:
            if key not in self.parameters:
                raise ValueError(f"parameter_space 中的 '{key}' 不在 parameters 中")
        return self

    @model_validator(mode="after")
    def _derive_production_gate(self) -> "BlockSpec":
        """根据 evidence_level 推导 block production_gate."""
        if self.status == "deprecated":
            self.production_gate = "deprecated"
            return self

        if self.evidence_level in (EvidenceLevel.E0, EvidenceLevel.E1, EvidenceLevel.E2, EvidenceLevel.E3):
            self.production_gate = "blocked"
        elif self.evidence_level == EvidenceLevel.E4:
            self.production_gate = "candidate"
        elif self.evidence_level in (EvidenceLevel.E5, EvidenceLevel.E6):
            self.production_gate = "approved"
        else:
            self.production_gate = "blocked"
        return self
```

---

## File 5: `hermass_platform/factors/registry.py`

```python
"""统一 metadata registry.

包含 SourceRegistry / FactorRegistry / BlockRegistry / EvidenceRegistry，
并提供跨 registry 校验能力。
"""

from typing import Dict, List, Optional

from hermass_platform.factors.block_schema import BlockSpec
from hermass_platform.factors.exceptions import (
    BlockNotFoundError,
    DataUnavailableError,
    DuplicateBlockError,
    DuplicateFactorError,
    DuplicateSourceError,
    EvidenceGateError,
    FactorNotFoundError,
    FutureLeakageError,
    SourceNotFoundError,
)
from hermass_platform.factors.factor_schema import (
    DataAvailability,
    FactorSpec,
    FutureLeakageRisk,
    ProductionGate,
    derive_factor_gate,
)
from hermass_platform.factors.source_schema import (
    Evidence,
    EvidenceLevel,
    FactorSource,
)


class SourceRegistry:
    """来源注册表."""

    def __init__(self) -> None:
        self._sources: Dict[str, FactorSource] = {}

    def register(self, source: FactorSource) -> FactorSource:
        if source.source_id in self._sources:
            raise DuplicateSourceError(f"source_id '{source.source_id}' 已存在")
        self._sources[source.source_id] = source
        return source

    def get(self, source_id: str) -> Optional[FactorSource]:
        return self._sources.get(source_id)

    def require(self, source_id: str) -> FactorSource:
        src = self._sources.get(source_id)
        if src is None:
            raise SourceNotFoundError(f"source_id '{source_id}' 不存在")
        return src

    def list_all(self) -> List[FactorSource]:
        return list(self._sources.values())

    def list_by_type(self, source_type: str) -> List[FactorSource]:
        return [s for s in self._sources.values() if s.source_type.value == source_type]

    def list_by_market(self, market: str) -> List[FactorSource]:
        return [s for s in self._sources.values() if any(m.value == market for m in s.applicable_markets)]

    def list_by_reliability(self, reliability: str) -> List[FactorSource]:
        return [s for s in self._sources.values() if s.reliability.value == reliability]


class EvidenceRegistry:
    """证据注册表."""

    def __init__(self) -> None:
        self._evidence: Dict[str, Evidence] = {}

    def register(self, evidence: Evidence) -> Evidence:
        if evidence.evidence_id in self._evidence:
            raise DuplicateFactorError(f"evidence_id '{evidence.evidence_id}' 已存在")
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    def get(self, evidence_id: str) -> Optional[Evidence]:
        return self._evidence.get(evidence_id)

    def list_all(self) -> List[Evidence]:
        return list(self._evidence.values())

    def list_by_target(self, target_id: str) -> List[Evidence]:
        return [e for e in self._evidence.values() if e.target_id == target_id]

    def list_by_level(self, level: str) -> List[Evidence]:
        return [e for e in self._evidence.values() if e.evidence_level.value == level]

    def list_by_status(self, status: str) -> List[Evidence]:
        return [e for e in self._evidence.values() if e.validation_status.value == status]


class FactorRegistry:
    """因子注册表."""

    def __init__(self) -> None:
        self._factors: Dict[str, FactorSpec] = {}

    def register(self, factor: FactorSpec) -> FactorSpec:
        if factor.factor_id in self._factors:
            raise DuplicateFactorError(f"factor_id '{factor.factor_id}' 已存在")
        self._factors[factor.factor_id] = factor
        return factor

    def get(self, factor_id: str) -> Optional[FactorSpec]:
        return self._factors.get(factor_id)

    def require(self, factor_id: str) -> FactorSpec:
        f = self._factors.get(factor_id)
        if f is None:
            raise FactorNotFoundError(f"factor_id '{factor_id}' 不存在")
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
        return [f for f in self._factors.values() if f.dsl_exposure.value in ("candidate", "exposed")]

    def list_production_ready(self) -> List[FactorSpec]:
        return [f for f in self._factors.values() if f.production_gate == ProductionGate.APPROVED]

    def validate_source_refs(self, source_registry: SourceRegistry) -> List[str]:
        """校验所有 factor 的 source_refs 是否存在于 source_registry."""
        errors: List[str] = []
        for factor in self._factors.values():
            for ref in factor.source_refs:
                if source_registry.get(ref) is None:
                    errors.append(f"factor '{factor.factor_id}' 引用不存在的 source '{ref}'")
        return errors

    def validate_evidence_gate(self) -> List[str]:
        """校验 evidence gate 规则."""
        errors: List[str] = []
        for factor in self._factors.values():
            if factor.production_gate == ProductionGate.APPROVED and factor.evidence_level not in (
                EvidenceLevel.E5,
                EvidenceLevel.E6,
            ):
                errors.append(
                    f"factor '{factor.factor_id}' production_gate=approved 但 evidence_level={factor.evidence_level}"
                )
        return errors

    def validate_no_future_leakage(self) -> List[str]:
        """校验未来函数风险."""
        errors: List[str] = []
        for factor in self._factors.values():
            if factor.future_leakage_risk == FutureLeakageRisk.HIGH:
                errors.append(f"factor '{factor.factor_id}' future_leakage_risk=high")
        return errors

    def validate_data_availability(self) -> List[str]:
        """校验数据可用性."""
        errors: List[str] = []
        for factor in self._factors.values():
            if factor.data_availability == DataAvailability.UNAVAILABLE:
                errors.append(f"factor '{factor.factor_id}' data_availability=unavailable")
        return errors


class BlockRegistry:
    """Block 注册表."""

    def __init__(self) -> None:
        self._blocks: Dict[str, BlockSpec] = {}

    def register(self, block: BlockSpec) -> BlockSpec:
        if block.block_id in self._blocks:
            raise DuplicateBlockError(f"block_id '{block.block_id}' 已存在")
        self._blocks[block.block_id] = block
        return block

    def get(self, block_id: str) -> Optional[BlockSpec]:
        return self._blocks.get(block_id)

    def require(self, block_id: str) -> BlockSpec:
        b = self._blocks.get(block_id)
        if b is None:
            raise BlockNotFoundError(f"block_id '{block_id}' 不存在")
        return b

    def list_all(self) -> List[BlockSpec]:
        return list(self._blocks.values())

    def list_by_type(self, block_type: str) -> List[BlockSpec]:
        return [b for b in self._blocks.values() if b.block_type.value == block_type]

    def list_by_category(self, category: str) -> List[BlockSpec]:
        # block 没有 category 字段，按 block_type 过滤
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
                    errors.append(f"block '{block.block_id}' 引用不存在的 source '{ref}'")
        return errors

    def validate_factor_refs(self, factor_registry: FactorRegistry) -> List[str]:
        """校验 block 引用的 factor_id 是否存在于 factor_registry."""
        errors: List[str] = []
        for block in self._blocks.values():
            refs = block.input_factor_refs or []
            for ref in refs:
                if factor_registry.get(ref) is None:
                    errors.append(f"block '{block.block_id}' 引用不存在的 factor '{ref}'")
        return errors

    def validate_parameter_space(self) -> List[str]:
        """校验参数空间边界."""
        errors: List[str] = []
        for block in self._blocks.values():
            for name, space in block.parameter_space.items():
                param = block.parameters.get(name)
                if param is None:
                    errors.append(f"block '{block.block_id}' parameter_space '{name}' 无对应 parameter")
                    continue
                if space.mode.value == "range":
                    if param.range_min is not None and space.min < param.range_min:
                        errors.append(
                            f"block '{block.block_id}' '{name}' space.min {space.min} < param.range_min {param.range_min}"
                        )
                    if param.range_max is not None and space.max > param.range_max:
                        errors.append(
                            f"block '{block.block_id}' '{name}' space.max {space.max} > param.range_max {param.range_max}"
                        )
        return errors

    def validate_market_scope(self) -> List[str]:
        """校验 market_scope 非空."""
        errors: List[str] = []
        for block in self._blocks.values():
            if not block.market_scope:
                errors.append(f"block '{block.block_id}' market_scope 为空")
        return errors

    def validate_no_unsafe_context(self) -> List[str]:
        """校验需要 backtest context 的 block 被正确标注.

        不阻塞，仅返回警告列表。
        """
        warnings: List[str] = []
        for block in self._blocks.values():
            from hermass_platform.factors.block_schema import ContextRequirement
            if ContextRequirement.BACKTEST in block.required_context:
                warnings.append(
                    f"block '{block.block_id}' 需要 BACKTEST 上下文，Preview 可能受限"
                )
        return warnings


class RegistryValidator:
    """跨 registry 统一校验器."""

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
        """执行全部跨 registry 校验."""
        return {
            "factor_source_refs": self.factor_registry.validate_source_refs(self.source_registry),
            "block_source_refs": self.block_registry.validate_source_refs(self.source_registry),
            "block_factor_refs": self.block_registry.validate_factor_refs(self.factor_registry),
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
```

---

## File 6: `hermass_platform/factors/catalog_loader.py`

```python
"""YAML catalog 加载器.

负责从 config/factors/*.yaml 加载 Source / Factor / Block / Evidence 元数据。
"""

from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from hermass_platform.factors.block_schema import BlockSpec
from hermass_platform.factors.exceptions import RegistryError
from hermass_platform.factors.factor_schema import FactorSpec
from hermass_platform.factors.registry import (
    BlockRegistry,
    EvidenceRegistry,
    FactorRegistry,
    SourceRegistry,
)
from hermass_platform.factors.source_schema import Evidence, FactorSource


class CatalogLoader:
    """Catalog 加载器."""

    def __init__(self, config_dir: Path) -> None:
        self.config_dir = Path(config_dir)
        self.source_path = self.config_dir / "source_catalog.yaml"
        self.factor_path = self.config_dir / "factor_catalog.yaml"
        self.block_path = self.config_dir / "block_catalog.yaml"
        self.evidence_path = self.config_dir / "evidence_catalog.yaml"

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"catalog 文件不存在: {path}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_sources(self) -> List[FactorSource]:
        data = self._load_yaml(self.source_path)
        items = data.get("sources", [])
        return [FactorSource.model_validate(item) for item in items]

    def load_factors(self) -> List[FactorSpec]:
        data = self._load_yaml(self.factor_path)
        items = data.get("factors", [])
        return [FactorSpec.model_validate(item) for item in items]

    def load_blocks(self) -> List[BlockSpec]:
        data = self._load_yaml(self.block_path)
        items = data.get("blocks", [])
        return [BlockSpec.model_validate(item) for item in items]

    def load_evidence(self) -> List[Evidence]:
        data = self._load_yaml(self.evidence_path)
        items = data.get("evidence", [])
        return [Evidence.model_validate(item) for item in items]

    def load_all(
        self,
    ) -> Tuple[SourceRegistry, FactorRegistry, BlockRegistry, EvidenceRegistry]:
        """加载全部 catalog 并返回已填充的 registries."""
        source_registry = SourceRegistry()
        factor_registry = FactorRegistry()
        block_registry = BlockRegistry()
        evidence_registry = EvidenceRegistry()

        for src in self.load_sources():
            source_registry.register(src)

        for fac in self.load_factors():
            factor_registry.register(fac)

        for blk in self.load_blocks():
            block_registry.register(blk)

        for ev in self.load_evidence():
            evidence_registry.register(ev)

        return source_registry, factor_registry, block_registry, evidence_registry


def load_catalogs(config_dir: Path) -> Tuple[SourceRegistry, FactorRegistry, BlockRegistry, EvidenceRegistry]:
    """便捷函数：从 config 目录加载所有 catalog."""
    return CatalogLoader(config_dir).load_all()
```

---

## File 7: `config/factors/source_catalog.yaml`

```yaml
# 因子来源 Catalog
# 至少 10 个示例条目

sources:
  - source_id: sqx_b143
    source_type: strategy_generator
    name: StrategyQuant X Build 143
    url_or_local_ref: https://strategyquant.com/doc/build-143-changelog
    reliability: high
    license_notes: 商业软件，仅参考 block 设计思想，不复制源码，不执行外部 snippets
    applicable_markets:
      - A_SHARE
      - US_EQUITY
      - FUTURES
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - signal_blocks
      - entry_blocks
      - exit_blocks
      - robustness

  - source_id: qlib_alpha158
    source_type: open_quant_framework
    name: Qlib Alpha158
    url_or_local_ref: https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py
    reliability: high
    license_notes: MIT License，可自由参考实现
    applicable_markets:
      - A_SHARE
      - US_EQUITY
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - cross_sectional
      - alpha_features

  - source_id: aqr_quality
    source_type: institutional_factor_research
    name: AQR Quality Factor Research
    url_or_local_ref: https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk
    reliability: high
    license_notes: 学术论文公开，因子定义可自由实现
    applicable_markets:
      - GLOBAL
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - quality
      - style_factor

  - source_id: fama_french
    source_type: academic_empirical
    name: Fama-French Factor Models
    url_or_local_ref: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
    reliability: high
    license_notes: 学术数据公开使用，需注明来源
    applicable_markets:
      - GLOBAL
      - US_EQUITY
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - size
      - value
      - momentum
      - profitability

  - source_id: fundamental_data
    source_type: fundamental
    name: A 股财务报表数据
    url_or_local_ref: config/data/fundamental/README.md
    reliability: medium
    license_notes: 需通过 Tushare / iFinD / Wind 等数据商授权获取
    applicable_markets:
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - valuation
      - profitability
      - growth

  - source_id: news_sentiment_api
    source_type: news_event_sentiment
    name: 新闻公告情绪数据
    url_or_local_ref: internal/data/news_sentiment_pipeline.md
    reliability: low
    license_notes: NLP 模型输出，仅作结构化抽取，不直接产生交易建议
    applicable_markets:
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - sentiment
      - nlp

  - source_id: blackwolf_moneyflow
    source_type: money_flow_microstructure
    name: 黑狼资金流数据
    url_or_local_ref: internal/data/blackwolf/README.md
    reliability: high
    license_notes: 内部数据，A 股日频主力/大单/中单/小单/主买主卖
    applicable_markets:
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - money_flow
      - a_share

  - source_id: minervini_vcp
    source_type: trader_methodology
    name: Mark Minervini SEPA / VCP
    url_or_local_ref: https://minervini.com/book-trade-like-a-stock-market-wizard
    reliability: medium
    license_notes: 交易方法论，拆分为 observable blocks 后使用
    applicable_markets:
      - US_EQUITY
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - trader_methodology
      - vcp
      - breakout

  - source_id: behavioral_finance
    source_type: behavioral_psychology
    name: 行为金融学经典研究
    url_or_local_ref: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1570484
    reliability: medium
    license_notes: 学术研究公开，需转为可观测 proxy
    applicable_markets:
      - GLOBAL
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - overreaction
      - momentum
      - crowdedness

  - source_id: hermass_statecube
    source_type: hermass_native
    name: Hermass State Cube
    url_or_local_ref: internal/hermass/state_cube/README.md
    reliability: high
    license_notes: Hermass 自有知识产权
    applicable_markets:
      - A_SHARE
      - ETF
      - INDEX
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - state_cube
      - multi_timeframe
      - native

  - source_id: wyckoff_method
    source_type: trader_methodology
    name: Wyckoff Method
    url_or_local_ref: https://wyckoffanalytics.com/wyckoff-method/
    reliability: medium
    license_notes: 公开交易方法论，拆分为 observable blocks 后使用
    applicable_markets:
      - US_EQUITY
      - A_SHARE
    imported_at: "2026-06-06T00:00:00Z"
    tags:
      - wyckoff
      - accumulation
      - distribution
```

---

## File 8: `config/factors/factor_catalog.yaml`

```yaml
# 因子 Catalog
# 至少 10 个示例条目，覆盖 L1-L5

factors:
  - factor_id: rsi_14
    name: RSI 14
    name_en: Relative Strength Index 14
    category: technical_momentum
    level: L1
    frequency: D1
    inputs:
      - close
    required_tables:
      - daily_bars
    required_columns:
      - close
    output_type: numeric
    window: 14
    direction: neutral
    normalization:
      - none
    neutralization: []
    compute_engine: polars
    preview_support: fully_supported
    dsl_exposure: exposed
    status: validated
    version: "0.1.0"
    source_refs:
      - qlib_alpha158
    evidence_level: E2
    data_availability: available
    future_leakage_risk: none
    a_share_notes: 使用收盘价计算，无未来函数

  - factor_id: atr_14
    name: ATR 14
    name_en: Average True Range 14
    category: technical_volatility
    level: L1
    frequency: D1
    inputs:
      - high
      - low
      - close
    required_tables:
      - daily_bars
    required_columns:
      - high
      - low
      - close
    output_type: numeric
    window: 14
    direction: neutral
    normalization: []
    neutralization: []
    compute_engine: polars
    preview_support: fully_supported
    dsl_exposure: exposed
    status: validated
    version: "0.1.0"
    source_refs:
      - qlib_alpha158
    evidence_level: E2
    data_availability: available
    future_leakage_risk: none
    a_share_notes: 使用当日 high/low/close，无未来函数

  - factor_id: macd_hist
    name: MACD 柱状图
    name_en: MACD Histogram
    category: technical_trend
    level: L1
    frequency: D1
    inputs:
      - close
    required_tables:
      - daily_bars
    required_columns:
      - close
    output_type: numeric
    direction: neutral
    normalization: []
    neutralization: []
    compute_engine: polars
    preview_support: fully_supported
    dsl_exposure: exposed
    status: validated
    version: "0.1.0"
    source_refs:
      - qlib_alpha158
    evidence_level: E2
    data_availability: available
    future_leakage_risk: none
    a_share_notes: 标准 MACD 计算，使用收盘价

  - factor_id: return_20d_rank
    name: 20日收益率横截面排名
    name_en: 20-Day Return Cross-Sectional Rank
    category: cross_sectional_momentum
    level: L2
    frequency: D1
    inputs:
      - close
    required_tables:
      - daily_bars
    required_columns:
      - close
      - symbol
      - date
    output_type: numeric
    window: 20
    direction: higher_better
    normalization:
      - rank_pct
    neutralization:
      - industry_optional
    compute_engine: polars
    preview_support: fully_supported
    dsl_exposure: candidate
    status: research
    version: "0.1.0"
    source_refs:
      - qlib_alpha158
    evidence_level: E2
    data_availability: available
    future_leakage_risk: none
    a_share_notes: 使用收盘价计算收益率，横截面排名需按交易日分组

  - factor_id: quality_roe_ttm
    name: ROE TTM
    name_en: Return on Equity TTM
    category: fundamental_quality
    level: L3
    frequency: D1
    inputs:
      - net_profit_ttm
      - equity
      - announcement_date
    required_tables:
      - financial_statements
      - daily_bars
    required_columns:
      - net_profit_ttm
      - equity
      - announcement_date
    output_type: numeric
    direction: higher_better
    normalization:
      - winsorize
      - zscore
    neutralization:
      - industry_optional
    compute_engine: polars
    preview_support: partial
    dsl_exposure: none
    status: research
    version: "0.1.0"
    source_refs:
      - aqr_quality
      - fundamental_data
    evidence_level: E1
    data_availability: available
    future_leakage_risk: high
    a_share_notes: 必须使用 announcement_date 对齐，禁止使用 fiscal_period_end，否则会产生未来函数

  - factor_id: value_pb
    name: 市净率
    name_en: Price-to-Book Ratio
    category: fundamental_valuation
    level: L3
    frequency: D1
    inputs:
      - close
      - book_value
    required_tables:
      - financial_statements
      - daily_bars
    required_columns:
      - close
      - book_value
      - announcement_date
    output_type: numeric
    direction: lower_better
    normalization:
      - winsorize
      - zscore
    neutralization:
      - industry_optional
    compute_engine: polars
    preview_support: partial
    dsl_exposure: none
    status: research
    version: "0.1.0"
    source_refs:
      - fama_french
      - fundamental_data
    evidence_level: E1
    data_availability: available
    future_leakage_risk: high
    a_share_notes: 必须使用 announcement_date 对齐账面价值

  - factor_id: main_force_inflow
    name: 主力净流入
    name_en: Main Force Net Inflow
    category: money_flow
    level: L4
    frequency: D1
    inputs:
      - main_force_inflow
    required_tables:
      - moneyflow_daily
    required_columns:
      - main_force_inflow
    output_type: numeric
    direction: higher_better
    normalization:
      - rank_pct
    neutralization: []
    compute_engine: polars
    preview_support: fully_supported
    dsl_exposure: candidate
    status: research
    version: "0.1.0"
    source_refs:
      - blackwolf_moneyflow
    evidence_level: E2
    data_availability: available
    future_leakage_risk: none
    a_share_notes: 黑狼资金流数据，日频更新

  - factor_id: d1_state
    name: D1 State
    name_en: Daily State
    category: state
    level: L5
    frequency: D1
    inputs:
      - open
      - high
      - low
      - close
      - volume
    required_tables:
      - daily_bars
    required_columns:
      - open
      - high
      - low
      - close
      - volume
    output_type: categorical
    direction: neutral
    normalization: []
    neutralization: []
    compute_engine: polars
    preview_support: fully_supported
    dsl_exposure: exposed
    status: production
    version: "1.0.0"
    source_refs:
      - hermass_statecube
    evidence_level: E3
    data_availability: available
    future_leakage_risk: none
    a_share_notes: Hermass 自有 State Cube，使用当日 OHLCV 计算

  - factor_id: limit_up_sentiment
    name: 涨停情绪指数
    name_en: Limit-Up Sentiment Index
    category: behavioral_sentiment
    level: L2
    frequency: D1
    inputs:
      - limit_up_count
      - total_stocks
    required_tables:
      - market_daily
    required_columns:
      - limit_up_count
      - total_stocks
    output_type: numeric
    direction: neutral
    normalization:
      - zscore
    neutralization: []
    compute_engine: polars
    preview_support: fully_supported
    dsl_exposure: candidate
    status: research
    version: "0.1.0"
    source_refs:
      - behavioral_finance
    evidence_level: E2
    data_availability: available
    future_leakage_risk: none
    a_share_notes: 使用当日涨停家数，收盘后计算

  - factor_id: news_sentiment_score
    name: 新闻情绪得分
    name_en: News Sentiment Score
    category: sentiment
    level: L4
    frequency: D1
    inputs:
      - news_text
    required_tables:
      - news_data
    required_columns:
      - news_text
      - publish_time
    output_type: numeric
    direction: higher_better
    normalization:
      - zscore
    neutralization: []
    compute_engine: pandas
    preview_support: partial
    dsl_exposure: none
    status: research
    version: "0.1.0"
    source_refs:
      - news_sentiment_api
    evidence_level: E1
    data_availability: partial
    future_leakage_risk: low
    a_share_notes: NLP 模型输出，需处理发布时间和新闻去重

  - factor_id: beta_to_index
    name: 市值 Beta
    name_en: Beta to Market Index
    category: cross_sectional_risk
    level: L2
    frequency: D1
    inputs:
      - close
      - index_close
    required_tables:
      - daily_bars
      - index_daily
    required_columns:
      - close
      - index_close
    output_type: numeric
    window: 252
    direction: neutral
    normalization: []
    neutralization: []
    compute_engine: polars
    preview_support: partial
    dsl_exposure: none
    status: research
    version: "0.1.0"
    source_refs:
      - qlib_alpha158
    evidence_level: E2
    data_availability: available
    future_leakage_risk: none
    a_share_notes: 使用滚动 252 日收益率对指数做回归
```

---

## File 9: `config/factors/block_catalog.yaml`

```yaml
# Block Catalog
# 至少 10 个示例条目，覆盖 signal/entry/exit/order/filter/robustness

blocks:
  - block_id: signal_indicator_cross_threshold
    block_type: signal
    name: 指标上穿阈值
    name_en: Indicator Cross Above Threshold
    description: 任意 numeric factor 上穿指定阈值时触发信号
    input_factor_types:
      - numeric
    parameters:
      factor_id:
        name: factor_id
        param_type: factor_ref
        description: 引用的因子 ID
        required: true
        factor_scope:
          - technical
          - state
          - money_flow
      operator:
        name: operator
        param_type: enum
        description: 比较操作符
        required: true
        enum_values:
          - cross_up
          - cross_down
          - ">"
          - "<"
          - ">="
          - "<="
      threshold:
        name: threshold
        param_type: float
        description: 阈值
        required: true
        range_min: -10.0
        range_max: 10.0
    parameter_space:
      factor_id:
        mode: choice
      threshold:
        mode: range
        min: -2.0
        max: 2.0
        step: 0.1
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns: []
    required_context:
      - none
    preview_support: fully_supported
    dsl_output: factor_threshold
    robustness_role: signal_timing
    market_scope:
      - A_SHARE
      - US_EQUITY
      - ETF
    status: validated
    version: "0.1.0"
    source_refs:
      - sqx_b143
    evidence_level: E2
    generation_weight: 1.0
    production_gate: candidate

  - block_id: signal_factor_cross
    block_type: signal
    name: 指标金叉
    name_en: Factor Golden Cross
    description: factor_a 上穿 factor_b 时触发
    input_factor_types:
      - numeric
    parameters:
      factor_a:
        name: factor_a
        param_type: factor_ref
        required: true
      factor_b:
        name: factor_b
        param_type: factor_ref
        required: true
    parameter_space:
      factor_a:
        mode: choice
      factor_b:
        mode: choice
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_context:
      - none
    preview_support: fully_supported
    dsl_output: factor_cross
    market_scope:
      - A_SHARE
      - ETF
    status: validated
    version: "0.1.0"
    source_refs:
      - sqx_b143
    evidence_level: E2
    generation_weight: 1.0
    production_gate: candidate

  - block_id: entry_breakout
    block_type: entry
    name: 突破入场
    name_en: Breakout Entry
    description: 价格突破 N 日高点且放量时入场
    input_factor_types:
      - numeric
      - boolean
    input_factor_refs:
      - close
      - high
      - volume
    parameters:
      lookback:
        name: lookback
        param_type: integer
        description: 回看周期
        required: true
        range_min: 5
        range_max: 60
        default: 20
      volume_multiplier:
        name: volume_multiplier
        param_type: float
        description: 成交量倍数
        required: true
        range_min: 1.0
        range_max: 3.0
        default: 1.5
    parameter_space:
      lookback:
        mode: range
        min: 10
        max: 60
        step: 5
      volume_multiplier:
        mode: range
        min: 1.0
        max: 3.0
        step: 0.25
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - close
      - high
      - volume
    required_context:
      - none
    preview_support: fully_supported
    dsl_output: block_entry
    robustness_role: entry_timing
    market_scope:
      - A_SHARE
      - US_EQUITY
    status: candidate
    version: "0.1.0"
    source_refs:
      - sqx_b143
      - minervini_vcp
    methodology_refs:
      - minervini_vcp
    evidence_level: E1
    generation_weight: 0.8
    production_gate: blocked

  - block_id: exit_fixed_stop_loss
    block_type: exit
    name: 固定止损出场
    name_en: Fixed Stop Loss Exit
    description: 价格跌破入场价一定比例时止损出场
    input_factor_types:
      - numeric
    parameters:
      stop_pct:
        name: stop_pct
        param_type: float
        description: 止损百分比
        required: true
        range_min: 0.01
        range_max: 0.5
        default: 0.08
    parameter_space:
      stop_pct:
        mode: range
        min: 0.05
        max: 0.15
        step: 0.01
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - close
    required_context:
      - backtest
    preview_support: partial
    dsl_output: block_exit
    robustness_role: risk_control
    market_scope:
      - A_SHARE
      - US_EQUITY
      - ETF
    status: validated
    version: "0.1.0"
    source_refs:
      - sqx_b143
    evidence_level: E2
    generation_weight: 1.0
    production_gate: candidate

  - block_id: exit_atr_trailing_stop
    block_type: exit
    name: ATR 追踪止损
    name_en: ATR Trailing Stop
    description: 基于 ATR 的追踪止损
    input_factor_types:
      - numeric
    input_factor_refs:
      - atr_14
    parameters:
      atr_multiplier:
        name: atr_multiplier
        param_type: float
        description: ATR 乘数
        required: true
        range_min: 1.0
        range_max: 5.0
        default: 2.0
    parameter_space:
      atr_multiplier:
        mode: range
        min: 1.5
        max: 3.5
        step: 0.25
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - close
      - high
      - low
    required_context:
      - backtest
      - position
    preview_support: partial
    dsl_output: block_exit
    robustness_role: risk_control
    market_scope:
      - A_SHARE
      - US_EQUITY
    status: candidate
    version: "0.1.0"
    source_refs:
      - sqx_b143
    evidence_level: E2
    generation_weight: 0.9
    production_gate: candidate

  - block_id: order_market
    block_type: order
    name: 市价订单
    name_en: Market Order
    description: 下一根 bar 开盘价执行
    input_factor_types: []
    parameters:
      slippage_pct:
        name: slippage_pct
        param_type: float
        description: 滑点百分比
        required: true
        range_min: 0.0
        range_max: 0.01
        default: 0.001
    parameter_space:
      slippage_pct:
        mode: range
        min: 0.0
        max: 0.005
        step: 0.0005
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - open
    required_context:
      - backtest
    preview_support: not_supported
    dsl_output: block_order
    market_scope:
      - A_SHARE
      - US_EQUITY
      - ETF
    status: validated
    version: "0.1.0"
    source_refs:
      - sqx_b143
    evidence_level: E2
    generation_weight: 1.0
    production_gate: candidate

  - block_id: filter_limit_up
    block_type: filter
    name: 涨停过滤
    name_en: Limit-Up Filter
    description: 过滤已涨停无法买入的股票
    input_factor_types:
      - boolean
    parameters: {}
    parameter_space: {}
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - close
      - limit_up_price
    required_context:
      - none
    preview_support: fully_supported
    dsl_output: block_filter
    market_scope:
      - A_SHARE
    status: production
    version: "1.0.0"
    source_refs:
      - sqx_b143
      - hermass_statecube
    evidence_level: E4
    generation_weight: 1.0
    production_gate: approved

  - block_id: filter_liquidity
    block_type: filter
    name: 流动性过滤
    name_en: Liquidity Filter
    description: 过滤成交额低于阈值的股票
    input_factor_types:
      - numeric
    parameters:
      min_amount:
        name: min_amount
        param_type: float
        description: 最小成交额（万元）
        required: true
        range_min: 100
        range_max: 10000
        default: 1000
    parameter_space:
      min_amount:
        mode: range
        min: 500
        max: 5000
        step: 500
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - amount
    required_context:
      - none
    preview_support: fully_supported
    dsl_output: block_filter
    market_scope:
      - A_SHARE
    status: validated
    version: "0.1.0"
    source_refs:
      - blackwolf_moneyflow
    evidence_level: E2
    generation_weight: 1.0
    production_gate: candidate

  - block_id: sizing_fixed_pct
    block_type: money_management
    name: 固定仓位比例
    name_en: Fixed Percentage Sizing
    description: 每笔交易使用账户固定百分比
    input_factor_types:
      - numeric
    parameters:
      pct:
        name: pct
        param_type: float
        description: 仓位百分比
        required: true
        range_min: 0.01
        range_max: 1.0
        default: 0.2
    parameter_space:
      pct:
        mode: range
        min: 0.05
        max: 0.25
        step: 0.05
    weight: 1.0
    enabled: true
    required_tables: []
    required_columns: []
    required_context:
      - portfolio
    preview_support: not_supported
    dsl_output: block_sizing
    market_scope:
      - A_SHARE
      - US_EQUITY
    status: validated
    version: "0.1.0"
    source_refs:
      - sqx_b143
    evidence_level: E2
    generation_weight: 1.0
    production_gate: candidate

  - block_id: robustness_walk_forward
    block_type: robustness
    name: Walk-Forward 稳健块
    name_en: Walk-Forward Robustness
    description: 按时间序列做滚动样本内外测试
    input_factor_types:
      - numeric
    parameters:
      train_pct:
        name: train_pct
        param_type: float
        description: 训练集占比
        required: true
        range_min: 0.5
        range_max: 0.8
        default: 0.7
      windows:
        name: windows
        param_type: integer
        description: 滚动窗口数
        required: true
        range_min: 3
        range_max: 10
        default: 5
    parameter_space:
      train_pct:
        mode: range
        min: 0.6
        max: 0.8
        step: 0.05
      windows:
        mode: range
        min: 3
        max: 6
        step: 1
    weight: 1.0
    enabled: false
    required_tables: []
    required_columns: []
    required_context:
      - backtest
    preview_support: not_supported
    dsl_output: block_robustness
    market_scope:
      - A_SHARE
      - US_EQUITY
    status: research
    version: "0.1.0"
    source_refs:
      - sqx_b143
    evidence_level: E3
    generation_weight: 0.5
    production_gate: blocked
    robustness_tests: []

  - block_id: vcp_contraction_detector
    block_type: signal
    name: VCP 收缩检测
    name_en: VCP Contraction Detector
    description: 检测波动率收缩模式，用于 Minervini VCP 策略
    input_factor_types:
      - numeric
    input_factor_refs:
      - atr_14
      - close
      - volume
    parameters:
      contraction_periods:
        name: contraction_periods
        param_type: integer
        description: 收缩阶段数（2-4）
        required: true
        range_min: 2
        range_max: 4
        default: 3
      volume_dry_up_pct:
        name: volume_dry_up_pct
        param_type: float
        description: 成交量萎缩比例
        required: true
        range_min: 0.3
        range_max: 0.8
        default: 0.5
    parameter_space:
      contraction_periods:
        mode: range
        min: 2
        max: 4
        step: 1
      volume_dry_up_pct:
        mode: range
        min: 0.4
        max: 0.7
        step: 0.1
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - close
      - volume
      - high
      - low
    required_context:
      - none
    preview_support: partial
    dsl_output: block_signal
    market_scope:
      - A_SHARE
      - US_EQUITY
    status: research
    version: "0.1.0"
    source_refs:
      - minervini_vcp
      - sqx_b143
    methodology_refs:
      - minervini_vcp
    evidence_level: E1
    generation_weight: 0.7
    production_gate: blocked

  - block_id: wyckoff_spring_test
    block_type: signal
    name: Wyckoff 弹簧测试
    name_en: Wyckoff Spring Test
    description: 价格短暂跌破支撑后快速收回，识别吸筹区弹簧
    input_factor_types:
      - numeric
    parameters:
      support_lookback:
        name: support_lookback
        param_type: integer
        description: 支撑线回看周期
        required: true
        range_min: 10
        range_max: 60
        default: 20
      retrace_pct:
        name: retrace_pct
        param_type: float
        description: 跌破支撑最大百分比
        required: true
        range_min: 0.01
        range_max: 0.05
        default: 0.03
    parameter_space:
      support_lookback:
        mode: range
        min: 20
        max: 40
        step: 5
      retrace_pct:
        mode: range
        min: 0.02
        max: 0.04
        step: 0.005
    weight: 1.0
    enabled: true
    required_tables:
      - daily_bars
    required_columns:
      - close
      - low
      - volume
    required_context:
      - none
    preview_support: partial
    dsl_output: block_signal
    market_scope:
      - A_SHARE
      - US_EQUITY
    status: research
    version: "0.1.0"
    source_refs:
      - wyckoff_method
    methodology_refs:
      - wyckoff
    evidence_level: E1
    generation_weight: 0.6
    production_gate: blocked
```

---

## File 10: `config/factors/evidence_catalog.yaml`

```yaml
# Evidence Catalog
# 至少 10 个证据记录示例

evidence:
  - evidence_id: ev_rsi_14_v01
    target_id: rsi_14
    target_type: factor
    evidence_level: E2
    evidence_type: backtest
    metric_refs: []
    validation_status: passed
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes: []
    validator_id: qoder_architect
    notes: 技术指标计算正确性已验证，IC 评估待补充

  - evidence_id: ev_return_20d_rank_v01
    target_id: return_20d_rank
    target_type: factor
    evidence_level: E2
    evidence_type: backtest
    metric_refs: []
    validation_status: in_progress
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes:
      - regime_dependent
    validator_id: kimi_research_engineer
    notes: 横截面排名计算正确，IC 测试进行中

  - evidence_id: ev_quality_roe_ttm_v01
    target_id: quality_roe_ttm
    target_type: factor
    evidence_level: E1
    evidence_type: literature
    metric_refs: []
    validation_status: pending
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes:
      - lookahead_risk
    validator_id: kimi_research_engineer
    notes: 文献支持存在，但 A 股数据需处理公告日期未来函数

  - evidence_id: ev_main_force_inflow_v01
    target_id: main_force_inflow
    target_type: factor
    evidence_level: E2
    evidence_type: backtest
    metric_refs: []
    validation_status: passed
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes: []
    validator_id: qoder_architect
    notes: 黑狼资金流数据可用，计算正确性已验证

  - evidence_id: ev_d1_state_v01
    target_id: d1_state
    target_type: factor
    evidence_level: E3
    evidence_type: backtest
    metric_refs:
      - metric: coverage
        value: 0.95
        threshold: 0.80
        passed: true
      - metric: stability
        value: 0.88
        threshold: 0.80
        passed: true
    validation_status: passed
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes: []
    validator_id: qoder_architect
    notes: State Cube 已用于现有策略，稳定性通过

  - evidence_id: ev_signal_indicator_cross_threshold_v01
    target_id: signal_indicator_cross_threshold
    target_type: block
    evidence_level: E2
    evidence_type: backtest
    metric_refs: []
    validation_status: passed
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes: []
    validator_id: qoder_architect

  - evidence_id: ev_entry_breakout_v01
    target_id: entry_breakout
    target_type: block
    evidence_level: E1
    evidence_type: literature
    metric_refs: []
    validation_status: pending
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes:
      - data_snooping
    validator_id: kimi_research_engineer
    notes: Minervini VCP 方法论支持，待回测验证

  - evidence_id: ev_exit_fixed_stop_loss_v01
    target_id: exit_fixed_stop_loss
    target_type: block
    evidence_level: E2
    evidence_type: backtest
    metric_refs: []
    validation_status: passed
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes:
      - cost_sensitive
    validator_id: qoder_architect

  - evidence_id: ev_filter_limit_up_v01
    target_id: filter_limit_up
    target_type: block
    evidence_level: E4
    evidence_type: backtest
    metric_refs:
      - metric: false_positive_rate
        value: 0.02
        threshold: 0.05
        passed: true
    validation_status: passed
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes: []
    validator_id: qoder_architect

  - evidence_id: ev_robustness_walk_forward_v01
    target_id: robustness_walk_forward
    target_type: block
    evidence_level: E3
    evidence_type: walk_forward
    metric_refs: []
    validation_status: pending
    last_validated_at: "2026-06-05T00:00:00Z"
    failure_modes:
      - short_sample
    validator_id: kimi_research_engineer
```

---

## Tests

至少 30 个 pytest 测试点，覆盖 schema、registry、loader、跨 registry 校验。

### Test File 1: `test_source_schema.py` (5 tests)

```python
import pytest
from hermass_platform.factors.source_schema import (
    ApplicableMarket,
    Evidence,
    EvidenceLevel,
    EvidenceType,
    FactorSource,
    FailureMode,
    MetricRef,
    Reliability,
    SourceType,
    ValidationStatus,
)


class TestFactorSource:
    def test_valid_source(self):
        src = FactorSource(
            source_id="sqx_b143",
            source_type=SourceType.STRATEGY_GENERATOR,
            name="SQX B143",
            url_or_local_ref="https://strategyquant.com",
            reliability=Reliability.HIGH,
            license_notes="commercial",
            applicable_markets=[ApplicableMarket.A_SHARE],
        )
        assert src.source_id == "sqx_b143"

    def test_missing_applicable_markets(self):
        with pytest.raises(ValueError):
            FactorSource(
                source_id="test",
                source_type=SourceType.OPEN_QUANT_FRAMEWORK,
                name="Test",
                url_or_local_ref="x",
                reliability=Reliability.HIGH,
                license_notes="x",
                applicable_markets=[],
            )

    def test_invalid_source_type(self):
        with pytest.raises(ValueError):
            FactorSource(
                source_id="test",
                source_type="invalid_type",  # type: ignore
                name="Test",
                url_or_local_ref="x",
                reliability=Reliability.HIGH,
                license_notes="x",
                applicable_markets=[ApplicableMarket.A_SHARE],
            )

    def test_evidence_level_enum(self):
        assert EvidenceLevel.E4.value == "E4"
        assert EvidenceLevel.E6.value == "E6"

    def test_metric_ref_validation(self):
        m = MetricRef(metric="RankIC_mean", value=0.05, threshold=0.02, passed=True)
        assert m.passed is True
```

### Test File 2: `test_factor_schema.py` (8 tests)

```python
import pytest
from hermass_platform.factors.factor_schema import (
    DataAvailability,
    FactorSpec,
    FactorStatus,
    FutureLeakageRisk,
    ProductionGate,
    derive_factor_gate,
)
from hermass_platform.factors.source_schema import EvidenceLevel


class TestFactorSpec:
    def _base(self, **overrides):
        defaults = dict(
            factor_id="test_factor",
            name="测试因子",
            category="technical",
            level="L1",
            frequency="D1",
            output_type="numeric",
            direction="higher_better",
            source_refs=["qlib_alpha158"],
            a_share_notes="测试说明",
        )
        defaults.update(overrides)
        return defaults

    def test_valid_factor(self):
        fac = FactorSpec(**self._base())
        assert fac.factor_id == "test_factor"

    def test_missing_source_refs(self):
        with pytest.raises(ValueError):
            FactorSpec(**self._base(source_refs=[]))

    def test_empty_a_share_notes(self):
        with pytest.raises(ValueError):
            FactorSpec(**self._base(a_share_notes=""))

    def test_production_gate_blocked_e0(self):
        fac = FactorSpec(**self._base(evidence_level=EvidenceLevel.E0))
        assert fac.production_gate == ProductionGate.BLOCKED

    def test_production_gate_candidate_e4(self):
        fac = FactorSpec(
            **self._base(
                evidence_level=EvidenceLevel.E4,
                data_availability=DataAvailability.AVAILABLE,
                future_leakage_risk=FutureLeakageRisk.NONE,
                status=FactorStatus.VALIDATED,
            )
        )
        assert fac.production_gate == ProductionGate.CANDIDATE

    def test_production_gate_approved_e5(self):
        fac = FactorSpec(
            **self._base(
                evidence_level=EvidenceLevel.E5,
                data_availability=DataAvailability.AVAILABLE,
                future_leakage_risk=FutureLeakageRisk.NONE,
                status=FactorStatus.PRODUCTION,
            )
        )
        assert fac.production_gate == ProductionGate.APPROVED

    def test_future_leakage_high_blocked(self):
        fac = FactorSpec(
            **self._base(
                evidence_level=EvidenceLevel.E5,
                future_leakage_risk=FutureLeakageRisk.HIGH,
            )
        )
        assert fac.production_gate == ProductionGate.BLOCKED

    def test_data_unavailable_blocked(self):
        fac = FactorSpec(
            **self._base(
                evidence_level=EvidenceLevel.E5,
                data_availability=DataAvailability.UNAVAILABLE,
            )
        )
        assert fac.production_gate == ProductionGate.BLOCKED

    def test_derive_factor_gate_validation_failed(self):
        gate = derive_factor_gate(
            evidence_level=EvidenceLevel.E6,
            validation_status="failed",
            data_availability=DataAvailability.AVAILABLE,
            future_leakage_risk=FutureLeakageRisk.NONE,
            status=FactorStatus.PRODUCTION,
        )
        assert gate == ProductionGate.BLOCKED
```

### Test File 3: `test_block_schema.py` (7 tests)

```python
import pytest
from hermass_platform.factors.block_schema import (
    BlockSpec,
    BlockType,
    ContextRequirement,
    ParameterSpace,
    ParameterSpec,
)
from hermass_platform.factors.source_schema import EvidenceLevel


class TestBlockSchema:
    def _base(self, **overrides):
        defaults = dict(
            block_id="test_block",
            block_type=BlockType.SIGNAL,
            name="测试 Block",
            source_refs=["sqx_b143"],
            market_scope=["A_SHARE"],
        )
        defaults.update(overrides)
        return defaults

    def test_valid_block(self):
        blk = BlockSpec(**self._base())
        assert blk.block_id == "test_block"

    def test_missing_source_refs(self):
        with pytest.raises(ValueError):
            BlockSpec(**self._base(source_refs=[]))

    def test_generation_weight_out_of_range(self):
        with pytest.raises(ValueError):
            BlockSpec(**self._base(generation_weight=1.5))

    def test_parameter_space_subset(self):
        with pytest.raises(ValueError):
            BlockSpec(
                **self._base(
                    parameter_space={
                        "unknown_param": ParameterSpace(mode="choice", choices=[1, 2])
                    }
                )
            )

    def test_exit_block_backtest_context(self):
        blk = BlockSpec(
            **self._base(
                block_id="exit_test",
                block_type=BlockType.EXIT,
                required_context=[ContextRequirement.BACKTEST],
            )
        )
        assert ContextRequirement.BACKTEST in blk.required_context

    def test_block_evidence_e1_blocked(self):
        blk = BlockSpec(**self._base(evidence_level=EvidenceLevel.E1))
        assert blk.production_gate == "blocked"

    def test_block_evidence_e4_candidate(self):
        blk = BlockSpec(**self._base(evidence_level=EvidenceLevel.E4))
        assert blk.production_gate == "candidate"

    def test_parameter_range_validation(self):
        with pytest.raises(ValueError):
            ParameterSpace(mode="range", min=10, max=5, step=1)
```

### Test File 4: `test_registry.py` (12 tests)

```python
import pytest
from hermass_platform.factors.block_schema import BlockSpec, BlockType
from hermass_platform.factors.exceptions import (
    DuplicateFactorError,
    DuplicateSourceError,
    FactorNotFoundError,
    SourceNotFoundError,
)
from hermass_platform.factors.factor_schema import FactorSpec
from hermass_platform.factors.registry import (
    BlockRegistry,
    FactorRegistry,
    RegistryValidator,
    SourceRegistry,
)
from hermass_platform.factors.source_schema import (
    ApplicableMarket,
    FactorSource,
    Reliability,
    SourceType,
)


class TestSourceRegistry:
    def test_register_and_get(self):
        reg = SourceRegistry()
        src = FactorSource(
            source_id="test_src",
            source_type=SourceType.OPEN_QUANT_FRAMEWORK,
            name="Test",
            url_or_local_ref="x",
            reliability=Reliability.HIGH,
            license_notes="x",
            applicable_markets=[ApplicableMarket.A_SHARE],
        )
        reg.register(src)
        assert reg.get("test_src") == src

    def test_duplicate_rejected(self):
        reg = SourceRegistry()
        src = FactorSource(
            source_id="test_src",
            source_type=SourceType.OPEN_QUANT_FRAMEWORK,
            name="Test",
            url_or_local_ref="x",
            reliability=Reliability.HIGH,
            license_notes="x",
            applicable_markets=[ApplicableMarket.A_SHARE],
        )
        reg.register(src)
        with pytest.raises(DuplicateSourceError):
            reg.register(src)

    def test_list_by_type(self):
        reg = SourceRegistry()
        reg.register(
            FactorSource(
                source_id="s1",
                source_type=SourceType.STRATEGY_GENERATOR,
                name="S1",
                url_or_local_ref="x",
                reliability=Reliability.HIGH,
                license_notes="x",
                applicable_markets=[ApplicableMarket.A_SHARE],
            )
        )
        reg.register(
            FactorSource(
                source_id="s2",
                source_type=SourceType.OPEN_QUANT_FRAMEWORK,
                name="S2",
                url_or_local_ref="x",
                reliability=Reliability.HIGH,
                license_notes="x",
                applicable_markets=[ApplicableMarket.A_SHARE],
            )
        )
        assert len(reg.list_by_type("strategy_generator")) == 1


class TestFactorRegistry:
    def _make_factor(self, factor_id="f1", **overrides):
        data = dict(
            factor_id=factor_id,
            name="Test",
            category="technical",
            level="L1",
            frequency="D1",
            output_type="numeric",
            direction="higher_better",
            source_refs=["s1"],
            a_share_notes="x",
        )
        data.update(overrides)
        return FactorSpec(**data)

    def test_register_and_get(self):
        reg = FactorRegistry()
        fac = self._make_factor()
        reg.register(fac)
        assert reg.get("f1") == fac

    def test_duplicate_rejected(self):
        reg = FactorRegistry()
        fac = self._make_factor()
        reg.register(fac)
        with pytest.raises(DuplicateFactorError):
            reg.register(fac)

    def test_list_production_ready_only_approved(self):
        reg = FactorRegistry()
        reg.register(self._make_factor("f_blocked", evidence_level="E1"))
        reg.register(self._make_factor("f_candidate", evidence_level="E4"))
        reg.register(self._make_factor("f_approved", evidence_level="E5"))
        ready = reg.list_production_ready()
        assert len(ready) == 1
        assert ready[0].factor_id == "f_approved"

    def test_validate_source_refs_missing(self):
        reg = FactorRegistry()
        reg.register(self._make_factor("f1", source_refs=["missing_src"]))
        src_reg = SourceRegistry()
        errors = reg.validate_source_refs(src_reg)
        assert len(errors) == 1
        assert "missing_src" in errors[0]


class TestBlockRegistry:
    def _make_block(self, block_id="b1", **overrides):
        data = dict(
            block_id=block_id,
            block_type=BlockType.SIGNAL,
            name="Test",
            source_refs=["s1"],
            market_scope=["A_SHARE"],
        )
        data.update(overrides)
        return BlockSpec(**data)

    def test_register_and_get(self):
        reg = BlockRegistry()
        blk = self._make_block()
        reg.register(blk)
        assert reg.get("b1") == blk

    def test_list_by_type(self):
        reg = BlockRegistry()
        reg.register(self._make_block("b1", block_type=BlockType.SIGNAL))
        reg.register(self._make_block("b2", block_type=BlockType.EXIT))
        assert len(reg.list_by_type("signal")) == 1
        assert len(reg.list_by_type("exit")) == 1

    def test_validate_factor_refs_missing(self):
        reg = BlockRegistry()
        reg.register(self._make_block("b1", input_factor_refs=["missing_factor"]))
        fac_reg = FactorRegistry()
        errors = reg.validate_factor_refs(fac_reg)
        assert len(errors) == 1

    def test_validate_parameter_space_out_of_range(self):
        from hermass_platform.factors.block_schema import ParameterSpec, ParameterSpace

        reg = BlockRegistry()
        blk = BlockSpec(
            block_id="b1",
            block_type=BlockType.SIGNAL,
            name="Test",
            source_refs=["s1"],
            market_scope=["A_SHARE"],
            parameters={
                "p": ParameterSpec(
                    name="p", param_type="float", range_min=0.0, range_max=1.0
                )
            },
            parameter_space={
                "p": ParameterSpace(mode="range", min=-1.0, max=2.0, step=0.1)
            },
        )
        reg.register(blk)
        errors = reg.validate_parameter_space()
        assert len(errors) == 2  # min too low, max too high


class TestRegistryValidator:
    def test_validate_all_cross_registry(self):
        src_reg = SourceRegistry()
        src_reg.register(
            FactorSource(
                source_id="qlib_alpha158",
                source_type=SourceType.OPEN_QUANT_FRAMEWORK,
                name="Qlib",
                url_or_local_ref="x",
                reliability=Reliability.HIGH,
                license_notes="x",
                applicable_markets=[ApplicableMarket.A_SHARE],
            )
        )
        fac_reg = FactorRegistry()
        fac_reg.register(
            FactorSpec(
                factor_id="rsi_14",
                name="RSI",
                category="technical",
                level="L1",
                frequency="D1",
                output_type="numeric",
                direction="neutral",
                source_refs=["qlib_alpha158"],
                a_share_notes="x",
            )
        )
        blk_reg = BlockRegistry()
        blk_reg.register(
            BlockSpec(
                block_id="signal_cross",
                block_type=BlockType.SIGNAL,
                name="Cross",
                source_refs=["qlib_alpha158"],
                market_scope=["A_SHARE"],
                input_factor_refs=["rsi_14"],
            )
        )
        validator = RegistryValidator(src_reg, fac_reg, blk_reg)
        result = validator.validate_all()
        assert result["factor_source_refs"] == []
        assert result["block_source_refs"] == []
        assert result["block_factor_refs"] == []

    def test_list_production_ready(self):
        src_reg = SourceRegistry()
        fac_reg = FactorRegistry()
        blk_reg = BlockRegistry()
        validator = RegistryValidator(src_reg, fac_reg, blk_reg)
        fac_reg.register(
            FactorSpec(
                factor_id="approved_factor",
                name="Approved",
                category="technical",
                level="L1",
                frequency="D1",
                output_type="numeric",
                direction="neutral",
                source_refs=["src"],
                a_share_notes="x",
                evidence_level="E5",
            )
        )
        assert len(validator.list_production_ready_factors()) == 1
```

### Test File 5: `test_catalog_loader.py` (5 tests)

```python
from pathlib import Path

import pytest

from hermass_platform.factors.catalog_loader import CatalogLoader, load_catalogs


class TestCatalogLoader:
    def test_load_sources(self, tmp_path):
        config_dir = tmp_path / "factors"
        config_dir.mkdir()
        (config_dir / "source_catalog.yaml").write_text(
            "sources:\n  - source_id: test\n    source_type: open_quant_framework\n"
            "    name: Test\n    url_or_local_ref: x\n    reliability: high\n"
            "    license_notes: x\n    applicable_markets: [A_SHARE]\n",
            encoding="utf-8",
        )
        loader = CatalogLoader(config_dir)
        sources = loader.load_sources()
        assert len(sources) == 1
        assert sources[0].source_id == "test"

    def test_load_missing_file(self, tmp_path):
        loader = CatalogLoader(tmp_path)
        with pytest.raises(FileNotFoundError):
            loader.load_sources()

    def test_load_all_empty(self, tmp_path):
        config_dir = tmp_path / "factors"
        config_dir.mkdir()
        for name in ["source_catalog.yaml", "factor_catalog.yaml", "block_catalog.yaml", "evidence_catalog.yaml"]:
            (config_dir / name).write_text(f"{name.split('_')[0]}s: []\n", encoding="utf-8")
        src, fac, blk, ev = load_catalogs(config_dir)
        assert len(src.list_all()) == 0
        assert len(fac.list_all()) == 0

    def test_load_full_catalog(self, tmp_path):
        # 使用 fixtures 或完整 YAML 测试
        pass
```

### Test File 6: `test_integration.py` (3 tests)

```python
from hermass_platform.factors.block_schema import BlockSpec, BlockType
from hermass_platform.factors.catalog_loader import CatalogLoader
from hermass_platform.factors.factor_schema import FactorSpec
from hermass_platform.factors.registry import RegistryValidator
from hermass_platform.factors.source_schema import (
    ApplicableMarket,
    FactorSource,
    Reliability,
    SourceType,
)


class TestIntegration:
    def test_factor_lifecycle_e1_to_e5(self, tmp_path):
        config_dir = tmp_path / "factors"
        config_dir.mkdir()
        # 创建最小 catalog
        (config_dir / "source_catalog.yaml").write_text(
            "sources:\n  - source_id: src1\n    source_type: open_quant_framework\n"
            "    name: Src\n    url_or_local_ref: x\n    reliability: high\n"
            "    license_notes: x\n    applicable_markets: [A_SHARE]\n",
            encoding="utf-8",
        )
        (config_dir / "factor_catalog.yaml").write_text(
            "factors:\n  - factor_id: f1\n    name: F1\n    category: technical\n"
            "    level: L1\n    frequency: D1\n    output_type: numeric\n"
            "    direction: higher_better\n    source_refs: [src1]\n"
            "    a_share_notes: x\n    evidence_level: E1\n",
            encoding="utf-8",
        )
        (config_dir / "block_catalog.yaml").write_text("blocks: []\n", encoding="utf-8")
        (config_dir / "evidence_catalog.yaml").write_text("evidence: []\n", encoding="utf-8")

        loader = CatalogLoader(config_dir)
        src, fac, blk, ev = loader.load_all()
        assert fac.get("f1").production_gate.value == "blocked"

    def test_methodology_to_block_refs(self):
        # VCP methodology -> converted_blocks 必须已注册
        src = SourceRegistry()
        src.register(
            FactorSource(
                source_id="minervini_vcp",
                source_type=SourceType.TRADER_METHODOLOGY,
                name="VCP",
                url_or_local_ref="x",
                reliability=Reliability.MEDIUM,
                license_notes="x",
                applicable_markets=[ApplicableMarket.A_SHARE],
            )
        )
        fac = FactorRegistry()
        blk = BlockRegistry()
        blk.register(
            BlockSpec(
                block_id="vcp_contraction_detector",
                block_type=BlockType.SIGNAL,
                name="VCP",
                source_refs=["minervini_vcp"],
                market_scope=["A_SHARE"],
            )
        )
        validator = RegistryValidator(src, fac, blk)
        result = validator.validate_all()
        assert result["block_source_refs"] == []

    def test_production_ready_only_approved(self):
        src = SourceRegistry()
        src.register(
            FactorSource(
                source_id="src1",
                source_type=SourceType.OPEN_QUANT_FRAMEWORK,
                name="Src",
                url_or_local_ref="x",
                reliability=Reliability.HIGH,
                license_notes="x",
                applicable_markets=[ApplicableMarket.A_SHARE],
            )
        )
        fac = FactorRegistry()
        fac.register(
            FactorSpec(
                factor_id="blocked",
                name="Blocked",
                category="technical",
                level="L1",
                frequency="D1",
                output_type="numeric",
                direction="neutral",
                source_refs=["src1"],
                a_share_notes="x",
                evidence_level="E1",
            )
        )
        fac.register(
            FactorSpec(
                factor_id="approved",
                name="Approved",
                category="technical",
                level="L1",
                frequency="D1",
                output_type="numeric",
                direction="neutral",
                source_refs=["src1"],
                a_share_notes="x",
                evidence_level="E5",
            )
        )
        blk = BlockRegistry()
        validator = RegistryValidator(src, fac, blk)
        ready = validator.list_production_ready_factors()
        assert len(ready) == 1
        assert ready[0].factor_id == "approved"
```

---

## 业务规则汇总

以下规则必须**硬编码**在代码中：

| 规则 | 实现位置 | 行为 |
|------|----------|------|
| E0-E3 默认 blocked | `derive_factor_gate()` / `BlockSpec._derive_production_gate()` | 返回 blocked |
| E4 只能 candidate | `derive_factor_gate()` / `BlockSpec._derive_production_gate()` | 返回 candidate |
| E5/E6 才允许 approved | `derive_factor_gate()` / `BlockSpec._derive_production_gate()` | 返回 approved |
| future_leakage_risk=high 必须 blocked | `derive_factor_gate()` | 返回 blocked |
| data_availability=unavailable 必须 blocked | `derive_factor_gate()` | 返回 blocked |
| source_refs 必须全部存在 | `RegistryValidator.validate_all()` | 返回错误列表 |
| 未注册 source ref 必须拒绝 | `FactorRegistry.validate_source_refs()` / `BlockRegistry.validate_source_refs()` | 返回错误 |
| production_ready 只返回 approved | `list_production_ready()` | 过滤 approved |
| registry 不做计算/回测/Web API | 设计约束 | 仅 metadata |

---

## Implementation Order

### Step 1: 新建包结构 (30 min)

```bash
mkdir -p hermass_platform/factors/tests
mkdir -p config/factors
```

**验收标准**:
- 目录结构存在
- `hermass_platform/factors/__init__.py` 为空或导出关键类

### Step 2: 写 exceptions.py (15 min)

**验收标准**:
- 所有异常类可导入
- 异常继承链正确

### Step 3: 写 source_schema.py (45 min)

**验收标准**:
- Pydantic v2 模型可导入
- 枚举值与 taxonomy 对齐
- `FactorSource` 必填字段校验通过
- `Evidence` 支持 metric_refs

### Step 4: 写 factor_schema.py (60 min)

**验收标准**:
- `FactorSpec` 必填字段校验通过
- `derive_factor_gate()` 所有分支测试通过
- `production_gate` 自动推导正确
- `a_share_notes` 空值被拒绝

### Step 5: 写 block_schema.py (60 min)

**验收标准**:
- `BlockSpec` 必填字段校验通过
- `ParameterSpec` / `ParameterSpace` 边界校验通过
- `parameter_space` 必须是 `parameters` 子集
- `weight` / `generation_weight` 范围校验
- `production_gate` 自动推导正确

### Step 6: 写 registry.py (90 min)

**验收标准**:
- 4 个 Registry 可独立使用
- `register` / `get` / `list_all` / `list_by_type` / `list_by_status` 正常工作
- 跨 registry 校验返回错误列表
- `RegistryValidator.validate_all()` 返回完整结果

### Step 7: 写 catalog_loader.py (45 min)

**验收标准**:
- 可从 YAML 加载 source/factor/block/evidence
- 返回已填充的 4 个 Registry
- 缺失文件抛出 `FileNotFoundError`
- 格式错误抛出 Pydantic ValidationError

### Step 8: 写最小 catalog YAML (60 min)

**验收标准**:
- `source_catalog.yaml` ≥ 10 条
- `factor_catalog.yaml` ≥ 10 条
- `block_catalog.yaml` ≥ 10 条
- `evidence_catalog.yaml` ≥ 10 条
- 所有 YAML 可被 loader 正常加载

### Step 9: 写测试 (120 min)

**验收标准**:
- 至少 30 个测试点全部通过
- 覆盖 schema / registry / loader / integration
- `pytest hermass_platform/factors/tests/` 全绿

### Step 10: 跑验收命令 (15 min)

```bash
cd /Users/lv111101/Documents/\ AI\ 原生度的量化\ Agent\ 平台
python -m pytest hermass_platform/factors/tests/ -v
```

**验收标准**:
- 测试通过率 100%
- 无 Pydantic deprecation warning
- catalog loader 能加载全部 YAML

---

## Non-MVP Exclusions

本轮明确不做：

1. **因子数值计算**: registry 只存 metadata，不实现 `compute()`。
2. **Alpha 回测**: 不连接 backtest engine。
3. **FastAPI 路由**: 不提供 HTTP 接口。
4. **LLM 生成因子**: 不调用 OpenAI/Claude 生成新因子。
5. **自动抓取网页来源**: source url 只作引用，不爬取。
6. **真实 SQX 代码导入**: 只参考设计思想，不解析 SQX 文件。
7. **动态 evidence 更新**: evidence 变更需重新加载 catalog 或调用 register。
8. **血缘追踪**: 不追踪 factor 的完整计算链。
9. **版本控制**: 不实现 factor 多版本并存。
10. **权限控制**: 不实现 source license 的自动化合规检查。
