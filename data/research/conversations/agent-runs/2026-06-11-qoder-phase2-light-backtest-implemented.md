# 2026-06-11 Qoder Phase 2 Light Backtest 实现交付

## 背景

`agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md` 定义了 Phase 2 Real Light Backtest 的完整工程契约（911 行）。此前 Phase 0/1 MVP 已通过 200 个测试，但 `BacktestAdapter` 仍返回 `light_stub` 占位指标。

## 实现范围

### 新增 5 个模块

| 文件 | 行数 | 职责 |
|---|---|---|
| `backtest_models.py` | 153 | MarketDataRequest/Bundle, SignalFrame, TradeSummary, EquityPoint, LightBacktestOutput |
| `backtest_data_provider.py` | 319 | DuckDB 取数、列归一化（state_hex_d1→d1_state, close→close_d1, ma_N→ma_N_d1）、必需列校验 |
| `light_backtest_engine.py` | 812 | Polars 向量化信号计算 + 行级交易生成 + 权益曲线 + 指标编排 |
| `backtest_metrics.py` | 170 | total_return, annual_return, max_drawdown, sharpe_ratio, win_rate, profit_factor, avg_holding_days, turnover, cost_total |
| `backtest_evidence.py` | 329 | build_trade_records + build_trade_event_evidence，输出 storage 兼容 dict |

### 改造 5 个现有文件

- `backtest_adapter.py`：facade 路由，foundation_db 存在→real engine，否则→stub
- `api_models.py`：BacktestRequest/Response/Metrics 新增可选字段
- `e2e_runner.py`：支持 real mode + trade 持久化 + status 从 risk_flags 计算
- `storage.py`：新增 `list_backtests()`
- `__init__.py`：导出新模块

### 新增 4 个单元测试文件 + 1 个集成测试文件

| 文件 | 测试数 | 覆盖 |
|---|---|---|
| `test_backtest_data_provider.py` | 11 | 列归一化、缺列报错、universe 过滤、state join、data_version |
| `test_light_backtest_engine.py` | 14 | 金叉/死叉信号、止损止盈优先级、同日冲突、100 股 rounding、停牌、MA 自动计算 |
| `test_backtest_metrics.py` | 22 | 总收益、年化、最大回撤、Sharpe、胜率、盈亏比、持仓天数、换手率 |
| `test_backtest_evidence.py` | 23 | trade record 提取、event type 映射、blocked exit→hold、indicator snapshot |
| `test_real_light_backtest_integration.py` | 8 | 端到端 synthetic DuckDB fixture，验证 mode/metrics/trades/storage |

## 验收结果

```
278 passed, 1 warning in 2.27s
```

- 200 个原有 Phase 0/1 测试零修改通过
- 78 个新增测试全部通过
- E2E acceptance: 5/5 cases passed

## 关键设计决策

1. **Provider 层做 D1 别名归一**：ConditionRegistry 解析列名为 `close_d1`/`ma_N_d1`，但 DuckDB fixture 只有 `close`/`ma_N`。Provider 统一添加别名，避免破坏 registry/translator。
2. **Status 始终从 risk_flags 计算**：不依赖 `BacktestResult.status` 默认值，而是 `"failed" if failed else "partial" if risk_flags else "success"`，保持与 Phase 0/1 测试期望一致。
3. **Engine 自动补算缺失 MA 列**：`_compute_required_ma()` 用 Polars `rolling_mean` 按 symbol 分组计算，不阻塞 MVP。
4. **交易生成用行级迭代**：持仓上下文、同日冲突、成本计算需要状态机，无法纯向量化。Polars 只负责信号层。

## 已知阻塞

- 真实 DB 缺失：`data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 不存在
- `light_real_v1` 只可作为 internal synthetic smoke
- Hardening backlog：real mode 缺 DB fallback、日期级多 symbol 语义、volume_ratio OR volume_ma_N 契约

## 下一步

1. 真实 DB 就绪后跑 Kimi real baseline gate
2. Hardening：real DB fallback + trade/event evidence 全链路落库
3. 修正多 symbol 日期级执行语义
4. 闭合 volume_ratio provider 契约
