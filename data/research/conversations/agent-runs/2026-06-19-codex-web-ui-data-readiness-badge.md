# Codex Web UI Data Readiness Badge 追加

## 背景

Phase 3 Web UI 已验收。用户要求主线切到真实数据 baseline handoff，同时 Codex 在 Web UI 加一个只读的 data readiness 展示位，读取 Kimi 将产出的 `outputs/benchmarks/data_readiness_status.json`。

边界：UI 里 backtest fallback 到 `light_stub` 保留，但必须持续显式标注，直到真实 DB baseline 验证完成。

## 已交付

- `web/data_readiness.py`
  - `load_data_readiness(path=None)`：读取 `outputs/benchmarks/data_readiness_status.json`。
  - 文件缺失/损坏时返回符合 contract 的 NOT_READY 默认结构。
  - `readiness_badge_class(verdict)`：映射 READY/PARTIAL/NOT_READY 到 CSS 类。
- `web/strategy_lab_routes.py`
  - 新增 `_ctx()` helper，自动为每个模板上下文注入 readiness keys。
  - 所有页面（structuring/diagnosis/evidence）都包含 readiness 上下文。
- `web/main.py`
  - 首页 index 也注入 readiness 上下文。
- `web/templates/base.html`
  - header 右侧运行标签旁显示数据基线 verdict badge。
- `web/templates/index.html`
  - 首页当前状态区域显示 readiness 中文说明与 next_steps。
- `scripts/test_web_ui_smoke.py`
  - home page 断言包含 NOT_READY / 数据基线 / 真实数据基线文案。

## 约定读取文件

```text
outputs/benchmarks/data_readiness_status.json
```

环境变量覆盖：

```bash
export DATA_READINESS_STATUS_PATH=/path/to/data_readiness_status.json
```

## 复核结果

```bash
uv run pytest hermass_platform/strategy_lab/tests -q
```

结果：`278 passed, 0 failed`

```bash
uv run python scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

结果：`5/5 cases passed`

```bash
uv run python scripts/test_web_ui_smoke.py
```

结果：5/5 passed

```bash
uv run python -m py_compile hermass_platform/strategy_lab/*.py web/*.py scripts/test_web_ui_smoke.py
```

结果：OK

## 下一步

1. Kimi 交付 `data/p116_foundation.duckdb`、`data/state_cube.duckdb` readiness 与 baseline 结果，产出 `outputs/benchmarks/data_readiness_status.json`。
2. Codex 在真实 DB 就绪后，验证 Web UI 从 NOT_READY 自动切换到 READY，并确认 `light_real_v1` 模式在 UI 上正确标注。
3. 守住边界：在真实 baseline gate summary 通过前，所有 UI 文案和运行标签不得把 `light_stub` / `synthetic` 描述为真实绩效能力。

## 参考

- `agents/KIMI_NEXT_TASK_PHASE3_REAL_BASELINE_HANDOFF.md`
- `docs/TASK_ALLOCATION.md` 中 `C20`
- `web/data_readiness.py`
