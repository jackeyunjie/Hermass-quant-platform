# 0005 Phase 2 Hot Path Gates

## 背景

Kimi 已完成真实数据 benchmark runbook，明确 Phase 2 回测引擎需要用真实 DuckDB 数据验证，而不是只依赖 synthetic benchmark。

## 决策

采纳 Kimi 的 Phase 2 Hot Path Gates 作为后续回测引擎验收标准。

性能门槛：

- Light Backtest 5000 × 252 P95 < 30s。
- 数据加载 P95 < 10s。
- 信号生成 P95 < 12s。
- 权益曲线 + 指标 P95 < 8s。
- 内存峰值 < 4GB。

禁止模式：

- `apply(lambda row`
- `iterrows`
- `for row in`
- pandas 中间转换
- `SELECT *` in hot path
- Python 级分组循环
- `eval` / `exec`

真实数据 benchmark 被采纳为验收依据前，必须先通过 `benchmarks/validate_real_data.py` 体检。

## 理由

Synthetic benchmark 只能证明脚本可运行和热路径结构合理，不能代表真实 A 股数据的 I/O、停牌、涨跌停、缺失日期和索引状态。

## 下一步

1. Codex 实现 `benchmarks/validate_real_data.py`。
2. 改进 benchmark：分阶段计时，增加 `--symbols/--days/--runs`。
3. Phase 2 开始前锁定 DuckDB/Polars 版本。
4. 真实数据就绪后跑 `*_real_YYYYMMDD.jsonl`，保存在 `outputs/benchmarks/`。
