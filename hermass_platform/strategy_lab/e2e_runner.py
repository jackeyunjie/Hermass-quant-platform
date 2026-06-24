"""E2E Runner - MVP end-to-end strategy execution.

This module provides the unified entry point for the complete strategy lifecycle:
    NL -> DSL -> Validation -> Red Line -> Preview -> Light Backtest -> Audit

Design constraints:
    - No LLM involvement. Template/rule-based NL parsing only.
    - All outputs validate against StrategyDSL schema.
    - Failed paths must still write audit records.
    - Light backtest is stubbed and explicitly marked as such.
"""

from __future__ import annotations

import re
import hashlib
import json
import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from .api_models import (
    BacktestMetrics,
    BacktestResponse,
    PreviewResponse,
    ValidateStrategyResponse,
    ValidationErrorItem,
)
from .audit import StrategyAuditLogger
from .backtest_adapter import run_dsl_backtest
from .backtest_evidence import build_trade_event_evidence, build_trade_records
from .dsl_schema import ConditionBlock, RiskConfig, StrategyDSL
from .dsl_validator import ValidationLevel, validate_dsl
from .preview_service import PreviewConfig, PreviewService
from .storage import StrategyLabStorage


# ---------------------------------------------------------------------------
# Result Model
# ---------------------------------------------------------------------------

class MvpE2EResult(BaseModel):
    """端到端执行结果。"""

    model_config = {"extra": "forbid"}

    trace_id: str = Field(..., description="全局追踪 ID")
    strategy_id: str = Field(..., description="策略标识")
    natural_language: str = Field(..., description="原始中文输入")

    # DSL 生成
    dsl: StrategyDSL | None = Field(default=None, description="生成的 DSL")
    generation_errors: list[str] = Field(default_factory=list)

    # 校验
    validation: ValidateStrategyResponse | None = Field(default=None)
    red_line_result: dict[str, Any] = Field(default_factory=dict)

    # Preview
    preview: PreviewResponse | None = Field(default=None)

    # Light Backtest
    backtest: BacktestResponse | None = Field(default=None)
    backtest_mode: Literal["light_stub", "light_real_v1", "light_mock", "full"] = Field(
        default="light_stub",
        description="回测执行模式",
    )

    # Audit
    audit_records: list[dict[str, Any]] = Field(default_factory=list)

    # 问题归档
    problem_items: list[dict[str, Any]] = Field(default_factory=list)

    # 性能剖析（可选）
    stage_timings: dict[str, float] = Field(
        default_factory=dict,
        description="各阶段耗时（秒），仅在 profile=True 时填充",
    )

    # 整体状态
    status: Literal["success", "partial", "failed"] = Field(default="failed")
    stage_reached: Literal[
        "generation", "validation", "preview", "backtest", "complete"
    ] = Field(default="generation", description="执行到的最远距离")


# ---------------------------------------------------------------------------
# NL -> DSL Parser (MVP rule-based, no LLM)
# ---------------------------------------------------------------------------

class NLToDSLParser:
    """Rule-based Chinese NL to StrategyDSL parser.

    Supports only the phrases defined in MVP_E2E_SAMPLES_2026_06_08.md Section 5.
    """

    def __init__(self) -> None:
        pass

    def parse(self, natural_language: str, strategy_id: str) -> StrategyDSL:
        """Parse Chinese natural language to StrategyDSL.

        Raises:
            ValueError: If input cannot be parsed or missing mandatory conditions.
        """
        nl = natural_language.strip()

        # Extract entry conditions (支持组合条件，用 "且" / "," 分隔)
        entry: list[ConditionBlock] = []

        # MA golden cross: MA{N}上穿MA{M}
        for ma_cross_match in re.finditer(r"MA(\d+)上穿MA(\d+)", nl):
            fast = int(ma_cross_match.group(1))
            slow = int(ma_cross_match.group(2))
            entry.append(
                ConditionBlock(
                    condition_type="ma_golden_cross",
                    params={"fast_period": fast, "slow_period": slow},
                )
            )

        # 均线多头排列: MA{N},MA{M},MA{P}均线顺序排列多头
        # 例如: "144,169,200均线顺序排列多头"
        ma_arrange_match = re.search(r"MA?(\d+)[,，]MA?(\d+)[,，]MA?(\d+).*?(?:均线)?顺序排列多头", nl)
        if ma_arrange_match:
            # 将多头排列转换为多个价格突破条件
            # 简化为: 价格上穿最短周期均线
            short_period = int(ma_arrange_match.group(1))
            entry.append(
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": short_period, "direction": "above"},
                )
            )

        # 价格回调/回测后上涨: 价格回测到MA{N}均线再次上涨
        # 例如: "价格回测到169均线再次上涨"
        pullback_match = re.search(r"价格回[测撤]到MA?(\d+).*?再次上涨", nl)
        if pullback_match:
            ma_period = int(pullback_match.group(1))
            entry.append(
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": ma_period, "direction": "above"},
                )
            )

        # 均线支撑: 价格回踩MA{N}均线支撑
        support_match = re.search(r"价格回踩MA?(\d+).*?支撑", nl)
        if support_match:
            ma_period = int(support_match.group(1))
            entry.append(
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": ma_period, "direction": "above"},
                )
            )

        # State hex in: D1状态属于...
        state_match = re.search(r"(MN1|W1|D1)状态属于([0-9a-zA-Z_、或]+)", nl)
        if state_match:
            timeframe = state_match.group(1)
            values_str = state_match.group(2)
            values = [v.strip() for v in re.split(r"[、或]", values_str) if v.strip()]
            entry.append(
                ConditionBlock(
                    condition_type="state_hex_in",
                    params={"timeframe": timeframe, "values": values},
                )
            )

        # Volume ratio: 成交量放大到{N}日均量{R}倍以上
        vol_match = re.search(r"成交量放大到(\d+)日均量([\d.]+)倍以上", nl)
        if vol_match:
            lookback = int(vol_match.group(1))
            ratio = float(vol_match.group(2))
            entry.append(
                ConditionBlock(
                    condition_type="volume_ratio",
                    params={"lookback": lookback, "operator": ">", "value": ratio},
                )
            )

        # State EF count: {TF}状态EF数量{op}{V}
        ef_match = re.search(r"状态EF数量(不少于|不低于|至少|大于等于|>=|<=|>|<|==|)(\d+)", nl)
        if ef_match:
            op_text = ef_match.group(1)
            op = _normalize_operator(op_text)
            value = int(ef_match.group(2))
            entry.append(
                ConditionBlock(
                    condition_type="state_ef_count",
                    params={"operator": op, "value": value},
                )
            )

        # Price cross MA (above): 上穿MA{N} (仅当不是 MA交叉的一部分时)
        # 使用 finditer 获取所有匹配，排除已作为 ma_golden_cross 处理过的
        ma_cross_ranges = [
            (m.start(), m.end())
            for m in re.finditer(r"MA\d+上穿MA\d+", nl)
        ]
        for price_above_match in re.finditer(r"上穿MA(\d+)", nl):
            # 检查是否落在任何 ma_cross_match 范围内
            pos = price_above_match.start()
            if any(start <= pos < end for start, end in ma_cross_ranges):
                continue
            ma_period = int(price_above_match.group(1))
            entry.append(
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": ma_period, "direction": "above"},
                )
            )

        if not entry:
            raise ValueError(f"无法从输入中提取任何 entry 条件: {nl[:50]}...")

        # Extract exit conditions
        exit: list[ConditionBlock] = []

        # MA death cross: MA{N}下穿MA{M}
        ma_death_match = re.search(r"MA(\d+)下穿MA(\d+)", nl)
        if ma_death_match:
            fast = int(ma_death_match.group(1))
            slow = int(ma_death_match.group(2))
            exit.append(
                ConditionBlock(
                    condition_type="ma_death_cross",
                    params={"fast_period": fast, "slow_period": slow},
                )
            )

        # Price cross MA (below): 跌破MA{N} / 均线{N}出场 / MA{N}出场
        price_below_match = re.search(r"跌破MA(\d+)", nl)
        if price_below_match:
            ma_period = int(price_below_match.group(1))
            exit.append(
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": ma_period, "direction": "below"},
                    logic="or",
                )
            )

        # 均线出场: MA{N}出场 / 均线{N}出场
        ma_exit_match = re.search(r"(?:MA|均线)(\d+).*?出场", nl)
        if ma_exit_match:
            ma_period = int(ma_exit_match.group(1))
            exit.append(
                ConditionBlock(
                    condition_type="price_cross_ma",
                    params={"timeframe": "D1", "ma_period": ma_period, "direction": "below"},
                    logic="or",
                )
            )

        # Stop loss: 止损{P}%
        stop_loss_match = re.search(r"止损([\d.]+)%", nl)
        if stop_loss_match:
            value = float(stop_loss_match.group(1)) / 100.0
            exit.append(
                ConditionBlock(
                    condition_type="stop_loss_pct",
                    params={"value": value},
                    logic="or",
                )
            )

        # Take profit: 止盈{P}%
        take_profit_match = re.search(r"止盈([\d.]+)%", nl)
        if take_profit_match:
            value = float(take_profit_match.group(1)) / 100.0
            exit.append(
                ConditionBlock(
                    condition_type="take_profit_pct",
                    params={"value": value},
                    logic="or",
                )
            )

        # Filters (default: exclude limit-up)
        filters: list[ConditionBlock] = []
        if "排除涨停" in nl or "排除涨停股票" in nl:
            filters.append(
                ConditionBlock(
                    condition_type="limit_up_filter",
                    params={"allow": False},
                )
            )
        elif "允许涨停" in nl:
            filters.append(
                ConditionBlock(
                    condition_type="limit_up_filter",
                    params={"allow": True},
                )
            )
        else:
            # MVP default: exclude limit-up
            filters.append(
                ConditionBlock(
                    condition_type="limit_up_filter",
                    params={"allow": False},
                )
            )

        # Industry include: 行业包含{行业1},{行业2}
        industry_include_match = re.search(r"行业包含([\u4e00-\u9fa5a-zA-Z,、]+)", nl)
        if industry_include_match:
            values_str = industry_include_match.group(1)
            values = [v.strip() for v in re.split(r"[,，、]", values_str) if v.strip()]
            if values:
                filters.append(
                    ConditionBlock(
                        condition_type="industry_include",
                        params={"values": values},
                    )
                )

        # Industry exclude: 行业排除{行业1},{行业2}
        industry_exclude_match = re.search(r"行业排除([\u4e00-\u9fa5a-zA-Z,、]+)", nl)
        if industry_exclude_match:
            values_str = industry_exclude_match.group(1)
            values = [v.strip() for v in re.split(r"[,，、]", values_str) if v.strip()]
            if values:
                filters.append(
                    ConditionBlock(
                        condition_type="industry_exclude",
                        params={"values": values},
                    )
                )

        # Risk config defaults
        max_position = 0.20
        position_match = re.search(r"仓位([\d.]+)%", nl)
        if position_match:
            max_position = float(position_match.group(1)) / 100.0

        risk_per_trade = 0.02
        risk_match = re.search(r"单笔风险([\d.]+)%", nl)
        if risk_match:
            risk_per_trade = float(risk_match.group(1)) / 100.0

        # 统一使用 model_construct 绕过 Pydantic 约束，让红线检查来处理
        risk = RiskConfig.model_construct(
            risk_per_trade=risk_per_trade,
            max_position_pct=max_position,
            stop_loss_required=True,
        )

        return StrategyDSL(
            strategy_id=strategy_id,
            name=self._generate_name(nl),
            description=nl,
            entry=entry,
            exit=exit,
            filters=filters,
            risk=risk,
        )

    @staticmethod
    def _generate_name(nl: str) -> str:
        """Generate a short strategy name from NL."""
        if "MA" in nl and "上穿" in nl:
            return "MA交叉策略"
        if "状态" in nl and "成交量" in nl:
            return "状态成交量策略"
        if "状态" in nl and "EF" in nl:
            return "MA状态组合策略"
        return "量化策略"


# ---------------------------------------------------------------------------
# E2E Runner
# ---------------------------------------------------------------------------

def run_mvp_e2e_sample(
    natural_language: str,
    strategy_id: str,
    *,
    trace_id: str,
    audit_db_path: str,
    storage_db_path: str,
    preview_data_source: Literal["mock", "duckdb"] = "mock",
    preview_duckdb_path: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    foundation_db: str | None = None,
    state_cube_db: str | None = None,
    universe: list[str] | None = None,
    profile: bool = False,
) -> MvpE2EResult:
    """执行单个 MVP E2E 样例。

    执行顺序：
        1. NL -> DSL（模板/规则生成，无 LLM）
        2. Schema/Pydantic 校验
        3. 红线检查
        4. Preview（仅红线通过时）
        5. Light Backtest（仅红线通过时）
        6. Audit 记录
        7. 问题归档（如有）

    失败链路也必须写 audit。例如缺少止损时，写入 generation + validation，
    不执行 preview/backtest。
    """
    result = MvpE2EResult(
        trace_id=trace_id,
        strategy_id=strategy_id,
        natural_language=natural_language,
    )
    timings: dict[str, float] = {}
    total_start = time.perf_counter()

    def _tick(label: str) -> None:
        if profile:
            timings[label] = time.perf_counter() - total_start

    audit_logger = StrategyAuditLogger(audit_db_path)
    audit_logger.init_schema()
    storage = StrategyLabStorage(storage_db_path)
    storage.init_schema()

    parser = NLToDSLParser()

    stage_start = time.perf_counter()

    # ------------------------------------------------------------------
    # Step 1: Generation
    # ------------------------------------------------------------------
    try:
        dsl = parser.parse(natural_language, strategy_id)
        result.dsl = dsl
    except Exception as exc:
        result.generation_errors.append(str(exc))
        result.status = "failed"
        result.stage_reached = "generation"
        _log_generation(audit_logger, trace_id, strategy_id, natural_language, None, result.generation_errors)
        result.audit_records = _load_audit_records(audit_logger, trace_id)
        return result

    _log_generation(audit_logger, trace_id, strategy_id, natural_language, dsl, [])
    timings["generation"] = time.perf_counter() - stage_start
    stage_start = time.perf_counter()

    # ------------------------------------------------------------------
    # Step 2: Validation
    # ------------------------------------------------------------------
    validation = validate_dsl(dsl)
    result.validation = _to_validate_response(validation, trace_id)
    result.red_line_result = {
        "passed": not validation.has_red_line_violation,
        "triggered_rules": [
            e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
        ],
    }

    _log_validation(
        audit_logger, trace_id, strategy_id, dsl, validation, result.red_line_result
    )

    if not validation.passed:
        result.status = "failed"
        result.stage_reached = "validation"
        _archive_problems(result, validation)
        result.audit_records = _load_audit_records(audit_logger, trace_id)
        if profile:
            result.stage_timings = timings
        return result

    timings["validation"] = time.perf_counter() - stage_start
    stage_start = time.perf_counter()

    storage.save_strategy_version(
        strategy_id=strategy_id,
        dsl=dsl.to_dict(),
        trace_id=trace_id,
        input_hash=_hash_payload({"natural_language": natural_language}),
        output_hash=_hash_payload(dsl.to_dict()),
    )
    timings["storage_save_version"] = time.perf_counter() - stage_start
    stage_start = time.perf_counter()

    # ------------------------------------------------------------------
    # Step 3: Preview
    # ------------------------------------------------------------------
    preview_service = PreviewService(
        PreviewConfig(duckdb_path=preview_duckdb_path)
    )
    try:
        preview = preview_service.preview(
            dsl, data_source=preview_data_source, trace_id=trace_id
        )
        result.preview = preview
    except Exception as exc:
        result.preview = None
        result.problem_items.append(
            {
                "sample_id": strategy_id,
                "category": "implementation",
                "stage": "preview",
                "summary": f"Preview execution failed: {exc}",
                "evidence": {"error": str(exc)},
                "owner": "codex",
                "next_action": "Investigate preview service error",
            }
        )

    _log_preview(audit_logger, trace_id, strategy_id, dsl, result.preview, result.red_line_result)
    timings["preview"] = time.perf_counter() - stage_start
    stage_start = time.perf_counter()

    if result.preview is None or result.preview.overall.overall_status == "failed":
        result.status = "failed"
        result.stage_reached = "preview"
        result.audit_records = _load_audit_records(audit_logger, trace_id)
        if profile:
            result.stage_timings = timings
        return result

    # ------------------------------------------------------------------
    # Step 4: Light Backtest
    # ------------------------------------------------------------------
    bt_start = start_date or "2023-01-01"
    bt_end = end_date or "2024-12-31"

    from pathlib import Path as _Path

    _foundation_db = _Path(foundation_db) if foundation_db else None

    try:
        bt_result = run_dsl_backtest(
            dsl,
            bt_start,
            bt_end,
            foundation_db=_foundation_db,
            state_cube_db=_Path(state_cube_db) if state_cube_db else None,
            universe=universe,
            trace_id=trace_id,
        )
        metrics = BacktestMetrics(
            total_return=bt_result.metrics.get("total_return"),
            annual_return=bt_result.metrics.get("annual_return"),
            sharpe_ratio=bt_result.metrics.get("sharpe_ratio"),
            max_drawdown=bt_result.metrics.get("max_drawdown"),
            profit_factor=bt_result.metrics.get("profit_factor"),
            trade_count=bt_result.metrics.get("trade_count"),
            total_trades=bt_result.metrics.get("total_trades", bt_result.metrics.get("trade_count")),
            win_rate=bt_result.metrics.get("win_rate"),
            avg_holding_days=bt_result.metrics.get("avg_holding_days"),
            turnover=bt_result.metrics.get("turnover"),
            cost_total=bt_result.metrics.get("cost_total"),
        )
        bt_status: Literal["success", "partial", "failed"] = (
            "failed" if bt_result.status == "failed"
            else "partial" if bt_result.risk_flags
            else "success"
        )
        bt_mode = bt_result.mode or "light_stub"

        result.backtest = BacktestResponse(
            trace_id=trace_id,
            status=bt_status,
            mode=bt_mode,
            metrics=metrics,
            risk_flags=bt_result.risk_flags,
            warnings=bt_result.warnings,
            trade_count=bt_result.metrics.get("trade_count"),
            daily_curve=bt_result.daily_curve[:100] if bt_result.daily_curve else [],
            trades=bt_result.trades[:100] if bt_result.trades else [],
            data_version=bt_result.data_version,
            elapsed_seconds=bt_result.elapsed_seconds,
            errors=bt_result.risk_flags + bt_result.warnings,
            daily_curve_total_count=len(bt_result.daily_curve) if bt_result.daily_curve else 0,
            trades_truncated=len(bt_result.trades) > 100 if bt_result.trades else False,
        )
        result.backtest_mode = bt_mode
        timings["backtest_engine"] = time.perf_counter() - stage_start
        stage_start = time.perf_counter()

        # Persist backtest result
        metrics_dict = dict(bt_result.metrics)
        metrics_dict["_mode"] = bt_mode
        if bt_result.warnings:
            metrics_dict["data_quality_warnings"] = bt_result.warnings
        storage.save_backtest_result(
            strategy_id=strategy_id,
            trace_id=trace_id,
            status=bt_status,
            metrics=metrics_dict,
            dsl_snapshot=dsl.to_dict(),
        )
        timings["backtest_save_result"] = time.perf_counter() - stage_start
        stage_start = time.perf_counter()

        # Persist trade records and events (real mode only)
        persist_timings: dict[str, float] = {}
        if bt_mode == "light_real_v1" and bt_result.trades:
            _persist_trades_and_events(
                storage=storage,
                bt_result=bt_result,
                dsl=dsl,
                trace_id=trace_id,
                strategy_id=strategy_id,
                timings=persist_timings,
            )
        timings["backtest_persist_trades"] = time.perf_counter() - stage_start
        timings.update(persist_timings)
    except Exception as exc:
        result.backtest = BacktestResponse(
            trace_id=trace_id,
            status="failed",
            mode="light_stub" if not foundation_db else "light_real_v1",
            errors=[f"Backtest execution failed: {exc}"],
        )
        result.backtest_mode = "light_stub" if not foundation_db else "light_real_v1"
        result.problem_items.append(
            {
                "sample_id": strategy_id,
                "category": "implementation",
                "stage": "backtest",
                "summary": f"Backtest execution failed: {exc}",
                "evidence": {"error": str(exc)},
                "owner": "codex",
                "next_action": "Investigate backtest adapter error",
            }
        )
        _log_backtest(audit_logger, trace_id, strategy_id, dsl, result.backtest, result.red_line_result)
        result.status = "failed"
        result.stage_reached = "backtest"
        result.audit_records = _load_audit_records(audit_logger, trace_id)
        return result

    _log_backtest(audit_logger, trace_id, strategy_id, dsl, result.backtest, result.red_line_result)

    # ------------------------------------------------------------------
    # Step 5: Finalize
    # ------------------------------------------------------------------
    result.status = "success" if not result.backtest.risk_flags else "partial"
    result.stage_reached = "complete"

    # Load audit records for response
    result.audit_records = _load_audit_records(audit_logger, trace_id)
    stage_start = time.perf_counter()
    audit_logger.close()
    timings["audit_load_close"] = time.perf_counter() - stage_start
    timings["total"] = time.perf_counter() - total_start
    if profile:
        result.stage_timings = timings

    return result


# ---------------------------------------------------------------------------
# Trade Persistence
# ---------------------------------------------------------------------------

def _persist_trades_and_events(
    *,
    storage: StrategyLabStorage,
    bt_result: Any,
    dsl: StrategyDSL,
    trace_id: str,
    strategy_id: str,
    timings: dict[str, float] | None = None,
) -> None:
    """Persist trade records and event evidence for real light backtest.

    Uses the completed signal_frame from the engine (via BacktestResult.signal_frame)
    to build trade records and event evidence. Falls back to the trades list
    when signal_frame is not available (e.g., stub or older backtest results).
    """
    def _tick(label: str, start: float) -> float:
        if timings is not None:
            timings[label] = time.perf_counter() - start
        return time.perf_counter()

    signal_frame = getattr(bt_result, "signal_frame", None)

    if signal_frame is not None and hasattr(signal_frame, "is_empty"):
        if not signal_frame.is_empty():
            t0 = time.perf_counter()
            trade_records = build_trade_records(signal_frame, dsl, trace_id)
            t1 = _tick("build_trade_records", t0)
            storage.save_trade_records_batch(trade_records)
            t2 = _tick("save_trade_records_batch", t1)

            events = build_trade_event_evidence(signal_frame, dsl, trace_id)
            t3 = _tick("build_trade_events", t2)
            storage.save_trade_event_evidence_batch(events)
            _tick("save_trade_events_batch", t3)
            return

    # Fallback: persist trades from bt_result.trades list (light_stub or legacy)
    if bt_result.trades:
        t0 = time.perf_counter()
        fallback_records: list[dict[str, Any]] = []
        for trade in bt_result.trades:
            trade_id = trade.get("trade_id", "")
            if not trade_id:
                continue
            fallback_records.append({
                "trade_id": trade_id,
                "strategy_id": strategy_id,
                "trace_id": trace_id,
                "symbol": trade.get("symbol", ""),
                "side": trade.get("side", "long"),
                "status": "closed" if trade.get("exit_date") else "open",
                "entry_time": trade.get("entry_date", ""),
                "entry_price": trade.get("entry_price"),
                "exit_time": trade.get("exit_date"),
                "exit_price": trade.get("exit_price"),
                "quantity": trade.get("shares"),
                "pnl": trade.get("pnl"),
                "pnl_pct": trade.get("pnl_pct"),
            })
        t1 = _tick("build_fallback_trade_records", t0)
        storage.save_trade_records_batch(fallback_records)
        _tick("save_fallback_trade_records_batch", t1)


# ---------------------------------------------------------------------------
# Audit Helpers
# ---------------------------------------------------------------------------

def _log_generation(
    logger: StrategyAuditLogger,
    trace_id: str,
    strategy_id: str,
    natural_language: str,
    dsl: StrategyDSL | None,
    errors: list[str],
) -> None:
    input_payload = {"natural_language": natural_language}
    output_payload = dsl.to_dict() if dsl else {"errors": errors}
    logger.log_generation(
        trace_id=trace_id,
        strategy_id=strategy_id,
        dsl_version="strategy_dsl_v2",
        input_payload=input_payload,
        output_payload=output_payload,
        red_line_result=None,
    )


def _log_validation(
    logger: StrategyAuditLogger,
    trace_id: str,
    strategy_id: str,
    dsl: StrategyDSL,
    validation: Any,
    red_line_result: dict[str, Any],
) -> None:
    input_payload = dsl.to_dict()
    output_payload = {
        "passed": validation.passed,
        "level": validation.level.value,
        "error_count": validation.error_count,
        "warning_count": validation.warning_count,
    }
    logger.log_validation(
        trace_id=trace_id,
        strategy_id=strategy_id,
        dsl_version="strategy_dsl_v2",
        input_payload=input_payload,
        output_payload=output_payload,
        red_line_result=red_line_result,
    )


def _log_preview(
    logger: StrategyAuditLogger,
    trace_id: str,
    strategy_id: str,
    dsl: StrategyDSL,
    preview: PreviewResponse | None,
    red_line_result: dict[str, Any] | None = None,
) -> None:
    input_payload = dsl.to_dict()
    output_payload = preview.model_dump(mode="json") if preview else {}
    logger.log_preview(
        trace_id=trace_id,
        strategy_id=strategy_id,
        dsl_version="strategy_dsl_v2",
        input_payload=input_payload,
        output_payload=output_payload,
        red_line_result=red_line_result or {},
    )


def _log_backtest(
    logger: StrategyAuditLogger,
    trace_id: str,
    strategy_id: str,
    dsl: StrategyDSL,
    backtest: BacktestResponse | None,
    red_line_result: dict[str, Any] | None = None,
) -> None:
    input_payload = dsl.to_dict()
    output_payload = backtest.model_dump(mode="json") if backtest else {}
    logger.log_backtest(
        trace_id=trace_id,
        strategy_id=strategy_id,
        dsl_version="strategy_dsl_v2",
        input_payload=input_payload,
        output_payload=output_payload,
        red_line_result=red_line_result or {},
    )


# ---------------------------------------------------------------------------
# Conversion Helpers
# ---------------------------------------------------------------------------

def _to_validate_response(validation: Any, trace_id: str) -> ValidateStrategyResponse:
    """Convert internal ValidationResult to API response model."""
    return ValidateStrategyResponse(
        trace_id=trace_id,
        passed=validation.passed,
        level=validation.level.value,
        errors=[
            ValidationErrorItem(
                level=e.level.value,
                code=e.code,
                message=e.message,
                path=e.path,
            )
            for e in validation.errors
        ],
        warnings=[
            ValidationErrorItem(
                level=w.level.value,
                code=w.code,
                message=w.message,
                path=w.path,
            )
            for w in validation.warnings
        ],
        red_line_result={
            "passed": not validation.has_red_line_violation,
            "triggered_rules": [
                e.code for e in validation.errors if e.level == ValidationLevel.RED_LINE
            ],
            "details": [
                e.detail for e in validation.errors if e.level == ValidationLevel.RED_LINE
            ],
        },
    )


def _archive_problems(result: MvpE2EResult, validation: Any) -> None:
    """Archive validation failures as problem items."""
    for error in validation.errors:
        category = "definition" if error.level in (ValidationLevel.STRUCTURE, ValidationLevel.SEMANTIC) else "acceptance"
        if error.level == ValidationLevel.RED_LINE:
            category = "definition"
        result.problem_items.append(
            {
                "sample_id": result.strategy_id,
                "category": category,
                "stage": "validation",
                "summary": error.message,
                "evidence": {
                    "code": error.code,
                    "path": error.path,
                    "detail": error.detail,
                },
                "owner": "codex",
                "next_action": "Fix DSL or adjust NL input",
            }
        )


def _normalize_operator(op_text: str) -> str:
    """Normalize supported Chinese comparison phrases to registry operators."""
    mapping = {
        "不少于": ">=",
        "不低于": ">=",
        "至少": ">=",
        "大于等于": ">=",
        "": ">=",
    }
    return mapping.get(op_text, op_text)


def _hash_payload(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def _load_audit_records(
    audit_logger: StrategyAuditLogger, trace_id: str
) -> list[dict[str, Any]]:
    return [
        {
            "trace_id": r.trace_id,
            "operation": r.operation,
            "strategy_id": r.strategy_id,
            "dsl_version": r.dsl_version,
            "input_hash": r.input_hash,
            "output_hash": r.output_hash,
            "red_line_result": r.red_line_result,
            "created_at": r.created_at,
        }
        for r in audit_logger.list_by_trace_id(trace_id)
    ]
