# 0014 Phase 2 Light Backtest 实现落地

## 背景

Phase 2 contract（0012）定义了 `light_real_v1` 的模块拆分、接口签名、交易规则和测试清单。Qoder 输出 911 行规格后，Codex 按推荐顺序完成全部实现：provider → engine → metrics → evidence → adapter facade → storage → e2e → tests。

## 决策

### 已实现

- 5 个新模块：`backtest_models.py`、`backtest_data_provider.py`、`light_backtest_engine.py`、`backtest_metrics.py`、`backtest_evidence.py`。
- 5 个改造文件：`backtest_adapter.py`、`api_models.py`、`e2e_runner.py`、`storage.py`、`__init__.py`。
- 78 个新测试（provider 11 + engine 14 + metrics 22 + evidence 23 + integration 8），200 个原有测试零修改通过。

### 设计裁决

1. **Provider 做 D1 别名归一**而非改 registry：`close → close_d1`、`ma_N → ma_N_d1`。理由：避免破坏 Phase 0/1 translator 和 preview 链路。
2. **交易生成用行级迭代**而非纯 Polars 向量化：持仓上下文、同日冲突规则和成本计算需要状态机。Polars 只负责信号层。
3. **Status 始终从 risk_flags 重新计算**：不信任 `BacktestResult.status` 默认值，保持与 Phase 0/1 测试一致。
4. **Engine 自动补算缺失 MA 列**：`_compute_required_ma()` 用 `rolling_mean.over("symbol")` 补算，不拒绝 MVP fixture。

### 已解决的硬阻塞（2026-06-22）

- ✅ 真实 DB baseline：`data/p116_foundation.duckdb`（8.6M 行，5,536 品种）和 `data/state_cube.duckdb` 已就绪，`verdict=READY`。
- ✅ Real mode 不静默 fallback：缺失 DB 时返回 `BT_DATA_DB_NOT_FOUND`；Web UI 和 API 均显式标注运行模式。
- ✅ 日期级多 symbol 执行语义：engine 按 `date ASC, symbol ASC` 排序迭代。
- ✅ trade/event evidence 全链路落库：`e2e_runner.py` 和 Web UI backtest 路径均持久化完整交易记录与事件证据。
- ✅ `volume_ratio OR volume_ma_N` provider 契约闭合：预计算 `volume_ratio` 可作为 `volume_ma_N` 的替代列。
- ✅ 真实数据端到端验收：`scripts/run_strategy_lab_real_e2e_acceptance.py` 3 个冻结中文样例在 100 品种 universe 上通过 `light_real_v1`。

## 理由

按 contract 的 8 步实现顺序逐步交付，每步有单测覆盖。把 provider、engine、metrics、evidence 拆开让每层可独立验证，符合"先交付确定性链路"原则。真实 DB 就绪后，通过 provider 列名归一和 engine 信号层兼容，使 Phase 0/1 的 DSL 样例无需修改即可跑通真实回测。

## 下一步

1. 扩展 `validate_real_data.py` P0 checks：停牌/退市/复权口径显式检查。
2. Engine 性能：在真实全量 5,000×252 benchmark 下决定是否优化行级交易生成。
3. Phase 3+：JSON API 完善、M3 Controlled Pilot 准备。
4. Phase 2 不扩展 Agent Debate / Paper Trading / 真实下单。

## 参考

- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md`
- `data/research/conversations/agent-runs/2026-06-11-qoder-phase2-light-backtest-implemented.md`
- `data/research/conversations/decisions/0012-phase2-light-backtest-contract.md`
