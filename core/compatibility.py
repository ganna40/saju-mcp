"""궁합 분석 — 두 사람의 사주 비교."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, STEM_YINYANG, BRANCH_OHAENG,
    GENERATING, CONTROLLING, OHAENG_LIST,
    CHEONGAN_HAP, YUKAP, YUKCHUNG, SAMHAP,
)
from .models import (
    FourPillars, CompatibilityResult, InteractionEntry,
)
from .ten_gods import calc_ten_god


def _day_stem_relation(stem_a: str, stem_b: str) -> tuple[str, float]:
    """일간 관계 분석 + 점수."""
    elem_a = STEM_OHAENG[stem_a]
    elem_b = STEM_OHAENG[stem_b]
    yy_a = STEM_YINYANG[stem_a]
    yy_b = STEM_YINYANG[stem_b]

    # 천간합
    if frozenset({stem_a, stem_b}) in CHEONGAN_HAP:
        return f"{stem_a}+{stem_b} 천간합 (최상의 조합)", 25.0

    if elem_a == elem_b:
        if yy_a != yy_b:
            return f"같은 오행({elem_a}) 음양 조화 — 서로 이해하며 보완", 18.0
        return f"같은 오행({elem_a}) 같은 음양 — 비슷한 성향, 경쟁 가능", 12.0

    if GENERATING.get(elem_a) == elem_b or GENERATING.get(elem_b) == elem_a:
        return f"상생 관계({elem_a}↔{elem_b}) — 서로 도와주는 관계", 20.0

    if CONTROLLING.get(elem_a) == elem_b:
        return f"{elem_a}→{elem_b} 극 관계 — A가 주도, B가 따르는 구도", 8.0

    if CONTROLLING.get(elem_b) == elem_a:
        return f"{elem_b}→{elem_a} 극 관계 — B가 주도, A가 따르는 구도", 8.0

    return "보통 관계", 10.0


def _ohaeng_complement(pillars_a: FourPillars, pillars_b: FourPillars) -> tuple[str, float]:
    """오행 보완 분석."""
    def count_ohaeng(p: FourPillars) -> dict[str, int]:
        counts = {e: 0 for e in OHAENG_LIST}
        for pillar in [p.year, p.month, p.day, p.hour]:
            se = STEM_OHAENG.get(pillar.stem, "")
            be = BRANCH_OHAENG.get(pillar.branch, "")
            if se:
                counts[se] += 1
            if be:
                counts[be] += 1
        return counts

    ca = count_ohaeng(pillars_a)
    cb = count_ohaeng(pillars_b)

    # A에 부족한데 B에 풍부한 오행
    complement_count = 0
    details = []
    for e in OHAENG_LIST:
        if ca[e] == 0 and cb[e] >= 2:
            complement_count += 1
            details.append(f"A에 부족한 {e}을 B가 보완")
        if cb[e] == 0 and ca[e] >= 2:
            complement_count += 1
            details.append(f"B에 부족한 {e}을 A가 보완")

    score = min(25.0, complement_count * 8.0)
    desc = " / ".join(details) if details else "오행 보완 관계 미약"
    return desc, score


def _branch_interactions(pillars_a: FourPillars, pillars_b: FourPillars) -> tuple[list[InteractionEntry], float]:
    """두 사주 사이의 지지 합충."""
    results: list[InteractionEntry] = []
    score = 0.0

    branches_a = [
        (pillars_a.year.branch, "A년지"), (pillars_a.month.branch, "A월지"),
        (pillars_a.day.branch, "A일지"), (pillars_a.hour.branch, "A시지"),
    ]
    branches_b = [
        (pillars_b.year.branch, "B년지"), (pillars_b.month.branch, "B월지"),
        (pillars_b.day.branch, "B일지"), (pillars_b.hour.branch, "B시지"),
    ]

    for ba, pa in branches_a:
        for bb, pb in branches_b:
            key = frozenset({ba, bb})

            if key in YUKAP:
                results.append(InteractionEntry(
                    type="합", subtype="육합",
                    positions=[pa, pb], elements=[ba, bb],
                    result=f"→ {YUKAP[key]}",
                    description=f"{ba}+{bb} 육합",
                ))
                score += 5.0

            if key in YUKCHUNG:
                results.append(InteractionEntry(
                    type="충", subtype="육충",
                    positions=[pa, pb], elements=[ba, bb],
                    description=f"{ba}↔{bb} 육충",
                ))
                score -= 5.0

    # 일지끼리의 합충은 가중치 2배
    day_key = frozenset({pillars_a.day.branch, pillars_b.day.branch})
    if day_key in YUKAP:
        score += 5.0  # 추가 보너스
    if day_key in YUKCHUNG:
        score -= 5.0  # 추가 감점

    return results, max(-25.0, min(25.0, score))


def _mutual_ten_gods(pillars_a: FourPillars, pillars_b: FourPillars) -> tuple[dict[str, str], float]:
    """상호 십신 분석."""
    stem_a = pillars_a.day.stem
    stem_b = pillars_b.day.stem

    tg_a_sees_b = calc_ten_god(stem_a, stem_b)
    tg_b_sees_a = calc_ten_god(stem_b, stem_a)

    mutual = {
        "A가 보는 B": tg_a_sees_b,
        "B가 보는 A": tg_b_sees_a,
    }

    # 점수: 정재/정관/정인 → 좋음, 상관/편관 → 나쁨
    good = {"정재", "정관", "정인", "식신"}
    bad = {"상관", "편관"}

    score = 0.0
    for tg in [tg_a_sees_b, tg_b_sees_a]:
        if tg in good:
            score += 8.0
        elif tg in bad:
            score -= 3.0
        else:
            score += 3.0

    return mutual, max(-25.0, min(25.0, score))


def calc_compatibility(pillars_a: FourPillars, pillars_b: FourPillars) -> CompatibilityResult:
    """궁합 총합 분석."""
    stem_a = pillars_a.day.stem
    stem_b = pillars_b.day.stem

    # 1. 일간 관계
    relation_desc, relation_score = _day_stem_relation(stem_a, stem_b)

    # 2. 오행 보완
    complement_desc, complement_score = _ohaeng_complement(pillars_a, pillars_b)

    # 3. 합충
    interactions, interaction_score = _branch_interactions(pillars_a, pillars_b)

    # 4. 상호 십신
    mutual, mutual_score = _mutual_ten_gods(pillars_a, pillars_b)

    total = relation_score + complement_score + max(0, interaction_score) + max(0, mutual_score)
    total = max(0, min(100, total))

    if total >= 80:
        grade = "천생연분"
    elif total >= 65:
        grade = "좋은 궁합"
    elif total >= 50:
        grade = "무난한 궁합"
    elif total >= 35:
        grade = "보통 궁합"
    else:
        grade = "노력이 필요한 궁합"

    details = [
        f"[일간관계] {relation_desc} ({relation_score}점)",
        f"[오행보완] {complement_desc} ({complement_score}점)",
        f"[합충관계] 합충 점수 {interaction_score}점",
        f"[상호십신] A→B: {mutual['A가 보는 B']}, B→A: {mutual['B가 보는 A']} ({mutual_score}점)",
    ]

    return CompatibilityResult(
        total_score=round(total, 1),
        grade=grade,
        day_stem_relation=relation_desc,
        ohaeng_complement=complement_desc,
        interactions=interactions,
        mutual_ten_gods=mutual,
        summary=f"{grade} (총점 {round(total, 1)}점/100점)",
        details=details,
    )
