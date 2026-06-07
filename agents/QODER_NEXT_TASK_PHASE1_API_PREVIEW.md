# Qoder Next Task: Phase 1 API And Preview Design

请先读取：

1. `AGENTS.md`
2. `docs/TASK_ALLOCATION.md`
3. `data/research/conversations/decisions/0002-kimi-performance-data-architecture.md`
4. `data/research/conversations/decisions/0003-qoder-phase-0-accepted-with-followups.md`
5. `hermass_platform/strategy_lab/dsl_schema.py`
6. `hermass_platform/strategy_lab/condition_registry.py`
7. `hermass_platform/strategy_lab/condition_translator.py`
8. `hermass_platform/strategy_lab/dsl_validator.py`

## 背景

Phase 0 已完成并由 Codex 复核：

- 110 个 strategy_lab 测试通过。
- DSL schema、condition registry、translator、validator 已可用。
- 回测适配器仍是 stub。

现在要推进 Phase 1：Strategy Lab API + Preview + 审计落库设计。

## 你的任务

请交付 Phase 1 工程设计和最小实现建议，必须能被 Codex 直接实现。

## 必须解决的 Phase 0 遗留点

当前 `ConditionSpec` 没有显式字段依赖，字段依赖由 translator 返回。请判断是否需要把字段依赖前移到 registry。

必须输出明确结论：

- 是否在 `ConditionSpec` 增加 `required_columns` / `required_tables`。
- 如果增加，如何保持 translator 与 registry 不重复或不冲突。
- 如何让 preview/backtest 在执行前拒绝非 MVP 字段。

## 必须设计的 Phase 1 文件

请给出这些文件的接口和职责：

1. `hermass_platform/strategy_lab/storage.py`
2. `hermass_platform/strategy_lab/audit.py`
3. `hermass_platform/strategy_lab/preview_service.py`
4. `hermass_platform/strategy_lab/api_models.py`
5. `web/main.py` 或 `web/strategy_lab_routes.py`
6. `migrations/strategy_lab/001_init.sql`

如果你认为路径应调整，请说明理由，但必须遵守：

- Web 层不放业务逻辑。
- 业务逻辑留在 `hermass_platform/strategy_lab/`。

## API 端点范围

设计这些 API：

- `POST /api/strategy-lab/generate`
- `POST /api/strategy-lab/validate`
- `POST /api/strategy-lab/preview`
- `POST /api/strategy-lab/backtest`
- `GET /api/strategy-lab/backtest/{id}`

其中 Phase 1 可以：

- `generate` 使用模板/规则 stub，不调用 LLM。
- `backtest` 返回 accepted/job stub，不跑真实回测。
- `preview` 必须设计成可真实查询 DuckDB；无真实数据时允许 mock provider。

## Preview 设计要求

Preview 至少返回：

- 每个 section 的条件表达式。
- `required_columns`
- `required_tables`
- 命中数量 `hit_count`
- 总样本数量 `sample_count`
- 数据源 freshness。
- `trace_id`

必须支持：

- 没有真实 DuckDB 时的 deterministic mock。
- 有真实 DuckDB 时的 SQL preview。
- 禁止 `SELECT *`。
- 查询前校验 DSL 和 red lines。

## StrategyLab DB DDL

请输出 MVP DDL，只需要：

- `user_strategies`
- `strategy_versions`
- `strategy_backtests`
- `strategy_audit_log`

不要先做：

- paper orders
- positions
- full agent judgments

## 测试要求

请设计测试文件：

- `hermass_platform/strategy_lab/tests/test_storage.py`
- `hermass_platform/strategy_lab/tests/test_audit.py`
- `hermass_platform/strategy_lab/tests/test_preview_service.py`
- `hermass_platform/strategy_lab/tests/test_api_models.py`

每个文件至少说明 5 个测试点。

## 输出格式

请按以下结构输出：

```markdown
# Phase 1 Strategy Lab API And Preview Design

## Field Dependency Decision

## Module Design

## API Request/Response Models

## Preview Flow

## StrategyLab DB DDL

## Tests

## Implementation Order For Codex

## Non-MVP Items
```

## 不做什么

- 不做真实 LLM 调用。
- 不做完整回测引擎。
- 不做 Agent Debate。
- 不做 Paper Trading。
- 不把业务逻辑写进 Web 路由。
