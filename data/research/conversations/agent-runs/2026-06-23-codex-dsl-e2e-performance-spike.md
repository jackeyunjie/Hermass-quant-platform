# DSL 端到端性能剖析 Spike（2026-06-23）

## 背景

M3 Pilot 准备期间发现：

- 纯 engine benchmark（`light_backtest_perf.py`）：5,000×252 P95=2.36s
- DSL 端到端（`run_strategy_lab_real_e2e_acceptance.py`）：~27-32s

差距约 12 倍。本 spike 目标：拆分 DSL 端到端各阶段耗时，定位瓶颈。

## 方法

1. 在 `hermass_platform/strategy_lab/e2e_runner.py` 的 `run_mvp_e2e_sample` 中增加 `profile=True` 模式，记录每个阶段耗时。
2. 新增 `benchmarks/dsl_e2e_perf.py`，对 3 个冻结样例跑全量真实数据（5,536 品种，2023-01-01 至 2024-12-31）。
3. 产出 `outputs/benchmarks/dsl_e2e_breakdown_20260623_081541.json`。

## 关键结果

| 阶段 | sample_ma_5_20_stop_8 | sample_state_volume | sample_ma_state_limit_filter |
|---|---|---|---|
| `generation` | 0.002s | 0.001s | 0.001s |
| `validation` | 0.001s | 0.001s | 0.001s |
| `storage_save_version` | 0.004s | 0.002s | 0.002s |
| `preview` | 0.001s | 0.001s | 0.001s |
| `backtest_engine`（adapter 层计时） | 15.97s | 14.19s | 15.46s |
| ├─ engine 内部 `elapsed_seconds` | 10.65s | 9.42s | 10.19s |
| └─ adapter 开销 | ~5.3s | ~4.8s | ~5.3s |
| `backtest_save_result` | 0.001s | 0.003s | 0.003s |
| `backtest_persist_trades` | 14.33s | 11.14s | 14.21s |
| `audit_load_close` | 0.003s | 0.003s | 0.002s |
| **total** | **30.33s** | **25.36s** | **29.70s** |

## 结论

### 1. 真正瓶颈不是 DSL 生成 / 校验 / Preview

`generation`、`validation`、`preview`、`storage_save_version`、`audit_load_close` 全部 < 0.01s。

### 2. 两大耗时块

**A. Backtest 引擎：9-11s 内部 + 4-5s adapter 开销**

- 纯 engine benchmark 的 2.36s 是简化向量化路径（只算组合收益，不生成完整交易明细）。
- DSL 路径调用 `light_backtest_engine.py` 生成完整 trades、daily_curve、state_breakdown，量级更重。
- Adapter 层（`BacktestAdapter.run_backtest`）有约 4-5s 开销，可能来自 DSL → BacktestConfig 转换、结果序列化/反序列化、signal_frame 构造。

**B. Trade/Event 持久化：11-14s（占总耗时 35-45%）**

- `_persist_trades_and_events` 逐条调用 `storage.save_trade_record()` 和 `storage.save_trade_event_evidence()`。
- 每个调用都是一次 DuckDB INSERT ... ON CONFLICT（UPSERT）。
- 样例 3 有 339 笔交易，event evidence 数量更大，逐条插入是主要耗时。

### 3. 12 倍差距解释

```
2.4s  benchmark  ≈ 纯向量化组合收益计算
27s   DSL E2E    ≈ 完整引擎（9-11s）+ adapter（4-5s）+ 逐条持久化（11-14s）
```

两者不是同一口径，不能直接用 2.4s 作为 DSL E2E 的目标。

## 优化实施与结果

在 spike 期间直接落地了两项优化：

### 1. 批量持久化（`storage.py` + `e2e_runner.py`）

- 新增 `StrategyLabStorage.save_trade_records_batch()` 和 `save_trade_event_evidence_batch()`，使用 DuckDB `executemany`。
- `_persist_trades_and_events` 改为批量写入，失败时回退逐条。
- 效果：保存 trades/events 从 ~0.5-1s（batch）取代 ~11-14s（row-by-row），但**不是主要瓶颈**。

### 2. signal_frame 过滤（`backtest_evidence.py`）

- `build_trade_records()` 和 `build_trade_event_evidence()` 在 `to_dicts()` 前先过滤 `trade_id IS NOT NULL`。
- 这避免把 250 万行 signal frame 全部转成 Python dict。
- 效果：
  - `build_trade_records`：6.7s → **0.01s**
  - `build_trade_events`：6.6s → **0.01s**

## 优化后结果

| 样例 | 优化前 total | 优化后 total | 提升 |
|---|---|---|---|
| sample_ma_5_20_stop_8 | 30.33s | **16.72s** | -45% |
| sample_state_volume_stop_8_take_15 | 25.36s | **14.58s** | -43% |
| sample_ma_state_limit_filter | 29.37s | **16.08s** | -45% |

优化后耗时 breakdown：

| 阶段 | 耗时 | 占比 |
|---|---|---|
| generation / validation / preview / audit | <0.01s | ~0% |
| backtest_save_result | <0.01s | ~0% |
| build_trade_records / build_trade_events | 0.01s | ~0.1% |
| save_trade_records_batch / save_trade_events_batch | 0.4-1.0s | ~5% |
| **backtest_engine**（adapter 层计时） | **14-16s** | **~90%** |
| ├─ engine 内部 `elapsed_seconds` | 9-11s | ~60% |
| └─ adapter 开销 | 4-5s | ~30% |

## 剩余瓶颈

**backtest_engine 仍是主要耗时来源（14-16s，占 ~90%）**，其中：

- engine 内部 9-11s：与 `light_backtest_perf.py` 的 2.4s 仍有 4-5 倍差距，因为 DSL 路径生成完整 trades、signal_frame、state_breakdown，口径更重。
- adapter 开销 4-5s：可能来自 DSL → BacktestConfig 转换、结果打包、signal_frame 构造。

进一步优化的 ROI 已经不高（从 16s 到 11s 的理论空间），且可能触及 engine 核心逻辑。建议 M3 Pilot 阶段保持当前水平（<20s 已满足体验要求），将 engine 优化放入 M4 backlog。

## 代码变更

- `hermass_platform/strategy_lab/storage.py`：新增 batch save 方法
- `hermass_platform/strategy_lab/e2e_runner.py`：使用 batch、增加 `profile=True`、细化 persist 计时
- `hermass_platform/strategy_lab/backtest_evidence.py`：signal_frame 先过滤再 `to_dicts()`
- `hermass_platform/strategy_lab/tests/test_storage.py`：新增 batch 单元测试
- `benchmarks/dsl_e2e_perf.py`：新增 E2E 性能剖析脚本

## 验证

- `pytest hermass_platform/strategy_lab/tests scripts/test_web_ui_smoke.py -q`：300 passed
- `python benchmarks/dsl_e2e_perf.py`：3 样例均 <17s

## 参考文件

- `benchmarks/dsl_e2e_perf.py`
- `outputs/benchmarks/dsl_e2e_breakdown_20260623_084150.json`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `hermass_platform/strategy_lab/backtest_evidence.py`
- `hermass_platform/strategy_lab/storage.py`
