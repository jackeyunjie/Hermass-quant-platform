"""Tests for block_schema.py — 6 test points."""

import pytest

from hermass_platform.factors.block_schema import (
    BlockSpec,
    BlockType,
    ParameterSpec,
    ParameterSpace,
    ParameterMode,
    ContextRequirement,
)
from hermass_platform.factors.exceptions import BlockValidationError
from hermass_platform.factors.source_schema import EvidenceLevel


class TestBlockType:
    """6. Test BlockType enum."""

    def test_all_block_types(self):
        expected = {
            "signal", "entry", "exit", "order", "filter",
            "money_management", "robustness", "report_column", "processor",
        }
        actual = {m.value for m in BlockType}
        assert actual == expected

    def test_block_type_values(self):
        assert BlockType.SIGNAL == "signal"
        assert BlockType.EXIT == "exit"
        assert BlockType.ROBUSTNESS == "robustness"


class TestParameterSpec:
    """7. Test ParameterSpec model."""

    def test_valid_parameter(self):
        p = ParameterSpec(
            name="threshold",
            param_type="float",
            description="A threshold",
            required=True,
        )
        assert p.name == "threshold"

    def test_parameter_with_enum(self):
        p = ParameterSpec(
            name="operator",
            param_type="enum",
            description="Operator",
            required=True,
            enum_values=[">", "<", "=="],
        )
        assert p.enum_values == [">", "<", "=="]


class TestParameterSpace:
    """8. Test ParameterSpace model."""

    def test_range_mode(self):
        ps = ParameterSpace(
            mode=ParameterMode.RANGE,
            min=0.0,
            max=1.0,
            step=0.1,
        )
        assert ps.mode == ParameterMode.RANGE
        assert ps.min == 0.0

    def test_choice_mode(self):
        ps = ParameterSpace(
            mode=ParameterMode.CHOICE,
            choices=["a", "b", "c"],
        )
        assert ps.choices == ["a", "b", "c"]


class TestBlockSpec:
    """9. Test BlockSpec model."""

    def test_valid_block(self):
        b = BlockSpec(
            block_id="test_block",
            block_type=BlockType.SIGNAL,
            name="Test Block",
            description="A test block",
            input_factor_types=["numeric"],
            parameters={
                "threshold": ParameterSpec(
                    name="threshold",
                    param_type="float",
                    description="Threshold",
                    required=True,
                )
            },
            parameter_space={
                "threshold": ParameterSpace(
                    mode=ParameterMode.RANGE,
                    min=0.0,
                    max=1.0,
                    step=0.1,
                )
            },
            weight=1.0,
            enabled=True,
            required_tables=["daily_bars"],
            required_context=[ContextRequirement.NONE],
            preview_support="fully_supported",
            market_scope=["A_SHARE"],
            status="validated",
            version="0.1.0",
            source_refs=["sqx_b143"],
            evidence_level=EvidenceLevel.E2,
            production_gate="candidate",
        )
        assert b.block_id == "test_block"
        assert b.block_type == BlockType.SIGNAL

    def test_parameter_space_subset_validation(self):
        """Parameter space keys must be subset of parameters keys."""
        with pytest.raises(ValueError):
            BlockSpec(
                block_id="bad_block",
                block_type=BlockType.SIGNAL,
                name="Bad",
                description="Bad block",
                input_factor_types=["numeric"],
                parameters={
                    "threshold": ParameterSpec(
                        name="threshold",
                        param_type="float",
                        description="Threshold",
                        required=True,
                    )
                },
                parameter_space={
                    "threshold": ParameterSpace(mode=ParameterMode.RANGE, min=0, max=1, step=0.1),
                    "extra": ParameterSpace(mode=ParameterMode.CHOICE, choices=["a"]),
                },
                weight=1.0,
                enabled=True,
                required_context=[ContextRequirement.NONE],
                market_scope=["A_SHARE"],
                status="validated",
                version="0.1.0",
                source_refs=["sqx_b143"],
                evidence_level=EvidenceLevel.E2,
                production_gate="candidate",
            )
