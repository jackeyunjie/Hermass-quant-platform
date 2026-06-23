# Kimi Next Task: Phase 2 Real DB Baseline Readiness And Runbook

你是 Hermass AI Quant Platform 的 Kimi Research Engineer（数据与性能方向）。本任务只确认 Phase 2 真实 DB baseline 是否具备运行条件，并给 Codex 一份可执行 runbook。不要实现代码，不要修改 benchmark、Strategy Lab 或数据构建脚本。

## Verdict

**BLOCKED_FOR_REAL_BASELINE: real DB absent locally; MVP stub/synthetic path remains unblocked.**

- 当前 workspace 没有可用于 Phase 2 real baseline 的真实 DuckDB。
- 不把 synthetic smoke 结果解释为真实数据性能。
- 不阻塞 Phase 0/1 MVP stub 链路，也不阻塞 Phase 2 synthetic integration 的工程验收。
- Phase 2 real backtest 发布、真实指标邀请制试点升级、GitHub 真实指标 demo 和 public beta 仍必须等待真实 DB validation + hot path gates。

## Local Real DB Check

检查日期：2026-06-11。

必需路径：

| 路径 | 结论 |
|------|------|
| `data/p116_foundation.duckdb` | 不存在 |
| `data/state_cube.duckdb` | 不存在 |

当前 `data/` 状态：

- `data/` 下只有 `data/research/conversations/PROJECT_INDEX.md` 和 Obsidian vault 目录。
- 未发现 `data/*.duckdb`、`data/*.db`、`data/*.parquet`、`data/*.csv`、`data/metadata.json`。
- 未发现 `data/market_assets.duckdb`、`stock_info`、`trading_calendar`、`adjust_factors` 或 `data_license` 元数据文件。

可能的替代路径/命名：

| 候选 | 结论 |
|------|------|
| `outputs/benchmarks/_synthetic_tmp.duckdb` | synthetic 临时库，只能用于 smoke，不能作为真实 baseline |
| `outputs/strategy_lab/mvp_e2e_acceptance_storage.duckdb` | MVP acceptance storage，不是行情 foundation DB |
| `outputs/strategy_lab/mvp_e2e_acceptance_audit.duckdb` | MVP audit DB，不是行情或 State Cube |
| 其他 `p116` / `foundation` / `state_cube` 命名文件 | 未发现可用候选 |

## If DB Is Missing: Codex Minimal Data Preparation Task

Codex 下一步只需准备最小真实 baseline 数据，不要扩展引擎功能：

1. 生成或接入本地真实数据 DuckDB：
   - `data/p116_foundation.duckdb`
   - `data/state_cube.duckdb`
2. `p116_foundation.duckdb` 至少包含 `daily_bars` 表，并满足 `benchmarks/validate_real_data.py` 的必需列：
   - `symbol`, `date`, `open`, `high`, `low`, `close`, `volume`
   - `ma_5`, `ma_10`, `ma_20`, `ma_60`
   - `atr_14`, `bb_position`, `volume_ratio`, `adx_14`
   - `is_limit_up`
3. `state_cube.duckdb` 至少包含 `state_cube` 表，并满足：
   - `symbol`, `date`
   - `d1_state` / `state_hex_d1` 至少一组可用
   - `w1_state` / `state_hex_w1` 至少一组可用
   - `mn1_state` / `state_hex_mn1` 至少一组可用
4. 补充最小 metadata：
   - `price_adjustment`
   - `data_source`
   - `license_status`
   - `last_refresh_at`
   - 可放在 DB 内 `data_license` 表，或放在 DB 同目录 `metadata.json`。
5. 最小样本目标：
   - real baseline minimum：`>=5000` symbols，`>=252` trading days。
   - 若暂时达不到，仍可跑 validation，但结果只能作为数据准备诊断，不能作为 Phase 2 release gate。

Codex 数据准备禁止事项：

- 不替换数据源作为默认答案；先补齐当前 foundation/state cube baseline。
- 不把 vendor raw data、credentials、token、DuckDB 文件提交到 Git。
- 不删除或覆盖其他 agent 生成的输出。
- 不修改 benchmark 或 Strategy Lab 代码来绕过 validation。
- 不用 synthetic DB 冒充真实 DB。
- 不承诺真实性能，直到真实 baseline gate summary 通过。

### Missing DB Handoff Template

Codex 完成数据准备后，请回传：

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
  - validate_real_data:
  - light_backtest_perf:
  - gate_summary:
```

## If DB Exists: Direct Run Commands

Use the project Python currently documented in benchmark runbooks:

```bash
PY=/Users/lv111101/.pyenv/versions/3.11.12/bin/python
DATE_TAG=$(date +%Y%m%d)
```

1. Validate real data:

```bash
$PY benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --min-symbols 5000 \
  --min-trading-days 252 \
  --max-staleness-days 30 \
  --as-of-date $(date +%Y-%m-%d) \
  --output outputs/benchmarks/real_data_validation_${DATE_TAG}.json
```

Acceptance:

- process exits `0`
- validation JSON has `ok=true`
- `errors=[]`
- no missing required tables or required columns
- state alias check passes
- freshness is within threshold

2. Run Light Backtest performance baseline:

```bash
$PY benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 5000 \
  --days 252 \
  --runs 5 \
  --output outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl
```

Acceptance:

- process exits `0`
- JSONL has records for `mode="full_polars"`
- `universe_n=5000`
- `days=252`
- `data_source="real"`
- 5 runs complete without failure

3. Summarize gates:

```bash
$PY benchmarks/gate_summary.py \
  --validation outputs/benchmarks/real_data_validation_${DATE_TAG}.json \
  --benchmark outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl \
  --output outputs/benchmarks/gate_summary_${DATE_TAG}.json
```

Acceptance:

- process exits `0`
- output JSON has `ok=true`
- all gate results pass

## Gate Thresholds

### Synthetic Smoke

Purpose: prove benchmark scripts and output format work.

Threshold:

- benchmark scripts exit `0`
- JSONL/JSON output exists and is parseable
- `data_source="synthetic"`
- performance numbers are informational only

Failure blocks benchmark script changes only. It does not say anything about real DB readiness or real performance.

### Real Baseline

Purpose: prove Phase 2 local real-data hot path is viable.

Scope:

- `>=5000` symbols
- `>=252` trading days
- local SSD real DuckDB
- validation must run before performance baseline

Threshold:

| Gate | Threshold |
|------|-----------|
| Data validation | `ok=true`, `errors=[]` |
| Light Backtest total P50 | `<20s` |
| Light Backtest total P95 | `<30s` |
| Data load P95 | `<10s` |
| Signal generation P95 | `<12s` |
| Equity + metrics P95 | `<8s` |
| Peak memory | `<4096MB` |
| Failure count | `0` |

Failure blocks Phase 2 real backtest release, real-metric pilot upgrade, GitHub real metrics demo, and public beta.

### Pilot / Public Beta

Purpose: prevent misleading external use.

Additional requirements beyond real baseline:

- pilot: freshness <= 30 calendar days
- public beta: freshness <= 7 calendar days
- `license_status` explicitly allows the target use
- survivorship bias controls exist via `list_date` / `delist_date`
- adjustment policy is declared and traceable
- suspended, delisted, limit-up, and limit-down trading constraints are represented
- no future leakage in indicators, industry classification, universe membership, or State Cube joins

Public beta should require at least `>=5000` symbols x `>=3 years` once data is available.

## Data Risk Checklist

| Risk | Required handling |
|------|-------------------|
| freshness | record `date_max`, `last_refresh_at`, `as_of_date`, and staleness days |
| 复权 | declare `price_adjustment`; do not mix raw and adjusted prices |
| 幸存者偏差 | use `list_date` / `delist_date` or date-aware universe membership |
| 未来函数 | indicators and State Cube fields must use only current/prior data |
| 停牌退市 | preserve `is_suspended` and delist handling; do not fill halted days as tradable bars |
| 涨跌停 | include `is_limit_up`, `is_limit_down`, and ideally limit prices |
| license | record `data_source`, `license_status`, permitted use, and refresh owner |

## Files To Commit / Not Commit

Commit this Kimi handoff pair:

- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-db-baseline-run.md`

Do not commit:

- `outputs/benchmarks/*.json`
- `outputs/benchmarks/*.jsonl`
- `outputs/benchmarks/*.duckdb`
- `data/*.duckdb`
- vendor raw data
- credentials, tokens, cookies, local cache files

If Codex later creates code or documentation changes, submit those separately and only after review. This Kimi task itself is research/runbook only.

## Explicit Non-Goals

- Do not implement code.
- Do not edit `benchmarks/` or `hermass_platform/strategy_lab/`.
- Do not replace the data source.
- Do not promise real performance from synthetic results.
- Do not block MVP stub/mock acceptance.
- Do not run real trading, paper trading, or external service integration.
- Do not execute LLM-generated strategy code.
