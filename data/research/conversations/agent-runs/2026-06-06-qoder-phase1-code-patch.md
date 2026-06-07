# Qoder Phase 1 Code Patch

## Implemented Files

### 1. Modified `hermass_platform/strategy_lab/condition_registry.py`

- Added `PreviewSupport` enum (`FULLY_SUPPORTED`, `MOCK_ONLY`, `REQUIRES_BACKTEST_CONTEXT`, `UNSUPPORTED`).
- Added `ContextRequirement` enum (`NONE`, `POSITION`, `PORTFOLIO`, `MARKET_STATE`).
- Extended `ConditionSpec` with 5 new fields:
  - `required_columns: list[str]` — static column dependency templates.
  - `required_tables: list[str]` — static table dependencies.
  - `context_requirements: list[ContextRequirement]` — runtime context needed.
  - `preview_support: PreviewSupport` — preview support classification.
  - `preview_notes: str` — human-readable explanation.
- Updated all 11 MVP conditions with complete metadata:
  - `stop_loss_pct`: `required_tables=["daily_bars"]` (NOT `positions`), `context_requirements=[POSITION]`, `preview_support=REQUIRES_BACKTEST_CONTEXT`.
  - `take_profit_pct`: same as stop_loss_pct.
  - `limit_up_filter`: `context_requirements=[MARKET_STATE]`.
  - All entry/filter conditions: `preview_support=FULLY_SUPPORTED`.

### 2. New `hermass_platform/strategy_lab/api_models.py`

Pydantic v2 API models:

- `ConditionPreviewItem` — per-condition preview result with `preview_support`, `has_context_required`, `estimated_hits`.
- `SectionPreviewItem` — per-section (entry/exit/filters) aggregation.
- `PreviewOverallItem` — overall status (`success`/`partial`/`failed`), hit totals, context-required counts.
- `PreviewRequest` / `PreviewResponse` — with auto-generated `trace_id` and `input_hash`.
- `ValidateStrategyRequest` / `ValidateStrategyResponse` — with `red_line_result` audit field.
- `GenerateStrategyRequest` / `GenerateStrategyResponse` — NL generation contract.
- `BacktestRequest` / `BacktestResponse` / `GetBacktestResponse` — backtest stubs with `BacktestMetrics`.

### 3. New `hermass_platform/strategy_lab/preview_service.py`

- `MockDataProvider` — deterministic mock hit counts per condition type.
  - Context-required conditions (`stop_loss_pct`, `take_profit_pct`) use simplified estimation model based on params.
- `PreviewService` — core preview logic:
  1. Validates DSL first (red-line failure blocks preview).
  2. Checks for `UNSUPPORTED` conditions (only cause of overall failure).
  3. `REQUIRES_BACKTEST_CONTEXT` returns estimates, does NOT fail.
  4. Aggregates section-level and overall results.
- `preview_condition_sql()` — returns SQL WHERE fragment (no `SELECT *`).

### 4. Modified `hermass_platform/strategy_lab/tests/test_condition_registry.py`

Added 6 new tests:
- `test_all_mvp_conditions_have_preview_support`
- `test_stop_loss_pct_preview_metadata`
- `test_take_profit_pct_preview_metadata`
- `test_stop_loss_pct_no_positions_table`
- `test_ma_golden_cross_fully_supported`
- `test_limit_up_filter_has_market_state_context`

### 5. New `hermass_platform/strategy_lab/tests/test_api_models.py`

Full coverage of all API models:
- Preview models (Condition/Section/Overall/Request/Response).
- Validation models (Request/Response/ErrorItem).
- Generation models (Request/Response).
- Backtest models (Request/Response/GetResponse).

### 6. New `hermass_platform/strategy_lab/tests/test_preview_service.py`

Full coverage:
- `MockDataProvider` hit estimation (known/unknown/stop_loss/take_profit/unsupported).
- `PreviewService.preview()`:
  - Valid DSL preview passes.
  - stop_loss_pct does NOT block preview.
  - Overall status is `partial` when context is required.
  - Red-line failure blocks preview.
  - Unsupported condition fails preview.
  - SQL preview contains no `SELECT *`.
  - Mock preview is deterministic.
  - trace_id and input_hash propagation.

## Tests Added

| File | Tests Added | Total Tests |
|------|-------------|-------------|
| `test_condition_registry.py` | 6 | 23 |
| `test_api_models.py` | 14 | 14 |
| `test_preview_service.py` | 15 | 15 |

**Total: 159 tests passed, 0 failed.**

Codex review update:

- Added `ConditionSpec.resolve_required_columns()` so registry column templates can resolve params such as `timeframe="D1"` into translator-compatible lowercase columns like `close_d1`.
- Changed `PreviewService` to pass a stable DSL-content `input_hash` into `PreviewResponse`; the hash no longer depends on `trace_id`.
- Added 3 regression tests for resolved dependency columns and trace-independent input hash.
- Final reviewed result: **162 tests passed, 0 failed**.

## Validation Commands

```bash
# Compile check
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile \
  hermass_platform/strategy_lab/condition_registry.py \
  hermass_platform/strategy_lab/api_models.py \
  hermass_platform/strategy_lab/preview_service.py

# Full test suite
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest \
  hermass_platform/strategy_lab/tests -q
```

## Design Choices

1. **preview_support 是 Preview 路由唯一权威** — `required_tables` 不再用于 blocklist 拒绝。只有 `UNSUPPORTED` 才导致整体失败。
2. **stop_loss_pct 特殊处理** — `required_tables=["daily_bars"]`（不包含 `positions`），`preview_support=REQUIRES_BACKTEST_CONTEXT`。Preview 返回估算命中数，不阻塞整体流程。
3. **MockDataProvider 确定性** — 固定 hit count 映射 + 参数化估算模型，保证测试可重复。
4. **DuckDB stub 可注入** — `PreviewConfig` 允许替换 registry 和 provider，为真实 DuckDB 实现预留接口。
5. **input_hash 计算** — 使用 `model_validator(mode="after")` 在构造后自动计算，避免 Pydantic v2 `field_validator` 的跨字段限制。

## Risks

| Risk | Mitigation |
|------|------------|
| DuckDB preview 仍是 stub | 已预留 `_estimate_duckdb()` 方法，真实实现不破坏接口 |
| `limit_up_filter` 的 `MARKET_STATE` context 未在 preview 中特殊处理 | 当前不影响 mock preview，真实实现时需区分 |

## Next Steps For Codex

1. **运行验收命令** 确认 159 tests passed。
2. **接入 DuckDB provider** — 实现 `_estimate_duckdb()` 的真实 SQL COUNT 查询。
3. **实现 storage/audit/DDL** — 按 `PHASE1_IMPLEMENTATION_PATCH_SPEC.md` 的 Storage Patch 章节。
4. **Web routes** — 基于 `api_models.py` 实现 FastAPI/Flask 入口（只做序列化，不放业务逻辑）。
