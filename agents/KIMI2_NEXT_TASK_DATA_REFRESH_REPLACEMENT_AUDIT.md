# Kimi2 Next Task: Data Refresh / Supplement / Replacement Necessity Audit

你是 Hermass AI Quant Platform 的 Kimi Research Engineer（数据与性能方向）。本轮任务不是立即更换数据源，而是对当前所有数据资产做一次系统性审计，判断在 MVP、Phase 2 真实回测、邀请制试点和 public beta 各阶段前，哪些数据需要冻结、刷新、补充、替换或推迟。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `data/research/conversations/decisions/0002-kimi-performance-data-architecture.md`
- `data/research/conversations/decisions/0010-external-service-readiness.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`
- `benchmarks/validate_real_data.py`
- `benchmarks/_synthetic.py`
- `config/factors/source_catalog.yaml`
- `hermass_platform/factors/source_schema.py`
- `hermass_platform/strategy_lab/backtest_adapter.py`
- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`

## 背景

当前项目数据状态：

- MVP 样例链路使用 deterministic mock / synthetic preview，不依赖真实历史数据。
- `benchmarks/` 有 synthetic fixture 和真实数据验证脚本，但真实数据（`p116_foundation.duckdb`、`state_cube.duckdb` 等）可能未完全就绪。
- Light Backtest 当前为 `light_stub`，返回占位指标，明确标注 `"_mode": "light_stub"`。
- K11 判定：public beta 前必须完成真实 Light Backtest；邀请制试点可在 stub 模式下进行，但必须防止用户误读。

Codex 判断：

- MVP 样例级链路可以继续冻结现有 mock/synthetic，不因真实数据缺口阻塞。
- 真实 Light Backtest、邀请制试点、GitHub demo 和 public beta 前，必须完成数据审计。
- 当前不应默认"换数据源"，应逐类判断 `freeze`、`refresh`、`supplement`、`replace` 或 `defer`。

## 本轮目标

输出一份数据资产审计与决策文档，回答：

1. 当前有哪些数据资产？状态如何？
2. 每类数据在 MVP / Phase 2 / 试点 / public beta 各阶段需要什么状态？
3. 哪些数据缺口阻塞下一阶段？
4. `light_stub` 被用户误读为真实绩效的风险如何缓解？
5. 数据授权、复权口径、幸存者偏差、未来函数等隐性风险有哪些？

## 必须输出

### 1. Data Inventory

盘点当前所有数据资产：

| 数据名称 | 类型 | 当前状态 | 位置 | 最后更新 | 备注 |
|----------|------|----------|------|----------|------|
| `p116_foundation.duckdb` | 真实数据 | 待确认 | `data/` | 待确认 | 预计算指标 |
| `state_cube.duckdb` | 真实数据 | 待确认 | `data/` | 待确认 | 状态聚合 |
| `market_assets.duckdb` | 真实数据 | 待确认 | `data/` | 待确认 | 标的元数据 |
| Blackwolf daily | 外部数据 | 待确认 | 外部 | 待确认 | 日线行情 |
| Blackwolf moneyflow | 外部数据 | 待确认 | 外部 | 待确认 | 资金流 |
| factor registry (YAML) | 配置 | 已就绪 | `config/factors/` | 2026-06-06 | F0/F1/F2 |
| synthetic fixture | 合成数据 | 已就绪 | `benchmarks/_synthetic.py` | 2026-06-06 | 基准测试用 |
| mock preview | 模拟数据 | 已就绪 | `hermass_platform/strategy_lab/preview_service.py` | 2026-06-07 | 命中估算 |
| `light_stub` output | 占位输出 | 已就绪 | `hermass_platform/strategy_lab/backtest_adapter.py` | 2026-06-08 | 回测占位 |

### 2. Verdict

给出总 verdict，只允许以下之一：

- `NO_CHANGE_FREEZE`：当前数据完全够用，全部冻结。
- `REFRESH_REQUIRED`：部分数据需要刷新（更新到最新时间）。
- `SUPPLEMENT_REQUIRED`：需要补充新数据（新字段、新表、新来源）。
- `REPLACE_REQUIRED`：部分数据需要替换（质量不达标或授权问题）。
- `MIXED`：不同数据类别有不同决策。

默认应为 `MIXED` 或 `NO_CHANGE_FREEZE`，除非有明确证据支持其他结论。

### 3. Decision Matrix

对每类数据给出决策矩阵：

| 数据类别 | MVP | Phase 2 真实回测 | 邀请制试点 | Public Beta | 决策 |
|----------|-----|------------------|------------|-------------|------|
| 预计算指标 | freeze | refresh? | refresh? | refresh | |
| 状态聚合 | freeze | supplement? | freeze | supplement | |
| 行情数据 | freeze | replace? | freeze | replace | |
| 资金流 | defer | defer | defer | supplement | |
| 行业分类 | freeze | refresh | freeze | refresh | |
| 复权因子 | freeze | refresh | freeze | refresh | |
| synthetic fixture | freeze | freeze | freeze | freeze | |
| mock preview | freeze | freeze | freeze | replace | |
| light_stub | freeze | replace | freeze | replace | |

决策选项：`freeze`、`refresh`、`supplement`、`replace`、`defer`。

### 4. Blocking Analysis

明确哪些数据缺口阻塞哪些阶段：

| 阻塞条件 | 阻塞阶段 | 缓解方案 |
|----------|----------|----------|
| 无真实历史行情 | Phase 2 真实回测 | 使用 synthetic 或延迟启动 |
| 数据过旧（>6个月） | 邀请制试点 | 标注数据截止日期 |
| 无复权处理 | 真实回测 | 补充复权因子表 |
| 幸存者偏差 | Public Beta | 补充退市/停牌记录 |
| 授权不明确 | 任何对外阶段 | 确认授权或替换数据源 |

### 5. Light Stub Misinterpretation Risk

分析 `light_stub` 被误读的风险：

- 当前标注是否足够：`metrics["_mode"] = "light_stub"` + `risk_flags = ["STUB_BACKTEST"]`
- UI 层是否需要额外标注。
- 用户测试是否发现误读。
- 邀请制试点中如何防止误读。

### 6. Hidden Risks

覆盖以下隐性风险：

- **数据过旧**：最后更新日期距今天数。
- **未来函数**：预览/回测中是否使用了未来信息。
- **复权口径**：前复权/后复权是否一致。
- **幸存者偏差**：是否只包含存活标的。
- **停牌退市**：停牌期间如何处理。
- **行业分类漂移**：行业分类是否随时间变化。
- **授权风险**：数据来源是否有合法授权。
- **Mock 被误解**：mock 数据是否被当作真实数据。

### 7. Data Contract For Real Backtest

给出真实 Light Backtest 前的数据契约：

- 需要哪些表、哪些字段、哪些索引。
- 数据时间范围。
- 数据质量检查命令。
- 验证通过标准。

### 8. Next Steps

按优先级列出 Codex 需要执行的数据任务。

## 输出文件

请写入：

`data/research/conversations/agent-runs/2026-06-11-kimi2-data-refresh-replacement-audit.md`

## 输出格式

```markdown
# Data Refresh / Supplement / Replacement Necessity Audit

## Data Inventory

## Verdict

## Decision Matrix

## Blocking Analysis

## Light Stub Misinterpretation Risk

## Hidden Risks

## Data Contract For Real Backtest

## Next Steps For Codex

## Risks

## Handoff For GitHub Sync
```

## 验收标准

- 结论明确，不含模糊话术。
- 默认 verdict 为 `NO_CHANGE_FREEZE` 或 `MIXED`。
- 每类数据有明确的 `freeze`/`refresh`/`supplement`/`replace`/`defer` 决策。
- 明确哪些数据缺口阻塞哪些阶段。
- 覆盖数据过旧、未来函数、复权口径、幸存者偏差、停牌退市、行业分类漂移、授权风险和 mock 被误解风险。
- 给出真实 Light Backtest 前的数据契约和验证命令。
- 按 K10 同步纪律输出 GitHub / Obsidian handoff。

## 不做什么

- 不直接更换数据源。
- 不删除现有数据。
- 不阻塞 MVP 样例链路。
- 不承诺数据质量达标。
- 不替 Codex 做最终数据采购决策。
