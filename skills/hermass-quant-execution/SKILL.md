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

## Output

Every implementation pass should produce:

- Changed files.
- Validation performed.
- Remaining risk.
- Next step.
