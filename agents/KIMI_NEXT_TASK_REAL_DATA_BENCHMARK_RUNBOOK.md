# Kimi Next Task: Real Data Benchmark Runbook And Hot Path Gates

请先读取：

1. `AGENTS.md`
2. `docs/TASK_ALLOCATION.md`
3. `data/research/conversations/agent-runs/2026-06-06-kimi-benchmark-scripts.md`
4. `benchmarks/README.md`
5. `benchmarks/light_backtest_perf.py`
6. `benchmarks/_synthetic.py`
7. `data/research/conversations/decisions/0002-kimi-performance-data-architecture.md`

## 背景

Kimi 已交付 benchmark 脚本，Codex 已复核通过，并修复了 synthetic DuckDB 临时文件并行锁冲突。

下一步需要把 benchmark 从“脚本可运行”推进到“真实数据可验收”的 runbook 和门槛。

## 你的任务

请交付真实数据 benchmark runbook、数据体检脚本设计、Phase 2 热路径验收门槛。

## 必须输出

### 1. 真实数据 runbook

请写清楚当以下文件就绪时如何运行：

- `data/p116_foundation.duckdb`
- `data/state_cube.duckdb`

必须包括：

- 前置检查。
- 表名检查。
- 列名检查。
- 行数检查。
- 日期覆盖检查。
- 索引检查。
- benchmark 命令。
- 输出文件命名规范。
- 如何判断结果是否可用于 Phase 2 验收。

### 2. 数据体检脚本规格

请设计但不要必须实现：

`benchmarks/validate_real_data.py`

要求输出 JSON：

- `ok`
- `db_path`
- `table_checks`
- `column_checks`
- `row_count`
- `date_min`
- `date_max`
- `symbol_count`
- `missing_required_columns`
- `index_checks`
- `warnings`
- `errors`

### 3. Phase 2 hot path gates

请定义工程验收门槛：

- Light Backtest 5000 × 252 P95 目标。
- 数据加载耗时上限。
- signal generation 耗时上限。
- metrics 耗时上限。
- 内存峰值观察方式。
- 禁止的代码模式。

禁止模式至少包括：

- `apply(lambda row`
- `iterrows`
- `for row in`
- pandas 中间转换
- `SELECT *` in hot path

### 4. CI/本地验收建议

请区分：

- 每次提交跑 synthetic smoke。
- 每日/手动跑真实数据 benchmark。
- 哪些输出进 Git，哪些只保留在 `outputs/benchmarks/`。

### 5. 对现有 benchmark 脚本的改进建议

请审查当前脚本设计，输出最多 8 条改进建议。必须区分：

- 立即改。
- Phase 2 再改。
- 不需要改。

重点关注：

- synthetic 数据是否过于理想。
- `filter_first` 是否可能漏掉止损日。
- benchmark 是否能拆分 data_load / signal_gen / metrics。
- 是否需要 `--runs`、`--symbols`、`--days` 参数。

## 输出文件

请写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-real-data-benchmark-runbook.md`

## 输出格式

```markdown
# Real Data Benchmark Runbook

## Preconditions

## Data Validation

## Benchmark Commands

## Phase 2 Hot Path Gates

## CI And Local Policy

## Script Improvement Recommendations

## Risks

## Next Steps For Codex
```

## 不做什么

- 不承诺 synthetic 性能等于真实性能。
- 不做 GPU、多机、Dask。
- 不改 DSL。
- 不做真实交易。
