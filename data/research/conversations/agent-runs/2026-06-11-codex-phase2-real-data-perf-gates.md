# Codex Run Note: Phase 2 Real Data And Performance Gates Execution

## Background

Kimi delivered the Phase 2 real-data / performance-gate handoff in:

- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-data-perf-gates.md`

This note records the Codex execution of the Codex-owned tasks from that handoff.

## Decision

Implemented the Phase 2 data-validation extensions and gate-summary tooling while preserving MVP mock/stub acceptance. Real-data baseline remains blocked until the project has populated `data/p116_foundation.duckdb` and `data/state_cube.duckdb`.

## Executed Changes

### 1. Extended `benchmarks/validate_real_data.py`

Added P0 checks:

- CLI parameters: `--min-symbols`, `--min-trading-days`, `--max-staleness-days`, `--as-of-date`.
- Type checks for `date`, numeric OHLCV/indicator columns, and boolean/integer flags.
- Uniqueness check on `(symbol, date)` for `daily_bars` and `state_cube`.
- Null/range checks: `close > 0`, `high >= low`, `volume >= 0`, and indicator null rates.
- Trading-day coverage check per symbol, with top low-coverage offenders.
- Freshness check: `date_max` vs `as_of_date`, fails when stale beyond threshold.
- Schema alias check for `state_cube`: `d1_state` vs `state_hex_d1`, `w1_state` vs `state_hex_w1`, `mn1_state` vs `state_hex_mn1`.
- Metadata check: looks for `data_license` table or `metadata.json` beside the DB and reports missing `price_adjustment`, `data_source`, `license_status`, `last_refresh_at`.

Also fixed `benchmarks/_synthetic.py` to emit `date` as a `DATE` type so synthetic fixtures can pass the new type checks.

### 2. Added `benchmarks/gate_summary.py`

Reads a validation JSON and a `light_backtest_real_*.jsonl`, computes per-mode percentiles, and emits an overall `PASS`/`FAIL` verdict against the Phase 2 hot-path gates:

- Total P50 < 20s, P95 < 30s
- Data load P95 < 10s
- Signal generation P95 < 12s
- Equity + metrics P95 < 8s
- Peak memory P95 < 4096 MB
- Failure rate = 0
- Data validation `ok = true`

Supports auto-discovery of newest files or explicit `--validation` / `--benchmark` paths.

### 3. Static Hot-Path Grep

Scanned `benchmarks/*.py` for forbidden patterns:

| Pattern | Result | Notes |
|---------|--------|-------|
| `apply(lambda row` | none | — |
| `iterrows` | none | — |
| `for row in` | found in `validate_real_data.py` and `state_cube_query.py` | Only for schema/index/date enumeration, not signal/equity hot path |
| `.to_pandas()` | none | — |
| `SELECT *` | found in `_synthetic.py` and `validate_real_data.py` | `_synthetic.py` is setup; `validate_real_data.py` uses `LIMIT 0/1` for metadata only |
| `eval(` / `exec(` | none | — |
| Python group loop by symbol | none | — |

No blocking forbidden patterns in the benchmark hot paths.

## Acceptance Results

### Missing DB Negative Check

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db /tmp/missing_foundation.duckdb \
  --state-cube-db /tmp/missing_state.duckdb \
  --output outputs/benchmarks/validation_missing.json
```

Result: exit code `1`, `ok=false`, errors list contains both missing DBs. ✅

### Synthetic Smoke

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/light_backtest_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/indicator_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/duckdb_vs_polars_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/state_cube_smoke.jsonl
```

Result: all exit `0`, each JSONL has rows, `data_source="synthetic"`. ✅

### Real Baseline

Not executed. `data/p116_foundation.duckdb` and `data/state_cube.duckdb` do not exist in the workspace yet. The real baseline commands are ready and should be run once the real datasets are refreshed/populated.

## Gate Summary Test

Ran gate summary against synthetic outputs to verify the script:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/gate_summary.py \
  --validation outputs/benchmarks/validation_synthetic_test.json \
  --benchmark outputs/benchmarks/light_backtest_smoke.jsonl \
  --output outputs/benchmarks/gate_summary_synthetic_test.json
```

Result: `status=PASS`, all 8 gates pass (synthetic numbers are far below thresholds). This validates the gate-summary machinery, not real performance.

## Files Changed

- `benchmarks/validate_real_data.py`
- `benchmarks/_synthetic.py`
- `benchmarks/gate_summary.py` (new)
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-real-data-perf-gates.md` (this note)
- `data/research/conversations/PROJECT_INDEX.md`

## Files Not Committed

- `outputs/benchmarks/*.jsonl`
- `outputs/benchmarks/*.json`
- Temporary `/tmp/*.duckdb`

## Next Steps

1. Populate or refresh `data/p116_foundation.duckdb` and `data/state_cube.duckdb` with real data.
2. Add `data_license` table or `metadata.json` with `price_adjustment`, `data_source`, `license_status`, `last_refresh_at`.
3. Run the real baseline commands and check gate summary output.
4. Address any real-data validation warnings/errors before declaring Phase 2 real backtest release ready.

## Explicit Non-Goals

- No data-source replacement.
- No deletion or migration of existing DuckDB files.
- No blocking of MVP mock/stub acceptance.
- No synthetic result treated as real performance.
- No GPU, distributed engine, Dask/Ray, or external online service.
- No user/LLM generated Python strategy execution.
