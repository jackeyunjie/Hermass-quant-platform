"""DSL Generator - Natural Language to DSL v2 conversion.

STUB for Phase 0. Full implementation will integrate LLM in Phase 1.

This module provides:
    - Interface definition for NL -> DSL conversion
    - Template-based generation for MVP conditions
    - Validation hooks

Design constraint: No LLM-generated Python code is executed.
All outputs must validate against StrategyDSL schema before use.
"""

from __future__ import annotations

from typing import Any

from .dsl_schema import ConditionBlock, RiskConfig, StrategyDSL


# ---------------------------------------------------------------------------
# Stub Interface
# ---------------------------------------------------------------------------

class DSLGenerator:
    """Natural language strategy generator.

    Phase 0: Template-based generation only.
    Phase 1: LLM integration for flexible NL parsing.
    """

    def __init__(self) -> None:
        self._templates: dict[str, dict[str, Any]] = {}
        self._register_builtin_templates()

    def _register_builtin_templates(self) -> None:
        """Register built-in strategy templates."""
        self._templates["ma_crossover"] = {
            "name": "MA Crossover Strategy",
            "description": "Moving average golden cross entry, death cross exit",
            "entry": [
                {
                    "condition_type": "ma_golden_cross",
                    "params": {"fast_period": 5, "slow_period": 20},
                    "logic": "and",
                    "weight": 1.0,
                }
            ],
            "exit": [
                {
                    "condition_type": "ma_death_cross",
                    "params": {"fast_period": 5, "slow_period": 20},
                    "logic": "and",
                    "weight": 1.0,
                },
                {
                    "condition_type": "stop_loss_pct",
                    "params": {"value": 0.08},
                    "logic": "or",
                    "weight": 1.0,
                },
            ],
            "filters": [
                {
                    "condition_type": "limit_up_filter",
                    "params": {"allow": False},
                    "logic": "and",
                    "weight": 1.0,
                }
            ],
            "risk": {
                "risk_per_trade": 0.02,
                "max_position_pct": 0.20,
                "stop_loss_required": True,
            },
        }

    def generate_from_template(
        self,
        template_name: str,
        strategy_id: str,
        overrides: dict[str, Any] | None = None,
    ) -> StrategyDSL:
        """Generate a strategy from a named template.

        Args:
            template_name: Name of registered template.
            strategy_id: Unique strategy identifier.
            overrides: Optional field overrides.

        Returns:
            Validated StrategyDSL instance.

        Raises:
            KeyError: If template_name is not registered.
        """
        if template_name not in self._templates:
            raise KeyError(
                f"Unknown template: '{template_name}'. "
                f"Available: {list(self._templates.keys())}"
            )

        template = self._templates[template_name].copy()
        template["strategy_id"] = strategy_id
        template["schema_version"] = "strategy_dsl_v2"

        if overrides:
            template.update(overrides)

        return StrategyDSL.model_validate(template)

    def generate_from_natural_language(
        self,
        natural_language: str,
        strategy_id: str,
    ) -> StrategyDSL:
        """Generate a strategy from natural language input.

        STUB for Phase 0. In Phase 1, this will:
            1. Parse NL with LLM
            2. Map to condition types
            3. Fill parameters
            4. Validate output

        Args:
            natural_language: User's strategy description in Chinese.
            strategy_id: Unique strategy identifier.

        Returns:
            Validated StrategyDSL instance.

        Raises:
            NotImplementedError: In Phase 0, always raises.
        """
        raise NotImplementedError(
            "NL generation is not implemented in Phase 0. "
            "Use generate_from_template() or construct StrategyDSL directly. "
            f"Input was: {natural_language[:100]}..."
        )

    def list_templates(self) -> list[str]:
        """List available template names."""
        return list(self._templates.keys())


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def create_ma_crossover_strategy(
    strategy_id: str,
    fast_period: int = 5,
    slow_period: int = 20,
    stop_loss: float = 0.08,
    max_position: float = 0.20,
    name: str | None = None,
) -> StrategyDSL:
    """Create a simple MA crossover strategy.

    Example:
        >>> dsl = create_ma_crossover_strategy("ma_5_20_v1")
        >>> print(dsl.name)
        'MA5上穿MA20策略'
    """
    return StrategyDSL(
        strategy_id=strategy_id,
        name=name or f"MA{fast_period}上穿MA{slow_period}策略",
        description=f"均线金叉买入，死叉卖出，止损{stop_loss*100:.0f}%",
        entry=[
            ConditionBlock(
                condition_type="ma_golden_cross",
                params={"fast_period": fast_period, "slow_period": slow_period},
            )
        ],
        exit=[
            ConditionBlock(
                condition_type="ma_death_cross",
                params={"fast_period": fast_period, "slow_period": slow_period},
                logic="and",
            ),
            ConditionBlock(
                condition_type="stop_loss_pct",
                params={"value": stop_loss},
                logic="or",
            ),
        ],
        filters=[
            ConditionBlock(
                condition_type="limit_up_filter",
                params={"allow": False},
            )
        ],
        risk=RiskConfig(
            risk_per_trade=0.02,
            max_position_pct=max_position,
        ),
    )
