"""재물그릇 v2 — 9항목 100점 만점 채점."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, BRANCH_OHAENG, HIDDEN_STEMS,
    CONTROLLING, GENERATING, TEN_GOD_CATEGORIES,
    WEALTH_GRADES,
)
from .models import (
    FourPillars, StrengthResult, PatternResult,
    WealthResult, WealthItem, DaeunEntry, InteractionEntry,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


def _get_all_ten_god_cats(day_stem: str, pillars: FourPillars) -> list[tuple[str, str]]:
    """(위치, 십신카테고리) 리스트."""
    results = []
    for label, p, is_stem in [
        ("년간", pillars.year, True), ("월간", pillars.month, True),
        ("시간", pillars.hour, True),
        ("년지", pillars.year, False), ("월지", pillars.month, False),
        ("일지", pillars.day, False), ("시지", pillars.hour, False),
    ]:
        if is_stem:
            tg = calc_ten_god(day_stem, p.stem)
        else:
            tg = calc_ten_god_for_branch(day_stem, p.branch)
        cat = TEN_GOD_CATEGORIES.get(tg, "")
        results.append((label, cat))
    return results


def calc_wealth(pillars: FourPillars, strength: StrengthResult, pattern: PatternResult,
                interactions: list[InteractionEntry],
                daeun: list[DaeunEntry] | None = None) -> WealthResult:
    """재물그릇 9항목 채점."""
    day_stem = pillars.day.stem
    cats = _get_all_ten_god_cats(day_stem, pillars)
    items: list[WealthItem] = []

    # 천간에 재성이 있는 위치
    stem_cats = [(l, c) for l, c in cats if "간" in l]
    branch_cats = [(l, c) for l, c in cats if "지" in l]

    jaeseong_stem_count = sum(1 for _, c in stem_cats if c == "재성")
    jaeseong_branch_count = sum(1 for _, c in branch_cats if c == "재성")
    siksang_count = sum(1 for _, c in cats if c == "식상")
    gwanseong_count = sum(1 for _, c in cats if c == "관성")

    # A. 재성 투출 (천간에 재성 있으면, 0~25)
    a_score = min(25, jaeseong_stem_count * 13)
    items.append(WealthItem(
        category="A", label="재성 투출", score=a_score, max_score=25,
        description=f"천간 재성 {jaeseong_stem_count}개",
    ))

    # B. 재성 통근 (재성이 천간+지지 모두 있으면, 0~15)
    b_score = 0
    if jaeseong_stem_count > 0 and jaeseong_branch_count > 0:
        b_score = 15
    elif jaeseong_branch_count > 0:
        b_score = 8
    items.append(WealthItem(
        category="B", label="재성 통근", score=b_score, max_score=15,
        description="재성이 천간-지지 연결" if b_score >= 15 else "",
    ))

    # C. 재고 (진/술/축/미에 재성 지장간, 0~12)
    c_score = 0
    storage_branches = ["진", "술", "축", "미"]
    for p in [pillars.year, pillars.month, pillars.day, pillars.hour]:
        if p.branch in storage_branches:
            tg = calc_ten_god_for_branch(day_stem, p.branch)
            if TEN_GOD_CATEGORIES.get(tg, "") == "재성":
                c_score += 6
    c_score = min(12, c_score)
    items.append(WealthItem(
        category="C", label="재고(창고)", score=c_score, max_score=12,
        description="토 지지에 재성 저장",
    ))

    # D. 식상생재 (식상이 재성을 생하는 구조, 0~15)
    d_score = 0
    if siksang_count > 0 and (jaeseong_stem_count + jaeseong_branch_count) > 0:
        d_score = min(15, siksang_count * 8)
    items.append(WealthItem(
        category="D", label="식상생재", score=d_score, max_score=15,
        description=f"식상 {siksang_count}개 → 재성 생" if d_score > 0 else "",
    ))

    # E. 신강/신약 보정 (-15~+12)
    e_score = 0.0
    if strength.score >= 55:
        e_score = min(12.0, (strength.score - 50) * 0.5)
    elif strength.score <= 35:
        e_score = max(-15.0, (strength.score - 50) * 0.5)
    else:
        e_score = (strength.score - 50) * 0.3
    items.append(WealthItem(
        category="E", label="신강/신약 보정", score=round(e_score, 1), max_score=12,
        description=f"{strength.label} ({strength.score}점)",
    ))

    # F. 종격 보너스 (0~+25)
    f_score = 0
    if pattern.is_special:
        if pattern.name == "종재격":
            f_score = 25
        elif pattern.name in ("종아격",):
            f_score = 15
        else:
            f_score = 8
    items.append(WealthItem(
        category="F", label="종격 보너스", score=f_score, max_score=25,
        description=pattern.name if f_score > 0 else "",
    ))

    # G. 합거/충파 보정 (-12~+3)
    g_score = 0.0
    hap_count = sum(1 for i in interactions if i.type == "합")
    chung_count = sum(1 for i in interactions if i.type == "충")
    hyung_count = sum(1 for i in interactions if i.type == "형")
    g_score += hap_count * 1.5  # 합은 약간 +
    g_score -= chung_count * 4.0  # 충은 -
    g_score -= hyung_count * 3.0  # 형은 -
    g_score = max(-12.0, min(3.0, g_score))
    items.append(WealthItem(
        category="G", label="합충형 보정", score=round(g_score, 1), max_score=3,
        description=f"합{hap_count}/충{chung_count}/형{hyung_count}",
    ))

    # H. 관성 제어 (-3~+8)
    h_score = 0.0
    if gwanseong_count == 1:
        h_score = 5.0  # 관성 1개: 적절한 제어
    elif gwanseong_count == 2:
        h_score = 3.0
    elif gwanseong_count >= 3:
        h_score = -3.0  # 관다: 재성 누설
    items.append(WealthItem(
        category="H", label="관성 제어", score=round(h_score, 1), max_score=8,
        description=f"관성 {gwanseong_count}개",
    ))

    # I. 대운 재성기 (0~13)
    i_score = 0.0
    peak_periods: list[str] = []
    risk_periods: list[str] = []
    if daeun:
        wealth_elem = CONTROLLING.get(STEM_OHAENG.get(day_stem, ""), "")
        for d in daeun:
            is_wealth_period = (d.stem_ohaeng == wealth_elem or d.branch_ohaeng == wealth_elem)
            if is_wealth_period:
                i_score += 2.0
                peak_periods.append(f"{d.age_start}~{d.age_end}세 ({d.stem}{d.branch})")
            # 기신 대운은 위험기
            helping = STEM_OHAENG.get(day_stem, "")
            if d.stem_ohaeng == CONTROLLING.get(helping, "") or d.branch_ohaeng == CONTROLLING.get(helping, ""):
                risk_periods.append(f"{d.age_start}~{d.age_end}세 ({d.stem}{d.branch})")
    i_score = min(13.0, i_score)
    items.append(WealthItem(
        category="I", label="대운 재성기", score=round(i_score, 1), max_score=13,
        description=f"재물운 대운 {len(peak_periods)}개" if peak_periods else "",
    ))

    total = sum(item.score for item in items)
    total = max(0, min(100, total))

    grade = "F"
    grade_label = ""
    for threshold, g, gl in WEALTH_GRADES:
        if total >= threshold:
            grade = g
            grade_label = gl
            break

    return WealthResult(
        total_score=round(total, 1),
        grade=grade,
        grade_label=grade_label,
        items=items,
        peak_periods=peak_periods,
        risk_periods=risk_periods,
    )
