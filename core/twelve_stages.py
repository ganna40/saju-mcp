"""십이운성(十二運星) 계산 — 일간 기준 각 지지의 에너지 단계."""
from __future__ import annotations

from .constants import (
    EARTHLY_BRANCHES, TWELVE_STAGES, TWELVE_STAGE_START,
    TWELVE_STAGE_DESC, STEM_YINYANG,
)
from .models import FourPillars


def _get_stage(day_stem: str, branch: str) -> str:
    """일간 기준 특정 지지의 십이운성 단계 반환."""
    start_branch = TWELVE_STAGE_START.get(day_stem, "")
    if not start_branch:
        return ""
    start_idx = EARTHLY_BRANCHES.index(start_branch)
    branch_idx = EARTHLY_BRANCHES.index(branch)

    yinyang = STEM_YINYANG.get(day_stem, "양")
    if yinyang == "양":
        offset = (branch_idx - start_idx) % 12
    else:
        offset = (start_idx - branch_idx) % 12

    return TWELVE_STAGES[offset]


def calc_twelve_stages(pillars: FourPillars) -> list[dict]:
    """사주 4주 각 지지의 십이운성 계산.

    Returns:
        [{"position": "년지", "branch": "인", "stage": "건록",
          "label": "건록(建祿)", "energy": "왕성", "meaning": "..."}]
    """
    day_stem = pillars.day.stem
    results = []

    for pos_name, pillar in [
        ("년지", pillars.year),
        ("월지", pillars.month),
        ("일지", pillars.day),
        ("시지", pillars.hour),
    ]:
        stage = _get_stage(day_stem, pillar.branch)
        desc = TWELVE_STAGE_DESC.get(stage, {})
        results.append({
            "position": pos_name,
            "branch": pillar.branch,
            "stage": stage,
            "label": desc.get("label", stage),
            "energy": desc.get("energy", ""),
            "meaning": desc.get("meaning", ""),
        })

    return results
