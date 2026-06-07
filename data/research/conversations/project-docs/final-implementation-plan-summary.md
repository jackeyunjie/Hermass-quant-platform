# Final Implementation Plan Summary

## 一句话

Hermass AI Quant Platform 是一个 DSL-first 的 AI 量化策略平台。自然语言只是入口，核心是确定性 DSL、回测、红线、Agent 评审和持续复盘。

## MVP

中文策略输入 -> DSL v2 -> Schema/Pydantic 校验 -> 红线检查 -> 条件命中预览 -> Light Backtest -> 报告与审计落库。

## 关键约束

- Web 层只做入口。
- DSL 是策略唯一表达。
- 禁止执行 LLM 生成代码。
- 红线不可绕过。
- 前沿研究隔离。

## 最大风险

- LLM 解析歧义。
- 回测性能不达标。
- Agent 输出无法长期证明有用。
- 范围过大导致 MVP 延迟。

## 当前裁剪

Phase 0/1 不做完整 Debate、Paper Trading、TS-FM、RAG-KG。只预留接口，先跑通确定性策略链路。
