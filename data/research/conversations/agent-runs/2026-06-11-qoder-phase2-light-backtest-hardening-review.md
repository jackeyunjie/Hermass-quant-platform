# Qoder Phase 2 Light Backtest Hardening Review

## 背景

C17 已把 Phase 2 Light Backtest contract 交给 Codex 实现，Codex 已完成第一版 `light_real_v1` synthetic integration，并记录在：

- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-light-backtest-implementation-review.md`

C18 要求 Qoder 对当前实现做 hardening review，按 blocker / acceptable / backlog 分类偏差，不实现代码。

## 决策

当前实现可以进入 internal synthetic release，但不能进入 Phase 2 real baseline release。

关键原因：

- adapter 入口红线已补上，provider 列裁剪也已补上，这两点满足 synthetic MVP 的安全底线。
- engine 仍使用 Python row loop，并且按 `symbol,date` 执行，会破坏多 symbol 日期级组合权益。
- real evidence 落库链路未闭合：E2E 依赖 `bt_result.signal_frame`，但 adapter 返回的 `BacktestResult` 没有该字段。
- 缺失真实 DB baseline 与 benchmark smoke，不能做真实指标或性能承诺。

完整任务说明已落地：

- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_HARDENING_REVIEW.md`

## 偏差分类

### Blocker

- real 模式缺 DB 时静默降级 `light_stub`。
- 多 symbol 日期级执行语义错误。
- trade/event evidence 不能从 real E2E path 自动可靠写入 storage。
- `volume_ratio OR volume_ma_N` provider 契约未闭合。
- 真实 DB gate 尚未运行。

### Acceptable for synthetic MVP

- adapter 入口重新 `validate_dsl()`。
- DuckDB provider 白名单列裁剪。
- E2E response 暂时只截断前 100 条 daily/trades。
- small synthetic fixture 下允许 row loop，但必须标注 synthetic smoke。
- `light_stub` 继续作为无 DB compatibility path。

### Phase 2 real baseline backlog

- `date,symbol` batch execution。
- API response truncation metadata 和 storage reference。
- `strategy_trade_events` 按 `trace_id` 查询。
- suspended close 缺失 forward-fill 与 warning。
- limit-down blocked exit 的 hold evidence。
- unsupported timeframe 明确 failed。
- service boundary: `run_light_backtest_service()` / `get_backtest_service()`。

## Codex 下一步

按以下顺序实现和验收：

1. 修 `backtest_adapter.py`，传入不存在的 `foundation_db` 时 failed，不再 fallback stub。
2. 暴露 real execution artifact，打通 `backtest_evidence.py` 到 `storage.py` 的 E2E evidence 写入。
3. 修 `light_backtest_engine.py` 日期级多 symbol 执行和 daily equity。
4. 补 `volume_ratio OR volume_ma_N` provider contract。
5. 补 API response 截断元数据。
6. 补停牌/跌停 hardening。
7. 真实 DB 就绪后运行 `validate_real_data.py` 和 benchmark smoke。

验收命令基线：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py benchmarks/*.py
```

真实数据 gate 只在 DB 存在后运行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/validation.json
```

## Release Gate

- Synthetic release: YES, only internal and only with synthetic label。
- Real baseline release: NO, blocked by execution semantics, evidence persistence, volume provider contract, and missing real DB gate。
- Pilot/public beta: NO, requires real baseline, data quality audit, response/storage traceability, performance gate, and clear non-investment-advice disclosure。

## 明确不做

本轮不扩展 Agent Debate、Paper Trading、分钟线、walk-forward、真实下单，也不允许 LLM Python 策略代码进入执行链路。
