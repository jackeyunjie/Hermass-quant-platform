# Contributing

Hermass is currently an MVP research platform. Contributions should preserve the deterministic Strategy Lab path before adding agentic or platform extensions.

## Ground Rules

- Read [AGENTS.md](AGENTS.md) before making changes.
- Keep DSL as the only strategy expression.
- Do not execute LLM-generated strategy code.
- Do not bypass red-line checks.
- Do not put business logic in web routes.
- Do not present mock, synthetic, or `light_stub` outputs as real performance.
- Do not commit `outputs/`, DuckDB runtime files, caches, secrets, or personal notes.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## Required Checks

Run these before proposing Strategy Lab changes:

```bash
python3 -m pytest hermass_platform/strategy_lab/tests -q
python3 scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

For factor registry changes, also run:

```bash
python3 -m pytest hermass_platform/factors/tests -q
```

## Pull Request Expectations

- Explain the user-visible behavior change.
- Include tests for changed behavior.
- State whether the change affects DSL, red lines, preview, backtest, or audit.
- State what validation was run.
- Add an Obsidian decision or agent-run record when the change affects project direction.

## Issue Scope

Useful issues:

- Reproducible bugs in the MVP chain.
- DSL schema or condition registry gaps.
- Red-line validation gaps.
- Preview/backtest/audit reproducibility issues.
- Documentation or onboarding problems.

Out of scope for now:

- Real trading.
- Broker integration.
- Investment advice.
- Stock recommendations.
- Return guarantees.
