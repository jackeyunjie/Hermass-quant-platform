# Kimi Next Task: GitHub And Obsidian Sync Discipline

你是 Hermass AI Quant Platform 的 Kimi Research Engineer。本轮任务是建立并执行“GitHub 与 Obsidian 及时同步”的协作纪律。用户明确要求：同步 GitHub 和 Obsidian 的责任都安排给 Kimi。

## 必读上下文

执行前先阅读：

- `AGENTS.md`
- `docs/TASK_ALLOCATION.md`
- `data/research/conversations/PROJECT_INDEX.md`
- `README.md`
- `skills/hermass-quant-execution/SKILL.md`
- `data/research/conversations/agent-runs/2026-06-09-codex-mvp-e2e-acceptance-script.md`
- `agents/KIMI_RESEARCH_ENGINEER_PROMPT.md`

如需使用 Obsidian 同步脚本，优先参考本地 Skill：

- `/Users/lv111101/.codex/skills/obsidian-knowledge-sync/SKILL.md`

## 背景

当前项目已经有较多 Agent 产物、任务文档、验收脚本和 Vault 记录。风险不是缺少资料，而是 GitHub 与 Obsidian 不及时同步，导致：

- GitHub 代码状态与本地任务状态不一致。
- Obsidian Vault 缺少最新决策与运行摘要。
- 后续 Agent 接手时重复阅读旧上下文。
- 已通过的 MVP 验收无法被追踪到对应提交或 Vault 记录。

本任务目标是让 Kimi 建立一个可执行的同步机制，并在每次研究/任务交付后主动产出同步证据。

## 本轮目标

输出一份同步纪律文档，并按文档执行一次同步检查。核心问题：

1. 哪些内容必须同步到 GitHub？
2. 哪些内容必须同步到 Obsidian Vault？
3. 每次 Kimi 交付后，如何证明同步完成？
4. 哪些内容禁止同步或需要脱敏？
5. 如果没有 GitHub push 权限，如何形成可由 Codex 直接接手的 handoff？

## Kimi 职责

Kimi 需要负责：

- 检查本地 `git status --short`。
- 汇总本轮新增/修改文件。
- 判断哪些文件应提交到 GitHub，哪些输出只应留在 `outputs/`。
- 更新或创建 Obsidian Vault 记录。
- 更新 `data/research/conversations/PROJECT_INDEX.md` 中必要索引。
- 给出建议 commit message。
- 如具备权限，执行 GitHub 同步；如无权限，产出 Codex 可直接执行的同步 handoff。

Kimi 不需要替代 Codex 做最终代码复核；但 Kimi 必须保证自己的研究产物和同步状态可追踪。

## 必须输出

### 1. Sync Policy

定义同步策略，至少包括：

- GitHub 应同步的内容。
- GitHub 不应同步的内容。
- Obsidian 应同步的内容。
- Obsidian 不应同步的内容。
- 需要脱敏或禁止提交的内容。

默认规则：

- 应进 GitHub：源码、测试、任务提示词、正式文档、可复用脚本、Vault 中的整理后决策/运行摘要。
- 不应进 GitHub：`outputs/` 运行产物、临时 DuckDB、缓存、未脱敏 token、未经整理的长对话原文。
- 应进 Obsidian：决策、Agent 运行摘要、阶段复盘、可复用流程、验收结果。
- 不应进 Obsidian：无上下文垃圾片段、重复日志、未压缩的大段终端输出、敏感凭据。

### 2. GitHub Sync Checklist

给出每次同步前必须检查的步骤：

- `git status --short`
- `git diff --stat`
- `git diff -- <关键文件>`
- 验收命令是否已运行。
- 是否包含敏感信息。
- 是否误包含 `outputs/`、缓存或临时 DB。
- 建议 commit message。
- 如有远程权限，给出 push/PR 步骤；如无权限，给出 handoff 格式。

### 3. Obsidian Sync Checklist

给出每次同步前必须检查的步骤：

- 是否新增 `data/research/conversations/agent-runs/YYYY-MM-DD-*.md`。
- 是否需要新增 `decisions/` 记录。
- 是否需要更新 `PROJECT_INDEX.md`。
- 是否需要更新 `skills/skill-iteration-log.md`。
- 每条 Vault 记录是否包含：背景、决策、理由、下一步。
- 是否需要运行 `obsidian_sync.py export` 或 `sync-docs`。

### 4. Cadence

定义同步节奏：

- 每次 Kimi 任务完成后立即同步一次。
- 每次 MVP acceptance 通过后同步一次。
- 每天结束前至少做一次状态检查。
- 大范围研究成果先写 Vault，再由 Codex 判断是否进入 GitHub 正式 docs。

### 5. Handoff Template

给出 Kimi 无法直接 push 时的交接模板，至少包含：

- 本轮目标。
- 修改文件列表。
- 验收命令与结果。
- Vault 记录路径。
- GitHub 建议 commit message。
- 不应提交的文件。
- 需要 Codex 复核的风险。

### 6. First Sync Audit

基于当前工作区做一次同步审计，输出：

- 当前未提交文件分类。
- 建议提交到 GitHub 的文件。
- 建议只保留本地或忽略的文件。
- 需要先补 Obsidian 记录的事项。
- 是否存在阻塞同步的问题。

不要凭空假设 GitHub 远程状态；如果无法访问远程，只输出本地可验证结论。

## 输出文件

请写入：

`data/research/conversations/agent-runs/2026-06-11-kimi-github-obsidian-sync-discipline.md`

## 输出格式

```markdown
# GitHub And Obsidian Sync Discipline

## Background

## Sync Policy

## GitHub Sync Checklist

## Obsidian Sync Checklist

## Cadence

## Handoff Template

## First Sync Audit

## Risks

## Next Steps For Codex
```

## 验收标准

- 能明确判断每类文件是否应同步 GitHub。
- 能明确判断每类内容是否应同步 Obsidian。
- 有可执行的同步检查清单，不是泛泛原则。
- 有 Kimi 无 GitHub push 权限时的 handoff 模板。
- 完成一次当前工作区的同步审计。
- 不要求为了同步而提交 `outputs/`、临时 DB、缓存或敏感信息。

## 不做什么

- 不执行破坏性 Git 命令。
- 不提交或展示任何 token、cookie、密钥。
- 不把 `outputs/` 大文件或临时 DuckDB 当作 GitHub 交付物。
- 不把未经整理的长对话直接塞入 Vault。
- 不用同步动作替代 MVP 验收。
