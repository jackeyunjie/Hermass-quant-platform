# Trade Evidence Database Design

本设计用于把每笔交易的入场、持仓、出场证据沉淀为可查询的大数据库。

目标不是直接做自动交易，而是建立可复盘、可审计、可统计的策略证据库：

```text
strategy DSL
  -> red-line validation
  -> preview/backtest/simulation
  -> trade record
  -> entry/hold/exit evidence snapshots
  -> strategy improvement dataset
```

## Core Principle

每笔交易必须保存两层信息：

1. `strategy_trades`：一笔交易的标准摘要。
2. `strategy_trade_events`：交易过程中的事件级证据快照。

事件级证据必须覆盖：

- 事件类型：`entry` / `hold` / `exit` / `stop_loss` / `take_profit` / `manual_review`。
- 时间与价格。
- 多周期状态：例如 `MN1`、`W1`、`D1`、`H4`、`H1`。
- 指标快照：例如 MA、ATR、volume_ratio、state_hex、rsi、macd、bb_position。
- 触发条件：对应 DSL 中的 entry/filter/exit condition。
- trace_id：和 generation / validation / preview / backtest audit 串起来。

## Tables

### strategy_trades

交易摘要表，一笔交易一行。

| Column | Purpose |
| --- | --- |
| `trade_id` | 全局唯一交易 ID |
| `strategy_id` | 策略 ID |
| `trace_id` | 本次策略执行 trace |
| `symbol` | 标的 |
| `side` | `long` / `short`，MVP 先只允许 `long` |
| `status` | `open` / `closed` / `cancelled` |
| `entry_time` | 入场时间 |
| `entry_price` | 入场价格 |
| `exit_time` | 出场时间 |
| `exit_price` | 出场价格 |
| `quantity` | 数量 |
| `pnl` | 收益金额 |
| `pnl_pct` | 收益率 |
| `created_at` | 落库时间 |

### strategy_trade_events

交易事件证据表，一笔交易多行。

| Column | Purpose |
| --- | --- |
| `id` | 事件自增 ID |
| `trade_id` | 关联交易 |
| `strategy_id` | 策略 ID |
| `trace_id` | 本次策略执行 trace |
| `symbol` | 标的 |
| `event_type` | `entry` / `hold` / `exit` 等 |
| `event_time` | 事件时间 |
| `price` | 事件价格 |
| `timeframe_states` | 多周期状态 JSON |
| `indicator_snapshot` | 指标快照 JSON |
| `triggered_conditions` | 触发条件 JSON |
| `notes` | 备注 |
| `created_at` | 落库时间 |

## JSON Contracts

### timeframe_states

```json
{
  "MN1": "0x11",
  "W1": "0x21",
  "D1": "0x23",
  "H4": "0x31",
  "H1": "0x32"
}
```

State 值来自 Hermass `state_hex`，支撑多周期状态复盘。

### indicator_snapshot

```json
{
  "D1": {
    "close": 10.8,
    "ma_5": 10.6,
    "ma_10": 10.9,
    "ma_20": 10.1,
    "volume_ratio_20": 1.7,
    "atr_14": 0.42,
    "state_hex": "0x23"
  },
  "H1": {
    "close": 10.8,
    "rsi_14": 58.0
  }
}
```

指标快照按 timeframe 分组，避免列爆炸。Phase 2 可再把高频查询指标抽成宽表或物化视图。

### triggered_conditions

```json
[
  {
    "section": "entry",
    "condition_type": "ma_golden_cross",
    "params": {
      "fast_period": 5,
      "slow_period": 20
    }
  }
]
```

触发条件必须能回溯到 DSL condition。

## MVP Acceptance

本阶段只要求：

- 能创建 `strategy_trades` 和 `strategy_trade_events`。
- 能写入一笔交易摘要。
- 能写入 entry 和 exit 两个事件快照。
- 能读取并保持 JSON 字段不丢失。
- 能通过 `trace_id` 和 `strategy_id` 查询交易。

验收命令：

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests/test_storage.py -q
```

## Phase 2 Extension

真实 Light Backtest 接入后：

- 每次交易生成 `strategy_trades`。
- 每次入场/出场生成 `strategy_trade_events`。
- `stop_loss_pct` 和 `take_profit_pct` 必须落为 exit evidence。
- 交易事件必须记录当时红线检查结果或 trace 可回溯到 validation audit。

## Big Database Roadmap

后续可以把证据库扩展为策略大数据库：

- `strategy_trade_features`：把常用指标 JSON 展开成训练/统计特征宽表。
- `strategy_state_outcomes`：按多周期 state 统计胜率、盈亏比、持仓周期。
- `strategy_condition_outcomes`：按 DSL condition 统计触发后表现。
- `strategy_regime_outcomes`：按市场环境/行业/指数状态统计。
- `strategy_iteration_memory`：记录策略修改原因和结果变化。

这些扩展必须等真实数据审计和真实 Light Backtest 完成后再进入生产链路。

## Non-Goals

- 不记录真实交易账户。
- 不接券商下单。
- 不给买卖建议。
- 不把回测收益当真实绩效。
- 不绕过红线检查。
