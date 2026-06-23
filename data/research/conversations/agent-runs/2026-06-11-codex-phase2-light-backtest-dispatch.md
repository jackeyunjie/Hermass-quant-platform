# Codex Phase 2 Light Backtest Dispatch

## 背景

Phase 0/1 Strategy Lab MVP 已经可运行，当前主链路仍是：

中文策略输入 -> DSL v2 -> Schema/Pydantic 校验 -> 红线检查 -> 条件命中预览 -> Light Backtest stub -> 审计落库。

下一步应从 `light_stub` 推进到 Phase 2 真实 Light Backtest，但不能牺牲 MVP 可运行基线，也不能提前扩展 Agent Debate、Paper Trading、TS-FM 或 RAG-KG。

## 决策

本轮分配两条并行任务：

- Qoder：设计 Phase 2 Real Light Backtest 的可实现工程契约，输出 `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md` 和对应 agent-run note。
- Kimi：设计 Phase 2 真实数据契约与性能门禁，输出 `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md` 和对应 agent-run note。

Codex 主线程负责维持基线验收、更新任务分配和项目记忆，不与两个子任务抢同一写入范围。

## 理由

真实 Light Backtest 同时依赖两个独立前提：

- 架构与交易语义：DSL 条件如何变成信号、仓位、止损/止盈、交易成本、同日冲突和审计记录。
- 数据与性能门禁：真实行情/状态/指标字段是否就绪，5000 symbols x 252 days 是否能达成 P50/P95 目标。

这两个方向可以并行推进，且都必须先形成可验收 contract，再进入引擎实现。

## 当前基线

已复核：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
```

结果：`200 passed, 1 warning`。

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

结果：`5/5 cases passed`。

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py benchmarks/*.py
```

结果：通过。

说明：系统默认 `python3` 当前指向 Homebrew Python 3.14，未安装 pytest；项目验收继续使用 Python 3.11.12。

## 下一步

1. 等待 Qoder 回传 Phase 2 Light Backtest contract。
2. 等待 Kimi 回传真实数据与性能门禁 contract。
3. Codex 复核两份输出，裁决冲突，并压缩成 Phase 2 第一批实现任务。
4. Phase 2 实现仍必须保留 `light_stub` 标注，不得把占位指标伪装成真实绩效。
