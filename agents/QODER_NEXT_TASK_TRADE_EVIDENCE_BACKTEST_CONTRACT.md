# Qoder Next Task: Trade Evidence Backtest Contract

你是 Hermass AI Quant Platform 的 Qoder Architect。本轮任务是把交易证据库接入 Phase 2 Light Backtest 的接口契约设计清楚。

## 必读上下文

- `AGENTS.md`
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `data/research/conversations/decisions/0011-trade-evidence-database.md`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/dsl_schema.py`
- `hermass_platform/strategy_lab/dsl_validator.py`
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`

## 背景

Codex 已新增最小交易证据库：

- `strategy_trades`
- `strategy_trade_events`
- `save_trade_record`
- `save_trade_event_evidence`
- `list_trades`
- `list_trade_events`

现在需要 Qoder 设计 Phase 2 真实 Light Backtest 如何生成和写入这些证据。

## 任务

请输出工程契约，说明 Backtest engine 在每次 entry/exit/hold 时如何构造 trade evidence。

## 必须输出

1. Backtest event model。
2. Trade ID 生成规则。
3. Entry evidence 写入时机。
4. Exit evidence 写入时机。
5. Stop loss / take profit 证据如何记录。
6. 多周期状态字段来源。
7. 指标快照字段来源。
8. DSL condition 到 `triggered_conditions` 的映射。
9. Storage API 是否需要补字段。
10. 最小测试计划。

## 输出文件

`data/research/conversations/agent-runs/2026-06-11-qoder-trade-evidence-backtest-contract.md`

## 不做什么

- 不实现真实交易。
- 不绕过红线检查。
- 不修改 DSL v2 的核心结构。
- 不把 `light_stub` 伪装成真实回测。
