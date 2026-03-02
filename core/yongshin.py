"""용신(用神) / 희신 / 기신 / 구신 판별."""
from __future__ import annotations

from .constants import (
    OHAENG_LIST, GENERATING, CONTROLLING, CONTROLLED_BY,
    STEM_OHAENG,
)
from .models import StrengthResult, PatternResult, YongshinResult


def _find_generating_me(elem: str) -> str:
    """나를 생하는 오행."""
    for k, v in GENERATING.items():
        if v == elem:
            return k
    return ""


def determine_yongshin(strength: StrengthResult, pattern: PatternResult) -> YongshinResult:
    """용신 판별."""
    day_elem = strength.day_stem_ohaeng
    score = strength.score

    # 특수격 (종격)의 경우
    if pattern.is_special:
        return _special_yongshin(pattern.name, day_elem, strength)

    # ── 보통격 ──
    if score >= 55:
        # 신강 → 설기/극기 필요 → 식상/재성/관성이 용신
        yongshin = GENERATING.get(day_elem, "")  # 식상 (내가 생하는 오행)
        reason = f"신강({score}점)이므로 기운을 빼주는 {yongshin}(식상)이 용신"
        heeshin = CONTROLLING.get(day_elem, "")  # 재성
        gishin = day_elem  # 비겁
        gushin = _find_generating_me(day_elem)  # 인성
    elif score <= 45:
        # 신약 → 부조 필요 → 인성/비겁이 용신
        yongshin = _find_generating_me(day_elem)  # 인성
        reason = f"신약({score}점)이므로 기운을 보충하는 {yongshin}(인성)이 용신"
        heeshin = day_elem  # 비겁
        gishin = CONTROLLING.get(day_elem, "")  # 재성
        gushin = GENERATING.get(day_elem, "")  # 식상
    else:
        # 중화 → 균형 유지. 약간 부족한 쪽 보강
        if score >= 50:
            yongshin = GENERATING.get(day_elem, "")
            reason = f"중화(약간 강, {score}점)이므로 약간의 설기가 필요"
        else:
            yongshin = _find_generating_me(day_elem)
            reason = f"중화(약간 약, {score}점)이므로 약간의 보조가 필요"
        heeshin = ""
        gishin = ""
        gushin = ""

    favorable = [yongshin]
    if heeshin:
        favorable.append(heeshin)
    unfavorable = [e for e in [gishin, gushin] if e]

    return YongshinResult(
        yongshin=yongshin,
        yongshin_reason=reason,
        heeshin=heeshin,
        gishin=gishin,
        gushin=gushin,
        favorable_elements=favorable,
        unfavorable_elements=unfavorable,
    )


def _special_yongshin(pattern_name: str, day_elem: str, strength: StrengthResult) -> YongshinResult:
    """종격의 용신."""
    if pattern_name == "종강격":
        yongshin = day_elem
        reason = "종강격이므로 비겁(같은 오행)이 용신"
        heeshin = _find_generating_me(day_elem)
    elif pattern_name == "종아격":
        yongshin = GENERATING.get(day_elem, "")
        reason = "종아격이므로 식상이 용신"
        heeshin = CONTROLLING.get(day_elem, "")
    elif pattern_name == "종재격":
        yongshin = CONTROLLING.get(day_elem, "")
        reason = "종재격이므로 재성이 용신"
        heeshin = GENERATING.get(day_elem, "")
    elif pattern_name == "종관격":
        yongshin = CONTROLLED_BY.get(day_elem, "")
        reason = "종관격이므로 관성이 용신"
        heeshin = CONTROLLING.get(day_elem, "")
    else:
        yongshin = day_elem
        reason = "특수격"
        heeshin = ""

    return YongshinResult(
        yongshin=yongshin,
        yongshin_reason=reason,
        heeshin=heeshin,
        favorable_elements=[yongshin, heeshin] if heeshin else [yongshin],
        unfavorable_elements=[],
    )
