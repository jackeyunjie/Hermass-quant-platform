# StrategyQuant X B143 Reference Model For Hermass

## 目的

StrategyQuant X B143 的价值不只是“指标多”，而是把策略拆成可组合、可加权、可调参数、可扩展、可稳健性测试的 building blocks。

Hermass 要借鉴的是这种结构，而不是照搬外汇/期货策略模板。

## SQX 可借鉴能力

### Building Blocks

SQX 将策略组件分为：

- Signals。
- Indicators。
- Stop / Limit entry blocks。
- Order types。
- Exit types。
- Custom data indicators。

Hermass 对应：

- Signal Blocks。
- Factor Indicators。
- Entry Blocks。
- Exit Blocks。
- Order / Execution Blocks。
- External Data Factors。

### 参数空间

每个 block 不只是一个函数，还应有：

- 参数范围。
- 固定参数。
- 参数集合。
- 生成权重。
- 启用状态。
- 适用市场。
- 校准规则。

Hermass 对应：

- `parameter_space`。
- `weight`。
- `enabled`。
- `market_scope`。
- `calibration`。

### 可扩展性

SQX 通过 snippets/custom indicators/custom signals 扩展。

Hermass 对应：

- `FactorSpec`。
- `BlockSpec`。
- `ConditionSpec`。
- `Translator`。
- `Evaluator`。

所有扩展必须通过 metadata 和测试注册，禁止直接执行用户/LLM 生成代码。

### Build 143 AI

B143 强化了 AI 生成策略能力。

Hermass 对应：

- AI 只能组合注册过的 blocks。
- AI 生成 DSL，不生成 Python。
- 生成策略必须经过红线、Preview、Backtest、Walk-forward、Robustness。

### Robustness

B143 强调 StockPicker / Single Asset 的新稳健性测试和更真实的成交模型。

Hermass 对应：

- Walk-forward。
- State split。
- Industry split。
- Symbol split。
- Parameter jitter。
- Execution degradation。
- Slippage/tax/commission stress。
- Limit fill realism。

## Hermass Block Taxonomy

### Signal Blocks

- factor threshold。
- factor cross。
- factor slope。
- factor rank。
- factor percentile。
- factor divergence。
- factor regime change。
- multi-timeframe agreement。
- state transition。

### Entry Blocks

- market entry。
- breakout entry。
- pullback entry。
- limit entry。
- stop entry。
- volatility contraction entry。
- industry rotation entry。
- state resonance entry。

### Exit Blocks

- stop loss。
- take profit。
- ATR trailing。
- chandelier exit。
- indicator reversal。
- state invalidation。
- time exit。
- volatility expansion exit。
- partial exit。

### Filter Blocks

- industry include/exclude。
- market regime。
- liquidity。
- volatility。
- limit-up/down。
- ST/new stock。
- data freshness。
- macro quadrant。

### Order Blocks

- market。
- limit。
- stop。
- stop-limit。
- better limit fill。
- limit over/under。
- slippage model。
- tax/commission model。

### Robustness Blocks

- walk-forward。
- Monte Carlo trade shuffle。
- parameter jitter。
- random skip trades。
- random degrade execution。
- market regime split。
- state split。
- symbol split。
- industry split。

## F0 只做什么

F0 不实现复杂策略生成器，只建立：

- `FactorSpec`
- `BlockSpec`
- `FactorRegistry`
- `BlockRegistry`
- `factor_catalog.yaml`
- `block_catalog.yaml`
- metadata tests

## 不做什么

- 不照搬 SQX 的 Java snippets。
- 不执行 LLM 生成代码。
- 不一次性实现所有指标。
- 不把未评估 blocks 暴露给生产 DSL。
