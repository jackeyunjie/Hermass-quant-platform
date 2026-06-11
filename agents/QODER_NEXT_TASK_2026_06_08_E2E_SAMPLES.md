# Qoder Next Task: 2026-06-08 MVP E2E Sample Contracts

你是 Hermass 项目的 Qoder Architect。本轮任务不是扩展平台，而是把 6 月 8 日周计划里的主链路验收口径冻结成 Codex 可直接实现的 contract。

不要写泛化架构方案。请输出可执行的文件路径、接口签名、数据结构、验收标准和不做什么。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `6月 8 日工作计划.MD`
- `docs/TASK_ALLOCATION.md`
- `agents/QODER_ARCHITECT_PROMPT.md`
- `hermass_platform/strategy_lab/dsl_schema.py`
- `hermass_platform/strategy_lab/dsl_generator.py`
- `hermass_platform/strategy_lab/dsl_validator.py`
- `hermass_platform/strategy_lab/condition_registry.py`
- `hermass_platform/strategy_lab/preview_service.py`
- `hermass_platform/strategy_lab/backtest_adapter.py`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/audit.py`
- `hermass_platform/strategy_lab/api_models.py`
- `hermass_platform/strategy_lab/tests/`

## 当前判断

Strategy Lab 已有模块级能力，但缺少本周验收需要的样例级 contract：

- 3 个中文策略样例尚未冻结。
- 自然语言到 DSL 的 MVP 转换边界不清。
- Preview / Light Backtest / Audit 尚未形成一个统一 trace 的端到端入口。
- 本周问题清单还没有标准分类模板。

## 本轮目标

冻结 3 个代表性中文策略样例，并定义端到端服务级 contract，让 Codex 后续可以直接实现：

`中文策略输入 -> DSL v2 -> Schema/Pydantic 校验 -> 红线检查 -> Preview -> Light Backtest -> Audit -> 问题归档`

## 必须交付

### 1. 3 个中文策略样例 contract

请新增或修改一个样例 contract 文件，建议路径：

- `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`

每个样例必须包含：

- `sample_id`
- 原始中文输入
- 策略复杂度分类：simple / medium / bounded_complex
- 期望 DSL v2 完整 JSON
- 使用到的 condition types
- 默认参数来源说明
- 预期 validator 结果
- 预期 red_line_result
- 预期 preview 行为
- 预期 light backtest 最小输出
- 预期 audit operations 顺序
- 明确不支持的解释

建议 3 个样例：

1. `sample_ma_5_20_stop_8`
   - 中文输入：`MA5上穿MA20买入，跌破MA10卖出，止损8%`
   - 类型：simple
   - 目标：覆盖 MVP 验收底线第一条。

2. `sample_state_volume_stop_8_take_15`
   - 中文输入：`D1状态属于0x21或0x23，成交量放大到20日均量1.5倍以上买入，止损8%，止盈15%`
   - 类型：medium
   - 目标：覆盖 `state_hex_in`、`volume_ratio`、`stop_loss_pct`、`take_profit_pct`。

3. `sample_ma_state_limit_filter`
   - 中文输入：`MA5上穿MA20且D1状态EF数量不少于2时买入，排除涨停股票，跌破MA10或止损8%卖出`
   - 类型：bounded_complex
   - 目标：覆盖组合条件、filter、OR exit。

如你认为样例 2 或 3 的条件类型与现有 registry 不完全匹配，请不要换成泛化新条件；请明确给出最小映射或建议 Codex 在现有 condition type 内实现。

### 2. MVP 中文输入到 DSL 的确定性映射规则

请定义本周只支持的映射规则，不要引入真实 LLM：

- 支持哪些中文短语。
- 每个短语映射到哪个 `condition_type`。
- 参数如何抽取。
- 未出现仓位时默认 `risk.max_position_pct` 是多少。
- 未出现 `risk_per_trade` 时默认是多少。
- 缺少止损时如何生成失败样例或直接拒绝。
- “跌破 MA10 卖出”应映射为 `price_cross_ma` 还是需要新增/调整 registry，请给出明确裁决。

输出必须能转成函数或表驱动 parser。

### 3. 端到端入口 contract

请给出 Codex 后续要实现的 service-level 入口，建议文件：

- `hermass_platform/strategy_lab/e2e_runner.py`

建议接口：

```python
def run_mvp_e2e_sample(
    natural_language: str,
    strategy_id: str,
    *,
    trace_id: str,
    audit_db_path: str,
    storage_db_path: str,
    preview_data_source: Literal["mock", "duckdb"] = "mock",
    preview_duckdb_path: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> MvpE2EResult:
    ...
```

请定义 `MvpE2EResult` 字段，至少包含：

- `trace_id`
- `strategy_id`
- `dsl`
- `validation`
- `red_line_result`
- `preview`
- `backtest`
- `audit_records`
- `problem_items`
- `status`

### 4. Light Backtest 本周最小口径

当前 `backtest_adapter.py` 仍是 stub。本周不要要求完整真实回测。

请明确本周最小验收是否允许 stub metrics，但必须满足：

- 只有通过红线检查才允许执行。
- 返回 `status`。
- 返回核心指标字段：`total_return`、`annual_return`、`max_drawdown`、`sharpe_ratio`、`win_rate`、`profit_factor`、`trade_count`。
- 写入 storage 和 audit。
- 在结果里标注是否为 `stub` 或 `light_mock`，避免误认为真实绩效。

### 5. Audit 事件顺序

请定义同一 `trace_id` 下必须写入的 operation 顺序：

1. `generation`
2. `validation`
3. `preview`
4. `backtest`

每个 operation 必须记录：

- `trace_id`
- `strategy_id`
- `dsl_version`
- `input_hash`
- `output_hash`
- `red_line_result`

失败链路也必须写 audit。例如缺少止损时，应写入 generation + validation，不执行 preview/backtest。

### 6. 问题清单模板

请给出问题归档数据结构，四类必须固定：

- `definition`
- `implementation`
- `data`
- `acceptance`

每条问题至少包含：

- `sample_id`
- `category`
- `stage`
- `summary`
- `evidence`
- `owner`
- `next_action`

## 验收标准

你的输出必须让 Codex 后续可以实现并验收：

1. 输入 `MA5上穿MA20买入，跌破MA10卖出，止损8%` 能生成合法 DSL。
2. 缺少止损的 DSL 或中文输入被拒绝，且 red-line 结果可审计。
3. 仓位超过 25% 的 DSL 被红线拒绝。
4. 3 个样例都能生成 preview，至少 mock 模式稳定返回命中数量。
5. 3 个样例都能返回 Light Backtest 最小指标，并明确标注 stub/light_mock。
6. 每个样例的 generation、validation、preview、backtest 都能通过同一 `trace_id` 查到审计记录。
7. 失败样例不会执行 preview/backtest。

## 不做什么

- 不新增真实 LLM 接入。
- 不执行 LLM 生成代码。
- 不扩因子库。
- 不新增外部数据源。
- 不实现完整真实 backtest engine。
- 不实现 Web 路由。
- 不做 Agent Debate DAG。
- 不做 Paper Trading。
- 不做 TS-FM / RAG-KG。
- 不改 benchmark。
- 不改 factors registry，除非你证明现有 condition type 无法表达本周样例。

## 输出记录

完成后写入：

`data/research/conversations/agent-runs/2026-06-08-qoder-mvp-e2e-sample-contracts.md`

格式：

```markdown
# Qoder MVP E2E Sample Contracts

## Files Added Or Modified

## Frozen Samples

## NL To DSL Mapping Rules

## E2E Runner Contract

## Light Backtest Minimum Contract

## Audit Contract

## Problem List Template

## Acceptance Criteria

## Not Doing

## Next Steps For Codex
```
