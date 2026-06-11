"""Validate public Strategy Lab example DSL files."""

from __future__ import annotations

import json
from pathlib import Path

from hermass_platform.strategy_lab.dsl_schema import StrategyDSL
from hermass_platform.strategy_lab.dsl_validator import validate_dsl


REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "examples" / "strategy_lab"


def test_strategy_lab_examples_are_valid_dsl() -> None:
    example_paths = sorted(EXAMPLES_DIR.glob("*.json"))
    assert example_paths, "Expected public Strategy Lab examples"

    for example_path in example_paths:
        dsl = StrategyDSL.model_validate(json.loads(example_path.read_text(encoding="utf-8")))
        validation = validate_dsl(dsl)

        assert validation.passed, (
            example_path.name,
            [error.code for error in validation.errors],
        )
        assert not validation.has_red_line_violation, example_path.name
        assert dsl.has_condition_type("stop_loss_pct"), example_path.name
