# Factor / Block Library Design Principles

## 一句话原则

重点清晰，准备完备，架构灵活。

Hermass 不追求一开始复制 SQX 的 548 个 blocks，而是建立能持续扩展到 548+ blocks 的结构。

## 重点清晰

第一优先级不是“最多指标”，而是可产生策略闭环的核心 block：

1. Factor：可计算、可评估的底层特征。
2. Signal：把 factor 变成条件判断。
3. Entry：把信号变成入场规则。
4. Exit：把风险和失效条件变成退出规则。
5. Money Management：把信号变成仓位。
6. Robustness：证明策略不是偶然。
7. Report Columns：让结果可诊断、可比较、可复盘。

MVP+ 的优先顺序：

1. `factor_registry`
2. `block_registry`
3. technical factor catalog
4. generic signal blocks
5. exit/risk blocks
6. robustness smoke
7. factor/block evaluation report

## 准备完备

每个 factor/block 必须有 metadata，不允许只写一个函数名。

### Factor 必备字段

- `factor_id`
- `category`
- `level`
- `inputs`
- `required_tables`
- `window`
- `frequency`
- `compute_engine`
- `output_type`
- `direction`
- `normalization`
- `neutralization`
- `preview_support`
- `dsl_exposure`
- `status`
- `version`

### Block 必备字段

- `block_id`
- `block_type`
- `parameters`
- `parameter_space`
- `weight`
- `enabled`
- `required_context`
- `preview_support`
- `dsl_output`
- `market_scope`
- `robustness_role`
- `status`
- `version`

### 进入生产 DSL 前必须有

- 参数边界。
- 数据依赖。
- 未来函数检查。
- 缺失率/覆盖率。
- IC 或策略回测证据。
- State/行业/市场环境分层表现。
- 成本后表现。
- 审计记录。

## 架构灵活

### 不为每个指标写一个 DSL condition

错误方向：

- `rsi_above`
- `macd_cross`
- `adx_filter`
- `cci_above`

正确方向：

- `factor_threshold`
- `factor_cross`
- `factor_rank`
- `factor_percentile`
- `factor_slope`
- `factor_composite_score`
- `block_signal`
- `block_exit`

这样 50 个因子可以通过 6-8 个通用 DSL condition 表达。

### 不把所有 block 直接暴露给用户

block status 分层：

- `research`
- `candidate`
- `validated`
- `production`
- `deprecated`

只有 `validated` 和 `production` 才能进入正式策略模板。

### 不把 SQX 的 FX/期货假设直接搬到 A 股

A 股必须单独处理：

- T+1。
- 涨跌停。
- 停牌。
- ST。
- 新股。
- 印花税/佣金。
- 流动性。
- 复权。
- 行业/市场状态。

## 三层落地模型

### F0: Metadata First

只做：

- factor schema。
- block schema。
- catalog yaml。
- registry。
- metadata tests。

不做：

- 大量指标计算。
- 策略生成器。
- 真实交易。

### F1: MVP+ Computable Factors

先实现可计算、数据依赖稳定的因子：

- RSI。
- ROC。
- CCI。
- Stochastic。
- Williams %R。
- ADX。
- ATR。
- Bollinger width / percent b。
- Keltner Channel。
- SuperTrend。
- VWAP deviation。
- return rank。
- volatility percentile。
- turnover / amount ratio。

### F2: Evaluation And Generator

新增：

- IC/RankIC。
- 分层收益。
- 多空收益。
- 因子换手。
- robustness smoke。
- block 权重和参数空间。
- AI 组合已注册 block 生成 DSL。

## 设计红线

- 禁止执行 LLM 生成代码。
- 禁止未评估因子进入生产 DSL。
- 禁止无边界参数空间。
- 禁止没有数据依赖声明的 block。
- 禁止没有成本模型的策略验收。
- 禁止把 synthetic benchmark 当真实性能承诺。

## 当前项目行动

1. 用 SQX inventory 扩充 block taxonomy。
2. Kimi 输出 120+ block 候选表。
3. Qoder 输出 `BlockSpec` / `BlockRegistry` 架构。
4. Codex 实现 F0：metadata registry + catalog tests。
5. 再进入 F1：计算第一批高价值因子。
