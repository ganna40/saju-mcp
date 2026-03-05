"""질문 기반 심층 상담 엔진 — 구체적 질문에 맞춤 분석."""
from __future__ import annotations

import re
from .constants import TEN_GOD_CATEGORIES, STEM_OHAENG, CAREER_BY_PATTERN
from .models import (
    FourPillars, StrengthResult, PatternResult, YongshinResult,
    TenGodEntry, InteractionEntry, SinsalEntry, WealthResult,
    DaeunEntry, CrossInsight, ConsultResponse, TimingAdvice,
    SeunEntry,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


# 질문 키워드 → 분석 유형 매핑
_QUESTION_KEYWORDS = {
    "이직": "career_change",
    "퇴사": "career_change",
    "전직": "career_change",
    "직장": "career",
    "승진": "career",
    "사업": "business",
    "창업": "business",
    "재물": "wealth",
    "돈": "wealth",
    "투자": "wealth",
    "부동산": "wealth",
    "연애": "love",
    "결혼": "marriage",
    "이혼": "marriage",
    "배우자": "marriage",
    "건강": "health",
    "올해": "yearly",
    "내년": "yearly",
    "시기": "timing",
    "언제": "timing",
    "적성": "aptitude",
    "공부": "study",
    "시험": "study",
    "자격증": "study",
}


def _classify_question(question: str) -> str:
    """질문을 분석 유형으로 분류."""
    for keyword, qtype in _QUESTION_KEYWORDS.items():
        if keyword in question:
            return qtype
    return "general"


def deep_consult(
    question: str,
    pillars: FourPillars,
    ten_gods: list[TenGodEntry],
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    interactions: list[InteractionEntry],
    sinsal: list[SinsalEntry],
    wealth: WealthResult,
    daeun: list[DaeunEntry],
    cross_insights: list[CrossInsight],
    gender: str = "남",
    birth_year: int = 0,
    target_year: int = 2026,
    seun: SeunEntry | None = None,
) -> ConsultResponse:
    """질문에 맞춤 심층 분석."""
    qtype = _classify_question(question)

    # 기본 구조
    resp = ConsultResponse(
        question=question,
        question_type=qtype,
    )

    # 질문 유형별 분석
    if qtype == "career_change":
        _analyze_career_change(resp, pillars, ten_gods, strength, pattern,
                               yongshin, daeun, cross_insights, birth_year, target_year, seun)
    elif qtype in ("career", "business"):
        _analyze_career(resp, pillars, ten_gods, strength, pattern,
                        yongshin, daeun, cross_insights, qtype)
    elif qtype == "wealth":
        _analyze_wealth(resp, wealth, cross_insights, daeun, yongshin, birth_year, target_year)
    elif qtype in ("love", "marriage"):
        _analyze_love(resp, pillars, ten_gods, sinsal, interactions,
                      daeun, gender, cross_insights, birth_year, qtype)
    elif qtype == "health":
        _analyze_health(resp, strength, yongshin, sinsal)
    elif qtype == "yearly":
        _analyze_yearly(resp, daeun, yongshin, birth_year, target_year, seun, cross_insights)
    elif qtype == "study":
        _analyze_study(resp, ten_gods, cross_insights, daeun, yongshin, birth_year, target_year)
    else:
        _analyze_general(resp, cross_insights, strength, pattern)

    # 관련 교차 인사이트 첨부
    resp.cross_insights = _filter_relevant_insights(cross_insights, qtype)

    return resp


def _filter_relevant_insights(insights: list[CrossInsight], qtype: str) -> list[CrossInsight]:
    """질문 유형에 관련된 인사이트만 필터."""
    relevance = {
        "career_change": ["관인상생", "상관견관", "역마", "충돌"],
        "career": ["관인상생", "상관견관", "살인상생", "에너지"],
        "business": ["식상생재", "비겁쟁재", "겁재극재"],
        "wealth": ["식상생재", "비겁쟁재", "겁재극재", "전성기", "주의"],
        "love": ["상관견관", "도화역마", "재관혼잡"],
        "marriage": ["상관견관", "재관혼잡", "궁위"],
        "health": ["에너지", "양인백호"],
        "yearly": ["전성기", "주의"],
        "study": ["관인상생", "살인상생"],
    }
    keywords = relevance.get(qtype, [])
    if not keywords:
        return insights[:3]
    return [i for i in insights if any(k in i.pattern_name for k in keywords)][:5]


def _analyze_career_change(resp, pillars, ten_gods, strength, pattern,
                           yongshin, daeun, insights, birth_year, target_year, seun):
    """이직 분석."""
    current_age = target_year - birth_year + 1

    # 현재 대운
    current_daeun = None
    for d in daeun:
        if d.age_start <= current_age <= d.age_end:
            current_daeun = d
            break

    # 관성 유무 = 직장운
    has_gwanseong = any(tg.category == "관성" for tg in ten_gods)
    has_siksang = any(tg.category == "식상" for tg in ten_gods)
    has_yeokma = False  # 신살에서 확인하려면 별도 체크 필요

    # 판단
    parts = []
    can_change = True
    reasons = []

    if current_daeun:
        d_elems = {current_daeun.stem_ohaeng, current_daeun.branch_ohaeng} - {""}
        favorable = set(yongshin.favorable_elements)
        unfavorable = set(yongshin.unfavorable_elements)

        if d_elems & favorable:
            parts.append(f"현재 대운({current_daeun.stem}{current_daeun.branch})이 용신 대운이라 전반적으로 좋은 흐름입니다.")
            reasons.append("용신 대운")
        elif d_elems & unfavorable:
            parts.append(f"현재 대운({current_daeun.stem}{current_daeun.branch})이 기신 대운이라 신중해야 합니다.")
            can_change = False
            reasons.append("기신 대운")

        # 대운 십신이 관성이면 직장 변화
        tg_s = current_daeun.ten_god_stem or ""
        tg_b = current_daeun.ten_god_branch or ""
        cats = {TEN_GOD_CATEGORIES.get(tg_s, ""), TEN_GOD_CATEGORIES.get(tg_b, "")} - {""}

        if "관성" in cats:
            parts.append("대운에 관성이 들어와 직장 변화 에너지가 있습니다.")
            reasons.append("대운 관성")
        if "식상" in cats:
            parts.append("대운에 식상이 들어와 새로운 시도에 유리합니다.")
            reasons.append("대운 식상")

    # 신강/약 기준
    if strength.score >= 55:
        parts.append("신강하여 변화를 감당할 체력이 있습니다.")
    else:
        parts.append("신약하여 무리한 변화보다는 준비된 이직이 좋습니다.")

    # 상관견관이면 조직 갈등
    sanggwan_insight = next((i for i in insights if "상관견관" in i.pattern_name), None)
    if sanggwan_insight:
        parts.append("상관견관 구조가 있어 현 직장에서의 갈등이 이직 동기일 수 있습니다.")

    if can_change:
        resp.answer_summary = "이직 가능합니다. 시기와 방향이 중요합니다."
    else:
        resp.answer_summary = "지금은 신중하게. 준비 기간을 거친 후 이직하는 것이 좋습니다."

    resp.detailed_analysis = " ".join(parts)

    # 시기 조언
    for d in daeun:
        yr = birth_year + d.age_start - 1
        if yr < target_year:
            continue
        d_elems = {d.stem_ohaeng, d.branch_ohaeng} - {""}
        favorable = set(yongshin.favorable_elements)
        if d_elems & favorable:
            tg_s = d.ten_god_stem or calc_ten_god(pillars.day.stem, d.stem)
            tg_b = d.ten_god_branch or calc_ten_god_for_branch(pillars.day.stem, d.branch)
            resp.timing.append(TimingAdvice(
                period=f"{d.age_start}~{d.age_end}세 ({yr}~{yr + d.age_end - d.age_start}년)",
                action="이직/전직에 유리한 시기",
                reason=f"용신 대운, {tg_s}/{tg_b}",
            ))
            if len(resp.timing) >= 2:
                break

    resp.cautions = [r for r in reasons if "기신" in r]
    resp.action_items = [
        "이직 전 용신 오행과 관련된 업종/환경인지 확인할 것",
        f"신강도가 {strength.score}점이므로 {'과감하게 도전 가능' if strength.score >= 55 else '안정적인 곳으로 이동 권장'}",
    ]


def _analyze_career(resp, pillars, ten_gods, strength, pattern,
                    yongshin, daeun, insights, qtype):
    """직장/사업 분석."""
    cats = {}
    for tg in ten_gods:
        cats[tg.category] = cats.get(tg.category, 0) + 1

    if qtype == "business":
        can_biz = strength.score >= 55 and cats.get("재성", 0) >= 1
        if can_biz:
            resp.answer_summary = "사업 적성이 있습니다."
            resp.detailed_analysis = f"신강({strength.score}점)하고 재성이 {cats.get('재성', 0)}개 있어 사업 체력과 돈 감각이 있습니다."
        else:
            resp.answer_summary = "직장 생활이 더 안정적입니다."
            resp.detailed_analysis = f"신강도 {strength.score}점으로 {'체력은 되나 재성이 부족' if strength.score >= 55 else '사업을 버틸 체력이 부족'}합니다."

        resp.cautions = []
        bigeop_insight = next((i for i in insights if "비겁" in i.pattern_name), None)
        if bigeop_insight:
            resp.cautions.append(bigeop_insight.warning)
    else:
        resp.answer_summary = f"{pattern.name} 기반 직업 적성 분석"
        careers = CAREER_BY_PATTERN.get(pattern.name, [])
        resp.detailed_analysis = f"격국 {pattern.name}에 맞는 직업: {', '.join(careers[:4]) if careers else '다방면'}"


def _analyze_wealth(resp, wealth, insights, daeun, yongshin, birth_year, target_year):
    """재물운 분석."""
    resp.answer_summary = f"재물 그릇 {wealth.grade}등급 ({wealth.total_score:.0f}점)"

    parts = [f"재물 등급: {wealth.grade} ({wealth.grade_label})"]
    if wealth.peak_periods:
        parts.append(f"전성기: {', '.join(wealth.peak_periods)}")
    if wealth.risk_periods:
        parts.append(f"위험기: {', '.join(wealth.risk_periods)}")

    wealth_insights = [i for i in insights if "재" in i.pattern_name or "식상생재" in i.pattern_name]
    for wi in wealth_insights[:2]:
        parts.append(f"{wi.pattern_name}: {wi.life_impact}")

    resp.detailed_analysis = " | ".join(parts)
    resp.cautions = [i.warning for i in wealth_insights if i.warning]


def _analyze_love(resp, pillars, ten_gods, sinsal, interactions,
                  daeun, gender, insights, birth_year, qtype):
    """연애/결혼 분석."""
    target_cat = "재성" if gender == "남" else "관성"
    count = sum(1 for tg in ten_gods if tg.category == target_cat)

    il_ji_tg = next((tg for tg in ten_gods if tg.position == "일지"), None)

    if count >= 2:
        resp.answer_summary = f"이성 인연이 풍부합니다 ({target_cat} {count}개)"
    elif count == 1:
        resp.answer_summary = "적당한 이성 인연이 있습니다"
    else:
        resp.answer_summary = f"이성 인연이 약합니다 ({target_cat} 0개). 대운에서 인연이 옵니다"

    parts = [f"배우자성({target_cat}): {count}개"]
    if il_ji_tg:
        parts.append(f"배우자궁(일지): {il_ji_tg.ten_god}")

    resp.detailed_analysis = " | ".join(parts)

    # 결혼 시기
    if qtype == "marriage":
        for d in daeun:
            tg_s = d.ten_god_stem or calc_ten_god(pillars.day.stem, d.stem)
            tg_b = d.ten_god_branch or calc_ten_god_for_branch(pillars.day.stem, d.branch)
            s_cat = TEN_GOD_CATEGORIES.get(tg_s, "")
            b_cat = TEN_GOD_CATEGORIES.get(tg_b, "")
            if target_cat in (s_cat, b_cat) and 20 <= d.age_start <= 45:
                yr = birth_year + d.age_start - 1
                resp.timing.append(TimingAdvice(
                    period=f"{d.age_start}~{d.age_end}세",
                    action="결혼 인연이 들어오는 시기",
                    reason=f"대운 {d.stem}{d.branch}에 {target_cat}",
                ))


def _analyze_health(resp, strength, yongshin, sinsal):
    """건강 분석."""
    from .constants import ELEM_ORGAN, HEALTH_WEAKNESS_BY_ELEM
    scores = strength.ohaeng_scores
    weakest = min(scores, key=scores.get) if scores else ""
    resp.answer_summary = f"가장 약한 오행: {weakest} — 관련 장기 주의"
    organ = ELEM_ORGAN.get(weakest, {})
    resp.detailed_analysis = f"약한 오행 {weakest}: {organ.get('장기', '')} / {organ.get('신체', '')} 주의. {HEALTH_WEAKNESS_BY_ELEM.get(weakest, '')}"

    has_baekho = any(s.name == "백호대살" for s in sinsal)
    if has_baekho:
        resp.cautions.append("백호대살 보유 — 사고/수술 수가 있으니 안전에 주의")


def _analyze_yearly(resp, daeun, yongshin, birth_year, target_year, seun, insights):
    """올해/내년 운세."""
    current_age = target_year - birth_year + 1
    current_daeun = None
    for d in daeun:
        if d.age_start <= current_age <= d.age_end:
            current_daeun = d
            break

    parts = [f"{target_year}년 만 {current_age}세"]
    if current_daeun:
        parts.append(f"대운: {current_daeun.stem}{current_daeun.branch}")
    if seun:
        parts.append(f"세운: {seun.stem}{seun.branch}")

    resp.answer_summary = " | ".join(parts)
    resp.detailed_analysis = "세부 분석은 saju_yearly 도구를 함께 사용하면 더 구체적입니다."


def _analyze_study(resp, ten_gods, insights, daeun, yongshin, birth_year, target_year):
    """공부/시험 분석."""
    gwanin = next((i for i in insights if "관인상생" in i.pattern_name), None)
    if gwanin:
        resp.answer_summary = "관인상생 구조로 시험/학업에 유리합니다"
        resp.detailed_analysis = gwanin.causal_chain + " " + gwanin.life_impact
    else:
        has_inseong = any(tg.category == "인성" for tg in ten_gods)
        if has_inseong:
            resp.answer_summary = "인성이 있어 학습 능력이 있습니다"
        else:
            resp.answer_summary = "인성이 약하여 학업보다 실무 경험이 맞을 수 있습니다"


def _analyze_general(resp, insights, strength, pattern):
    """일반 질문."""
    resp.answer_summary = f"{pattern.name}, {strength.label}({strength.score}점)"
    if insights:
        resp.detailed_analysis = insights[0].causal_chain + " " + insights[0].life_impact
