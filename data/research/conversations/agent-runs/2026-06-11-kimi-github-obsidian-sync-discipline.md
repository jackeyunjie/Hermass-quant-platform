# GitHub And Obsidian Sync Discipline

## Background

当前项目已有大量 Agent 产物、任务文档、验收脚本和 Vault 记录。风险不是缺少资料，而是 GitHub 与 Obsidian 不及时同步，导致：

- GitHub 代码状态与本地任务状态不一致。
- Obsidian Vault 缺少最新决策与运行摘要。
- 后续 Agent 接手时重复阅读旧上下文。
- 已通过的 MVP 验收无法被追踪到对应提交或 Vault 记录。

本任务目标是让 Kimi 建立一个可执行的同步机制，并在每次研究/任务交付后主动产出同步证据。

## Sync Policy

### GitHub 应同步的内容

| 类别 | 示例 | 理由 |
|------|------|------|
| 源码 | `hermass_platform/**/*.py` | 核心资产，必须版本控制 |
| 测试 | `hermass_platform/**/tests/*.py` | 验收依据 |
| 任务提示词 | `agents/KIMI_NEXT_TASK_*.md`, `agents/QODER_NEXT_TASK_*.md` | Agent 可复用上下文 |
| 正式文档 | `docs/*.md`, `README.md` | 项目知识资产 |
| 可复用脚本 | `scripts/*.py`, `benchmarks/*.py` | 可执行验收工具 |
| 配置 | `pyproject.toml`, `config/**/*.yaml` | 构建与运行依赖 |
| Vault 整理后决策 | `data/research/conversations/decisions/*.md` | 工程决策追踪 |
| Vault 整理后运行摘要 | `data/research/conversations/agent-runs/*.md` | 可复现证据 |
| Skill | `skills/**/*.md` | 可复用流程 |

### GitHub 不应同步的内容

| 类别 | 示例 | 处理方式 |
|------|------|----------|
| 运行产物 | `outputs/**/*.jsonl`, `outputs/**/*.json`, `outputs/**/*.duckdb` | 本地保留，`.gitignore` 已覆盖 |
| 临时 DuckDB | `*_tmp.duckdb`, `*.db-journal` | 不提交 |
| 缓存 | `.pytest_cache/`, `__pycache__/`, `*.pyc` | `.gitignore` 已覆盖 |
| 敏感凭据 | `.env`, `*.key`, `token.json` | 不提交，如误加立即 `git rm --cached` |
| 未经整理的长对话 | 原始 LLM 输出、多轮无结构记录 | 压缩为 agent-runs 摘要后再考虑 |
| 个人工作计划 | `6月8日工作计划.MD` 等 | 本地保留，不进仓库 |
| 大文件 | >10MB 的数据文件、模型文件 | 放对象存储或本地 |

### Obsidian Vault 应同步的内容

| 类别 | 路径 | 要求 |
|------|------|------|
| 工程决策 | `data/research/conversations/decisions/*.md` | 必须包含：背景、决策、理由、下一步 |
| Agent 运行摘要 | `data/research/conversations/agent-runs/YYYY-MM-DD-*.md` | 必须包含：目标、交付、验收、风险、下一步 |
| 阶段复盘 | `data/research/conversations/daily/` | 每日/每周状态快照 |
| Skill 迭代记录 | `data/research/conversations/skills/*.md` | 可复用流程的演进 |
| 项目索引 | `data/research/conversations/PROJECT_INDEX.md` | 必须随新增文件更新 |

### Obsidian Vault 不应同步的内容

| 类别 | 示例 | 理由 |
|------|------|------|
| 无上下文垃圾片段 | 单句记录、无头无尾的想法 | 污染 Vault |
| 重复日志 | 同一验收命令跑多次且无差异 | 只保留最新 |
| 未压缩的大段终端输出 | 完整 pytest 输出、traceback | 只保留结论和关键错误 |
| 敏感凭据 | API key、数据库连接串 | 安全红线 |
| 原始 LLM 多轮对话 | 未经提炼的完整对话记录 | 先压缩为结构化摘要 |

## GitHub Sync Checklist

每次 Kimi 交付后执行：

- [ ] `git status --short` — 查看未提交变更
- [ ] `git diff --stat` — 确认变更范围合理
- [ ] `git diff -- <关键文件>` — 检查关键 diff 无敏感信息
- [ ] 验收命令是否已运行并记录结果
- [ ] 是否误包含 `outputs/`、缓存、临时 DB — 如有，`git reset HEAD <file>`
- [ ] 是否包含 token/cookie/密钥 — 如有，立即移除并轮换
- [ ] 编写 commit message（格式见下方）
- [ ] 如具备 push 权限：`git add <files>` -> `git commit -m "..."` -> `git push`
- [ ] 如无 push 权限：按 Handoff Template 产出交接文档

### Commit Message 格式

```
[<agent>] <type>: <short summary>

- <detail 1>
- <detail 2>

验收: <command> -> <result>
```

示例：
```
[kimi] research: K9 product scope and K10 sync discipline

- Add K9 product scope service boundary prompt
- Add K10 GitHub/Obsidian sync discipline prompt
- Update TASK_ALLOCATION.md with K9/K10
- Update PROJECT_INDEX.md with new entries

验收: N/A (prompt and doc tasks)
```

## Obsidian Sync Checklist

每次 Kimi 交付后执行：

- [ ] 是否新增 `data/research/conversations/agent-runs/YYYY-MM-DD-*.md`
- [ ] 是否需要新增 `decisions/` 记录（如涉及架构/技术决策）
- [ ] 是否更新 `PROJECT_INDEX.md`（新增文件必须索引）
- [ ] 是否更新 `skills/skill-iteration-log.md`（如 Skill 有变化）
- [ ] 每条 Vault 记录是否包含：背景、决策、理由、下一步
- [ ] 检查是否有重复或过时记录需要归档

## Cadence

| 触发条件 | 动作 |
|----------|------|
| 每次 Kimi 任务完成后 | 立即执行 GitHub + Obsidian 同步检查 |
| 每次 MVP acceptance 通过后 | 同步验收脚本、结果、Vault 记录 |
| 每天结束前 | 至少做一次 `git status` 状态检查 |
| 大范围研究成果 | 先写 Vault，再由 Codex 判断是否进入 GitHub 正式 docs |
| 每周五 | 整理本周 agent-runs，归档重复记录 |

## Handoff Template

当 Kimi 无 GitHub push 权限时，产出以下交接文档供 Codex 执行：

```markdown
## Kimi Handoff: <任务名>

### 本轮目标
<一句话描述>

### 修改文件列表
- 新增: `<path>`
- 修改: `<path>`
- 删除: `<path>`

### 验收命令与结果
```bash
<command>
```
结果: <pass/fail + 关键指标>

### Vault 记录路径
- `data/research/conversations/agent-runs/YYYY-MM-DD-*.md`
- `data/research/conversations/decisions/XXXX-*.md` (如适用)

### GitHub 建议 commit message
```
[<agent>] <type>: <summary>
```

### 不应提交的文件
- `outputs/...`
- `*.tmp.duckdb`
- `__pycache__/`
- `<sensitive file>`

### 需要 Codex 复核的风险
- <风险 1: 如是否影响现有测试>
- <风险 2: 如是否有未验证的依赖>
```

## First Sync Audit

基于当前工作区（2026-06-11）的同步审计结果：

### 已修改但未提交（`git diff`）

| 文件 | 变更 | 建议 |
|------|------|------|
| `README.md` | +9 行，更新 MVP 状态 | **提交** |
| `data/research/conversations/PROJECT_INDEX.md` | +5 行，新增索引 | **提交** |
| `docs/TASK_ALLOCATION.md` | +81 行，新增 Q4/K9/K10/C14 | **提交** |
| `hermass_platform/strategy_lab/api_models.py` | +3 行，新增 backtest 字段 | **提交** |
| `hermass_platform/strategy_lab/dsl_schema.py` | +10/-5 行，放宽约束注释 | **提交** |
| `hermass_platform/strategy_lab/tests/test_dsl_schema.py` | +30/-6 行，测试更新 | **提交** |
| `hermass_platform/strategy_lab/tests/test_dsl_validator.py` | +15/-3 行，测试更新 | **提交** |
| `skills/hermass-quant-execution/SKILL.md` | +11 行，Skill 更新 | **提交** |

### 未追踪文件（`git ls-files --others`）

| 文件 | 建议 |
|------|------|
| `agents/KIMI_NEXT_TASK_GITHUB_OBSIDIAN_SYNC_DISCIPLINE.md` | **提交** — Kimi 任务提示词 |
| `agents/KIMI_NEXT_TASK_PRODUCT_SCOPE_SERVICE_BOUNDARY.md` | **提交** — Kimi 任务提示词 |
| `agents/QODER_NEXT_TASK_2026_06_08_E2E_SAMPLES.md` | **提交** — Qoder 任务提示词 |
| `data/research/conversations/agent-runs/2026-06-08-codex-mvp-e2e-runner-acceptance.md` | **提交** — 运行摘要 |
| `data/research/conversations/agent-runs/2026-06-08-qoder-mvp-e2e-sample-contracts.md` | **提交** — 运行摘要 |
| `data/research/conversations/agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md` | **提交** — 运行摘要 |
| `data/research/conversations/agent-runs/2026-06-11-codex-assign-kimi-github-obsidian-sync.md` | **提交** — 运行摘要 |
| `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md` | **提交** — 正式文档 |
| `hermass_platform/strategy_lab/e2e_runner.py` | **提交** — 核心源码 |
| `hermass_platform/strategy_lab/tests/test_e2e_runner.py` | **提交** — 测试 |
| `scripts/run_strategy_lab_mvp_e2e_acceptance.py` | **提交** — 验收脚本 |
| `6月8日工作计划.MD` | **忽略** — 个人本地文件 |

### 需要先补 Vault 记录的事项

1. **2026-06-08 Codex MVP E2E Runner 验收** — 已有 `agent-runs/2026-06-08-codex-mvp-e2e-runner-acceptance.md`，需确认是否包含完整验收结果。
2. **2026-06-09 E2E Acceptance Script** — 已有 `agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md`，需确认 5/5 passed 记录。
3. ** dsl_schema.py 约束放宽** — 从 `le=0.10/le=0.25` 改为 `le=1.0`，由 validator 执行红线检查。此变更应有决策记录或至少 agent-run 说明理由。

### 阻塞同步的问题

- **无阻塞问题**。所有未提交文件均可按上述建议分类处理。
- 注意：`outputs/` 目录已被 `.gitignore` 覆盖，不会误提交。

## Risks

| 风险 | 影响 | 缓解 |
|------|------|------|
| Kimi 无 GitHub push 权限，handoff 延迟 | 同步滞后 | Handoff Template 标准化，Codex 每日检查 |
| Vault 记录质量下降 | 后续 Agent 重复阅读 | 每条记录强制四要素（背景/决策/理由/下一步） |
| 敏感信息误提交 | 安全事件 | diff 检查 + `.gitignore` 已覆盖 outputs/ |
| 重复提交相同内容 | 仓库膨胀 | 提交前 `git diff --stat` 确认范围 |

## Next Steps For Codex

1. 按 First Sync Audit 建议，批量提交已修改和未追踪文件。
2. 建议 commit message：
   ```
   [codex] sync: batch commit pending changes from K9/K10 and C14

   - Add K9 product scope service boundary prompt
   - Add K10 GitHub/Obsidian sync discipline prompt
   - Add Q4 E2E sample contracts and C14 acceptance script
   - Update TASK_ALLOCATION.md with Q4/K9/K10/C14
   - Update PROJECT_INDEX.md with new entries
   - Add e2e_runner.py and acceptance script
   - Update dsl_schema constraint relaxation with validator red-line

   验收: /Users/lv111101/.pyenv/versions/3.11.12/bin/python -m pytest hermass_platform/strategy_lab/tests -q -> 197 passed
   ```
3. 检查 `dsl_schema.py` 约束放宽是否有对应决策记录；如无，补 `decisions/` 或 agent-run 说明。
4. 确认 `6月8日工作计划.MD` 是否需要加入 `.gitignore` 或移至个人目录。
