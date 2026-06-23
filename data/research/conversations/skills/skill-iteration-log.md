# Skill Iteration Log

## 当前项目内 Skill

### hermass-quant-execution

路径：`skills/hermass-quant-execution/SKILL.md`

用途：

- Hermass MVP 执行规则。
- DSL、红线、回测、Agent 路由、可观测性任务。

状态：草案，等待 Phase 0 真实任务验证。

## 2026-06-06 Kimi 输出后的 Skill 更新点

`hermass-backtest-mvp` 后续必须内置这些规则：

- DuckDB 负责取数、列裁剪、预过滤。
- Polars 负责信号、权益曲线、绩效指标。
- benchmark 必须输出 JSONL。
- 热路径禁止 Python 逐行循环。

`hermass-dsl-builder` 后续必须内置这些规则：

- 条件注册表要声明字段依赖。
- MVP 条件优先映射到预计算列。
- 使用非预计算参数时，要明确进入动态计算或拒绝路径。

## 2026-06-06 Qoder Phase 0 输出后的 Skill 更新点

`hermass-dsl-builder` 后续应从 Qoder 实现中抽取：

- `StrategyDSL` 必须先过 Pydantic，再进入 validator。
- 缺少 `stop_loss_pct` 是红线错误。
- `max_position_pct > 0.25` 应在 schema 层优先拦截。
- condition translator 必须返回 required columns/tables，供 preview/backtest 使用。

`hermass-quant-execution` 后续应加入：

- 默认测试解释器为 `/Users/lv111101/.pyenv/versions/3.11.12/bin/python`，除非项目建立 `.venv`。
- Phase 0 验收命令固定为 strategy_lab 测试 + py_compile + AC 烟测。

## 2026-06-06 Kimi Benchmark 输出后的 Skill 更新点

`hermass-backtest-mvp` 后续应加入：

- benchmark 脚本必须支持 `--synthetic` 和 `--output`。
- JSONL 字段必须包含 p50/p95、data_source、platform。
- synthetic 结果只验证脚本和热路径，不作为真实性能承诺。
- 多个 benchmark 不应并行共用同一个 DuckDB 临时文件；当前 Kimi 脚本已修复为进程级唯一临时库路径。

## 2026-06-06 Qoder Phase 1 设计后的 Skill 更新点

`hermass-dsl-builder` 后续应加入：

- Condition registry 可以声明静态依赖，但 Preview 不能简单因为 `stop_loss_pct` 需要持仓上下文而拒绝整个策略。
- 条件 metadata 需要区分数据依赖和执行上下文依赖。
- `stop_loss_pct` 属于 backtest/position context，不等于 Phase 1 blocked condition。

## 2026-06-06 Kimi Real Data Runbook 后的 Skill 更新点

`hermass-backtest-mvp` 后续应加入：

- 真实数据 benchmark 前必须先跑 `validate_real_data.py`。
- Phase 2 hot path gates：5000×252 P95 < 30s，load < 10s，signal < 12s，metrics < 8s，峰值内存 < 4GB。
- 热路径禁止 pandas 中间转换、`SELECT *`、`iterrows`、`apply(lambda row`、Python 分组循环、`eval/exec`。

## 2026-06-06 Qoder Patch Spec 后的 Skill 更新点

`hermass-dsl-builder` 后续应加入：

- `preview_support` 是 Preview 路由权威。
- `required_tables` 只描述静态数据依赖，不用于简单 blocklist。
- `context_requirements` 描述 position/portfolio/market_state 等运行时上下文。
- `requires_backtest_context` 不等于失败；只在 condition/section 级标记。

## 2026-06-11 Qoder Phase 2 Light Backtest 实现后的 Skill 更新点

`hermass-backtest-mvp` 后续应内置：

- Provider D1 别名归一：`close→close_d1`, `ma_N→ma_N_d1`, `state_hex_d1→d1_state`，查询层屏蔽 timeframe 后缀差异。
- 行级迭代交易生成：持仓上下文需状态机（entry/exit/hold），Polars 只负责信号层，禁止向量化交易生成。
- Status 从 `risk_flags` 重新计算，不依赖模型默认值，确保红线结果与运行时一致。
- Engine 自动补算缺失 MA 列（`compute_required_ma`），避免 provider 层遗漏导致信号丢失。
- 100 股 lot rounding、同日 exit-first-no-reentry、停牌/涨跌停规则已固化在 engine。

`hermass-quant-execution` 后续应加入：

- 4 层单元测试覆盖：provider(11) + engine(14) + metrics(22) + evidence(23) + integration(8) = 78 个回测测试。
- Real DB 阻塞条件：`data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 不存在时，只跑 synthetic smoke，不出 real baseline。
- Phase 2 hardening backlog 追踪：real mode fallback、multi-symbol 日期语义、trade/event 全链路落库、volume_ratio 契约。

## 待拆分 Skill

- `hermass-dsl-builder`
- `hermass-backtest-mvp`
- `hermass-redline-review`
- `hermass-agent-debate`

## 复盘问题

每轮结束后记录：

- 哪个步骤重复出现？
- 哪个步骤最容易出错？
- 哪个步骤值得脚本化？
- 哪个步骤应该写进 Skill？
