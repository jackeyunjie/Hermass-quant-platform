# Kimi Next Task: Phase 2 Real Data And Performance Gates

你是 Hermass AI Quant Platform 的 Kimi Research Engineer（数据与性能方向）。本任务把当前 benchmark 资产推进到 Phase 2 真实数据 readiness / performance gates，供 Codex 和 Qoder 直接落实现实回测任务。

## Verdict

**MIXED: freeze MVP mock/stub, supplement real-data contract, refresh real datasets, defer source replacement.**

- MVP mock preview / `light_stub` 验收继续冻结，不因真实数据缺口阻塞。
- Phase 2 real backtest、邀请制试点升级项和 public beta 必须先通过真实数据契约、数据体检和 hot path gates。
- 不把“换数据源”作为默认答案；当前按 `freeze` / `refresh` / `supplement` / `replace` / `defer` 分类推进。

## Current Benchmark Capability Inventory

| 脚本 | 当前能力 | 可用于 | 缺口 |
|------|----------|--------|------|
| `benchmarks/validate_real_data.py` | 检查 DB 存在、`daily_bars` / `state_cube` 表、必需列、行数、symbol 数、日期跨度、State Cube 索引 | 真实 benchmark 前置体检 | 未校验字段类型、唯一键、交易日覆盖、freshness、复权口径、停牌/退市、涨跌停一致性、行业时点、future leakage、license 元数据 |
| `benchmarks/light_backtest_perf.py` | DuckDB 取数 + Polars vectorized signal/equity，`full_polars` vs `filter_first`，输出阶段耗时和 `peak_memory_mb` | 5000 symbols x 252 days hot path smoke / baseline | `filter_first` 仍是启发式，不等价真实持仓区间；未接入 DSL runner；`tracemalloc` 不是 RSS；未输出 gate verdict |
| `benchmarks/indicator_precompute_vs_compute.py` | 对比实时窗口计算 `ma_20` vs 读取预计算列 | 验证预计算收益 | 只覆盖 `ma_20`；未覆盖 `ma_5/10/60`、`volume_ratio`、`atr_14`、`adx_14`、State 字段 |
| `benchmarks/duckdb_vs_polars.py` | DuckDB-only 简单金叉 vs DuckDB load + Polars signal | 引擎分工基准 | 只覆盖入场信号；未覆盖止损/止盈/涨停过滤/行业过滤 |
| `benchmarks/state_cube_query.py` | State Cube `no_cache` / `pruned` / `lru_cache` 查询模式 | State Cube 查询热路径 | `universe_n=None`，未输出 rows scanned；宽表/行业聚合/多周期组合还未覆盖 |
| `benchmarks/_synthetic.py` | 生成 `daily_bars` 与 `state_cube` fixture | CI smoke 和本地快速回归 | 无真实停牌、退市、复权、行业漂移、涨跌停制度差异；不可作为真实性能承诺 |

## Phase 2 Light Backtest Real Data Contract

### Required Tables

| 表 | 存储 | 用途 | 必需性 |
|----|------|------|--------|
| `daily_bars` | `data/p116_foundation.duckdb` | OHLCV、预计算指标、涨跌停/停牌状态 | P0 |
| `state_cube` | `data/state_cube.duckdb` | D1/W1/MN1 state 与 EF 字段 | P0 |
| `stock_info` 或 `market_assets` | `data/market_assets.duckdb` 或 foundation DB | symbol 元数据、行业、上市/退市状态 | P0 for industry filter / survivorship check |
| `adjust_factors` | foundation DB 或独立表 | 复权因子、复权口径追踪 | P0 for real performance |
| `trading_calendar` | foundation DB 或独立表 | 交易日、半日市、休市 | P0 |
| `data_license` 或 metadata JSON | `data/` | 来源、授权、截止日期、口径 | P0 for pilot/public beta |

### Required Fields

`daily_bars` P0 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `symbol` | string | 稳定证券代码，不允许复用歧义 |
| `date` | date | 交易日 |
| `open/high/low/close` | double | 统一复权口径价格；禁止混用 |
| `volume` | double/int | 成交量 |
| `amount` | double | 成交额，建议 P0 supplement |
| `adj_factor` | double | 复权因子，或可通过 `adjust_factors` join 得到 |
| `is_suspended` | bool | 当日停牌，不允许用前收盘填充成可交易 bar |
| `is_limit_up` / `is_limit_down` | bool | A 股涨跌停状态 |
| `limit_up_price` / `limit_down_price` | double | 涨跌停价格，用于成交可行性 |
| `ma_5/ma_10/ma_20/ma_60` | double | P0 均线预计算 |
| `volume_ma_20` / `volume_ratio` | double | 成交量条件 |
| `atr_14` / `bb_position` / `adx_14` | double | P0/P1 指标 |

`state_cube` P0 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `symbol` | string | 与 `daily_bars.symbol` 一致 |
| `date` | date | 与交易日对齐 |
| `d1_state` / `w1_state` / `mn1_state` | string | 当前脚本字段 |
| `state_hex_d1` / `state_hex_w1` / `state_hex_mn1` | string | translator 当前依赖字段，需二选一 alias 兼容 |
| `ef_count` | int | `state_ef_count` 条件依赖 |
| `ef_width` | double | State Cube 分析依赖 |

`stock_info` / `market_assets` P0 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `symbol` | string | 主键 |
| `name` | string | 名称 |
| `exchange` | string | 交易所 |
| `list_date` / `delist_date` | date nullable | 幸存者偏差检查 |
| `industry` | string | 当前行业 |
| `industry_date` 或 `valid_from/valid_to` | date | 行业分类时点，避免未来行业漂移 |
| `is_st` | bool | ST 风险过滤 |

### Date And Sample Scope

| 阶段 | 样本范围 | 最低要求 | 说明 |
|------|----------|----------|------|
| Synthetic smoke | 500 symbols x 120 days | 脚本退出 0、JSONL 有记录 | 不比较性能数字 |
| Real baseline minimum | >=5000 symbols x >=252 trading days | `validate_real_data.py ok=true`，真实 DB 本地 SSD | Phase 2 gate 基线 |
| Public beta readiness | >=5000 symbols x >=3 years | survivorship/freshness/license 通过 | 真实绩效展示前要求 |

复权口径：Phase 2 必须声明 `price_adjustment` 为 `forward_adjusted`、`backward_adjusted` 或 `raw`，并在 validation 输出中记录。未声明时 `ok=false`。

停牌处理：停牌日必须用 `is_suspended=true` 或缺行 + `trading_calendar` 可解释，不能把停牌填充为可交易。

涨跌停处理：`is_limit_up/is_limit_down` 必须能支持“买入过滤”和“卖出无法成交”两种语义；当前 MVP 只用了 `limit_up_filter`，Phase 2 real backtest 需补 `is_limit_down`。

行业状态字段：行业过滤若使用 `industry`，Phase 2 至少要有 `industry_date`；public beta 前应改为 `valid_from/valid_to` 时点表。

## `validate_real_data.py` Next Improvements

### P0 Improvements Before Real Baseline

1. 增加 `--min-symbols`、`--min-trading-days`、`--max-staleness-days`、`--as-of-date` 参数。
2. 增加类型检查：`date` 必须可 cast date，OHLCV/指标为 numeric，flag 为 bool/int。
3. 增加唯一性检查：`daily_bars(symbol,date)`、`state_cube(symbol,date)` 不允许重复。
4. 增加 null/range 检查：`close>0`、`high>=low`、`volume>=0`、关键指标非空率。
5. 增加交易日覆盖：按 `trading_calendar` 或 distinct date 检查每个 symbol 缺失率，输出 top offenders。
6. 增加 freshness：输出 `date_max` 与 `as_of_date` 差距，超过阈值时 `ok=false` for pilot/public beta。
7. 增加 schema alias 检查：`state_hex_d1` 与 `d1_state` 至少存在一组，并明确 translator 使用哪组。
8. 增加 metadata 检查：`price_adjustment`、`data_source`、`license_status`、`last_refresh_at`。

### Acceptance Commands

Missing DB negative check:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db /tmp/missing_foundation.duckdb \
  --state-cube-db /tmp/missing_state.duckdb \
  --output outputs/benchmarks/validation_missing.json
```

Expected: exit code `1`, `ok=false`, errors list contains both missing DBs.

Synthetic smoke:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/light_backtest_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/indicator_precompute_vs_compute.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/indicator_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/duckdb_vs_polars.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/duckdb_vs_polars_smoke.jsonl
/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/state_cube_query.py --synthetic --symbols 500 --days 120 --runs 2 --output outputs/benchmarks/state_cube_smoke.jsonl
```

Expected: all exit `0`, each JSONL has at least one row, `data_source="synthetic"`.

Real baseline:

```bash
DATE_TAG=$(date +%Y%m%d)

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --output outputs/benchmarks/real_data_validation_${DATE_TAG}.json

/Users/lv111101/.pyenv/versions/3.11.12/bin/python benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 5000 --days 252 --runs 5 \
  --output outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl
```

Expected: validation `ok=true`; `light_backtest_perf` output contains `universe_n=5000`, `days>=252`, `data_source="real"`, and gate fields.

## Hot Path Gates

### Synthetic Smoke

| Gate | Threshold | Failure action |
|------|-----------|----------------|
| All 4 benchmark scripts exit 0 | required | block benchmark script changes |
| JSONL rows present | required | block benchmark script changes |
| No hot-path forbidden patterns in benchmark scripts | required | block benchmark script changes |
| Performance numbers | informational only | do not block |

### Real Baseline: 5000 Symbols x 252 Trading Days

| Metric | Threshold | Scope |
|--------|-----------|-------|
| Light Backtest total P50 | < 20s | `mode=full_polars`, real data |
| Light Backtest total P95 | < 30s | `mode=full_polars`, real data |
| Data load P95 | < 10s | DuckDB query + Arrow/Polars transfer |
| Signal generation P95 | < 12s | Polars vectorized expressions |
| Equity + metrics P95 | < 8s | portfolio curve and core metrics |
| Peak memory | < 4GB RSS preferred; `tracemalloc` as fallback | local benchmark machine |
| Failure rate | 0/5 runs fail | real baseline gate |
| Data validation | `ok=true`, 0 errors | required before benchmark is accepted |

Gate rule: real baseline failure blocks Phase 2 real backtest release, invitation pilot upgrade to real metrics, GitHub demo with real metrics, and public beta. It does not block Phase 0/1 MVP mock/stub acceptance.

Forbidden hot-path patterns:

- `apply(lambda row`
- `iterrows`
- `for row in`
- `.to_pandas()` in signal/equity path
- `SELECT *`
- Python-level group loop by symbol
- `eval` / `exec`

## Risk Checklist

| 风险 | 阶段影响 | Gate |
|------|----------|------|
| 数据 freshness 过旧 | 试点/公开展示会误导 | `date_max` + metadata `last_refresh_at`; pilot max staleness 30 calendar days, public beta max 7 days |
| 幸存者偏差 | 真实绩效虚高 | `stock_info.list_date/delist_date`，回测 universe 必须按 date 过滤 |
| Future leakage | 信号提前使用未来数据 | 指标预计算必须只使用 `ROWS BETWEEN N PRECEDING AND CURRENT ROW`；行业/成分股使用 valid range |
| 复权口径混用 | 收益曲线错误 | metadata `price_adjustment` 必填；`adj_factor` 可追溯 |
| 停牌/退市处理缺失 | 交易不可执行 | `is_suspended`、`delist_date`、缺行解释必须存在 |
| 涨跌停成交约束缺失 | 入场/出场乐观 | `is_limit_up/is_limit_down` + limit price 字段 |
| 行业分类漂移 | 行业过滤使用未来信息 | `industry_date` 或 `valid_from/valid_to` |
| License 不明确 | 对外风险 | `license_status=approved_for_research/pilot/public`；未批准只能本地研究 |
| Mock/stub 被误解 | 试点合规风险 | UI 和报告必须标注 `light_stub` / `synthetic` / `mock` |

## Tasks For Codex

1. 扩展 `benchmarks/validate_real_data.py` P0 检查项，并为缺失 DB、重复键、缺失 metadata 增加最小测试或 fixture。
2. 增加一个 gate summary 脚本或模式：读取 `real_data_validation_*.json` 与 `light_backtest_real_*.jsonl`，输出 `pass/fail` 和失败阈值。
3. 对 `benchmarks/*.py` 做静态 hot-path grep，至少在 run note 中记录结果。
4. 真实 DB 就绪后执行 real baseline 命令，输出只保留在 `outputs/benchmarks/`，不要提交。
5. 更新 Obsidian run note 和 `PROJECT_INDEX.md`（如项目纪律要求新增索引）。

## Tasks For Qoder

1. 在 Phase 2 real backtest API 设计中加入 `DataReadinessStatus`：
   - `validation_ok`
   - `data_source`
   - `price_adjustment`
   - `date_min/date_max`
   - `freshness_days`
   - `license_status`
   - `benchmark_gate_status`
2. 明确 DSL condition 到数据字段的 alias 策略，尤其是 `state_hex_d1` vs `d1_state`、`close_d1` vs `close`。
3. 定义 real backtest 返回结构必须包含：
   - `mode="light_real"`
   - `data_cutoff_date`
   - `data_quality_flags`
   - `benchmark_gate_snapshot`
   - `audit_trace_id`

## GitHub / Obsidian Handoff

### Files To Commit

- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-data-perf-gates.md`

If Codex later implements code changes, also commit:

- `benchmarks/validate_real_data.py`
- related benchmark tests / fixtures
- `benchmarks/README.md` if command docs change
- `data/research/conversations/PROJECT_INDEX.md` if updated

### Files Not To Commit

- `outputs/benchmarks/*.jsonl`
- `outputs/benchmarks/*.json`
- `outputs/benchmarks/*.duckdb`
- `data/*.duckdb`
- credentials, token files, raw vendor data, cache directories

### Suggested Commit Message

```text
[kimi] research: phase2 real data and performance gates

- Add Phase 2 real data contract for Light Backtest
- Inventory current benchmark scripts and gaps
- Define validate_real_data next checks and acceptance commands
- Define synthetic smoke vs real baseline hot path gates
- Add data freshness, survivorship, leakage, license risk checklist

验收: N/A (research handoff; executable commands included)
```

## Explicit Non-Goals

- 不更换默认数据源。
- 不删除、迁移或重建现有 DuckDB。
- 不阻塞 Phase 0/1 MVP mock preview 和 `light_stub` 验收。
- 不把 synthetic benchmark 当真实性能承诺。
- 不引入 GPU、多机、Dask、Ray 或外部在线服务。
- 不允许执行用户/LLM 生成的 Python 策略代码。
- 不承诺 public beta readiness，直到真实数据、合规、license、性能 gate 全部通过。
