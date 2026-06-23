# 0017 M3 Controlled Pilot 启动决策

## 背景

M2（Real Data Baseline）已于 2026-06-22 完成并复核：

- 真实数据：`data/p116_foundation.duckdb`（5,536 品种，8.6M 行）+ `data/state_cube.duckdb` 就绪
- 性能门禁：5000×252 P50=2.218s / P95=2.364s << 30s gate，`gate_summary.py` 8/8 PASS
- 3 个冻结样例 real E2E acceptance：3/3 passed，`light_real_v1` mode（`outputs/benchmarks/real_e2e_full_benchmark_20260622_192555.json`）
- Web UI：3 页面 + data readiness badge + JSON API 已落地
- 已知非阻塞开销：DSL 端到端 backtest 路径（含 preview/validation/audit/storage）约 27-32s，超出纯 engine 时间，作为 M3 Pilot 用户体验基线

按 Vision doc 规划，M3 目标为"允许 5-20 个受控用户使用 Hermass 做研究，不公开商业化"。

## 决策

### 1. M3 准入条件

| 条件 | 状态 | 说明 |
|---|---|---|
| 真实 baseline 就绪 | ✅ | M2 完成 |
| 免责声明可见 | ✅ | Web UI 所有页面显示 `not investment advice` |
| 运行标签不可隐藏 | ✅ | `synthetic`/`light_stub`/`light_real_v1` 显式展示 |
| 红线不可绕过 | ✅ | DSL validator 强制拦截，无 skip 入口 |
| audit 可追溯 | ✅ | 每步 trace_id 可查 |
| 用户身份可控 | ⚠️ | 当前无认证，靠邀请链接 + 白名单控制 |

### 2. 试点边界

- **人数**：5 人（首轮），不超过 20 人（累计）
- **用途**：策略研究、回测验证、假设检验
- **禁止**：作为投资建议、向他人推荐、真实交易、资金托管
- **周期**：2 周观察期，收集反馈后决定是否扩大
- **数据**：使用现有 `light_real_v1` 回测，不承诺实时数据

### 3. 用户分层诊断表（H1/H2/H3 进入标准）

见 `docs/product/H1_H2_H3_USER_DIAGNOSIS.md`（待创建）。

核心逻辑：

- H1（Strategy Structuring）：用户能描述策略想法 → 进入 DSL 生成页面
- H2（Strategy Diagnosis）：用户已有 DSL 或想验证假设 → 进入 Preview + 红线检查
- H3（Strategy Evidence）：用户接受"假设-证据-复盘"循环 → 进入真实回测 + Evidence Lab
- 跳过判断：只想收益率/买卖点 → 不适合，引导至免责声明

### 4. Onboarding 流程

1. **邀请发送**：手动发送含免责声明链接的私信/邮件
2. **免责声明签收**：用户必须勾选"我理解 Hermass 是研究工具..."（电子记录）
3. **分层诊断**：回答 3-5 个问题，自动推荐 H1/H2/H3 入口
4. **首次体验**：冻结样例引导（MA5/MA20 策略），展示完整链路
5. **反馈收集**：第 7 天和第 14 天各一次结构化问卷

### 5. 停止标准

出现以下任一情况，暂停试点：

- 用户要求跳过红线或认为红线是"平台不够聪明"
- 用户将回测结果作为投资建议传播
- 系统性能导致用户体验不可接受（>60s 等待）
- 数据质量投诉（停牌/退市/复权问题）

## 理由

1. **M2 工程基线已稳定**，真实数据 + 性能门禁 + 全链路验收通过，具备对外暴露条件。
2. **受控试点优于直接开放**：5 人小范围可快速发现问题，避免公开 beta 的合规风险。
3. **分层诊断匹配 S 级私董会逻辑**：不是所有人用同一入口，而是按研究成熟度匹配不同场域。
4. **免责声明 + 运行标签是合规底线**：必须在用户第一眼看到结果时明确"这不是投资建议"。

## 下一步

1. **Codex**：创建 H1/H2/H3 用户诊断表页面（Web UI 新增 `/onboarding` 路由）
2. **Codex**：实现免责声明电子签收（存储到 audit_db）
3. **Kimi**：设计 5 人目标用户画像和邀请话术（合规安全）
4. **Qoder**：设计分层诊断问题集（3-5 题，自动路由 H1/H2/H3）
5. **Codex**：实现反馈收集表单（第 7/14 天触发）

## 参考

- `docs/product/VISION_MILESTONES_AND_KEY_ASSUMPTIONS.md` M3 章节
- `data/research/conversations/decisions/0011-external-service-readiness.md`
- `data/research/conversations/decisions/0014-phase2-light-backtest-implemented.md`
