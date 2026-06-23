# Qoder Next Task: Phase 3 Web UI Contract

你是 Hermass AI Quant Platform 的 Qoder Architect。本轮任务是把 Phase 3 Web UI 从“未落”推进到可实现、可审阅、可验收的工程契约。**必须收缩范围，禁止发散成新平台设计或 Agent 包装。**

## 必读上下文

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md` 中 Web / Strategy Lab 相关部分
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`
- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/preview_service.py`
- `hermass_platform/strategy_lab/dsl_validator.py`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/audit.py`
- `scripts/run_strategy_lab_mvp_e2e_acceptance.py`

## 总裁决

Phase 3 Web UI 是薄层入口，不是业务逻辑层。主线立刻启动，真实数据 baseline 拆成独立 Kimi handoff，互不阻塞。

```text
Web Layer (FastAPI + Jinja2)
  -> parse form/query params
  -> call hermass_platform/strategy_lab/ service
  -> render template
  -> display trace_id + run tag + not investment advice disclaimer
```

规则：

- Web 路由只做参数解析、service 调用、模板返回。
- 业务逻辑全部留在 `hermass_platform/strategy_lab/`。
- 必须复用现有服务契约：`GenerateStrategyRequest/Response`、`ValidateStrategyRequest/Response`、`PreviewRequest/Response`、`BacktestRequest/Response`。
- UI 必须显式暴露运行标签：`synthetic`、`light_stub`、`light_real_v1`，以及 `not investment advice`。
- UI 验收不依赖真实 DB；用 3 个冻结中文样例跑通 `generate -> validate -> preview -> backtest`。

## 页面范围（只许 3 个）

### Page 1: Strategy Structuring（策略构建）

用途：用户输入中文策略描述，系统生成 DSL 并展示校验结果。

表单字段：

- `strategy_id`：文本，必填，小写 + 下划线，例如 `ma5_cross_ma20_stop_8`。
- `natural_language`：多行文本，必填，例如 `MA5上穿MA20买入，跌破MA10卖出，止损8%`。
- 提交按钮：`生成并校验`。

调用 service：

- `NLToDSLParser.parse(natural_language, strategy_id)` -> `StrategyDSL`
- `validate_dsl(dsl)` -> `ValidationResult`
- 转换为 `GenerateStrategyResponse`、`ValidateStrategyResponse`

显示字段：

- 全局 `trace_id`
- 生成状态：成功 / 失败
- 生成的 DSL JSON（可折叠）
- 校验结果：`passed`、`level`、错误列表（`code`、`message`、`path`）
- 红线结果：`passed`、触发的规则代码
- 若红线通过，显示“进入 Preview / Backtest”链接或按钮
- 若红线失败，明确显示拒绝原因，例如：
  - `RL_EXIT_MUST_HAVE_STOP_LOSS`：策略缺少止损条件。
  - `RL_MAX_POSITION`：仓位超过 25%。

### Page 2: Strategy Diagnosis（策略诊断）

用途：展示同一 `trace_id` 下的 Preview 和 Light Backtest 结果。

表单字段：

- `trace_id`：文本，必填。
- `start_date`：日期，默认 `2023-01-01`。
- `end_date`：日期，默认 `2024-12-31`。
- 数据来源/模式选择：固定显示当前运行标签，不可由用户切换真实数据源。
- 提交按钮：`运行 Preview` / `运行 Backtest`。

调用 service：

- `PreviewService.preview(dsl, data_source="mock", trace_id=trace_id)` -> `PreviewResponse`
- `run_dsl_backtest(dsl, start_date, end_date, ...)` -> `BacktestResult` -> `BacktestResponse`

显示字段：

- 全局 `trace_id`
- 运行标签：`synthetic` / `light_stub` / `light_real_v1`
- Preview：overall status、total estimated hits、每 section 命中数、warnings
- Backtest：status、mode、metrics（total_return、annual_return、max_drawdown、sharpe_ratio、win_rate、profit_factor、trade_count 等）、trade_count、warnings、errors
- `daily_curve` 和 `trades` 可截断显示前 20 条，并提示完整数据在 storage/audit
- 免责声明：`not investment advice`

### Page 3: Evidence Lab（证据实验室）

用途：按 `trace_id` 查询 audit timeline 和存储的交易证据。

表单字段：

- `trace_id`：文本，必填。
- 提交按钮：`查询审计链路`。

调用 service：

- `StrategyAuditLogger.list_by_trace_id(trace_id)` -> audit records
- `StrategyLabStorage.list_backtests(trace_id=trace_id)` / `get_backtest_result(trace_id)`
- `StrategyLabStorage.list_trades(trace_id=trace_id)`
- `StrategyLabStorage.list_trade_events(trace_id=trace_id)`

显示字段：

- 全局 `trace_id`
- Audit timeline：按时间顺序显示 generation / validation / preview / backtest 记录
  - operation
  - created_at
  - dsl_version
  - input_hash
  - output_hash
  - red_line_result（passed / triggered_rules）
- Backtest summary：status、mode、metrics JSON
- Trades：trade_id、symbol、entry_time、exit_time、pnl、pnl_pct、status
- Trade events：event_type、symbol、date、notes
- 若 audit 记录缺失，提示“未找到该 trace_id 的审计记录”

## 技术边界（固定）

- 框架：FastAPI + Jinja2。
- 不引入 React/Vue/SPA、不引入前后端分离、不引入前端状态管理框架。
- 静态资源（CSS/JS）如需使用，只放 `web/static/`，且保持最小可用。
- 模板放 `web/templates/`。
- 路由只做参数解析、调用 service、返回模板。
- Web 层不直接读写 DuckDB、不调用 LLM、不生成策略代码。

## 文件级 Contract

### 新增 `web/main.py`

职责：FastAPI 应用入口、生命周期、静态资源挂载、Jinja2 模板引擎配置、路由注册。

最小签名：

```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Hermass Strategy Lab Web")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

app.include_router(strategy_lab_routes.router)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

环境变量：

- `STRATEGY_LAB_STORAGE_DB`：默认 `outputs/strategy_lab/web_storage.duckdb`
- `STRATEGY_LAB_AUDIT_DB`：默认 `outputs/strategy_lab/web_audit.duckdb`
- `FOUNDATION_DB`：可选，默认 `data/p116_foundation.duckdb`
- `STATE_CUBE_DB`：可选，默认 `data/state_cube.duckdb`

### 新增 `web/strategy_lab_routes.py`

职责：Strategy Lab 三个页面的路由和 API 转发。

最小路由：

```python
from fastapi import APIRouter, Form, Query, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/strategy-lab", tags=["strategy-lab"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/structuring")
async def structuring_page(request: Request): ...

@router.post("/structuring")
async def structuring_submit(
    request: Request,
    strategy_id: str = Form(...),
    natural_language: str = Form(...),
): ...

@router.get("/diagnosis")
async def diagnosis_page(
    request: Request,
    trace_id: str | None = Query(None),
): ...

@router.post("/diagnosis/run")
async def diagnosis_run(
    request: Request,
    trace_id: str = Form(...),
    start_date: str = Form("2023-01-01"),
    end_date: str = Form("2024-12-31"),
    stage: str = Form(...),  # "preview" or "backtest"
): ...

@router.get("/evidence")
async def evidence_page(
    request: Request,
    trace_id: str | None = Query(None),
): ...
```

约束：

- `structuring_submit` 中若 DSL 生成失败，仍返回页面并显示错误。
- `diagnosis_run` 必须从 storage 中按 `trace_id` 读取 DSL snapshot；找不到则返回错误页。
- `diagnosis_run` 中 backtest 默认尝试 `light_real_v1`；若 `FOUNDATION_DB` 不存在或失败，明确降级显示 `light_stub` 或 `failed`，**不得静默伪装真实绩效**。

### 新增 `web/templates/base.html`

职责：统一布局、导航栏、免责声明、运行标签样式。

必须包含：

- 导航链接：Strategy Structuring、Strategy Diagnosis、Evidence Lab
- 页脚免责声明：
  ```
  本工具仅用于策略研究与技术验证，不构成投资建议。回测结果不代表未来收益。
  ```
- 运行标签显示区域：每个页面顶部或结果卡片上显示当前 `run_tag`。

### 新增 `web/templates/structuring.html`

职责：策略构建页面。

渲染上下文：

```python
{
    "request": request,
    "trace_id": str,
    "strategy_id": str,
    "natural_language": str,
    "dsl": dict | None,
    "generation_errors": list[str],
    "validation": ValidateStrategyResponse | None,
    "red_line_result": dict,
    "run_tag": "synthetic",
}
```

### 新增 `web/templates/diagnosis.html`

职责：策略诊断页面。

渲染上下文：

```python
{
    "request": request,
    "trace_id": str,
    "dsl_snapshot": dict | None,
    "preview": PreviewResponse | None,
    "backtest": BacktestResponse | None,
    "run_tag": "light_stub" | "light_real_v1" | "synthetic",
    "errors": list[str],
}
```

### 新增 `web/templates/evidence.html`

职责：证据实验室页面。

渲染上下文：

```python
{
    "request": request,
    "trace_id": str,
    "audit_records": list[dict],
    "backtest_summary": dict | None,
    "trades": list[dict],
    "trade_events": list[dict],
    "errors": list[str],
}
```

### 新增 `web/templates/index.html`

职责：项目首页，简单说明三个页面用途和免责声明。

### 新增 `web/static/style.css`（如需）

职责：最小样式，保证运行标签、错误信息、免责声明清晰可见。

## 服务调用模型映射

| 页面 | HTTP 方法 | 调用模型 | 返回模型 | 业务逻辑文件 |
|------|-----------|----------|----------|--------------|
| Structuring | GET/POST | `GenerateStrategyRequest` | `GenerateStrategyResponse` + `ValidateStrategyResponse` | `e2e_runner.NLToDSLParser` + `dsl_validator.validate_dsl` |
| Diagnosis (preview) | POST | `PreviewRequest` | `PreviewResponse` | `preview_service.PreviewService.preview` |
| Diagnosis (backtest) | POST | `BacktestRequest` | `BacktestResponse` | `backtest_adapter.run_dsl_backtest` |
| Evidence | GET | `trace_id` query | audit + trades + events | `audit.StrategyAuditLogger` + `storage.StrategyLabStorage` |

## UI 运行标签规范

每个结果页必须显式展示以下标签之一：

- `synthetic`：Preview 使用 mock / synthetic 数据。
- `light_stub`：Backtest 未接入真实 DB，或真实 DB 缺失，返回 stub 结果。
- `light_real_v1`：Backtest 接入真实 DuckDB 并运行成功。
- `not investment advice`：所有页面固定显示。

标签显示文案：

```text
运行模式：{synthetic | light_stub | light_real_v1} | 本工具不构成投资建议，回测结果不代表未来收益。
```

## 验收标准（不依赖真实 DB）

### AC1: 3 个冻结样例跑通

使用 `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md` 中的 3 个样例：

1. `MA5上穿MA20买入，跌破MA10卖出，止损8%`
2. `D1状态属于0x23且成交量放大到20日均量1.5倍以上，MA5上穿MA20买入，止损8%，止盈15%，排除涨停`
3. 修改样例 1 使仓位为 30%：`MA5上穿MA20买入，跌破MA10卖出，仓位30%`

在 Structuring 页面输入后：

- 样例 1/2 生成合法 DSL，校验通过，红线通过。
- 样例 3 被红线拒绝，显示 `RL_MAX_POSITION` 原因。

### AC2: 缺止损显示红线拒绝原因

输入：`MA5上穿MA20买入，跌破MA10卖出`

- 校验失败，显示 `RL_EXIT_MUST_HAVE_STOP_LOSS`。
- 不执行 Preview / Backtest。
- Audit timeline 中可见 `generation` + `validation` 两条记录。

### AC3: 每一步展示 trace_id

- Structuring 页面提交后，顶部显示 `trace_id`。
- Diagnosis 页面提交后，顶部显示 `trace_id`。
- Evidence 页面查询后，顶部显示 `trace_id`。
- Audit timeline 每条记录显示 `trace_id`。

### AC4: Audit timeline 可拉出完整链路

对样例 1 执行：

1. Structuring -> 生成 DSL
2. Diagnosis -> 运行 Preview
3. Diagnosis -> 运行 Backtest
4. Evidence -> 按 trace_id 查询

Evidence 页面应显示：

- generation
- validation
- preview
- backtest

四条 audit 记录，顺序正确。

### AC5: 服务契约复用

Web 路由代码中：

- 不得新建与 `api_models.py` 重复的请求/响应模型。
- 如需表单包装，必须转换为现有模型后调用 service。

### AC6: Web 层无业务逻辑

- `web/` 下不出现 `DuckDB` 直接查询。
- `web/` 下不出现 `polars` 信号计算。
- `web/` 下不出现 LLM 调用或策略代码生成。

## 明确 Non-MVP Items（本轮不做）

本轮 Phase 3 Web UI 明确不进入：

- SPA / 前后端分离架构。
- React / Vue / Angular 等前端框架。
- Redux / Pinia / Zustand 等前端状态管理框架。
- Agent Debate 界面或工作流。
- Paper Trading 界面或模拟实盘。
- 真实实时行情接入 / WebSocket 行情推送。
- 用户认证、权限管理、多租户。
- 策略分享、社区、评论、 marketplace。
- 移动端适配（保持桌面可用即可）。
- 复杂图表库（如需要曲线图，先用表格或文本展示）。

## 输出物清单

Qoder 本轮必须交付：

1. `agents/QODER_NEXT_TASK_PHASE3_WEB_UI_CONTRACT.md`（本文件，迭代版）。
2. `data/research/conversations/agent-runs/2026-06-18-qoder-phase3-web-ui-contract.md`（运行摘要）。
3. 文件级 contract 附录（可选单独文件 `docs/design/PHASE3_WEB_UI_FILE_CONTRACT.md`）：
   - `web/main.py` 完整接口签名。
   - `web/strategy_lab_routes.py` 完整路由签名。
   - 每个模板渲染上下文。
   - 每个页面调用的 service、模型、显示字段。

## Codex 实现提示

- 启动命令：`uvicorn web.main:app --reload --port 8000`
- 验收脚本：`scripts/run_strategy_lab_mvp_e2e_acceptance.py` 继续作为后端基线；Web 验收可新增 `scripts/test_web_ui_smoke.py` 用 `httpx` 或 `requests` 访问 3 个页面并检查 trace_id 与免责声明。
- 确保 `web/` 目录加入 `pyproject.toml` 的 package include 或保持为根目录模块；若影响 hatchling 构建，需同步调整。
