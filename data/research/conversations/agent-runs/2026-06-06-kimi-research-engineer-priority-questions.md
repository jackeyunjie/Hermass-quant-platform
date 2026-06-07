# Kimi Research Engineer — 性能/数据/研究执行记录

> 日期：2026-06-06  
> 来源：`agents/KIMI_RESEARCH_ENGINEER_PROMPT.md`  
> 目标：回答优先问题，给出可验证的最小实验设计、基准测试方法、收益/风险/替代方案，并判定是否进入 MVP。

---

## 背景

根据最终实施方案，Phase 2 回测引擎必须在 Light 模式下达到：

- 单策略单品种 252 天 < 5s
- 全市场 5000+ 品种一年 < 30s

同时 State Cube、Foundation DB、产业链 Agent、TS-FM/RAG-KG sandbox 均需要研究结论，且不能阻塞 MVP。

本文件按 `KIMI_RESEARCH_ENGINEER_PROMPT.md` 的 7 项输出要求，逐项回答 5 个优先问题。

---

## Q1. 全市场 5000+ 品种一年 Light Backtest < 30s 是否现实？

### 1. 数据依赖

- `p116_foundation.duckdb`：全部 A 股日 K（约 5000 只 × 252 天 ≈ 126 万行），含 `symbol, date, open, high, low, close, volume`。
- 预计算指标：`ma_5, ma_10, ma_20, ma_60, atr_14, bb_position, volume_ratio`。
- `state_cube.duckdb`：每个品种每个交易日的 `d1_state, w1_state, mn1_state`。
- 硬件基准：Apple Silicon M2 Max / 32GB RAM（当前开发机）。

### 2. 最小实验设计

1. 构造 3 档数据：`symbols=500 / 2000 / 5000`，`days=252`。
2. 策略为 MVP 最简单策略：`MA5 上穿 MA20 买入，MA5 下穿 MA10 或止损 8% 卖出`。
3. 分别测试两条路径：
   - A 路径：DuckDB 取数 → Polars 全量向量化回测。
   - B 路径：DuckDB 先按条件过滤出候选信号日，Polars 只对有信号的 symbol-date 做权益曲线。
4. 每个档位重复 10 次，记录 `total / data_load / signal_gen / equity_curve / metrics` 耗时。

### 3. 性能基准命令 / 伪代码

```python
# benchmarks/light_backtest_perf.py
import time, polars as pl, duckdb
from pathlib import Path

def benchmark(universe_n: int, mode: str) -> dict:
    t0 = time.perf_counter()
    con = duckdb.connect("data/p116_foundation.duckdb")
    df = con.execute(
        f"""
        SELECT symbol, date, open, high, low, close, volume,
               ma_5, ma_10, ma_20, atr_14
        FROM daily_bars
        WHERE symbol IN (SELECT symbol FROM symbols LIMIT {universe_n})
          AND date BETWEEN '2024-01-01' AND '2024-12-31'
        """
    ).pl()
    t1 = time.perf_counter()

    if mode == "full_polars":
        signals = compute_signals_polars(df)
        curve = compute_equity_curve_polars(signals)
    else:
        hits = con.execute(
            "SELECT symbol, date FROM df WHERE ma_5 > ma_20 AND ..."
        ).pl()
        signals = compute_signals_polars(df.join(hits, on=["symbol","date"], how="semi"))
        curve = compute_equity_curve_polars(signals)

    t2 = time.perf_counter()
    return {
        "universe": universe_n,
        "mode": mode,
        "load_s": t1 - t0,
        "compute_s": t2 - t1,
        "total_s": t2 - t0,
    }

if __name__ == "__main__":
    for n in [500, 2000, 5000]:
        for mode in ["full_polars", "filter_first"]:
            times = [benchmark(n, mode)["total_s"] for _ in range(10)]
            print(n, mode, sorted(times)[5], sorted(times)[9])
```

运行：

```bash
python -m venv .venv && source .venv/bin/activate
pip install polars duckdb pyarrow
python benchmarks/light_backtest_perf.py > outputs/benchmarks/light_backtest_20260606.jsonl
```

### 4. 预期收益

- 若 Polars 热路径（`groupby + shift + cumsum`）实现正确，5000×252 的向量计算可在 **5–12s** 完成。
- DuckDB 取数（列裁剪 + Arrow 零拷贝）约 **3–8s**。
- 合计 **10–20s**，**P95 < 30s 现实**。
- `filter_first` 路径可在信号稀疏时进一步降到 **5–10s**。

### 5. 风险

- **数据 I/O 抖动**：DuckDB 冷启动或未建立索引时取数可能 > 15s。
- **向量化被破坏**：一旦出现 `apply(lambda row: ...)` 或 Python 级逐行循环，性能会崩塌到分钟级。
- **内存峰值**：5000 只股票一年全量加载约 200–400MB，加上中间列，内存可能 > 2GB。
- **Walk-Forward 3 折**：如果串行执行，时间会 ×3，必须改为并行或增量。

### 6. 替代方案

| 方案 | 适用场景 | 代价 |
|------|----------|------|
| `filter_first`：DuckDB WHERE 先过滤 | 信号稀疏（< 10% 交易日命中） | 代码复杂度略增 |
| 分块 batch（每次 1000 只） | 内存不足 | 总时间可能增加 20–40% |
| 纯 DuckDB SQL 回测 | 极简单策略 | 复杂出场逻辑（ATR 吊灯、移动止损）难以表达 |
| 异步后台 Full Backtest | Light 超时 | 用户等待变长，需要状态轮询 |

### 7. MVP / backlog 判定

- **进入 MVP**：Polars 热路径实现 + `filter_first` 优化作为 Phase 2 默认实现。
- **进入 backlog**：GPU/多机并行、分布式 Dask 方案在研究 sandbox 中验证，不进入 MVP。

---

## Q2. 哪些指标应该预计算进 Foundation DB？

### 1. 数据依赖

- `condition_registry.py` 中 P0/P1 条件类型：
  - `price_cross_ma`：MA5/10/20/60
  - `ma_golden_cross` / `ma_death_cross`：MA5/10/20/60 交叉
  - `bb_position`：布林带（20,2）
  - `atr_stop`：ATR14
  - `volume_ratio`：成交量 / MA20 成交量
  - `adx_threshold`：ADX14
  - `state_hex_in`：D1/W1/MN1 state_hex
- 策略模板库中高频参数分布（前 5 个模板）。

### 2. 最小实验设计

1. 统计条件注册表中每个指标被引用的次数和参数分布。
2. 在完整历史数据上（约 126 万行）对比两类耗时：
   - 实时 DuckDB/Polars 窗口计算。
   - 直接读取预计算列。
3. 评估存储代价：每增加一列，`.duckdb` 文件增大约多少。

### 3. 性能基准命令 / 伪代码

```python
# benchmarks/indicator_precompute_vs_compute.py
import duckdb, time

con = duckdb.connect("data/p116_foundation.duckdb")

# 基准 1：DuckDB 窗口函数实时算 MA20
start = time.perf_counter()
con.execute("""
    SELECT symbol, date,
           AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma20
    FROM daily_bars
    WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
""").pl()
print("compute ma20", time.perf_counter() - start)

# 基准 2：读预计算列
start = time.perf_counter()
con.execute("""
    SELECT symbol, date, ma_20 FROM daily_bars
    WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
""").pl()
print("read ma20", time.perf_counter() - start)
```

同时测量表大小：

```bash
du -h data/p116_foundation.duckdb
```

### 4. 预期收益

预计算以下列可以命中 80% 的 MVP 策略条件：

| 预计算列 | 理由 | 命中策略条件 |
|----------|------|--------------|
| `ma_5, ma_10, ma_20, ma_60` | 最常用趋势指标 | price_cross_ma / ma_golden_cross / ma_death_cross |
| `bb_position` | 布林带位置 | bb_position |
| `atr_14` | 止损/吊灯 | atr_stop |
| `volume_ratio` | 量价过滤 | volume_ratio |
| `adx_14` | 趋势过滤 | adx_threshold |
| `d1_state, w1_state, mn1_state` | State Cube 核心 | state_hex_in |

- 读取预计算列通常比窗口计算快 **5–20x**。
- 预计算后，Light Backtest 取数阶段减少 **30–50%** 时间。

### 5. 风险

- **Schema 膨胀**：每增加一列，存储增加约 5–10MB（126 万行）。6 列约 30–60MB，可控。
- **参数僵化**：用户可能使用 MA13/MA34 等非标准参数，预计算无法覆盖。
- **更新成本**：每日 ETL 需要重新计算全量指标，耗时增加。

### 6. 替代方案

| 方案 | 说明 |
|------|------|
| 全动态计算 | 不预存任何指标，灵活但慢 |
| 懒加载缓存 | 第一次计算后写入 `.duckdb` 的 `computed_indicators` 表，后续命中 |
| 按策略按需预计算 | 根据用户保存的策略反推所需指标， nightly 预计算 |

### 7. MVP / backlog 判定

- **进入 MVP**：预计算 `ma_5/10/20/60`、`bb_position`、`atr_14`、`volume_ratio`、`adx_14`、`d1/w1/mn1_state`。
- **进入 backlog**：自适应指标缓存、按策略热度动态扩展预计算列。

---

## Q3. DuckDB 与 Polars 在信号生成和权益曲线计算上如何分工？

### 1. 数据依赖

- `p116_foundation.duckdb`：主数据湖，按日期和 symbol 组织。
- `state_cube.duckdb`：多周期状态。
- DSL 条件翻译器输出：DuckDB SQL 或 Polars 表达式。

### 2. 最小实验设计

1. 选择同一策略（MA 金叉买入 + 8% 止损），分别用以下方式实现：
   - A：纯 DuckDB SQL（窗口函数 + CASE + 累计）。
   - B：纯 Polars（从 Parquet/CSV 加载）。
   - C：DuckDB 取数 + Polars 计算（推荐分工）。
2. 在 500/2000/5000 品种上运行，对比：
   - 总耗时
   - 峰值内存
   - 代码可维护性（出场逻辑复杂度）
3. 在出场逻辑加入 ATR 吊灯 trailing stop 后，再看三种方案复杂度差异。

### 3. 性能基准命令 / 伪代码

```python
# benchmarks/duckdb_vs_polars.py
import duckdb, polars as pl, time
from backtest.engine import simple_ma_strategy

con = duckdb.connect("data/p116_foundation.duckdb")
df = con.execute("SELECT ... FROM daily_bars WHERE ...").pl()

# Polars 信号 + 权益曲线
start = time.perf_counter()
signals = simple_ma_strategy.polars_run(df)
print("polars", time.perf_counter() - start)

# DuckDB 纯 SQL（仅限简单出场）
start = time.perf_counter()
con.execute("""
    WITH signals AS (
        SELECT symbol, date,
               CASE WHEN ma_5 > ma_20 AND LAG(ma_5) OVER w < LAG(ma_20) OVER w THEN 1 ELSE 0 END AS entry
        FROM daily_bars
        WINDOW w AS (PARTITION BY symbol ORDER BY date)
    )
    ...
""")
print("duckdb", time.perf_counter() - start)
```

### 4. 预期收益

推荐分工：

| 阶段 | 工具 | 原因 |
|------|------|------|
| **数据加载** | DuckDB | SQL 过滤 + 列裁剪 + 与 Foundation DB 原生集成 |
| **指标窗口计算** | DuckDB | `OVER (PARTITION BY symbol ORDER BY date)` 性能极高 |
| **信号生成** | Polars | 复杂条件组合（跨列、跨周期状态 join）表达更清晰 |
| **权益曲线 / 持仓模拟** | Polars | 需要按 symbol 分组的有状态遍历，`groupby + shift` 最自然 |
| **绩效指标** | Polars | 向量化年化/回撤/夏普计算 |
| **报告落库** | DuckDB | 写回 `StrategyLab.duckdb` |

预期整体性能比纯 DuckDB 或纯 Polars 快 **20–50%**，且出场逻辑可维护性更好。

### 5. 风险

- **Arrow 零拷贝失效**：如果类型转换或索引方式不当，可能出现隐式 copy。
- **团队技能分裂**：部分开发者只熟悉 SQL，部分只熟悉 Polars，需要统一编码规范。
- **DuckDB SQL 复杂出场难以调试**：trailing stop 需要递归/自连接，SQL 表达困难。

### 6. 替代方案

| 方案 | 适用 |
|------|------|
| 纯 DuckDB | 仅适用于简单 fixed stop / 固定出场 |
| 纯 Polars | 适用于小宇宙（< 1000 只）或内存充裕 |
| DuckDB -> pandas -> Polars | 中间转换增加 20–50% 开销，不推荐 |

### 7. MVP / backlog 判定

- **进入 MVP**：DuckDB 取数 + Polars 回测计算作为 `backtest/engine.py` 默认架构。
- **进入 backlog**：纯 DuckDB SQL 回测路径作为可选“极速模式”，在 sandbox 验证后再考虑引入。

---

## Q4. State Cube 查询如何避免重复扫描？

### 1. 数据依赖

- `state_cube.duckdb`：至少包含 `symbol, date, d1_state, w1_state, mn1_state`。
- Agent DAG 中多个节点会并发/串行查询 State Cube：
  - Trend Analyst：查 symbol 的 d1/w1 state 时间序列。
  - Market Macro：查全市场某日的 state 分布。
  - Industry Chain：查同行业 symbol list 的 state。

### 2. 最小实验设计

1. 统计一个完整 Agent Debate DAG 执行过程中 State Cube 的查询次数和扫描列。
2. 对比三种缓存/索引策略：
   - 无缓存：每次都 `SELECT * FROM state_cube WHERE ...`
   - 列裁剪：只 SELECT 需要的列
   - 内存缓存：将最近 5 个交易日的全市场 state 缓存为 Polars DataFrame
   - 物化视图：按日期预聚合 `daily_state_distribution`
3. 用 DuckDB `EXPLAIN ANALYZE` 检查是否有全表扫描。

### 3. 性能基准命令 / 伪代码

```python
# benchmarks/state_cube_query.py
import duckdb, time, functools
from lru_cache import LRUCache

cache = LRUCache(maxsize=10)

@functools.lru_cache(maxsize=5)
def get_state_for_dates_cached(dates: tuple, columns: tuple) -> pl.DataFrame:
    cols = ",".join(columns)
    return con.execute(f"""
        SELECT symbol, date, {cols} FROM state_cube
        WHERE date IN ({','.join(['?']*len(dates))})
    """, list(dates)).pl()

# 对比无缓存 vs 有缓存
for cols in [("d1_state",), ("d1_state","w1_state","mn1_state")]:
    for use_cache in [False, True]:
        start = time.perf_counter()
        for _ in range(100):
            if use_cache:
                get_state_for_dates_cached(("2024-06-01",), cols)
            else:
                con.execute("SELECT * FROM state_cube WHERE date = '2024-06-01'")
        print(cols, use_cache, time.perf_counter() - start)
```

索引建议：

```sql
CREATE INDEX idx_state_cube_date ON state_cube(date);
CREATE INDEX idx_state_cube_symbol ON state_cube(symbol);
```

### 4. 预期收益

- 列裁剪可减少 **50–70%** I/O。
- 日期索引可将 `WHERE date = x` 查询从全表扫描降到毫秒级。
- 内存缓存最近交易日 state 后，Agent DAG 中重复查询可从百毫秒降到 **< 1ms**。

### 5. 风险

- **缓存一致性**：State Cube 每日更新后，缓存必须失效。
- **内存占用**：全市场 5000 只 × 5 天 × 3 state 列 ≈ 1MB，极低。
- **并发安全**：多 Agent 线程共享缓存需要加锁或使用不可变 DataFrame。

### 6. 替代方案

| 方案 | 说明 |
|------|------|
| 每次直接查询 DuckDB | 最简单，但 Debate DAG 中重复扫描严重 |
| 每日生成 Parquet 快照 | 适合只读分析，但增加 ETL 步骤 |
| 内存数据库（如 mem state） | 过度设计，State Cube 本身不大 |

### 7. MVP / backlog 判定

- **进入 MVP**：
  - State Cube 查询增加 `SELECT` 列白名单，禁止 `SELECT *`。
  - 对 `date` 和 `symbol` 建立索引。
  - 在 `tools/state_cube.py` 中加入 LRU 内存缓存（最近 5 个交易日）。
- **进入 backlog**：
  - 按行业/按市场的物化视图、每日 Parquet 快照、分布式缓存。

---

## Q5. 产业链 Agent 在没有完整知识图谱前如何做最小版本？

### 1. 数据依赖

- `market_assets.duckdb` 或本地 CSV：品种 -> 申万/中信行业映射。
- 手工维护的产业链映射 JSON：行业 -> `[上游行业, 下游行业, 同行业]`。
- `state_cube.duckdb`：关联品种的多周期 state。
- 资金流向表（可选）：行业主力资金净流入，用于验证传导方向。

### 2. 最小实验设计

1. 选取 3 个典型产业链（如：锂电池 -> 整车 -> 零部件；光伏 -> 逆变器 -> 电站）。
2. 构建静态 JSON 映射：
   ```json
   {"锂电池": {"upstream": ["锂矿"], "peer": ["锂电池"], "downstream": ["整车", "储能"]}}
   ```
3. 当 Industry Chain Agent 被调用时：
   - 输入 symbol -> 查行业 -> 查映射 -> 取关联 symbol list。
   - 查询这些 symbol 在 state_cube 中最近 5 个交易日的 state 分布。
   - 输出：产业评分（关联行业中强势状态占比）、上下游传导信号、风险提示（关联行业分歧大）。
4. 与完整 KG 方案（Kuzu）对比：开发成本、查询延迟、准确率（以未来 5 日行业收益率相关性为 proxy）。

### 3. 性能基准命令 / 伪代码

```python
# hermass_platform/agents/industry_chain.py
import json, polars as pl

with open("config/industry_chain_map.json") as f:
    CHAIN_MAP = json.load(f)

def lookup_related_industries(industry: str) -> dict:
    return CHAIN_MAP.get(industry, {"upstream": [], "peer": [industry], "downstream": []})

def industry_chain_score(symbol: str, state_cube: pl.DataFrame, industry_map: dict) -> dict:
    industry = industry_map[symbol]
    related = lookup_related_industries(industry)
    all_related = related["upstream"] + related["peer"] + related["downstream"]
    related_symbols = [s for s, ind in industry_map.items() if ind in all_related]

    slice_df = state_cube.filter(
        pl.col("symbol").is_in(related_symbols) &
        pl.col("date") >= pl.lit("2024-12-01")
    )
    score = slice_df["d1_state"].str.starts_with("2").mean()  # 强势状态比例示例
    return {
        "industry": industry,
        "related_count": len(related_symbols),
        "strong_state_ratio": score,
        "upstream": related["upstream"],
        "downstream": related["downstream"],
        "verdict": "positive" if score > 0.6 else "neutral",
    }
```

测试：

```bash
python -m pytest tests/agents/test_industry_chain.py -v
```

### 4. 预期收益

- 最小版本开发周期 **< 3 天**。
- 不引入 Kuzu/Neo4j 依赖，MVP 阶段无额外运维成本。
- 覆盖 80% 的产业链分析需求（同行业 + 一级上下游）。
- 为后续 KG 方案积累评估基线（准确率、延迟）。

### 5. 风险

- **静态映射不完整**：A 股产业链复杂，手工 JSON 只能覆盖常见链。
- **无因果方向**：无法区分“上游涨价利空下游” vs “下游需求拉动上游”。
- **更新滞后**：行业分类每年调整，JSON 需要人工维护。

### 6. 替代方案

| 方案 | 说明 |
|------|------|
| Kuzu 知识图谱 | 能力强，但需要schema设计、数据清洗、推理调试，至少 2–4 周 |
| LLM 实时抽取产业链 | 动态更新，但幻觉严重，需要人工审核 |
| 使用公开供应链数据库（如 Wind/同花顺） | 数据质量好，但成本高、接入慢 |

### 7. MVP / backlog 判定

- **进入 MVP**：静态 JSON 映射 + state_cube 聚合作为 Industry Chain Agent 的最小实现，纳入 Phase 3。
- **进入 backlog**：Kuzu 知识图谱构建、LLM 动态抽取、产业链因果推理模型，全部放入 `hermass_platform/research/rag_kg_sandbox/`。

---

## 综合结论与下一步

### 可进入 MVP 的研究结论

1. **回测性能目标 < 30s 现实**，前提是：Polars 热路径 + DuckDB 列裁剪/索引 + `filter_first` 预过滤。
2. **Foundation DB 预计算 7 类指标**：MA5/10/20/60、布林带位置、ATR14、volume_ratio、ADX14、D1/W1/MN1 state。
3. **DuckDB ↔ Polars 分工**：DuckDB 负责取数和窗口指标，Polars 负责信号、权益曲线和绩效指标。
4. **State Cube 查询优化**：禁止 `SELECT *`，对 date/symbol 建索引，引入 LRU 内存缓存（最近 5 交易日）。
5. **产业链 Agent 最小版**：静态 JSON 行业链映射 + state_cube 聚合，不阻塞 Phase 3。

### 进入 Research Backlog 的内容

- TS-FM（Chronos ONNX）A 股效果验证 → `research/tsfm_sandbox/`
- RAG-KG（Kuzu）完整产业链图谱 → `research/rag_kg_sandbox/`
- 自适应预计算指标缓存（按策略热度）
- 纯 DuckDB SQL 极速回测模式
- 多机并行 / Dask 横向扩展

### 下一步行动

1. Codex 在 Phase 2 创建 `backtest/engine.py` 时，按上述 DuckDB/Polars 分工实现骨架。
2. Qoder 在 DSL 条件翻译器中，对 `state_hex_in` / `price_cross_ma` 条件默认映射到预计算列名。
3. Kimi 在 1 周内提供 `benchmarks/light_backtest_perf.py`、`benchmarks/state_cube_query.py` 的可运行版本，并跑出基线数据。
4. 所有性能结论以 JSONL 形式写入 `outputs/benchmarks/`，作为 Phase 2 验收依据。
