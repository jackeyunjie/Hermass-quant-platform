# Qoder Next Task: Phase 1 DuckDB Preview + Storage/Audit Patch

你是 Hermass 项目的 Architect/Implementer。本轮任务是把 Phase 1 从 mock preview 推进到最小真实可用：DuckDB 条件预览 + Storage/Audit 基础设施。

不要写方案文档。请直接实现代码补丁。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `agents/PHASE1_API_PREVIEW_DESIGN.md`
- `agents/PHASE1_IMPLEMENTATION_PATCH_SPEC.md`
- `data/research/conversations/decisions/0006-phase1-preview-metadata-design.md`
- `data/research/conversations/agent-runs/2026-06-06-qoder-phase1-code-patch.md`
- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/preview_service.py`
- `hermass_platform/strategy_lab/condition_registry.py`
- `hermass_platform/strategy_lab/condition_translator.py`
- `hermass_platform/strategy_lab/dsl_validator.py`
- `hermass_platform/strategy_lab/tests/`

## 当前状态

已完成：

- `ConditionSpec` 有 `required_columns`、`required_tables`、`context_requirements`、`preview_support`。
- `PreviewService.preview(..., data_source="mock")` 已可用。
- `PreviewService.preview(..., data_source="duckdb")` 目前仍回退到 mock，不是真实查询。
- `PreviewService.input_hash` 已由 Codex 修正为 DSL 内容 hash，不要改回 trace_id hash。
- `stop_loss_pct` / `take_profit_pct` 是 `REQUIRES_BACKTEST_CONTEXT`，不能阻塞 Preview。

## 目标

实现 Phase 1 最小真实闭环：

1. DuckDB preview provider 能对 `FULLY_SUPPORTED` 条件执行真实 `COUNT` 查询。
2. `REQUIRES_BACKTEST_CONTEXT` 条件仍返回估算，不阻塞整体 Preview。
3. Storage/Audit 最小落库可用，记录 trace_id、dsl_version、input_hash、output_hash、red_line_result。

## 必须新增/修改文件

### 1. 修改 `hermass_platform/strategy_lab/preview_service.py`

实现真实 DuckDB preview：

- `PreviewConfig` 增加 `duckdb_path: str | None = None`。
- 新增 `DuckDBPreviewProvider` 或等价类。
- `data_source="duckdb"` 时：
  - 对 `FULLY_SUPPORTED` 条件用 `condition_translator.translate_condition(..., "duckdb")` 生成 WHERE fragment。
  - 拼出 `SELECT COUNT(*) AS hit_count FROM ... WHERE ...`。
  - 禁止 `SELECT *`。
  - 只允许显式表名和列名来自 registry/translator，不允许用户参数拼接表名。
- 对 `MOCK_ONLY` 条件回退 mock，并在 notes 标注。
- 对 `REQUIRES_BACKTEST_CONTEXT` 条件回退估算，并在 notes 标注。
- 对 `UNSUPPORTED` 条件整体失败。

必须支持的最小真实查询：

- `ma_golden_cross`
- `ma_death_cross`
- `volume_ratio`
- `limit_up_filter`
- `state_hex_in`
- `state_ef_count`

行业条件可先回退 mock，除非你实现了 `stock_info` join。

### 2. 新增 `hermass_platform/strategy_lab/storage.py`

实现最小 DuckDB storage：

- `StrategyLabStorage(db_path: str)`
- `init_schema()`
- `save_strategy_version(strategy_id, dsl, trace_id, input_hash, output_hash)`
- `save_backtest_result(strategy_id, trace_id, status, metrics, dsl_snapshot)`
- `get_strategy_versions(strategy_id)`
- `get_backtest(trace_id)`

DDL 至少包含：

- `user_strategies`
- `strategy_versions`
- `strategy_backtests`

可以按 `agents/PHASE1_API_PREVIEW_DESIGN.md` 简化，但字段必须支持后续扩展。

### 3. 新增 `hermass_platform/strategy_lab/audit.py`

实现最小审计：

- `StrategyAuditLogger(db_path: str)`
- `init_schema()`
- `log_generation(...)`
- `log_validation(...)`
- `log_preview(...)`
- `log_backtest(...)`
- `list_by_trace_id(trace_id)`

必须记录：

- `trace_id`
- `operation`
- `strategy_id`
- `dsl_version`
- `input_hash`
- `output_hash`
- `red_line_result`
- `created_at`

### 4. 新增测试

必须新增/修改：

- `hermass_platform/strategy_lab/tests/test_preview_duckdb.py`
- `hermass_platform/strategy_lab/tests/test_storage.py`
- `hermass_platform/strategy_lab/tests/test_audit.py`
- 如有必要修改 `test_preview_service.py`

测试要求：

#### DuckDB Preview

- synthetic DuckDB fixture 建 `daily_bars` 和 `state_cube`。
- `data_source="duckdb"` 对 `ma_golden_cross` 返回真实 hit count。
- `data_source="duckdb"` 对 `limit_up_filter` 返回真实 hit count。
- `data_source="duckdb"` 对 `state_hex_in` 返回真实 hit count。
- SQL 查询不包含 `SELECT *`。
- 缺少 `duckdb_path` 时返回错误或明确回退 mock，行为必须测试固定。
- `stop_loss_pct` 不阻塞 DuckDB preview，仍标记 `requires_backtest_context`。

#### Storage

- `init_schema()` 创建 3 张表。
- 能保存并读取 strategy version。
- 能保存并读取 backtest result。
- 保存内容 JSON 可反序列化。

#### Audit

- `log_preview()` 写入 trace_id/input_hash/output_hash/red_line_result。
- `log_validation()` 写入 red_line_result。
- 同一 trace_id 可查询完整链路。
- input_hash 对相同 DSL 稳定。

## 业务规则

必须保持：

- Web 层不实现。
- 不实现真实 LLM。
- 不实现真实 backtest engine。
- 不改 benchmark。
- 不改 factors registry。
- 不把 `required_tables` 用作 blocklist。
- `preview_support` 仍是 preview 路由唯一权威。
- `stop_loss_pct` / `take_profit_pct` 不因为需要 position context 而失败。

## 验收命令

Codex 后续必须能运行：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py
```

## 输出记录

完成后写入：

`data/research/conversations/agent-runs/2026-06-07-qoder-phase1-duckdb-preview-storage-audit.md`

格式：

```markdown
# Qoder Phase 1 DuckDB Preview Storage Audit Patch

## Implemented Files

## DuckDB Preview Behavior

## Storage/Audit Tables

## Tests Added

## Validation Commands

## Design Choices

## Known Limits

## Next Steps For Codex
```
