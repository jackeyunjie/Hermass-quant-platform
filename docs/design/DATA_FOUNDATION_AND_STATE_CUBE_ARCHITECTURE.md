# Data Foundation & State Cube Architecture

## One-Sentence Positioning

> State Cube is the core of the application and risk-control layer; it sits on top of a broader data foundation rather than being treated as just another raw input.

---

## Three-Layer Model

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3 — Application & Risk-Control                                       │
│                                                                            │
│  Strategy Lab            Red-Line Engine          Risk Guardian            │
│  • generate DSL         • RL_EXIT_MUST_HAVE_     • regime-aware limits     │
│  • validate DSL           STOP_LOSS              • concentration checks    │
│  • preview conditions   • RL_MAX_POSITION        • correlation guardrails  │
│  • run light backtest                                                      │
│                                                                            │
│  Consumes: State Cube (regime context), Foundation DB (observable facts)   │
└────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │ derived / interpreted
┌────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2 — State / Regime Cube (L0.5)                                       │
│                                                                            │
│  Multi-timeframe market-state abstraction built from Foundation DB.        │
│                                                                            │
│  Contents:                                                                 │
│  • MN1 / W1 / D1 / H4 / H1 state_hex                                       │
│  • EF width, EF count, boundary distance                                   │
│  • Multi-timeframe resonance scores                                        │
│  • Regime classification (trending / ranging / breakout / compression)     │
│                                                                            │
│  Storage: `state_cube` table in `state_cube.duckdb` or `foundation_db`     │
│  Key property: methodology-dependent, must be validated for look-ahead.    │
└────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │ computed from
┌────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1 — Data Foundation (L0)                                             │
│                                                                            │
│  Broad base of observable, uninterpreted market and reference data.        │
│                                                                            │
│  Contents:                                                                 │
│  • OHLCV (`daily_bars`)                                                    │
│  • Tradability flags (`is_limit_up`, `is_limit_down`, `is_suspended`, ...) │
│  • Pre-computed indicators (`ma_5`, `ma_20`, `bb_position`, `atr_14`, ...) │
│  • Industry / concept classification                                       │
│  • Money flow (Blackwolf aggregates)                                       │
│  • Fundamental data (valuation, profitability, quality, growth)            │
│  • Macro / market breadth                                                  │
│                                                                            │
│  Storage: `p116_foundation.duckdb`                                         │
│  Key property: can independently support backtests with `include_state=false`.
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Layering Matters

### 1. Foundation DB can be validated independently

Before trusting any State-based signal, we must first trust the underlying bars, indicators, and tradability flags. M2 real-data baseline therefore has two readiness gates:

- **Foundation gate**: `validate_real_data.py` passes for L0 tables/columns.
- **State gate**: State Cube columns exist, are fresh, and have no look-ahead bias.

### 2. State Cube is a first-class risk input

Risk rules should not only enforce position limits and mandatory stop-loss. They should also ask:

- Is the strategy attempting to buy into a regime where the D1/H4/H1 states conflict?
- Is the entry state consistent with the strategy's stated timeframe?

These checks are only possible if State Cube is explicitly positioned as a risk-control input, not buried in a generic factor list.

### 3. Evidence is layered

Every trade record in `strategy_trade_events` carries:

- **L0 facts**: price, volume, tradability flags at entry/exit.
- **L0.5 state**: `timeframe_states` JSON with MN1/W1/D1/H4/H1 state_hex.
- **L3 decision**: which DSL condition triggered entry/exit/hold.

This layering makes it possible to answer both "what happened?" (L0) and "why did the model think this was the right regime?" (L0.5).

---

## Module Mapping

| Layer | Representative File | Responsibility |
|-------|---------------------|----------------|
| L0 | `data/p116_foundation.duckdb` | Store daily bars, indicators, tradability, industry, money flow, fundamentals. |
| L0.5 | `data/state_cube.duckdb` or `state_cube` table | Store multi-timeframe state_hex, EF metrics, regime labels. |
| Boundary | `backtest_data_provider.py` | Connect both DBs, normalize column names, validate required columns, produce `MarketDataBundle`. |
| L3 | `light_backtest_engine.py` | Consume `d1_state` / `w1_state` / `mn1_state` for signals. |
| L3 | `backtest_evidence.py` | Persist `timeframe_states` in trade event evidence. |
| L3 | `preview_service.py` / condition registry | Use `state_cube` table for preview queries. |

---

## Data Flow: Backtest with State

```text
User DSL
    │
    ▼
validation / red-line
    │
    ▼
backtest_adapter.run_backtest()
    │
    ├── foundation_db ──► DuckDBBacktestDataProvider._load_daily_bars()
    │                       (L0: OHLCV, indicators, tradability flags)
    │
    ├── state_cube_db ──► DuckDBBacktestDataProvider._join_state_data()
    │                       (L0.5: state_hex, ef_count, ef_width)
    │
    ▼
MarketDataBundle
    │
    ▼
LightBacktestEngine
    │
    ├── signal generation (Polars vectorized)
    ├── row-level trade state machine
    └── evidence snapshots per entry/exit/hold
    │
    ▼
BacktestResult + persisted trades/events
```

---

## Non-Goals

- State Cube is **not** the only source of signals. L1 technical factors, L2 cross-sectional factors, and L3 fundamental factors remain independent inputs.
- Foundation DB is **not** aware of State Cube semantics. It provides the raw material; State Cube provides the interpretation.
- The layering does **not** imply that State Cube must be in a separate physical file. It may be a schema or table namespace within the same DuckDB instance.

---

## Migration Notes

Current code already respects this layering:

- `BacktestConfig` exposes both `foundation_db` and `state_cube_db`.
- `MarketDataRequest.include_state` toggles L0.5 loading.
- `DuckDBBacktestDataProvider` normalizes `state_hex_d1` → `d1_state`.

No breaking changes are required. This document formalizes a boundary that the implementation already follows.

---

## Related Documents

- `data/research/conversations/decisions/0015-state-cube-architectural-positioning.md`
- `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
- `docs/FACTOR_SOURCE_TAXONOMY.md`
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `hermass_platform/strategy_lab/backtest_data_provider.py`
