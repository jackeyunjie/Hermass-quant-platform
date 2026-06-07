"""Tests for condition_registry.py - Condition type registration and validation."""

from __future__ import annotations

import pytest

from hermass_platform.strategy_lab.condition_registry import (
    ConditionCategory,
    ConditionRegistry,
    ConditionSpec,
    ParamSchema,
    TranslatorDialect,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_registry() -> ConditionRegistry:
    return ConditionRegistry()


@pytest.fixture
def default_registry() -> ConditionRegistry:
    return ConditionRegistry.default()


@pytest.fixture
def sample_condition() -> ConditionSpec:
    return ConditionSpec(
        condition_type="test_condition",
        category=ConditionCategory.ENTRY,
        params=[
            ParamSchema(
                name="threshold",
                param_type="number",
                required=True,
                constraints={"minimum": 0.0, "maximum": 1.0},
            ),
            ParamSchema(
                name="optional_flag",
                param_type="boolean",
                required=False,
                default=False,
            ),
        ],
        translator=TranslatorDialect.BOTH,
        description="A test condition",
    )


# ---------------------------------------------------------------------------
# Registry Tests
# ---------------------------------------------------------------------------

class TestConditionRegistry:
    def test_register_and_get(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        retrieved = empty_registry.get("test_condition")
        assert retrieved.condition_type == "test_condition"
        assert retrieved.category == ConditionCategory.ENTRY

    def test_register_duplicate(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        with pytest.raises(ValueError, match="already registered"):
            empty_registry.register(sample_condition)

    def test_register_empty_type(self, empty_registry: ConditionRegistry) -> None:
        spec = ConditionSpec(
            condition_type="",
            category=ConditionCategory.ENTRY,
            params=[],
            translator=TranslatorDialect.BOTH,
        )
        with pytest.raises(ValueError, match="must not be empty"):
            empty_registry.register(spec)

    def test_get_unknown(self, empty_registry: ConditionRegistry) -> None:
        with pytest.raises(KeyError, match="Unknown condition type"):
            empty_registry.get("unknown")

    def test_has(self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec) -> None:
        assert empty_registry.has("test_condition") is False
        empty_registry.register(sample_condition)
        assert empty_registry.has("test_condition") is True

    def test_list_all(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        assert len(empty_registry.list_all()) == 0
        empty_registry.register(sample_condition)
        assert len(empty_registry.list_all()) == 1

    def test_list_by_category(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        entry_conds = empty_registry.list_by_category(ConditionCategory.ENTRY)
        assert len(entry_conds) == 1
        exit_conds = empty_registry.list_by_category(ConditionCategory.EXIT)
        assert len(exit_conds) == 0

    def test_list_by_translator(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        duckdb_conds = empty_registry.list_by_translator(TranslatorDialect.DUCKDB)
        assert len(duckdb_conds) == 1
        polars_conds = empty_registry.list_by_translator(TranslatorDialect.POLARS)
        assert len(polars_conds) == 1

    def test_register_many(self, empty_registry: ConditionRegistry) -> None:
        specs = [
            ConditionSpec(
                condition_type="cond_a",
                category=ConditionCategory.ENTRY,
                params=[],
                translator=TranslatorDialect.DUCKDB,
            ),
            ConditionSpec(
                condition_type="cond_b",
                category=ConditionCategory.EXIT,
                params=[],
                translator=TranslatorDialect.POLARS,
            ),
        ]
        empty_registry.register_many(specs)
        assert len(empty_registry.list_all()) == 2


# ---------------------------------------------------------------------------
# Default Registry Tests
# ---------------------------------------------------------------------------

class TestDefaultRegistry:
    def test_all_mvp_conditions_registered(self, default_registry: ConditionRegistry) -> None:
        mvp_types = [
            "ma_golden_cross",
            "ma_death_cross",
            "price_cross_ma",
            "state_hex_in",
            "state_ef_count",
            "volume_ratio",
            "industry_include",
            "industry_exclude",
            "stop_loss_pct",
            "take_profit_pct",
            "limit_up_filter",
        ]
        for ct in mvp_types:
            assert default_registry.has(ct), f"Missing condition type: {ct}"

    def test_mvp_condition_count(self, default_registry: ConditionRegistry) -> None:
        all_conds = default_registry.list_all()
        assert len(all_conds) == 11

    def test_condition_categories(self, default_registry: ConditionRegistry) -> None:
        entry_conds = default_registry.list_by_category(ConditionCategory.ENTRY)
        exit_conds = default_registry.list_by_category(ConditionCategory.EXIT)
        filter_conds = default_registry.list_by_category(ConditionCategory.FILTER)

        assert len(entry_conds) == 5  # ma_golden_cross, price_cross_ma, state_hex_in, state_ef_count, volume_ratio
        assert len(exit_conds) == 3   # ma_death_cross, stop_loss_pct, take_profit_pct
        assert len(filter_conds) == 3  # industry_include, industry_exclude, limit_up_filter

    def test_get_ma_golden_cross(self, default_registry: ConditionRegistry) -> None:
        spec = default_registry.get("ma_golden_cross")
        assert spec.condition_type == "ma_golden_cross"
        assert spec.category == ConditionCategory.ENTRY
        assert spec.translator == TranslatorDialect.BOTH
        assert len(spec.params) == 2

        fast_param = spec.get_param("fast_period")
        assert fast_param is not None
        assert fast_param.param_type == "integer"
        assert fast_param.constraints["minimum"] == 1
        assert fast_param.constraints["maximum"] == 252


# ---------------------------------------------------------------------------
# Parameter Validation Tests
# ---------------------------------------------------------------------------

class TestParamValidation:
    def test_valid_params(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        result = empty_registry.validate_params("test_condition", {"threshold": 0.5})
        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_required_param(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        result = empty_registry.validate_params("test_condition", {})
        assert result.valid is False
        assert any("Missing required parameter" in e for e in result.errors)

    def test_wrong_type(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        result = empty_registry.validate_params(
            "test_condition", {"threshold": "not_a_number"}
        )
        assert result.valid is False
        assert any("expects type 'number'" in e for e in result.errors)

    def test_constraint_violation_min(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        result = empty_registry.validate_params(
            "test_condition", {"threshold": -0.1}
        )
        assert result.valid is False
        assert any("below minimum" in e for e in result.errors)

    def test_constraint_violation_max(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        result = empty_registry.validate_params(
            "test_condition", {"threshold": 1.5}
        )
        assert result.valid is False
        assert any("exceeds maximum" in e for e in result.errors)

    def test_unknown_param_warning(
        self, empty_registry: ConditionRegistry, sample_condition: ConditionSpec
    ) -> None:
        empty_registry.register(sample_condition)
        result = empty_registry.validate_params(
            "test_condition", {"threshold": 0.5, "unknown_param": "value"}
        )
        assert result.valid is True  # Unknown params are warnings, not errors
        assert any("Unknown parameter" in w for w in result.warnings)

    def test_optional_param(self, empty_registry: ConditionRegistry) -> None:
        spec = ConditionSpec(
            condition_type="opt_test",
            category=ConditionCategory.ENTRY,
            params=[
                ParamSchema(
                    name="required_val",
                    param_type="integer",
                    required=True,
                ),
                ParamSchema(
                    name="optional_val",
                    param_type="integer",
                    required=False,
                    default=10,
                ),
            ],
            translator=TranslatorDialect.BOTH,
        )
        empty_registry.register(spec)

        # Without optional
        result = empty_registry.validate_params("opt_test", {"required_val": 5})
        assert result.valid is True

        # With optional
        result = empty_registry.validate_params(
            "opt_test", {"required_val": 5, "optional_val": 20}
        )
        assert result.valid is True

    def test_unknown_condition_type(self, empty_registry: ConditionRegistry) -> None:
        result = empty_registry.validate_params("unknown", {})
        assert result.valid is False
        assert any("Unknown condition type" in e for e in result.errors)


# ---------------------------------------------------------------------------
# ParamSchema Tests
# ---------------------------------------------------------------------------

class TestParamSchema:
    def test_to_json_schema(self) -> None:
        param = ParamSchema(
            name="test",
            param_type="number",
            description="A test parameter",
            constraints={"minimum": 0, "maximum": 100},
        )
        schema = param.to_json_schema()
        assert schema["type"] == "number"
        assert schema["description"] == "A test parameter"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 100

    def test_get_param(self, sample_condition: ConditionSpec) -> None:
        param = sample_condition.get_param("threshold")
        assert param is not None
        assert param.name == "threshold"

        missing = sample_condition.get_param("nonexistent")
        assert missing is None

    def test_get_required_params(self, sample_condition: ConditionSpec) -> None:
        required = sample_condition.get_required_params()
        assert len(required) == 1
        assert required[0].name == "threshold"


# ---------------------------------------------------------------------------
# ConditionSpec Tests
# ---------------------------------------------------------------------------

class TestConditionSpec:
    def test_spec_creation(self) -> None:
        spec = ConditionSpec(
            condition_type="my_cond",
            category=ConditionCategory.FILTER,
            params=[],
            translator=TranslatorDialect.DUCKDB,
            description="My condition",
            examples=[{"param1": 1}],
        )
        assert spec.description == "My condition"
        assert len(spec.examples) == 1

    def test_spec_defaults(self) -> None:
        spec = ConditionSpec(
            condition_type="minimal",
            category=ConditionCategory.ENTRY,
            params=[],
            translator=TranslatorDialect.BOTH,
        )
        assert spec.description == ""
        assert spec.examples == []
