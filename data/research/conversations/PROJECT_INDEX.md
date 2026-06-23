# Hermass AI Quant Platform Vault

这是项目 Obsidian Vault 的首页。

## 快速入口

- [[decisions/0001-agent-collaboration-system]]
- [[decisions/0002-kimi-performance-data-architecture]]
- [[decisions/0003-qoder-phase-0-accepted-with-followups]]
- [[decisions/0004-phase1-preview-stop-loss-context]]
- [[decisions/0005-phase2-hot-path-gates]]
- [[decisions/0006-phase1-preview-metadata-design]]
- [[decisions/0007-factor-library-expansion-direction]]
- [[decisions/0008-broad-factor-source-evidence-governance]]
- [[decisions/0009-factor-catalog-registry-accepted]]：Codex 对 Kimi 因子目录和 Qoder Registry 规格的采纳裁决，不是提示词。
- [[decisions/0010-external-service-readiness]]：当前只允许邀请制研究试点，不允许公开商业化、投资建议、真实交易或收益承诺。
- [[decisions/0011-trade-evidence-database]]：新增交易摘要与交易事件证据库，用于记录进场/出场多周期状态、指标快照和触发条件。
- [[decisions/0012-phase2-light-backtest-contract]]：采纳 Qoder 的 `light_real_v1` 回测模块合同和 Kimi 的真实数据/性能门禁。
- [[decisions/0013-vision-milestones-key-assumptions]]：参考 S 级私董会，将 Hermass 定义为分层策略研究共同体与 AI 量化研究操作系统。
- [[decisions/0014-phase2-light-backtest-implemented]]：Phase 2 Light Backtest 实现落地，5 个新模块 + 78 个新测试，278 全量通过。
- [[decisions/0015-state-cube-architectural-positioning]]：State Cube 作为应用层与风控层核心，建立在更广泛数据基座之上。
- [[decisions/0016-phase3-web-ui-real-baseline-split]]：Phase 3 Web UI 与真实数据 baseline 拆分为并行任务，Web 层 FastAPI + Jinja2，不阻塞真实数据准备。
- [[project-docs/final-implementation-plan-summary]]
- [[skills/skill-iteration-log]]
- [[agent-runs/README]]

## SQX Local Study

- `docs/SQX_LOCAL_BLOCK_INVENTORY.md`
- `docs/FACTOR_BLOCK_LIBRARY_DESIGN_PRINCIPLES.md`
- `docs/FACTOR_SOURCE_TAXONOMY.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-factor-catalog-curation.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-factor-library-research.md`
- `data/research/conversations/agent-runs/2026-06-06-kimi-f1-factor-formula-contracts.md`
- `agents/SOURCE_FACTOR_REGISTRY_CODE_SPEC.md`
- `hermass_platform/factors/`
- `config/factors/`
- `data/research/conversations/agent-runs/2026-06-07-qoder-phase1-duckdb-preview-storage-audit.md`
- `data/research/conversations/agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-assign-kimi-github-obsidian-sync.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-github-obsidian-sync-discipline.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-external-service-readiness-pilot.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-github-stars-growth-plan.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-github-maturity-p0.md`
- `hermass_platform/strategy_lab/storage.py`
- `hermass_platform/strategy_lab/audit.py`
- `scripts/run_strategy_lab_mvp_e2e_acceptance.py`
- `docs/strategy_lab/TRADE_EVIDENCE_DATABASE_DESIGN.md`
- `data/research/conversations/decisions/0011-trade-evidence-database.md`

## Next Agent Prompts

- `agents/QODER_NEXT_TASK_PHASE1_API_PREVIEW.md`
- `agents/KIMI_NEXT_TASK_BENCHMARKS.md`
- `agents/QODER_NEXT_TASK_PHASE1_IMPLEMENTATION_PATCH.md`
- `agents/KIMI_NEXT_TASK_REAL_DATA_BENCHMARK_RUNBOOK.md`
- `agents/QODER_NEXT_TASK_PHASE1_CODE_PATCH.md`
- `agents/KIMI_NEXT_TASK_VALIDATE_AND_BENCHMARK_PATCH.md`
- `agents/KIMI_NEXT_TASK_FACTOR_LIBRARY_RESEARCH.md`
- `agents/QODER_NEXT_TASK_FACTOR_LIBRARY_ARCHITECTURE.md`
- `agents/KIMI_NEXT_TASK_STRATEGYQUANT_FACTOR_BLOCKS_RESEARCH.md`
- `agents/QODER_NEXT_TASK_BLOCK_LIBRARY_ARCHITECTURE.md`
- `agents/KIMI_NEXT_TASK_FACTOR_CATALOG_CURATION.md`
- `agents/QODER_NEXT_TASK_SOURCE_FACTOR_REGISTRY_CODE.md`
- `agents/KIMI_NEXT_TASK_F1_FACTOR_FORMULA_CONTRACTS.md`
- `agents/QODER_NEXT_TASK_FACTOR_REGISTRY_IMPLEMENTATION_PATCH.md`
- `agents/QODER_NEXT_TASK_PHASE1_DUCKDB_PREVIEW_STORAGE_AUDIT.md`
- `agents/KIMI_NEXT_TASK_PRODUCT_SCOPE_SERVICE_BOUNDARY.md`
- `agents/KIMI_NEXT_TASK_GITHUB_OBSIDIAN_SYNC_DISCIPLINE.md`
- `agents/KIMI_NEXT_TASK_EXTERNAL_SERVICE_READINESS_PILOT.md`
- `agents/KIMI_NEXT_TASK_GITHUB_STARS_GROWTH_PLAN.md`
- `agents/KIMI2_NEXT_TASK_DATA_REFRESH_REPLACEMENT_AUDIT.md`
- `agents/KIMI_NEXT_TASK_SOFT_LAUNCH_READINESS_OUTREACH_PACK.md`
- `agents/QODER_NEXT_TASK_TRADE_EVIDENCE_BACKTEST_CONTRACT.md`
- `agents/KIMI_NEXT_TASK_TRADE_EVIDENCE_DATABASE_PERFORMANCE.md`
- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_CONTRACT.md`
- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DATA_PERF_GATES.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-light-backtest-dispatch.md`
- `data/research/conversations/agent-runs/2026-06-11-qoder-phase2-light-backtest-contract.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-data-perf-gates.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-real-data-perf-gates.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-light-backtest-implementation-review.md`
- `agents/KIMI_NEXT_TASK_PHASE2_REAL_DB_BASELINE_RUN.md`
- `agents/QODER_NEXT_TASK_PHASE2_LIGHT_BACKTEST_HARDENING_REVIEW.md`
- `data/research/conversations/agent-runs/2026-06-11-codex-phase2-real-baseline-hardening-dispatch.md`
- `data/research/conversations/agent-runs/2026-06-11-kimi-phase2-real-db-baseline-run.md`
- `data/research/conversations/agent-runs/2026-06-11-qoder-phase2-light-backtest-hardening-review.md`
- `data/research/conversations/agent-runs/2026-06-18-codex-state-cube-architecture-audit.md`
- `data/research/conversations/agent-runs/2026-06-19-codex-phase3-web-ui-implementation.md`
- `data/research/conversations/agent-runs/2026-06-19-codex-web-ui-data-readiness-badge.md`
- `docs/product/VISION_MILESTONES_AND_KEY_ASSUMPTIONS.md`
- `data/research/conversations/decisions/0013-vision-milestones-key-assumptions.md`
- `data/research/conversations/agent-runs/2026-06-11-qoder-phase2-light-backtest-implemented.md`
- `data/research/conversations/decisions/0014-phase2-light-backtest-implemented.md`
- `hermass_platform/strategy_lab/backtest_models.py`
- `hermass_platform/strategy_lab/backtest_data_provider.py`
- `hermass_platform/strategy_lab/light_backtest_engine.py`
- `hermass_platform/strategy_lab/backtest_metrics.py`
- `hermass_platform/strategy_lab/backtest_evidence.py`
- `hermass_platform/strategy_lab/tests/test_backtest_data_provider.py`
- `hermass_platform/strategy_lab/tests/test_light_backtest_engine.py`
- `hermass_platform/strategy_lab/tests/test_backtest_metrics.py`
- `hermass_platform/strategy_lab/tests/test_backtest_evidence.py`
- `hermass_platform/strategy_lab/tests/test_real_light_backtest_integration.py`

## 当前目标

先交付 MVP：

中文策略输入 -> DSL v2 -> 校验 -> 红线 -> 预览 -> Light Backtest -> 报告 -> 审计。

## 记录规则

每条重要记录必须包含：

- 背景。
- 决策。
- 理由。
- 下一步。

不要把未经整理的长对话直接堆进 Vault。
