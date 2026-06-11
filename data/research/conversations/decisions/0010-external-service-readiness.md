# 0010 External Service Readiness

## Background

The user asked whether Hermass can provide services externally.

The current MVP chain is working at sample-level acceptance:

`中文策略输入 -> DSL v2 -> 校验 -> 红线 -> Preview -> Light Backtest -> Audit`

However, the current system is still an MVP. Light Backtest may still include stub/mock behavior, public-facing service copy is not finalized, and legal/compliance review has not been completed.

## Decision

Hermass may only provide **controlled invitation-based research pilots** at the current stage.

Hermass is **not ready for public commercial launch**.

Allowed current service scope:

- Invitation-only demo.
- Strategy research and backtest experiment workflow.
- Chinese strategy input to DSL structure.
- Red-line checks, condition preview, and Light Backtest research demonstration.
- Audit trail and strategy version explanation.
- Private testing with familiar users, internal teams, or research collaborators.

Prohibited current service scope:

- No investment advice.
- No stock recommendations or buy/sell promises.
- No guaranteed returns.
- No real trading.
- No custody or fund management.
- No user Python strategy execution.
- No execution of LLM-generated code.
- No marketing as an auto-trading or auto-stock-picking product.
- No presenting `light_stub`, mock, or unvalidated results as real performance.

## Reason

The MVP demonstrates the deterministic strategy research loop, but public external financial services carry regulatory, operational, and trust risks.

The safe product boundary is research tooling:

- Users provide strategy ideas.
- Hermass structures and validates the strategy.
- Hermass previews and backtests under red-line constraints.
- Outputs are auditable and explicitly non-advisory.

This preserves MVP momentum without implying investment advice, trading execution, or performance guarantees.

## Next Step

Kimi should execute `agents/KIMI_NEXT_TASK_EXTERNAL_SERVICE_READINESS_PILOT.md` and produce:

- Service readiness verdict.
- Invitation-only pilot plan.
- Allowed/prohibited services.
- External service copy and disclaimers.
- Engineering go/no-go checklist.
- Legal/compliance review checklist.

Codex should review Kimi's output before any external user access is expanded.
