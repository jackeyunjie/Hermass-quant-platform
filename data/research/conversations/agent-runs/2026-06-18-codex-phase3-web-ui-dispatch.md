# Codex Agent Run: Phase 3 Web UI Dispatch

## 日期

2026-06-18

## 背景

用户明确指示：同意将 Phase 3 Web UI 作为主线启动，同时把真实数据 baseline 明确拆成独立 handoff，不互相阻塞。

当前仓库状态：

- `hermass_platform/strategy_lab/` 主链路已成形。
- Web 层尚未落地。
- 真实数据 `data/p116_foundation.duckdb` 和 `data/state_cube.duckdb` 缺失，继续阻塞 real baseline。

## 决策

Codex 按用户意见裁决：

1. Phase 3 Web UI 作为主线立刻启动。
2. 真实数据 baseline 拆为独立 Kimi handoff，不阻塞 Web UI。
3. Web UI 范围严格收缩为 3 个页面 + FastAPI + Jinja2 + 现有 service 契约。
4. UI 必须显式暴露运行标签和免责声明。
5. UI 验收不依赖真实 DB。

## 已派发任务

### Qoder

- 任务文件：`agents/QODER_NEXT_TASK_PHASE3_WEB_UI_CONTRACT.md`
- 目标：输出 Phase 3 Web UI 工程契约，包含文件级 contract 和 Non-MVP Items。

### Kimi

- 任务文件：`agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`
- 目标：校验真实 DB、跑 `validate_real_data.py`、产出 `data_readiness_status.json`。

## 已更新项目资产

- `docs/TASK_ALLOCATION.md` 增加 C20。
- `data/research/conversations/decisions/0016-phase3-web-ui-real-baseline-split.md`

## 下一步

1. 等待 Qoder 回传 Web UI contract。
2. Codex 按 contract 实现 `web/` 层。
3. 等待 Kimi 回传 data readiness 状态。
4. Codex 在 UI 上集成 readiness 显示。

## 不做什么

- 不现在就直接写 Web UI 代码，等 Qoder contract。
- 不等真实 DB 就绪再启动 Web UI。
- 不扩展 Agent Debate / Paper Trading / 实时行情。
