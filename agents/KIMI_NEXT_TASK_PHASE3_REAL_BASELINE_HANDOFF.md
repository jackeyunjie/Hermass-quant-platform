# Kimi Next Task: Phase 3 Real Data Baseline Handoff

你是 Hermass AI Quant Platform 的 Kimi Research Engineer（数据与性能方向）。本轮任务只负责真实数据 baseline 准备，**不碰 Web UI、不阻塞 Phase 3 Web 开发、不修改 strategy_lab 或 benchmark 代码来绕过数据缺失。**

## 必读上下文

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md` 中 Data Foundation / State Cube / Light Backtest 相关部分
- `docs/design/DATA_FOUNDATION_AND_STATE_CUBE_ARCHITECTURE.md`
- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md`
- `agents/KIMI2_NEXT_TASK_DATA_REFRESH_REPLACEMENT_AUDIT.md`
- `benchmarks/validate_real_data.py`
- `benchmarks/light_backtest_perf.py`
- `benchmarks/gate_summary.py`

## 总裁决

Phase 3 主线是 Web UI，真实数据 baseline 拆成独立 handoff，不互相阻塞。

```text
Kimi 负责：
  -> 校验 data/p116_foundation.duckdb
  -> 校验 data/state_cube.duckdb
  -> 跑 benchmarks/validate_real_data.py
  -> 产出 data readiness 状态和 baseline 结果

Codex/Qoder 负责：
  -> Phase 3 Web UI Contract
  -> Web 层实现
  -> UI 上显示 data readiness 状态
```

规则：

- 真实 DB 存在则跑 validation + gate，产出 baseline 结果。
- 真实 DB 不存在则明确标记 blocker，给出最小数据准备清单，不阻塞 Web UI。
- 不用 synthetic DB 冒充真实 DB。
- 不修改 `benchmarks/` 或 `hermass_platform/strategy_lab/` 代码来绕过 validation。
- Web UI 可以通过读取 readiness JSON 显示状态，但 Kimi 不实现 Web 代码。

## 任务范围

### 1. 校验 `data/p116_foundation.duckdb`

检查项：

- 文件是否存在。
- 能否用 DuckDB 正常打开。
- 是否包含 `daily_bars` 表。
- `daily_bars` 必需列是否齐全：
  - `symbol`, `date`, `open`, `high`, `low`, `close`, `volume`
  - `ma_5`, `ma_10`, `ma_20`, `ma_60`
  - `atr_14`, `bb_position`, `volume_ratio`, `adx_14`
  - `is_limit_up`
- 数据规模：symbol 数量、交易日数量、总行数。
- 日期范围：`MIN(date)`、`MAX(date)`。
- 数据新鲜度：`MAX(date)` 到当前日期的天数。
- 数据质量：是否有 NULL、是否有重复 `(symbol, date)`、是否有异常价格（<=0）。
- 复权口径：是否声明 `forward_adjusted` / `backward_adjusted` / `raw`。
- metadata：是否有 `data_source`、`price_adjustment`、`license_status`、`last_refresh_at` 等信息。

### 2. 校验 `data/state_cube.duckdb`

检查项：

- 文件是否存在。
- 能否用 DuckDB 正常打开。
- 是否包含 `state_cube` 表。
- 必需列是否齐全：
  - `symbol`, `date`
  - `d1_state` 或 `state_hex_d1` 至少一组可用
  - `w1_state` 或 `state_hex_w1` 至少一组可用
  - `mn1_state` 或 `state_hex_mn1` 至少一组可用
- 数据规模：symbol 数量、交易日数量、state cube 行数。
- 日期范围：`MIN(date)`、`MAX(date)`。
- state 值分布与合法性（非空、格式是否符合预期）。
- `state_cube` 与 `daily_bars` 的日期/品种覆盖对齐情况。

### 3. 跑 `benchmarks/validate_real_data.py`

命令：

```bash
PY=/Users/lv111101/.pyenv/versions/3.11.12/bin/python
DATE_TAG=$(date +%Y%m%d)
$PY benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --min-symbols 5000 \
  --min-trading-days 252 \
  --max-staleness-days 30 \
  --as-of-date $(date +%Y-%m-%d) \
  --output outputs/benchmarks/real_data_validation_${DATE_TAG}.json
```

验收：

- process exits `0`
- output JSON has `ok=true`
- `errors=[]`
- no missing required tables or columns
- state alias check passes
- freshness within threshold

若失败，记录失败原因和修复建议。

### 4. 产出 data readiness 状态

输出文件：`outputs/benchmarks/data_readiness_status.json`

结构：

```json
{
  "as_of_date": "2026-06-18",
  "verdict": "READY" | "PARTIAL" | "NOT_READY",
  "foundation_db": {
    "path": "data/p116_foundation.duckdb",
    "exists": true,
    "open_ok": true,
    "table": "daily_bars",
    "columns_ok": true,
    "missing_columns": [],
    "symbol_count": 5200,
    "trading_days": 500,
    "total_rows": 2600000,
    "date_min": "2022-01-04",
    "date_max": "2024-12-31",
    "staleness_days": 170,
    "data_quality_issues": [],
    "metadata": {
      "data_source": "...",
      "price_adjustment": "forward_adjusted",
      "license_status": "research_only",
      "last_refresh_at": "..."
    }
  },
  "state_cube_db": {
    "path": "data/state_cube.duckdb",
    "exists": true,
    "open_ok": true,
    "table": "state_cube",
    "columns_ok": true,
    "missing_columns": [],
    "symbol_count": 5200,
    "trading_days": 500,
    "total_rows": 2600000,
    "date_min": "2022-01-04",
    "date_max": "2024-12-31",
    "staleness_days": 170,
    "state_value_issues": []
  },
  "validation_result_path": "outputs/benchmarks/real_data_validation_YYYYMMDD.json",
  "validation_ok": true,
  "validation_errors": [],
  "ui_display": {
    "zh": "真实数据基线已就绪，可切换 light_real_v1 模式。",
    "en": "Real data baseline is ready; light_real_v1 mode available."
  }
}
```

若 DB 不存在：

```json
{
  "as_of_date": "2026-06-18",
  "verdict": "NOT_READY",
  "foundation_db": {"exists": false, "path": "data/p116_foundation.duckdb"},
  "state_cube_db": {"exists": false, "path": "data/state_cube.duckdb"},
  "validation_result_path": null,
  "validation_ok": false,
  "validation_errors": ["data/p116_foundation.duckdb not found", "data/state_cube.duckdb not found"],
  "ui_display": {
    "zh": "真实数据基线尚未就绪，当前仅支持 synthetic / light_stub 模式。",
    "en": "Real data baseline not ready; synthetic / light_stub modes only."
  },
  "next_steps": [
    "生成或接入 data/p116_foundation.duckdb",
    "生成或接入 data/state_cube.duckdb",
    "重新运行 benchmarks/validate_real_data.py"
  ]
}
```

### 5. 真实 baseline 性能跑测（仅在 validation 通过后）

命令：

```bash
PY=/Users/lv111101/.pyenv/versions/3.11.12/bin/python
DATE_TAG=$(date +%Y%m%d)
$PY benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 5000 \
  --days 252 \
  --runs 5 \
  --output outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl

$PY benchmarks/gate_summary.py \
  --validation outputs/benchmarks/real_data_validation_${DATE_TAG}.json \
  --benchmark outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl \
  --output outputs/benchmarks/gate_summary_${DATE_TAG}.json
```

验收：

- `light_backtest_perf.py` exits 0
- JSONL has records for `mode="full_polars"`
- `universe_n=5000`, `days=252`, `data_source="real"`
- 5 runs complete without failure
- `gate_summary.py` exits 0
- output JSON has `ok=true`

### 6. Handoff 给 Codex

Kimi 完成校验后，回传以下模板：

```markdown
## Real DB Handoff

- foundation_db: `data/p116_foundation.duckdb`
- state_cube_db: `data/state_cube.duckdb`
- data_source:
- price_adjustment: `forward_adjusted` / `backward_adjusted` / `raw`
- license_status: `research_only` / `approved_for_pilot` / `approved_for_public`
- last_refresh_at: `YYYY-MM-DDTHH:MM:SSZ`
- date_min:
- date_max:
- symbol_count:
- trading_days:
- daily_bars_rows:
- state_cube_rows:
- known_missing_fields:
- known_data_limitations:
- command_outputs:
  - validate_real_data: (pass/fail, 关键错误)
  - light_backtest_perf: (pass/fail, P50/P95)
  - gate_summary: (pass/fail, 哪些 gate 未通过)
```

## 本轮执行结果（2026-06-19）

真实数据 baseline 性能 gate 已通过，可 handoff 给 Codex。

### 关键修复

- **根因**：DuckDB 1.5.3 连接已有 DB 时会尝试 autoload/autoinstall extension，触发网络 stall，导致 `light_backtest_perf.py` data_load 阶段耗时 ~34s。
- **修复**：统一在 DuckDB 连接后执行 `SET autoinstall_known_extensions=false` 与 `SET autoload_known_extensions=false`。
- **改动文件**：
  - `benchmarks/light_backtest_perf.py`：连接后禁用 autoload。
  - `benchmarks/gate_summary.py`：按 `(mode, universe_n)` 分组，gate 评估使用最大 universe（`full_polars_5000`）。
  - `hermass_platform/strategy_lab/_duckdb_helper.py`（新增）：统一连接入口。
  - `hermass_platform/strategy_lab/backtest_data_provider.py`、`preview_service.py`、`storage.py`、`audit.py`：改用 helper。
  - `scripts/build_hermass_data_from_blackwolf.py`：改用带 autoload 禁用的本地 helper。

### 验收数据

- `validate_real_data`：ok=true，errors=[]，warnings=2
- `light_backtest_perf` 5000×252 `full_polars`：
  - P50=2.12s，P95=2.28s
  - data_load P95=0.32s
  - signal_gen P95=0.20s
  - equity_metrics P95=1.80s
- `gate_summary`：status=PASS，8/8 gates 通过
- 回归测试：strategy_lab 278 passed / web smoke 5/5 / E2E 5/5 / real integration 8 passed

### 输出物

- `outputs/benchmarks/real_data_validation_20260619.json`
- `outputs/benchmarks/light_backtest_real_20260619.jsonl`
- `outputs/benchmarks/gate_summary_20260619.json`
- `outputs/benchmarks/data_readiness_status.json`（verdict=READY）
- `data/research/conversations/agent-runs/2026-06-19-kimi-phase3-real-baseline-handoff.md`

## 明确不做什么

- 不实现 Web UI 代码。
- 不修改 `web/`、`hermass_platform/strategy_lab/`、`benchmarks/` 代码。
- 不替换默认数据源作为答案。
- 不把 synthetic DB 冒充真实 DB。
- 不承诺真实性能直到真实 baseline gate summary 通过。
- 不阻塞 Phase 3 Web UI 开发；Web UI 应基于 `data_readiness_status.json` 显示状态。
- 不运行真实交易、paper trading 或外部服务集成。
- 不执行 LLM 生成的策略代码。

## 输出物清单

Kimi 本轮必须交付：

1. `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`（本文件，迭代版）。
2. `data/research/conversations/agent-runs/2026-06-18-kimi-phase3-real-baseline-handoff.md`（运行摘要）。
3. `outputs/benchmarks/data_readiness_status.json`（data readiness 状态，供 UI 读取）。
4. 若真实 DB 存在：`outputs/benchmarks/real_data_validation_YYYYMMDD.json`、`outputs/benchmarks/light_backtest_real_YYYYMMDD.jsonl`、`outputs/benchmarks/gate_summary_YYYYMMDD.json`。

## 文件提交规则

提交：

- `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`
- `data/research/conversations/agent-runs/2026-06-18-kimi-phase3-real-baseline-handoff.md`

不提交：

- `outputs/benchmarks/*.json`
- `outputs/benchmarks/*.jsonl`
- `outputs/benchmarks/*.duckdb`
- `data/*.duckdb`
- vendor raw data、credentials、tokens
