"""신강/신약 판별 — 오행 점수 기반 (0~100)."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, BRANCH_OHAENG, HIDDEN_STEMS,
    GENERATING, CONTROLLING, OHAENG_LIST,
    MONTH_SEASON_ELEMENT, GEONROK,
)
from .models import FourPillars, StrengthResult


def _count_ohaeng(pillars: FourPillars) -> dict[str, float]:
    """사주 전체에서 오행별 점수 합산."""
    scores: dict[str, float] = {e: 0.0 for e in OHAENG_LIST}

    # 천간: 각 10점
    for p in [pillars.year, pillars.month, pillars.day, pillars.hour]:
        elem = STEM_OHAENG.get(p.stem, "")
        if elem:
            scores[elem] += 10.0

    # 지지: 본기 기준 10점
    for p in [pillars.year, pillars.month, pillars.day, pillars.hour]:
        elem = BRANCH_OHAENG.get(p.branch, "")
        if elem:
            scores[elem] += 10.0

    # 지장간 가중치
    for p in [pillars.year, pillars.month, pillars.day, pillars.hour]:
        hidden = HIDDEN_STEMS.get(p.branch, [])
        total_days = sum(w for _, w in hidden)
        for stem, weight in hidden:
            elem = STEM_OHAENG.get(stem, "")
            if elem and total_days > 0:
                scores[elem] += 5.0 * (weight / total_days)

    return scores


def _season_bonus(pillars: FourPillars) -> dict[str, float]:
    """월지 계절에 따른 오행 보정."""
    bonus: dict[str, float] = {e: 0.0 for e in OHAENG_LIST}
    season_elem = MONTH_SEASON_ELEMENT.get(pillars.month.branch, "")
    if season_elem:
        bonus[season_elem] += 15.0
    return bonus


def calc_strength(pillars: FourPillars) -> StrengthResult:
    """신강/신약 점수 계산 (0~100)."""
    day_stem = pillars.day.stem
    day_elem = STEM_OHAENG[day_stem]

    ohaeng_scores = _count_ohaeng(pillars)
    season = _season_bonus(pillars)
    for e in OHAENG_LIST:
        ohaeng_scores[e] += season[e]

    # 일간을 돕는 오행: 같은 오행(비겁) + 나를 생하는 오행(인성)
    from .constants import CONTROLLED_BY
    generating_me = None
    for k, v in GENERATING.items():
        if v == day_elem:
            generating_me = k
            break

    helping = ohaeng_scores.get(day_elem, 0)
    if generating_me:
        helping += ohaeng_scores.get(generating_me, 0)

    total = sum(ohaeng_scores.values())
    if total == 0:
        total = 1

    # 신강도 = (도와주는 오행 점수 / 전체) * 100
    raw_score = (helping / total) * 100
    score = max(0.0, min(100.0, raw_score))

    # 건록 보정: 일지가 건록이면 +5
    if GEONROK.get(day_stem) == pillars.day.branch:
        score = min(100.0, score + 5.0)

    if score >= 55:
        label = "신강"
    elif score >= 45:
        label = "중화"
    else:
        label = "신약"

    # 도와주는/빼앗는 오행
    helping_elems = [day_elem]
    if generating_me:
        helping_elems.append(generating_me)
    draining_elems = [e for e in OHAENG_LIST if e not in helping_elems]

    return StrengthResult(
        score=round(score, 1),
        label=label,
        day_stem=day_stem,
        day_stem_ohaeng=day_elem,
        ohaeng_scores={k: round(v, 1) for k, v in ohaeng_scores.items()},
        helping_elements=helping_elems,
        draining_elements=draining_elems,
    )
