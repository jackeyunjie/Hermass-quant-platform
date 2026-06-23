"""M3 Controlled Pilot onboarding routes.

Thin HTTP layer for disclaimer consent and H1/H2/H3 user diagnosis.
All business logic remains in the strategy_lab package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from hermass_platform.strategy_lab.audit import StrategyAuditLogger

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

AUDIT_DB = os.getenv(
    "STRATEGY_LAB_AUDIT_DB",
    "outputs/strategy_lab/web_audit.duckdb",
)

CONSENT_VERSION = "m3-pilot-v1"

DISCLAIMER_ITEMS = [
    ("research_only", "我理解 Hermass 是策略研究工具，不是投资建议服务。"),
    ("no_recommendation", "我不会把 Hermass 的输出当作买卖指令或向他人推荐。"),
    ("no_future_guarantee", "我理解回测结果不代表未来收益，历史表现不能预测未来。"),
    ("structured_process", "我接受所有策略必须经过 DSL 结构化、红线检查和回测验证。"),
    ("no_bypass", "我不会要求跳过止损、仓位限制或审计等安全约束。"),
    ("data_limits", "我理解当前数据可能存在停牌、退市、复权等处理边界，结果仅供研究参考。"),
    ("feedback", "我愿意把使用过程中的问题和建议反馈给 Hermass 团队。"),
]

DIAGNOSIS_QUESTIONS = [
    {
        "id": "q1",
        "text": "你当前的状态是？",
        "options": [
            ("idea", "我有一个策略想法，但不知道怎么表达清楚", {"H1": 3}),
            ("rules", "我已经有明确的策略规则（比如 MA 交叉 + 止损）", {"H2": 2}),
            ("validate", "我想用真实数据验证我的策略假设，并复盘每笔交易", {"H3": 3}),
            ("auto_profit", "我想找一个能自动赚钱的系统", {"REJECT": 1}),
        ],
    },
    {
        "id": "q2",
        "text": "你对策略回测的理解是？",
        "options": [
            ("returns", "回测就是看看历史收益率", {"H1": 1}),
            ("evidence", "回测需要看每笔交易的进出理由和当时的市场状态", {"H3": 2}),
            ("context", "回测结果不代表未来，但可以帮助我理解策略在什么环境下有效", {"H3": 3}),
            ("tomorrow", "我不关心回测，只关心明天买什么", {"REJECT": 1}),
        ],
    },
    {
        "id": "q3",
        "text": "你能接受以下哪种结果？",
        "options": [
            ("diagnose", "系统告诉我策略哪里不严谨，帮我修正", {"H2": 2}),
            ("records", "系统给我完整的交易记录，让我自己判断策略好坏", {"H3": 2}),
            ("direct_answer", "系统直接告诉我策略好不好，能不能赚钱", {"REJECT": 1}),
            ("explore", "我还没想好，想先试试", {"H1": 1}),
        ],
    },
    {
        "id": "q4",
        "text": "你有过量化交易经验吗？（可选）",
        "options": [
            ("none", "完全没有", {"H1": 1}),
            ("tools", "用过 Excel/同花顺等工具做过简单筛选", {"H2": 1}),
            ("code", "写过策略代码或用过量化平台（聚宽、米筐等）", {"H3": 1}),
            ("live", "管理过实盘量化策略", {"H3": 2}),
        ],
    },
]


@dataclass(frozen=True)
class DiagnosisResult:
    scores: dict[str, int]
    recommended_level: str
    rejected: bool


def _audit_logger() -> StrategyAuditLogger:
    logger = StrategyAuditLogger(AUDIT_DB)
    logger.init_schema()
    return logger


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _compute_diagnosis(answers: dict[str, str]) -> DiagnosisResult:
    scores: dict[str, int] = {"H1": 0, "H2": 0, "H3": 0}
    rejected = False
    for question in DIAGNOSIS_QUESTIONS:
        qid = question["id"]
        selected = answers.get(qid)
        if not selected:
            continue
        for value, _, deltas in question["options"]:
            if value == selected:
                if "REJECT" in deltas:
                    rejected = True
                for level, delta in deltas.items():
                    if level in scores:
                        scores[level] += delta
                break

    if rejected:
        return DiagnosisResult(scores=scores, recommended_level="REJECT", rejected=True)

    h3 = scores["H3"]
    h2 = scores["H2"]
    h1 = scores["H1"]
    if h3 >= 5 and h3 > h2 and h3 > h1:
        recommended = "H3"
    elif h2 >= 4 and h2 > h1:
        recommended = "H2"
    else:
        recommended = "H1"
    return DiagnosisResult(scores=scores, recommended_level=recommended, rejected=False)


@router.get("/")
async def disclaimer(request: Request) -> "TemplateResponse":
    """Show the M3 pilot disclaimer/consent form."""
    return templates.TemplateResponse(
        request,
        "onboarding/disclaimer.html",
        {
            "request": request,
            "items": DISCLAIMER_ITEMS,
            "consent_version": CONSENT_VERSION,
        },
    )


@router.post("/consent")
async def consent(
    request: Request,
    agreed_items: list[str] = Form(default_factory=list),
) -> Any:
    """Record disclaimer consent and redirect to diagnosis."""
    required = {key for key, _ in DISCLAIMER_ITEMS}
    if not required.issubset(set(agreed_items)):
        return templates.TemplateResponse(
            request,
            "onboarding/disclaimer.html",
            {
                "request": request,
                "items": DISCLAIMER_ITEMS,
                "consent_version": CONSENT_VERSION,
                "errors": ["请阅读并勾选全部免责声明项后方可进入系统。"],
            },
            status_code=400,
        )

    trace_id = f"onboarding-{uuid4().hex[:12]}"
    logger = _audit_logger()
    logger.log_onboarding_consent(
        trace_id=trace_id,
        consent_version=CONSENT_VERSION,
        agreed_items={key: key in agreed_items for key, _ in DISCLAIMER_ITEMS},
        client_ip=_client_ip(request),
    )
    logger.close()

    response = RedirectResponse(url="/onboarding/diagnosis", status_code=303)
    response.set_cookie(key="onboarding_trace_id", value=trace_id, httponly=True)
    return response


@router.get("/diagnosis")
async def diagnosis_form(request: Request) -> "TemplateResponse":
    """Show the H1/H2/H3 diagnosis questionnaire."""
    trace_id = request.cookies.get("onboarding_trace_id")
    if not trace_id:
        return RedirectResponse(url="/onboarding/", status_code=303)
    return templates.TemplateResponse(
        request,
        "onboarding/diagnosis.html",
        {
            "request": request,
            "questions": DIAGNOSIS_QUESTIONS,
            "trace_id": trace_id,
        },
    )


@router.post("/diagnosis")
async def diagnosis_submit(
    request: Request,
    q1: str = Form(...),
    q2: str = Form(...),
    q3: str = Form(...),
    q4: str = Form(""),
    selected_level: str = Form(""),
) -> Any:
    """Compute diagnosis result and redirect to recommendation page."""
    trace_id = request.cookies.get("onboarding_trace_id")
    if not trace_id:
        return RedirectResponse(url="/onboarding/", status_code=303)

    answers = {"q1": q1, "q2": q2, "q3": q3, "q4": q4}
    result = _compute_diagnosis(answers)

    logger = _audit_logger()
    logger.log_onboarding_diagnosis(
        trace_id=trace_id,
        answers=answers,
        scores=result.scores,
        recommended_level=result.recommended_level,
        selected_level=selected_level or None,
    )
    logger.close()

    if result.rejected:
        return RedirectResponse(url="/onboarding/not-suitable", status_code=303)

    response = RedirectResponse(
        url=f"/onboarding/result?level={result.recommended_level}",
        status_code=303,
    )
    return response


@router.get("/result")
async def result(
    request: Request,
    level: str = "H1",
) -> "TemplateResponse":
    """Show the recommended entry point and first-experience guidance."""
    trace_id = request.cookies.get("onboarding_trace_id")
    level_guides = {
        "H1": {
            "title": "H1：策略构建场",
            "description": "你当前最适合从「把策略想法讲清楚」开始。",
            "next_url": "/strategy-lab/structuring",
            "steps": [
                "查看 3 个冻结样例的 DSL 结构（如 MA5/MA20 策略）",
                "用自然语言描述一个简单策略",
                "查看 DSL 生成结果，理解每个字段含义",
                "体验红线检查：缺少止损会被拒绝",
                "完成一次 mock preview，看到条件命中数量",
            ],
        },
        "H2": {
            "title": "H2：策略诊断场",
            "description": "你已有策略规则，适合从验证和诊断开始。",
            "next_url": "/strategy-lab/diagnosis",
            "steps": [
                "查看一个已有 DSL 的 preview 结果",
                "观察红线检查通过/失败的不同结果",
                "理解 preview 中「可直接预览」与「需回测上下文」的区别",
                "修改一个参数，观察 preview 变化",
            ],
        },
        "H3": {
            "title": "H3：证据实验室",
            "description": "你希望用真实数据验证假设并复盘每笔交易。",
            "next_url": "/strategy-lab/evidence",
            "steps": [
                "查看完整策略的 light_real_v1 回测结果",
                "查看 trade records 和 event evidence",
                "理解「为什么进、为什么出、当时状态是什么」",
                "查看 audit timeline，理解 trace_id 追溯",
                "修改一个 exit 条件，重新跑回测并对比",
            ],
        },
    }
    guide = level_guides.get(level, level_guides["H1"])
    return templates.TemplateResponse(
        request,
        "onboarding/result.html",
        {
            "request": request,
            "trace_id": trace_id,
            "level": level,
            **guide,
        },
    )


@router.get("/not-suitable")
async def not_suitable(request: Request) -> "TemplateResponse":
    """Show a polite rejection page for users who expect investment advice."""
    trace_id = request.cookies.get("onboarding_trace_id")
    return templates.TemplateResponse(
        request,
        "onboarding/not_suitable.html",
        {
            "request": request,
            "trace_id": trace_id,
        },
    )


@router.get("/feedback")
async def feedback_form(
    request: Request,
    day: int = 7,
) -> Any:
    """Show the day 7 or day 14 feedback form."""
    trace_id = request.cookies.get("onboarding_trace_id")
    if not trace_id:
        return RedirectResponse(url="/onboarding/", status_code=303)
    if day not in (7, 14):
        return templates.TemplateResponse(
            request,
            "onboarding/feedback.html",
            {
                "request": request,
                "trace_id": trace_id,
                "day": day,
                "errors": ["反馈问卷仅支持第 7 天或第 14 天。"],
            },
            status_code=400,
        )
    return templates.TemplateResponse(
        request,
        "onboarding/feedback.html",
        {
            "request": request,
            "trace_id": trace_id,
            "day": day,
        },
    )


@router.post("/feedback")
async def feedback_submit(
    request: Request,
    day: int = Form(...),
    primary_level: str = Form(...),
    strategies_created: int = Form(0),
    blockers: str = Form(""),
    red_line_helpful: int = Form(0),
    explainability: int = Form(0),
    nps: int = Form(0),
    usage_count: int = Form(0),
    modified_idea: str = Form("false"),
    most_wanted_feature: str = Form(""),
    most_wanted_improvement: str = Form(""),
    would_pay: str = Form(""),
    free_text: str = Form(""),
) -> Any:
    """Record a feedback submission."""
    trace_id = request.cookies.get("onboarding_trace_id")
    if not trace_id:
        return RedirectResponse(url="/onboarding/", status_code=303)

    errors: list[str] = []
    if day not in (7, 14):
        errors.append("反馈问卷仅支持第 7 天或第 14 天。")
    if primary_level not in ("H1", "H2", "H3"):
        errors.append("请选择主要使用层级。")
    for field, label, lo, hi in [
        (red_line_helpful, "红线检查帮助度", 1, 5),
        (explainability, "回测结果可解释性", 1, 5),
        (nps, "NPS", 0, 10),
    ]:
        if not lo <= field <= hi:
            errors.append(f"{label} 必须在 {lo}-{hi} 之间。")

    if errors:
        return templates.TemplateResponse(
            request,
            "onboarding/feedback.html",
            {
                "request": request,
                "trace_id": trace_id,
                "day": day,
                "errors": errors,
            },
            status_code=400,
        )

    logger = _audit_logger()
    logger.log_onboarding_feedback(
        trace_id=trace_id,
        feedback_day=day,
        primary_level=primary_level,
        strategies_created=strategies_created,
        blockers=blockers,
        red_line_helpful=red_line_helpful,
        explainability=explainability,
        nps=nps,
        usage_count=usage_count,
        modified_idea=modified_idea.lower() in ("true", "on", "1", "yes"),
        most_wanted_feature=most_wanted_feature,
        most_wanted_improvement=most_wanted_improvement,
        would_pay=would_pay,
        free_text=free_text,
    )
    logger.close()

    return templates.TemplateResponse(
        request,
        "onboarding/feedback_thanks.html",
        {
            "request": request,
            "trace_id": trace_id,
            "day": day,
        },
    )


@router.get("/feedback/summary")
async def feedback_summary(
    request: Request,
    day: int | None = None,
) -> "TemplateResponse":
    """Simple ops summary of feedback submissions (no auth in M3)."""
    logger = _audit_logger()
    rows = logger.list_feedback(feedback_day=day, limit=200)
    logger.close()
    return templates.TemplateResponse(
        request,
        "onboarding/feedback_summary.html",
        {
            "request": request,
            "day": day,
            "rows": rows,
            "count": len(rows),
        },
    )
