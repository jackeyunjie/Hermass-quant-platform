# Qoder Phase 1 DuckDB Preview Storage Audit Patch

## Implemented Files

- `hermass_platform/strategy_lab/preview_service.py` — 新增 `DuckDBPreviewProvider`，修改 `PreviewConfig` 增加 `duckdb_path`，修改 `PreviewService` 支持真实 DuckDB COUNT 查询
- `hermass_platform/strategy_lab/storage.py` — 新增 `StrategyLabStorage`，最小 DuckDB 持久化（3 张表）
- `hermass_platform/strategy_lab/audit.py` — 新增 `StrategyAuditLogger`，最小审计日志
- `hermass_platform/strategy_lab/tests/test_preview_duckdb.py` — DuckDB Preview 测试
- `hermass_platform/strategy_lab/tests/test_storage.py` — Storage 测试
- `hermass_platform/strategy_lab/tests/test_audit.py` — Audit 测试
- `hermass_platform/strategy_lab/condition_translator.py` — 修复 DuckDB `LAG()` 为 `lag() OVER (PARTITION BY symbol ORDER BY date)`
- `hermass_platform/strategy_lab/tests/test_condition_translator.py` — 适配大小写不敏感断言

## DuckDB Preview Behavior

- `FULLY_SUPPORTED` 条件执行真实 `SELECT COUNT(*) FROM table WHERE ...` 或 `SELECT COUNT(*) FROM (SELECT 1 FROM table QUALIFY ...)`
- 包含窗口函数（`lag()`）的条件自动使用 `QUALIFY` 子查询包装，因为 DuckDB 不允许窗口函数出现在 WHERE 中
- `MOCK_ONLY` 条件回退 mock，并在 notes 标注
- `REQUIRES_BACKTEST_CONTEXT` 条件（如 `stop_loss_pct`）回退估算，不阻塞整体 Preview
- `UNSUPPORTED` 条件导致整体失败
- 缺少 `duckdb_path` 时回退 mock，行为确定
- SQL 安全：禁止 `SELECT *`，允许 `COUNT(*)`；窗口函数子查询使用 `SELECT 1`

## Storage/Audit Tables

**Storage (`StrategyLabStorage`)**
- `user_strategies` — strategy_id, name, description, created_at, updated_at
- `strategy_versions` — id (sequence), strategy_id, dsl (JSON), trace_id, input_hash, output_hash, created_at
- `strategy_backtests` — id (sequence), strategy_id, trace_id, status, metrics (JSON), dsl_snapshot (JSON), created_at

**Audit (`StrategyAuditLogger`)**
- `strategy_audit_log` — id (sequence), trace_id, operation, strategy_id, dsl_version, input_hash, output_hash, red_line_result (JSON), created_at

## Tests Added

| 文件 | 测试数 | 覆盖点 |
|------|--------|--------|
| test_preview_duckdb.py | 12 | 真实 COUNT、QUALIFY 包装、无 SELECT *、stop_loss 不阻塞、无 duckdb_path 回退、确定性 |
| test_storage.py | 7 | 3 张表创建、version 保存/读取、backtest 保存/读取、JSON 往返 |
| test_audit.py | 7 | 表创建、preview/validation 日志、同一 trace 多操作、input_hash 稳定性 |

## Validation Commands

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
# 188 passed, 1 warning

/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/strategy_lab/*.py
# 无错误
```

## Design Choices

1. **QUALIFY 包装**：DuckDB 不允许窗口函数在 WHERE 中。对于含 `lag()` 的条件，自动包装为 `(SELECT 1 FROM table QUALIFY expr)`，这是 DuckDB 原生支持的语法且不使用 `SELECT *`。
2. **分区窗口函数**：condition_translator 中 DuckDB 方言的 `LAG(col)` 改为 `lag(col) OVER (PARTITION BY symbol ORDER BY date)`，避免跨 symbol 串数。
3. **Sequence 自增**：DuckDB 的 `INTEGER PRIMARY KEY` 不自动递增。使用 `CREATE SEQUENCE ... DEFAULT nextval('seq')` 实现自增。
4. **ON CONFLICT 时间戳**：DuckDB 在 `DO UPDATE SET` 中把 `CURRENT_TIMESTAMP` 解析为列名。使用 `now()` 函数替代。
5. **input_hash 稳定**：audit logger 使用 `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"))` 计算 SHA-256 前 16 位，确保相同 payload 产生相同 hash。

## Known Limits

- `industry_include` / `industry_exclude` 需要 `stock_info` 表，当前测试 fixture 未建该表，真实查询会 fallback 到 mock
- `price_cross_ma` 的 DuckDB 翻译已修复窗口函数语法，但未在测试中验证真实 COUNT（因为 fixture 缺少 `close_d1` / `ma_20_d1` 列）
- Storage 的 `user_strategies` upsert 需要 `name` 字段在 DSL 中；如果 DSL 没有 `name`，会插入空字符串
- Audit logger 的 `log_*` 方法接受 `input_payload` / `output_payload` 字典，实际存储的是它们的 hash，不是原始内容

## Next Steps For Codex

1. 在 `PreviewService.preview()` 中集成 `StrategyAuditLogger.log_preview()` 调用，把每次 preview 的 input_hash / output_hash / red_line_result 写入 audit 表
2. 在 `dsl_validator.validate_dsl()` 返回结果中暴露 `red_line_result` 字典，方便 audit logger 记录
3. 考虑把 `storage.py` 和 `audit.py` 的 `db_path` 统一配置到 `PreviewConfig` 或全局配置中
4. 为 `PreviewService` 添加 `__enter__` / `__exit__` 上下文管理器，确保 DuckDB 连接正确关闭
