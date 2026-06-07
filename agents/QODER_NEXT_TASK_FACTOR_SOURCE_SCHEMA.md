# Qoder Next Task: Factor Source And Evidence Schema

请先读取：

1. `docs/FACTOR_SOURCE_TAXONOMY.md`
2. `docs/FACTOR_LIBRARY_EXPANSION_PLAN.md`
3. `agents/QODER_NEXT_TASK_FACTOR_LIBRARY_ARCHITECTURE.md`
4. `agents/QODER_NEXT_TASK_BLOCK_LIBRARY_ARCHITECTURE.md`
5. `AGENTS.md`

## 背景

Hermass 因子库来源会非常广，包括 SQX、Qlib、量化公司研究、基本面、消息面、资金流、订单流、交易大咖方法论和 Hermass native sources。

需要设计 source/evidence metadata schema，避免因子库变成无来源、无证据、无治理的指标堆。

## 你的任务

设计 FactorSource / Evidence / Methodology Translation 架构。

## 必须输出

### 1. Source Schema

字段：

- source_id
- source_type
- name
- url_or_local_ref
- reliability
- license_notes
- applicable_markets
- imported_at

### 2. Evidence Schema

字段：

- evidence_level: E0-E6
- evidence_type
- metric_refs
- validation_status
- last_validated_at
- failure_modes

### 3. FactorSpec 扩展

增加：

- source_refs
- evidence_level
- data_availability
- future_leakage_risk
- a_share_notes
- production_gate

### 4. BlockSpec 扩展

增加：

- source_refs
- methodology_refs
- evidence_level
- generation_weight
- production_gate

### 5. Methodology Translation Schema

字段：

- methodology_id
- source_type
- components: setup/trigger/invalidation/risk/review
- converted_blocks
- assumptions
- unsupported_parts

### 6. 测试设计

至少 20 个测试点。

## 输出文件

写入：

`agents/FACTOR_SOURCE_SCHEMA.md`

## 输出格式

```markdown
# Factor Source And Evidence Schema

## Source Schema

## Evidence Schema

## FactorSpec Extensions

## BlockSpec Extensions

## Methodology Translation Schema

## Tests

## Implementation Order
```
