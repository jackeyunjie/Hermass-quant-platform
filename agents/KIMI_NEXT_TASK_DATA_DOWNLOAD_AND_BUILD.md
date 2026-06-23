# Kimi Next Task: 真实数据下载与 DuckDB 构建

你是 Hermass AI Quant Platform 的 Kimi Research Engineer（数据与性能方向）。本轮任务是**实际下载 A 股真实行情数据并构建两个 DuckDB 文件**，不再只做审计和 readiness 判断。

## 必读上下文

- `AGENTS.md`
- `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md` 第 1 节（数据层架构图）
- `docs/design/DATA_FOUNDATION_AND_STATE_CUBE_ARCHITECTURE.md`（三层数据模型）
- `benchmarks/validate_real_data.py`（完整校验逻辑）
- `hermass_platform/strategy_lab/backtest_data_provider.py`（列名规范化 + 必需列）
- `config/factors/source_catalog.yaml`（已声明黑狼为数据源）
- `agents/KIMI2_NEXT_TASK_DATA_REFRESH_REPLACEMENT_AUDIT.md`
- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md`
- `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`

## 总裁决

**Phase 3 Web UI 已落地，主线已切换到真实数据 baseline handoff。本轮必须实际产出 DuckDB 文件，不再停留在审计/判断阶段。**

```text
Kimi 负责：
  -> 选定可用数据源（黑狼优先，AKShare/baostock 备选）
  -> 下载 A 股日线行情
  -> 计算预计算指标
  -> 构建 data/p116_foundation.duckdb
  -> 计算多周期 state_hex
  -> 构建 data/state_cube.duckdb
  -> 跑 validation 并产出 data_readiness_status.json

Codex 负责：
  -> Web UI data readiness 展示位（已完成）
  -> 接收 handoff 后做集成验证
```

---

## 第一阶段：数据源评估与下载

### 1.1 数据源选择

**优先用黑狼（Blackwolf）API**，项目 `source_catalog.yaml` 已将其声明为 A 股行情数据源。

#### 黑狼需要确认

| 检查项 | 问题 |
|--------|------|
| API endpoint | 可用的日线数据接口 URL |
| 认证方式 | token / key / 无需认证 |
| 复权支持 | 前复权 / 后复权 / 不复权 / 复权因子 |
| 可交易标记 | `is_limit_up`、`is_limit_down`、`is_suspended`、`is_st` |
| 调用限制 | 每日调用次数、单次最大 symbol 数、并发限制 |
| 日期范围 | 最早/最新可用日期 |

#### 备选方案（黑狼不可用时按顺序评估）

| 方案 | 安装 | 特点 | 注册门槛 |
|------|------|------|----------|
| AKShare | `pip install akshare` | 免费、A 股全覆盖、前复权/后复权 | 无需注册 |
| baostock | `pip install baostock` | 免费、需登录（免费）、前复权 | 手机号注册 |
| Tushare Pro | `pip install tushare` | 积分制、字段最全 | 需 token + 积分 |

**裁决：黑狼优先。若黑狼不可用，选 AKShare。禁止因数据源选择卡住超过半天。**

### 1.2 下载后的原始数据形态

无论数据源，原始数据写入 `data/raw/` 目录暂存（Parquet 或 CSV），便于复核和重放。最终 DuckDB 构建后该目录可删除。

下载的参数选择：

- 复权方式：**前复权**（`forward_adjusted`）
- 时间范围：**2022-01-01 至最新可用交易日**
- 目标标的数：**全市场 A 股（含北交所），预期 ≥ 5000**

### 1.3 判别的关键质量检查（下载后立即执行）

- `close > 0`，无 NULL 价格
- `high >= low`
- `volume > 0` 或 `volume >= 0`（停牌日可为 0）
- `symbol` 格式统一（如 `000001.SZ`、`600000.SH`）
- `date` 无重复 `(symbol, date)` 对

---

## 第二阶段：构建 `data/p116_foundation.duckdb`

### 2.1 `daily_bars` 表 - 必需列

以下列与 `benchmarks/validate_real_data.py` 中的 `REQUIRED_FOUNDATION_COLUMNS` 完全对齐：

| 列名 | 类型 | 说明 |
|------|------|------|
| `symbol` | VARCHAR | 股票代码，如 `000001.SZ` |
| `date` | DATE | 交易日 |
| `open` | DOUBLE | 开盘价（前复权） |
| `high` | DOUBLE | 最高价（前复权） |
| `low` | DOUBLE | 最低价（前复权） |
| `close` | DOUBLE | 收盘价（前复权） |
| `volume` | BIGINT | 成交量（手） |
| `ma_5` | DOUBLE | 5 日均线 |
| `ma_10` | DOUBLE | 10 日均线 |
| `ma_20` | DOUBLE | 20 日均线 |
| `ma_60` | DOUBLE | 60 日均线 |
| `atr_14` | DOUBLE | 14 日 ATR |
| `bb_position` | DOUBLE | 布林带位置 |
| `volume_ratio` | DOUBLE | 量比（当日量 / 5 日均量） |
| `adx_14` | DOUBLE | 14 日 ADX |
| `is_limit_up` | INTEGER | 是否涨停（1/0） |

### 2.2 `daily_bars` 表 - 可选列（缺失时警告不报错）

| 列名 | 类型 | 说明 |
|------|------|------|
| `is_limit_down` | INTEGER | 是否跌停 |
| `is_suspended` | INTEGER | 是否停牌 |
| `is_st` | INTEGER | 是否 ST |

### 2.3 数据规模硬性要求

| 指标 | 最低值 | 备注 |
|------|--------|------|
| symbol 数 | ≥ 5000 | A 股全市场（含北交所约 5300） |
| 交易日数 | ≥ 252 | 约一年 |
| 建议日期范围 | 2022-01-01 ~ 最新 | 覆盖牛市+熊市 |

### 2.4 预计算指标 SQL（在 DuckDB 内执行，数据导入后）

```sql
-- Step 1: 导入原始 OHLCV 到 daily_bars_raw（仅 symbol, date, open, high, low, close, volume）
-- Step 2: 按 symbol 分区、按 date 排序后计算指标

CREATE TABLE daily_bars AS
SELECT
    symbol,
    date,
    open,
    high,
    low,
    close,
    volume,

    -- 均线
    AVG(close) OVER w5  AS ma_5,
    AVG(close) OVER w10 AS ma_10,
    AVG(close) OVER w20 AS ma_20,
    AVG(close) OVER w60 AS ma_60,

    -- 布林带位置: (close - MA20) / (2 * 20日标准差)
    (close - AVG(close) OVER w20)
        / (2 * STDDEV_POP(close) OVER w20) AS bb_position,

    -- 量比: volume / 5日均量
    volume / NULLIF(AVG(volume) OVER w5, 0) AS volume_ratio,

    -- ATR(14): TR = MAX(high-low, ABS(high-prev_close), ABS(low-prev_close))
    -- 先子查询算 TR，再 14 日均值
    NULL::DOUBLE AS atr_14,

    -- ADX(14): DM+/DM-/TR/DI+/DI-/DX/ADX 完整链
    NULL::DOUBLE AS adx_14,

    -- 涨跌停
    CASE
        WHEN close = prev_high AND close > 0 THEN 1
        ELSE 0
    END AS is_limit_up

FROM (
    SELECT
        *,
        -- 涨停价 = round(prev_close * 1.10, 2)（A 股主板 10%）
        -- 此处仅为示意，实际需要结合昨日收盘价和涨跌幅限制计算
        MAX(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING)
            AS prev_high  -- 简化，实际需要 yesterday close * 1.10
    FROM daily_bars_raw
)
WINDOW
    w5  AS (PARTITION BY symbol ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW),
    w10 AS (PARTITION BY symbol ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW),
    w20 AS (PARTITION BY symbol ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW),
    w60 AS (PARTITION BY symbol ORDER BY date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW);
```

**ATR/ADX 的完整计算较复杂，可以使用 Python 脚本辅助**（参考 `benchmarks/_synthetic.py` 的计算逻辑）。如果计算复杂，MVP 阶段可以先用 `benchmarks/_synthetic.py` 作为参考模板，将 synthetic 数据生成逻辑替换为真实数据.

### 2.5 `data_license` 元数据表（在 DuckDB 内创建）

```sql
CREATE TABLE IF NOT EXISTS data_license (
    key   VARCHAR PRIMARY KEY,
    value VARCHAR
);

INSERT INTO data_license VALUES
    ('price_adjustment', 'forward_adjusted'),
    ('data_source', 'akshare'),             -- 根据实际来源填写
    ('license_status', 'research_only'),
    ('last_refresh_at', '2026-06-19T00:00:00Z'),
    ('date_min', '2022-01-04'),
    ('date_max', '2026-06-18'),
    ('symbol_count', '5300'),
    ('trading_days', '1050');
```

### 2.6 附加索引

```sql
CREATE INDEX IF NOT EXISTS idx_daily_bars_symbol ON daily_bars(symbol);
CREATE INDEX IF NOT EXISTS idx_daily_bars_date ON daily_bars(date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_bars_symbol_date ON daily_bars(symbol, date);
```

---

## 第三阶段：构建 `data/state_cube.duckdb`

### 3.1 `state_cube` 表结构

| 列名 | 类型 | 说明 |
|------|------|------|
| `symbol` | VARCHAR | 股票代码 |
| `date` | DATE | 交易日 |
| `state_hex_d1` | VARCHAR | 日线市场状态 |
| `state_hex_w1` | VARCHAR | 周线市场状态 |
| `state_hex_mn1` | VARCHAR | 月线市场状态 |

`backtest_data_provider.py` 的 `_STATE_COLUMN_ALIASES` 已处理 `state_hex_d1 -> d1_state` 映射，两种列名均可。

可选列（不强校验）：

| 列名 | 类型 | 说明 |
|------|------|------|
| `ef_count` | INTEGER | EF 数量 |
| `ef_width` | DOUBLE | EF 宽度 |
| `resonance_score` | DOUBLE | 多周期共振评分 |

### 3.2 State Hex 计算规则（MVP 简化版）

```python
# D1 state — 基于 20 日均线（需要 ma_20 列）
#   close >  ma_20 且 ma_20 斜率 >  0 → trending_up
#   close >  ma_20 且 ma_20 斜率 <= 0 → topping
#   close <  ma_20 且 ma_20 斜率 <  0 → trending_down
#   close <  ma_20 且 ma_20 斜率 >= 0 → bottoming
#   close == ma_20                    → ranging

# W1 state — 基于 60 日均线，按周重采样后同 D1 逻辑
# MN1 state — 基于 120 日均线，按月重采样后同 D1 逻辑
```

### 3.3 对齐检查

构建完成后自检：

```sql
-- state_cube 的 symbol 必须与 daily_bars 有交集
SELECT COUNT(DISTINCT s.symbol) AS alignment_count
FROM state_cube s
INNER JOIN daily_bars d ON s.symbol = d.symbol AND s.date = d.date;
-- 期望 >= 5000

-- date 覆盖范围
SELECT MIN(date), MAX(date), COUNT(DISTINCT date) FROM state_cube;
```

---

## 第四阶段：校验与产出

### 4.1 运行 `validate_real_data.py`

```bash
DATE_TAG=$(date +%Y%m%d)

uv run python benchmarks/validate_real_data.py \
  --foundation-db data/p116_foundation.duckdb \
  --state-cube-db data/state_cube.duckdb \
  --min-symbols 5000 \
  --min-trading-days 252 \
  --max-staleness-days 30 \
  --as-of-date $(date +%Y-%m-%d) \
  --output outputs/benchmarks/real_data_validation_${DATE_TAG}.json
```

**验收**：exit 0，output JSON 中 `ok=true` 且 `errors=[]`。

### 4.2 产出 `data_readiness_status.json`

基于 validation 输出文件和自检结果，手工构建 readiness JSON。结构完全对齐 `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md` 第 4 节定义。

**verdict 判断**：

| 条件 | verdict |
|------|---------|
| 两个 DB 均存在 + validation pass + `errors=[]` | `READY` |
| DB 存在但 validation 有 warning 或 freshness 超阈值 | `PARTIAL` |
| DB 不存在或 validation 有 error | `NOT_READY` |

### 4.3 跑 performance baseline（仅 validation pass 后）

```bash
DATE_TAG=$(date +%Y%m%d)

uv run python benchmarks/light_backtest_perf.py \
  --db-path data/p116_foundation.duckdb \
  --symbols 5000 \
  --days 252 \
  --runs 5 \
  --output outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl

uv run python benchmarks/gate_summary.py \
  --validation outputs/benchmarks/real_data_validation_${DATE_TAG}.json \
  --benchmark outputs/benchmarks/light_backtest_real_${DATE_TAG}.jsonl \
  --output outputs/benchmarks/gate_summary_${DATE_TAG}.json
```

**验收**：

- `light_backtest_perf.py` exit 0
- JSONL 包含 `data_source="real"` 的记录
- `gate_summary.py` exit 0
- gate summary JSON 中 `ok=true`

---

## 可以做（可选）

以下为额外加分项，不阻塞 baseline：

- `daily_bars` 中新增 `is_limit_down`、`is_suspended`、`is_st`
- `daily_bars` 新增行业列 `industry_sw`（申万一级）
- `state_cube` 新增 `ef_count`、`ef_width`
- 无需额外代码

---

## 明确不做

- 不碰 `web/`、`hermass_platform/strategy_lab/` 代码
- 不修改 `benchmarks/validate_real_data.py` 或其他 benchmark 脚本绕过校验
- 不把 synthetic DB 冒充真实 DB
- 不因数据源选择卡住超过半天——黑狼不可用直接切 AKShare
- 不阻塞 Web UI 或 Strategy Lab
- 不运行真实交易、paper trading、外部服务集成

---

## 本轮执行结果（2026-06-19）

任务已完成，真实数据已刷新至 2026-06-18。

### 数据源

- 黑狼（Blackwolf）API 可用，Hermass 仓库已有最新合并 zip `blackwolf_ashare_daily_mac_format_20180515_20260618.zip`。
- 直接复用该 zip，未触发逐日 API 下载。

### 构建结果

- foundation_db: `data/p116_foundation.duckdb`
- state_cube_db: `data/state_cube.duckdb`
- data_source: `blackwolf_real`
- price_adjustment: `forward_adjusted`
- license_status: `research_only`
- last_refresh_at: `2026-06-19`
- date_min: `2018-05-15`
- date_max: `2026-06-18`
- symbol_count: 5536
- trading_days: 1964
- daily_bars_rows: 8,591,347
- state_cube_rows: 8,591,347
- staleness_days: 0
- validation: ok=true, errors=[]
- readiness verdict: READY

### 性能基线

- `light_backtest_perf` 5000×252 `full_polars`：P50=1.97s, P95=2.12s
- data_load P95=0.18s, signal_gen P95=0.19s, equity_metrics P95=1.76s
- `gate_summary`: PASS（8/8 gates 通过）

### 回归测试

- `pytest hermass_platform/strategy_lab/tests scripts/test_web_ui_smoke.py`：284 passed
- `pytest hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`：8 passed
- `python scripts/run_strategy_lab_mvp_e2e_acceptance.py`：5/5 passed

### 运行摘要

- `data/research/conversations/agent-runs/2026-06-19-kimi-data-download-and-build-run.md`

## 输出物清单

| # | 文件 | 提交 Git |
|---|------|----------|
| 1 | `data/p116_foundation.duckdb` | 否 |
| 2 | `data/state_cube.duckdb` | 否 |
| 3 | `outputs/benchmarks/data_readiness_status.json` | 否 |
| 4 | `outputs/benchmarks/real_data_validation_YYYYMMDD.json` | 否 |
| 5 | `outputs/benchmarks/light_backtest_real_YYYYMMDD.jsonl` | 否 |
| 6 | `outputs/benchmarks/gate_summary_YYYYMMDD.json` | 否 |
| 7 | `agents/KIMI_NEXT_TASK_DATA_DOWNLOAD_AND_BUILD.md`（本文件迭代版） | 是 |
| 8 | `data/research/conversations/agent-runs/2026-06-19-kimi-data-download-and-build-run.md` | 是 |

---

## Handoff 模板（完成后回传 Codex）

```markdown
## Real DB Handoff

- foundation_db: data/p116_foundation.duckdb
- state_cube_db: data/state_cube.duckdb
- data_source: [黑狼 / akshare / baostock / ...]
- price_adjustment: forward_adjusted
- license_status: research_only
- last_refresh_at: YYYY-MM-DD
- date_min: YYYY-MM-DD
- date_max: YYYY-MM-DD
- symbol_count: [number]
- trading_days: [number]
- daily_bars_rows: [number]
- state_cube_rows: [number]
- known_missing_fields: [如果有]
- known_data_limitations: [如果有]
- command_outputs:
  - validate_real_data: [pass/fail，附关键错误]
  - light_backtest_perf: [pass/fail，P50/P95]
  - gate_summary: [pass/fail，未通过的 gate]
```
