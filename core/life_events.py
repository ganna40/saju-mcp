"""인생이벤트 타임라인 — 대운 기반 주요 이벤트 예측."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, GENERATING, CONTROLLING,
    TEN_GOD_CATEGORIES,
)
from .models import (
    FourPillars, DaeunEntry, StrengthResult, YongshinResult, LifeEvent,
)
from .ten_gods import calc_ten_god


def _daeun_ten_god(day_stem: str, daeun: DaeunEntry) -> tuple[str, str]:
    """대운의 천간/지지 십신 반환."""
    stem_tg = calc_ten_god(day_stem, daeun.stem)
    from .ten_gods import calc_ten_god_for_branch
    branch_tg = calc_ten_god_for_branch(day_stem, daeun.branch)
    return stem_tg, branch_tg


def _favorability(day_elem: str, daeun_elem: str, yongshin: YongshinResult) -> str:
    """대운 오행이 용신/희신이면 길, 기신/구신이면 흉."""
    if daeun_elem in yongshin.favorable_elements:
        return "길"
    if daeun_elem in yongshin.unfavorable_elements:
        return "흉"
    return "보통"


def _events_for_period(stem_tg: str, branch_tg: str, age_start: int) -> list[str]:
    """십신 조합 기반 이벤트 추정."""
    events = []
    stem_cat = TEN_GOD_CATEGORIES.get(stem_tg, "")
    branch_cat = TEN_GOD_CATEGORIES.get(branch_tg, "")
    cats = {stem_cat, branch_cat}

    if "재성" in cats:
        events.append("재물운 상승 / 재테크 기회")
        if age_start >= 25:
            events.append("사업 확장 또는 투자 기회")

    if "관성" in cats:
        events.append("직장/승진 관련 변화")
        if "재성" in cats:
            events.append("직장 + 재물 동시 상승 가능")

    if "인성" in cats:
        events.append("학업/자격증/공부 관련 성과")
        if age_start < 30:
            events.append("학업 성취 / 시험 합격 가능")

    if "식상" in cats:
        events.append("표현력/창작 활동 활발")
        if age_start >= 25:
            events.append("자녀 관련 이벤트 가능")

    if "비겁" in cats:
        events.append("경쟁 심화 / 독립 욕구")
        if age_start >= 30:
            events.append("동업/협력 또는 경쟁 관계")

    if not events:
        events.append("큰 변화 없이 안정적 시기")

    # 연령대별 추가
    if age_start <= 15:
        events.append("성장기 — 가정환경/학업이 주요 테마")
    elif age_start <= 25:
        events.append("청년기 — 진로/학업 결정의 시기")
    elif age_start <= 40:
        if "재성" in cats or "관성" in cats:
            events.append("중년 초반 — 커리어 전성기 가능")
    elif age_start <= 55:
        events.append("중년 — 건강과 재물 관리가 중요")
    else:
        events.append("장년기 — 안정과 건강에 집중")

    return events


def calc_life_events(pillars: FourPillars, daeun: list[DaeunEntry],
                     strength: StrengthResult, yongshin: YongshinResult) -> list[LifeEvent]:
    """대운별 인생이벤트 타임라인 생성."""
    day_stem = pillars.day.stem
    day_elem = STEM_OHAENG[day_stem]
    results: list[LifeEvent] = []

    for d in daeun:
        stem_tg, branch_tg = _daeun_ten_god(day_stem, d)
        events = _events_for_period(stem_tg, branch_tg, d.age_start)
        fav = _favorability(day_elem, d.stem_ohaeng, yongshin)

        results.append(LifeEvent(
            age_range=f"{d.age_start}~{d.age_end}세",
            period=f"{d.stem}{d.branch}",
            events=events,
            key_element=f"{d.stem_ohaeng}/{d.branch_ohaeng}",
            favorability=fav,
        ))

    return results
