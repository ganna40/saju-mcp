"""격국(格局) 판별 — 16종 규칙 기반."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, HIDDEN_STEMS,
    PATTERN_TRAITS, CAREER_BY_PATTERN, GEONROK, YANGIN,
    TEN_GOD_CATEGORIES,
)
from .models import FourPillars, PatternResult, StrengthResult
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


def _month_branch_main_god(day_stem: str, month_branch: str) -> str:
    """월지 정기의 십신 반환."""
    return calc_ten_god_for_branch(day_stem, month_branch)


def _count_category(day_stem: str, pillars: FourPillars) -> dict[str, int]:
    """십신 카테고리별 개수."""
    counts: dict[str, int] = {"비겁": 0, "식상": 0, "재성": 0, "관성": 0, "인성": 0}

    for p in [pillars.year, pillars.month, pillars.hour]:
        tg = calc_ten_god(day_stem, p.stem)
        cat = TEN_GOD_CATEGORIES.get(tg, "")
        if cat:
            counts[cat] += 1

    for p in [pillars.year, pillars.month, pillars.day, pillars.hour]:
        tg = calc_ten_god_for_branch(day_stem, p.branch)
        cat = TEN_GOD_CATEGORIES.get(tg, "")
        if cat:
            counts[cat] += 1

    return counts


def determine_pattern(pillars: FourPillars, strength: StrengthResult) -> PatternResult:
    """격국 판별."""
    day_stem = pillars.day.stem

    # ── 1. 특수격 (종격) 판별 ──
    cat_counts = _count_category(day_stem, pillars)
    total = sum(cat_counts.values())

    # 종강격: 비겁이 전체의 60% 이상이고 신강 70 이상
    if total > 0 and cat_counts["비겁"] / total >= 0.6 and strength.score >= 70:
        return _make_result("종강격", is_special=True)

    # 종아격: 식상이 전체의 50% 이상이고 신약
    if total > 0 and cat_counts["식상"] / total >= 0.5 and strength.score < 40:
        return _make_result("종아격", is_special=True)

    # 종재격: 재성이 전체의 50% 이상이고 신약
    if total > 0 and cat_counts["재성"] / total >= 0.5 and strength.score < 40:
        return _make_result("종재격", is_special=True)

    # 종관격: 관성이 전체의 50% 이상이고 신약
    if total > 0 and cat_counts["관성"] / total >= 0.5 and strength.score < 40:
        return _make_result("종관격", is_special=True)

    # ── 2. 건록격/양인격 ──
    month_branch = pillars.month.branch
    if GEONROK.get(day_stem) == month_branch:
        return _make_result("건록격")

    if YANGIN.get(day_stem) == month_branch:
        return _make_result("양인격")

    # ── 3. 보통격 — 월지 정기 기준 ──
    month_god = _month_branch_main_god(day_stem, month_branch)
    pattern_name = f"{month_god}격"

    if pattern_name in PATTERN_TRAITS:
        return _make_result(pattern_name)

    # fallback: 가장 많은 카테고리 기반
    if total > 0:
        dominant = max(cat_counts, key=cat_counts.get)  # type: ignore
        cat_to_pattern = {
            "비겁": "비견격", "식상": "식신격", "재성": "편재격",
            "관성": "정관격", "인성": "정인격",
        }
        return _make_result(cat_to_pattern.get(dominant, "비견격"))

    return _make_result("비견격")


def _make_result(name: str, is_special: bool = False) -> PatternResult:
    return PatternResult(
        name=name,
        description=PATTERN_TRAITS.get(name, ""),
        traits=PATTERN_TRAITS.get(name, ""),
        careers=CAREER_BY_PATTERN.get(name, []),
        is_special=is_special,
    )
