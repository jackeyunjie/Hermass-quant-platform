# 0016 Phase 3 Web UI 作为主线启动，真实数据 baseline 拆为独立 handoff

## 背景

Phase 2 Light Backtest 的实现与 hardening 已完成，当前仓库的确定性主链路已在 `hermass_platform/strategy_lab/` 成形：

- `api_models.py`
- `preview_service.py`
- `e2e_runner.py`
- `backtest_adapter.py`
- `storage.py`
- `audit.py`

但 Web 层尚未落地。同时，真实数据 baseline 仍受外部数据阻塞：`data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 缺失。项目内 skill 和 README 已把这两个文件缺失列为 blocker。

按 `AGENTS.md`，MVP 优先级是可验证链路，不是等待外部数据齐备。因此 Codex 裁决：Phase 3 Web UI 作为主线立刻启动，真实数据 baseline 拆成独立 Kimi handoff，互不阻塞。

## 决策

### 1. Phase 3 Web UI 作为主线

Web UI 是薄层入口，不是业务逻辑层。范围严格收缩为：

- 3 个页面：
  - Strategy Structuring
  - Strategy Diagnosis
  - Evidence Lab
- 技术边界：FastAPI + Jinja2。
- 路由只做参数解析、调用 service、返回模板。
- 业务逻辑全部留在 `hermass_platform/strategy_lab/`。

### 2. Web 必须复用现有服务契约

禁止在 Web 层新建重复的服务模型。必须复用：

- `GenerateStrategyRequest` / `GenerateStrategyResponse`
- `ValidateStrategyRequest` / `ValidateStrategyResponse`
- `PreviewRequest` / `PreviewResponse`
- `BacktestRequest` / `BacktestResponse`

### 3. UI 必须显式暴露运行标签

每个结果页必须展示：

- `synthetic`
- `light_stub` / `light_real_v1`
- `not investment advice`

运行标签不得被隐藏或弱化。

### 4. UI 验收不依赖真实 DB

用 3 个冻结中文样例跑通：

- `MA5上穿MA20买入，跌破MA10卖出，止损8%`
- `D1状态属于0x23且成交量放大到20日均量1.5倍以上，MA5上穿MA20买入，止损8%，止盈15%，排除涨停`
- 仓位 30% 的变体

验收项：

- 样例 1/2 生成合法 DSL、校验通过、红线通过。
- 样例 3 被 `RL_MAX_POSITION` 红线拒绝。
- 缺止损样例被 `RL_EXIT_MUST_HAVE_STOP_LOSS` 拒绝。
- 每一步展示 `trace_id`。
- Evidence Lab 能按 `trace_id` 拉出 generation / validation / preview / backtest 记录。

### 5. 真实数据 baseline 拆为独立 Kimi handoff

Kimi 负责：

- 校验 `data/p116_foundation.duckdb`
- 校验 `data/state_cube.duckdb`
- 跑 `benchmarks/validate_real_data.py`
- 产出 `outputs/benchmarks/data_readiness_status.json`
- 若真实 DB 就绪，再跑 `benchmarks/light_backtest_perf.py` 和 `benchmarks/gate_summary.py`

Kimi 不碰 Web，不修改 benchmark 或 strategy_lab 代码来绕过数据缺失。

### 6. 明确 Phase 3 Web UI 不做的事情

- SPA / 前后端分离
- React / Vue / Angular 等前端框架
- Redux / Pinia / Zustand 等前端状态管理框架
- Agent Debate 界面
- Paper Trading 界面
- 真正的实时行情接入
- 用户认证、权限管理、多租户
- 策略分享、社区、marketplace
- 复杂图表库

## 理由

1. **MVP 可交付性优先**。Web UI 是用户可见的入口，当前后端服务已就绪，适合立即接上。
2. **避免真实数据阻塞可验证链路**。mock / synthetic 路径足够完成 UI 验收和红线检查展示。
3. **保持架构边界清晰**。Web 层只做薄层，避免业务逻辑泄漏到前端或路由层。
4. **风险提示必须可见**。`light_stub` / `synthetic` / `not investment advice` 是合规底线，必须在 UI 第一层暴露。
5. **真实数据准备独立推进**。数据采购、清洗、授权是外部依赖，不应让 UI 开发空转等待。

## 影响

- 新增 `agents/QODER_NEXT_TASK_PHASE3_WEB_UI_CONTRACT.md`。
- 新增 `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`。
- 更新 `docs/TASK_ALLOCATION.md` 增加 C20 任务记录。
- Web 层目录 `web/` 将被创建，包含 `main.py`、`strategy_lab_routes.py`、`templates/`、`static/`。
- `pyproject.toml` 可能需要调整以包含 `web/` 目录。

## 下一步

1. Qoder 输出 Phase 3 Web UI 文件级 contract。
2. Codex 按 contract 实现 `web/` 层。
3. Kimi 校验真实 DB 并产出 `data_readiness_status.json`。
4. Codex 在 Web UI 中读取 `data_readiness_status.json`，显示真实数据 readiness 状态。
5. 真实 DB 就绪后，Codex 在 UI 上启用 `light_real_v1` 选项，并更新验收脚本。

## 参考

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `agents/QODER_NEXT_TASK_PHASE3_WEB_UI_CONTRACT.md`
- `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`
- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/e2e_runner.py`
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`
