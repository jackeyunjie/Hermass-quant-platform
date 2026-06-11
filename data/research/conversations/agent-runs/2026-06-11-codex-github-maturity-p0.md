# Codex GitHub Maturity P0

## Background

Kimi K12 completed a GitHub stars and open-source maturity audit with verdict `NOT_READY_TO_PROMOTE`.

The repository needed practical P0/P1 maturity assets before any external promotion:

- A README that explains the project in 30 seconds.
- Copyable Quickstart commands without local absolute paths.
- Safety boundaries and disclaimer.
- Public example DSL files.
- Issue templates and contribution guidance.
- GitHub metadata guidance for manual owner settings.

## Decision

Codex implemented the low-risk maturity items that do not require legal or owner-only GitHub permissions.

Codex initially did not add a `LICENSE` file because license choice is a legal and business decision requiring owner confirmation.

The owner later confirmed Apache-2.0 on 2026-06-11, so Codex added `LICENSE`.

The owner also confirmed remote metadata changes. Codex updated GitHub Description and Topics through the GitHub API on 2026-06-11.

## Changes

- Rewrote `README.md` around the DSL -> validation -> red-line -> preview -> Light Backtest -> audit loop.
- Added `CONTRIBUTING.md`.
- Added `.github/ISSUE_TEMPLATE/bug_report.md`.
- Added `.github/ISSUE_TEMPLATE/feature_request.md`.
- Added `docs/github/METADATA_RECOMMENDATIONS.md`.
- Added 3 frozen Strategy Lab example DSL JSON files under `examples/strategy_lab/`.
- Added `hermass_platform/strategy_lab/tests/test_examples.py` so public examples are validated by tests.
- Added `LICENSE` with Apache License 2.0 after owner confirmation.
- Updated `.gitignore` to exclude `6月 8 日工作计划.MD`.
- Updated GitHub repository description.
- Updated GitHub repository topics.

## Reason

These changes make the repository easier to understand and safer to share, while preserving K11 service boundaries:

- No investment advice.
- No real trading.
- No performance guarantee.
- `light_stub` remains clearly labeled as non-real performance.

## Validation

Run:

```bash
python3 -m pytest hermass_platform/strategy_lab/tests -q
python3 scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

## Next Step

Apache-2.0 is now applied locally. GitHub Description and Topics are updated remotely. Broader promotion still depends on committing and pushing the local working tree.

GitHub metadata applied:

- Description: `AI-native quantitative strategy research platform: Chinese strategy input -> DSL -> red-line validation -> preview -> audit.`
- Topics: `audit-trail`, `backtesting`, `dsl`, `duckdb`, `polars`, `pydantic`, `quantitative-trading`, `strategy-research`.
