# Benchmarks

可运行基准脚本集合。所有脚本支持 `--synthetic` 在没有真实 DuckDB 时生成临时数据。

## 文件清单

| 文件 | 说明 |
|------|------|
| `light_backtest_perf.py` | Light Backtest `full_polars` vs `filter_first` |
| `indicator_precompute_vs_compute.py` | 预计算 `ma_20` 读取 vs 窗口函数实时计算 |
| `duckdb_vs_polars.py` | DuckDB-only 简单信号 vs DuckDB 取数 + Polars 计算 |
| `state_cube_query.py` | State Cube 无缓存 / 列裁剪 / LRU 缓存查询对比 |
| `_synthetic.py` | Synthetic 数据生成器（setup 用，允许循环） |

## 运行方式

```bash
# 使用 synthetic 数据（默认输出到 outputs/benchmarks/）
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic

# 使用真实数据
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --db-path data/p116_foundation.duckdb
```

## 输出格式

所有脚本输出 JSONL，每行包含：

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

## 注意事项

- Synthetic 结果仅用于验证脚本可运行，**不作为最终性能承诺**。
- 热路径（信号生成、权益曲线、查询循环）**不使用 Python 逐行循环**。
- `_synthetic.py` 中的循环仅用于数据构造，与 benchmark 热路径分离。
