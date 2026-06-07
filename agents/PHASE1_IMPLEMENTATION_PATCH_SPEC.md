# Phase 1 Implementation Patch Spec

## ConditionSpec Final Shape

### 新增枚举

```python
from enum import Enum

class PreviewSupport(str, Enum):
    """条件在 Preview 中的支持状态。"""
    FULLY_SUPPORTED = "fully_supported"           # Mock 和 DuckDB 都支持
    MOCK_ONLY = "mock_only"                       # 仅 Mock 支持（无真实数据源）
    REQUIRES_BACKTEST_CONTEXT = "requires_backtest_context"  # 需要持仓/回测上下文
    UNSUPPORTED = "unsupported"                   # 完全不支持 Preview


class ContextRequirement(str, Enum):
    """条件执行所需的上下文类型。"""
    NONE = "none"                                 # 不需要额外上下文
    POSITION = "position"                         # 需要持仓上下文（entry_price, position_size）
    PORTFOLIO = "portfolio"                       # 需要组合上下文（总资金、当前仓位）
    MARKET_STATE = "market_state"                 # 需要市场状态（如涨跌停状态）
```

### 修订后的 ConditionSpec

```python
@dataclass(frozen=True)
class ConditionSpec:
    """Specification for a registered condition type.

    Attributes:
        condition_type: Unique type identifier (snake_case).
        category: Primary category (entry, exit, filter).
        params: List of parameter schemas.
        translator: Supported translation dialect(s).
        description: Human-readable description.
        examples: Example parameter sets for documentation.
        required_columns: Static column dependency templates (e.g. ["ma_{fast_period}"]).
        required_tables: Static table dependencies (e.g. ["daily_bars"]).
        context_requirements: Runtime context needed beyond static data.
        preview_support: Preview support classification.
        preview_notes: Human-readable explanation for preview limitations.
    """

    condition_type: str
    category: ConditionCategory
    params: list[ParamSchema]
    translator: TranslatorDialect
    description: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)

    # 数据源依赖（静态声明）
    required_columns: list[str] = field(default_factory=list)
    required_tables: list[str] = field(default_factory=list)

    # 执行上下文依赖（运行时）
    context_requirements: list[ContextRequirement] = field(default_factory=list)

    # Preview 支持状态
    preview_support: PreviewSupport = PreviewSupport.FULLY_SUPPORTED
    preview_notes: str = ""
```

### 关键设计决策

1. **`required_tables` 不再用于 blocklist 拒绝**：
   - 原设计：检查 `required_tables` 是否在 `MVP_BLOCKED_TABLES` 中，如果在则整体拒绝 Preview
   - 新设计：`required_tables` 仅用于信息展示和 SQL 构建，**不用于拒绝 Preview**
   - Preview 是否失败由 `preview_support` 决定

2. **`context_requirements` 区分数据依赖和上下文依赖**：
   - `required_tables` = 静态数据表依赖（daily_bars, state_cube 等）
   - `context_requirements` = 运行时上下文依赖（position, portfolio 等）
   - 需要 `POSITION` 上下文 ≠ Preview 失败，只是标记为 `requires_backtest_context`

3. **`preview_support` 是单一权威字段**：
   - 所有 Preview 路由决策只看 `preview_support`
   - 不再从 `required_tables` 推断是否可 Preview

---

## MVP Condition Metadata

### 完整 Metadata 表

| condition_type | category | required_columns | required_tables | context_requirements | preview_support | preview_notes |
|---|---|---|---|---|---|---|
| `ma_golden_cross` | ENTRY | `["ma_{fast_period}", "ma_{slow_period}"]` | `["daily_bars"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `ma_death_cross` | EXIT | `["ma_{fast_period}", "ma_{slow_period}"]` | `["daily_bars"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `price_cross_ma` | ENTRY | `["close_{timeframe}", "ma_{ma_period}_{timeframe}"]` | `["daily_bars"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `state_hex_in` | ENTRY | `["state_hex_{timeframe}"]` | `["state_cube"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `state_ef_count` | ENTRY | `["ef_count"]` | `["state_cube"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `volume_ratio` | ENTRY | `["volume", "volume_ma_{lookback}"]` | `["daily_bars"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `industry_include` | FILTER | `["industry"]` | `["stock_info"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `industry_exclude` | FILTER | `["industry"]` | `["stock_info"]` | `[]` | `FULLY_SUPPORTED` | "" |
| `stop_loss_pct` | EXIT | `["close"]` | `["daily_bars"]` | `["POSITION"]` | `REQUIRES_BACKTEST_CONTEXT` | "Stop loss requires position context (entry_price). Preview returns estimated hit count based on price distribution." |
| `take_profit_pct` | EXIT | `["close"]` | `["daily_bars"]` | `["POSITION"]` | `REQUIRES_BACKTEST_CONTEXT` | "Take profit requires position context (entry_price). Preview returns estimated hit count based on price distribution." |
| `limit_up_filter` | FILTER | `["is_limit_up"]` | `["daily_bars"]` | `["MARKET_STATE"]` | `FULLY_SUPPORTED` | "" |

### 关键变更说明

#### `stop_loss_pct`

- **原设计**：`required_tables=["daily_bars", "positions"]` → 触发 blocklist 拒绝
- **新设计**：
  - `required_tables=["daily_bars"]`（只需要价格数据做估算）
  - `context_requirements=["POSITION"]`（需要 entry_price 做精确计算）
  - `preview_support=REQUIRES_BACKTEST_CONTEXT`
  - Preview 不失败，而是标记该条件为 "需要回测上下文"

#### `take_profit_pct`

- 与 `stop_loss_pct` 相同处理

#### `limit_up_filter`

- `context_requirements=["MARKET_STATE"]`：需要知道当日是否涨停
- 但 `preview_support=FULLY_SUPPORTED`：因为 `is_limit_up` 是静态数据列

---

## Preview Semantics

### Preview 支持状态定义

```python
class PreviewSupport(str, Enum):
    FULLY_SUPPORTED = "fully_supported"
    """Mock 和 DuckDB 都支持完整预览。"""

    MOCK_ONLY = "mock_only"
    """仅 Mock 支持，DuckDB 无对应数据。"""

    REQUIRES_BACKTEST_CONTEXT = "requires_backtest_context"
    """需要回测/持仓上下文才能精确计算。
    
    Preview 行为：
    - Mock 模式：返回基于统计分布的估算命中数
    - DuckDB 模式：返回基于价格分布的估算命中数
    - 条件标记为 requires_backtest_context，不阻塞整体 Preview
    """

    UNSUPPORTED = "unsupported"
    """完全不支持 Preview。遇到时整体 Preview 失败。"""
```

### 条件级 Preview 结果

```python
@dataclass
class ConditionPreview:
    """单个条件的预览结果。"""
    condition_type: str
    condition_expression: str | None
    preview_support: PreviewSupport
    hit_count: int | None
    sample_count: int
    notes: str = ""
```

### Section 级 Preview 结果

```python
@dataclass
class SectionPreview:
    """一个 section（entry/exit/filters）的预览结果。"""
    section_name: str
    conditions: list[ConditionPreview]
    combined_hit_count: int | None
    sample_count: int
    sql_preview: str | None
    has_context_required: bool  # 是否有条件需要回测上下文
```

### Preview 执行规则

#### 规则 1：整体失败只由 UNSUPPORTED 触发

```python
def _check_preview_support(dsl: StrategyDSL, registry: ConditionRegistry) -> list[str]:
    """检查是否有 unsupported 条件。返回 unsupported 的条件类型列表。"""
    unsupported = []
    for cond in dsl.get_all_conditions():
        spec = registry.get(cond.condition_type)
        if spec.preview_support == PreviewSupport.UNSUPPORTED:
            unsupported.append(cond.condition_type)
    return unsupported
```

#### 规则 2：REQUIRES_BACKTEST_CONTEXT 条件不阻塞整体 Preview

```python
# Mock 模式下 stop_loss_pct 的处理
def _preview_condition_mock(cond: ConditionBlock, spec: ConditionSpec) -> ConditionPreview:
    if spec.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT:
        # 基于统计分布估算
        return ConditionPreview(
            condition_type=cond.condition_type,
            condition_expression="estimated: close <= entry_price * (1 - stop_loss)",
            preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
            hit_count=_estimate_hit_count(cond),  # 基于参数估算
            sample_count=3000,
            notes=f"{cond.condition_type} requires backtest context for precise calculation",
        )
```

#### 规则 3：Section 级 hit_count 计算

```python
def _calculate_section_hit_count(conditions: list[ConditionPreview]) -> int | None:
    """计算 section 级命中数。
    
    规则：
    - 如果所有条件都是 FULLY_SUPPORTED：返回真实命中数
    - 如果有 REQUIRES_BACKTEST_CONTEXT：返回估算值（基于其他条件过滤后的样本）
    - 如果有 UNSUPPORTED：返回 None（整体失败）
    """
    ...
```

#### 规则 4：Mock vs DuckDB 差异

| 条件类型 | Mock 模式 | DuckDB 模式 |
|---|---|---|
| `ma_golden_cross` | deterministic 命中数 | 真实 SQL 查询 |
| `stop_loss_pct` | 基于参数估算（如 8% 止损 ≈ 10% 样本） | 基于价格分布统计估算 |
| `take_profit_pct` | 基于参数估算 | 基于价格分布统计估算 |
| `industry_include` | deterministic 命中数 | 真实 SQL 查询 |

### Preview 响应结构（修订版）

```json
{
  "trace_id": "prev_xyz789",
  "sections": {
    "entry": {
      "section_name": "entry",
      "conditions": [
        {
          "condition_type": "ma_golden_cross",
          "condition_expression": "(ma_5 > ma_20 AND LAG(ma_5) <= LAG(ma_20))",
          "preview_support": "fully_supported",
          "hit_count": 142,
          "sample_count": 3000,
          "notes": ""
        }
      ],
      "combined_hit_count": 142,
      "sample_count": 3000,
      "sql_preview": "SELECT ma_5, ma_20 FROM daily_bars WHERE (ma_5 > ma_20 AND LAG(ma_5) <= LAG(ma_20)) LIMIT 10000",
      "has_context_required": false
    },
    "exit": {
      "section_name": "exit",
      "conditions": [
        {
          "condition_type": "ma_death_cross",
          "condition_expression": "(ma_5 < ma_20 AND LAG(ma_5) >= LAG(ma_20))",
          "preview_support": "fully_supported",
          "hit_count": 98,
          "sample_count": 3000,
          "notes": ""
        },
        {
          "condition_type": "stop_loss_pct",
          "condition_expression": "estimated: close <= entry_price * 0.92",
          "preview_support": "requires_backtest_context",
          "hit_count": 156,
          "sample_count": 3000,
          "notes": "stop_loss_pct requires backtest context for precise calculation"
        }
      ],
      "combined_hit_count": 254,
      "sample_count": 3000,
      "sql_preview": "SELECT ma_5, ma_20, close FROM daily_bars WHERE ... LIMIT 10000",
      "has_context_required": true
    }
  },
  "overall": {
    "hit_count": 142,
    "sample_count": 3000,
    "data_freshness": "2024-12-31",
    "has_context_required": true
  },
  "required_columns": ["ma_5", "ma_20", "close"],
  "required_tables": ["daily_bars"],
  "errors": []
}
```

---

## API And Service Patch Details

### `api_models.py` 修订

#### 新增模型

```python
from pydantic import BaseModel, Field
from typing import Literal

class ConditionPreviewItem(BaseModel):
    """单个条件的预览结果。"""
    condition_type: str
    condition_expression: str | None
    preview_support: Literal["fully_supported", "mock_only", "requires_backtest_context", "unsupported"]
    hit_count: int | None
    sample_count: int
    notes: str = ""

class SectionPreviewItem(BaseModel):
    """Section 级预览结果。"""
    section_name: str
    conditions: list[ConditionPreviewItem]
    combined_hit_count: int | None
    sample_count: int
    sql_preview: str | None
    has_context_required: bool

class PreviewOverallItem(BaseModel):
    """整体预览统计。"""
    hit_count: int | None
    sample_count: int
    data_freshness: str | None
    has_context_required: bool

class PreviewResponse(BaseModel):
    """Preview 响应（修订版）。"""
    trace_id: str
    sections: dict[str, SectionPreviewItem]  # entry, exit, filters
    overall: PreviewOverallItem
    required_columns: list[str]
    required_tables: list[str]
    errors: list[str]
```

#### 保留模型（不变）

- `GenerateStrategyRequest/Response`
- `ValidateStrategyRequest/Response`
- `BacktestRequest/Response`
- `GetBacktestResponse`

---

### `preview_service.py` 修订

#### 核心类

```python
class PreviewService:
    def __init__(
        self,
        registry: ConditionRegistry,
        duckdb_provider: DuckDBProvider | None = None,
        mock_provider: MockDataProvider | None = None,
    ):
        self.registry = registry
        self.duckdb = duckdb_provider
        self.mock = mock_provider or MockDataProvider()

    def preview(
        self,
        dsl: StrategyDSL,
        data_source: Literal["mock", "duckdb"] = "mock",
        universe: str = "csi300",
        date_range: DateRange | None = None,
    ) -> PreviewResult:
        """执行条件预览。
        
        流程：
        1. 检查是否有 UNSUPPORTED 条件 → 有则整体失败
        2. 对每个 section 分别预览
        3. 标记 REQUIRES_BACKTEST_CONTEXT 条件
        4. 返回 section 级和整体统计
        """
        # Step 1: 检查 unsupported
        unsupported = self._check_unsupported(dsl)
        if unsupported:
            return PreviewResult(
                trace_id=generate_trace_id(),
                sections={},
                overall=PreviewOverall(
                    hit_count=None,
                    sample_count=0,
                    data_freshness=None,
                    has_context_required=False,
                ),
                required_columns=[],
                required_tables=[],
                errors=[f"Preview failed: unsupported conditions: {unsupported}"],
            )

        # Step 2: 预览每个 section
        sections: dict[str, SectionPreview] = {}
        for section_name in ["entry", "exit", "filters"]:
            section_preview = self._preview_section(
                dsl, section_name, data_source, universe, date_range
            )
            sections[section_name] = section_preview

        # Step 3: 计算整体统计
        overall = self._calculate_overall(sections)

        # Step 4: 收集依赖
        all_columns, all_tables = self._collect_dependencies(dsl)

        return PreviewResult(
            trace_id=generate_trace_id(),
            sections=sections,
            overall=overall,
            required_columns=all_columns,
            required_tables=all_tables,
            errors=[],
        )

    def _check_unsupported(self, dsl: StrategyDSL) -> list[str]:
        """检查是否有 unsupported 条件。"""
        unsupported = []
        for cond in dsl.get_all_conditions():
            spec = self.registry.get(cond.condition_type)
            if spec.preview_support == PreviewSupport.UNSUPPORTED:
                unsupported.append(cond.condition_type)
        return unsupported

    def _preview_section(
        self,
        dsl: StrategyDSL,
        section_name: str,
        data_source: str,
        universe: str,
        date_range: DateRange | None,
    ) -> SectionPreview:
        """预览单个 section。"""
        conditions = getattr(dsl, section_name)
        if not conditions:
            return SectionPreview(
                section_name=section_name,
                conditions=[],
                combined_hit_count=0,
                sample_count=0,
                sql_preview=None,
                has_context_required=False,
            )

        condition_previews: list[ConditionPreview] = []
        has_context_required = False

        for cond in conditions:
            spec = self.registry.get(cond.condition_type)
            cp = self._preview_condition(cond, spec, data_source, universe, date_range)
            condition_previews.append(cp)
            if cp.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT:
                has_context_required = True

        # 构建 SQL 预览（仅包含 fully_supported 条件）
        sql_preview = self._build_section_sql(dsl, section_name, condition_previews)

        # 计算 combined_hit_count
        combined = self._calculate_combined_hit_count(condition_previews)

        return SectionPreview(
            section_name=section_name,
            conditions=condition_previews,
            combined_hit_count=combined,
            sample_count=3000,  # 或从数据源获取
            sql_preview=sql_preview,
            has_context_required=has_context_required,
        )

    def _preview_condition(
        self,
        cond: ConditionBlock,
        spec: ConditionSpec,
        data_source: str,
        universe: str,
        date_range: DateRange | None,
    ) -> ConditionPreview:
        """预览单个条件。"""
        if spec.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT:
            return self._preview_context_required(cond, spec, data_source)

        if spec.preview_support == PreviewSupport.MOCK_ONLY and data_source == "duckdb":
            return ConditionPreview(
                condition_type=cond.condition_type,
                condition_expression=None,
                preview_support=PreviewSupport.MOCK_ONLY,
                hit_count=None,
                sample_count=0,
                notes="Mock-only condition, not available in DuckDB preview",
            )

        # FULLY_SUPPORTED: 正常翻译并查询
        translation = translate_condition(cond, self.registry, dialect="duckdb")
        
        if data_source == "mock":
            result = self.mock.query(translation.sql_expr, spec.required_tables)
        else:
            result = self.duckdb.query(translation.sql_expr, spec.required_tables)

        return ConditionPreview(
            condition_type=cond.condition_type,
            condition_expression=translation.sql_expr,
            preview_support=PreviewSupport.FULLY_SUPPORTED,
            hit_count=result.hit_count,
            sample_count=result.sample_count,
            notes="",
        )

    def _preview_context_required(
        self,
        cond: ConditionBlock,
        spec: ConditionSpec,
        data_source: str,
    ) -> ConditionPreview:
        """预览需要回测上下文的条件（返回估算值）。"""
        # 基于参数估算命中数
        estimated_hits = self._estimate_context_required_hits(cond, data_source)
        
        return ConditionPreview(
            condition_type=cond.condition_type,
            condition_expression=f"estimated: {self._build_estimated_expression(cond)}",
            preview_support=PreviewSupport.REQUIRES_BACKTEST_CONTEXT,
            hit_count=estimated_hits,
            sample_count=3000,
            notes=f"{cond.condition_type} requires backtest context for precise calculation",
        )

    def _estimate_context_required_hits(
        self, cond: ConditionBlock, data_source: str
    ) -> int:
        """估算需要上下文的条件的命中数。
        
        Mock 模式：基于参数 deterministic 估算
        DuckDB 模式：基于价格分布统计估算
        """
        params = cond.params
        if cond.condition_type == "stop_loss_pct":
            value = params.get("value", 0.08)
            # 估算：止损概率 ≈ 止损幅度 * 2（简化模型）
            base_rate = min(value * 2, 0.5)
            return int(3000 * base_rate)
        elif cond.condition_type == "take_profit_pct":
            value = params.get("value", 0.15)
            base_rate = min(value * 1.5, 0.5)
            return int(3000 * base_rate)
        return 150  # 默认值

    def _build_section_sql(
        self,
        dsl: StrategyDSL,
        section_name: str,
        condition_previews: list[ConditionPreview],
    ) -> str | None:
        """构建 section 的 SQL 预览（仅包含 fully_supported 条件）。"""
        supported_conditions = [
            cp for cp in condition_previews
            if cp.preview_support == PreviewSupport.FULLY_SUPPORTED
        ]
        
        if not supported_conditions:
            return None

        # 从 DSL 获取原始条件块
        conditions = getattr(dsl, section_name)
        
        # 构建 SQL（禁止 SELECT *）
        columns = []
        where_clauses = []
        
        for cond in conditions:
            spec = self.registry.get(cond.condition_type)
            if spec.preview_support == PreviewSupport.FULLY_SUPPORTED:
                translation = translate_condition(cond, self.registry, dialect="duckdb")
                columns.extend(translation.required_columns)
                if translation.sql_expr:
                    where_clauses.append(translation.sql_expr)

        unique_columns = list(dict.fromkeys(columns))
        col_str = ", ".join(unique_columns) if unique_columns else "symbol, date, close"
        where_str = " AND ".join(f"({w})" for w in where_clauses) if where_clauses else "1=1"
        
        return f"SELECT {col_str} FROM daily_bars WHERE {where_str} LIMIT 10000"
```

---

### `audit.py` 修订

#### 核心类

```python
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

class AuditLogger:
    def __init__(self, db_connection):
        self.db = db_connection

    def _compute_hash(self, data: str | dict) -> str:
        """计算 SHA256 hash。"""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def log_generation(
        self,
        trace_id: str,
        user_id: str,
        input_text: str,
        dsl: StrategyDSL | None,
        success: bool,
        errors: list[str],
    ) -> None:
        """记录策略生成审计。"""
        input_hash = self._compute_hash(input_text)
        output_hash = self._compute_hash(dsl.to_dict() if dsl else {})
        
        self._insert(
            trace_id=trace_id,
            user_id=user_id,
            operation="generate",
            strategy_id=dsl.strategy_id if dsl else None,
            version_id=None,
            dsl_version=dsl.schema_version if dsl else None,
            input_hash=input_hash,
            output_hash=output_hash,
            red_line_result=None,
            metadata_json={"success": success, "errors": errors},
        )

    def log_validation(
        self,
        trace_id: str,
        user_id: str,
        strategy_id: str,
        dsl: StrategyDSL,
        validation_result: ValidationResult,
    ) -> None:
        """记录校验审计。"""
        input_hash = self._compute_hash(dsl.to_dict())
        
        red_line_data = {
            "passed": not validation_result.has_red_line_violation,
            "triggered_rules": [
                e.code for e in validation_result.errors
                if e.level == ValidationLevel.RED_LINE
            ],
        }
        
        self._insert(
            trace_id=trace_id,
            user_id=user_id,
            operation="validate",
            strategy_id=strategy_id,
            version_id=None,
            dsl_version=dsl.schema_version,
            input_hash=input_hash,
            output_hash=input_hash,  # 校验时输入输出相同
            red_line_result=red_line_data,
            metadata_json={
                "passed": validation_result.passed,
                "level": validation_result.level.value,
                "error_count": validation_result.error_count,
                "warning_count": validation_result.warning_count,
            },
        )

    def log_preview(
        self,
        trace_id: str,
        user_id: str,
        strategy_id: str,
        dsl: StrategyDSL,
        preview_result: PreviewResult,
        data_source: str,
    ) -> None:
        """记录预览审计。"""
        input_hash = self._compute_hash(dsl.to_dict())
        output_hash = self._compute_hash(preview_result.to_dict())
        
        self._insert(
            trace_id=trace_id,
            user_id=user_id,
            operation="preview",
            strategy_id=strategy_id,
            version_id=None,
            dsl_version=dsl.schema_version,
            input_hash=input_hash,
            output_hash=output_hash,
            red_line_result=None,
            metadata_json={
                "data_source": data_source,
                "hit_count": preview_result.overall.hit_count,
                "sample_count": preview_result.overall.sample_count,
                "has_context_required": preview_result.overall.has_context_required,
                "required_tables": preview_result.required_tables,
            },
        )

    def log_backtest(
        self,
        trace_id: str,
        user_id: str,
        job_id: str,
        strategy_id: str,
        status: str,
    ) -> None:
        """记录回测审计。"""
        self._insert(
            trace_id=trace_id,
            user_id=user_id,
            operation="backtest",
            strategy_id=strategy_id,
            version_id=None,
            dsl_version=None,
            input_hash=None,
            output_hash=None,
            red_line_result=None,
            metadata_json={"job_id": job_id, "status": status},
        )

    def _insert(self, **kwargs) -> None:
        """插入审计记录。"""
        # 参数化 SQL 插入
        ...
```

---

## Storage And DDL Patch Details

### DDL 修订（不变）

`migrations/strategy_lab/001_init.sql` 保持原设计不变：

- `user_strategies`
- `strategy_versions`
- `strategy_backtests`
- `strategy_audit_log`

### `storage.py` 修订

#### 核心类（保持接口不变，增加辅助方法）

```python
class StrategyStorage:
    def __init__(self, db_connection):
        self.db = db_connection

    def create_strategy(self, user_id: str, name: str, description: str) -> str:
        """创建策略记录，返回 strategy_id。"""
        strategy_id = self._generate_strategy_id(name)
        self.db.execute(
            "INSERT INTO user_strategies (strategy_id, user_id, name, description) VALUES (?, ?, ?, ?)",
            (strategy_id, user_id, name, description),
        )
        return strategy_id

    def save_version(self, strategy_id: str, dsl: StrategyDSL, created_by: str) -> str:
        """保存策略版本，返回 version_id。"""
        version_number = self._get_next_version_number(strategy_id)
        version_id = f"{strategy_id}_v{version_number}"
        dsl_json = dsl.to_json()
        schema_hash = hashlib.sha256(dsl_json.encode()).hexdigest()
        
        self.db.execute(
            """INSERT INTO strategy_versions 
               (version_id, strategy_id, version_number, dsl_json, dsl_version, schema_hash, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (version_id, strategy_id, version_number, dsl_json, dsl.schema_version, schema_hash, created_by),
        )
        return version_id

    def get_latest_version(self, strategy_id: str) -> StrategyDSL | None:
        """获取策略最新版本。"""
        row = self.db.execute(
            "SELECT dsl_json FROM strategy_versions WHERE strategy_id = ? ORDER BY version_number DESC LIMIT 1",
            (strategy_id,),
        ).fetchone()
        
        if row:
            return StrategyDSL.from_dict(json.loads(row[0]))
        return None

    def list_strategies(self, user_id: str, limit: int = 50) -> list[StrategySummary]:
        """列出用户的策略。"""
        rows = self.db.execute(
            "SELECT strategy_id, name, status, created_at FROM user_strategies WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        
        return [StrategySummary(id=r[0], name=r[1], status=r[2], created_at=r[3]) for r in rows]

    def save_backtest_result(self, job_id: str, strategy_id: str, 
                              version_id: str, result: dict) -> None:
        """保存回测结果。"""
        self.db.execute(
            "UPDATE strategy_backtests SET status = ?, result_json = ?, completed_at = CURRENT_TIMESTAMP WHERE job_id = ?",
            ("completed", json.dumps(result), job_id),
        )

    def get_backtest_result(self, job_id: str) -> dict | None:
        """获取回测结果。"""
        row = self.db.execute(
            "SELECT result_json FROM strategy_backtests WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        
        if row and row[0]:
            return json.loads(row[0])
        return None

    def _generate_strategy_id(self, name: str) -> str:
        """生成 strategy_id（snake_case + 时间戳）。"""
        import re
        base = re.sub(r'[^\w]', '_', name.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base}_{timestamp}"

    def _get_next_version_number(self, strategy_id: str) -> int:
        """获取下一个版本号。"""
        row = self.db.execute(
            "SELECT MAX(version_number) FROM strategy_versions WHERE strategy_id = ?",
            (strategy_id,),
        ).fetchone()
        return (row[0] or 0) + 1
```

---

## Tests To Add Or Change

### 1. `test_condition_registry.py` — 修改

**新增测试点**：

```python
def test_condition_spec_has_preview_support():
    """所有 MVP 条件必须有 preview_support 字段。"""
    registry = ConditionRegistry.default()
    for spec in registry.list_all():
        assert spec.preview_support is not None
        assert spec.preview_support in PreviewSupport

def test_stop_loss_preview_support_is_context_required():
    """stop_loss_pct 的 preview_support 必须是 REQUIRES_BACKTEST_CONTEXT。"""
    registry = ConditionRegistry.default()
    spec = registry.get("stop_loss_pct")
    assert spec.preview_support == PreviewSupport.REQUIRES_BACKTEST_CONTEXT
    assert ContextRequirement.POSITION in spec.context_requirements

def test_stop_loss_required_tables_does_not_include_positions():
    """stop_loss_pct 的 required_tables 不应包含 positions（避免 blocklist 拒绝）。"""
    registry = ConditionRegistry.default()
    spec = registry.get("stop_loss_pct")
    assert "positions" not in spec.required_tables
    assert "daily_bars" in spec.required_tables
```

### 2. `test_preview_service.py` — 新增/修改

**修改现有测试**：

```python
# 原测试（需要修改）：
# def test_reject_non_mvp_table():
#     """DSL 包含 stop_loss_pct 时 preview 被拒绝。"""
#     ...

# 新测试（替换）：
def test_stop_loss_pct_mock_preview_succeeds():
    """合法 DSL 含 stop_loss_pct 时，mock preview 整体通过。"""
    dsl = create_valid_dsl_with_stop_loss()
    service = PreviewService(registry=ConditionRegistry.default())
    result = service.preview(dsl, data_source="mock")
    
    assert len(result.errors) == 0
    assert "exit" in result.sections
    exit_section = result.sections["exit"]
    
    # stop_loss_pct 条件存在且标记为 requires_backtest_context
    stop_loss_preview = [c for c in exit_section.conditions if c.condition_type == "stop_loss_pct"][0]
    assert stop_loss_preview.preview_support == "requires_backtest_context"
    assert stop_loss_preview.hit_count is not None  # 有估算值
    assert stop_loss_preview.hit_count > 0

def test_stop_loss_pct_duckdb_preview_not_failing():
    """合法 DSL 含 stop_loss_pct 时，DuckDB preview 不整体失败。"""
    dsl = create_valid_dsl_with_stop_loss()
    service = PreviewService(registry=ConditionRegistry.default())
    result = service.preview(dsl, data_source="duckdb")
    
    assert len(result.errors) == 0  # 不整体失败
    assert "exit" in result.sections
    
    exit_section = result.sections["exit"]
    assert exit_section.has_context_required is True
    
    # stop_loss_pct 标记为 requires_backtest_context
    stop_loss_preview = [c for c in exit_section.conditions if c.condition_type == "stop_loss_pct"][0]
    assert stop_loss_preview.preview_support == "requires_backtest_context"

def test_unsupported_condition_fails_preview():
    """真正 unsupported 条件才整体失败。"""
    # 创建一个包含 UNSUPPORTED 条件的 DSL（测试用）
    dsl = create_dsl_with_unsupported_condition()
    service = PreviewService(registry=ConditionRegistry.default())
    result = service.preview(dsl, data_source="mock")
    
    assert len(result.errors) > 0
    assert "unsupported" in result.errors[0].lower()
```

**保留测试**：

```python
def test_sql_preview_no_select_star():
    """SQL 预览不包含 SELECT *。"""
    dsl = create_valid_dsl()
    service = PreviewService(registry=ConditionRegistry.default())
    result = service.preview(dsl, data_source="mock")
    
    for section in result.sections.values():
        if section.sql_preview:
            assert "SELECT *" not in section.sql_preview
            assert "SELECT " in section.sql_preview  # 有明确列名

def test_preview_fails_on_red_line_violation():
    """Preview 前红线失败时不执行查询。"""
    dsl = create_dsl_without_stop_loss()  # 缺少止损，红线失败
    service = PreviewService(registry=ConditionRegistry.default())
    
    # PreviewService.preview 应在调用前检查红线
    # 或者由路由层先校验再调用 preview
    # 这里测试：如果传入未通过红线的 DSL，preview 应拒绝
    with pytest.raises(ValueError, match="red line"):
        service.preview(dsl, data_source="mock")
```

### 3. `test_audit.py` — 新增

```python
def test_audit_logs_all_required_fields():
    """审计记录包含所有必要字段。"""
    logger = AuditLogger(db_connection)
    dsl = create_valid_dsl()
    
    logger.log_generation(
        trace_id="trace_123",
        user_id="user_1",
        input_text="MA5上穿MA20买入",
        dsl=dsl,
        success=True,
        errors=[],
    )
    
    # 查询审计记录
    row = db_connection.execute(
        "SELECT trace_id, dsl_version, input_hash, output_hash, red_line_result FROM strategy_audit_log WHERE trace_id = ?",
        ("trace_123",),
    ).fetchone()
    
    assert row[0] == "trace_123"
    assert row[1] == "strategy_dsl_v2"
    assert row[2] is not None  # input_hash
    assert len(row[2]) == 64  # SHA256 hex
    assert row[3] is not None  # output_hash
    assert len(row[3]) == 64  # SHA256 hex
    assert row[4] is None  # generate 时无 red_line_result

def test_audit_logs_red_line_result_on_validation():
    """校验审计记录 red_line_result。"""
    logger = AuditLogger(db_connection)
    dsl = create_valid_dsl()
    validation_result = validate_dsl(dsl)
    
    logger.log_validation(
        trace_id="trace_456",
        user_id="user_1",
        strategy_id=dsl.strategy_id,
        dsl=dsl,
        validation_result=validation_result,
    )
    
    row = db_connection.execute(
        "SELECT red_line_result FROM strategy_audit_log WHERE trace_id = ?",
        ("trace_456",),
    ).fetchone()
    
    red_line = json.loads(row[0])
    assert "passed" in red_line
    assert "triggered_rules" in red_line
```

### 4. `test_api_models.py` — 修改

```python
def test_preview_response_has_section_level_context_flag():
    """PreviewResponse 支持 section 级 has_context_required 标记。"""
    response = PreviewResponse(
        trace_id="test",
        sections={
            "entry": SectionPreviewItem(
                section_name="entry",
                conditions=[],
                combined_hit_count=0,
                sample_count=0,
                sql_preview=None,
                has_context_required=False,
            ),
            "exit": SectionPreviewItem(
                section_name="exit",
                conditions=[],
                combined_hit_count=0,
                sample_count=0,
                sql_preview=None,
                has_context_required=True,  # 有 stop_loss_pct
            ),
        },
        overall=PreviewOverallItem(
            hit_count=0,
            sample_count=0,
            data_freshness=None,
            has_context_required=True,
        ),
        required_columns=[],
        required_tables=[],
        errors=[],
    )
    
    assert response.sections["exit"].has_context_required is True
    assert response.overall.has_context_required is True
```

---

## Implementation Order

### Codex 应按以下顺序实现（避免返工）

**Step 1: 修改 `condition_registry.py`**
- 增加 `PreviewSupport` 和 `ContextRequirement` 枚举
- 修改 `ConditionSpec` dataclass（增加 4 个新字段）
- 更新所有 11 个 MVP 条件的 metadata
- 更新 `test_condition_registry.py`
- **验收**：所有 registry 测试通过，每个条件都有 preview_support

**Step 2: 修改 `condition_translator.py`**
- `TranslationResult` 保持不变（translator 职责不变）
- 确保 translator 不依赖新的 registry 字段
- **验收**：translator 测试全部通过

**Step 3: 实现 `api_models.py`**
- 定义所有请求/响应 Pydantic 模型（含修订后的 PreviewResponse）
- 新增 `ConditionPreviewItem`, `SectionPreviewItem`, `PreviewOverallItem`
- 编写 `test_api_models.py`
- **验收**：模型可序列化/反序列化

**Step 4: 实现 `storage.py` 和 DDL**
- 执行 `001_init.sql`
- 实现 `StrategyStorage` 类
- 编写 `test_storage.py`
- **验收**：CRUD 正常

**Step 5: 实现 `audit.py`**
- 实现 `AuditLogger` 类（含 hash 计算）
- 确保记录所有必要字段
- 编写 `test_audit.py`
- **验收**：审计记录完整

**Step 6: 实现 `preview_service.py`**
- 实现 `PreviewService`（含新的 preview 语义）
- 实现 `_preview_context_required` 估算逻辑
- 实现 `_check_unsupported`（替代原 blocklist）
- 编写 `test_preview_service.py`
- **验收**：
  - Mock 模式含 stop_loss_pct 的 DSL 整体通过
  - DuckDB 模式含 stop_loss_pct 的 DSL 不整体失败
  - UNSUPPORTED 条件整体失败
  - SQL 不含 SELECT *

**Step 7: 实现 Web 路由**
- 实现 5 个 API 端点
- 路由层先校验红线再调用 preview
- **验收**：端点可调用

---

## Risks

### 风险 1：估算逻辑过于简化

**风险**：`stop_loss_pct` 的估算（`value * 2`）过于简化，可能误导用户。

**缓解**：
- Preview 响应中明确标注 "estimated" 和 "requires backtest context"
- 估算公式可配置，后续可根据历史数据统计调整

### 风险 2：Mock 和 DuckDB 结果差异大

**风险**：Mock 返回 deterministic 估算，DuckDB 返回统计估算，两者差异可能让用户困惑。

**缓解**：
- 响应中明确标注 `data_source`
- `preview_support` 字段说明是估算还是真实查询

### 风险 3：后续添加新条件时忘记设置 preview_support

**风险**：开发者添加新条件时可能忘记设置 `preview_support`，默认为 `FULLY_SUPPORTED` 可能导致错误。

**缓解**：
- 注册时校验 `preview_support` 必须显式设置
- 添加测试：`test_all_conditions_have_explicit_preview_support`

### 风险 4：ContextRequirement 和 PreviewSupport 组合爆炸

**风险**：随着条件增多，`context_requirements` 和 `preview_support` 的组合可能变得复杂。

**缓解**：
- 保持枚举简单（4 个 PreviewSupport，4 个 ContextRequirement）
- 文档中明确每种组合的预期行为

### 风险 5：与 Phase 0 测试的兼容性

**风险**：修改 `ConditionSpec` 可能影响 Phase 0 的测试。

**缓解**：
- 新字段都有默认值（`default_factory=list`, `default=PreviewSupport.FULLY_SUPPORTED`）
- Phase 0 的测试不需要修改（除非测试显式检查字段数量）
- 运行全部测试验证兼容性
