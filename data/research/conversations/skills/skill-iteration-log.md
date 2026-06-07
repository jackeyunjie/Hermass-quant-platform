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
