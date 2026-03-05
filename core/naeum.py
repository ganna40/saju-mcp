"""납음오행(納音五行) — 60갑자별 소리오행 판별."""
from __future__ import annotations

from .constants import NAEUM_TABLE
from .models import FourPillars


def calc_naeum(stem: str, branch: str) -> dict:
    """천간+지지 조합의 납음오행 반환.

    Returns:
        {"name": "해중금", "hanja": "海中金", "element": "금", "description": "..."}
    """
    entry = NAEUM_TABLE.get((stem, branch))
    if not entry:
        return {"name": "", "hanja": "", "element": "", "description": ""}
    return {
        "name": entry[0],
        "hanja": entry[1],
        "element": entry[2],
        "description": entry[3],
    }


def calc_all_naeum(pillars: FourPillars) -> dict:
    """사주 4주 전체의 납음오행 반환.

    Returns:
        {
            "year": {"name": "해중금", "hanja": "海中金", ...},
            "month": {...},
            "day": {...},
            "hour": {...},
            "day_naeum_summary": "일주 납음: 해중금(海中金) — 바다 속 금...",
        }
    """
    result = {}
    for key, pillar in [
        ("year", pillars.year),
        ("month", pillars.month),
        ("day", pillars.day),
        ("hour", pillars.hour),
    ]:
        result[key] = calc_naeum(pillar.stem, pillar.branch)

    # 일주 납음 요약 (가장 중요)
    day_n = result["day"]
    if day_n["name"]:
        result["day_naeum_summary"] = (
            f"일주 납음: {day_n['name']}({day_n['hanja']}) — {day_n['description']}"
        )
    else:
        result["day_naeum_summary"] = ""

    return result
