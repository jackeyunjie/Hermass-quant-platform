# M3 Controlled Pilot 启动检查清单

> 用途：在正式发送 5 个邀请链接前，逐项确认工程、合规、运营准备就绪。
> 适用时间：2026-06-23（M3 工程与研究交付完成后）
> 维护责任：Codex + 项目 Owner

---

## 一、工程环境检查

### 1.1 代码与测试

- [ ] 当前分支包含以下 commit：
  - `[codex] M3 pilot: onboarding system + feedback + docs`
  - `[codex] M3 invite token gate`
  - `[codex] M3 pilot invite email template + fix smoke test reload`
  - `[codex] Qoder review + Kimi task file for M3 pilot user personas`
  - `[codex] DSL E2E performance: batch persistence + signal_frame filter`
- [ ] `python -m pytest hermass_platform/strategy_lab/tests scripts/test_web_ui_smoke.py -q` → 全部通过
- [ ] `python scripts/run_strategy_lab_real_e2e_acceptance.py` → 3/3 样例 passed
- [ ] `python benchmarks/dsl_e2e_perf.py` → 3 样例 total < 20s
- [ ] `python scripts/test_web_ui_smoke.py::test_invite_token_gate_active_blocks_without_token -v` → 403 确认

### 1.2 运行环境变量

```bash
# 必须配置
export HERMASS_M3_INVITE_TOKENS="VFmDwizfH8kkj3Gz09lq_A,cfIPwHmW0G9rjm4rDQuHBA,AlLg1MjVVC0a6SuY-4EGOA,IjDV09cbRTk_NCw7VKZpXQ,Jlww1D1kOwJEfz4oDSkJgA"

# 可选但建议配置
export STRATEGY_LAB_STORAGE_DB="outputs/strategy_lab/web_storage.duckdb"
export STRATEGY_LAB_AUDIT_DB="outputs/strategy_lab/web_audit.duckdb"
export FOUNDATION_DB="data/p116_foundation.duckdb"
export STATE_CUBE_DB="data/state_cube.duckdb"
```

- [ ] `HERMASS_M3_INVITE_TOKENS` 已设置且包含 5 个 token
- [ ] 启动 Web 服务前已 source 环境变量
- [ ] 验证 `/onboarding/` 无 token 时返回 403
- [ ] 验证 `/onboarding/?invite=VFmDwizfH8kkj3Gz09lq_A` 可进入免责声明页
- [ ] 验证 `/onboarding/?invite=INVALID` 返回 403
- [ ] 验证 cookie 持久化：首次用 token 访问后，后续不带 token 也能访问

### 1.3 数据基线检查

- [ ] `data/p116_foundation.duckdb` 存在（5,536 品种，8.6M 行）
- [ ] `data/state_cube.duckdb` 存在
- [ ] `python benchmarks/validate_real_data.py` → `ok=true`，`errors=[]`
- [ ] 首页 data readiness badge 显示 `READY`
- [ ] 默认运行模式显示 `light_real_v1`

---

## 二、合规与文案检查

### 2.1 页面级免责声明

- [ ] `/` 首页底部显示免责声明
- [ ] `/onboarding/` 免责声明包含 7 项强制勾选
- [ ] `/strategy-lab/structuring` 页面显示免责声明
- [ ] `/strategy-lab/diagnosis` 页面显示免责声明
- [ ] `/strategy-lab/evidence` 页面显示免责声明
- [ ] 所有报告/结果页显示 `trace_id`、`mode`、`data_cutoff_date`

### 2.2 邀请话术检查

> 注：K16（Kimi 用户画像任务）因模型 404 暂时无法执行。以下检查项分为"Kimi 可用时"和"Kimi 不可用时替代方案"。

**Kimi 可用时**：
- [ ] 已阅读 `data/research/conversations/agent-runs/2026-06-22-kimi-m3-pilot-user-personas.md`
- [ ] 5 个画像已对应到 5 个真实用户（匿名化处理）
- [ ] 每人的话术已替换 `[称呼]`、`[Name]`、`[TOKEN]`

**Kimi 不可用时（当前方案）**：
- [ ] 使用 `docs/product/M3_PILOT_INVITE_EMAIL_TEMPLATE.md` 中的标准模板
- [ ] 手动确认 5 个用户的画像类型（H1/H2/H3 至少各 1 人）
- [ ] 在邮件中明确说明"研究工具，非投资建议"
- [ ] 发送前进行最后一轮敏感词检查（禁止：赚钱、盈利、收益、稳赚、必涨、推荐、买入、卖出、加仓、减仓、抄底、逃顶）

**通用检查**：
- [ ] 发送渠道已确定：
  - pilot-01：微信私信
  - pilot-02：邮件
  - pilot-03：邮件
  - pilot-04：微信私信
  - pilot-05：邮件/线下

---

## 三、邀请发送清单

### 3.0 紧急回滚预案

- [ ] 确认关闭 invite gate 的方法：`unset HERMASS_M3_INVITE_TOKENS` 或设为空字符串
- [ ] 确认关闭后所有 onboarding 路由开放（向后兼容开发模式）
- [ ] 确认 audit_db 和 storage_db 已备份或可被重建

### 3.1 发送前

- [ ] 确认 5 个 pilot 用户均已知悉：
  - Hermass 是研究工具，不是投资建议服务
  - 2 周试点周期
  - 第 7 天和第 14 天需要填写反馈问卷
  - 所有操作会写入审计日志
- [ ] 确认 5 个用户均理解"不能跳过红线检查"
- [ ] 确认服务器已启动并可访问

### 3.2 发送内容（每封邀请必须包含）

- [ ] 一句说明：Hermass 是策略研究工具
- [ ] 完整免责声明链接或摘要
- [ ] onboarding 链接：`http://<host>/onboarding/?invite=<TOKEN>`
- [ ] 2 周试点周期说明
- [ ] 反馈邀请（第 7/14 天）
- [ ] 联系人（处理技术问题或合规疑问）

### 3.3 发送记录

| 编号 | Token | 用户画像 | 渠道 | 发送时间 | 发送人 | 状态 |
|---|---|---|---|---|---|---|
| pilot-01 | `VFmDwizfH8kkj3Gz09lq_A` | H1 主观交易员转量化 | 微信私信 | | | 待发送 |
| pilot-02 | `cfIPwHmW0G9rjm4rDQuHBA` | H2 策略研究员 | 邮件 | | | 待发送 |
| pilot-03 | `AlLg1MjVVC0a6SuY-4EGOA` | H3 私募量化研究员 | 邮件 | | | 待发送 |
| pilot-04 | `IjDV09cbRTk_NCw7VKZpXQ` | H1→H2 数据分析师 | 微信私信 | | | 待发送 |
| pilot-05 | `Jlww1D1kOwJEfz4oDSkJgA` | H2/H3 技术开发者 | 邮件/线下 | | | 待发送 |

---

## 四、试点期间监控

### 4.1 每日检查（Codex 负责）

> 检查脚本建议（可放入 `scripts/m3_daily_audit.py`）：

```python
# 伪代码 - 每日 audit 检查项
1. SELECT COUNT(*) FROM onboarding_consent WHERE date(created_at) = today
2. SELECT COUNT(*) FROM onboarding_diagnosis WHERE date(created_at) = today
3. SELECT COUNT(*) FROM onboarding_feedback WHERE day IN (7, 14)
4. SELECT COUNT(*) FROM strategy_audit_log WHERE operation='generation' AND date(created_at) = today
5. 检查 403 访问日志（如有 access log）
```

- [ ] 检查 `audit_db` 中 `onboarding_consent` 表是否有新记录
- [ ] 检查 `onboarding_diagnosis` 表是否有新记录
- [ ] 检查是否有用户触发 `/onboarding/not-suitable`（期望投资建议）
- [ ] 检查是否有 403 邀请 token 异常访问
- [ ] 检查 `strategy_audit_log` 中 generation/validation/preview/backtest 是否正常记录

### 4.2 关键指标追踪

| 指标 | 目标 | 测量方式 |
|---|---|---|
| onboarding 完成率 | 100%（5/5） | `onboarding_consent` + `onboarding_diagnosis` 记录数 |
| 平均创建策略数 | >=3 | `strategy_audit_log` operation='generation' |
| 红线理解率 | >=80% | 第 7 天问卷 Q4 |
| NPS | >=30 | 第 7 天问卷 Q6 |
| 平均单次回测耗时 | <20s | `backtest_elapsed_seconds` + persist 时间 |
| 合规事件 | 0 | 人工监控 + 用户反馈 |

### 4.3 第 3 天轻触（人工）

- [ ] pilot-01：确认是否完成首次 DSL 生成
- [ ] pilot-02：确认是否完成 preview 与 backtest 全流程
- [ ] pilot-03：确认是否查看 evidence lab 和 audit
- [ ] pilot-04：重点确认是否有"平台应该直接告诉我买什么"的误解
- [ ] pilot-05：确认是否跑通 3 个冻结样例

### 4.4 第 7 天问卷触发

- [ ] 发送 `/onboarding/feedback?day=7` 链接给所有 5 人
- [ ] 收集：主要功能、策略数、阻塞、红线帮助度、可解释性、NPS

### 4.5 第 14 天问卷触发

- [ ] 发送 `/onboarding/feedback?day=14` 链接给所有 5 人
- [ ] 收集：使用次数、是否修改策略想法、最想要的功能、最希望改进的体验、付费意愿

---

## 五、停止标准

出现以下任一情况，立即暂停试点：

- [ ] 用户要求跳过红线或认为红线是"平台不够聪明"
- [ ] 用户将回测结果作为投资建议传播（截图/转发）
- [ ] 系统性能导致单次操作 >60s 等待
- [ ] 数据质量投诉（停牌/退市/复权问题）
- [ ] 2 人及以上在 NPS 中评分 <5

---

## 六、试点成功标准（2 周后评估）

- [ ] 5 人完成首次体验
- [ ] 平均创建策略数 >=3
- [ ] 红线理解率 >=80%
- [ ] NPS >=30
- [ ] 无合规事件
- [ ] 性能满意度 >=3/5

满足以上标准 → 进入 M4 Public Beta 准备；未满足 → 延长试点或调整方向。

---

## 七、GitHub Handoff

**文件路径**：`docs/product/M3_PILOT_LAUNCH_CHECKLIST.md`

**关键结论**：
1. M3 工程系统已就绪（onboarding + feedback + invite token + DSL E2E 性能优化）。
2. K16 用户画像因 Kimi 模型 404 暂未完成，但标准邮件模板可覆盖启动需求。
3. 启动前必须配置 `HERMASS_M3_INVITE_TOKENS` 并跑通工程检查。
4. 试点期间需要每日 audit 监控和人工轻触。
5. 已准备紧急回滚预案（关闭 invite gate 即可开放访问）。

**下一步**：
- [ ] 项目 Owner 确认 5 个真实 pilot 用户并授权发送邀请。
- [ ] 确认 Kimi 模型是否恢复（如恢复，优先执行 K16 用户画像）。
- [ ] Codex 在服务器上配置环境变量并启动服务。
- [ ] 发送邀请后，Codex 开始每日 audit 监控。
- [ ] 第 3 天执行轻触检查，第 7/14 天触发反馈问卷。
