# Benchmarks

可运行基准脚本集合。所有脚本支持 `--synthetic` 在没有真实 DuckDB 时生成临时数据。

## 文件清单

| 文件 | 说明 |
|------|------|
| `validate_real_data.py` | 数据体检：验证 Foundation DB 和 State Cube 的表、列、索引、行数 |
| `light_backtest_perf.py` | Light Backtest `full_polars` vs `filter_first`，含分阶段计时 |
| `indicator_precompute_vs_compute.py` | 预计算 `ma_20` 读取 vs 窗口函数实时计算 |
| `duckdb_vs_polars.py` | DuckDB-only 简单信号 vs DuckDB 取数 + Polars 计算 |
| `state_cube_query.py` | State Cube 无缓存 / 列裁剪 / LRU 缓存查询对比 |
| `_synthetic.py` | Synthetic 数据生成器（setup 用，允许循环） |

## 统一 CLI 参数

所有 benchmark 脚本支持：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--db-path` | DuckDB 路径 | 见各脚本 |
| `--synthetic` | 使用 synthetic 数据 | `False` |
| `--output` | JSONL 输出路径 | `outputs/benchmarks/...` |
| `--runs` | 每配置重复次数 | `5` |
| `--symbols` | 品种数（逗号分隔或单值） | 见各脚本 |
| `--days` | synthetic 数据天数 | `252` |

## 数据体检

在跑真实数据 benchmark 前必须先执行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/real_data_validation_$(date +%Y%m%d).json
```

- `ok=true` 时才能将 benchmark 结果作为 Phase 2 验收依据。
- `ok=false` 时修复数据后再跑 benchmark。
- 缺失 DB 或 schema 不完整时脚本仍会写出 JSON，但进程退出码为 1，这是预期行为。

## 运行方式

### Synthetic Smoke（CI / 本地快速验证）

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --symbols 500 --days 120 --runs 2
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --symbols 500 --days 120 --runs 2
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --symbols 500 --days 120 --runs 2
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --symbols 500 --days 120 --runs 2
```

### 真实数据 Benchmark

```bash
# 1. 先体检
python benchmarks/validate_real_data.py --foundation-db data/p116_foundation.duckdb --state-cube-db data/state_cube.duckdb --output outputs/benchmarks/validation.json

# 2. 再 benchmark
python benchmarks/light_backtest_perf.py --db-path data/p116_foundation.duckdb
python benchmarks/indicator_precompute_vs_compute.py --db-path data/p116_foundation.duckdb
python benchmarks/duckdb_vs_polars.py --db-path data/p116_foundation.duckdb
python benchmarks/state_cube_query.py --db-path data/state_cube.duckdb
```

## 输出格式

所有 benchmark 脚本输出 JSONL，每行包含：

```json
{
  "benchmark_name": "...",
  "mode": "...",
  "universe_n": 5000,
  "days": 252,
  "run_index": 0,
  "elapsed_s": 1.234567,
  "p50_s": 1.1,
  "p95_s": 1.5,
  "data_source": "synthetic",
  "python_version": "3.11.12",
  "platform": "macOS-...",
  "notes": "rows_loaded=1260000"
}
```

`light_backtest_perf.py` 额外包含分阶段计时字段：

```json
{
  "data_load_s": 0.5,
  "signal_gen_s": 0.3,
  "equity_metrics_s": 0.2,
  "peak_memory_mb": 256.5
}
```

## Phase 2 Hot Path Gates

- Light Backtest 5000×252 **P95 < 30s**。
- 数据加载 **< 10s**，信号生成 **< 12s**，权益曲线+指标 **< 8s**。
- 内存峰值 **< 4GB**。
- 热路径**禁止**以下模式：
  - `apply(lambda row: ...)`
  - `iterrows`
  - `for row in ...`
  - pandas 中间转换
  - `SELECT *`
  - Python 级分组循环
  - `eval` / `exec`

## 注意事项

- Synthetic 结果仅用于验证脚本可运行，**不作为最终性能承诺**。
- 热路径（信号生成、权益曲线、查询循环）**不使用 Python 逐行循环**。
- `_synthetic.py` 中的循环仅用于数据构造，与 benchmark 热路径分离。
- 真实数据 benchmark 结果写入 `*_real_YYYYMMDD.jsonl`，保留 30 天，旧文件归档到 `outputs/benchmarks/archive/`。
