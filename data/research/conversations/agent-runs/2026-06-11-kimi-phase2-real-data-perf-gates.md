# Kimi Run Note: Phase 2 Real Data And Performance Gates

## Background

Codex requested a Phase 2 real-data / performance-gate handoff from the Kimi Research Engineer role. The project already has MVP mock/stub acceptance assets and benchmark scripts, but true Phase 2 Light Backtest cannot be accepted on synthetic fixture results alone.

Read context:

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `benchmarks/README.md`
- `benchmarks/validate_real_data.py`
- `benchmarks/light_backtest_perf.py`
- `benchmarks/indicator_precompute_vs_compute.py`
- `benchmarks/duckdb_vs_polars.py`
- `benchmarks/state_cube_query.py`
- `benchmarks/_synthetic.py`
- `data/research/conversations/agent-runs/2026-06-06-kimi-real-data-benchmark-runbook.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`
- `agents/KIMI2_NEXT_TASK_DATA_REFRESH_REPLACEMENT_AUDIT.md`

`data/research/conversations/agent-runs/2026-06-11-kimi2-data-refresh-replacement-audit.md` was requested as recent context but does not exist in the current workspace. I treated that as a missing upstream audit and did not infer that it had been completed.

## Decision

Verdict: **MIXED**.

- Freeze MVP mock preview, synthetic smoke, and `light_stub` acceptance. These continue to support Phase 0/1 and do not depend on real historical data.
- Supplement the Phase 2 real-data contract before accepting real Light Backtest.
- Refresh / validate real datasets before invitation pilot upgrades, GitHub demo metrics, or public beta.
- Defer data-source replacement unless license or quality evidence makes replacement necessary.

This preserves MVP velocity while making real-data gates explicit for Phase 2.

## Benchmark Capability Inventory

| Script | Current capability | Main gap |
|--------|--------------------|----------|
| `validate_real_data.py` | DB/table/column/row/date/index checks for `daily_bars` and `state_cube` | No type, duplicate key, freshness, metadata, adjustment, suspension/delist, leakage, license checks |
| `light_backtest_perf.py` | `full_polars` vs `filter_first`, staged timing, `peak_memory_mb` | Not DSL-backed; `filter_first` is heuristic; no gate verdict |
| `indicator_precompute_vs_compute.py` | `ma_20` compute vs precomputed read | Only one indicator; no state/volume/ATR/ADX coverage |
| `duckdb_vs_polars.py` | DuckDB-only vs DuckDB + Polars simple MA signal | No exit/risk/filter complexity |
| `state_cube_query.py` | no-cache / pruned / LRU cache query comparison | No wide-table or industry/state aggregation baseline |
| `_synthetic.py` | synthetic `daily_bars` + `state_cube` fixture | No real suspension, delisting, adjustment, industry drift, limit regime |

Conclusion: current scripts are good for smoke and first baseline, but Phase 2 needs stronger data readiness checks and an explicit gate summary.

## Data Contract

Required Phase 2 tables:

- `daily_bars` in `data/p116_foundation.duckdb`
- `state_cube` in `data/state_cube.duckdb`
- `stock_info` or `market_assets`
- `adjust_factors`
- `trading_calendar`
- metadata table/file for `data_source`, `license_status`, `price_adjustment`, `last_refresh_at`

Required high-risk fields:

- `daily_bars`: `symbol`, `date`, OHLCV, `amount`, `adj_factor`, `is_suspended`, `is_limit_up`, `is_limit_down`, `limit_up_price`, `limit_down_price`, `ma_5`, `ma_10`, `ma_20`, `ma_60`, `volume_ma_20`, `volume_ratio`, `atr_14`, `bb_position`, `adx_14`
- `state_cube`: `symbol`, `date`, `d1_state/w1_state/mn1_state` plus aliases or contract for `state_hex_d1/state_hex_w1/state_hex_mn1`, `ef_count`, `ef_width`
- `stock_info/market_assets`: `symbol`, `name`, `exchange`, `list_date`, `delist_date`, `industry`, `industry_date` or `valid_from/valid_to`, `is_st`

The current registry/translator has an alias mismatch risk:

- `validate_real_data.py` checks `d1_state/w1_state/mn1_state`.
- `condition_registry.py` declares `state_hex_{timeframe_lower}` for `state_hex_in`.

Qoder should define the canonical alias strategy before Phase 2 real backtest is exposed.

## Hot Path Gates

Synthetic smoke:

- All 4 benchmark scripts exit 0.
- JSONL rows are produced.
- Performance numbers are informational only.

Real baseline, 5000 symbols x 252 trading days:

| Metric | Gate |
|--------|------|
| Total P50 | < 20s |
| Total P95 | < 30s |
| Data load P95 | < 10s |
| Signal generation P95 | < 12s |
| Equity + metrics P95 | < 8s |
| Memory | < 4GB RSS preferred, `tracemalloc` fallback |
| Failure rate | 0/5 runs |
| Data validation | `ok=true`, 0 errors |

This gate blocks Phase 2 real backtest release, real-metrics pilot upgrade, GitHub demo real metrics, and public beta. It does not block MVP mock/stub acceptance.

## Risk Register

| Risk | Required mitigation |
|------|---------------------|
| Freshness | `date_max`, `last_refresh_at`, staleness threshold |
| Survivorship bias | `list_date/delist_date`; date-aware universe |
| Future leakage | rolling/window formulas only use current and prior rows; time-valid industry/constituents |
| Adjustment mismatch | `price_adjustment` metadata and `adj_factor` traceability |
| Suspension/delisting | `is_suspended`, delist handling, missing-day explanation |
| Limit-up/limit-down | both flags and prices, not just `is_limit_up` |
| Industry drift | `industry_date` or `valid_from/valid_to` |
| License | `license_status` before any external/pilot use |
| Mock/stub misunderstanding | UI/report labels for `mock`, `synthetic`, `light_stub` |

## Validation Commands

Negative validation:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db /tmp/missing_foundation.duckdb \
  --state-cube-db /tmp/missing_state.duckdb \
  --output outputs/benchmarks/validation_missing.json
```

Synthetic smoke:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/light_backtest_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/indicator_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/duckdb_vs_polars_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/state_cube_smoke.jsonl
```

Real baseline:

```bash
DATE_TAG=$(date +%Y%m%d)

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/real_data_validation_${DATE_TAG}.json

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 5000 --days 252 --runs 5 \
  --output outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl
```

## Next Steps

### Codex

1. Implement P0 extensions in `benchmarks/validate_real_data.py`: type checks, duplicate keys, freshness, metadata, null/range checks, and state alias reporting.
2. Add a gate summary command that reads validation JSON + real benchmark JSONL and emits pass/fail with failed thresholds.
3. Run static hot-path grep for forbidden patterns before Phase 2 backtest acceptance.
4. Keep `outputs/benchmarks/` and all DuckDB files out of Git.

### Qoder

1. Define `DataReadinessStatus` and include it in real backtest API responses.
2. Resolve field aliases for state and D1 price/MA columns.
3. Require real backtest results to include `mode="light_real"`, `data_cutoff_date`, `data_quality_flags`, `benchmark_gate_snapshot`, and `audit_trace_id`.

## Handoff For GitHub Sync

### Modified Files

- Added: `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md`
- Added: `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-data-perf-gates.md`

No benchmark code was changed. Current low-risk script improvements from the prior runbook already exist; remaining gaps require broader validation semantics and should be implemented as explicit Phase 2 tasks.

### Files To Commit

- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-data-perf-gates.md`

### Files Not To Commit

- `outputs/benchmarks/*.jsonl`
- `outputs/benchmarks/*.json`
- `outputs/benchmarks/*.duckdb`
- `data/*.duckdb`
- credentials, raw vendor exports, cache directories

### Suggested Commit Message

```text
[kimi] research: phase2 real data and performance gates

- Add Phase 2 Light Backtest real data contract
- Inventory benchmark capabilities and gaps
- Define validate_real_data next checks and commands
- Define synthetic smoke vs real baseline hot path gates
- Document freshness, survivorship, leakage, license risks

验收: N/A (research handoff; executable commands included)
```

## Explicit Non-Goals

- No data-source replacement as default answer.
- No deletion or migration of existing DuckDB files.
- No blocking of MVP mock/stub acceptance.
- No synthetic result treated as real performance.
- No GPU, distributed engine, Dask/Ray, or external online service.
- No user/LLM generated Python strategy execution.
