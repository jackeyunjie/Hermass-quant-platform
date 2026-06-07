# Kimi Next Task: Benchmark Scripts And Baseline

请先读取：

1. `AGENTS.md`
2. `docs/TASK_ALLOCATION.md`
3. `data/research/conversations/decisions/0002-kimi-performance-data-architecture.md`
4. `data/research/conversations/agent-runs/2026-06-06-kimi-research-engineer-priority-questions.md`
5. `hermass_platform/strategy_lab/condition_translator.py`

## 背景

Kimi 已完成性能与数据架构研究，项目已采纳：

- DuckDB 负责数据加载、列裁剪、预计算指标读取、可选 `filter_first`。
- Polars 负责信号生成、权益曲线和绩效指标。
- Benchmark 结果必须写入 `outputs/benchmarks/` 的 JSONL 文件。
- 真实数据不可用时，允许先用 synthetic fixture，但必须明确标注不可作为最终性能承诺。

## 你的任务

请实现可运行 benchmark 脚本，不只写方案。

## 必须交付文件

1. `benchmarks/light_backtest_perf.py`
2. `benchmarks/indicator_precompute_vs_compute.py`
3. `benchmarks/duckdb_vs_polars.py`
4. `benchmarks/state_cube_query.py`
5. `benchmarks/README.md`

## 脚本要求

每个脚本必须：

- 支持 `--db-path` 参数。
- 支持 `--synthetic` 参数，在没有真实 DuckDB 时生成临时 synthetic 数据。
- 支持 `--output` 参数，默认写入 `outputs/benchmarks/<script_name>_<date>.jsonl`。
- 输出 JSONL，每行至少包含：
  - `benchmark_name`
  - `mode`
  - `universe_n`
  - `days`
  - `run_index`
  - `elapsed_s`
  - `p50_s`
  - `p95_s`
  - `data_source`: `real` 或 `synthetic`
  - `python_version`
  - `platform`
  - `notes`
- 不得在热路径使用 Python row loop。
- 允许测试脚本中用循环生成 synthetic 数据，但必须与热路径分离。

## 具体 benchmark 目标

### 1. `light_backtest_perf.py`

比较：

- `full_polars`
- `filter_first`

数据规模：

- `symbols=500, 2000, 5000`
- `days=252`
- 每档至少 5 次重复。

策略：

- MA5 上穿 MA20 入场。
- MA5 下穿 MA10 或止损 8% 出场。

### 2. `indicator_precompute_vs_compute.py`

比较：

- 实时窗口计算 `ma_20`
- 读取预计算 `ma_20`

输出：

- 耗时。
- 行数。
- 读/算性能比。

### 3. `duckdb_vs_polars.py`

比较：

- DuckDB-only 简单信号。
- DuckDB load + Polars compute。

说明：

- DuckDB-only 只需要覆盖简单 MA 信号，不要求复杂止损。
- 重点验证分工是否合理。

### 4. `state_cube_query.py`

比较：

- 无缓存查询。
- 列裁剪查询。
- 最近 5 交易日 LRU 缓存查询。

必须验证：

- 禁止 `SELECT *` 的查询路径。
- `date/symbol` 索引存在或给出创建 SQL。

## 输出格式

完成后请写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-benchmark-scripts.md`

内容结构：

```markdown
# Kimi Benchmark Scripts

## Implemented Files

## How To Run

## Synthetic Baseline Results

## Real Data Requirements

## Risks

## Next Steps For Codex
```

## 验收标准

Codex 后续必须能运行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --output outputs/benchmarks/light_backtest_synthetic.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --output outputs/benchmarks/indicator_synthetic.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --output outputs/benchmarks/duckdb_vs_polars_synthetic.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --output outputs/benchmarks/state_cube_synthetic.jsonl
```

并且每个脚本至少生成 1 行 JSONL。

## 不做什么

- 不做 GPU、多机、Dask。
- 不做真实交易。
- 不修改 Strategy DSL。
- 不把 synthetic 结果当作最终性能承诺。
