"""서사 생성 엔진 — 교차 분석 결과를 하나의 스토리로 엮는다."""
from __future__ import annotations

from .constants import (
    DAY_STEM_METAPHORS, DAY_STEM_TRAITS, STEM_OHAENG,
    TEN_GOD_CATEGORIES, PATTERN_TRAITS, CAREER_BY_PATTERN,
)
from .models import (
    FourPillars, StrengthResult, PatternResult, YongshinResult,
    TenGodEntry, CrossInsight, Retrodiction, DaeunEntry,
    WealthResult, SajuNarrative,
)


def generate_narrative(
    pillars: FourPillars,
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    ten_gods: list[TenGodEntry],
    cross_insights: list[CrossInsight],
    retrodictions: list[Retrodiction],
    wealth: WealthResult,
    daeun: list[DaeunEntry],
    gender: str = "남",
    birth_year: int = 0,
) -> SajuNarrative:
    """교차 분석 + 역추적 결과를 종합 서사로 변환."""
    day_stem = pillars.day.stem
    meta = DAY_STEM_METAPHORS.get(day_stem, {})

    return SajuNarrative(
        one_line=_one_line(pattern, strength, cross_insights, wealth),
        personality_story=_personality_story(pillars, strength, pattern, ten_gods, meta, cross_insights),
        life_arc=_life_arc(daeun, yongshin, retrodictions, birth_year, pillars),
        current_chapter=_current_chapter(daeun, birth_year, yongshin, pillars),
        top3_insights=_top3(cross_insights),
        practical_advice=_advice(cross_insights, yongshin, strength, pattern),
    )


def _one_line(pattern, strength, insights, wealth) -> str:
    """이 사주를 한 줄로 정의."""
    # 가장 높은 우선순위 인사이트 기반
    if insights:
        top = insights[0]
        if "식상생재" in top.pattern_name:
            return f"재능으로 돈 버는 팔자 — {pattern.name}, 재물 {wealth.grade}등급"
        if "관인상생" in top.pattern_name:
            return f"공부로 인정받는 팔자 — {pattern.name}, 시험/자격증에 강함"
        if "상관견관" in top.pattern_name:
            return f"자유로운 영혼, 틀을 깨는 팔자 — {pattern.name}"
        if "편인도식" in top.pattern_name:
            return f"숨은 재능이 있는 팔자 — {pattern.name}, 표현 출구 필요"
        if "비겁쟁재" in top.pattern_name:
            return f"혼자 벌어야 지키는 팔자 — {pattern.name}, 동업 금지"
        if "종격" in top.pattern_name:
            return f"흐름을 따라가는 특별한 팔자 — {pattern.name}"

    # 기본 패턴
    if strength.score >= 65:
        return f"에너지 넘치는 {pattern.name} — 발산할 출구 필요"
    if strength.score <= 35:
        return f"지원군이 필요한 {pattern.name} — 혼자보다 함께"

    return f"{pattern.name}, {strength.label}({strength.score}점) — 재물 {wealth.grade}등급"


def _personality_story(pillars, strength, pattern, ten_gods, meta, insights) -> str:
    """성격 서사 2~3문단."""
    day_stem = pillars.day.stem
    parts = []

    # 1문단: 일간 메타포 기반
    image = meta.get("image", day_stem)
    nature = meta.get("nature", "")
    if strength.score >= 55:
        desc = meta.get("strong", "")
    elif strength.score <= 45:
        desc = meta.get("weak", "")
    else:
        desc = meta.get("balanced", "")

    parts.append(
        f"{day_stem} 일간은 {image}에 비유됩니다. "
        f"{nature}이 핵심 본성이고, "
        f"신강도 {strength.score}점({strength.label})이라 {desc}."
    )

    # 2문단: 십신 조합 기반 사회적 행동
    cats = {}
    for tg in ten_gods:
        cats[tg.category] = cats.get(tg.category, 0) + 1
    dominant = max(cats, key=cats.get) if cats else ""

    wolgan_tg = next((tg for tg in ten_gods if tg.position == "월간"), None)
    wolgan_desc = ""
    if wolgan_tg:
        wolgan_desc = f"월간에 {wolgan_tg.ten_god}이 있어 사회생활에서 {_wolgan_style(wolgan_tg.ten_god)}"

    parts.append(
        f"십신 구성을 보면 {dominant}이 {cats.get(dominant, 0)}개로 지배적입니다. "
        f"{wolgan_desc} "
        f"격국은 {pattern.name}으로, {pattern.traits}."
    )

    # 3문단: 교차 분석 기반 핵심 패턴
    personality_insights = [i for i in insights if i.priority <= 2]
    if personality_insights:
        top = personality_insights[0]
        parts.append(
            f"특히 이 사주의 핵심 구조는 '{top.pattern_name}'입니다. "
            f"{top.causal_chain} "
            f"{top.life_impact}"
        )

    return "\n\n".join(parts)


def _wolgan_style(tg_name: str) -> str:
    """월간 십신별 사회 스타일 한 줄."""
    styles = {
        "비견": "독립적으로 일하는 걸 선호합니다.",
        "겁재": "사교적이지만 속내를 잘 안 보여줍니다.",
        "식신": "표현력이 좋고 사람들과 잘 어울립니다.",
        "상관": "틀에 박힌 걸 싫어하고 자기 방식대로 합니다.",
        "편재": "돈 감각이 있고 여러 일을 동시에 벌입니다.",
        "정재": "계획적이고 안정적인 걸 추구합니다.",
        "편관": "겉으로는 온화하지만 속으로는 승부욕이 강합니다.",
        "정관": "원칙적이고 조직 생활에 잘 맞습니다.",
        "편인": "남들과 다른 독특한 시각을 가지고 있습니다.",
        "정인": "배움을 좋아하고 학구적입니다.",
    }
    return styles.get(tg_name, "자신만의 스타일이 있습니다.")


def _life_arc(daeun, yongshin, retros, birth_year, pillars) -> str:
    """인생 전체 흐름 서사."""
    if not retros:
        return ""

    parts = []
    favorable = set(yongshin.favorable_elements)

    past_retros = [r for r in retros if r.year < 2026]

    # 과거 흐름 요약
    if past_retros:
        parts.append("지금까지의 인생 흐름을 보면:")
        for r in past_retros[:4]:
            marker = "★" if r.confidence == "높음" else "·"
            parts.append(f"  {marker} {r.age}세({r.year}년) — {r.predicted_event}")

    # 미래 대운 예측
    future_daeun = [d for d in daeun if birth_year + d.age_start - 1 >= 2026]
    if future_daeun:
        parts.append("")
        parts.append("앞으로의 흐름:")
        for d in future_daeun[:3]:
            d_elems = {d.stem_ohaeng, d.branch_ohaeng} - {""}
            is_good = bool(d_elems & favorable)
            label = "↑ 상승기" if is_good else "→ 안정기"
            parts.append(f"  {label} {d.age_start}~{d.age_end}세({d.stem}{d.branch})")

    return "\n".join(parts)


def _current_chapter(daeun, birth_year, yongshin, pillars) -> str:
    """지금은 인생의 어떤 시기인지."""
    current_age = 2026 - birth_year + 1
    current_daeun = None
    for d in daeun:
        if d.age_start <= current_age <= d.age_end:
            current_daeun = d
            break

    if not current_daeun:
        return ""

    d_elems = {current_daeun.stem_ohaeng, current_daeun.branch_ohaeng} - {""}
    favorable = set(yongshin.favorable_elements)
    unfavorable = set(yongshin.unfavorable_elements)

    if d_elems & favorable:
        tone = "용신이 작용하는 상승기"
    elif d_elems & unfavorable:
        tone = "기신이 작용하여 조심해야 하는 시기"
    else:
        tone = "큰 변동 없이 내실을 다지는 시기"

    tg_s = current_daeun.ten_god_stem or ""
    tg_b = current_daeun.ten_god_branch or ""

    return (
        f"현재 만 {current_age}세, {current_daeun.stem}{current_daeun.branch} 대운 "
        f"({current_daeun.age_start}~{current_daeun.age_end}세) 중입니다. "
        f"대운 십신 {tg_s}/{tg_b}로, {tone}입니다."
    )


def _top3(insights: list[CrossInsight]) -> list[str]:
    """핵심 통찰 3개."""
    result = []
    for i in insights[:3]:
        result.append(f"{i.pattern_name}: {i.life_impact}")
    return result


def _advice(insights, yongshin, strength, pattern) -> list[str]:
    """구체적 실행 조언."""
    advice = []

    # 교차 분석 기반 조언
    for i in insights[:3]:
        if i.warning:
            advice.append(i.warning)

    # 용신 기반 기본 조언
    if yongshin.yongshin:
        from .constants import ELEM_COLOR, ELEM_DIRECTION, ELEM_FOOD
        elem = yongshin.yongshin
        color = ELEM_COLOR.get(elem, "")
        direction = ELEM_DIRECTION.get(elem, "")
        food = ELEM_FOOD.get(elem, "")
        advice.append(f"용신({elem}): {color} 계열 착용, {direction} 방향, {food} 섭취가 도움.")

    return advice[:5]
