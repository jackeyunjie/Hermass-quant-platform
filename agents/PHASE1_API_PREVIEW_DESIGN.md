# Phase 1 Strategy Lab API And Preview Design

## Field Dependency Decision

### 结论：**必须在 `ConditionSpec` 增加 `required_columns` 和 `required_tables`**

### 理由

1. **当前问题**：`required_columns` 和 `required_tables` 只在 `TranslationResult` 中返回，意味着必须调用 `translate_condition()` 才能知道数据依赖。这导致：
   - Preview 在翻译前无法拒绝非 MVP 字段（如需要 `positions` 表但 MVP 没有）
   - 无法在 registry 层面做静态数据源校验
   - translator 和 registry 职责重叠但没有显式契约

2. **前移后的优势**：
   - **静态校验**：在翻译前就能判断 DSL 是否依赖不可用数据源
   - **Mock/Real 路由**：Preview Service 可根据 `required_tables` 决定用 mock provider 还是 DuckDB
   - **单一事实源**：registry 成为条件元数据的唯一权威，translator 只做表达式生成

### 设计方案

#### 修改 `ConditionSpec` 增加字段

```python
@dataclass(frozen=True)
class ConditionSpec:
    condition_type: str
    category: ConditionCategory
    params: list[ParamSchema]
    translator: TranslatorDialect
    description: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)
    
    # 新增：数据源依赖声明
    required_columns: list[str] = field(default_factory=list)
    required_tables: list[str] = field(default_factory=list)
```

#### 保持与 translator 不冲突的规则

| 职责 | Registry | Translator |
|------|----------|------------|
| 声明性依赖 | ✅ 静态声明 required_columns/tables | ❌ 不声明 |
| 动态派生列 | ❌ 不处理 | ✅ 根据 params 生成列名（如 `ma_5`） |
| 校验 | ✅ Preview 前静态拒绝不可用表 | ❌ 不负责拒绝 |
| 表达式生成 | ❌ 不生成 | ✅ 生成 SQL/Polars 表达式 |

**关键规则**：
- Registry 中的 `required_columns` 是**通配符/模板**（如 `["ma_{fast}", "ma_{slow}"]`）
- Translator 返回的 `required_columns` 是**实例化后**的具体列名（如 `["ma_5", "ma_20"]`）
- Preview 执行前校验流程：
  1. 从 registry 获取静态依赖 → 检查是否包含非 MVP 表（如 `positions`）
  2. 如果通过，再调用 translator 获取具体列名 → 执行查询

#### MVP 字段白名单

```python
MVP_ALLOWED_TABLES = {"daily_bars", "state_cube", "stock_info"}
MVP_BLOCKED_TABLES = {"positions", "orders", "paper_accounts"}
```

Preview 前拒绝逻辑：
```python
def validate_data_availability(dsl: StrategyDSL, registry: ConditionRegistry) -> list[str]:
    """返回被拒绝的表名列表，空列表表示可用"""
    blocked = []
    for cond in dsl.get_all_conditions():
        spec = registry.get(cond.condition_type)
        for table in spec.required_tables:
            if table in MVP_BLOCKED_TABLES:
                blocked.append(table)
    return list(set(blocked))
```

#### 修改现有 ConditionSpec 示例

```python
ConditionSpec(
    condition_type="ma_golden_cross",
    category=ConditionCategory.ENTRY,
    params=[...],
    translator=TranslatorDialect.BOTH,
    description="Fast MA crosses above slow MA (golden cross)",
    examples=[{"fast_period": 5, "slow_period": 20}],
    required_columns=["ma_{fast_period}", "ma_{slow_period}"],  # 新增
    required_tables=["daily_bars"],  # 新增
),

ConditionSpec(
    condition_type="stop_loss_pct",
    category=ConditionCategory.EXIT,
    params=[...],
    translator=TranslatorDialect.BOTH,
    description="Exit when loss exceeds specified percentage",
    examples=[{"value": 0.08}],
    required_columns=["close", "entry_price"],  # 新增
    required_tables=["daily_bars", "positions"],  # 新增 - MVP 会被拒绝
),
```

---

## Module Design

### 1. `hermass_platform/strategy_lab/api_models.py`

**职责**：定义所有 API 端点的请求/响应 Pydantic 模型。

**核心模型**：

```python
class GenerateStrategyRequest(BaseModel):
    natural_language: str
    user_id: str = ""
    trace_id: str = Field(default_factory=generate_trace_id)

class GenerateStrategyResponse(BaseModel):
    success: bool
    dsl: StrategyDSL | None
    errors: list[ValidationErrorItem]
    trace_id: str

class ValidateStrategyRequest(BaseModel):
    dsl: dict[str, Any]
    levels: list[str] = ["structure", "semantic", "red_line", "completeness"]

class ValidateStrategyResponse(BaseModel):
    passed: bool
    level: str
    errors: list[ValidationErrorItem]
    warnings: list[ValidationWarningItem]
    red_line_result: RedLineResultItem

class PreviewRequest(BaseModel):
    dsl: dict[str, Any]
    data_source: Literal["mock", "duckdb"] = "mock"
    universe: str = "csi300"  # 股票池
    date_range: DateRange | None = None

class PreviewResponse(BaseModel):
    trace_id: str
    sections: dict[str, SectionPreview]  # entry, exit, filters
    required_columns: list[str]
    required_tables: list[str]
    hit_count: int
    sample_count: int
    data_freshness: str | None
    sql_preview: str | None
    errors: list[str]

class SectionPreview(BaseModel):
    condition_expressions: list[str]
    hit_count: int
    sample_count: int

class BacktestRequest(BaseModel):
    dsl: dict[str, Any]
    backtest_config: BacktestConfig

class BacktestResponse(BaseModel):
    job_id: str
    status: Literal["accepted", "running", "completed", "failed"]
    message: str

class GetBacktestResponse(BaseModel):
    job_id: str
    status: str
    result: BacktestResult | None
    error: str | None
```

**不做什么**：
- 不包含业务逻辑
- 不执行校验（只定义数据结构）
- 不处理数据库操作

---

### 2. `hermass_platform/strategy_lab/storage.py`

**职责**：Strategy Lab 数据持久化层，负责策略版本管理和回测结果存储。

**核心接口**：

```python
class StrategyStorage:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_strategy(self, user_id: str, name: str, description: str) -> str:
        """创建策略记录，返回 strategy_id"""
        ...
    
    def save_version(self, strategy_id: str, dsl: StrategyDSL, created_by: str) -> str:
        """保存策略版本，返回 version_id"""
        ...
    
    def get_latest_version(self, strategy_id: str) -> StrategyDSL | None:
        """获取策略最新版本"""
        ...
    
    def list_strategies(self, user_id: str, limit: int = 50) -> list[StrategySummary]:
        """列出用户的策略"""
        ...
    
    def save_backtest_result(self, job_id: str, strategy_id: str, 
                              version_id: str, result: dict) -> None:
        """保存回测结果"""
        ...
    
    def get_backtest_result(self, job_id: str) -> dict | None:
        """获取回测结果"""
        ...
```

**设计原则**：
- 所有方法接受已校验的 DSL 对象
- 不负责校验（调用方必须先通过 validator）
- 使用参数化查询防止 SQL 注入
- 所有写操作返回 ID 用于审计追踪

---

### 3. `hermass_platform/strategy_lab/audit.py`

**职责**：审计日志记录，满足 AGENTS.md 第 7 条可观测性要求。

**核心接口**：

```python
class AuditLogger:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def log_generation(self, trace_id: str, input_text: str, 
                       dsl: StrategyDSL | None, success: bool, 
                       errors: list[str]) -> None:
        """记录策略生成审计"""
        ...
    
    def log_validation(self, trace_id: str, strategy_id: str,
                       dsl_version: str, validation_result: dict) -> None:
        """记录校验审计"""
        ...
    
    def log_preview(self, trace_id: str, strategy_id: str,
                    required_tables: list[str], hit_count: int,
                    data_source: str) -> None:
        """记录预览审计"""
        ...
    
    def log_backtest(self, trace_id: str, job_id: str, 
                     strategy_id: str, status: str) -> None:
        """记录回测审计"""
        ...
```

**审计字段（必须记录）**：
- `trace_id`：全局追踪 ID
- `dsl_version`：DSL schema 版本
- `input_hash`：输入文本的 SHA256（用于去重）
- `output_hash`：输出 DSL 的 SHA256
- `red_line_result`：红线检查结果（pass/fail + triggered rules）
- `timestamp`：操作时间
- `user_id`：操作用户
- `operation`：操作类型（generate/validate/preview/backtest）

---

### 4. `hermass_platform/strategy_lab/preview_service.py`

**职责**：条件预览服务，查询命中数量并返回 SQL 预览。

**核心接口**：

```python
class PreviewService:
    def __init__(self, registry: ConditionRegistry, 
                 duckdb_provider: DuckDBProvider | None = None,
                 mock_provider: MockDataProvider | None = None):
        self.registry = registry
        self.duckdb = duckdb_provider
        self.mock = mock_provider or MockDataProvider()
    
    def preview(self, dsl: StrategyDSL, 
                data_source: Literal["mock", "duckdb"] = "mock",
                universe: str = "csi300",
                date_range: DateRange | None = None) -> PreviewResult:
        """执行条件预览"""
        ...
    
    def _validate_data_availability(self, dsl: StrategyDSL) -> list[str]:
        """校验数据源可用性，返回被拒绝的表"""
        ...
    
    def _build_section_query(self, dsl: StrategyDSL, 
                              section: str) -> QueryPlan:
        """构建单个 section 的查询计划"""
        ...
    
    def _execute_query(self, query: QueryPlan, 
                       data_source: str) -> QueryResult:
        """执行查询（mock 或 duckdb）"""
        ...
```

**关键流程**（见下方 Preview Flow 章节）

---

### 5. Web 路由：`web/strategy_lab_routes.py`

**职责**：HTTP 路由层，只做参数解析、调用 service、返回响应。

**设计原则**：
- 路由函数不超过 20 行
- 所有业务逻辑在 service 层
- 错误统一处理，返回标准格式

```python
@router.post("/api/strategy-lab/generate")
async def generate_strategy(request: GenerateStrategyRequest):
    # 1. 解析参数
    # 2. 调用 StrategyLabService.generate()
    # 3. 记录审计
    # 4. 返回响应
    ...

@router.post("/api/strategy-lab/validate")
async def validate_strategy(request: ValidateStrategyRequest):
    # 1. 反序列化 DSL
    # 2. 调用 validate_dsl()
    # 3. 记录审计
    # 4. 返回响应
    ...

@router.post("/api/strategy-lab/preview")
async def preview_strategy(request: PreviewRequest):
    # 1. 反序列化 DSL
    # 2. 校验 DSL
    # 3. 调用 PreviewService.preview()
    # 4. 记录审计
    # 5. 返回响应
    ...

@router.post("/api/strategy-lab/backtest")
async def start_backtest(request: BacktestRequest):
    # 1. 反序列化 DSL
    # 2. 校验 DSL
    # 3. 创建回测任务
    # 4. 记录审计
    # 5. 返回 job_id
    ...

@router.get("/api/strategy-lab/backtest/{job_id}")
async def get_backtest_result(job_id: str):
    # 1. 查询回测结果
    # 2. 返回状态和结果
    ...
```

---

## API Request/Response Models

### POST `/api/strategy-lab/generate`

**Phase 1 行为**：使用模板/规则 stub，不调用 LLM。

**Request**:
```json
{
  "natural_language": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
  "user_id": "user_123",
  "trace_id": "gen_abc123"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "dsl": {
    "strategy_id": "ma_crossover_v1",
    "name": "MA交叉策略",
    "schema_version": "strategy_dsl_v2",
    "entry": [...],
    "exit": [...],
    "risk": {...}
  },
  "errors": [],
  "trace_id": "gen_abc123"
}
```

**Response (Failure)**:
```json
{
  "success": false,
  "dsl": null,
  "errors": [
    {
      "code": "GENERATE_FAILED",
      "message": "无法解析止损条件"
    }
  ],
  "trace_id": "gen_abc123"
}
```

---

### POST `/api/strategy-lab/validate`

**Request**:
```json
{
  "dsl": {
    "strategy_id": "ma_crossover_v1",
    "name": "MA交叉策略",
    "schema_version": "strategy_dsl_v2",
    "entry": [...],
    "exit": [...],
    "risk": {...}
  },
  "levels": ["structure", "semantic", "red_line", "completeness"]
}
```

**Response (Passed)**:
```json
{
  "passed": true,
  "level": "structure",
  "errors": [],
  "warnings": [
    {
      "code": "STRUCT_NO_DESCRIPTION",
      "message": "Strategy has no description"
    }
  ],
  "red_line_result": {
    "passed": true,
    "triggered_rules": [],
    "details": []
  }
}
```

**Response (Failed - Red Line)**:
```json
{
  "passed": false,
  "level": "red_line",
  "errors": [
    {
      "level": "red_line",
      "code": "RL_EXIT_MUST_HAVE_STOP_LOSS",
      "message": "Red line violated: exit conditions must include a stop_loss_pct condition"
    }
  ],
  "warnings": [],
  "red_line_result": {
    "passed": false,
    "triggered_rules": ["RL_EXIT_MUST_HAVE_STOP_LOSS"],
    "details": [...]
  }
}
```

---

### POST `/api/strategy-lab/preview`

**Request**:
```json
{
  "dsl": {
    "strategy_id": "ma_crossover_v1",
    "name": "MA交叉策略",
    "schema_version": "strategy_dsl_v2",
    "entry": [
      {
        "condition_type": "ma_golden_cross",
        "params": {"fast_period": 5, "slow_period": 20},
        "logic": "and",
        "weight": 1.0
      }
    ],
    "exit": [
      {
        "condition_type": "ma_death_cross",
        "params": {"fast_period": 5, "slow_period": 20},
        "logic": "and",
        "weight": 1.0
      },
      {
        "condition_type": "stop_loss_pct",
        "params": {"value": 0.08},
        "logic": "or",
        "weight": 1.0
      }
    ],
    "risk": {
      "risk_per_trade": 0.02,
      "max_position_pct": 0.20,
      "stop_loss_required": true
    }
  },
  "data_source": "mock",
  "universe": "csi300",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  }
}
```

**Response (Success - Mock)**:
```json
{
  "trace_id": "prev_xyz789",
  "sections": {
    "entry": {
      "condition_expressions": [
        "(ma_5 > ma_20 AND LAG(ma_5) <= LAG(ma_20))"
      ],
      "hit_count": 142,
      "sample_count": 3000
    },
    "exit": {
      "condition_expressions": [
        "(ma_5 < ma_20 AND LAG(ma_5) >= LAG(ma_20))",
        "OR (close <= entry_price * 0.92)"
      ],
      "hit_count": 98,
      "sample_count": 3000
    }
  },
  "required_columns": ["ma_5", "ma_20", "close", "entry_price"],
  "required_tables": ["daily_bars", "positions"],
  "hit_count": 142,
  "sample_count": 3000,
  "data_freshness": "2024-12-31",
  "sql_preview": "SELECT ... FROM daily_bars WHERE ...",
  "errors": []
}
```

**Response (Failure - Blocked Table)**:
```json
{
  "trace_id": "prev_xyz789",
  "sections": {},
  "required_columns": [],
  "required_tables": ["daily_bars", "positions"],
  "hit_count": 0,
  "sample_count": 0,
  "data_freshness": null,
  "sql_preview": null,
  "errors": [
    "Preview rejected: table 'positions' is not available in MVP"
  ]
}
```

---

### POST `/api/strategy-lab/backtest`

**Phase 1 行为**：返回 accepted/job stub，不跑真实回测。

**Request**:
```json
{
  "dsl": {...},
  "backtest_config": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 1000000,
    "universe": "csi300"
  }
}
```

**Response**:
```json
{
  "job_id": "bt_20240606_abc123",
  "status": "accepted",
  "message": "Backtest job queued (stub in Phase 1)"
}
```

---

### GET `/api/strategy-lab/backtest/{job_id}`

**Response (Completed)**:
```json
{
  "job_id": "bt_20240606_abc123",
  "status": "completed",
  "result": {
    "total_return": 0.1523,
    "annual_return": 0.1487,
    "max_drawdown": 0.0821,
    "sharpe_ratio": 1.82,
    "total_trades": 47,
    "win_rate": 0.638
  },
  "error": null
}
```

**Response (Running)**:
```json
{
  "job_id": "bt_20240606_abc123",
  "status": "running",
  "result": null,
  "error": null
}
```

---

## Preview Flow

### 完整流程

```
用户请求 Preview
    ↓
1. 反序列化 DSL (api_models.py)
    ↓
2. Pydantic 结构校验 (dsl_schema.py)
    ├─ 失败 → 返回 400 + 错误
    └─ 成功 ↓
3. 语义校验 + 红线检查 (dsl_validator.py)
    ├─ 红线失败 → 返回 400 + triggered rules
    └─ 通过 ↓
4. 数据源可用性校验 (preview_service.py)
    ├─ 获取所有条件的 required_tables (registry)
    ├─ 检查是否包含 MVP_BLOCKED_TABLES
    ├─ 包含 → 返回 400 + "Preview rejected: table 'X' not available"
    └─ 不包含 ↓
5. 翻译条件为 SQL (condition_translator.py)
    ├─ 遍历 entry/exit/filters sections
    ├─ 每个条件调用 translate_condition()
    └─ 收集 required_columns (实例化后)
    ↓
6. 构建查询计划 (preview_service.py)
    ├─ 选择数据源 (mock 或 duckdb)
    ├─ 组合 SQL 表达式 (AND/OR logic)
    └─ 生成完整 SQL（禁止 SELECT *）
    ↓
7. 执行查询
    ├─ Mock 模式：返回 deterministic 模拟数据
    └─ DuckDB 模式：执行真实查询
    ↓
8. 组装响应
    ├─ 每个 section 的 condition_expressions
    ├─ hit_count / sample_count
    ├─ required_columns / required_tables
    ├─ data_freshness
    └─ sql_preview
    ↓
9. 记录审计日志 (audit.py)
    ├─ trace_id
    ├─ dsl_version
    ├─ input_hash / output_hash
    ├─ red_line_result
    └─ hit_count / sample_count
    ↓
10. 返回 PreviewResponse
```

### Mock Provider 设计

```python
class MockDataProvider:
    """Deterministic mock data provider for preview without DuckDB."""
    
    def query(self, sql: str, tables: list[str]) -> QueryResult:
        """返回确定性模拟结果"""
        # 基于 SQL hash 生成确定性命中数
        sql_hash = hash(sql) % 1000
        hit_count = (sql_hash % 200) + 50  # 50-249
        sample_count = 3000  # 固定样本
        
        return QueryResult(
            hit_count=hit_count,
            sample_count=sample_count,
            data_freshness="2024-12-31",  # 固定日期
        )
```

### SQL 构建规则

**禁止**：
- `SELECT *`
- 子查询超过 2 层
- JOIN 超过 3 个表

**必须**：
- 明确列出所需列
- 使用 WHERE 过滤
- 添加 LIMIT 防止全表扫描

```python
def build_preview_query(section_conditions: list[ConditionBlock],
                         registry: ConditionRegistry) -> str:
    """构建预览 SQL"""
    columns = []
    where_clauses = []
    
    for cond in section_conditions:
        result = translate_condition(cond, registry, dialect="duckdb")
        columns.extend(result.required_columns)
        where_clauses.append(result.sql_expr)
    
    # 去重列
    unique_columns = list(dict.fromkeys(columns))
    
    # 构建 SQL（禁止 SELECT *）
    col_str = ", ".join(unique_columns)
    where_str = " AND ".join(f"({w})" for w in where_clauses if w)
    
    return f"SELECT {col_str} FROM daily_bars WHERE {where_str} LIMIT 10000"
```

---

## StrategyLab DB DDL

### `migrations/strategy_lab/001_init.sql`

```sql
-- StrategyLab MVP DDL
-- 只包含 user_strategies, strategy_versions, strategy_backtests, strategy_audit_log
-- 不包含：paper orders, positions, full agent judgments

-- 1. 用户策略主表
CREATE TABLE IF NOT EXISTS user_strategies (
    strategy_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL CHECK (length(name) <= 64),
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived', 'rejected')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_strategies_user_id ON user_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_user_strategies_status ON user_strategies(status);

-- 2. 策略版本表
CREATE TABLE IF NOT EXISTS strategy_versions (
    version_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL REFERENCES user_strategies(strategy_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    dsl_json TEXT NOT NULL,  -- 完整 DSL JSON
    dsl_version TEXT NOT NULL DEFAULT 'strategy_dsl_v2',
    schema_hash TEXT NOT NULL,  -- DSL JSON 的 SHA256
    validation_result TEXT,  -- 校验结果 JSON
    red_line_result TEXT,  -- 红线检查 JSON
    created_by TEXT NOT NULL,  -- Agent 或用户 ID
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_strategy_versions_strategy_id ON strategy_versions(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_versions_dsl_version ON strategy_versions(dsl_version);

-- 3. 回测结果表
CREATE TABLE IF NOT EXISTS strategy_backtests (
    job_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL REFERENCES user_strategies(strategy_id) ON DELETE CASCADE,
    version_id TEXT NOT NULL REFERENCES strategy_versions(version_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    config_json TEXT NOT NULL,  -- 回测配置 JSON
    result_json TEXT,  -- 回测结果 JSON（完成后写入）
    error_message TEXT,  -- 失败时记录错误
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategy_backtests_strategy_id ON strategy_backtests(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_backtests_status ON strategy_backtests(status);
CREATE INDEX IF NOT EXISTS idx_strategy_backtests_created_at ON strategy_backtests(created_at);

-- 4. 审计日志表
CREATE TABLE IF NOT EXISTS strategy_audit_log (
    log_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('generate', 'validate', 'preview', 'backtest')),
    strategy_id TEXT,  -- 可选，生成前可能还没有 strategy_id
    version_id TEXT,  -- 可选
    dsl_version TEXT,  -- DSL schema 版本
    input_hash TEXT,  -- 输入文本 SHA256
    output_hash TEXT,  -- 输出 DSL SHA256
    red_line_result TEXT,  -- 红线检查结果 JSON
    metadata_json TEXT,  -- 额外元数据（如 hit_count, sample_count）
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_trace_id ON strategy_audit_log(trace_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON strategy_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON strategy_audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_strategy_id ON strategy_audit_log(strategy_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON strategy_audit_log(created_at);

-- 辅助函数：自动生成 trace_id
CREATE OR REPLACE FUNCTION generate_trace_id()
RETURNS TEXT AS $$
BEGIN
    RETURN 'trace_' || to_char(CURRENT_TIMESTAMP, 'YYYYMMDD_HH24MISS') || '_' || substr(md5(random()::text), 1, 8);
END;
$$ LANGUAGE plpgsql;
```

---

## Tests

### `test_storage.py` - 至少 5 个测试点

1. **创建策略并返回 ID**
   - Given: user_id, name, description
   - When: `create_strategy()`
   - Then: 返回非空 strategy_id，数据库中存在记录

2. **保存策略版本并自动递增版本号**
   - Given: 已有策略 v1
   - When: `save_version()` 再次调用
   - Then: 版本号自动变为 v2，两个版本都可查询

3. **获取最新版本**
   - Given: 策略有 v1, v2, v3
   - When: `get_latest_version()`
   - Then: 返回 v3 的 DSL

4. **级联删除**
   - Given: 策略有关联的版本和回测记录
   - When: 删除策略
   - Then: 版本和回测记录也被删除

5. **列出用户策略（分页）**
   - Given: 用户有 60 个策略
   - When: `list_strategies(user_id, limit=50)`
   - Then: 返回 50 个，按 created_at 倒序

6. **保存和查询回测结果**
   - Given: job_id, strategy_id, 回测结果 dict
   - When: `save_backtest_result()` 后 `get_backtest_result()`
   - Then: 返回相同结果

---

### `test_audit.py` - 至少 5 个测试点

1. **记录生成审计**
   - Given: trace_id, input_text, DSL, 成功
   - When: `log_generation()`
   - Then: 数据库中有记录，input_hash 正确

2. **记录校验审计（含红线结果）**
   - Given: trace_id, validation_result, red_line_result
   - When: `log_validation()`
   - Then: red_line_result JSON 可查询

3. **记录预览审计（含命中数）**
   - Given: trace_id, hit_count, sample_count
   - When: `log_preview()`
   - Then: metadata_json 中包含命中统计

4. **trace_id 可追踪完整链路**
   - Given: 同一 trace_id 的 generate → validate → preview
   - When: 查询 `WHERE trace_id = ?`
   - Then: 返回 3 条记录，操作类型不同

5. **input_hash 去重**
   - Given: 相同输入文本两次生成
   - When: 比较 input_hash
   - Then: hash 值相同

6. **DSL version 记录**
   - Given: 使用 strategy_dsl_v2 生成
   - When: 查询审计记录
   - Then: dsl_version = 'strategy_dsl_v2'

---

### `test_preview_service.py` - 至少 5 个测试点

1. **Mock 模式返回确定性结果**
   - Given: 相同 DSL，两次调用 preview(mock)
   - When: 比较 hit_count
   - Then: 结果相同（deterministic）

2. **拒绝非 MVP 表**
   - Given: DSL 包含 `stop_loss_pct`（需要 positions 表）
   - When: `preview()`
   - Then: 返回错误 "Preview rejected: table 'positions' not available"

3. **SQL 预览不包含 SELECT ***
   - Given: 合法 DSL
   - When: preview 返回 sql_preview
   - Then: SQL 中不包含 `SELECT *`

4. **多个条件组合（AND/OR）**
   - Given: entry 有 2 个条件（logic: and）
   - When: preview
   - Then: SQL WHERE 包含 AND 连接

5. **数据源 freshness 返回**
   - Given: DuckDB 模式
   - When: preview
   - Then: data_freshness 为最新数据日期

6. **空条件列表处理**
   - Given: section 为空列表
   - When: preview
   - Then: 该 section hit_count = 0，不报错

---

### `test_api_models.py` - 至少 5 个测试点

1. **GenerateStrategyRequest 验证 trace_id 自动生成**
   - Given: 不传 trace_id
   - When: 构造请求
   - Then: trace_id 自动生成且非空

2. **ValidateStrategyRequest 反序列化 DSL**
   - Given: dict 格式的 DSL
   - When: 反序列化为 StrategyDSL
   - Then: 可通过 Pydantic 校验

3. **PreviewRequest 默认数据源为 mock**
   - Given: 不传 data_source
   - When: 构造请求
   - Then: data_source = "mock"

4. **PreviewResponse 字段完整性**
   - Given: 成功 preview
   - When: 检查响应
   - Then: 包含 trace_id, sections, hit_count, sample_count 等所有必填字段

5. **BacktestResponse job_id 格式**
   - Given: 创建回测任务
   - When: 返回响应
   - Then: job_id 格式为 `bt_YYYYMMDD_xxxxxx`

6. **错误响应格式统一**
   - Given: 校验失败
   - When: 返回错误
   - Then: errors 数组包含 code 和 message

---

## Implementation Order For Codex

### Phase 1 实现顺序（建议 5 步）

**Step 1: 修改 ConditionSpec 增加字段依赖**
- 文件：`condition_registry.py`
- 任务：
  1. 增加 `required_columns` 和 `required_tables` 字段
  2. 更新所有 MVP conditions 的声明
  3. 更新测试 `test_condition_registry.py`
- 验收：测试通过，registry 包含完整依赖声明

**Step 2: 实现 api_models.py**
- 文件：`hermass_platform/strategy_lab/api_models.py`
- 任务：
  1. 定义所有请求/响应 Pydantic 模型
  2. 添加 trace_id 自动生成
  3. 编写 `test_api_models.py`
- 验收：模型可序列化/反序列化，测试通过

**Step 3: 实现 storage.py 和 DDL**
- 文件：
  - `migrations/strategy_lab/001_init.sql`
  - `hermass_platform/strategy_lab/storage.py`
- 任务：
  1. 执行 DDL 创建表
  2. 实现 StrategyStorage 类
  3. 编写 `test_storage.py`
- 验收：CRUD 操作正常，测试通过

**Step 4: 实现 audit.py**
- 文件：`hermass_platform/strategy_lab/audit.py`
- 任务：
  1. 实现 AuditLogger 类
  2. 确保所有操作记录必要字段
  3. 编写 `test_audit.py`
- 验收：审计记录可查询，trace_id 链路完整

**Step 5: 实现 preview_service.py 和 Web 路由**
- 文件：
  - `hermass_platform/strategy_lab/preview_service.py`
  - `web/strategy_lab_routes.py`
- 任务：
  1. 实现 PreviewService（mock + duckdb）
  2. 实现数据源可用性校验
  3. 实现 5 个 API 端点
  4. 编写 `test_preview_service.py`
- 验收：
  - Mock 模式可返回确定性结果
  - 非 MVP 表被拒绝
  - SQL 预览不含 SELECT *
  - 所有 API 端点可调用

---

## Non-MVP Items

### Phase 1 明确不做

| 项目 | 原因 | 预留方式 |
|------|------|----------|
| 真实 LLM 调用 | Phase 1 只验证链路，不调用外部模型 | `generate` 使用模板 stub |
| 完整回测引擎 | Phase 2 才实现 | `backtest` 返回 accepted stub |
| Agent Debate | 超出 MVP 范围 | 预留 `agent_judgments` 表但未创建 |
| Paper Trading | 执行层 Phase 3 才做 | `execution.mode` 只支持 "paper" 枚举 |
| positions/orders 表 | 回测前不需要真实持仓 | DDL 不创建，preview 拒绝依赖这些表的条件 |
| 多用户权限 | MVP 单用户 | `user_id` 字段预留但不做权限校验 |
| 实时数据流 | MVP 用静态数据 | 预留 `data_freshness` 字段 |
| 条件权重评分 | MVP 只用布尔命中 | `weight` 字段保留但不参与预览计算 |

### Phase 1 可选预留（如果时间允许）

- `generate` 支持简单的规则模板（如 "MA{fast}上穿MA{slow}" → DSL）
- `preview` 支持多股票池（目前只支持 csi300）
- 基础的性能监控（请求耗时记录）

---

## 总结

Phase 1 核心交付物：

1. ✅ **字段依赖前移到 ConditionSpec** - 解决 Phase 0 遗留点
2. ✅ **API 模型定义** - 5 个端点的请求/响应结构
3. ✅ **Storage 层** - 策略版本管理和回测结果存储
4. ✅ **Audit 层** - 完整的审计日志（满足 AGENTS.md 可观测性要求）
5. ✅ **Preview Service** - 支持 mock 和 DuckDB 两种模式
6. ✅ **Web 路由** - 纯路由层，无业务逻辑
7. ✅ **DDL** - 4 张 MVP 表
8. ✅ **测试方案** - 4 个测试文件，每个至少 5 个测试点

Phase 1 验收标准：

- 所有测试通过
- API 端点可调用（即使返回 stub）
- 红线检查在 preview 前执行
- 非 MVP 表被拒绝
- 每次操作都有审计记录
- SQL 预览不含 SELECT *
