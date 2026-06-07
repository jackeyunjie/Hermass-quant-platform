# 0008 Broad Factor Source Evidence Governance

## 背景

Kimi 已完成广义因子来源研究，输出 278 条 factor/block 候选，覆盖 10 类来源：

- Strategy Generator。
- Open Quant Framework。
- Institutional。
- Academic。
- Fundamental。
- News/Event/Sentiment。
- Money Flow/Microstructure。
- Trader Methodology。
- Behavioral/Psychology。
- Hermass Native。

Qoder 已完成 Factor Source And Evidence Schema，定义 Source、Evidence、FactorSpec Extensions、BlockSpec Extensions 和 Methodology Translation。

## 决策

Hermass 因子库采用 source/evidence 治理：

- 每个 factor/block 必须有来源。
- 每个 factor/block 必须有 evidence level。
- 每个 methodology 必须拆成 setup/trigger/invalidation/risk/review。
- 未通过 evidence gate 的 factor/block 不得进入 production DSL。

Evidence gate：

- E0-E3：blocked。
- E4：candidate。
- E5-E6：approved / production。

高风险项：

- `future_leakage_risk=high` 默认 blocked。
- 数据可得性为 unavailable/requires_license 默认 blocked 或 research。
- 方法论类内容必须先转成 observable blocks。

## 理由

因子来源越广，越容易变成未经验证的概念堆。Source/Evidence Schema 可以保证广泛吸收和严格治理同时存在。

## 下一步

1. Codex 实现 source/evidence schema 的 F0 registry。
2. Kimi 的 278 候选表进入 research catalog，不直接进入 production。
3. Qoder 的 schema 用于扩展 FactorSpec 和 BlockSpec。
4. 因子进入 DSL 前必须经过 Factor Evaluation。
