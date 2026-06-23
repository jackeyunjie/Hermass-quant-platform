---
name: hermass-quant-execution
description: Use when implementing or reviewing Hermass AI Quant Platform MVP tasks involving Strategy DSL, red lines, backtest integration, Agent routing, observability, or project execution discipline.
---

# Hermass Quant Execution

## Trigger

Use this skill for Hermass AI Quant Platform implementation tasks, especially:

- Strategy DSL schema or condition registry work.
- DSL validation and red-line checks.
- Backtest adapter or Light Backtest integration.
- Strategy Lab API implementation.
- Agent task routing or debate contracts.
- Project memory, audit, trace, or Obsidian updates.

## Workflow

1. Read `AGENTS.md`.
2. Identify whether the task is MVP, platform extension, or research sandbox.
3. For MVP tasks, prioritize DSL -> validation -> preview -> backtest -> audit.
4. For research tasks, keep work isolated and do not block MVP.
5. Add or update tests whenever behavior changes.
6. Record important decisions in `data/research/conversations/decisions/`.

## Guardrails

- Do not execute LLM-generated strategy code.
- Do not bypass `red_lines.py`.
- Do not put business logic in `web/main.py`.
- Do not add full Agent Debate before the deterministic strategy path works.
- Do not claim performance targets without a benchmark.
- Do not use Python row loops in the backtest hot path.
- Do not query State Cube with `SELECT *`.

## Backtest Defaults

- Use DuckDB for data loading, column pruning, precomputed indicators, and optional `filter_first`.
- Use Polars for signal generation, equity curve simulation, and metrics.
- Write benchmark results as JSONL under `outputs/benchmarks/`.

## Light Backtest v1 (Phase 2)

### Architecture

```
DSL v2 -> validate_dsl() -> red-line -> DuckDB load -> Polars compute -> Storage write -> Audit write
```

### Module Boundary

| Module | Responsibility |
|---|---|
| `backtest_adapter.py` | Facade: routes to engine or stub |
| `backtest_models.py` | Internal dataclass contracts |
| `backtest_data_provider.py` | DuckDB load + column normalization |
| `light_backtest_engine.py` | Polars signal/trade/equity hot path |
| `backtest_metrics.py` | Pure metric functions |
| `backtest_evidence.py` | Trade record + event evidence |

### Trading Rules (MVP)

- Long-only daily-bar. No short, no T+0.
- Close execution with slippage. A-share cost model (commission 万三, stamp 千五, slippage 千一).
- 100-share lot rounding. One position per symbol.
- Exit priority: stop_loss > take_profit > price_cross_ma > ma_death_cross.
- Same-day conflict: exit first, no re-entry after exit.
- Suspended = no trade. Limit-down blocks sell. Limit-up filter blocks buy.

### Mode Routing

- `foundation_db` exists -> `light_real_v1` via provider + engine.
- `foundation_db` is None -> `light_stub` (Phase 0 compatibility).
- Red-line failure -> no DuckDB read, no trade write, audit `validation` only.

### Test Suite

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/ -q
```

Covers: provider (11), engine (14), metrics (22), evidence (23), integration (8), + 200 Phase 0/1 tests.

## Output

Every implementation pass should produce:

- Changed files.
- Validation performed.
- Remaining risk.
- Next step.

## MVP Acceptance Command

Run the sample-level Strategy Lab acceptance when changing the MVP chain:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

The command must pass 3 valid frozen samples and 2 red-line failure samples.
It writes JSON/DuckDB evidence under `outputs/strategy_lab/`.

## Known Blockers

- Real DB baseline blocked: `data/p116_foundation.duckdb` and `data/state_cube.duckdb` not present.
- `light_real_v1` is internal synthetic smoke only, NOT publishable as real baseline.
- Phase 2 hardening backlog: real DB fallback, date-level multi-symbol semantics, trade/event persistence, volume_ratio contract.
