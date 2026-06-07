# Real Data Benchmark Runbook

> 日期：2026-06-06  
> 任务来源：`agents/KIMI_NEXT_TASK_REAL_DATA_BENCHMARK_RUNBOOK.md`  
> 执行人：Kimi Research Engineer

---

## Preconditions

真实数据 benchmark 运行前，必须满足以下前置条件：

1. 数据库文件存在：
   - `data/p116_foundation.duckdb`
   - `data/state_cube.duckdb`
2. Python 环境：
   - `/Users/lv111101/.pyenv/versions/3.11.12/bin/python`
   - 已安装 `duckdb>=1.5`、`polars>=1.41`、`pyarrow>=24.0`
3. 硬件基准（当前开发机）：
   - Apple Silicon M2 Max / 32GB RAM
   - SSD 本地存储
   - 关闭其他大型进程（避免内存/CPU 抖动）
4. 项目目录：
   - 所有命令在仓库根目录执行。
   - `outputs/benchmarks/` 目录可写。

---

## Data Validation

在跑 benchmark 之前，必须先跑数据体检。体检通过是 benchmark 结果被采纳为 Phase 2 验收依据的必要条件。

### 体检脚本规格：`benchmarks/validate_real_data.py`

**作用**：验证真实 DuckDB 是否满足 benchmark 和 Phase 2 回测引擎的最低数据要求。

**命令行接口**：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/real_data_validation.json
```

**输出 JSON 结构**：

```json
{
  "ok": true,
  "foundation_db": "data/p116_foundation.duckdb",
  "state_cube_db": "data/state_cube.duckdb",
  "timestamp": "2026-06-06T18:00:00Z",
  "python_version": "3.11.12",
  "platform": "macOS-...",
  "foundation": {
    "table_checks": {
      "daily_bars": {
        "exists": true,
        "row_count": 1260000,
        "symbol_count": 5000,
        "date_min": "2024-01-02",
        "date_max": "2024-12-31",
        "trading_days": 252
      }
    },
    "column_checks": {
      "daily_bars": {
        "symbol": true,
        "date": true,
        "open": true,
        "high": true,
        "low": true,
        "close": true,
        "volume": true,
        "ma_5": true,
        "ma_10": true,
        "ma_20": true,
        "ma_60": true,
        "atr_14": true,
        "bb_position": true,
        "volume_ratio": true,
        "adx_14": true,
        "is_limit_up": true
      }
    },
    "missing_required_columns": [],
    "index_checks": {},
    "warnings": ["table daily_bars has no explicit primary key"]
  },
  "state_cube": {
    "table_checks": {
      "state_cube": {
        "exists": true,
        "row_count": 1260000,
        "symbol_count": 5000,
        "date_min": "2024-01-02",
        "date_max": "2024-12-31",
        "trading_days": 252
      }
    },
    "column_checks": {
      "state_cube": {
        "symbol": true,
        "date": true,
        "d1_state": true,
        "w1_state": true,
        "mn1_state": true
      }
    },
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

**检查项与通过标准**：

| 检查项 | 通过标准 | 失败处理 |
|--------|----------|----------|
| 数据库文件存在 | `os.path.exists` 为真 | 报错，不继续跑 benchmark |
| 表存在 | `daily_bars` / `state_cube` 存在 | 报错，记录缺失表名 |
| 必需列 | Foundation 16 列，State Cube 5 列全部存在 | 报错，列出缺失列 |
| 行数 | `daily_bars` >= 1,000,000；`state_cube` >= 1,000,000 | 警告，benchmark 仍可跑但结果标注 "low_volume" |
| 品种数 | `daily_bars` >= 5000 个不同 symbol | 警告 |
| 日期覆盖 | 至少 240 个交易日（约一年） | 警告 |
| 索引 | `state_cube` 必须有 `idx_state_cube_date` 和 `idx_state_cube_symbol` | 警告，建议立即建索引 |

**`ok=true` 的判定**：

- `errors` 列表为空。
- 所有 "报错" 级别的检查通过。
- 警告级别的项目不影响 `ok`，但必须在 runbook 日志中记录。

---

## Benchmark Commands

### 1. 数据体检

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/real_data_validation_$(date +%Y%m%d).json
```

如果 `ok=false`，停止后续 benchmark，先修复数据。

### 2. 真实数据 benchmark

```bash
DATE_TAG=$(date +%Y%m%d)

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --output outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py \
  --db-path data/p116_foundation.duckdb \
  --output outputs/benchmarks/indicator_precompute_vs_compute_real_${DATE_TAG}.jsonl

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py \
  --db-path data/p116_foundation.duckdb \
  --output outputs/benchmarks/duckdb_vs_polars_real_${DATE_TAG}.jsonl

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py \
  --db-path data/state_cube.duckdb \
  --output outputs/benchmarks/state_cube_query_real_${DATE_TAG}.jsonl
```

### 3. 输出文件命名规范

| 脚本 | synthetic 输出 | 真实数据输出 |
|------|----------------|--------------|
| `light_backtest_perf.py` | `light_backtest_synthetic_YYYYMMDD.jsonl` | `light_backtest_real_YYYYMMDD.jsonl` |
| `indicator_precompute_vs_compute.py` | `indicator_precompute_vs_compute_synthetic_YYYYMMDD.jsonl` | `indicator_precompute_vs_compute_real_YYYYMMDD.jsonl` |
| `duckdb_vs_polars.py` | `duckdb_vs_polars_synthetic_YYYYMMDD.jsonl` | `duckdb_vs_polars_real_YYYYMMDD.jsonl` |
| `state_cube_query.py` | `state_cube_query_synthetic_YYYYMMDD.jsonl` | `state_cube_query_real_YYYYMMDD.jsonl` |

### 4. 结果是否可用于 Phase 2 验收

必须同时满足：

1. `validate_real_data.py` 输出 `ok=true`。
2. `light_backtest_perf.py` 在 `universe_n=5000`、`days=252`、`mode=full_polars` 条件下，`p95_s < 30s`。
3. `light_backtest_perf.py` 数据加载阶段（见改进建议）`elapsed_load_s < 10s`。
4. 热路径无禁止代码模式（见 Phase 2 Hot Path Gates）。
5. benchmark 输出文件按命名规范落盘。

任一条件不满足，Phase 2 验收不通过。

---

## Phase 2 Hot Path Gates

### 性能目标

| 阶段 | 指标 | 目标 | 测量方式 |
|------|------|------|----------|
| 总耗时 | Light Backtest 5000×252 P95 | **< 30s** | `light_backtest_perf.py` 重复 5 次以上 |
| 数据加载 | DuckDB 查询 + Arrow 传输 P95 | **< 10s** | 在 benchmark 脚本内拆分阶段计时 |
| 信号生成 | Polars 表达式计算 P95 | **< 12s** | 在 benchmark 脚本内拆分阶段计时 |
| 权益曲线+指标 | Polars groupby + cumprod P95 | **< 8s** | 在 benchmark 脚本内拆分阶段计时 |
| 内存峰值 | 5000×252 全量加载 + 中间列 | **< 4GB** | 使用 `tracemalloc` 或 `/usr/bin/time -l` |

### 内存观察方式

推荐在 benchmark 脚本中可选开启：

```python
import tracemalloc

tracemalloc.start()
# ... run benchmark ...
current, peak = tracemalloc.get_traced_memory()
print(f"peak_memory_mb={peak / 1024 / 1024:.1f}")
```

本地也可以用：

```bash
/usr/bin/time -l python benchmarks/light_backtest_perf.py --db-path data/p116_foundation.duckdb
# 查看 "maximum resident set size"
```

### 禁止的代码模式

以下模式出现在 `backtest/engine.py`、`backtest/metrics.py`、`backtest/dsl_runner.py` 的热路径中，**直接判定 Phase 2 验收不通过**：

| 模式 | 示例 | 风险 |
|------|------|------|
| `apply(lambda row: ...)` | `df.apply(lambda row: compute_signal(row), axis=1)` | Python 逐行，性能崩塌 |
| `iterrows` | `for idx, row in df.iterrows(): ...` | pandas 逐行循环 |
| `for row in` | `for row in df.rows(): ...` | 逐行访问 |
| pandas 中间转换 | `df.to_pandas()` 后再转回 Polars | 额外拷贝和类型转换开销 |
| `SELECT *` | `SELECT * FROM daily_bars` | 读取不需要的列，浪费 I/O |
| Python 级分组循环 | `for symbol in symbols:` 内再跑 Polars | 破坏向量化，增加 overhead |
| 动态 `eval` / `exec` | 执行 LLM 或用户生成的代码 | 安全红线 |

### 白名单操作

热路径允许：

- Polars `with_columns`、`filter`、`group_by`、`over`、`shift`、`cum_sum`、`rolling_mean` 等向量化表达式。
- DuckDB `SELECT` 明确列名 + `WHERE` 过滤 + 窗口函数。
- Arrow 零拷贝：`con.execute(...).pl()`。

---

## CI And Local Policy

### 每次提交（CI / pre-commit）

- 运行 synthetic smoke：

```bash
make benchmark-smoke
# 或
python benchmarks/light_backtest_perf.py --synthetic --output /tmp/light_backtest_smoke.jsonl
python benchmarks/indicator_precompute_vs_compute.py --synthetic --output /tmp/indicator_smoke.jsonl
python benchmarks/duckdb_vs_polars.py --synthetic --output /tmp/duckdb_vs_polars_smoke.jsonl
python benchmarks/state_cube_query.py --synthetic --output /tmp/state_cube_smoke.jsonl
```

- 验收：每个脚本正常退出且 JSONL 至少 1 行。
- **不比较性能数字**，只验证脚本可运行。
- 运行时间限制：单脚本 < 5 分钟（synthetic 通常在 30 秒内）。

### 每日/手动真实数据 benchmark

- 触发条件：
  - 每日数据更新后（ETL 完成后）。
  - Phase 2 开发关键节点（ Codex 手动触发）。
  - 重大代码变更后（如 `backtest/engine.py` 重构）。
- 流程：先 `validate_real_data.py`，再跑 4 个 benchmark。
- 输出保存到 `outputs/benchmarks/`。
- 保留最近 30 天 JSONL；旧文件归档到 `outputs/benchmarks/archive/`。

### Git 管理策略

- **提交到 Git**：
  - `benchmarks/*.py`
  - `benchmarks/README.md`
  - `data/research/conversations/agent-runs/2026-06-06-kimi-real-data-benchmark-runbook.md`
- **不提交到 Git**：
  - `outputs/benchmarks/*.jsonl`
  - `outputs/benchmarks/*.duckdb`
  - `outputs/benchmarks/archive/`
- 确保 `.gitignore` 包含：

```gitignore
outputs/benchmarks/*.jsonl
outputs/benchmarks/*.duckdb
outputs/benchmarks/archive/
```

---

## Script Improvement Recommendations

### 立即改（MVP / Phase 2 之前）

1. **拆分 benchmark 阶段计时**
   - 在 `light_backtest_perf.py` 中拆分 `data_load_s`、`signal_gen_s`、`equity_metrics_s`。
   - 当前只记录总耗时，无法验证 Hot Path Gates 中的分项预算。
   - 改动小，价值大。

2. **增加 `--symbols` 和 `--days` CLI 参数**
   - 当前 universe 和 days 在脚本内硬编码（500/2000/5000 和 252）。
   - 增加 `--symbols 1000 --days 120` 便于快速验证和小规模调试。

3. **统一 `--runs` / `--repeats` 参数命名**
   - `light_backtest_perf.py` 和 `duckdb_vs_polars.py` 用 `--repeats`，`state_cube_query.py` 没有重复次数参数。
   - 建议统一为 `--runs`，默认值 5，所有 benchmark 脚本都支持。

4. **`filter_first` 启发式替换为真实信号过滤**
   - 当前 heuristic（`close < ma_20 * 0.92 OR ma_5 > ma_20 OR ma_5 < ma_10`）可能漏掉止损日。
   - 短期改进：在 DuckDB 中先用 SQL 计算 `entry_signal` 和 `exit_ma_signal`，Polars 只加载这些信号日 + 持仓区间。
   - 这样 `filter_first` 才有真实的性能意义。

### Phase 2 再改（功能增强）

5. **增强 synthetic 数据的真实性**
   - 当前 synthetic 是均匀随机 walk，没有停牌、跳空、涨跌停聚集。
   - Phase 2 可以在 `_synthetic.py` 中加入：随机停牌日（缺失行）、涨停日聚类、收益波动聚集。
   - 这有助于验证向量化逻辑对真实边界的处理能力。

6. **在 `duckdb_vs_polars.py` 中加入复杂出场模式**
   - 当前只对比简单 MA 金叉信号。
   - Phase 2 增加 `trailing_stop` 模式，验证复杂出场逻辑下 Polars 的优势。

7. **`state_cube_query.py` 支持宽表模式**
   - 当前 synthetic state_cube 只有 9 列；真实 State Cube 可能扩展到数十列。
   - Phase 2 增加 `--wide` 模式（例如 50 列），更真实对比 `SELECT *` 和列裁剪。

### 不需要改

8. **不引入 GPU / 多机 / Dask**
   - 当前项目约束明确排除分布式方案。
   - 保持 benchmark 聚焦在单节点 DuckDB + Polars，不做过度设计。

---

## Risks

1. **真实数据 I/O 抖动**：DuckDB 文件若存放于网络磁盘或未建立索引，数据加载可能超过 10s 预算。
2. **`filter_first` 替换后收益不确定**：真实信号密度可能高于 synthetic，导致过滤收益变小甚至为负。
3. **停牌导致向量化逻辑异常**：真实数据中存在缺失交易日， Polars `shift(1).over("symbol")` 会把相邻交易日当作连续，可能产生伪信号。需要 data validation 中加入 "无跳空缺失" 检查或回测引擎中处理停牌。
4. **Polars 版本升级破坏 API**：`cum_sum` / `rolling_mean` 等 API 可能在新版本中变化。建议锁定 `polars==1.41.2` 在 `pyproject.toml`。
5. **真实数据 benchmark 被手动选择性运行**：如果只在 synthetic 上跑 CI，可能遗漏真实数据性能退化。必须将真实数据 benchmark 纳入每周至少一次的手动/定时流程。

---

## Next Steps For Codex

1. **实现 `benchmarks/validate_real_data.py`**：按本 runbook 的 JSON 规格实现，并在真实数据就绪后第一时间跑通。
2. **改进现有 benchmark 脚本的 "立即改" 项**：
   - 拆分 `light_backtest_perf.py` 阶段计时。
   - 增加 `--symbols`、`--days`、`--runs` 参数。
   - 修正 `filter_first` 为真实信号过滤。
3. **在 `.gitignore` 中排除 `outputs/benchmarks/*.jsonl` 和 `.duckdb`**。
4. **在 CI / Makefile 中加入 `benchmark-smoke` 目标**：仅 synthetic，验证脚本可运行。
5. **在 `backtest/engine.py` 开发完成后，跑真实数据 benchmark 并归档 `*_real_YYYYMMDD.jsonl`**。
6. **执行 Phase 2 Hot Path Gates 审查**：检查热路径中无禁止模式，并锁定 Polars/DuckDB 版本。
