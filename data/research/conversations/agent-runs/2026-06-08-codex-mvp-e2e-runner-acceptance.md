# Codex MVP E2E Runner Acceptance

## Background

Qoder completed `agents/QODER_NEXT_TASK_2026_06_08_E2E_SAMPLES.md` by adding:

- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `data/research/conversations/agent-runs/2026-06-08-qoder-mvp-e2e-sample-contracts.md`

Codex then audited the implementation against the 2026-06-08 weekly MVP objective:

`中文策略输入 -> DSL -> 校验 -> Preview -> Light Backtest -> Audit`

## Decision

Accept the Qoder contract and keep the E2E runner as the Phase 1 weekly sample runner, with Codex fixes applied.

## Fixes Applied

- Added missing `BacktestMetrics` fields: `annual_return`, `profit_factor`, `trade_count`.
- Fixed `NLToDSLParser` so `D1状态EF数量不少于2` maps to `state_ef_count(operator=">=", value=2)`.
- Preserved over-limit risk values through `RiskConfig.model_construct()` so red-line checks can audit `RL_MAX_POSITION` instead of failing early in Pydantic construction.
- Passed `preview_duckdb_path` into `PreviewService` through `PreviewConfig`.
- Saved strategy versions before saving backtest results, avoiding storage foreign key failures.
- Added audit record loading for generation and validation failure returns.
- Added red-line results to preview/backtest audit records.
- Stopped the chain after failed preview instead of running backtest on an invalid preview result.
- Added focused E2E tests for 3 frozen samples, missing stop loss, over-position red-line rejection, audit order, and storage persistence.

## Validation

Commands:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_e2e_runner.py -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py
```

Results:

- `test_e2e_runner.py`: 9 passed, 1 warning.
- Strategy Lab tests: 197 passed, 1 warning.
- `py_compile`: passed.

## 2026-06-10 Follow-up Review

Qoder reported the three critical fixes again:

- Combined entry extraction for `MA5上穿MA20且D1状态EF数量不少于2`.
- Risk config structural construction should not block red-line audit for over-limit position/risk values.
- Missing stop loss should reach validator and produce `RL_EXIT_MUST_HAVE_STOP_LOSS`.

Codex re-ran the project MVP acceptance command. The sample-level acceptance passed 5/5 cases, but full Strategy Lab tests initially failed because `test_dsl_schema.py` still expected Pydantic to reject red-line violations directly.

Codex fixed the tests to match the intended boundary:

- `RiskConfig` allows red-line-range violations structurally up to `1.0`.
- `dsl_validator` owns `RL_MAX_POSITION`, `RL_RISK_PER_TRADE`, and `RL_STOP_LOSS_REQUIRED`.
- `test_dsl_validator.py` now explicitly verifies `stop_loss_required=False` triggers `RL_STOP_LOSS_REQUIRED`.

Follow-up validation:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_dsl_schema.py hermass_platform/strategy_lab/tests/test_dsl_validator.py hermass_platform/strategy_lab/tests/test_e2e_runner.py -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py --run-id codex-post-fix
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

Results:

- Targeted tests: 59 passed, 1 warning.
- MVP E2E acceptance: 5/5 cases passed.
- Strategy Lab tests: 197 passed, 1 warning.
- `py_compile`: passed.

## Next Step

Use `run_mvp_e2e_sample()` as the working runner for the weekly 3-sample acceptance, then decide whether to promote the parser and runner flow into a project-local Skill after the same workflow repeats.
