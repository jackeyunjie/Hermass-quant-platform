# M3 Pilot 邀请邮件模板

> 本文件存放可直接发送给 pilot 用户的邀请邮件 Markdown 模板。
> 发送前请：
> 1. 将 `{{HOST}}` 替换为实际服务器地址
> 2. 将 `{{TOKEN}}` 替换为对应 pilot 的 invite token
> 3. 在 0017 决策记录中更新"使用人"和"发送日期"

---

## 邮件模板（中文）

**主题**：邀请你参与 Hermass 策略研究平台 M3 受控试点

---

你好，

感谢你同意参与 Hermass M3 受控试点。

Hermass 是一个**策略研究工具**，不是投资建议服务。它的目标是帮助有策略想法的人，把想法结构化、用真实历史数据验证、并理解策略为什么有效或失效。

**你的专属邀请链接**：

```
http://{{HOST}}/onboarding/?invite={{TOKEN}}
```

**使用前请务必了解**：

1. Hermass 的所有输出仅供研究参考，不构成任何买卖建议
2. 回测结果不代表未来收益，历史表现不能预测未来
3. 所有策略必须经过 DSL 结构化、红线检查和回测验证
4. 当前数据覆盖 2018-2026 年 A 股日线，可能存在停牌、退市、复权等处理边界

**试点周期**：2 周（从你首次访问链接开始计算）

**反馈邀请**：第 7 天和第 14 天我们会邀请你填写简短问卷，帮助我们改进产品。

如果你有任何问题，随时回复这封邮件。

期待你的反馈。

Hermass 团队

---

## 邮件模板（英文 - 备用）

**Subject**: Invitation to Hermass M3 Controlled Pilot

---

Hi,

Thank you for agreeing to participate in the Hermass M3 controlled pilot.

Hermass is a **strategy research tool**, not an investment advisory service. Its goal is to help people with strategy ideas structure them, validate with real historical data, and understand why a strategy works or fails.

**Your exclusive invitation link**:

```
http://{{HOST}}/onboarding/?invite={{TOKEN}}
```

**Important notes before you start**:

1. All outputs from Hermass are for research purposes only, not investment advice
2. Backtest results do not guarantee future performance
3. All strategies must go through DSL structuring, red-line checks, and backtest validation
4. Current data covers A-share daily data 2018-2026; boundaries exist for suspended/delisted/adjusted prices

**Pilot duration**: 2 weeks (from your first visit)

**Feedback**: We'll invite you to a short questionnaire on day 7 and day 14.

Reply to this email if you have any questions.

Looking forward to your feedback.

The Hermass Team

---

## 发送检查清单

- [ ] 已替换 `{{HOST}}` 为实际地址
- [ ] 已替换 `{{TOKEN}}` 为正确 token（5 个 token 各不相同）
- [ ] 已确认收件人理解"研究工具，非投资建议"
- [ ] 已在 0017 决策记录中标记发送日期
- [ ] 已告知收件人链接有效期（建议 2 周）
