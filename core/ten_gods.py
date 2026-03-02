"""십신(十神) 계산 — 일간 대비 각 간지의 십신 판별."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, STEM_YINYANG,
    BRANCH_OHAENG, BRANCH_YINYANG,
    GENERATING, CONTROLLING, CONTROLLED_BY,
    HIDDEN_STEMS, TEN_GOD_CATEGORIES,
)
from .models import TenGodEntry, FourPillars


def _get_relation(day_elem: str, target_elem: str) -> str:
    """일간 오행 vs 대상 오행 → 관계 문자열."""
    if day_elem == target_elem:
        return "same"
    if GENERATING.get(day_elem) == target_elem:
        return "generating"  # 내가 생하는 → 식상
    if CONTROLLING.get(day_elem) == target_elem:
        return "wealth"  # 내가 극하는 → 재성
    if CONTROLLING.get(target_elem) == day_elem:
        return "power"  # 나를 극하는 → 관성
    if GENERATING.get(target_elem) == day_elem:
        return "seal"  # 나를 생하는 → 인성
    return "same"


def calc_ten_god(day_stem: str, target_stem: str) -> str:
    """일간 vs 대상 천간 → 십신 이름 반환."""
    day_elem = STEM_OHAENG[day_stem]
    target_elem = STEM_OHAENG[target_stem]
    day_yy = STEM_YINYANG[day_stem]
    target_yy = STEM_YINYANG[target_stem]

    relation = _get_relation(day_elem, target_elem)
    same_yinyang = (day_yy == target_yy)

    from .constants import TEN_GOD_TABLE
    return TEN_GOD_TABLE.get((relation, same_yinyang), "비견")


def calc_ten_god_for_branch(day_stem: str, branch: str) -> str:
    """일간 vs 지지 → 지지의 정기(가장 큰 비중) 기준 십신."""
    hidden = HIDDEN_STEMS.get(branch, [])
    if not hidden:
        return ""
    main_stem = hidden[-1][0]  # 정기 = 마지막 (가장 큰 비중)
    return calc_ten_god(day_stem, main_stem)


def get_all_ten_gods(pillars: FourPillars) -> list[TenGodEntry]:
    """사주 4주 전체의 십신 리스트 반환."""
    day_stem = pillars.day.stem
    results = []

    positions = [
        ("년간", pillars.year.stem, True),
        ("년지", pillars.year.branch, False),
        ("월간", pillars.month.stem, True),
        ("월지", pillars.month.branch, False),
        ("일지", pillars.day.branch, False),
        ("시간", pillars.hour.stem, True),
        ("시지", pillars.hour.branch, False),
    ]

    for pos_name, char, is_stem in positions:
        if is_stem:
            tg = calc_ten_god(day_stem, char)
        else:
            tg = calc_ten_god_for_branch(day_stem, char)

        results.append(TenGodEntry(
            position=pos_name,
            char=char,
            ten_god=tg,
            category=TEN_GOD_CATEGORIES.get(tg, ""),
        ))

    return results
