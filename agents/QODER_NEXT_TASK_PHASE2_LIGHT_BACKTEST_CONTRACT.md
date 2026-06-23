# Qoder Next Task: Phase 2 Real Light Backtest Contract

你是 Hermass AI Quant Platform 的 Qoder Architect。本轮任务是把 Phase 2 Real Light Backtest 从 `light_stub` 推进到可实现、可审阅、可验收的工程契约。

## 必读上下文

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md` 中 Strategy Lab / Light Backtest / API 相关部分
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `data/research/conversations/decisions/0011-trade-evidence-database.md`
- `benchmarks/validate_real_data.py`
- `benchmarks/light_backtest_perf.py`
- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/dsl_schema.py`
- `hermass_platform/strategy_lab/dsl_validator.py`
- `hermass_platform/strategy_lab/condition_registry.py`
- `hermass_platform/strategy_lab/condition_translator.py`
- `hermass_platform/strategy_lab/preview_service.py`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/audit.py`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `hermass_platform/strategy_lab/tests/`

## 背景

Phase 0/1 MVP acceptance 已通过：

- 中文策略输入可以生成合法 DSL。
- 缺少止损、仓位超过 25% 会被红线拒绝。
- Preview 可以返回命中数量。
- Light Backtest 当前能写 storage 和 audit，但 `BacktestAdapter` 仍是 `light_stub`。

下一步不是 Agent Debate、Paper Trading 或完整平台化，而是把回测从 stub 升级为真实、确定性、可审计的 Light Backtest v1。

## 总裁决

Phase 2 默认采用：

```text
DSL v2
  -> Pydantic/schema validate
  -> red-line check
  -> DuckDB load narrowed market/state data
  -> Polars compute signals, positions, exits, equity curve, metrics
  -> StrategyLabStorage write backtest summary + trades + trade event evidence
  -> StrategyAuditLogger write backtest audit
```

规则：

- DSL 是唯一策略表达，禁止生成或执行 LLM/Python 策略代码。
- Backtest 必须先过 `validate_dsl()` 和 red-line 检查。
- `light_stub` 不得伪装成真实绩效。
- Phase 2 只做 long-only daily-bar Light Backtest。

## 文件路径与模块边界

### 必须改造

#### `hermass_platform/strategy_lab/backtest_adapter.py`

继续作为 Strategy Lab 的服务入口和向后兼容 facade，但不要把 provider/engine 全塞在这个文件里。

保留：

```python
def run_dsl_backtest(
    dsl: StrategyDSL,
    start_date: str,
    end_date: str,
    foundation_db: Path | None = None,
    initial_capital: float = 1_000_000.0,
    cost_model: str = "a_share_default",
    mode: str = "light",
) -> BacktestResult:
    ...
```

更新：

- `BacktestAdapter.run_backtest()` 从 stub 改为调用 `LightBacktestEngine`。
- `BacktestConfig` 增加 `state_cube_db: Path | None = None`、`universe: list[str] | None = None`、`trace_id: str | None = None`。
- `BacktestResult` 增加 `mode: str`、`status: str`、`data_version: str | None`、`warnings: list[str]`、`trades_path: str` 可选字段。

#### 新增 `hermass_platform/strategy_lab/backtest_models.py`

放 Light Backtest 专用 Pydantic/dataclass contract，避免 `api_models.py` 与 engine 内部结构互相污染。

#### 新增 `hermass_platform/strategy_lab/backtest_data_provider.py`

DuckDB 取数边界。只负责读取和字段归一，不负责交易逻辑。

#### 新增 `hermass_platform/strategy_lab/light_backtest_engine.py`

Polars 热路径。负责信号、持仓、交易、权益曲线、指标。

#### 新增或扩展 `hermass_platform/strategy_lab/backtest_metrics.py`

封装指标计算，便于单测。

#### 可选新增 `hermass_platform/strategy_lab/backtest_evidence.py`

把 trade/event evidence 构造从 engine 主流程抽出来。若实现很小，也可先放 `light_backtest_engine.py`，但接口必须清晰。

### 可扩展但不阻塞

#### `hermass_platform/strategy_lab/api_models.py`

Backtest API 结构要能表达 real light 输出，但保持已有字段兼容。

#### `hermass_platform/strategy_lab/storage.py`

现有 `strategy_backtests.metrics JSON` 足够承载 v1 指标；已有 `strategy_trades` 和 `strategy_trade_events` 必须复用。除非测试证明必要，不做破坏性 DDL 迁移。

建议只新增非破坏性读取方法：

```python
def list_backtests(self, *, strategy_id: str | None = None) -> list[BacktestResult]:
    ...
```

## 接口签名

### Backtest data provider

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import polars as pl

@dataclass(frozen=True)
class MarketDataRequest:
    start_date: str
    end_date: str
    required_columns: list[str]
    universe: list[str] | None = None
    include_state: bool = True

@dataclass(frozen=True)
class MarketDataBundle:
    bars: pl.DataFrame
    data_version: str
    warnings: list[str]
    source_summary: dict[str, Any]

class DuckDBBacktestDataProvider:
    def __init__(
        self,
        foundation_db: Path,
        state_cube_db: Path | None = None,
    ) -> None:
        ...

    def load(self, request: MarketDataRequest) -> MarketDataBundle:
        ...
```

Data provider 输出列的最小标准：

- `symbol`
- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`
- DSL 依赖的 `ma_*`
- `volume_ratio` 或 `volume_ma_{lookback}`
- `is_limit_up`
- 可得时：`is_limit_down`、`is_suspended`
- 可得时：`d1_state`、`w1_state`、`mn1_state`

若源表列名为 `state_hex_d1` 等，provider 负责归一到 evidence 需要的 state key。

### Light backtest engine

```python
from dataclasses import dataclass, field
from typing import Any, Literal
import polars as pl

@dataclass(frozen=True)
class SignalFrame:
    frame: pl.DataFrame
    required_columns: list[str]
    warnings: list[str] = field(default_factory=list)

class LightBacktestEngine:
    def __init__(
        self,
        registry: ConditionRegistry | None = None,
        cost_model: CostModel | None = None,
    ) -> None:
        ...

    def build_signal_frame(
        self,
        dsl: StrategyDSL,
        data: MarketDataBundle,
    ) -> SignalFrame:
        ...

    def run(
        self,
        dsl: StrategyDSL,
        config: BacktestConfig,
        data: MarketDataBundle,
    ) -> BacktestResult:
        ...
```

`SignalFrame.frame` 最小列：

- `symbol`
- `date`
- `open`
- `high`
- `low`
- `close`
- `entry_signal`
- `filter_pass`
- `raw_exit_signal`
- `stop_loss_signal`
- `take_profit_signal`
- `exit_signal`
- `exit_reason`
- `position`
- `entry_price`
- `shares`
- `trade_id`
- `daily_return`
- `portfolio_value`

### Metrics

```python
def compute_light_metrics(
    daily_curve: pl.DataFrame,
    trades: pl.DataFrame,
    initial_capital: float,
) -> dict[str, float | int | None]:
    ...
```

必须返回：

- `total_return`
- `annual_return`
- `max_drawdown`
- `sharpe_ratio`
- `win_rate`
- `profit_factor`
- `trade_count`
- `total_trades`
- `avg_holding_days`
- `turnover`
- `cost_total`

### Evidence

```python
def build_trade_records(
    signal_frame: pl.DataFrame,
    dsl: StrategyDSL,
    trace_id: str,
) -> list[dict[str, Any]]:
    ...

def build_trade_event_evidence(
    signal_frame: pl.DataFrame,
    dsl: StrategyDSL,
    trace_id: str,
) -> list[dict[str, Any]]:
    ...
```

## API/Pydantic 数据结构建议

### Strategy Lab API service boundary

Web/FastAPI 层只做 request/response 转换和 service 调用，不放 provider、engine、storage 业务逻辑。

建议新增或收敛到 service 函数：

```python
def run_light_backtest_service(
    request: BacktestRequest,
    *,
    storage: StrategyLabStorage,
    audit_logger: StrategyAuditLogger,
    foundation_db: Path,
    state_cube_db: Path | None = None,
) -> BacktestResponse:
    ...

def get_backtest_service(
    trace_id: str,
    *,
    storage: StrategyLabStorage,
) -> GetBacktestResponse:
    ...
```

Endpoint 映射：

- `POST /api/strategy-lab/backtest` -> `run_light_backtest_service()`
- `GET /api/strategy-lab/backtest/{id}` -> `get_backtest_service()`

`id` 在 Phase 2 MVP 中继续使用 `trace_id`；若后续引入独立 `backtest_id`，必须保持 `trace_id` 查询兼容。

### `BacktestRequest`

当前模型只含 DSL、日期和 trace。Phase 2 建议扩展为：

```python
class BacktestRequest(BaseModel):
    dsl: StrategyDSL
    start_date: str
    end_date: str
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: Literal["light"] = "light"
    initial_capital: float = Field(default=1_000_000.0, gt=0)
    foundation_db: str | None = None
    state_cube_db: str | None = None
    universe: list[str] | None = None
```

Web 层可不暴露 DB path；service 层可从配置注入。

### `BacktestMetrics`

保持现有字段，新增可选字段：

```python
avg_holding_days: float | None = None
turnover: float | None = None
cost_total: float | None = None
```

### `BacktestResponse`

建议扩展：

```python
class BacktestResponse(BaseModel):
    trace_id: str
    dsl_version: str = "strategy_dsl_v2"
    status: Literal["success", "partial", "failed"] = "failed"
    mode: Literal["light_real_v1", "light_stub"] = "light_real_v1"
    metrics: BacktestMetrics = Field(default_factory=BacktestMetrics)
    risk_flags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    trade_count: int | None = None
    daily_curve: list[dict[str, Any]] = Field(default_factory=list)
    trades: list[dict[str, Any]] = Field(default_factory=list)
    state_breakdown: dict[str, Any] = Field(default_factory=dict)
    data_version: str | None = None
    elapsed_seconds: float | None = None
    errors: list[str] = Field(default_factory=list)
    input_hash: str = ""
    output_hash: str = ""
```

为避免 API 响应过大，Web API 可限制 `daily_curve` 和 `trades` 返回摘要；完整记录以 storage 为准。

## DSL 条件到交易信号的最小语义

所有 condition 先由 registry 校验参数。engine 不接受未注册 condition。

### `ma_golden_cross`

参数：

- `fast_period`
- `slow_period`

语义：

```text
ma_fast[t] > ma_slow[t] AND ma_fast[t-1] <= ma_slow[t-1]
```

按 `symbol` 分组、按 `date` 排序计算。首日无前值为 false。

用途：

- entry section 中产生 `entry_signal`。

### `price_cross_ma`

参数：

- `timeframe`
- `ma_period`
- `direction`

Phase 2 Light 只支持 `timeframe == "D1"`。其他 timeframe 返回 validation/backtest failed，错误码建议 `BT_UNSUPPORTED_TIMEFRAME`。

语义：

```text
direction == "above":
  close[t] > ma[t] AND close[t-1] <= ma[t-1]

direction == "below":
  close[t] < ma[t] AND close[t-1] >= ma[t-1]
```

用途：

- entry 中可作为 entry signal。
- exit 中可作为 `raw_exit_signal`，`exit_reason="price_cross_ma"`.

### `stop_loss_pct`

参数：

- `value`

语义：

```text
position_open AND close[t] <= entry_price * (1 - value)
```

MVP 用日线 close 触发，不做 intraday high/low 路径推断。若后续要用 low 触发，必须单独改 contract。

用途：

- exit only。
- 触发时 `exit_reason="stop_loss_pct"`。
- 必须写 `strategy_trade_events.event_type="stop_loss"`。

### `take_profit_pct`

参数：

- `value`

语义：

```text
position_open AND close[t] >= entry_price * (1 + value)
```

MVP 用日线 close 触发。

用途：

- exit only。
- 触发时 `exit_reason="take_profit_pct"`。
- 必须写 `strategy_trade_events.event_type="take_profit"`。

### `state_hex_in`

参数：

- `timeframe`: `MN1` / `W1` / `D1`
- `values`

语义：

```text
state_for_timeframe[t] IN values
```

Provider 映射优先级：

- `D1`: `d1_state` 或 `state_hex_d1`
- `W1`: `w1_state` 或 `state_hex_w1`
- `MN1`: `mn1_state` 或 `state_hex_mn1`

用途：

- entry/filter section 中参与布尔组合。

### `volume_ratio`

参数：

- `lookback`
- `operator`
- `value`

语义：

优先使用预计算列：

```text
volume_ratio <operator> value
```

若没有 `volume_ratio` 但有 `volume_ma_{lookback}`：

```text
volume / NULLIF(volume_ma_{lookback}, 0) <operator> value
```

Phase 2 不运行时补算任意 lookback 的 volume MA；缺列直接 failed，错误码建议 `BT_MISSING_REQUIRED_COLUMN`。

### `limit_up_filter`

参数：

- `allow`

语义：

```text
allow == false: is_limit_up == false
allow == true: is_limit_up == true
```

默认 DSL 里 `allow=false` 表示排除涨停买入。

用途：

- 只作为 pre-entry filter，不强制平仓。
- 若 `is_limit_up` 缺列，backtest failed，不 silent ignore。

## 组合语义

同一 section 按 `ConditionBlock.logic` 顺序组合：

- 第一条作为初始表达式。
- 第 N 条用自己的 `logic` 与前面累计结果组合。
- `and` -> `&`
- `or` -> `|`

MVP 不使用 `weight` 做打分；只保留在 triggered evidence 中。

Entry 执行条件：

```text
not currently holding symbol
AND entry section evaluates true
AND filters section evaluates true
AND tradability allows buy
```

Exit 执行条件：

```text
currently holding symbol
AND any exit source triggers
AND tradability allows sell
```

## DuckDB/Polars 分工

DuckDB：

- 打开 `p116_foundation.duckdb` / `state_cube.duckdb`。
- 按日期、universe、required_columns 做列裁剪。
- join state data 到 daily bars。
- 不拼接用户输入表名或列名；表/列来自 registry/provider 白名单。
- 不执行策略逻辑。

Polars：

- 排序、shift/window 计算。
- condition signal 计算。
- filter/entry/exit 合成。
- position、entry_price、shares、trade_id 生成。
- cost、daily_return、portfolio equity curve。
- metrics 和 evidence frame。

## 交易处理规则

### 交易方向

- MVP 只做 long-only。
- 不做 short、融资融券、T+0。

### 成本模型

沿用 `CostModel`：

- buy commission: `max(notional * 0.0003, 5.0)`
- sell commission: `max(notional * 0.0003, 5.0)`
- sell stamp duty: `notional * 0.0005`
- slippage both sides: `notional * 0.001`

成交价：

- MVP 用当日 close。
- 买入成交价可记为 `close * (1 + slippage_rate)`。
- 卖出成交价可记为 `close * (1 - slippage_rate)`。
- 费用仍要拆出 commission/stamp/slippage/cost_total。

### 仓位

每个 symbol 同时最多一笔仓位。

入场金额：

```text
target_notional = portfolio_value_previous_day * risk.max_position_pct
shares = floor(target_notional / buy_fill_price / 100) * 100
```

A 股最小 100 股。`shares <= 0` 时跳过入场并记录 warning。

MVP 默认允许多 symbol 同时持仓，但总持仓用可用资金约束：

- 如果当日多个 symbol 触发入场，按 `symbol` 升序处理。
- 资金不足则跳过后续入场，记录 `BT_INSUFFICIENT_CASH_SKIP` warning。

### 止损/止盈

同日多个 exit 同时触发时优先级：

1. `stop_loss_pct`
2. `take_profit_pct`
3. `price_cross_ma`
4. `ma_death_cross`

优先级只影响 `exit_reason` 和 evidence event type；exit price 仍为当日 close。

### 同日 entry/exit 冲突

同一 symbol 同一日：

- 已持仓时，先处理 exit，再考虑新的 entry。
- 刚 exit 的同一日不允许再次 entry，避免日线同价回转。
- 未持仓且 entry 与 exit 条件同时为 true，只允许 entry；exit 条件无 position context，不生效。

### 停牌/涨跌停过滤

停牌：

- 若存在 `is_suspended` 且为 true，则当日不允许买入或卖出。
- 若持仓遇停牌，position 延续，daily_return 用 close-to-close；若 close 缺失则 forward-fill 前收，记录 warning。

涨停：

- `limit_up_filter allow=false` 时不允许买入涨停股。
- 卖出不受涨停限制。

跌停：

- 若存在 `is_limit_down` 且为 true，则不允许卖出。
- 若触发 stop/take/exit 但跌停无法卖出，记录 `blocked_exit_reason`，仓位延续，event 可写 `hold`，不写 closed trade。
- 若缺少 `is_limit_down` 列，MVP 假设可卖，并记录 data warning。

缺列：

- 必需列缺失 -> backtest failed。
- 可选风控列缺失 -> warnings，但必须在 metrics JSON 中写 `data_quality_warnings`。

## 审计 operation 顺序

正常链路：

1. `generation`
2. `validation`
3. `preview`
4. `backtest`

Backtest service/API 被直接调用时，若没有 generation/preview：

1. `validation`
2. `backtest`

Backtest 内部必须重新执行：

```python
validation = validate_dsl(dsl)
if not validation.passed:
    fail before provider/engine
```

Backtest audit payload：

```json
{
  "mode": "light_real_v1",
  "status": "success",
  "metrics": {...},
  "trade_count": 12,
  "data_version": "...",
  "elapsed_seconds": 1.23,
  "risk_flags": [],
  "warnings": []
}
```

`red_line_result` 必须包含：

```json
{
  "passed": true,
  "triggered_rules": [],
  "details": []
}
```

红线失败时：

- 不读 DuckDB。
- 不运行 engine。
- 写 `validation` audit。
- 若入口语义要求创建 backtest response，可写 `backtest` audit/status failed，但不得写 trades。

## Storage 写入要求

### `strategy_backtests`

每次真实 light backtest 完成或失败都写一条记录：

```json
{
  "_mode": "light_real_v1",
  "status": "success|partial|failed",
  "total_return": 0.12,
  "annual_return": 0.08,
  "max_drawdown": -0.15,
  "sharpe_ratio": 0.9,
  "win_rate": 0.48,
  "profit_factor": 1.2,
  "trade_count": 34,
  "total_trades": 34,
  "avg_holding_days": 7.2,
  "turnover": 3.1,
  "cost_total": 1234.56,
  "data_version": "...",
  "elapsed_seconds": 2.4,
  "risk_flags": [],
  "warnings": [],
  "data_quality_warnings": []
}
```

`dsl_snapshot` 必须保存本次 DSL 完整 JSON。

### `strategy_trades`

每笔 closed/open trade 写入或更新一行：

- `trade_id`: `"{trace_id}:{symbol}:{entry_date}:{seq}"`
- `side`: `"long"`
- `status`: `"closed"` 或 `"open"`
- `pnl` / `pnl_pct`: closed trade 必填；open trade 可为空。

### `strategy_trade_events`

必须至少写：

- 每笔 entry 一个 `event_type="entry"`。
- 每笔正常 exit 一个 `event_type="exit"`。
- stop loss exit 写 `event_type="stop_loss"`。
- take profit exit 写 `event_type="take_profit"`。
- 跌停阻塞 exit 可写 `event_type="hold"`，notes 说明 blocked exit。

`triggered_conditions` 元素格式：

```json
{
  "section": "exit",
  "condition_type": "stop_loss_pct",
  "params": {"value": 0.08},
  "logic": "or",
  "weight": 1.0,
  "signal_value": true
}
```

`timeframe_states`：

```json
{
  "MN1": "0x11",
  "W1": "0x21",
  "D1": "0x23"
}
```

`indicator_snapshot` 最小字段：

```json
{
  "D1": {
    "close": 10.8,
    "ma_5": 10.6,
    "ma_10": 10.9,
    "ma_20": 10.1,
    "volume": 12345678,
    "volume_ratio": 1.7,
    "atr_14": 0.42,
    "is_limit_up": false,
    "is_limit_down": false,
    "is_suspended": false
  }
}
```

## 验收标准

1. `BacktestAdapter.run_backtest()` 不再默认返回 `STUB_BACKTEST`。
2. `MA5上穿MA20买入，跌破MA10卖出，止损8%` 在 synthetic DuckDB fixture 下产生非 stub 的 `light_real_v1` 结果。
3. 缺少止损的 DSL 被拒绝，且不读 DuckDB、不写 trade records。
4. `max_position_pct > 0.25` 被拒绝，且不读 DuckDB、不写 trade records。
5. `ma_golden_cross` 能产生 entry trades。
6. `price_cross_ma direction=below` 能产生 exit trades。
7. `stop_loss_pct` 触发时 event type 为 `stop_loss`。
8. `take_profit_pct` 触发时 event type 为 `take_profit`。
9. `state_hex_in` 和 `volume_ratio` 能参与 entry/filter 布尔组合。
10. `limit_up_filter allow=false` 会阻止涨停入场。
11. 同一 symbol 同一天 exit 后不会再 entry。
12. strategy_backtests 写入 `_mode="light_real_v1"`。
13. strategy_trades 与 strategy_trade_events 可按 `trace_id` 查询。
14. audit 中 backtest operation 的 `red_line_result.passed` 为 true。
15. 现有 Phase 0/1 测试继续通过。

## 测试清单

### Unit tests

新增：

- `hermass_platform/strategy_lab/tests/test_backtest_data_provider.py`
- `hermass_platform/strategy_lab/tests/test_light_backtest_engine.py`
- `hermass_platform/strategy_lab/tests/test_backtest_metrics.py`
- `hermass_platform/strategy_lab/tests/test_backtest_evidence.py`

覆盖：

- required column extraction。
- missing column failure。
- MA golden cross signal。
- price cross MA exit。
- stop loss / take profit priority。
- limit up entry filter。
- suspended day no trade。
- same-day conflict rule。
- cost model calculation。
- 100 股 lot rounding。

### Integration tests

新增：

- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`

用小型 synthetic DuckDB fixture，必须包含：

- `daily_bars`
- `state_cube`
- 至少 2 个 symbol、20 个交易日。
- 一只触发金叉入场和跌破 MA 出场。
- 一只触发止损或止盈。
- 一只当日涨停被 filter 排除。

断言：

- `BacktestResult.mode == "light_real_v1"`。
- `risk_flags` 不含 `STUB_BACKTEST`。
- metrics 字段非空。
- trades/event evidence 写入并可读。
- audit operation 顺序满足 contract。

### E2E tests

更新 `test_e2e_runner.py` 或新增 parallel test：

- 保留 stub 兼容测试时，显式指定 stub mode。
- real light test 显式提供 fixture DB path。
- real mode 下 `result.backtest_mode == "light_real_v1"`。

### Benchmark smoke

先跑 synthetic：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --symbols 500 --days 252 --runs 2 --output outputs/benchmarks/light_backtest_phase2_smoke.jsonl
```

真实数据就绪后先跑：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py --foundation-db data/p116_foundation.duckdb --state-cube-db data/state_cube.duckdb --output outputs/benchmarks/validation.json
```

## 明确不做什么

- 不做 Agent Debate。
- 不做 Paper Trading。
- 不做真实下单或券商接口。
- 不做 LLM 生成/执行 Python 策略代码。
- 不做 full backtest、walk-forward、HTML tearsheet。
- 不做分钟线、盘中 high/low 止损路径推断。
- 不做 short、多账户、融资融券、T+0。
- 不做任意动态指标补算；缺少 MVP 必需预计算列就 fail。
- 不做大规模 schema 迁移；优先复用现有 JSON metrics 和 trade evidence 表。
- 不把 synthetic benchmark 当真实性能承诺。

## 推荐实现顺序

1. 新增 `backtest_models.py`，扩展 API model 可选字段。
2. 新增 synthetic integration fixture。
3. 实现 provider required column extraction 和 DuckDB load。
4. 实现 Polars signal frame。
5. 实现 position/trade/equity/metrics。
6. 接入 storage trades/events。
7. 接入 audit 和 E2E runner real mode。
8. 跑全量 Strategy Lab tests。
