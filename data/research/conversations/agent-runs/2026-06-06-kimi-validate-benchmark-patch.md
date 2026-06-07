# Kimi Validate And Benchmark Patch

> 日期：2026-06-06  
> 任务来源：`agents/KIMI_NEXT_TASK_VALIDATE_AND_BENCHMARK_PATCH.md`  
> 执行人：Kimi Research Engineer

---

## Implemented Files

| 文件 | 说明 |
|------|------|
| `benchmarks/validate_real_data.py` | **新增**。数据体检脚本，验证 Foundation DB 和 State Cube 的表、列、行数、日期覆盖、索引。 |
| `benchmarks/light_backtest_perf.py` | **修改**。新增 `--runs`/`--symbols`/`--days` 参数；拆分 `data_load_s` / `signal_gen_s` / `equity_metrics_s` / `peak_memory_mb`；移除硬编码日期范围。 |
| `benchmarks/indicator_precompute_vs_compute.py` | **修改**。新增 `--runs`/`--symbols`/`--days` 参数；支持多轮重复输出。 |
| `benchmarks/duckdb_vs_polars.py` | **修改**。新增 `--runs`/`--symbols`/`--days` 参数；统一使用 `args.days` 输出。 |
| `benchmarks/state_cube_query.py` | **修改**。新增 `--runs`/`--symbols`/`--days` 参数；支持多轮重复查询集。 |
| `benchmarks/README.md` | **修改**。加入 validate 使用方式、统一 CLI 参数说明、分阶段计时字段说明、Phase 2 hot path gates。 |

---

## Validation Commands

以下验收命令全部通过：

```bash
# 1. 缺失 DB 验证（ok=false，正常写 JSON，预期退出码为 1）
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db /tmp/missing_foundation.duckdb \
  --state-cube-db /tmp/missing_state.duckdb \
  --output outputs/benchmarks/validation_missing.json

# 2. Synthetic smoke（小数据量快速验证）
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py \
  --synthetic --symbols 500 --days 120 --runs 2 \
  --output outputs/benchmarks/light_backtest_smoke.jsonl

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py \
  --synthetic --symbols 500 --days 120 --runs 2 \
  --output outputs/benchmarks/indicator_smoke.jsonl

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py \
  --synthetic --symbols 500 --days 120 --runs 2 \
  --output outputs/benchmarks/duckdb_vs_polars_smoke.jsonl

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py \
  --synthetic --symbols 500 --days 120 --runs 2 \
  --output outputs/benchmarks/state_cube_smoke.jsonl
```

---

## JSON Output Shape

### validate_real_data.py

```json
{
  "ok": true,
  "foundation_db": "...",
  "state_cube_db": "...",
  "timestamp": "2026-06-06T...",
  "python_version": "3.11.12",
  "platform": "macOS-...",
  "foundation": {
    "table_checks": {"daily_bars": {"exists": true, "row_count": 1260000, ...}},
    "column_checks": {"symbol": true, "ma_5": true, ...},
    "missing_required_columns": [],
    "index_checks": {},
    "warnings": []
  },
  "state_cube": {
    "table_checks": {"state_cube": {"exists": true, ...}},
    "column_checks": {"d1_state": true, ...},
    "missing_required_columns": [],
    "index_checks": {
      "idx_state_cube_date": {"exists": true, "columns": ["date"]},
      "idx_state_cube_symbol": {"exists": true, "columns": ["symbol"]}
    },
    "warnings": []
  },
  "errors": []
}
```

### light_backtest_perf.py（新增字段）

```json
{
  "elapsed_s": 0.041886,
  "data_load_s": 0.015878,
  "signal_gen_s": 0.002023,
  "equity_metrics_s": 0.023985,
  "peak_memory_mb": 0.02,
  "p50_s": 0.035755,
  "p95_s": 0.041886
}
```

---

## Benchmark Changes

| 改动 | 影响文件 | 说明 |
|------|----------|------|
| `--runs` 参数 | 全部 4 个 benchmark | 统一重复次数，默认 5 |
| `--symbols` 参数 | 全部 4 个 benchmark | 支持逗号分隔（如 `500,2000,5000`）或单值，用于 synthetic 数据规模 |
| `--days` 参数 | 全部 4 个 benchmark | synthetic 数据天数，默认 252 |
| 分阶段计时 | `light_backtest_perf.py` | `data_load_s` + `signal_gen_s` + `equity_metrics_s` |
| 内存峰值 | `light_backtest_perf.py` | `peak_memory_mb` 通过 `tracemalloc` 测量 |
| 移除硬编码日期 | `light_backtest_perf.py`、`duckdb_vs_polars.py` | SQL 不再限制 `2024-01-01` 到 `2024-12-31`，加载所选 symbol 的全部数据 |

---

## Risks

1. **validate_real_data.py 使用 `duckdb_indexes()`**：DuckDB 旧版本可能不支持此函数。当前开发机使用 duckdb 1.5.3，已验证通过。如后续升级导致 API 变化，需同步更新。
2. **tracemalloc 仅测量 Python 堆**：`peak_memory_mb` 未包含 DuckDB 原生 C 层内存。若需精确总内存，需改用 `/usr/bin/time -l` 外部测量。
3. **state_cube_query.py `--runs` 含义**：每次 run 重新生成 50 个随机查询，总记录数 = runs × queries × modes。runs=5 时输出 750 行，文件较大但仍在可控范围。
4. **indicator_precompute_vs_compute.py 的 `--symbols` 仅影响 synthetic**：真实数据模式下，该脚本始终扫描全表，不限制 symbol 数量。

---

## Next Steps For Codex

1. **将 validate 集成到真实数据 pipeline**：ETL 完成后自动跑 `validate_real_data.py`，`ok=false` 时阻塞后续 benchmark。
2. **在 CI 中启用 synthetic smoke**：每次提交跑 4 个 benchmark 的 `--synthetic --symbols 500 --days 120 --runs 1`，确保脚本不崩溃。
3. **真实数据就绪后跑完整 benchmark**：使用默认参数 `--symbols 500,2000,5000 --days 252 --runs 5`，产出 `*_real_YYYYMMDD.jsonl`。
4. **审查 backtest/engine.py 热路径**：对照 hot path gates，确保无禁止模式。
5. **锁定依赖版本**：在 `pyproject.toml` 中固定 `duckdb==1.5.3` 和 `polars==1.41.2`。
