"""만세력 — lunar_python 래퍼.

Solar → Lunar → EightChar(사주) 변환, 대운/세운 계산.
"""
from __future__ import annotations

from lunar_python import Solar, Lunar

from .constants import (
    CN_STEM_TO_KR, CN_BRANCH_TO_KR,
    STEM_OHAENG, STEM_YINYANG, STEM_HANJA,
    BRANCH_OHAENG, BRANCH_YINYANG, BRANCH_HANJA,
    HIDDEN_STEMS, EARTHLY_BRANCHES, HEAVENLY_STEMS,
)
from .models import Pillar, FourPillars, DaeunEntry, SeunEntry


def _cn_to_kr_stem(cn: str) -> str:
    """중문 천간 한 글자 → 한글."""
    return CN_STEM_TO_KR.get(cn, cn)


def _cn_to_kr_branch(cn: str) -> str:
    """중문 지지 한 글자 → 한글."""
    return CN_BRANCH_TO_KR.get(cn, cn)


def _parse_ganzhi(gz: str) -> tuple[str, str]:
    """중문 간지 2글자(예: '甲子') → (한글천간, 한글지지)."""
    if len(gz) >= 2:
        return _cn_to_kr_stem(gz[0]), _cn_to_kr_branch(gz[1])
    return gz, ""


def _make_pillar(stem_kr: str, branch_kr: str) -> Pillar:
    hidden = []
    if branch_kr in HIDDEN_STEMS:
        for s, w in HIDDEN_STEMS[branch_kr]:
            hidden.append({"stem": s, "ohaeng": STEM_OHAENG.get(s, ""), "weight": w})
    return Pillar(
        stem=stem_kr,
        branch=branch_kr,
        stem_hanja=STEM_HANJA.get(stem_kr, ""),
        branch_hanja=BRANCH_HANJA.get(branch_kr, ""),
        stem_ohaeng=STEM_OHAENG.get(stem_kr, ""),
        branch_ohaeng=BRANCH_OHAENG.get(branch_kr, ""),
        hidden_stems=hidden,
    )


def get_four_pillars(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> FourPillars:
    """양력 생년월일시 → 사주 4주 반환."""
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    y_s, y_b = _parse_ganzhi(ec.getYear())
    m_s, m_b = _parse_ganzhi(ec.getMonth())
    d_s, d_b = _parse_ganzhi(ec.getDay())
    h_s, h_b = _parse_ganzhi(ec.getTime())

    return FourPillars(
        year=_make_pillar(y_s, y_b),
        month=_make_pillar(m_s, m_b),
        day=_make_pillar(d_s, d_b),
        hour=_make_pillar(h_s, h_b),
    )


def get_daeun(year: int, month: int, day: int, hour: int = 12, minute: int = 0,
              gender: str = "남") -> list[DaeunEntry]:
    """대운 리스트 반환 (10개 정도)."""
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    gender_code = 1 if gender == "남" else 0
    yun = ec.getYun(gender_code)
    da_yun_list = yun.getDaYun()

    result = []
    for dy in da_yun_list:
        gz = dy.getGanZhi()
        if not gz or len(gz) < 2:
            continue
        s, b = _parse_ganzhi(gz)
        start_age = dy.getStartAge()
        end_age = dy.getEndAge()
        result.append(DaeunEntry(
            age_start=start_age,
            age_end=end_age,
            stem=s,
            branch=b,
            stem_ohaeng=STEM_OHAENG.get(s, ""),
            branch_ohaeng=BRANCH_OHAENG.get(b, ""),
        ))
    return result


def get_seun(year: int, month: int, day: int, hour: int = 12, minute: int = 0,
             gender: str = "남", target_year: int | None = None) -> list[SeunEntry]:
    """세운 리스트 반환. target_year가 주어지면 해당 연도만."""
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    gender_code = 1 if gender == "남" else 0
    yun = ec.getYun(gender_code)
    da_yun_list = yun.getDaYun()

    result = []
    for dy in da_yun_list:
        liu_nian_list = dy.getLiuNian()
        for ln in liu_nian_list:
            ln_year = ln.getYear()
            if target_year is not None and ln_year != target_year:
                continue
            gz = ln.getGanZhi()
            if not gz or len(gz) < 2:
                continue
            s, b = _parse_ganzhi(gz)
            age = ln_year - year + 1  # 한국 나이
            result.append(SeunEntry(
                year=ln_year,
                age=age,
                stem=s,
                branch=b,
                stem_ohaeng=STEM_OHAENG.get(s, ""),
                branch_ohaeng=BRANCH_OHAENG.get(b, ""),
            ))
            if target_year is not None:
                return result
    return result


def get_birth_year_branch(year: int) -> str:
    """생년의 지지 반환 (연지)."""
    idx = (year - 4) % 12
    return EARTHLY_BRANCHES[idx]
