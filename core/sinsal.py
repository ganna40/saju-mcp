"""신살(神殺) 12종 판별."""
from __future__ import annotations

from .constants import (
    YEOKMA, DOHWA, HWAGAE, GWIMUN, BAEKHO,
    GOEGANG_ILJU, YANGIN, CHEONUL, MUNCHANG,
    HAKDANG, JANGSEONG, GEOPSAL, SINSAL_DESCRIPTIONS,
)
from .models import FourPillars, SinsalEntry, DaeunEntry


def _all_branches(pillars: FourPillars) -> dict[str, list[str]]:
    """위치별 지지 매핑."""
    return {
        "년지": [pillars.year.branch],
        "월지": [pillars.month.branch],
        "일지": [pillars.day.branch],
        "시지": [pillars.hour.branch],
    }


def _check_lookup(lookup: dict, key: str, branches: dict[str, list[str]]) -> list[str]:
    """lookup[key]에 해당하는 지지가 있는 위치 반환."""
    target = lookup.get(key)
    if not target:
        return []
    positions = []
    for pos, bs in branches.items():
        if target in bs:
            positions.append(pos)
    return positions


def detect_sinsal(pillars: FourPillars, daeun: list[DaeunEntry] | None = None) -> list[SinsalEntry]:
    """원국의 신살 12종 판별."""
    day_stem = pillars.day.stem
    day_branch = pillars.day.branch
    year_branch = pillars.year.branch
    branches = _all_branches(pillars)
    all_branch_list = [pillars.year.branch, pillars.month.branch,
                       pillars.day.branch, pillars.hour.branch]
    results: list[SinsalEntry] = []

    # 1. 역마살 (일지 기준)
    pos = _check_lookup(YEOKMA, day_branch, branches)
    # 연지 기준도 체크
    pos2 = _check_lookup(YEOKMA, year_branch, branches)
    all_pos = list(set(pos + pos2))
    if all_pos:
        results.append(_entry("역마살", all_pos, daeun, YEOKMA, day_branch))

    # 2. 도화살 (일지/연지 기준)
    pos = _check_lookup(DOHWA, day_branch, branches)
    pos2 = _check_lookup(DOHWA, year_branch, branches)
    all_pos = list(set(pos + pos2))
    if all_pos:
        results.append(_entry("도화살", all_pos, daeun, DOHWA, day_branch))

    # 3. 화개살
    pos = _check_lookup(HWAGAE, day_branch, branches)
    pos2 = _check_lookup(HWAGAE, year_branch, branches)
    all_pos = list(set(pos + pos2))
    if all_pos:
        results.append(_entry("화개살", all_pos, daeun, HWAGAE, day_branch))

    # 4. 귀문관살
    pos = _check_lookup(GWIMUN, day_branch, branches)
    if pos:
        results.append(_entry("귀문관살", pos, daeun, GWIMUN, day_branch))

    # 5. 백호대살
    pos = _check_lookup(BAEKHO, day_branch, branches)
    if pos:
        results.append(_entry("백호대살", pos, daeun, BAEKHO, day_branch))

    # 6. 괴강살 (일주 기준)
    if (day_stem, day_branch) in GOEGANG_ILJU:
        results.append(SinsalEntry(
            name="괴강살",
            description=SINSAL_DESCRIPTIONS.get("괴강살", ""),
            positions=["일주"],
        ))

    # 7. 양인살 (일간 기준)
    yangin_branch = YANGIN.get(day_stem)
    if yangin_branch and yangin_branch in all_branch_list:
        pos_list = [p for p, bs in branches.items() if yangin_branch in bs]
        results.append(SinsalEntry(
            name="양인살",
            description=SINSAL_DESCRIPTIONS.get("양인살", ""),
            positions=pos_list,
        ))

    # 8. 천을귀인 (일간 기준)
    cheonul_branches = CHEONUL.get(day_stem, [])
    found_pos = []
    for cb in cheonul_branches:
        for p, bs in branches.items():
            if cb in bs:
                found_pos.append(p)
    if found_pos:
        results.append(SinsalEntry(
            name="천을귀인",
            description=SINSAL_DESCRIPTIONS.get("천을귀인", ""),
            positions=list(set(found_pos)),
        ))

    # 9. 문창귀인
    mc_branch = MUNCHANG.get(day_stem)
    if mc_branch and mc_branch in all_branch_list:
        pos_list = [p for p, bs in branches.items() if mc_branch in bs]
        results.append(SinsalEntry(
            name="문창귀인",
            description=SINSAL_DESCRIPTIONS.get("문창귀인", ""),
            positions=pos_list,
        ))

    # 10. 학당귀인
    hd_branch = HAKDANG.get(day_stem)
    if hd_branch and hd_branch in all_branch_list:
        pos_list = [p for p, bs in branches.items() if hd_branch in bs]
        results.append(SinsalEntry(
            name="학당귀인",
            description=SINSAL_DESCRIPTIONS.get("학당귀인", ""),
            positions=pos_list,
        ))

    # 11. 장성살
    pos = _check_lookup(JANGSEONG, day_branch, branches)
    pos2 = _check_lookup(JANGSEONG, year_branch, branches)
    all_pos = list(set(pos + pos2))
    if all_pos:
        results.append(_entry("장성살", all_pos, daeun, JANGSEONG, day_branch))

    # 12. 겁살
    pos = _check_lookup(GEOPSAL, day_branch, branches)
    pos2 = _check_lookup(GEOPSAL, year_branch, branches)
    all_pos = list(set(pos + pos2))
    if all_pos:
        results.append(_entry("겁살", all_pos, daeun, GEOPSAL, day_branch))

    # 대운 발동시기 계산
    if daeun:
        for entry in results:
            entry.activation_periods = _find_activation_periods(entry.name, day_stem, day_branch, year_branch, daeun)

    return results


def _entry(name: str, positions: list[str], daeun: list[DaeunEntry] | None,
           lookup: dict, ref_branch: str) -> SinsalEntry:
    return SinsalEntry(
        name=name,
        description=SINSAL_DESCRIPTIONS.get(name, ""),
        positions=positions,
    )


def _find_activation_periods(sinsal_name: str, day_stem: str, day_branch: str,
                             year_branch: str, daeun: list[DaeunEntry]) -> list[str]:
    """대운에서 해당 신살이 발동하는 시기 찾기."""
    lookup_map = {
        "역마살": YEOKMA, "도화살": DOHWA, "화개살": HWAGAE,
        "귀문관살": GWIMUN, "백호대살": BAEKHO,
        "장성살": JANGSEONG, "겁살": GEOPSAL,
    }
    lookup = lookup_map.get(sinsal_name)
    if not lookup:
        return []

    target_from_day = lookup.get(day_branch)
    target_from_year = lookup.get(year_branch)
    targets = set()
    if target_from_day:
        targets.add(target_from_day)
    if target_from_year:
        targets.add(target_from_year)

    periods = []
    for d in daeun:
        if d.branch in targets:
            periods.append(f"{d.age_start}~{d.age_end}세 ({d.stem}{d.branch}운)")
    return periods
