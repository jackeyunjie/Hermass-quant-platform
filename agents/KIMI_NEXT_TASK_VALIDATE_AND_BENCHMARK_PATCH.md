# Kimi Next Task: Validate Real Data And Benchmark Patch

请先读取：

1. `AGENTS.md`
2. `docs/TASK_ALLOCATION.md`
3. `data/research/conversations/agent-runs/2026-06-06-kimi-real-data-benchmark-runbook.md`
4. `data/research/conversations/decisions/0005-phase2-hot-path-gates.md`
5. `benchmarks/README.md`
6. `benchmarks/light_backtest_perf.py`
7. `benchmarks/indicator_precompute_vs_compute.py`
8. `benchmarks/duckdb_vs_polars.py`
9. `benchmarks/state_cube_query.py`
10. `benchmarks/_synthetic.py`

## 背景

真实数据 benchmark runbook 已被采纳。现在不要再写方案，请直接实现数据体检脚本和 benchmark 立即改项。

## 你的任务

实现以下代码补丁。

## 必须新增/修改文件

### 1. 新增 `benchmarks/validate_real_data.py`

实现 CLI：

```bash
python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/real_data_validation.json
```

输出 JSON 必须包含：

- `ok`
- `foundation_db`
- `state_cube_db`
- `timestamp`
- `python_version`
- `platform`
- `foundation.table_checks`
- `foundation.column_checks`
- `foundation.missing_required_columns`
- `foundation.index_checks`
- `foundation.warnings`
- `state_cube.table_checks`
- `state_cube.column_checks`
- `state_cube.missing_required_columns`
- `state_cube.index_checks`
- `state_cube.warnings`
- `errors`

要求：

- 数据库不存在时 `ok=false`，但脚本正常退出并写 JSON。
- 表/列缺失时 `ok=false`。
- 行数、品种数、交易日不足是 warning，不一定导致 `ok=false`。
- 检查 State Cube 是否存在 date/symbol 索引；缺索引 warning。

### 2. 修改 benchmark 脚本参数

对以下脚本增加统一参数：

- `--runs`，默认 5。
- `--symbols`，默认 `500,2000,5000`，允许传单个或逗号分隔。
- `--days`，默认 252。

适用文件：

- `benchmarks/light_backtest_perf.py`
- `benchmarks/duckdb_vs_polars.py`
- `benchmarks/state_cube_query.py`

`indicator_precompute_vs_compute.py` 至少支持：

- `--runs`
- `--symbols`
- `--days`

### 3. 修改 `light_backtest_perf.py` 分阶段计时

JSONL 每行新增：

- `data_load_s`
- `signal_gen_s`
- `equity_metrics_s`
- `peak_memory_mb`（如果暂时难以精确，允许 `null`，但字段必须存在）

要求：

- 不改变现有必需字段。
- 热路径继续禁止 Python row loop。

### 4. 更新 `benchmarks/README.md`

加入：

- `validate_real_data.py` 使用方式。
- 新 CLI 参数说明。
- synthetic smoke 和 real benchmark 的区别。
- Phase 2 hot path gates。

## 验收命令

Codex 后续必须能运行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py --foundation-db /tmp/missing_foundation.duckdb --state-cube-db /tmp/missing_state.duckdb --output outputs/benchmarks/validation_missing.json
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/light_backtest_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/indicator_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/duckdb_vs_polars_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/state_cube_smoke.jsonl
```

## 不做什么

- 不承诺 synthetic 性能。
- 不改 DSL。
- 不实现 backtest engine。
- 不做 GPU/Dask/多机。
- 不提交 `outputs/benchmarks/*.jsonl`。

## 输出记录

完成后写入：

`data/research/conversations/agent-runs/2026-06-06-kimi-validate-benchmark-patch.md`

格式：

```markdown
# Kimi Validate And Benchmark Patch

## Implemented Files

## Validation Commands

## JSON Output Shape

## Benchmark Changes

## Risks

## Next Steps For Codex
```
