# Codex Phase 2 Light Backtest Implementation Review

## 背景

Qoder Phase 2 Light Backtest 合约已被实现到工作区，目标是把 `light_stub` 之外的真实日线 Light Backtest v1 打通，同时保持 MVP mock/stub 链路不回归。

本次 Codex 复核重点：

- 是否仍通过当前 Strategy Lab 测试。
- 是否保持 MVP E2E acceptance。
- 是否遵守红线不可绕过。
- 是否符合 DuckDB 列裁剪和不使用 `SELECT *` 的 contract。

## 决策

采纳当前 Phase 2 Real Light Backtest 第一版实现，但补充两处 contract 防线：

1. `BacktestAdapter.run_backtest()` 入口强制执行 `validate_dsl()`。红线或 DSL 校验失败时返回 failed，不读 DuckDB、不运行 engine、不生成 trades。
2. `DuckDBBacktestDataProvider` 改为白名单列裁剪，根据 base columns、DSL required columns 和 state alias 选择列，不再对 `daily_bars` / `state_cube` 使用 `SELECT *`。

## 理由

E2E runner 会先做 validation，但 adapter 是公开 facade，不能假设所有调用方都会先通过 runner。红线检查必须靠近 backtest 执行入口。

列裁剪是 Phase 2 性能和安全 contract 的关键约束。provider 只应读取已知表和已发现 schema 中的白名单列，避免把未知数据面扩大到 engine。

## 已复核结果

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
```

结果：`278 passed, 1 warning`。

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

结果：`5/5 cases passed`。

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py benchmarks/*.py
```

结果：通过。

相关局部测试：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest \
  hermass_platform/strategy_lab/tests/test_backtest_data_provider.py \
  hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py -q
```

结果：`19 passed, 1 warning`。

## 当前交付

新增模块：

- `hermass_platform/strategy_lab/backtest_models.py`
- `hermass_platform/strategy_lab/backtest_data_provider.py`
- `hermass_platform/strategy_lab/light_backtest_engine.py`
- `hermass_platform/strategy_lab/backtest_metrics.py`
- `hermass_platform/strategy_lab/backtest_evidence.py`

改造模块：

- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/__init__.py`

新增测试：

- `hermass_platform/strategy_lab/tests/test_backtest_data_provider.py`
- `hermass_platform/strategy_lab/tests/test_light_backtest_engine.py`
- `hermass_platform/strategy_lab/tests/test_backtest_metrics.py`
- `hermass_platform/strategy_lab/tests/test_backtest_evidence.py`
- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`

## 未完成项

真实数据 baseline 尚未运行，因为当前 workspace 缺少：

- `data/p116_foundation.duckdb`
- `data/state_cube.duckdb`

因此当前 Phase 2 状态是：synthetic integration 通过，real data baseline 待真实 DB 就绪后执行。

## 下一步

1. 决定是否提交 Phase 2 Light Backtest 实现。
2. 真实 DB 就绪后运行 Kimi 定义的 `validate_real_data.py` 和 hot path gate。
3. 若真实 baseline 失败，优先修 provider 数据契约或 engine 热路径，不扩大产品范围。
