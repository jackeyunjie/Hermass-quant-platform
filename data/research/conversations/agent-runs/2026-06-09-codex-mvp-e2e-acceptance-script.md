# Codex MVP E2E Acceptance Script

## Background

The Strategy Lab E2E runner already implements the Phase 1 weekly MVP chain:

`中文策略输入 -> DSL v2 -> 校验 -> 红线 -> Preview -> Light Backtest -> Audit`

Unit tests verify the behavior, but the project needed a reusable command that any Agent can run as a sample-level acceptance check.

## Decision

Add `scripts/run_strategy_lab_mvp_e2e_acceptance.py` as the project-level executable MVP acceptance entry.

The script runs:

- 3 frozen valid Chinese strategy samples.
- 1 missing stop-loss red-line failure sample.
- 1 over-position red-line failure sample.

## Reason

This turns the `AGENTS.md` MVP bottom line into one repeatable command instead of requiring future Agents to reconstruct the acceptance flow from tests and documents.

The command preserves the current safety contract:

- Valid samples must reach `stage_reached="complete"`.
- Valid samples must write audit operations in order: generation, validation, preview, backtest.
- Failure samples must stop at validation.
- Failure samples must not run preview/backtest.
- Light Backtest remains explicitly marked `light_stub`.

## Validation

Command:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py --run-id smoke
```

Result:

- `passed=true`
- `passed_cases=5`
- `failed_cases=[]`

Additional baseline:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
```

Result:

- `197 passed, 1 warning`

## Files Added Or Modified

- `scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- `README.md`
- `skills/hermass-quant-execution/SKILL.md`
- `data/research/conversations/agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md`

## Next Step

Use this command as the default Strategy Lab MVP regression gate before expanding from 3 frozen samples to the next batch of Chinese strategy inputs.
