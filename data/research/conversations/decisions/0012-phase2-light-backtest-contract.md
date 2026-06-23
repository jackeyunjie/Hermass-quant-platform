# 0012 Phase 2 Light Backtest Contract

## 背景

Phase 0/1 Strategy Lab MVP 已通过样例级验收，但 `BacktestAdapter` 仍以 `light_stub` 返回占位指标。下一阶段目标是实现可审计、确定性、日线级的真实 Light Backtest，同时保留当前 mock/stub MVP 验收能力。

本轮 Codex 并行分配：

- Qoder：输出 Phase 2 Real Light Backtest 工程契约。
- Kimi：输出 Phase 2 真实数据与性能门禁。

## 决策

采纳 Qoder 的 Phase 2 合同：

- `backtest_adapter.py` 保留为 Strategy Lab facade。
- 新增 `backtest_models.py`、`backtest_data_provider.py`、`light_backtest_engine.py`、`backtest_metrics.py`，可选 `backtest_evidence.py`。
- DuckDB 负责列裁剪、日期/universe 过滤、state join 和字段归一。
- Polars 负责信号、仓位、交易、权益曲线、指标和 evidence frame。
- 真实回测模式标识固定为 `light_real_v1`，不得把 `light_stub` 或 synthetic benchmark 当真实绩效。
- Backtest 必须重新执行 schema/Pydantic 校验和 red-line 检查；失败时不读 DuckDB、不写 trades。

采纳 Kimi 的数据与性能门禁：

- Verdict 为 `MIXED`：MVP mock/stub 冻结继续可用；Phase 2 real backtest 需要补真实数据契约和 hot path gates。
- 真实基线目标为 5000 symbols x 252 trading days：total P50 < 20s，P95 < 30s，load P95 < 10s，signal P95 < 12s，metrics P95 < 8s，内存 < 4GB，0/5 runs fail。
- `validate_real_data.py` 需要补字段类型、唯一键、freshness、metadata、复权、停牌退市、license 和 future leakage 检查。
- `state_hex_d1` vs `d1_state` 的字段分歧由 Phase 2 data provider 做 alias 归一，避免本轮破坏 registry/translator。

## 理由

Qoder 的模块拆分让 provider、engine、metrics、evidence 可以分别单测，符合“Web 层只做入口，业务逻辑下沉 service”的项目规则。Kimi 的门禁把 synthetic smoke 与真实 baseline 分开，防止把 benchmark fixture 或 stub 输出误解为真实回测能力。

该裁决同时保持 MVP 可运行，不让真实数据缺口阻塞 Phase 0/1，也不为了 Phase 2 提前扩展 Agent Debate、Paper Trading 或前沿研究 sandbox。

## 下一步

1. Codex 实现第一批 Phase 2 backtest 模块和 synthetic integration fixture。
2. Codex 扩展 `benchmarks/validate_real_data.py` P0 checks，并新增 gate summary。
3. Qoder 后续审阅实现是否偏离 contract，重点看交易语义、审计顺序和 storage 写入。
4. Kimi 后续跟进真实 DB baseline、数据 freshness、license 和 hot path gate 结果。

## 参考

- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md`
- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md`
- `data/research/conversations/agent-runs/2026-06-11-qoder-phase2-light-backtest-contract.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-data-perf-gates.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-light-backtest-dispatch.md`
