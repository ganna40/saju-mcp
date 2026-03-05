"""조후용신(調候用神) 판별 — 궁통보감 기반 계절 조절."""
from __future__ import annotations

from .constants import JOHU_TABLE, STEM_OHAENG
from .models import FourPillars


def calc_johu(pillars: FourPillars) -> dict:
    """일간 + 월지 기준 조후용신 판별.

    Returns:
        {
            "needed_element": "화",
            "specific_stems": ["정"],
            "reason": "가을 금이 강해 화로 제어",
            "metaphor": "서릿발 같은 금기운, 따뜻한 불빛으로 나무를 지키는 형국",
            "season_context": "유월(가을) 생으로 금기운이 왕성한 시기",
            "has_johu": True,
        }
    """
    day_stem = pillars.day.stem
    month_branch = pillars.month.branch
    day_elem = STEM_OHAENG.get(day_stem, "")

    entry = JOHU_TABLE.get((day_stem, month_branch))
    if not entry:
        return {
            "needed_element": "",
            "specific_stems": [],
            "reason": "조후 테이블에 해당 없음",
            "metaphor": "",
            "season_context": "",
            "has_johu": False,
        }

    season_map = {
        "인": "인월(초봄)", "묘": "묘월(한봄)", "진": "진월(늦봄)",
        "사": "사월(초여름)", "오": "오월(한여름)", "미": "미월(늦여름)",
        "신": "신월(초가을)", "유": "유월(한가을)", "술": "술월(늦가을)",
        "해": "해월(초겨울)", "자": "자월(한겨울)", "축": "축월(늦겨울)",
    }
    season_name = season_map.get(month_branch, month_branch)

    return {
        "needed_element": entry["needed"],
        "specific_stems": entry["elements"],
        "reason": entry["reason"],
        "metaphor": entry["metaphor"],
        "season_context": f"{season_name} 생으로 {_season_element_desc(month_branch)}",
        "has_johu": True,
    }


def _season_element_desc(month_branch: str) -> str:
    """월지별 계절 기운 설명."""
    desc = {
        "인": "목(木)기운이 솟아오르는 시기",
        "묘": "목(木)기운이 가장 왕성한 시기",
        "진": "토(土)기운으로 전환되는 과도기",
        "사": "화(火)기운이 피어오르는 시기",
        "오": "화(火)기운이 가장 극성인 시기",
        "미": "토(土)기운으로 전환되며 아직 더운 시기",
        "신": "금(金)기운이 서늘하게 시작하는 시기",
        "유": "금(金)기운이 가장 날카로운 시기",
        "술": "토(土)기운으로 전환되며 건조한 시기",
        "해": "수(水)기운이 차갑게 밀려오는 시기",
        "자": "수(水)기운이 가장 깊고 차가운 시기",
        "축": "토(土)기운 아래 수(水)가 얼어붙는 시기",
    }
    return desc.get(month_branch, "")
