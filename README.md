# Hermass AI Quant Platform

Hermass turns Chinese quantitative strategy ideas into verifiable, auditable structured research loops.

Current MVP path:

```text
Chinese strategy input
  -> DSL v2
  -> Schema/Pydantic validation
  -> red-line checks
  -> condition hit preview
  -> Light Backtest stub
  -> report and audit storage
```

## What It Is

- A DSL-first strategy research framework.
- A red-line-first validation chain for mandatory stop loss and position limits.
- An audit-first execution loop where generation, validation, preview, and backtest share a `trace_id`.
- A deterministic MVP runner for frozen Chinese strategy samples.

## What It Is Not

- Not investment advice.
- Not an automatic stock-picking tool.
- Not a trading bot.
- Not a real-order execution system.
- Not a performance or profit guarantee.

Current Light Backtest output is explicitly marked as `light_stub`. It is a framework placeholder, not real historical performance.

## Current Status

Phase 0/1 MVP is implemented for the Strategy Lab path:

- DSL v2 Pydantic schema.
- Condition registry and parameter validation.
- Red-line validation.
- Mock preview service.
- DuckDB storage and audit logging.
- Sample-level E2E runner.
- Acceptance script covering 3 valid samples and 2 red-line failures.

Phase 2 Light Backtest v1 (synthetic integration):

- `light_backtest_engine.py` - Polars vectorized signal computation + trade generation.
- `backtest_data_provider.py` - DuckDB data loading with column normalization.
- `backtest_evidence.py` - Trade record and event evidence construction.
- `backtest_metrics.py` - Performance metrics (sharpe, drawdown, win_rate, etc.).
- `backtest_adapter.py` - Facade routing to real engine or stub fallback.
- `e2e_runner.py` - Complete NL→DSL→Validation→Preview→Backtest→Audit pipeline.
- API truncation metadata (`daily_curve_total_count`, `trades_truncated`).
- Tradability hardening (limit-down blocked exit → hold evidence).

Phase 2 Hardening (2026-06-19):

- ✅ No silent stub fallback when real DB is missing (returns `BT_DATA_DB_NOT_FOUND`).
- ✅ Multi-symbol date-level execution semantics (sort: `date ASC, symbol ASC`).
- ✅ Trade/event evidence E2E persistence via `BacktestResult.signal_frame`.
- ✅ `volume_ratio OR volume_ma_N` provider alternate group contract.

Phase 3 Web UI (2026-06-19):

- `web/main.py` + `web/strategy_lab_routes.py` - FastAPI + Jinja2 thin layer.
- Strategy Structuring page: Chinese input → DSL → validation → red-line result.
- Strategy Diagnosis page: Preview + Light Backtest by trace_id.
- Evidence Lab page: Audit timeline + trades + trade events by trace_id.
- Explicit run tags (`synthetic` / `light_stub` / `light_real_v1`) + not-investment-advice disclaimer.
- Data readiness badge: reads `outputs/benchmarks/data_readiness_status.json` and displays READY / PARTIAL / NOT_READY.
- Web smoke test: `scripts/test_web_ui_smoke.py`.

Latest local verification:

- Strategy Lab tests: `278 passed`.
- MVP E2E acceptance: `5/5 cases passed`.
- Web UI smoke test: `5/5 checks passed`.

## Quickstart

Requires Python 3.11+.

```bash
git clone https://github.com/jackeyunjie/Hermass-quant-platform.git
cd Hermass-quant-platform
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

Run the MVP acceptance chain:

```bash
python3 scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

Run Strategy Lab tests:

```bash
python3 -m pytest hermass_platform/strategy_lab/tests -q
```

Validate example DSL files:

```bash
python3 -m pytest hermass_platform/strategy_lab/tests/test_examples.py -q
```

Run the Web UI locally:

```bash
python3 -m uvicorn web.main:app --reload --port 8000
```

Then open http://localhost:8000 and navigate through Strategy Structuring / Diagnosis / Evidence Lab.

The acceptance script writes local evidence under `outputs/strategy_lab/`. The `outputs/` directory is intentionally ignored by Git.

## Example

Input:

```text
MA5上穿MA20买入，跌破MA10卖出，止损8%
```

DSL excerpt:

```json
{
  "strategy_id": "sample_ma_5_20_stop_8",
  "schema_version": "strategy_dsl_v2",
  "entry": [
    {
      "condition_type": "ma_golden_cross",
      "params": {
        "fast_period": 5,
        "slow_period": 20
      }
    }
  ],
  "exit": [
    {
      "condition_type": "price_cross_ma",
      "params": {
        "timeframe": "D1",
        "ma_period": 10,
        "direction": "below"
      }
    },
    {
      "condition_type": "stop_loss_pct",
      "params": {
        "value": 0.08
      }
    }
  ],
  "risk": {
    "risk_per_trade": 0.02,
    "max_position_pct": 0.2,
    "stop_loss_required": true
  }
}
```

Full examples are available in [examples/strategy_lab](examples/strategy_lab).

Expected red-line result:

```json
{
  "passed": true,
  "triggered_rules": []
}
```

Light Backtest result is currently a stub:

```json
{
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

## Frozen MVP Samples

| Sample | Input | Purpose |
| --- | --- | --- |
| `sample_ma_5_20_stop_8` | `MA5上穿MA20买入，跌破MA10卖出，止损8%` | Basic MA strategy with mandatory stop loss |
| `sample_state_volume_stop_8_take_15` | `D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，止损8%，止盈15%` | State + volume entry with stop loss and take profit |
| `sample_ma_state_limit_filter` | `MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，跌破MA10或止损8%卖出` | Composite entry, limit-up filter, OR exit |

Failure samples in the acceptance script cover:

- Missing stop loss -> `RL_EXIT_MUST_HAVE_STOP_LOSS`.
- Position above 25% -> `RL_MAX_POSITION`.

## Architecture

```text
NLToDSLParser
  -> StrategyDSL
  -> validate_dsl
  -> red-line checks
  -> PreviewService
  -> BacktestAdapter
  -> StrategyAuditLogger / StrategyLabStorage
```

Key modules:

- [hermass_platform/strategy_lab/dsl_schema.py](hermass_platform/strategy_lab/dsl_schema.py)
- [hermass_platform/strategy_lab/condition_registry.py](hermass_platform/strategy_lab/condition_registry.py)
- [hermass_platform/strategy_lab/dsl_validator.py](hermass_platform/strategy_lab/dsl_validator.py)
- [hermass_platform/strategy_lab/preview_service.py](hermass_platform/strategy_lab/preview_service.py)
- [hermass_platform/strategy_lab/e2e_runner.py](hermass_platform/strategy_lab/e2e_runner.py)
- [scripts/run_strategy_lab_mvp_e2e_acceptance.py](scripts/run_strategy_lab_mvp_e2e_acceptance.py)

## Roadmap

| Phase | Goal | Status |
| --- | --- | --- |
| Phase 0 | DSL schema, condition registry, red-line validation | ✅ Implemented |
| Phase 1 | Preview, storage, audit, sample E2E runner | ✅ Implemented |
| Phase 2 | Real Light Backtest with DuckDB + Polars | ✅ Synthetic integration (blockers resolved) |
| Phase 3 | Web UI, richer factor/block library, industry-chain agent | ✅ Web UI implemented (Jinja2/FastAPI); factor library & industry-chain agent planned |

The current default route is MVP first. Full Agent Debate, Paper Trading, TS-FM, and RAG-KG remain research backlog items.

## Safety And Compliance

Hermass is for strategy research and engineering experiments only.

- It does not provide investment advice.
- It does not recommend securities.
- It does not execute trades.
- It does not manage funds.
- Stub or mock outputs must not be presented as real performance.

All strategy modifications, preview, and backtest execution paths must pass red-line checks before continuing.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).

## Project Coordination

- Project rules: [AGENTS.md](AGENTS.md)
- Task allocation: [docs/TASK_ALLOCATION.md](docs/TASK_ALLOCATION.md)
- Agent prompts: [agents](agents)
- Obsidian vault: [data/research/conversations](data/research/conversations)
- Strategy Lab samples: [docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md](docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md)
- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
