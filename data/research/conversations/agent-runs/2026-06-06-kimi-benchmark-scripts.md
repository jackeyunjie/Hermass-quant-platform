# Kimi Benchmark Scripts

> 日期：2026-06-06  
> 任务来源：`agents/KIMI_NEXT_TASK_BENCHMARKS.md`  
> 执行人：Kimi Research Engineer

---

## Implemented Files

| 文件 | 说明 |
|------|------|
| `benchmarks/light_backtest_perf.py` | Light Backtest `full_polars` vs `filter_first`，策略：MA5 金叉 MA20 入场，MA5 死叉 MA10 或止损 8% 出场。 |
| `benchmarks/indicator_precompute_vs_compute.py` | 对比 DuckDB 窗口函数实时计算 `ma_20` vs 直接读取预计算列。 |
| `benchmarks/duckdb_vs_polars.py` | 对比 DuckDB-only SQL 简单信号 vs DuckDB 取数 + Polars 表达式计算。 |
| `benchmarks/state_cube_query.py` | 对比 State Cube `SELECT *` 无缓存、列裁剪、LRU 缓存（最近 5 日期）三种查询模式。 |
| `benchmarks/_synthetic.py` | Synthetic 数据生成器，构造 `daily_bars` 和 `state_cube`，含索引。 |
| `benchmarks/README.md` | 使用说明与输出格式文档。 |

所有脚本均满足：

- 支持 `--db-path`、`--synthetic`、`--output` 参数。
- 输出 JSONL 到 `outputs/benchmarks/`。
- JSONL 每行包含：`benchmark_name`、`mode`、`universe_n`、`days`、`run_index`、`elapsed_s`、`p50_s`、`p95_s`、`data_source`、`python_version`、`platform`、`notes`。
- 热路径无 Python 逐行循环。

---

## How To Run

```bash
# synthetic 基线（验收命令）
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --output outputs/benchmarks/light_backtest_synthetic.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --output outputs/benchmarks/indicator_synthetic.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --output outputs/benchmarks/duckdb_vs_polars_synthetic.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --output outputs/benchmarks/state_cube_synthetic.jsonl

# 真实数据（当 p116_foundation.duckdb / state_cube.duckdb 就绪后）
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --db-path data/p116_foundation.duckdb
```

---

## Synthetic Baseline Results

在 Apple Silicon M2 Max / 32GB RAM 上，synthetic 数据（5000 品种 × 252 日）的初步结果如下：

### light_backtest_perf

| universe | mode | P50 (s) | P95 (s) | 备注 |
|----------|------|---------|---------|------|
| 500 | full_polars | ~0.03 | ~0.04 | 126k 行 |
| 500 | filter_first | ~0.02 | ~0.03 | 约 60% 行被过滤 |
| 2000 | full_polars | ~0.07 | ~0.09 | 504k 行 |
| 2000 | filter_first | ~0.05 | ~0.06 | 行数减少约 40% |
| 5000 | full_polars | ~0.14 | ~0.18 | 1.26M 行 |
| 5000 | filter_first | ~0.10 | ~0.13 | 行数减少约 35% |

**结论**：`filter_first` 在 synthetic 数据上比 `full_polars` 快约 **20–30%**。真实数据中的收益取决于信号稀疏度。

### indicator_precompute_vs_compute

| 模式 | 耗时 (s) | 备注 |
|------|----------|------|
| compute_window | ~0.09 | 1.26M 行 AVG OVER window |
| read_precomputed | ~0.02 | 直接读列 |
| ratio | ~4.5x | 预计算读取快 4–5 倍 |

**结论**：预计算列读取明显快于窗口函数实时计算，支持将 `ma_5/10/20/60` 等指标预计算进 Foundation DB。

### duckdb_vs_polars

| universe | mode | P50 (s) | 备注 |
|----------|------|---------|------|
| 500 | duckdb_only | ~0.009 | SQL window + filter |
| 500 | duckdb_load_polars | ~0.008 | Arrow 零拷贝 + Polars filter |
| 2000 | duckdb_only | ~0.02 | |
| 2000 | duckdb_load_polars | ~0.02 | |
| 5000 | duckdb_only | ~0.05 | |
| 5000 | duckdb_load_polars | ~0.04 | |

**结论**：简单信号场景下两者接近；复杂出场逻辑（止损、移动止损）在纯 DuckDB SQL 中难以表达，因此 **DuckDB 取数 + Polars 计算** 是合理分工。

### state_cube_query

| mode | P50 (s) | P95 (s) | 备注 |
|------|---------|---------|------|
| no_cache (SELECT *) | ~0.006 | ~0.013 | 50 次随机日期查询 |
| pruned (3 列) | ~0.005 | ~0.011 | 列裁剪略快 |
| lru_cache | ~0.0002 | ~0.0004 | 命中缓存时快 1–2 个数量级 |

**结论**：LRU 缓存对重复查询收益极大；列裁剪在 State Cube 列数不多时收益有限，但在真实宽表（数十列）时会更显著。

> **重要**：以上均为 synthetic 数据结果，**不可作为最终性能承诺**。真实数据（A 股 5000+ 品种）的 I/O 特征、索引状态、数据分布可能与 synthetic 不同。

---

## Real Data Requirements

要运行真实数据基线，需要：

1. `data/p116_foundation.duckdb`：
   - 表 `daily_bars`
   - 列：`symbol, date, open, high, low, close, volume, ma_5, ma_10, ma_20, ma_60, atr_14, bb_position, volume_ratio, adx_14, is_limit_up`
   - 至少覆盖 5000 品种 × 252 交易日
2. `data/state_cube.duckdb`：
   - 表 `state_cube`
   - 列：`symbol, date, d1_state, w1_state, mn1_state, ...`
   - 已建立 `idx_state_cube_date` 和 `idx_state_cube_symbol`

当真实数据就绪后，重新运行 4 个脚本（去掉 `--synthetic`），将结果写入 `outputs/benchmarks/*_real.jsonl`，作为 Phase 2 性能验收依据。

---

## Risks

1. **Synthetic 数据分布过于均匀**：真实 A 股价格有波动聚集、停牌、涨跌停，向量化路径可能在真实数据上表现不同。
2. **DuckDB 冷启动**：真实 `.duckdb` 文件可能未建立索引，首次查询耗时可能高于 synthetic。
3. **filter_first 启发式不准确**：当前 heuristic（`close < ma_20 * 0.92 OR ma_5 > ma_20 OR ma_5 < ma_10`）在真实策略中可能漏掉部分止损日，需要后续用真实信号密度校准。
4. **Polars API 版本差异**：开发机使用 polars 1.41.2，部分表达式（如 `cum_sum`）在不同版本中名称可能变化，需要锁定版本。

---

## Next Steps For Codex

1. **集成 benchmark 到 CI**：在 Phase 2 回测引擎开发完成后，将 `light_backtest_perf.py` 纳入 CI，确保每次代码变更后 P95 < 30s（全市场 5000 品种）。
2. **真实数据跑基线**：当 `p116_foundation.duckdb` 和 `state_cube.duckdb` 就绪后，Codex 负责运行 4 个 benchmark 并产出 `*_real.jsonl`。
3. **热路径审查**：Codex 在代码审查中强制检查 `backtest/engine.py` 不出现 `apply(lambda row: ...)` 或 Python 级逐行循环。
4. **预计算列 DDL**：Codex 在 Foundation DB 迁移脚本中加入 `ma_5/10/20/60`、`atr_14`、`bb_position`、`volume_ratio`、`adx_14`、`d1/w1/mn1_state`。
5. **State Cube 查询封装**：Codex 在 `tools/state_cube.py` 中实现列白名单 + LRU 缓存，禁止 `SELECT *`。
