# 0015 State Cube 架构定位：应用层与风控层的核心

## 背景

在 Phase 2 Light Backtest 实现与 hardening 过程中，State Cube 与 Foundation DB 的边界反复被讨论。Kimi 的真实数据 runbook 把 `p116_foundation.duckdb` 和 `state_cube.duckdb` 并列为 Phase 2 数据基座；Qoder 的 hardening review 则发现 State Cube 被 preview、backtest、evidence 多层同时依赖，但缺少明确的架构分层说明。

审计结论：

> State 系统应作为应用层与风控层的核心，建立在更广泛的数据基座之上。

本决策记录把这条结论固化为工程边界。

## 决策

### 1. 明确三层数据架构

```text
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Application & Risk-Control                         │
│ - Strategy Lab (generate / validate / preview / backtest)   │
│ - Red-line validation                                       │
│ - Trade evidence & audit                                    │
│ - State-driven entry / filter / exit / hold decisions       │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: State / Regime Cube                                │
│ - MN1 / W1 / D1 / H4 / H1 state_hex                         │
│ - EF width, EF count, boundary distance                     │
│ - Multi-timeframe resonance & regime classification         │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Data Foundation                                    │
│ - OHLCV (open/high/low/close/volume/amount)                 │
│ - Tradability flags (limit_up/limit_down/suspended/ST/IPO)  │
│ - Pre-computed indicators (MA/BB/ATR/ADX/volume_ratio)      │
│ - Industry / concept classification                         │
│ - Money flow (Blackwolf, level-1/level-2 aggregates)        │
│ - Fundamental data (valuation/profitability/quality/growth) │
│ - Macro / market breadth                                    │
└─────────────────────────────────────────────────────────────┘
```

### 2. State Cube 不是 L0 Raw Input

在因子库分层中，State Cube 原被列在 `L0 Raw Inputs`。从现在起：

- **L0 Raw Inputs** 只保留可直接观测、未解释的数据：OHLCV、交易状态、行业分类、资金流、基本面、宏观数据。
- **L0.5 State / Regime Layer** 作为新增分层，承接从 L0 计算得到的 market-state 抽象。
- State Cube 属于 L0.5，不是 L0。

### 3. State Cube 是应用层与风控层的核心输入

State Cube 在应用层承担以下角色：

- **Entry regime filter**: `state_hex_in` 决定策略只在特定市场状态下入场。
- **Volume-state composite**: `state_ef_count` 把量能与状态空间结构结合。
- **Hold / exit context**: 每笔交易的 evidence 必须包含多周期 state 快照。
- **Risk control**: Risk Guardian 和 red-line 检查可基于 state 判断策略是否匹配当前 regime。

### 4. Foundation DB 负责“更广泛的数据基座”

`p116_foundation.duckdb` 是 L0 数据的主存储，必须能够：

- 独立支撑无 State Cube 的回测（`include_state=false`）。
- 为 State Cube 计算提供原始输入。
- 承载预计算指标，避免运行时再算所有指标。

`state_cube.duckdb` 可以是独立文件，也可以是 foundation DB 内的一张物化表，但逻辑上属于 L0.5。

### 5. 模块边界

- `backtest_data_provider.py` 同时连接 foundation_db 与 state_cube_db，但内部必须区分 L0 与 L0.5 来源。
- `light_backtest_engine.py` 消费标准化后的 `d1_state` / `w1_state` / `mn1_state` 等列，不直接读原始 state 字段。
- `backtest_evidence.py` 必须记录 `timeframe_states` JSON，作为 State Cube 在交易证据中的落地。

## 理由

1. **防止 State Cube 被误当作普通因子**。State 是对市场结构的抽象解释，带有方法论假设，需要单独评估其有效性和未来函数风险。
2. **让 Foundation DB 独立可验证**。真实数据基线（M2）可以先验证 OHLCV、指标、 tradability 字段的正确性，再叠加 State Cube。
3. **支撑风控层设计**。Risk Guardian 未来可以基于 State Cube 做 regime-based 风险规则，例如“禁止在 H1/H4 共振为 bear 时追涨”。
4. **与 Hermass 差异化护城河一致**。State Cube 是 Hermass 自有方法论的外化，必须在架构上被显式突出，而不是淹没在因子列表里。

## 影响

- `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md` 中 L0 描述需要更新，增加 L0.5 State / Regime Layer。
- `docs/FACTOR_SOURCE_TAXONOMY.md` 中 S10 需要说明 State Cube 作为应用/风控层核心。
- 新增 `docs/design/DATA_FOUNDATION_AND_STATE_CUBE_ARCHITECTURE.md` 描述三层架构。
- 代码层面无需破坏性修改；`BacktestDataProvider` 已经通过 `include_state` 参数体现该分层。

## 下一步

1. Qoder 在 DSL v2 / 条件注册表扩展时，把 State 相关条件标记为 `layer: l0.5_state`。
2. Kimi 在真实数据 runbook 中区分 `foundation_db readiness` 与 `state_cube readiness` 两个 gate。
3. Codex 在实现 Risk Guardian 模块时，优先复用 State Cube 而不是直接读 L0 指标。
4. Phase 3 产业链 Agent 接入时，产业链传播结果进入 State / Regime Layer，而不是直接作为 raw input。

## 参考

- `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
- `docs/FACTOR_SOURCE_TAXONOMY.md`
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `hermass_platform/strategy_lab/backtest_data_provider.py`
- `hermass_platform/strategy_lab/backtest_evidence.py`
