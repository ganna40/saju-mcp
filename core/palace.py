"""궁위(宮位) 분석 — 년월일시 4궁의 십신 배치 해석."""
from __future__ import annotations

from .constants import (
    PALACE_INFO, TEN_GOD_CATEGORIES, STEM_HANJA, BRANCH_HANJA,
)
from .models import FourPillars
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


def analyze_palaces(pillars: FourPillars) -> list[dict]:
    """4궁 분석.

    Returns:
        [{
            "palace": "년주",
            "palace_name": "조상궁/사회궁",
            "age_range": "초년(1~15세)",
            "represents": "조상, 가문, 어린 시절 환경, 사회적 인식",
            "stem": "경", "branch": "오",
            "stem_ten_god": "편관", "branch_ten_god": "상관",
            "stem_category": "관성", "branch_category": "식상",
            "interpretation": "...",
        }]
    """
    day_stem = pillars.day.stem
    results = []

    pillar_map = [
        ("년주", pillars.year),
        ("월주", pillars.month),
        ("일주", pillars.day),
        ("시주", pillars.hour),
    ]

    for palace_name, pillar in pillar_map:
        info = PALACE_INFO.get(palace_name, {})

        # 일간(본인)은 십신 계산 안 함
        if palace_name == "일주":
            stem_tg = "본인(일간)"
            stem_cat = ""
        else:
            stem_tg = calc_ten_god(day_stem, pillar.stem)
            stem_cat = TEN_GOD_CATEGORIES.get(stem_tg, "")

        branch_tg = calc_ten_god_for_branch(day_stem, pillar.branch)
        branch_cat = TEN_GOD_CATEGORIES.get(branch_tg, "")

        # 궁위 해석 생성
        interpretation = _build_palace_interp(
            palace_name, info, stem_tg, branch_tg, stem_cat, branch_cat
        )

        results.append({
            "palace": palace_name,
            "palace_name": info.get("name", ""),
            "age_range": info.get("age_range", ""),
            "represents": info.get("represents", ""),
            "stem": pillar.stem,
            "branch": pillar.branch,
            "stem_hanja": STEM_HANJA.get(pillar.stem, ""),
            "branch_hanja": BRANCH_HANJA.get(pillar.branch, ""),
            "stem_ten_god": stem_tg,
            "branch_ten_god": branch_tg,
            "stem_category": stem_cat,
            "branch_category": branch_cat,
            "interpretation": interpretation,
        })

    return results


def _build_palace_interp(
    palace_name: str, info: dict,
    stem_tg: str, branch_tg: str,
    stem_cat: str, branch_cat: str,
) -> str:
    """궁위별 해석 텍스트 생성."""
    parts = []
    ten_god_meanings = info.get("ten_god_meanings", {})

    if palace_name == "일주":
        # 일주는 특별 처리: 일지(배우자궁) 중심
        meaning = ten_god_meanings.get(branch_cat, "")
        parts.append(f"일지(배우자 자리)에 {branch_tg}이(가) 있음.")
        if meaning:
            parts.append(meaning)
        return " ".join(parts)

    # 천간 해석
    if stem_cat and stem_cat in ten_god_meanings:
        parts.append(f"{palace_name} 천간에 {stem_tg}({stem_cat})이 있음.")
        parts.append(ten_god_meanings[stem_cat])

    # 지지 해석
    if branch_cat and branch_cat in ten_god_meanings:
        parts.append(f"{palace_name} 지지에 {branch_tg}({branch_cat})이 있음.")
        if branch_cat != stem_cat:  # 중복 방지
            parts.append(ten_god_meanings[branch_cat])

    return " ".join(parts) if parts else f"{palace_name}의 십신 배치가 특이한 양상을 보임."
