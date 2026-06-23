# Kimi Next Task: M3 Pilot 5 人目标用户画像与合规邀请话术

> 任务编号：K16
> 指派：Kimi Research Engineer
> 依赖：M3 onboarding 系统已完成（C21），5 个 invite token 已生成
> 阻塞：无（本任务为研究/文案任务，不阻塞工程）

---

## 背景

M3 受控试点的工程系统已落地：

- Onboarding 路由：`/onboarding/`（免责声明）→ `/onboarding/diagnosis`（4 题诊断）→ `/onboarding/result`（H1/H2/H3 推荐）
- 反馈系统：第 7 天/第 14 天问卷，`/onboarding/feedback` 和 `/onboarding/feedback/summary`
- 邀请 token：5 个预生成 token，通过 `HERMASS_M3_INVITE_TOKENS` 环境变量控制准入
- 邮件模板：`docs/product/M3_PILOT_INVITE_EMAIL_TEMPLATE.md`

现在需要明确：这 5 个邀请发给谁？用什么话术？如何确保合规？

---

## 交付物

### 1. 5 人目标用户画像（`data/research/conversations/agent-runs/2026-06-22-kimi-m3-pilot-user-personas.md`）

每个画像必须包含：

| 字段 | 说明 |
|---|---|
| 编号 | pilot-01 ~ pilot-05 |
| 用户类型 | 例如：量化新手、主观交易员转量化、策略研究员、技术开发者、资深投资者 |
| 背景描述 | 2-3 句话，不暴露真实个人隐私 |
| 研究成熟度 | H1 / H2 / H3（预期进入层级） |
| 使用预期 | 他们最可能尝试什么功能？ |
| 风险等级 | 低/中/高（对"投资建议"误解的可能性） |
| 邀请渠道 | 微信/邮件/线下（建议） |
| 跟进策略 | 第 3 天、第 7 天、第 14 天分别做什么？ |

5 个画像应覆盖不同 H 层级，确保 H1/H2/H3 都有代表。

### 2. 合规邀请话术（同一文件或独立文件）

每个渠道（微信私信、邮件、线下）的话术必须：

- 明确标注"研究工具，不是投资建议"
- 不承诺任何收益
- 不暗示"测试版特权"或"抢先赚钱机会"
- 包含 onboarding 链接和 token
- 包含 2 周试点周期说明
- 包含反馈邀请（第 7/14 天问卷）

### 3. 合规检查清单

- [ ] 所有话术经过"投资建议"敏感词扫描
- [ ] 所有话术包含免责声明
- [ ] 不承诺收益、不暗示确定性、不提供具体买卖建议
- [ ] 明确告知数据边界（历史数据、A 股日线、2018-2026）
- [ ] 明确告知系统边界（无实时行情、无自动交易、无资金托管）

---

## 验收标准

1. 5 个画像覆盖 H1/H2/H3 至少各 1 人
2. 每个画像有明确的风险等级和跟进策略
3. 邀请话术通过合规检查清单
4. 输出文件按 K10 同步纪律写入 Obsidian 并提供 GitHub handoff

---

## 输入参考

- `docs/product/H1_H2_H3_USER_DIAGNOSIS.md`：诊断问题集和路由规则
- `docs/product/M3_PILOT_ONBOARDING.md`：试点流程和停止标准
- `data/research/conversations/decisions/0017-m3-controlled-pilot.md`：M3 决策记录（含 token 列表）
- `docs/product/M3_PILOT_INVITE_EMAIL_TEMPLATE.md`：现有邮件模板（可在此基础上修改）
- `docs/product/VISION_MILESTONES_AND_KEY_ASSUMPTIONS.md`：M3 章节

---

## 非目标

- 不设计公开推广方案（M3 是邀请制，不是 public launch）
- 不设计付费转化路径（M3 是研究试点，不涉及定价）
- 不收集真实个人隐私（画像用虚构/匿名化描述）

---

## 输出格式

```markdown
# M3 Pilot 5 人目标用户画像

## 画像 1：pilot-01（H1 代表）
...

## 画像 2：pilot-02（H2 代表）
...

## 画像 3：pilot-03（H3 代表）
...

## 画像 4：pilot-04（混合层级）
...

## 画像 5：pilot-05（边缘案例）
...

## 合规邀请话术

### 微信私信版
...

### 邮件版
...

### 线下口头版
...

## 合规检查清单
...
```
