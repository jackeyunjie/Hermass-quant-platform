# Factor Source And Evidence Schema

## Source Schema

用于注册和管理因子/Block 的来源信息,确保每个因子都有明确的出处、可靠性和授权说明。

### 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_id` | string | ✅ | 唯一标识,如 `sqx_b143`, `qlib_alpha158`, `aqr_quality` |
| `source_type` | enum | ✅ | 来源类型,见下方枚举 |
| `name` | string | ✅ | 来源名称,如 `StrategyQuant X Build 143` |
| `url_or_local_ref` | string | ✅ | 文档链接、论文 URL、本地参考路径 |
| `reliability` | enum | ✅ | 可靠性等级: `high`, `medium`, `low`, `unverified` |
| `license_notes` | string | ✅ | 授权说明、使用限制、版权声明 |
| `applicable_markets` | array[string] | ✅ | 适用市场: `A_SHARE`, `US_EQUITY`, `GLOBAL`, `FUTURES`, `CRYPTO` |
| `imported_at` | datetime | ✅ | 导入时间戳 |
| `tags` | array[string] | ❌ | 标签,如 `technical`, `fundamental`, `sentiment` |
| `notes` | string | ❌ | 补充说明 |

### source_type 枚举

```python
SOURCE_TYPES = {
    "strategy_generator": "S1: Strategy Generators (SQX, AlgoWizard 等)",
    "open_quant_framework": "S2: Open Quant Frameworks (Qlib, Zipline, Backtrader 等)",
    "institutional_factor": "S3: Institutional Factor Research (AQR, Barra, MSCI 等)",
    "academic_literature": "S4: Academic/Empirical Factor Literature (Fama-French 等)",
    "fundamental_data": "S5: Fundamental Factors (估值、盈利、成长等)",
    "news_sentiment": "S6: News/Event/Sentiment (新闻情绪、公告情绪等)",
    "money_flow": "S7: Money Flow/Order Flow/Microstructure (资金流、订单流等)",
    "trader_methodology": "S8: Trader Methodology (Wyckoff, Minervini, CANSLIM 等)",
    "behavioral_factor": "S9: Behavioral/Psychology Factors (过度反应、追涨杀跌等)",
    "hermass_native": "S10: Hermass Native Sources (State Cube, Agent Memory, 产业链等)"
}
```

### 示例

```yaml
source_id: sqx_b143
source_type: strategy_generator
name: "StrategyQuant X Build 143"
url_or_local_ref: "https://strategyquant.com/doc/build-143-changelog"
reliability: high
license_notes: "商业软件,仅参考 block 设计思想,不复制源码"
applicable_markets:
  - A_SHARE
  - US_EQUITY
  - FUTURES
imported_at: "2026-06-06T00:00:00Z"
tags:
  - signal_blocks
  - entry_blocks
  - exit_blocks
  - robustness
notes: "核心参考 source,提供 block weighting 和 parameter space 设计范式"
```

---

## Evidence Schema

用于记录因子/Block 的证据等级、验证状态和失效模式,确保生产环境只使用经过充分验证的因子。

### 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `evidence_level` | enum | ✅ | 证据等级 E0-E6,见下方定义 |
| `evidence_type` | enum | ✅ | 证据类型: `literature`, `backtest`, `walk_forward`, `paper_trading`, `live_trading`, `theoretical` |
| `metric_refs` | array[object] | ✅ | 验证指标引用,见下方结构 |
| `validation_status` | enum | ✅ | 验证状态: `pending`, `in_progress`, `passed`, `failed`, `expired` |
| `last_validated_at` | datetime | ✅ | 最后验证时间 |
| `failure_modes` | array[string] | ✅ | 已知失效模式,如 `high_turnover`, `data_snooping`, `regime_dependent` |
| `validator_id` | string | ❌ | 验证者标识 (Agent ID 或研究员) |
| `validation_report_url` | string | ❌ | 验证报告链接 |

### evidence_level 枚举

| 等级 | 含义 | 生产准入 |
|------|------|----------|
| `E0` | Idea only,仅概念 | ❌ 禁止 |
| `E1` | Known literature / public framework | ❌ 禁止 |
| `E2` | Data available and computable | ❌ 禁止 |
| `E3` | IC/stratified return passed | ❌ 禁止 |
| `E4` | Backtest passed | ✅ 候选 |
| `E5` | Walk-forward / robustness passed | ✅ 生产 |
| `E6` | Paper trading validated | ✅ 生产 (高置信) |

**生产 DSL 只允许 E4+ 进入候选,E5+ 进入生产。**

### metric_refs 结构

```yaml
metric_refs:
  - metric: "RankIC_mean"           # 指标名称
    value: 0.045                    # 指标值
    threshold: 0.02                 # 通过阈值
    window: "2020-2025"             # 测试窗口
    universe: "A_SHARE_ALL"         # 测试股票池
    passed: true                    # 是否通过
  - metric: "ICIR"
    value: 0.85
    threshold: 0.5
    window: "2020-2025"
    universe: "A_SHARE_ALL"
    passed: true
  - metric: "layer_return_spread"   # 分层收益差 (Q5-Q1)
    value: 0.12                     # 年化 12%
    threshold: 0.05
    window: "2020-2025"
    universe: "A_SHARE_ALL"
    passed: true
  - metric: "turnover_annual"       # 年化换手率
    value: 8.5
    threshold: 20                   # 低于 20 倍为可接受
    window: "2020-2025"
    universe: "A_SHARE_ALL"
    passed: true
```

### failure_modes 常见值

```python
FAILURE_MODES = {
    "high_turnover": "高换手,交易成本侵蚀收益",
    "data_snooping": "数据挖掘偏差,过拟合风险",
    "regime_dependent": "依赖特定市场状态 (如牛市)",
    "liquidity_bias": "流动性偏差,小盘股主导",
    "survivorship_bias": "幸存者偏差",
    "lookahead_risk": "未来函数风险 (未处理财报滞后)",
    "short_sample": "样本期过短",
    "cost_sensitive": "对交易成本敏感",
    "crowding_risk": "拥挤度高,因子失效风险",
    "structural_break": "存在结构性断点"
}
```

### 示例

```yaml
evidence_level: E4
evidence_type: backtest
metric_refs:
  - metric: "RankIC_mean"
    value: 0.045
    threshold: 0.02
    window: "2020-2025"
    universe: "A_SHARE_ALL"
    passed: true
  - metric: "ICIR"
    value: 0.85
    threshold: 0.5
    window: "2020-2025"
    universe: "A_SHARE_ALL"
    passed: true
validation_status: passed
last_validated_at: "2026-06-05T12:00:00Z"
failure_modes:
  - regime_dependent
  - cost_sensitive
validator_id: "kimi_research_engineer"
validation_report_url: "data/research/conversations/validations/quality_roe_ttm_v01.md"
```

---

## FactorSpec Extensions

在现有 `FactorSpec` 基础上增加来源和证据相关字段,保持向后兼容。

### 新增字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_refs` | array[string] | ✅ | 引用的 source_id 列表,如 `["institutional_factor", "fundamental_data"]` |
| `evidence_level` | enum | ✅ | 证据等级 E0-E6,继承自 Evidence Schema |
| `data_availability` | enum | ✅ | 数据可用性: `pending`, `available`, `partial`, `unavailable`, `requires_license` |
| `future_leakage_risk` | enum | ✅ | 未来函数风险: `none`, `low`, `medium`, `high`, `mitigated` |
| `a_share_notes` | string | ✅ | A 股适配说明,如财报滞后处理、涨跌停限制等 |
| `production_gate` | enum | ✅ | 生产闸门: `blocked`, `candidate`, `approved`, `deprecated` |
| `evidence_summary` | object | ❌ | 证据摘要 (可选,用于快速查询) |

### 完整 FactorSpec 示例

```yaml
factor_id: "quality_roe_ttm"
name: "ROE TTM (质量因子)"
category: "fundamental_quality"
level: "L3"
frequency: "D1"
inputs:
  - "roe_ttm"
  - "report_date"
  - "announcement_date"
required_tables:
  - "financial_statements"
output_type: "numeric"
window: null
direction: "higher_better"
normalization:
  - "winsorize"
  - "zscore"
neutralization:
  - "industry_optional"
compute_engine: "polars"
preview_support: "fully_supported"
dsl_exposure: "candidate"
status: "research"
version: "0.1.0"

# === 新增来源和证据字段 ===
source_refs:
  - "institutional_factor"         # AQR/Barra 质量因子研究
  - "academic_literature"          # Fama-French quality minus junk
evidence_level: E1                 # 目前有文献支持,待回测验证
data_availability: available       # 黑狼数据源可用
future_leakage_risk: high          # 必须使用公告日期,禁止使用财报期截止日
a_share_notes: "必须使用 announcement_date 对齐,禁止使用 fiscal_period_end,否则会产生未来函数"
production_gate: blocked           # E1 等级,禁止进入生产
evidence_summary:                  # 可选,快速查询
  ic_mean: null
  icir: null
  last_test_window: null
```

### production_gate 逻辑

```python
def evaluate_production_gate(factor_spec: FactorSpec) -> str:
    """
    根据证据等级和验证状态自动计算 production_gate。
    
    规则:
    - E0-E3: blocked
    - E4 + validation_status=passed: candidate
    - E5-E6 + validation_status=passed: approved
    - validation_status=failed: blocked
    - future_leakage_risk=high: blocked (除非 mitigated)
    """
    if factor_spec.validation_status == "failed":
        return "blocked"
    
    if factor_spec.future_leakage_risk == "high":
        return "blocked"
    
    if factor_spec.evidence_level in ["E0", "E1", "E2", "E3"]:
        return "blocked"
    
    if factor_spec.evidence_level == "E4" and factor_spec.validation_status == "passed":
        return "candidate"
    
    if factor_spec.evidence_level in ["E5", "E6"] and factor_spec.validation_status == "passed":
        return "approved"
    
    return "blocked"
```

---

## BlockSpec Extensions

在现有 `BlockSpec` 基础上增加来源、证据和方法论引用字段。

### 新增字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_refs` | array[string] | ✅ | 引用的 source_id 列表 |
| `methodology_refs` | array[string] | ✅ | 引用的方法论 ID (如 `minervini_vcp`, `wyckoff_accumulation`) |
| `evidence_level` | enum | ✅ | 证据等级 E0-E6 |
| `generation_weight` | float | ✅ | 生成器默认权重 (0.0-1.0),用于 AI 策略生成 |
| `production_gate` | enum | ✅ | 生产闸门: `blocked`, `candidate`, `approved`, `deprecated` |
| `robustness_tests` | array[string] | ❌ | 通过的稳健性测试列表 |

### 完整 BlockSpec 示例

```yaml
block_id: "breakout_entry"
block_type: "entry"
name: "突破入场"
description: "价格突破近期高点时入场,需配合放量确认"
input_factor_types:
  - "numeric"
  - "boolean"
parameters:
  lookback_period:
    type: integer
    range: [10, 60]
    default: 20
  volume_multiplier:
    type: float
    range: [1.0, 3.0]
    default: 1.5
parameter_space:
  lookback_period:
    mode: range
    min: 10
    max: 60
    step: 5
  volume_multiplier:
    mode: range
    min: 1.0
    max: 3.0
    step: 0.25
weight: 1.0
enabled: true
required_tables:
  - "daily_bars"
required_columns:
  - "high"
  - "volume"
required_context: []
preview_support: "fully_supported"
dsl_output: "block_entry"
robustness_role: "entry_timing"
market_scope:
  - "A_SHARE"
  - "ETF"
status: "research"
version: "0.1.0"

# === 新增来源和证据字段 ===
source_refs:
  - "sqx_b143"                    # StrategyQuant X 突破入场块
  - "trader_methodology"          # Minervini VCP 突破思想
methodology_refs:
  - "minervini_vcp"               # 引用方法论翻译
evidence_level: E1                # 文献/方法论支持,待回测
generation_weight: 0.8            # AI 生成策略时的高权重 (经典入场方式)
production_gate: blocked          # E1 等级,禁止进入生产
robustness_tests: []              # 尚未通过稳健性测试
```

### methodology_refs 说明

方法论引用指向 `MethodologyTranslation` 记录,用于追踪 Block 是如何从交易大咖方法论拆解而来的。

例如:
- `minervini_vcp` → `breakout_entry`, `volatility_contraction`, `volume_expansion`
- `wyckoff_accumulation` → `accumulation_phase_detection`, `spring_entry`, `sign_of_strength`
- `turtle_trend_following` → `donchian_breakout`, `atr_position_sizing`, `whipsaw_filter`

---

## Methodology Translation Schema

用于将交易大咖方法论 (S8) 拆解为可观测、可回测的 Block 组合。

### 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `methodology_id` | string | ✅ | 方法论唯一标识,如 `minervini_vcp`, `wyckoff_accumulation` |
| `source_type` | enum | ✅ | 固定为 `trader_methodology` |
| `components` | object | ✅ | 方法论组件: setup/trigger/invalidation/risk/review |
| `converted_blocks` | array[string] | ✅ | 已转换的 block_id 列表 |
| `assumptions` | array[string] | ✅ | 方法论假设和前提条件 |
| `unsupported_parts` | array[string] | ✅ | 无法转换为 Block 的部分 (如主观判断) |
| `original_source` | string | ✅ | 原始来源 (书籍、文章、视频) |
| `translation_notes` | string | ❌ | 翻译说明和取舍理由 |

### components 结构

```yaml
components:
  setup:                        #  setup 条件 (形态、趋势、相对强弱等)
    - "trend_up"
    - "relative_strength_high"
    - "volatility_contraction"
  trigger:                      # 触发条件 (突破、放量等)
    - "breakout_on_volume"
  invalidation:                 # 失效条件 (假突破、止损等)
    - "failed_breakout"
    - "stop_loss_pct"
  risk:                         # 风控规则 (仓位、追高限制等)
    - "position_size_limit"
    - "no_chasing_extended"
  review:                       # 复盘规则 (交易后评估)
    - "post_trade_review"
```

### 完整示例

```yaml
methodology_id: "minervini_vcp"
source_type: trader_methodology
components:
  setup:
    - "trend_up"                  # 200日均线以上
    - "relative_strength_high"    # RS 排名 > 80
    - "volatility_contraction"    # 波动率收缩 (VCP)
  trigger:
    - "breakout_on_volume"        # 放量突破枢轴点
  invalidation:
    - "failed_breakout"           # 突破失败 (3日内回落)
    - "stop_loss_pct"             # 止损 7-8%
  risk:
    - "position_size_limit"       # 单仓位不超过 25%
    - "no_chasing_extended"       # 不追涨延伸阶段
  review:
    - "post_trade_review"         # 交易后复盘
converted_blocks:
  - "trend_filter_ma_stack"
  - "relative_strength_rank"
  - "vcp_contraction"
  - "breakout_entry"
  - "volume_expansion"
  - "stop_loss_pct"
  - "position_size_red_line"
assumptions:
  - "适用于成长股牛市环境"
  - "需要高流动性 (>1000万日成交额)"
  - "不适用于周期股顶部"
  - "假设市场整体趋势向上"
unsupported_parts:
  - "主观判断行业景气度"
  - "管理层质量评估"
  - "产品管线前景判断"
  - "精确枢轴点识别 (需人工标注)"
original_source: "Mark Minervini - Trade Like a Stock Market Wizard (1998)"
translation_notes: >
  VCP 核心是波动率收缩 + 放量突破,已拆解为 vcp_contraction + breakout_entry + volume_expansion。
  主观部分 (管理层、产品) 无法量化,保留在 unsupported_parts。
  止损和仓位限制已对接红线检查系统。
```

### 另一个示例: Wyckoff

```yaml
methodology_id: "wyckoff_accumulation"
source_type: trader_methodology
components:
  setup:
    - "downtrend_exhaustion"
    - "selling_climax"
    - "secondary_test"
    - "spring_or_shakeout"
  trigger:
    - "sign_of_strength"
    - "backup_to_creek"
  invalidation:
    - "spring_failure"
    - "breakdown_below_support"
  risk:
    - "position_scale_in"
    - "stop_below_spring_low"
  review:
    - "phase_identification_review"
converted_blocks:
  - "selling_climax_detection"
  - "spring_entry"
  - "sign_of_strength"
  - "stop_loss_pct"
  - "scale_in_order"
assumptions:
  - "适用于大资金吸筹阶段识别"
  - "需要较长周期 (周线/月线) 确认"
  - "假设主力行为可追踪"
unsupported_parts:
  - "Phase A-E 精确划分 (需人工标注)"
  - "Composite Man 意图判断"
  - "量价关系主观解读"
original_source: "Richard Wyckoff - Studies in Tape Reading (1910) / Stock Market Technique (1931)"
translation_notes: >
  Wyckoff 核心是吸筹/派发阶段识别和 Spring/Upthrust 信号。
  已拆解为 selling_climax_detection + spring_entry + sign_of_strength。
  Phase 划分依赖人工标注,暂不支持自动化。
```

---

## Tests

至少 20 个测试点,覆盖 Source/Evidence/Methodology 的核心校验逻辑。

### Source Registry 测试 (6 个)

| # | 测试点 | 预期 |
|---|--------|------|
| 1 | 注册合法 source | 成功,source_id 唯一 |
| 2 | 重复 source_id | 拒绝,抛出 `DuplicateSourceError` |
| 3 | 无效 source_type | 拒绝,抛出 `InvalidSourceType` |
| 4 | 缺失必填字段 | 拒绝,Pydantic 校验失败 |
| 5 | 查询 source_by_type | 返回指定类型的所有 sources |
| 6 | 查询 source_by_market | 返回适用指定市场的 sources |

### Evidence Validation 测试 (6 个)

| # | 测试点 | 预期 |
|---|--------|------|
| 7 | E0-E3 因子进入生产 | 拒绝,`production_gate=blocked` |
| 8 | E4 因子 + validation=passed | 允许,`production_gate=candidate` |
| 9 | E5 因子 + validation=passed | 允许,`production_gate=approved` |
| 10 | future_leakage_risk=high | 拒绝,`production_gate=blocked` |
| 11 | validation_status=failed | 拒绝,`production_gate=blocked` |
| 12 | metric_refs 阈值检查 | 所有关键指标必须 passed=true |

### FactorSpec Extensions 测试 (4 个)

| # | 测试点 | 预期 |
|---|--------|------|
| 13 | 缺少 source_refs | 拒绝,Pydantic 校验失败 |
| 14 | data_availability=unavailable | 允许注册,但 `production_gate=blocked` |
| 15 | a_share_notes 为空 | 拒绝,A 股必须有适配说明 |
| 16 | production_gate 自动计算 | 根据证据等级和验证状态正确计算 |

### BlockSpec Extensions 测试 (3 个)

| # | 测试点 | 预期 |
|---|--------|------|
| 17 | generation_weight 超出范围 | 拒绝,必须 0.0-1.0 |
| 18 | methodology_refs 引用不存在 | 警告,不阻塞 (方法论可选) |
| 19 | block 未通过 robustness | `production_gate=blocked` |

### Methodology Translation 测试 (3 个)

| # | 测试点 | 预期 |
|---|--------|------|
| 20 | 所有 converted_blocks 必须已注册 | 拒绝未注册的 block_id |
| 21 | components 五部分完整性 | 缺失任一组件则拒绝 |
| 22 | unsupported_parts 非空警告 | 提醒方法论有未量化部分 |

### 集成测试 (2 个)

| # | 测试点 | 预期 |
|---|--------|------|
| 23 | 完整因子生命周期 | 注册 (E1) → 验证 (E4) → 生产 (E5) |
| 24 | 方法论 → Block → DSL 全链路 | VCP 方法论拆解 → Block 注册 → DSL 生成 |

### 测试代码示例

```python
# hermass_platform/factors/tests/test_source_evidence_schema.py

import pytest
from hermass_platform.factors.source_registry import SourceRegistry
from hermass_platform.factors.evidence_validator import EvidenceValidator
from hermass_platform.factors.factor_schema import FactorSpec
from hermass_platform.factors.block_schema import BlockSpec
from hermass_platform.factors.methodology_translator import MethodologyTranslator

class TestSourceRegistry:
    def test_register_valid_source(self):
        registry = SourceRegistry()
        source = registry.register(
            source_id="sqx_b143",
            source_type="strategy_generator",
            name="StrategyQuant X Build 143",
            url_or_local_ref="https://strategyquant.com/doc/build-143",
            reliability="high",
            license_notes="商业软件,仅参考设计思想",
            applicable_markets=["A_SHARE", "US_EQUITY"]
        )
        assert source.source_id == "sqx_b143"
        assert registry.get("sqx_b143") == source

    def test_duplicate_source_id(self):
        registry = SourceRegistry()
        registry.register(...)  # 首次注册
        with pytest.raises(DuplicateSourceError):
            registry.register(...)  # 重复注册相同 source_id

    def test_invalid_source_type(self):
        registry = SourceRegistry()
        with pytest.raises(InvalidSourceType):
            registry.register(source_type="unknown_type", ...)

    def test_query_by_type(self):
        registry = SourceRegistry()
        registry.register(source_type="strategy_generator", ...)
        registry.register(source_type="open_quant_framework", ...)
        results = registry.list_by_type("strategy_generator")
        assert len(results) == 1

    def test_query_by_market(self):
        registry = SourceRegistry()
        registry.register(applicable_markets=["A_SHARE", "US_EQUITY"], ...)
        registry.register(applicable_markets=["CRYPTO"], ...)
        results = registry.list_by_market("A_SHARE")
        assert len(results) == 1

class TestEvidenceValidator:
    def test_blocked_low_evidence(self):
        validator = EvidenceValidator()
        gate = validator.evaluate_gate(evidence_level="E3", validation_status="passed")
        assert gate == "blocked"

    def test_candidate_e4(self):
        validator = EvidenceValidator()
        gate = validator.evaluate_gate(evidence_level="E4", validation_status="passed")
        assert gate == "candidate"

    def test_approved_e5(self):
        validator = EvidenceValidator()
        gate = validator.evaluate_gate(evidence_level="E5", validation_status="passed")
        assert gate == "approved"

    def test_blocked_future_leakage(self):
        validator = EvidenceValidator()
        gate = validator.evaluate_gate(
            evidence_level="E5",
            validation_status="passed",
            future_leakage_risk="high"
        )
        assert gate == "blocked"

    def test_blocked_validation_failed(self):
        validator = EvidenceValidator()
        gate = validator.evaluate_gate(
            evidence_level="E5",
            validation_status="failed"
        )
        assert gate == "blocked"

    def test_metric_threshold_check(self):
        validator = EvidenceValidator()
        metrics = [
            {"metric": "RankIC_mean", "value": 0.045, "threshold": 0.02, "passed": True},
            {"metric": "ICIR", "value": 0.85, "threshold": 0.5, "passed": True}
        ]
        assert validator.check_metrics_passed(metrics)

class TestFactorSpecExtensions:
    def test_missing_source_refs(self):
        with pytest.raises(ValidationError):
            FactorSpec(
                factor_id="test_factor",
                # source_refs 缺失
                evidence_level="E1",
                ...
            )

    def test_unavailable_data_blocked(self):
        spec = FactorSpec(
            factor_id="test_factor",
            source_refs=["academic_literature"],
            evidence_level="E1",
            data_availability="unavailable",
            future_leakage_risk="none",
            a_share_notes="测试说明",
            production_gate="blocked",
            ...
        )
        assert spec.production_gate == "blocked"

    def test_a_share_notes_required(self):
        with pytest.raises(ValidationError):
            FactorSpec(
                factor_id="test_factor",
                source_refs=["academic_literature"],
                evidence_level="E1",
                data_availability="available",
                future_leakage_risk="none",
                a_share_notes="",  # 空字符串
                production_gate="blocked",
                ...
            )

    def test_production_gate_auto_calculation(self):
        spec = FactorSpec(
            factor_id="quality_roe_ttm",
            source_refs=["institutional_factor"],
            evidence_level="E4",
            data_availability="available",
            future_leakage_risk="mitigated",
            a_share_notes="使用公告日期对齐",
            production_gate="candidate",  # 自动计算
            validation_status="passed",
            ...
        )
        assert spec.production_gate == "candidate"

class TestBlockSpecExtensions:
    def test_generation_weight_range(self):
        with pytest.raises(ValidationError):
            BlockSpec(
                block_id="test_block",
                generation_weight=1.5,  # 超出 0.0-1.0
                ...
            )

    def test_methodology_refs_warning(self):
        # methodology_refs 引用不存在的方法论,只警告不阻塞
        block = BlockSpec(
            block_id="breakout_entry",
            source_refs=["sqx_b143"],
            methodology_refs=["unknown_methodology"],
            evidence_level="E1",
            generation_weight=0.8,
            production_gate="blocked",
            ...
        )
        assert block.methodology_refs == ["unknown_methodology"]
        # 记录警告日志

class TestMethodologyTranslation:
    def test_all_converted_blocks_registered(self):
        translator = MethodologyTranslator()
        with pytest.raises(UnregisteredBlockError):
            translator.translate(
                methodology_id="test_methodology",
                converted_blocks=["nonexistent_block"],
                ...
            )

    def test_components_completeness(self):
        with pytest.raises(IncompleteComponentsError):
            MethodologyTranslation(
                methodology_id="test",
                source_type="trader_methodology",
                components={
                    "setup": ["trend_up"],
                    # 缺少 trigger/invalidation/risk/review
                },
                converted_blocks=[],
                assumptions=[],
                unsupported_parts=[],
                ...
            )

    def test_unsupported_parts_warning(self):
        translation = MethodologyTranslation(
            methodology_id="minervini_vcp",
            source_type="trader_methodology",
            components={...},
            converted_blocks=[...],
            assumptions=[...],
            unsupported_parts=["主观判断行业景气度"],
            ...
        )
        assert len(translation.unsupported_parts) > 0
        # 记录警告: 方法论有未量化部分

class TestIntegration:
    def test_factor_lifecycle(self):
        """测试因子从注册到生产的完整生命周期"""
        # 1. 注册 (E1)
        source = SourceRegistry().register(...)
        factor = FactorSpec(
            factor_id="quality_roe_ttm",
            source_refs=["institutional_factor"],
            evidence_level="E1",
            production_gate="blocked",
            ...
        )
        assert factor.production_gate == "blocked"

        # 2. 验证通过 (E4)
        factor.evidence_level = "E4"
        factor.validation_status = "passed"
        factor.production_gate = "candidate"
        assert factor.production_gate == "candidate"

        # 3. Walk-forward 通过 (E5)
        factor.evidence_level = "E5"
        factor.production_gate = "approved"
        assert factor.production_gate == "approved"

    def test_methodology_to_dsl_pipeline(self):
        """测试方法论 → Block → DSL 全链路"""
        # 1. 注册方法论
        methodology = MethodologyTranslator().translate(
            methodology_id="minervini_vcp",
            ...
        )

        # 2. 验证所有 converted_blocks 已注册
        for block_id in methodology.converted_blocks:
            assert BlockRegistry().get(block_id) is not None

        # 3. 生成 DSL (简化示例)
        dsl = generate_dsl_from_methodology(methodology)
        assert "block_entry" in dsl
        assert "stop_loss_pct" in dsl
```

---

## Implementation Order

分 5 步实施,每步都可独立验收。

### Step 1: Source Schema 和 Registry (Day 1)

**目标**: 实现来源注册表,支持 CRUD 和查询。

**交付物**:
- `hermass_platform/factors/source_schema.py` - Pydantic models
- `hermass_platform/factors/source_registry.py` - 注册表实现
- `config/factors/source_catalog.yaml` - 示例 catalog (至少 5 个 sources)
- `hermass_platform/factors/tests/test_source_registry.py` - 6 个测试

**验收标准**:
- 能注册/查询 source
- 重复 source_id 被拒绝
- 无效 source_type 被拒绝

### Step 2: Evidence Schema 和 Validator (Day 2)

**目标**: 实现证据等级校验和生产闸门逻辑。

**交付物**:
- `hermass_platform/factors/evidence_schema.py` - Pydantic models
- `hermass_platform/factors/evidence_validator.py` - 验证器实现
- `hermass_platform/factors/tests/test_evidence_validator.py` - 6 个测试

**验收标准**:
- E0-E3 被 blocked
- E4 + passed = candidate
- E5-E6 + passed = approved
- future_leakage_risk=high 被 blocked

### Step 3: FactorSpec 和 BlockSpec Extensions (Day 3)

**目标**: 扩展现有 schema,集成来源和证据字段。

**交付物**:
- `hermass_platform/factors/factor_schema.py` - 更新 FactorSpec
- `hermass_platform/factors/block_schema.py` - 更新 BlockSpec
- `hermass_platform/factors/tests/test_factor_block_extensions.py` - 7 个测试

**验收标准**:
- FactorSpec 必须有 source_refs, evidence_level, production_gate
- BlockSpec 必须有 source_refs, generation_weight, production_gate
- a_share_notes 必填

### Step 4: Methodology Translation (Day 4)

**目标**: 实现方法论拆解为 Block 的翻译器。

**交付物**:
- `hermass_platform/factors/methodology_schema.py` - Pydantic models
- `hermass_platform/factors/methodology_translator.py` - 翻译器实现
- `config/factors/methodology_catalog.yaml` - 示例 (VCP, Wyckoff)
- `hermass_platform/factors/tests/test_methodology_translator.py` - 3 个测试

**验收标准**:
- components 五部分完整性校验
- converted_blocks 必须是已注册的 block
- unsupported_parts 记录警告

### Step 5: 集成测试和 Catalog 示例 (Day 5)

**目标**: 完整链路测试,确保 Source → Evidence → Factor/Block → DSL 贯通。

**交付物**:
- `hermass_platform/factors/tests/test_integration.py` - 2 个集成测试
- `config/factors/source_catalog.yaml` - 完善至 10+ sources
- `config/factors/factor_catalog.yaml` - 更新为包含来源和证据字段
- `config/factors/block_catalog.yaml` - 更新为包含来源和方法论字段

**验收标准**:
- 因子生命周期测试通过 (E1 → E4 → E5)
- 方法论 → Block → DSL 链路测试通过
- 所有 24 个测试点通过

---

## Non-MVP Items

以下功能**不在当前实施范围**,仅预留接口:

1. **自动化证据验证 Pipeline**: 当前手动记录 metric_refs,未来可自动跑 IC/backtest/walk-forward 并更新 evidence_level。

2. **动态 production_gate**: 当前基于规则计算,未来可引入 Agent 审核和动态审批流。

3. **方法论自动拆解**: 当前 methodology_translator 是人工拆解,未来可用 LLM 辅助拆解 trader methodology。

4. **来源可信度动态调整**: 当前 reliability 是静态字段,未来可根据因子表现动态调整来源权重。

5. **跨来源因子对比**: 未来可对比同一因子在不同来源下的表现差异 (如 Qlib vs SQX 的 RSI 实现)。

6. **证据版本管理**: 当前 evidence 是单版本,未来需要版本化记录每次验证结果。

7. **因子血缘追踪**: 未来可追踪因子是如何从原始数据 → 计算 → 标准化 → DSL 的完整血缘。

8. **License 合规检查**: 当前 license_notes 是文本,未来可自动化检查商业因子的使用授权。
