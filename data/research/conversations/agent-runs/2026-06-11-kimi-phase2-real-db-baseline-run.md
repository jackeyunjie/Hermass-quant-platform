# Kimi Run Note: Phase 2 Real DB Baseline Readiness And Runbook

## Background

Codex asked Kimi to follow up on Phase 2 real-data/performance gates with a narrower baseline-readiness runbook. The Phase 2 Real Light Backtest implementation and synthetic tests exist, but real baseline had not run because the required local DuckDB files were missing.

This run intentionally avoided code changes. It only inspected repository state and produced the next Kimi handoff.

## Decision

**Real DB baseline is not ready on 2026-06-11.**

The MVP stub/synthetic path remains valid. Real-data release gates remain blocked until the workspace has valid real DB files and passes validation plus hot-path performance gates.

## Read-Only Local Checks

Required DBs:

| File | Exists | Conclusion |
|------|--------|------------|
| `data/p116_foundation.duckdb` | no | blocks real baseline |
| `data/state_cube.duckdb` | no | blocks real baseline |

Current local data state:

- `data/` contains only the research vault directory.
- No `data/*.duckdb`, `data/*.db`, `data/*.parquet`, `data/*.csv`, or `data/metadata.json` files were present.
- No valid alternative `p116`, `foundation`, `state_cube`, or `market_assets` DB was found under `data/`.

Observed non-real alternatives:

| File | Why it is not usable for real baseline |
|------|----------------------------------------|
| `outputs/benchmarks/_synthetic_tmp.duckdb` | synthetic benchmark fixture only |
| `outputs/strategy_lab/mvp_e2e_acceptance_storage.duckdb` | MVP acceptance storage DB, not market data |
| `outputs/strategy_lab/mvp_e2e_acceptance_audit.duckdb` | audit DB, not market data |

Current `outputs/benchmarks/` contains synthetic/smoke artifacts only, including synthetic JSONL, synthetic validation JSON, missing-DB validation JSON, gate summary synthetic test JSON, and `_synthetic_tmp.duckdb`. These are useful evidence that benchmark scripts run, but they are not real-data evidence and must not be submitted.

## Runbook If DB Is Missing

Codex should prepare the minimum real-data handoff before asking Kimi to evaluate performance again:

1. Place real local DuckDB files at:
   - `data/p116_foundation.duckdb`
   - `data/state_cube.duckdb`
2. Ensure `daily_bars` and `state_cube` satisfy `benchmarks/validate_real_data.py`.
3. Add `data_license` table or `metadata.json` with:
   - `price_adjustment`
   - `data_source`
   - `license_status`
   - `last_refresh_at`
4. Target at least `>=5000` symbols and `>=252` trading days for real baseline.
5. Return a handoff with data source, adjustment policy, license status, date range, symbol count, row counts, known gaps, and command outputs.

Codex should not modify benchmark code or Strategy Lab code to bypass data checks. Missing fields should be fixed in the data prep layer or clearly recorded as blockers.

## Runbook If DB Exists

Use:

```bash
PY=/Users/lv111101/.pyenv/versions/3.11.12/bin/python
DATE_TAG=$(date +%Y%m%d)
```

Validate:

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

Benchmark:

```bash
$PY benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 5000 \
  --days 252 \
  --runs 5 \
  --output outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl
```

Gate summary:

```bash
$PY benchmarks/gate_summary.py \
  --validation outputs/benchmarks/real_data_validation_${DATE_TAG}.json \
  --benchmark outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl \
  --output outputs/benchmarks/gate_summary_${DATE_TAG}.json
```

Acceptance:

- `validate_real_data.py` exits `0`, `ok=true`, `errors=[]`.
- `light_backtest_perf.py` exits `0` and writes real `full_polars` records for `5000 x 252`.
- `gate_summary.py` exits `0`, `ok=true`, all gates pass.

## Gate Distinctions

Synthetic smoke:

- proves scripts and JSON output work
- uses synthetic generated data
- performance numbers are informational only
- does not unblock real-data release

Real baseline:

- requires real local DB
- minimum `5000` symbols x `252` trading days
- requires validation first
- gate thresholds: total P50 `<20s`, total P95 `<30s`, data load P95 `<10s`, signal generation P95 `<12s`, equity+metrics P95 `<8s`, peak memory `<4096MB`, failure count `0`

Pilot / public beta:

- requires real baseline plus data governance controls
- pilot freshness target: <= 30 calendar days
- public beta freshness target: <= 7 calendar days
- public beta should move to `>=3 years` history before showing real metrics externally
- license must explicitly allow the intended use

## Data Risks

The next real DB handoff must address:

- freshness: stale data can mislead pilot users
- 复权: raw/forward/backward-adjusted prices cannot be mixed
- 幸存者偏差: universe must respect list/delist dates
- 未来函数: indicators, State Cube joins, industry and universe membership must be point-in-time
- 停牌退市: halted and delisted instruments must not appear as freely tradable bars
- 涨跌停: entry and exit feasibility need limit-up/limit-down fields
- license: external use needs explicit permission, not inferred permission

## Files

New files produced by this Kimi run:

- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-db-baseline-run.md`

Files that should not be committed:

- `outputs/benchmarks/*`
- `data/*.duckdb`
- vendor raw data
- credentials or token files

## Non-Goals

- No code implementation.
- No benchmark or Strategy Lab edits.
- No data-source replacement recommendation.
- No real-performance claim.
- No MVP stub/mock blockage.
- No Git commit.

## Next Step

Codex should either prepare the real DB handoff or explicitly mark real baseline as blocked while proceeding with MVP stub/synthetic work. Once real DBs exist, rerun the validate/perf/gate-summary sequence above and attach the generated output paths in a new run note without committing those output files.
