# 2026-06-19 Kimi 真实数据下载与 DuckDB 构建运行摘要

## 任务

按 `agents/KIMI_NEXT_TASK_DATA_DOWNLOAD_AND_BUILD.md` 实际下载 A 股真实日线数据，构建：

- `data/p116_foundation.duckdb`
- `data/state_cube.duckdb`
- `outputs/benchmarks/data_readiness_status.json`

## 数据源

- **黑狼（Blackwolf）**：API 可用，`BLACKWOLF_TOKEN` 环境变量已配置。
- Hermass 仓库中已有每日合并的 Mac-format zip，最新到 `2026-06-18`。
- 直接复用 Hermass 仓库中的最新 zip，无需逐日重新调用 API。

## 执行步骤

1. 验证 Blackwolf API 可用性（单日期测试 `2026-06-18`）。
2. 更新 `scripts/build_hermass_data_from_blackwolf.py` 默认 zip 路径为最新 `blackwolf_ashare_daily_mac_format_20180515_20260618.zip`。
3. 运行构建脚本：

```bash
uv run python scripts/build_hermass_data_from_blackwolf.py
```

## 构建结果

```json
{
  "status": "PASS",
  "foundation_db": "data/p116_foundation.duckdb",
  "state_cube_db": "data/state_cube.duckdb",
  "foundation_stats": {
    "row_count": 8591347,
    "symbol_count": 5536,
    "date_min": "2018-05-15",
    "date_max": "2026-06-18",
    "trading_days": 1964
  },
  "state_stats": {
    "row_count": 8591347,
    "symbol_count": 5536,
    "date_min": "2018-05-15",
    "date_max": "2026-06-18"
  },
  "validation_ok": true,
  "validation_errors": [],
  "readiness": {
    "verdict": "READY",
    "staleness_days": 0
  }
}
```

## 性能基线

```bash
uv run python benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 500,2000,5000 --days 252 --runs 5

uv run python benchmarks/gate_summary.py \
  --output outputs/benchmarks/gate_summary_20260619.json
```

- 5000×252 `full_polars`：P50=1.97s，P95=2.12s
- data_load P95=0.18s
- signal_gen P95=0.19s
- equity_metrics P95=1.76s
- **gate_summary：PASS（8/8）**

## 回归测试

- `pytest hermass_platform/strategy_lab/tests scripts/test_web_ui_smoke.py`：284 passed
- `pytest hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`：8 passed
- `python scripts/run_strategy_lab_mvp_e2e_acceptance.py`：5/5 passed

## 关键改动

- `scripts/build_hermass_data_from_blackwolf.py`：默认 zip 路径更新到 2026-06-18。
- 复用此前已合并的 DuckDB autoload 禁用 helper（`_duckdb_helper.py`），构建脚本已使用该 helper。

## 输出物

- `data/p116_foundation.duckdb`
- `data/state_cube.duckdb`
- `data/metadata.json`
- `outputs/benchmarks/real_data_validation_20260619.json`
- `outputs/benchmarks/light_backtest_real_20260619.jsonl`
- `outputs/benchmarks/gate_summary_20260619.json`
- `outputs/benchmarks/data_readiness_status.json`

## 下一步

Handoff 给 Codex：真实数据已刷新至 2026-06-18，Web UI data readiness badge 应显示 READY，diagnosis backtest 可稳定走 `light_real_v1`。
