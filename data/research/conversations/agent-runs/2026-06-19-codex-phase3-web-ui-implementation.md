# Codex Phase 3 Web UI 实现

## 背景

Qoder 已回传 `agents/QODER_NEXT_TASK_PHASE3_WEB_UI_CONTRACT.md`，明确 Phase 3 Web UI 为 FastAPI + Jinja2 薄层，只含 3 个页面：Strategy Structuring、Strategy Diagnosis、Evidence Lab。真实数据 baseline 拆分为独立 Kimi handoff。

本记录为 Codex 按 contract 完成实现的总结。

## 已交付文件

### Web 层

- `web/main.py`：FastAPI 应用入口、静态资源挂载、Jinja2 模板配置、环境变量读取。
- `web/strategy_lab_routes.py`：3 个页面的路由与 service 调用。
- `web/templates/base.html`：统一布局、导航、运行标签、免责声明。
- `web/templates/index.html`：首页说明。
- `web/templates/structuring.html`：策略构建页。
- `web/templates/diagnosis.html`：策略诊断页（Preview + Backtest）。
- `web/templates/evidence.html`：证据实验室页（audit + trades + events）。
- `web/static/style.css`：最小样式。
- `web/__init__.py`：使 `web` 成为可导入包。

### 基础设施改动

- `hermass_platform/strategy_lab/storage.py`
  - 新增 `get_strategy_version_by_trace_id(trace_id)`：按 trace_id 读取 DSL snapshot。
  - 扩展 `list_trade_events(trade_id=None, *, trace_id=None)`：支持按 trace_id 查询交易事件，保持旧按 trade_id 查询兼容。
- `pyproject.toml`
  - 新增依赖 `jinja2>=3.1`、`python-multipart>=0.0.9`。
  - `[tool.hatch.build.targets.wheel]` 的 `packages` 增加 `"web"`。

### 测试

- `scripts/test_web_ui_smoke.py`：基于 `fastapi.testclient.TestClient` 的端到端冒烟测试，覆盖：
  - 首页免责声明
  - 合法样例生成 DSL 并通过校验
  - 缺止损红线拒绝
  - 仓位超限红线拒绝
  - 完整链路：structuring → preview → backtest → evidence

## 运行命令

```bash
uv run uvicorn web.main:app --reload --port 8000
```

## 复核结果

```bash
uv run pytest hermass_platform/strategy_lab/tests -q
```

结果：`278 passed, 0 failed`

```bash
uv run python scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

结果：`5/5 cases passed`

```bash
uv run python scripts/test_web_ui_smoke.py
```

结果：

- ✅ home page
- ✅ structuring valid sample
- ✅ structuring over-position red line
- ✅ structuring missing stop loss
- ✅ full journey

```bash
uv run python -m py_compile hermass_platform/strategy_lab/*.py web/*.py scripts/test_web_ui_smoke.py
```

结果：OK

## 设计要点

- Web 路由只做参数解析、service 调用、模板渲染，无业务逻辑。
- 复用现有 `api_models.py` 的 Pydantic 模型作为响应格式。
- Backtest 默认尝试真实 DB；缺失时自动 fallback `light_stub`，并在 UI 显式标注运行模式，不伪装真实绩效。
- 每个结果页顶部显示 `trace_id` 与运行标签 + 免责声明。
- Evidence Lab 按 `trace_id` 串联 audit timeline、backtest summary、trades、trade events。

## 未实现项（按 contract 明确不做）

- SPA / 前后端分离
- React / Vue / Angular
- Agent Debate 界面
- Paper Trading 界面
- 实时行情 / WebSocket
- 用户认证与权限
- 策略社区 / marketplace
- 移动端适配
- 复杂图表库

## 下一步

1. Kimi 完成真实数据 baseline handoff：`data/p116_foundation.duckdb`、`data/state_cube.duckdb`、validate_real_data.py、data_readiness_status.json。
2. Web UI 读取 `data_readiness_status.json` 并在页面显示真实数据 readiness。
3. 真实 DB 就绪后验收 `light_real_v1` 在 Web 上的运行与展示。
4. 可选：把 Web UI smoke test 接入 CI / pytest 集合。

## 参考

- `agents/QODER_NEXT_TASK_PHASE3_WEB_UI_CONTRACT.md`
- `data/research/conversations/decisions/0016-phase3-web-ui-real-baseline-split.md`
- `docs/TASK_ALLOCATION.md` 中 `C20`
