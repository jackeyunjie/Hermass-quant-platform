# GitHub Stars Growth And Open Source Maturity Plan

## Star Readiness Verdict

**NOT_READY_TO_PROMOTE**

当前仓库不具备自然 star 增长条件。核心原因：README 无法 30 秒讲清价值、无 License、无 Topics、Description 有拼写错误、本地大量成果未同步到 GitHub、无 Demo/截图、无 Quickstart。在这些问题修复前，任何外部宣传都是浪费注意力。

---

## Current Repository Audit

### GitHub 远程状态（2026-06-11）

| 项目 | 当前状态 | 问题 |
|------|----------|------|
| Stars | 0 | — |
| Forks | 0 | — |
| Watchers | 0 | — |
| Visibility | public | 已公开，但内容未准备好 |
| License | **none** | 严重缺失，开发者不敢用 |
| Topics | **none** | 无法被搜索发现 |
| Description | `AI NANTIVE Hermass quant platform` | **拼写错误**（NANTIVE -> NATIVE） |
| Latest push | 2026-06-07 | 本地 4 天成果未推送 |

### README 审计

| 检查项 | 当前状态 | 问题 |
|--------|----------|------|
| 30 秒讲清项目 | **否** | 只有一句 "Agent-native quantitative strategy platform MVP"，无价值主张 |
| What it is / What it is not | **无** | 未定义边界，易被误解为交易工具 |
| Quickstart（3 分钟可运行） | **否** | 命令含绝对路径 `/Users/lv111101/.pyenv/...`，他人无法直接复制 |
| Demo GIF/截图 | **无** | 无法直观展示 |
| Example input/output | **无** | 没有中文策略 -> DSL -> 报告的例子 |
| Badges | **无** | 无 Python 版本、测试状态、License 等徽章 |
| Roadmap | **无** | 开发者不知道项目方向 |
| Safety / disclaimer | **无** | 金融项目必须有的合规声明缺失 |
| Contribution guide | **无** | 无法吸引外部贡献 |
| Architecture diagram | **无** | 无法快速理解系统结构 |

### 本地未同步成果审计

基于 `git status`，以下重要文件/修改**未提交到 GitHub**：

| 文件/目录 | 类型 | 重要性 |
|-----------|------|--------|
| `README.md`（修改） | 文档 | 高 — 更新 MVP 状态 |
| `docs/TASK_ALLOCATION.md`（修改） | 文档 | 中 — 任务追踪 |
| `hermass_platform/strategy_lab/e2e_runner.py`（新增） | 源码 | **高** — 核心 E2E 链路 |
| `hermass_platform/strategy_lab/tests/test_e2e_runner.py`（新增） | 测试 | **高** |
| `scripts/run_strategy_lab_mvp_e2e_acceptance.py`（新增） | 脚本 | **高** — 验收入口 |
| `docs/strategy_lab/MVP_E2E_SAMPLES_2026_06_08.md`（新增） | 文档 | **高** — 样例合约 |
| `agents/` 多个任务提示词（新增） | 文档 | 中 — 项目协作资产 |
| `data/research/conversations/` 多个 agent-runs | 记录 | 中 — 决策可追溯 |
| `hermass_platform/strategy_lab/api_models.py`（修改） | 源码 | 高 — 新增 backtest 字段 |
| `hermass_platform/strategy_lab/dsl_schema.py`（修改） | 源码 | 高 — 约束放宽 |

### 为什么当前 0 stars

1. **无 License**：开发者看到无 License 的仓库，第一反应是"不敢用"。
2. **README 不完整**：36 行 README 无法让陌生人在 30 秒内理解项目价值。
3. **无 Demo/截图**：量化策略平台是视觉密集型产品，没有运行截图等于没有证据。
4. **Quickstart 不可用**：绝对路径命令只对当前机器有效。
5. **Description 拼写错误**：`NANTIVE` 直接降低专业可信度。
6. **本地成果未同步**：E2E runner、验收脚本、样例合约等核心资产都在本地。
7. **无 Topics**：GitHub 搜索和推荐算法无法发现该仓库。
8. **无安全声明**：金融相关项目没有 disclaimer，专业用户会质疑合规意识。

---

## Star Growth Positioning

### 一句话定位

> **Hermass** — 将中文量化策略想法转化为可验证、可审计的结构化研究框架。

### 面向开发者的价值主张

- DSL-first：策略是唯一表达，禁止 LLM 生成代码执行。
- Red-line first：仓位、止损等约束硬编码，不合格策略无法进入回测。
- Audit-first：每次生成、校验、预览、回测都有 trace_id 和审计记录。
- 确定性链路：中文输入 -> 结构化 DSL -> 校验 -> 预览 -> 回测 -> 审计，全程可追踪。

### 面向量化研究者的价值主张

- 用中文描述策略想法，系统自动结构化为可执行的 DSL。
- 红线检查防止常见风险（无止损、仓位过大）。
- 条件预览快速估算策略在历史数据中的命中情况。
- 完整审计链支持策略版本管理和回测追溯。

### 与普通 backtest 框架的差异

| 维度 | 普通 Backtest 框架 | Hermass |
|------|-------------------|---------|
| 输入 | Python 代码 | 中文自然语言 |
| 策略表达 | 代码 | DSL v2（结构化 JSON） |
| 安全约束 | 无 | 红线检查硬编码 |
| 审计 | 无 | 全链路 trace_id + audit log |
| 代码执行 | 用户 Python | **禁止** — 仅结构化 |
| AI 参与 | 无或生成代码 | 仅结构化，不执行 |

### 与自动荐股/交易系统的边界

- **不是**自动荐股系统：不输出买卖建议。
- **不是**自动交易系统：不执行真实下单。
- **不是**收益承诺工具：回测为研究演示，不代表真实绩效。
- **是**策略研究实验平台：帮助用户将想法结构化、验证、审计。

---

## GitHub Improvement Backlog

### P0: Before Any Promotion（必须先完成）

| # | 任务 | 负责人 | 验收标准 |
|---|------|--------|----------|
| P0-1 | 批量提交本地未同步成果 | Codex | `git status --short` 无重要未提交文件 |
| P0-2 | 修正 GitHub Description 拼写 | 用户 | `AI NANTIVE` -> `AI-Native` |
| P0-3 | 添加 License | Codex | 仓库根目录有 `LICENSE` 文件 |
| P0-4 | 添加 Topics | 用户 | 至少 5 个相关 topic |
| P0-5 | 重写 README | Codex | 见下方 README Rewrite Outline |
| P0-6 | 增加 Quickstart | Codex | 新用户 3 分钟内可运行验收命令 |
| P0-7 | 增加 Example input/output | Codex | README 中包含中文策略 -> DSL -> 报告示例 |
| P0-8 | 增加 Service boundary / disclaimer | Codex | README 中明确"不是投资建议" |
| P0-9 | 增加 Roadmap | Codex | 至少列出 Phase 0/1/2/3 目标 |
| P0-10 | 添加 `.gitignore` 检查 | Codex | 确认 `outputs/`、缓存、敏感文件不被提交 |

### P1: Soft Launch（P0 完成后）

| # | 任务 | 负责人 | 验收标准 |
|---|------|--------|----------|
| P1-1 | Demo 截图或 ASCII 输出 | Codex | README 中有运行结果截图或文本示例 |
| P1-2 | GitHub Release v0.1.0 | Codex | 有 tag 和 release notes |
| P1-3 | Issues templates | Codex | `.github/ISSUE_TEMPLATE/` 有 bug/feature 模板 |
| P1-4 | CONTRIBUTING.md | Codex | 有贡献指南 |
| P1-5 | 示例策略目录 | Codex | `examples/` 有 3 个冻结样例的 DSL JSON |
| P1-6 | 一键验收命令 | Codex | `python -m pytest` 或 `python scripts/...` 可直接运行 |
| P1-7 | Badges | Codex | README 有 Python 版本、License、tests 等 badge |
| P1-8 | GitHub Actions（可选） | Codex | CI 跑通 pytest |

### P2: Public Growth（P1 完成后）

| # | 任务 | 负责人 | 验收标准 |
|---|------|--------|----------|
| P2-1 | 技术博文 | Kimi | 发布 1 篇中文/英文技术介绍 |
| P2-2 | 3 分钟 demo 视频/GIF | Codex | 展示中文策略输入到报告输出 |
| P2-3 | DuckDB/Polars/AI Agent 社区关联 | Kimi | 在相关社区分享 |
| P2-4 | 对比其他 quant 工具的定位文章 | Kimi | 明确差异点 |
| P2-5 | 真实 Light Backtest 后再扩大传播 | Codex | stub 替换为真实回测后更新 README |
| P2-6 | 邀请制试点反馈入 README | Kimi | 用户证言或反馈摘要 |

---

## README Rewrite Outline

```markdown
# Hermass AI Quant Platform

## Tagline
将中文量化策略想法转化为可验证、可审计的结构化研究框架。

## What It Is
- 中文策略输入 -> DSL v2 -> 校验 -> 红线检查 -> 条件预览 -> Light Backtest -> 审计落库
- DSL-first：策略是唯一表达，禁止 LLM 生成代码执行
- Red-line first：止损、仓位等约束硬编码
- Audit-first：每次操作都有 trace_id 和审计记录

## What It Is Not
- 不提供投资建议
- 不执行真实交易
- 不保证收益
- 当前回测为演示框架（light_stub），非真实绩效

## Quickstart

### 安装
```bash
git clone https://github.com/jackeyunjie/Hermass-quant-platform.git
cd Hermass-quant-platform
pip install -e ".[dev]"
```

### 运行验收
```bash
python scripts/run_strategy_lab_mvp_e2e_acceptance.py
```

### 运行测试
```bash
python -m pytest hermass_platform/strategy_lab/tests -q
```

## Example

### 输入
```
MA5上穿MA20买入，跌破MA10卖出，止损8%
```

### 输出 DSL
```json
{
  "strategy_id": "sample_ma_5_20_stop_8",
  "name": "MA5上穿MA20策略",
  "entry": [{"condition_type": "ma_golden_cross", "params": {"fast_period": 5, "slow_period": 20}}],
  "exit": [{"condition_type": "price_cross_ma", "params": {"ma_period": 10, "direction": "below"}},
           {"condition_type": "stop_loss_pct", "params": {"value": 0.08}}],
  "risk": {"max_position_pct": 0.20, "stop_loss_required": true}
}
```

### 红线检查
- 有止损 -> 通过
- 仓位 20% <= 25% -> 通过

### 预览输出
- ma_golden_cross: estimated_hits=42
- price_cross_ma: estimated_hits=55
- stop_loss_pct: requires_backtest_context

### 回测输出（演示框架）
```json
{
  "mode": "light_stub",
  "metrics": {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 0.0, "trade_count": 0},
  "risk_flags": ["STUB_BACKTEST: Not yet implemented"]
}
```

## Architecture

```
中文输入 -> NL Parser -> DSL v2 -> Validator -> Red Lines -> Preview -> Backtest -> Audit
```

## Current Limitations
- 仅支持冻结的 3 个中文策略样例映射
- Light Backtest 为 stub，非真实历史数据回测
- 无 Web UI，仅命令行/脚本
- 条件注册表仅覆盖 P0 类型

## Roadmap

| Phase | 目标 | 状态 |
|-------|------|------|
| Phase 0 | DSL 基础、校验、红线、审计 | 已完成 |
| Phase 1 | 条件预览、存储、E2E runner | 已完成 |
| Phase 2 | 真实 Light Backtest（DuckDB + Polars） | 进行中 |
| Phase 3 | Web UI、产业链 Agent、高配因子库 | 计划中 |

## Safety & Disclaimer

> 本工具仅供量化策略研究实验使用，不构成投资建议。
> 平台不执行真实交易、不保证收益、不提供买卖建议。
> 当前回测为演示框架，指标值为占位符，不代表真实历史绩效。
> 投资有风险，决策需谨慎。

## License

[MIT / Apache-2.0 / BSL-1.1 — 待定]

## Contributing

见 [CONTRIBUTING.md](CONTRIBUTING.md)

## Acknowledgments

- DuckDB / Polars 社区
- Pydantic / FastAPI 生态
```

---

## Suggested GitHub Metadata

### Repository Description

```
Hermass: AI-Native Quantitative Strategy Research Platform —
Turn Chinese strategy ideas into verifiable, auditable structured research loops.
```

### Topics

```
quantitative-trading, strategy-research, dsl, backtesting, duckdb, polars, pydantic,
ai-agent, audit-trail, chinese-nlp, algorithmic-trading, fintech
```

建议至少选择 5-8 个：
- `quantitative-trading`
- `strategy-research`
- `dsl`
- `backtesting`
- `duckdb`
- `polars`
- `pydantic`
- `audit-trail`

### License 选项

| 选项 | 优点 | 缺点 | 建议 |
|------|------|------|------|
| **MIT** | 最开放，开发者友好 | 无专利保护，可被商业闭源 | 如果希望最大化社区采用 |
| **Apache-2.0** | 有专利授权保护，企业友好 | 稍复杂 | **推荐** — 平衡开放与保护 |
| **BSL-1.1 (Business Source License)** | 初期保护，未来转开放 | 非传统开源，社区接受度低 | 如果有明确的商业化计划 |
| **GPL-3.0** | 强制衍生作品开源 | 企业采用意愿低 | 不推荐 |

**Kimi 建议**：先采用 **Apache-2.0**，理由：
- 有专利保护，防止恶意专利诉讼。
- 企业用户更放心采用。
- 与 DuckDB、Polars、Pydantic 等依赖的许可证兼容。
- 未来如需调整，可在 major version 时变更。

**注意**：License 选择涉及法律和商业决策，最终需用户/律师确认。

### Suggested Release

- **v0.1.0-alpha** — 当前 MVP 阶段
- **v0.1.0** — P0 完成后、soft launch 时
- Release notes 模板：
  ```markdown
  ## What's New
  - E2E runner: Chinese NL -> DSL -> Validation -> Preview -> Backtest -> Audit
  - 3 frozen strategy samples with acceptance script
  - Red-line checks: stop-loss required, max position <= 25%
  - DuckDB-based audit and storage

  ## Known Limitations
  - Light Backtest is stub only
  - Only 3 Chinese strategy patterns supported
  - No Web UI

  ## Verification
  ```bash
  python scripts/run_strategy_lab_mvp_e2e_acceptance.py
  ```
  ```

---

## Star Targets

### 0 -> 5 stars（P0 完成后 2 周内）

**条件**：
- README 重写完成
- License 添加
- Topics 设置
- Description 修正
- 本地成果全部推送

**动作**：
- 作者个人社交网络分享（朋友圈、Twitter/X、LinkedIn）
- 发给 5-10 个熟人/同事请求 star 和反馈
- 在 DuckDB/Polars 中文社区低调分享

**预期**：5 stars 来自熟人网络，验证 README 是否足够清晰。

### 5 -> 20 stars（P1 完成后 1 个月内）

**条件**：
- Demo 截图/GIF 就位
- Release v0.1.0 发布
- CONTRIBUTING.md 就位
- Issues template 就位

**动作**：
- 在 V2EX、知乎、稀土掘金发技术介绍帖
- 在 GitHub 相关 awesome-list 提交 PR
- 参与 DuckDB/Polars/Quant 社区讨论时自然提及

**预期**：20 stars 来自技术社区的自然发现。

### 20 -> 100 stars（P2 前期，真实回测前）

**条件**：
- 1 篇技术博文（中文+英文）
- 3 分钟 demo 视频或 GIF
- 与现有 quant 工具的对比文章

**动作**：
- Hacker News Show、Product Hunt（需谨慎，可能引来非目标用户）
- Reddit r/algotrading、r/quant 分享
- 中文技术媒体投稿

**预期**：100 stars 需要内容资产支撑，不能仅靠仓库本身。

### 100+ stars（真实 Light Backtest 后）

**条件**：
- 真实历史数据回测可用
- 至少 10 个试点用户反馈
- 有用户实际使用案例

**动作**：
- 更新 README 展示真实回测案例
- 发布 v0.2.0 或 v1.0.0-beta
- 扩大技术博文和 demo 视频传播

**预期**：100+ 需要产品价值被验证，不能仅靠营销。

---

## Launch Plan

### Soft Launch Checklist

- [ ] P0 全部完成（README、License、Topics、Description、同步）
- [ ] README 通过"陌生人测试"：给 1 个不熟悉项目的人看，能否 30 秒理解
- [ ] Quickstart 通过"新机器测试"：在新环境克隆，3 分钟内跑通验收
- [ ] 无敏感信息泄露（token、路径、个人数据）
- [ ] Disclaimer 醒目且不可跳过
- [ ] 禁止话术检查通过

### 目标受众

| 优先级 | 受众 | 渠道 |
|--------|------|------|
| P0 | 个人熟人/同事 | 私聊、小群 |
| P1 | 量化研究爱好者 | V2EX、知乎、稀土掘金 |
| P2 | Python/数据工程师 | GitHub 探索、DuckDB/Polars 社区 |
| P3 | 更广泛的 AI/Agent 开发者 | Hacker News、Reddit |

### 发布渠道

1. **GitHub Explore**：Topics 设置正确后可被推荐
2. **个人社交网络**：Twitter/X、LinkedIn、朋友圈
3. **中文技术社区**：V2EX、知乎、稀土掘金、SegmentFault
4. **英文技术社区**：Hacker News（Show HN）、Reddit、Dev.to
5. **垂直社区**：QuantStack、DuckDB Discord、Polars Discord

### 反馈收集

- GitHub Issues：bug 报告、功能请求
- 个人私聊：早期熟人的直接反馈
- 社区帖子评论：公开讨论中的问题

### 成功标准

| 阶段 | 标准 |
|------|------|
| Soft Launch | 5 stars + 0 个"这是什么"的困惑反馈 |
| P1 Launch | 20 stars + 至少 1 个外部 issue/PR |
| P2 Launch | 100 stars + 至少 1 篇外部引用/推荐 |

### 停止标准

| 条件 | 动作 |
|------|------|
| 收到"这是荐股软件吗"的反馈 | 立即检查 README 边界声明是否足够清晰 |
| 发现 License 冲突 | 暂停传播，解决后再继续 |
| 收到安全漏洞报告 | 立即修复，通知已 star 用户 |
| 连续 2 周无增长 | 复盘内容资产是否足够 |

---

## Compliance-Safe Copy

### GitHub README Tagline

```
Hermass — Turn Chinese quantitative strategy ideas into verifiable, auditable structured research loops.

Not investment advice. No real trading. Research only.
```

### X/LinkedIn 短帖（英文）

```
Open-sourcing Hermass: an AI-native quantitative strategy research platform.

Turn Chinese strategy descriptions into structured DSL, validate with red-line checks, preview conditions, and audit everything.

Not a trading bot. Not investment advice. Just structured research.

GitHub: github.com/jackeyunjie/Hermass-quant-platform

#quant #opensource #duckdb #polars #pydantic
```

### 中文朋友圈/社群短帖

```
开源了一个量化策略研究实验平台 Hermass。

能把中文策略想法（比如"MA5上穿MA20买入，止损8%"）自动结构化为可验证的 DSL，
带红线检查、条件预览、审计追踪。

不是自动交易系统，不是荐股软件，仅供研究实验。

欢迎 star 和提 issue：github.com/jackeyunjie/Hermass-quant-platform
```

### 禁止使用的话术

| 禁止话术 | 替代方案 |
|----------|----------|
| "AI 选股" / "智能选股" | "AI 策略结构化" |
| "稳赚" / "高收益" | "策略研究框架" |
| "回测收益率 X%" | "回测演示框架（占位符）" |
| "自动交易" / "一键下单" | "策略研究，不执行交易" |
| "跟着买就能赚钱" | "仅供研究参考" |
| "专业投资顾问" | "策略研究工具" |
| "跑赢大盘" | "历史条件命中估算" |

---

## Risks

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 过早宣传导致负面印象 | 高 | 高 | 严格按 P0 -> P1 -> P2 顺序 |
| 被误解为荐股/交易工具 | 高 | 高 | README 多处 disclaimer + 禁止话术清单 |
| License 选择不当 | 中 | 高 | Apache-2.0 建议，但需用户确认 |
| 刷星/买星诱惑 | 低 | 高 | 明确禁止，专注内容质量 |
| 本地成果未同步就宣传 | 中 | 中 | K10 同步纪律执行 |
| 真实回测延迟导致期望落差 | 中 | 中 | README 明确标注当前为 stub |

---

## Next Steps For Codex

按优先级排序的可执行任务：

### 立即执行（本周）

1. **批量提交本地成果**
   - 文件：所有 `git status` 中的修改和新增文件
   - 排除：`outputs/`、`6月8日工作计划.MD`、缓存
   - Commit message：参考 K10 handoff 模板

2. **添加 License**
   - 文件：`LICENSE`（Apache-2.0 建议）
   - 验收：GitHub 页面显示 License 信息

3. **重写 README**
   - 文件：`README.md`
   - 按上方 README Rewrite Outline 执行
   - 验收：陌生人 30 秒能理解项目价值

### 短期执行（下周）

4. **修正 GitHub Description**
   - 用户手动修改：`AI NANTIVE Hermass quant platform` -> `AI-Native Quantitative Strategy Research Platform`

5. **添加 Topics**
   - 用户手动添加：quantitative-trading, strategy-research, dsl, backtesting, duckdb, polars, pydantic, audit-trail

6. **添加 `examples/` 目录**
   - 文件：`examples/sample_ma_5_20_stop_8.json` 等 3 个样例 DSL
   - 验收：新用户可直接查看样例

### 中期执行（2 周内）

7. **Demo 截图/ASCII 输出**
   - 文件：README 中嵌入运行结果
   - 验收：直观展示输入 -> 输出

8. **GitHub Release v0.1.0**
   - 创建 tag + release notes
   - 验收：Releases 页面有内容

9. **Issues Templates + CONTRIBUTING.md**
   - 文件：`.github/ISSUE_TEMPLATE/bug.md`、`.github/ISSUE_TEMPLATE/feature.md`、`CONTRIBUTING.md`

### 长期（真实回测后）

10. **更新 README 展示真实回测**
    - 替换 stub 示例为真实回测案例
    - 发布 v0.2.0

11. **技术博文和 Demo 视频**
    - Kimi 负责内容，Codex 配合技术细节

---

## Handoff For GitHub Sync

Kimi 无 GitHub push 权限，以下 handoff 供 Codex 执行：

### 本轮目标
审计当前仓库 0 stars 原因，输出 GitHub 成熟化计划和开源增长策略。

### 修改文件列表
- 新增：`data/research/conversations/agent-runs/2026-06-11-kimi-github-stars-growth-plan.md`
- 新增：`agents/KIMI_NEXT_TASK_GITHUB_STARS_GROWTH_PLAN.md`（已存在，任务提示词）
- 需修改：`README.md`（按 README Rewrite Outline 重写）
- 需新增：`LICENSE`（建议 Apache-2.0）
- 需新增：`examples/`（3 个样例 DSL JSON）
- 需新增：`.github/ISSUE_TEMPLATE/`（bug/feature 模板）
- 需新增：`CONTRIBUTING.md`
- 用户手动修改：GitHub Description、Topics

### Vault 记录路径
- `data/research/conversations/agent-runs/2026-06-11-kimi-github-stars-growth-plan.md`

### GitHub 建议 commit message（P0 批量提交）
```
[codex] sync: batch commit MVP achievements and GitHub maturity prep

- Add E2E runner, acceptance script, and sample contracts
- Add K9-K12 agent prompts and agent-run records
- Add 0010 external service readiness decision
- Update README with MVP status and verification commands
- Update TASK_ALLOCATION.md with Q4/K9/K10/K11/K12
- Update PROJECT_INDEX.md with new entries

验收: python -m pytest hermass_platform/strategy_lab/tests -q -> 197 passed
```

### 不应提交的文件
- `outputs/`
- `6月8日工作计划.MD`
- 临时 DuckDB
- 缓存
- 敏感凭据

### 需要 Codex 复核的风险
- License 选择需用户最终确认（当前建议 Apache-2.0）。
- README 重写后需通过"陌生人测试"验证清晰度。
- GitHub Description 修正需用户手动操作（无 API 权限）。
