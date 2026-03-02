"""6축 운세 레이더 — 재물/직업/인기/건강/학업/대인 점수."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, TEN_GOD_CATEGORIES, RADAR_AXES,
    GENERATING, CONTROLLING,
)
from .models import (
    FourPillars, StrengthResult, YongshinResult,
    RadarResult, DaeunEntry, SeunEntry,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


def _base_scores(pillars: FourPillars, strength: StrengthResult) -> dict[str, float]:
    """원국 기반 6축 기본 점수."""
    day_stem = pillars.day.stem
    scores = {axis: 50.0 for axis in RADAR_AXES}

    # 원국 십신 카테고리 수집
    cats: list[str] = []
    for p in [pillars.year, pillars.month, pillars.hour]:
        tg = calc_ten_god(day_stem, p.stem)
        cats.append(TEN_GOD_CATEGORIES.get(tg, ""))
    for p in [pillars.year, pillars.month, pillars.day, pillars.hour]:
        tg = calc_ten_god_for_branch(day_stem, p.branch)
        cats.append(TEN_GOD_CATEGORIES.get(tg, ""))

    # 카테고리 → 축 가산
    for cat in cats:
        if cat == "재성":
            scores["재물운"] += 8
        elif cat == "관성":
            scores["직업운"] += 8
        elif cat == "식상":
            scores["인기운"] += 8
            scores["학업운"] += 3
        elif cat == "인성":
            scores["학업운"] += 8
            scores["건강운"] += 3
        elif cat == "비겁":
            scores["대인운"] += 5
            scores["건강운"] += 3

    # 신강/신약 보정
    if strength.label == "신강":
        scores["건강운"] += 8
        scores["직업운"] += 3
    elif strength.label == "신약":
        scores["건강운"] -= 5

    return scores


def calc_radar(pillars: FourPillars, strength: StrengthResult,
               yongshin: YongshinResult,
               seun: SeunEntry | None = None) -> RadarResult:
    """6축 레이더 점수 계산."""
    scores = _base_scores(pillars, strength)

    # 세운 보정
    if seun:
        day_stem = pillars.day.stem
        stem_tg = calc_ten_god(day_stem, seun.stem)
        branch_tg = calc_ten_god_for_branch(day_stem, seun.branch)

        for tg in [stem_tg, branch_tg]:
            cat = TEN_GOD_CATEGORIES.get(tg, "")
            if cat == "재성":
                scores["재물운"] += 10
            elif cat == "관성":
                scores["직업운"] += 10
            elif cat == "식상":
                scores["인기운"] += 10
            elif cat == "인성":
                scores["학업운"] += 10
            elif cat == "비겁":
                scores["대인운"] += 5

        # 세운 오행이 용신이면 전체 +5
        if seun.stem_ohaeng in yongshin.favorable_elements:
            for axis in RADAR_AXES:
                scores[axis] += 5
        if seun.branch_ohaeng in yongshin.favorable_elements:
            for axis in RADAR_AXES:
                scores[axis] += 3

        # 기신이면 전체 -3
        if seun.stem_ohaeng in yongshin.unfavorable_elements:
            for axis in RADAR_AXES:
                scores[axis] -= 3

    # 0~100 클램프
    for axis in RADAR_AXES:
        scores[axis] = round(max(0, min(100, scores[axis])), 1)

    strongest = max(scores, key=scores.get)  # type: ignore
    weakest = min(scores, key=scores.get)  # type: ignore

    return RadarResult(
        axes=scores,
        strongest=strongest,
        weakest=weakest,
    )
