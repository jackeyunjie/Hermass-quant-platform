# MVP E2E Sample Contracts — 2026-06-08

本文档冻结 3 个代表性中文策略样例，定义端到端服务级 contract，供 Codex 直接实现。

链路：`中文策略输入 -> DSL v2 -> Schema/Pydantic 校验 -> 红线检查 -> Preview -> Light Backtest -> Audit -> 问题归档`

---

## 1. 冻结样例总览

| sample_id | 中文输入 | 复杂度 | 目标 |
|---|---|---|---|
| `sample_ma_5_20_stop_8` | MA5上穿MA20买入，跌破MA10卖出，止损8% | simple | 覆盖 MVP 验收底线第 1 条 |
| `sample_state_volume_stop_8_take_15` | D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，止损8%，止盈15% | medium | 覆盖 state_hex_in、volume_ratio、stop_loss_pct、take_profit_pct |
| `sample_ma_state_limit_filter` | MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，跌破MA10或止损8%卖出 | bounded_complex | 覆盖组合条件、filter、OR exit |

---

## 2. 样例 1：sample_ma_5_20_stop_8

### 2.1 原始中文输入

```
MA5上穿MA20买入，跌破MA10卖出，止损8%
```

### 2.2 复杂度

simple

### 2.3 期望 DSL v2 完整 JSON

```json
{
  "strategy_id": "sample_ma_5_20_stop_8",
  "name": "MA5上穿MA20策略",
  "schema_version": "strategy_dsl_v2",
  "description": "MA5上穿MA20买入，跌破MA10卖出，止损8%",
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
      "condition_type": "price_cross_ma",
      "params": {"timeframe": "D1", "ma_period": 10, "direction": "below"},
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
  "filters": [
    {
      "condition_type": "limit_up_filter",
      "params": {"allow": false},
      "logic": "and",
      "weight": 1.0
    }
  ],
  "risk": {
    "risk_per_trade": 0.02,
    "max_position_pct": 0.20,
    "stop_loss_required": true
  }
}
```

### 2.4 使用到的 condition types

- `ma_golden_cross` (ENTRY)
- `price_cross_ma` (ENTRY category, used in exit — 会产生 SEMANTIC_WRONG_SECTION warning)
- `stop_loss_pct` (EXIT)
- `limit_up_filter` (FILTER)

### 2.5 默认参数来源

| 字段 | 值 | 来源 |
|---|---|---|
| `risk.risk_per_trade` | 0.02 | MVP 默认值（未在中文输入中提及） |
| `risk.max_position_pct` | 0.20 | MVP 默认值（未在中文输入中提及仓位） |
| `risk.stop_loss_required` | true | 硬编码，必须 true |
| `filters.limit_up_filter.allow` | false | MVP 默认排除涨停 |

### 2.6 预期 validator 结果

- `passed`: true
- `level`: structure
- `warnings`: 包含 `SEMANTIC_WRONG_SECTION`（`price_cross_ma` 在 exit section）
- `errors`: []

### 2.7 预期 red_line_result

```json
{
  "passed": true,
  "triggered_rules": [],
  "details": []
}
```

### 2.8 预期 preview 行为（mock 模式）

- `overall.overall_status`: "partial"（exit 含 `stop_loss_pct`，标记 requires_backtest_context）
- `entry` section:
  - `ma_golden_cross`: `preview_support="fully_supported"`, `estimated_hits=42`
- `exit` section:
  - `price_cross_ma`: `preview_support="fully_supported"`, `estimated_hits=55`
  - `stop_loss_pct`: `preview_support="requires_backtest_context"`, `estimated_hits=360`（8% * 1.5 * 3000）
  - `has_context_required`: true
- `filters` section:
  - `limit_up_filter`: `preview_support="fully_supported"`, `estimated_hits=500`

### 2.9 预期 light backtest 最小输出

```json
{
  "status": "partial",
  "mode": "light_stub",
  "metrics": {
    "total_return": 0.0,
    "annual_return": 0.0,
    "max_drawdown": 0.0,
    "sharpe_ratio": 0.0,
    "win_rate": 0.0,
    "profit_factor": 0.0,
    "trade_count": 0
  },
  "risk_flags": ["STUB_BACKTEST: Not yet implemented"]
}
```

### 2.10 预期 audit operations 顺序

1. `generation` — input_hash = SHA256(中文输入), output_hash = SHA256(DSL)
2. `validation` — red_line_result = {"passed": true, ...}
3. `preview` — metadata 含 hit_count, sample_count
4. `backtest` — metadata 含 job_id, status

### 2.11 明确不支持的解释

- 不支持自定义均线周期以外的参数（如 EMA、WMA）。
- 不支持多时间框架组合（如“日线MA5上穿周线MA20”）。

---

## 3. 样例 2：sample_state_volume_stop_8_take_15

### 3.1 原始中文输入

```
D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，止损8%，止盈15%
```

### 3.2 复杂度

medium

### 3.3 期望 DSL v2 完整 JSON

```json
{
  "strategy_id": "sample_state_volume_stop_8_take_15",
  "name": "状态成交量策略",
  "schema_version": "strategy_dsl_v2",
  "description": "D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，止损8%，止盈15%",
  "entry": [
    {
      "condition_type": "state_hex_in",
      "params": {"timeframe": "D1", "values": ["0x21", "0x23"]},
      "logic": "and",
      "weight": 1.0
    },
    {
      "condition_type": "volume_ratio",
      "params": {"lookback": 20, "operator": ">", "value": 1.5},
      "logic": "and",
      "weight": 1.0
    }
  ],
  "exit": [
    {
      "condition_type": "stop_loss_pct",
      "params": {"value": 0.08},
      "logic": "or",
      "weight": 1.0
    },
    {
      "condition_type": "take_profit_pct",
      "params": {"value": 0.15},
      "logic": "or",
      "weight": 1.0
    }
  ],
  "filters": [
    {
      "condition_type": "limit_up_filter",
      "params": {"allow": false},
      "logic": "and",
      "weight": 1.0
    }
  ],
  "risk": {
    "risk_per_trade": 0.02,
    "max_position_pct": 0.20,
    "stop_loss_required": true
  }
}
```

### 3.4 使用到的 condition types

- `state_hex_in` (ENTRY)
- `volume_ratio` (ENTRY)
- `stop_loss_pct` (EXIT)
- `take_profit_pct` (EXIT)
- `limit_up_filter` (FILTER)

### 3.5 默认参数来源

| 字段 | 值 | 来源 |
|---|---|---|
| `risk.risk_per_trade` | 0.02 | MVP 默认值 |
| `risk.max_position_pct` | 0.20 | MVP 默认值 |
| `filters.limit_up_filter.allow` | false | MVP 默认排除涨停 |

### 3.6 预期 validator 结果

- `passed`: true
- `level`: structure
- `warnings`: []
- `errors`: []

### 3.7 预期 red_line_result

```json
{
  "passed": true,
  "triggered_rules": [],
  "details": []
}
```

### 3.8 预期 preview 行为（mock 模式）

- `overall.overall_status`: "partial"（exit 含 stop_loss_pct + take_profit_pct）
- `entry` section:
  - `state_hex_in`: `preview_support="fully_supported"`, `estimated_hits=120`
  - `volume_ratio`: `preview_support="fully_supported"`, `estimated_hits=67`
- `exit` section:
  - `stop_loss_pct`: `preview_support="requires_backtest_context"`, `estimated_hits=360`
  - `take_profit_pct`: `preview_support="requires_backtest_context"`, `estimated_hits=1050`（0.5 - 0.15 = 0.35; 0.35 * 3000）
  - `has_context_required`: true

### 3.9 预期 light backtest 最小输出

同样例 1（stub 模式），但 `risk_flags` 可能额外标注 "take_profit_present"。

### 3.10 预期 audit operations 顺序

同样例 1：generation -> validation -> preview -> backtest

### 3.11 明确不支持的解释

- 不支持状态值范围（如 "0x20-0x30"），必须用枚举列表。
- 不支持成交量与特定日期对比（如 "比昨日放大"），只能用 N 日均量。

---

## 4. 样例 3：sample_ma_state_limit_filter

### 4.1 原始中文输入

```
MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，跌破MA10或止损8%卖出
```

### 4.2 复杂度

bounded_complex

### 4.3 期望 DSL v2 完整 JSON

```json
{
  "strategy_id": "sample_ma_state_limit_filter",
  "name": "MA状态组合策略",
  "schema_version": "strategy_dsl_v2",
  "description": "MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，跌破MA10或止损8%卖出",
  "entry": [
    {
      "condition_type": "ma_golden_cross",
      "params": {"fast_period": 5, "slow_period": 20},
      "logic": "and",
      "weight": 1.0
    },
    {
      "condition_type": "state_ef_count",
      "params": {"operator": ">=", "value": 2},
      "logic": "and",
      "weight": 1.0
    }
  ],
  "exit": [
    {
      "condition_type": "price_cross_ma",
      "params": {"timeframe": "D1", "ma_period": 10, "direction": "below"},
      "logic": "or",
      "weight": 1.0
    },
    {
      "condition_type": "stop_loss_pct",
      "params": {"value": 0.08},
      "logic": "or",
      "weight": 1.0
    }
  ],
  "filters": [
    {
      "condition_type": "limit_up_filter",
      "params": {"allow": false},
      "logic": "and",
      "weight": 1.0
    }
  ],
  "risk": {
    "risk_per_trade": 0.02,
    "max_position_pct": 0.20,
    "stop_loss_required": true
  }
}
```

### 4.4 使用到的 condition types

- `ma_golden_cross` (ENTRY)
- `state_ef_count` (ENTRY)
- `price_cross_ma` (ENTRY category, used in exit)
- `stop_loss_pct` (EXIT)
- `limit_up_filter` (FILTER)

### 4.5 默认参数来源

同样例 1。

### 4.6 预期 validator 结果

- `passed`: true
- `level`: structure
- `warnings`: 包含 `SEMANTIC_WRONG_SECTION`（`price_cross_ma` 在 exit section）
- `errors`: []

### 4.7 预期 red_line_result

```json
{
  "passed": true,
  "triggered_rules": [],
  "details": []
}
```

### 4.8 预期 preview 行为（mock 模式）

- `overall.overall_status`: "partial"
- `entry` section:
  - `ma_golden_cross`: `estimated_hits=42`
  - `state_ef_count`: `estimated_hits=89`
- `exit` section:
  - `price_cross_ma`: `estimated_hits=55`
  - `stop_loss_pct`: `preview_support="requires_backtest_context"`, `estimated_hits=360`
  - `has_context_required`: true
- `filters` section:
  - `limit_up_filter`: `estimated_hits=500`

### 4.9 预期 light backtest 最小输出

同样例 1。

### 4.10 预期 audit operations 顺序

同样例 1。

### 4.11 明确不支持的解释

- 不支持 "EF数量不少于2" 以外的状态子条件（如 "EF类型包含A"）。
- 不支持买入后动态调整 filter（如 "持有期间排除ST"）。

---

## 5. MVP 中文输入到 DSL 的确定性映射规则

### 5.1 支持的中文短语表

| 中文短语 | condition_type | 参数抽取规则 | 备注 |
|---|---|---|---|
| MA{N}上穿MA{M} | `ma_golden_cross` | fast_period=N, slow_period=M | N < M，否则 warning |
| MA{N}下穿MA{M} | `ma_death_cross` | fast_period=N, slow_period=M | 仅用于 exit |
| 跌破MA{N} | `price_cross_ma` | timeframe="D1", ma_period=N, direction="below" | 用于 exit，产生 semantic warning |
| 上穿MA{N} | `price_cross_ma` | timeframe="D1", ma_period=N, direction="above" | 用于 entry |
| D1状态属于{列表} | `state_hex_in` | timeframe="D1", values=[列表] | 状态值以 0x 开头 |
| {TF}状态EF数量{op}{V} | `state_ef_count` | operator=op, value=V | TF ∈ {D1, W1, MN1} |
| 成交量放大到{N}日均量{R}倍以上 | `volume_ratio` | lookback=N, operator=">", value=R | R 为浮点数 |
| 止损{P}% | `stop_loss_pct` | value=P/100 | 必须存在，否则 red line fail |
| 止盈{P}% | `take_profit_pct` | value=P/100 | 可选 |
| 排除涨停股票 | `limit_up_filter` | allow=false | MVP 默认 filter |
| 允许涨停股票 | `limit_up_filter` | allow=true | 不推荐 |

### 5.2 默认参数规则

| 字段 | 默认值 | 触发条件 |
|---|---|---|
| `risk.max_position_pct` | 0.20 | 中文输入未提及仓位时 |
| `risk.risk_per_trade` | 0.02 | 中文输入未提及单笔风险时 |
| `risk.stop_loss_required` | true | 永远 true |
| `filters` | `[limit_up_filter(allow=false)]` | 中文输入未提及 filter 时 |

### 5.3 缺少止损的处理

如果中文输入中未提取到 `止损{P}%` 短语：

1. NL parser 应尝试生成 `stop_loss_pct`，但无参数可用。
2. 若 DSL 生成后 `exit` 中不含 `stop_loss_pct`，则红线检查失败：
   - `RL_EXIT_MUST_HAVE_STOP_LOSS` 触发
   - `validation.passed = false`
   - `level = red_line`
3. 该链路写入 audit（generation + validation），不执行 preview/backtest。

### 5.4 "跌破 MA10 卖出"映射裁决

**裁决**：使用现有 `price_cross_ma` 条件，参数 `{"timeframe": "D1", "ma_period": 10, "direction": "below"}`。

- 不需要新增 condition type。
- `price_cross_ma` 的 category 是 ENTRY，用于 exit section 时 `dsl_validator` 会产生 `SEMANTIC_WRONG_SECTION` warning，但不阻止执行。
- 若后续需要消除此 warning，可在 registry 中新增 `price_below_ma`（EXIT category），但本周不做。

---

## 6. E2E Runner Contract

### 6.1 文件路径

`hermass_platform/strategy_lab/e2e_runner.py`

### 6.2 接口签名

```python
from typing import Any, Literal

from pydantic import BaseModel, Field

from .api_models import (
    BacktestMetrics,
    BacktestResponse,
    PreviewResponse,
    ValidateStrategyResponse,
)
from .dsl_schema import StrategyDSL


class MvpE2EResult(BaseModel):
    """端到端执行结果。"""

    model_config = {"extra": "forbid"}

    trace_id: str = Field(..., description="全局追踪 ID")
    strategy_id: str = Field(..., description="策略标识")
    natural_language: str = Field(..., description="原始中文输入")

    # DSL 生成
    dsl: StrategyDSL | None = Field(default=None, description="生成的 DSL")
    generation_errors: list[str] = Field(default_factory=list)

    # 校验
    validation: ValidateStrategyResponse | None = Field(default=None)
    red_line_result: dict[str, Any] = Field(default_factory=dict)

    # Preview
    preview: PreviewResponse | None = Field(default=None)

    # Light Backtest
    backtest: BacktestResponse | None = Field(default=None)
    backtest_mode: Literal["light_stub", "light_mock", "full"] = Field(
        default="light_stub",
        description="回测执行模式",
    )

    # Audit
    audit_records: list[dict[str, Any]] = Field(default_factory=list)

    # 问题归档
    problem_items: list[dict[str, Any]] = Field(default_factory=list)

    # 整体状态
    status: Literal["success", "partial", "failed"] = Field(default="failed")
    stage_reached: Literal[
        "generation", "validation", "preview", "backtest", "complete"
    ] = Field(default="generation", description="执行到的最远距离")


def run_mvp_e2e_sample(
    natural_language: str,
    strategy_id: str,
    *,
    trace_id: str,
    audit_db_path: str,
    storage_db_path: str,
    preview_data_source: Literal["mock", "duckdb"] = "mock",
    preview_duckdb_path: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> MvpE2EResult:
    """执行单个 MVP E2E 样例。

    执行顺序：
        1. NL -> DSL（模板/规则生成，无 LLM）
        2. Schema/Pydantic 校验
        3. 红线检查
        4. Preview（仅红线通过时）
        5. Light Backtest（仅红线通过时）
        6. Audit 记录
        7. 问题归档（如有）

    失败链路也必须写 audit。例如缺少止损时，写入 generation + validation，
    不执行 preview/backtest。
    """
    ...
```

### 6.3 执行流程伪代码

```python
def run_mvp_e2e_sample(nl, strategy_id, *, trace_id, ...):
    result = MvpE2EResult(trace_id=trace_id, strategy_id=strategy_id, natural_language=nl)
    audit_logger = StrategyAuditLogger(audit_db_path)
    storage = StrategyLabStorage(storage_db_path)

    # Step 1: Generation
    try:
        dsl = _nl_to_dsl(nl, strategy_id)  # 模板/表驱动 parser
        result.dsl = dsl
    except Exception as e:
        result.generation_errors.append(str(e))
        result.status = "failed"
        result.stage_reached = "generation"
        _log_audit(audit_logger, trace_id, "generation", ...)
        return result

    _log_audit(audit_logger, trace_id, "generation", ...)

    # Step 2: Validation
    validation = validate_dsl(dsl)
    result.validation = _to_api_response(validation, trace_id)
    result.red_line_result = {
        "passed": not validation.has_red_line_violation,
        "triggered_rules": [e.code for e in validation.errors if e.level == "red_line"],
    }
    _log_audit(audit_logger, trace_id, "validation", ..., result.red_line_result)

    if not validation.passed:
        result.status = "failed"
        result.stage_reached = "validation"
        _archive_problems(result, validation)
        return result

    # Step 3: Preview（仅通过校验时）
    preview_service = PreviewService(...)
    preview = preview_service.preview(dsl, data_source=preview_data_source, trace_id=trace_id)
    result.preview = preview
    _log_audit(audit_logger, trace_id, "preview", ...)

    # Step 4: Light Backtest（仅通过校验时）
    bt_result = run_dsl_backtest(dsl, start_date or "2023-01-01", end_date or "2024-12-31")
    result.backtest = BacktestResponse(
        trace_id=trace_id,
        status="partial" if bt_result.risk_flags else "success",
        metrics=BacktestMetrics(**bt_result.metrics),
        errors=bt_result.risk_flags,
    )
    result.backtest_mode = "light_stub"
    _log_audit(audit_logger, trace_id, "backtest", ...)
    storage.save_backtest_result(strategy_id, trace_id, result.backtest.status, bt_result.metrics, dsl.to_dict())

    # Step 5: 归档
    result.status = "success" if not result.backtest.errors else "partial"
    result.stage_reached = "complete"
    return result
```

---

## 7. Light Backtest 本周最小 Contract

### 7.1 前提

- 只有通过红线检查（`red_line_result.passed == true`）才允许执行。
- 当前 `backtest_adapter.py` 仍是 stub，本周不实现完整真实回测。

### 7.2 最小返回字段

```python
class LightBacktestResult(BaseModel):
    status: Literal["success", "partial", "failed"]
    mode: Literal["light_stub", "light_mock"]  # 必须标注，避免误认为真实绩效
    metrics: dict[str, float | int]  # 核心指标
    risk_flags: list[str]           # 必须包含 "STUB_BACKTEST" 标记
    trace_id: str
    strategy_id: str
```

### 7.3 核心指标字段（必须存在）

| 字段 | 类型 | stub 值 | 说明 |
|---|---|---|---|
| `total_return` | float | 0.0 | 总收益率 |
| `annual_return` | float | 0.0 | 年化收益率 |
| `max_drawdown` | float | 0.0 | 最大回撤 |
| `sharpe_ratio` | float | 0.0 | 夏普比率 |
| `win_rate` | float | 0.0 | 胜率 |
| `profit_factor` | float | 0.0 | 盈亏比 |
| `trade_count` | int | 0 | 交易次数 |

### 7.4 存储与审计

- 必须写入 `strategy_backtests` 表（通过 `StrategyLabStorage.save_backtest_result`）。
- 必须写入 `strategy_audit_log` 表（operation="backtest"）。
- `metrics` JSON 中必须包含 `"_mode": "light_stub"` 字段。

### 7.5 失败处理

- 若 DSL 未通过红线检查，返回 `status="failed"`，`stage_reached="validation"`，不写入 backtest 记录。
- 若 backtest 执行异常，返回 `status="failed"`，`stage_reached="backtest"`，写入 audit 和 storage（status="failed"）。

---

## 8. Audit 事件顺序 Contract

### 8.1 同一 trace_id 下的 operation 顺序

```
generation -> validation -> preview -> backtest
```

### 8.2 每个 operation 必须记录的字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `trace_id` | str | 全局追踪 ID |
| `operation` | str | generate / validation / preview / backtest |
| `strategy_id` | str | 策略标识 |
| `dsl_version` | str | 固定 "strategy_dsl_v2" |
| `input_hash` | str | 输入 payload SHA256 前 16 位 |
| `output_hash` | str | 输出 payload SHA256 前 16 位 |
| `red_line_result` | JSON | 红线结果（无则 {}） |
| `created_at` | timestamp | 自动写入 |

### 8.3 失败链路审计规则

| 失败点 | 写入的 operations | 不执行的 operations |
|---|---|---|
| DSL 生成失败 | generation | validation, preview, backtest |
| 红线检查失败 | generation, validation | preview, backtest |
| Preview 异常 | generation, validation, preview | backtest |
| Backtest 异常 | generation, validation, preview, backtest | 无 |

### 8.4 查询验证

Codex 验收时必须验证：

```sql
SELECT operation, red_line_result
FROM strategy_audit_log
WHERE trace_id = ?
ORDER BY created_at ASC;
```

对于通过样例，应返回 4 条记录，operation 依次为 generation, validation, preview, backtest。

---

## 9. 问题清单模板

### 9.1 四类固定分类

| category | 说明 |
|---|---|
| `definition` | 策略定义问题（NL 歧义、条件缺失、参数错误） |
| `implementation` | 实现问题（代码 bug、接口不匹配、性能问题） |
| `data` | 数据问题（数据源缺失、字段不存在、质量异常） |
| `acceptance` | 验收问题（结果不符合预期、指标不达标） |

### 9.2 问题数据结构

```python
class ProblemItem(BaseModel):
    """问题归档条目。"""

    model_config = {"extra": "forbid"}

    sample_id: str = Field(..., description="关联的样例 ID")
    category: Literal["definition", "implementation", "data", "acceptance"] = Field(...)
    stage: Literal["generation", "validation", "preview", "backtest", "e2e"] = Field(...)
    summary: str = Field(..., max_length=200, description="一句话摘要")
    evidence: dict[str, Any] = Field(default_factory=dict, description="证据（DSL 片段、错误码、截图等）")
    owner: Literal["qoder", "kimi", "codex", "user"] = Field(..., description="负责角色")
    next_action: str = Field(..., description="下一步行动")
    created_at: str = Field(default="", description="ISO 时间戳")
```

### 9.3 示例问题条目

```json
{
  "sample_id": "sample_ma_5_20_stop_8",
  "category": "definition",
  "stage": "validation",
  "summary": "price_cross_ma 用于 exit section 产生 semantic warning",
  "evidence": {
    "warning_code": "SEMANTIC_WRONG_SECTION",
    "dsl_path": "exit[0].condition_type",
    "note": "price_cross_ma category=ENTRY 但被用于 exit"
  },
  "owner": "codex",
  "next_action": "评估是否需要新增 price_below_ma EXIT 条件，或接受 warning",
  "created_at": "2026-06-08T12:00:00Z"
}
```

---

## 10. 验收标准

Codex 实现后必须通过以下验收：

1. 输入 `MA5上穿MA20买入，跌破MA10卖出，止损8%` 能生成合法 DSL（`sample_ma_5_20_stop_8`）。
2. 缺少止损的 DSL 或中文输入被红线拒绝，且 `red_line_result` 可审计。
3. 仓位超过 25% 的 DSL 被红线拒绝（`RL_MAX_POSITION`）。
4. 3 个样例都能生成 preview，mock 模式稳定返回命中数量。
5. 3 个样例都能返回 Light Backtest 最小指标，并明确标注 `mode="light_stub"`。
6. 每个样例的 generation、validation、preview、backtest 都能通过同一 `trace_id` 查到审计记录。
7. 失败样例（如缺少止损）不会执行 preview/backtest，但 audit 有 generation + validation 记录。

---

## 11. 不做什么

- 不新增真实 LLM 接入。
- 不执行 LLM 生成代码。
- 不扩因子库。
- 不新增外部数据源。
- 不实现完整真实 backtest engine。
- 不实现 Web 路由。
- 不做 Agent Debate DAG。
- 不做 Paper Trading。
- 不做 TS-FM / RAG-KG。
- 不改 benchmark。
- 不改 factors registry（本周样例均可用现有 condition type 表达）。

---

## 12. Codex 下一步行动

1. 实现 `e2e_runner.py` 中的 `run_mvp_e2e_sample()` 和 `MvpE2EResult`。
2. 实现 `_nl_to_dsl()` 表驱动 parser（基于第 5 节映射规则）。
3. 为 3 个样例编写端到端测试，验证完整链路。
4. 确保 `backtest_adapter.py` stub 返回的 `BacktestResult` 包含 `_mode: "light_stub"`。
5. 确保 `audit.py` 在失败链路中也能正确写入记录。
