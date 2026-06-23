# 2026-06-19 Kimi Phase 3 Real Data Baseline Handoff

## 背景

Phase 3 Web UI 需要真实数据 baseline。之前 `light_backtest_perf.py` 在 5000 品种 × 252 天真实数据上 P50 ~36s、P95 ~36s，data_load P95 ~34.7s，未通过性能 gate（目标 P50<20s / P95<30s / data_load<10s）。

## 诊断

- 信号生成与权益曲线阶段本身很快（<2s）。
- 耗时瓶颈在 **DuckDB 连接后的扩展自动加载**：DuckDB 1.5.3 在打开已有 DB 时会尝试 autoload/autoinstall extension，触发网络请求，在受限网络下形成数十秒等待。
- 测试确认：在连接后立即 `SET autoinstall_known_extensions=false; SET autoload_known_extensions=false`，`COPY ... TO PARQUET` 数据导出从 ~34s 降至 ~0.2s。

## 决策与改动

1. **benchmarks/light_backtest_perf.py**
   - 连接后禁用 extension autoload/autoinstall。
   - 保留 `_load_via_parquet` 的 pyarrow-free 数据加载路径（`COPY ... TO PARQUET` + `pl.read_parquet`）。

2. **benchmarks/gate_summary.py**
   - `summarize_benchmark` 现在按 `(mode, universe_n)` 分组，例如 `full_polars_5000`。
   - gate 评估优先取 `full_polars_{max_universe}`，确保 5000×252 是验收对象，而不是把不同品种数混在一起。

3. **hermass_platform/strategy_lab/_duckdb_helper.py（新增）**
   - 统一 DuckDB 连接入口，禁用 extension autoload，避免生产路径（storage/audit/backtest/preview）受网络 stall 影响。

4. **生产路径替换**
   - `backtest_data_provider.py`
   - `preview_service.py`
   - `storage.py`
   - `audit.py`
   - `scripts/build_hermass_data_from_blackwolf.py`

   全部改用 helper 连接。

## 验收结果

### validate_real_data

```bash
uv run python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/real_data_validation_20260619.json
```

- exit 0
- ok=true
- errors=[]
- warnings=2（非阻塞）

### light_backtest_perf

```bash
uv run python benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 500,2000,5000 \
  --days 252 \
  --runs 5
```

- 30 records written
- 5000×252 `full_polars` P50=2.12s, P95=2.28s
- data_load P95=0.32s
- signal_gen P95=0.20s
- equity_metrics P95=1.80s

### gate_summary

```bash
uv run python benchmarks/gate_summary.py \
  --output outputs/benchmarks/gate_summary_20260619.json
```

- status=PASS
- gates=8 全部通过

### 回归测试

- `pytest hermass_platform/strategy_lab/tests`：278 passed
- `python scripts/test_web_ui_smoke.py`：5/5 passed
- `python scripts/run_strategy_lab_mvp_e2e_acceptance.py`：5/5 passed
- `pytest hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`：8 passed

## 数据基线摘要

- foundation_db: `data/p116_foundation.duckdb`
- state_cube_db: `data/state_cube.duckdb`
- data_source: `blackwolf_real`
- price_adjustment: `forward_adjusted`
- license_status: `research_only`
- last_refresh_at: `2026-06-19T07:14:59Z`
- date_min: `2018-05-15`
- date_max: `2026-06-10`
- symbol_count: 5534
- trading_days: 1958
- daily_bars_rows: 8,558,275
- state_cube_rows: 8,558,275
- known_missing_fields: 无
- known_data_limitations:
  - 真实数据仅覆盖 A 股日线，分钟线未接入。
  - State Cube 当前仅含 d1/w1/mn1，不含 h4/h1。

## 下一步

Handoff 给 Codex：Web UI `light_real_v1` 已可稳定运行，建议将 diagnosis backtest 默认走真实数据（当前 adapter 在 foundation_db 存在时已是 light_real_v1），并在 UI 上继续显示 data readiness badge 与免责声明。
