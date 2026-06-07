# Qoder Next Task After Kimi Research

请先读取：

1. `AGENTS.md`
2. `docs/TASK_ALLOCATION.md`
3. `data/research/conversations/decisions/0002-kimi-performance-data-architecture.md`
4. `AI_QUANT_PLATFORM_FINAL_IMPLEMENTATION_PLAN.md`

## 背景

Kimi 已完成性能与数据架构研究。项目已采纳以下结论：

- DuckDB 负责数据加载、列裁剪、预计算指标读取、可选 `filter_first`。
- Polars 负责信号生成、权益曲线和绩效指标。
- Foundation DB MVP 预计算列包括：
  - `ma_5`
  - `ma_10`
  - `ma_20`
  - `ma_60`
  - `bb_position`
  - `atr_14`
  - `volume_ratio`
  - `adx_14`
  - `d1_state`
  - `w1_state`
  - `mn1_state`
- State Cube 查询禁止 `SELECT *`。

## 你的任务

请交付 DSL v2 MVP 的工程设计，必须能被 Codex 直接实现。

## 必须输出

1. `hermass_platform/strategy_lab/dsl_schema.py` 的 Pydantic 模型草案。
2. `hermass_platform/strategy_lab/condition_registry.py` 的条件注册表草案。
3. 每个条件的：
   - `condition_type`
   - 可用位置：`entry/filter/exit`
   - 参数 schema
   - 依赖字段
   - DuckDB 取数字段
   - Polars 表达式意图
4. `dsl_validator.py` 的语义校验规则。
5. 至少 5 个合法 DSL 样例。
6. 至少 5 个非法 DSL 样例。
7. MVP 不支持的条件和原因。

## MVP 条件范围

优先支持：

- `ma_golden_cross`
- `ma_death_cross`
- `price_cross_ma`
- `state_hex_in`
- `state_ef_count`
- `volume_ratio`
- `industry_include`
- `industry_exclude`
- `stop_loss_pct`
- `take_profit_pct`
- `limit_up_filter`

## 硬约束

- DSL 是策略唯一表达。
- 禁止执行 LLM 生成 Python。
- 缺少止损必须拒绝。
- `max_position_pct > 0.25` 必须拒绝。
- 条件依赖字段不在 Foundation DB/State Cube 可用字段内时，必须拒绝或标记为非 MVP。
- 不要设计完整 Agent Debate，不要扩展 TS-FM/RAG-KG。

## 输出格式

请按以下结构输出：

```markdown
# DSL v2 MVP Design

## Schema

## Condition Registry

## Validation Rules

## Legal Examples

## Illegal Examples

## Non-MVP Items

## Implementation Notes For Codex
```
