# 0007 Factor Library Expansion Direction

## 背景

用户要求将底层因子库极大扩展，目标是高配，并借鉴成熟项目。

当前 Hermass MVP 仅有趋势、State、量能、行业过滤和基础风控条件，足够 Strategy Lab MVP，但不够成熟平台。

## 决策

采用分层因子库路线：

- L0 Raw Inputs。
- L1 Technical Factors。
- L2 Cross-Sectional Factors。
- L3 Fundamental Factors。
- L4 Money Flow / Microstructure。
- L5 Hermass-Specific Factors。

先实现 Factor Registry 和 Factor Metadata，不直接大规模堆计算。

## 借鉴对象

- Qlib：Alpha158/Alpha360、DataHandler、Processor、横截面标准化。
- QuantConnect LEAN：大规模 indicator library 和 indicator abstraction。
- Alphalens：IC、分层收益、factor tear sheet。
- TA-Lib / pandas-ta：技术指标分类。

## 原则

- 未评估因子不进入生产 DSL。
- 因子必须有 metadata、数据依赖、计算窗口、方向、归一化、评估记录。
- DSL 使用通用 factor conditions，不为每个因子创建单独 condition。
- 因子评估闭环比因子数量更重要。

## 下一步

1. Kimi 输出 50+ 因子优先级和数据依赖。
2. Qoder 输出 Factor Registry 架构。
3. Codex 实现 F0 registry/catalog/tests。
