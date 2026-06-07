# Agent Task Allocation

## 当前总目标

把最终实施方案压缩成 Phase 0/1 MVP，并建立可复用协作机制。

## Qoder 任务

### Q1: DSL v2 MVP Schema

交付：
- `strategy_id/name/schema_version/entry/filters/exit/risk/evaluation/execution/provenance` 字段定义。
- Pydantic 模型草案。
- JSON Schema 草案。
- 10 条合法/非法样例。

验收：
- 缺少 `exit` 拒绝。
- 缺少止损拒绝。
- `max_position_pct > 0.25` 拒绝。

状态：已完成，Codex 已复核。

复核证据：
- `/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q`
- 结果：110 passed, 1 warning。
- `py_compile` 通过。
- AC1/AC2/AC3 烟测通过。

### Q2: 条件注册表 MVP

交付：
- P0 条件类型列表。
- 每个条件的参数 schema。
- 条件是否可用于 entry/filter/exit。
- 对应 DuckDB 字段依赖。

验收：
- 至少覆盖 MA 交叉、State、Volume、Industry、Stop Loss。

状态：已完成，Codex 已复核。

已覆盖：
- `ma_golden_cross`
- `ma_death_cross`
- `price_cross_ma`
- `state_hex_in`
- `state_ef_count`
- `volume_ratio`
- `industry_include`
- `industry_exclude`
- `stop_loss_pct`
- `take_profit_pct`
- `limit_up_filter`

### Q3: Strategy Lab API MVP

交付：
- `/generate`
- `/validate`
- `/preview`
- `/backtest`
- `/backtest/{id}`

验收：
- 每个 API 有请求/响应 schema。
- 每个 API 标注业务逻辑所在 service 文件。

## Kimi 任务

### K1: Light Backtest 性能基准

交付：
- DuckDB/Polars 分工建议。
- 基准测试数据规模。
- P50/P95 指标。
- 最小 benchmark 脚本设计。

验收：
- 能回答 5000 品种 252 天 <30s 是否可行。

状态：已完成研究方案，等待可运行 benchmark 脚本和真实基线数据。

采纳结论：
- Phase 2 默认采用 DuckDB 取数 + Polars 信号/权益曲线/绩效指标。
- Light Backtest <30s 现实，但必须避免 Python 逐行循环。
- `filter_first` 作为信号稀疏策略的默认优化方向。

### K2: Foundation DB 指标预计算建议

交付：
- MVP 必需预计算指标。
- 查询字段清单。
- 缓存策略。

验收：
- 能支持 P0 条件注册表，不需要运行时重复计算所有 MA。

状态：已完成研究方案，进入 MVP 数据要求。

采纳结论：
- 预计算 `ma_5/10/20/60`、`bb_position`、`atr_14`、`volume_ratio`、`adx_14`、`d1_state/w1_state/mn1_state`。
- 非标准 MA 参数进入后续动态缓存 backlog，不进入 MVP。

### K3: 产业链 Agent 最小版本

交付：
- 不依赖完整知识图谱的产业链数据结构。
- 行业/概念/上下游映射表设计。
- Agent 输入输出 contract。

验收：
- 能在 Phase 3 作为只读 Agent 接入，不影响 Phase 1/2。

状态：已完成研究方案，放入 Phase 3。

采纳结论：
- 先用静态 JSON 行业链映射 + State Cube 聚合。
- Kuzu 知识图谱、LLM 动态抽取、产业链因果推理全部进入 research backlog。

### K4: 可运行 Benchmark 脚本

交付：
- `benchmarks/light_backtest_perf.py`
- `benchmarks/indicator_precompute_vs_compute.py`
- `benchmarks/duckdb_vs_polars.py`
- `benchmarks/state_cube_query.py`

验收：
- 输出 JSONL 到 `outputs/benchmarks/`。
- 每个 benchmark 至少记录 P50/P95、数据规模、硬件、执行时间拆分。
- 真实数据不可用时，先提供 synthetic fixture，但标注不可作为最终性能承诺。

状态：新增任务。

## Codex 任务

### C1: 项目协作资产

交付：
- `AGENTS.md`
- `agents/` 三个 Agent prompt。
- Obsidian Vault。
- 项目内 Skill。

验收：
- 新 Agent 可按文件快速接手项目。

### C2: Phase 0 工程骨架

交付：
- `hermass_platform/strategy_lab/` 骨架。
- DSL schema。
- condition registry。
- validator。
- migration SQL。
- 最小测试。

验收：
- py_compile 通过。
- DSL 合法/非法测试通过。

新增要求：
- condition registry 字段依赖必须覆盖 Kimi 采纳的预计算列。
- validator 要禁止需要未声明字段的条件进入回测。

状态：已实现并复核，但保留两个下一步修正点。

复核结果：
- 110 个 strategy_lab 测试通过。
- 8 个源文件 py_compile 通过。
- 最小 DSL 构造、校验、翻译烟测通过。

待修正：
- `pyproject.toml` 引用 `README.md` 的风险已修复。
- 条件注册表目前没有显式字段依赖属性，字段依赖由 translator 返回；后续 Phase 1/2 应考虑把字段依赖前移到 registry，便于 preview/backtest 提前拒绝非 MVP 字段。

### C5: 下一轮 Agent 派工

交付：
- `agents/QODER_NEXT_TASK_PHASE1_API_PREVIEW.md`
- `agents/KIMI_NEXT_TASK_BENCHMARKS.md`

验收：
- Qoder 有明确 Phase 1 API/Preview/DDL 任务。
- Kimi 有明确 benchmark 脚本任务。
- 两份提示词都包含验收命令或输出结构。

状态：已完成。

### C3: Phase 1 API 与预览

交付：
- Strategy Lab API。
- preview service。
- 审计日志。

验收：
- 10 条中文策略中至少 8 条生成合法 DSL。

### C4: Phase 2 Backtest 骨架

交付：
- `backtest/dsl_runner.py`
- `backtest/engine.py`
- `backtest/metrics.py`
- `benchmarks/` 基准脚本入口。

验收：
- DuckDB 只做列裁剪取数和可选预过滤。
- Polars 负责信号生成、权益曲线、绩效指标。
- 禁止 `apply(lambda row: ...)` 和 Python 逐行循环出现在热路径。
- benchmark 输出写入 `outputs/benchmarks/`。

状态：待 Phase 0/1 后启动。

## 冲突处理

当 Qoder 追求架构完整性、Kimi 追求性能研究、Codex 追求 MVP 交付发生冲突时，默认先保证 MVP 可运行。
