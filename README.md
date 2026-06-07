# Hermass AI Quant Platform

Agent-native quantitative strategy platform MVP.

Current MVP path:

中文策略输入 -> DSL v2 -> Schema/Pydantic 校验 -> 红线检查 -> 条件命中预览 -> Light Backtest -> 报告与审计落库。

## Current Status

Phase 0 DSL foundation is implemented under `hermass_platform/strategy_lab/`.

Verified with:

```bash
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q
/Users/lv111101/.pyenv/versions/3.11.12/bin/python -m py_compile hermass_platform/__init__.py hermass_platform/strategy_lab/__init__.py hermass_platform/strategy_lab/dsl_schema.py hermass_platform/strategy_lab/condition_registry.py hermass_platform/strategy_lab/condition_translator.py hermass_platform/strategy_lab/dsl_validator.py hermass_platform/strategy_lab/dsl_generator.py hermass_platform/strategy_lab/backtest_adapter.py
```

## Project Coordination

- Project rules: `AGENTS.md`
- Task allocation: `docs/TASK_ALLOCATION.md`
- Agent prompts: `agents/`
- Obsidian vault: `data/research/conversations/`
- Project skill draft: `skills/hermass-quant-execution/`
