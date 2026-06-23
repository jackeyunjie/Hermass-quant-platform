# Codex Phase 2 Real Baseline And Hardening Dispatch

## 背景

Phase 2 Real Light Backtest 第一版已经完成 synthetic integration，并通过当前 Strategy Lab 测试。Codex 复核时已补两处 contract 防线：

- `BacktestAdapter.run_backtest()` 入口强制执行 `validate_dsl()`。
- `DuckDBBacktestDataProvider` 使用白名单列裁剪，不再对行情/状态表使用 `SELECT *`。

当前未完成的关键门槛是真实 DB baseline：workspace 尚未确认存在 `data/p116_foundation.duckdb` 和 `data/state_cube.duckdb`。

## 决策

本轮继续分配两条并行任务：

- Kimi：输出 Phase 2 real DB baseline readiness/runbook，检查真实 DB 是否存在，并给出存在/不存在两套执行路径。
- Qoder：输出 Phase 2 Light Backtest hardening review，对当前实现与 contract 偏差做 blocker / acceptable / backlog 分类。

本轮不启动新的代码实现。先确认真实数据门槛与 hardening 清单，再决定是否提交 Phase 2 实现或继续修补。

## 理由

Phase 2 现在已经越过 synthetic integration，但尚未越过 real baseline。Kimi 更适合判断数据 readiness 和 gate 命令，Qoder 更适合审阅实现是否偏离 DSL-first / red-line-first / audit-first contract。

把两类审阅分开，可以避免把真实性能问题和引擎语义问题混在一起。

## 下一步

1. 等待 Kimi 回传 `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md` 和对应 run note。
2. 等待 Qoder 回传 `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_HARDENING_REVIEW.md` 和对应 run note。
3. Codex 复核两份输出，更新 `docs/TASK_ALLOCATION.md`。
4. 若存在 blocker，Codex 先修 blocker；若无 blocker，准备提交 Phase 2 synthetic release 实现。
