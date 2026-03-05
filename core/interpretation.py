"""해석 힌트 엔진 — 전문가 수준의 메타포와 맥락 해석 생성."""
from __future__ import annotations

from .constants import (
    DAY_STEM_METAPHORS, STEM_OHAENG, STEM_HANJA,
    BRANCH_HANJA, OHAENG_LIST, GENERATING, CONTROLLING,
    INTERACTION_PALACE_MEANING,
)
from .models import (
    FourPillars, StrengthResult, PatternResult,
    YongshinResult, InteractionEntry,
)


def generate_interpretation_hints(
    pillars: FourPillars,
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    interactions: list[InteractionEntry],
    twelve_stages: list[dict],
    gongmang: dict,
    johu: dict,
    naeum: dict,
    palace: list[dict],
) -> dict:
    """전문가 수준의 종합 해석 힌트 생성.

    Returns:
        {
            "day_stem_analysis": "...",  # 일간 심층 분석
            "ohaeng_balance": "...",     # 오행 밸런스 해석
            "pattern_context": "...",    # 격국 맥락 해석
            "yongshin_guide": "...",     # 용신+조후 실천 가이드
            "interaction_stories": [...], # 합충형파해 스토리
            "twelve_stage_summary": "...", # 십이운성 요약
            "core_narrative": "...",      # 핵심 서사 (가장 중요)
            "key_points": [...],          # 해석 핵심 포인트 (3~5개)
        }
    """
    day_stem = pillars.day.stem
    day_elem = STEM_OHAENG.get(day_stem, "")

    return {
        "day_stem_analysis": _day_stem_analysis(day_stem, strength),
        "ohaeng_balance": _ohaeng_balance(strength),
        "pattern_context": _pattern_context(pattern, strength, pillars),
        "yongshin_guide": _yongshin_guide(yongshin, johu, day_elem),
        "interaction_stories": _interaction_stories(interactions),
        "twelve_stage_summary": _twelve_stage_summary(twelve_stages),
        "core_narrative": _core_narrative(
            pillars, strength, pattern, yongshin, johu, naeum,
            twelve_stages, gongmang
        ),
        "key_points": _key_points(
            pillars, strength, pattern, yongshin, interactions,
            twelve_stages, gongmang, johu
        ),
    }


def _day_stem_analysis(day_stem: str, strength: StrengthResult) -> str:
    """일간 메타포 + 신강/약 맥락 해석."""
    meta = DAY_STEM_METAPHORS.get(day_stem, {})
    if not meta:
        return ""

    hanja = STEM_HANJA.get(day_stem, "")
    elem = STEM_OHAENG.get(day_stem, "")

    parts = [f"일간 {day_stem}({hanja}, {elem}) — {meta['image']}."]
    parts.append(f"본성: {meta['nature']}")

    score = strength.score
    if score >= 55:
        parts.append(f"신강({score}점): {meta['strong']}")
    elif score <= 45:
        parts.append(f"신약({score}점): {meta['weak']}")
    else:
        parts.append(f"중화({score}점): {meta['balanced']}")

    return " ".join(parts)


def _ohaeng_balance(strength: StrengthResult) -> str:
    """오행 밸런스 시각적 해석."""
    scores = strength.ohaeng_scores
    total = sum(scores.values()) or 1

    parts = []
    dominant = max(scores, key=scores.get)  # type: ignore
    weakest = min(scores, key=scores.get)  # type: ignore

    parts.append(f"가장 강한 오행: {dominant}({scores[dominant]:.0f}점, {scores[dominant]/total*100:.0f}%)")
    parts.append(f"가장 약한 오행: {weakest}({scores[weakest]:.0f}점, {scores[weakest]/total*100:.0f}%)")

    # 편중도 분석
    avg = total / 5
    deviations = [abs(scores[e] - avg) for e in OHAENG_LIST]
    avg_dev = sum(deviations) / 5

    if avg_dev > avg * 0.5:
        parts.append("오행이 심하게 편중되어 있어 특정 분야에 강하지만 균형이 필요합니다.")
    elif avg_dev > avg * 0.3:
        parts.append("오행이 다소 편중되어 있어 용신으로 보완하면 크게 발전할 수 있습니다.")
    else:
        parts.append("오행이 비교적 고르게 분포되어 안정적인 기본기를 가졌습니다.")

    # 빠진 오행
    missing = [e for e in OHAENG_LIST if scores.get(e, 0) < 3]
    if missing:
        parts.append(f"거의 없는 오행: {', '.join(missing)} — 해당 오행의 영역(직업/건강/관계)에서 보완이 필요합니다.")

    return " ".join(parts)


def _pattern_context(pattern: PatternResult, strength: StrengthResult,
                     pillars: FourPillars) -> str:
    """격국의 맥락적 해석."""
    parts = [f"격국: {pattern.name}."]
    if pattern.traits:
        parts.append(pattern.traits)

    if pattern.is_special:
        parts.append(
            "종격(從格)은 일반 사주와 해석법이 다릅니다. "
            "흐름을 거스르지 말고 강한 기운을 따라가야(從) 성공합니다. "
            "용신도 일반격과 반대입니다."
        )
    else:
        if strength.score >= 55:
            parts.append(
                f"신강한 {pattern.name}이므로, 강한 에너지를 생산적으로 발산하는 것이 핵심입니다. "
                "가만히 있으면 에너지가 내부에서 충돌합니다."
            )
        elif strength.score <= 45:
            parts.append(
                f"신약한 {pattern.name}이므로, 든든한 지원군(인성/비겁)이 있어야 격국의 장점이 발휘됩니다. "
                "무리하면 에너지 소진이 빠릅니다."
            )

    return " ".join(parts)


def _yongshin_guide(yongshin: YongshinResult, johu: dict, day_elem: str) -> str:
    """용신 + 조후 통합 실천 가이드."""
    parts = []
    parts.append(f"용신: {yongshin.yongshin}. {yongshin.yongshin_reason}")

    if yongshin.heeshin:
        parts.append(f"희신(보조): {yongshin.heeshin}")
    if yongshin.gishin:
        parts.append(f"기신(주의): {yongshin.gishin}")

    # 조후 통합
    if johu.get("has_johu"):
        johu_elem = johu["needed_element"]
        parts.append(f"조후용신: {johu_elem}. {johu['reason']}")
        parts.append(f"계절 비유: {johu['metaphor']}")

        if johu_elem == yongshin.yongshin:
            parts.append("용신과 조후가 일치하여 해당 오행이 매우 중요합니다.")
        else:
            parts.append(
                f"용신({yongshin.yongshin})과 조후({johu_elem})가 다릅니다. "
                "두 오행을 모두 고려하되, 실생활에서는 조후를 우선합니다."
            )

    return " ".join(parts)


def _interaction_stories(interactions: list[InteractionEntry]) -> list[dict]:
    """합충형파해를 실생활 스토리로 변환."""
    stories = []
    for inter in interactions:
        story = {
            "type": inter.type,
            "subtype": inter.subtype,
            "description": inter.description,
            "palace_meaning": "",
            "life_impact": "",
        }

        # 궁위 의미 매핑
        if len(inter.positions) >= 2:
            key = (inter.positions[0], inter.positions[1])
            palace_meaning = INTERACTION_PALACE_MEANING.get(key, "")
            if palace_meaning:
                story["palace_meaning"] = palace_meaning

        # 합충 유형별 생활 영향
        if inter.type == "합":
            story["life_impact"] = _hap_impact(inter)
        elif inter.type == "충":
            story["life_impact"] = _chung_impact(inter)
        elif inter.type == "형":
            story["life_impact"] = _hyung_impact(inter)
        elif inter.type == "파":
            story["life_impact"] = "관계의 틈이 생기거나 일이 순조롭지 않은 시기를 나타냄. 큰 충격은 아니지만 사소한 어긋남이 쌓일 수 있음"
        elif inter.type == "해":
            story["life_impact"] = "은근한 해로움, 신뢰하던 관계에서 배신이나 실망이 올 수 있음. 표면은 괜찮아 보이지만 내부에 문제가 잠재"

        stories.append(story)

    return stories


def _hap_impact(inter: InteractionEntry) -> str:
    if inter.subtype == "천간합":
        return "두 기운이 합쳐져 새로운 에너지로 변화함. 좋은 인연, 합작, 결합의 기운. 다만 합이 되면 본래 기능을 잃을 수 있음(합거)"
    elif inter.subtype == "육합":
        return "밀접한 관계, 깊은 인연을 나타냄. 연인, 동업자, 가까운 친구와의 강한 유대. 때로는 집착으로 나타남"
    elif inter.subtype == "삼합":
        return "세 기운이 하나로 뭉치는 강력한 결합. 큰 프로젝트나 팀워크에서 시너지. 인생의 큰 흐름을 만드는 기운"
    elif inter.subtype == "반삼합":
        return "삼합의 일부가 이루어진 상태. 잠재력은 있으나 완성되려면 나머지 한 요소가 필요. 대운/세운에서 완성될 때 크게 발동"
    return "합(合)의 기운이 작용"


def _chung_impact(inter: InteractionEntry) -> str:
    if inter.subtype == "천간충":
        return "두 기운이 정면 충돌. 갈등, 대립, 변화를 가져옴. 다만 충은 '움직임'을 만드므로 정체된 상황을 깨는 전환점이 될 수도 있음"
    elif inter.subtype == "육충":
        return "강한 변동과 갈등. 이사, 이직, 이별 등 '이(離)'의 기운이 강함. 해당 궁위의 안정이 흔들림. 다만 막혀있던 것을 뚫는 에너지이기도 함"
    return "충(沖)의 기운이 작용"


def _hyung_impact(inter: InteractionEntry) -> str:
    if "삼형살" in inter.subtype:
        return "강한 형벌적 에너지. 법적 분쟁, 소송, 신체적 상해 주의. 다만 법조인/의료인에게는 오히려 전문성을 높이는 기운"
    elif "무례지형" in inter.subtype:
        return "예의 없는 형벌. 가까운 관계(부부, 형제)에서의 마찰과 갈등. 서로를 존중하는 의식적 노력이 필요"
    elif "자형" in inter.subtype:
        return "같은 기운의 자기 충돌. 내면의 갈등, 자기 비하, 또는 같은 실수의 반복. 자기 성찰이 해결책"
    return "형(刑)의 기운이 작용"


def _twelve_stage_summary(stages: list[dict]) -> str:
    """십이운성 종합 요약."""
    parts = []
    for s in stages:
        parts.append(f"{s['position']}: {s['branch']}({s['label']}, {s['energy']})")

    # 핵심 해석
    day_stage = next((s for s in stages if s["position"] == "일지"), None)
    if day_stage:
        parts.append(
            f"일지(배우자 자리)가 {day_stage['label']}에 해당하여: {day_stage['meaning']}"
        )

    hour_stage = next((s for s in stages if s["position"] == "시지"), None)
    if hour_stage:
        parts.append(
            f"시지(말년/자녀)가 {hour_stage['label']}에 해당하여: {hour_stage['meaning']}"
        )

    return " | ".join(parts)


def _core_narrative(
    pillars: FourPillars,
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    johu: dict,
    naeum: dict,
    twelve_stages: list[dict],
    gongmang: dict,
) -> str:
    """핵심 서사 — 사주 전체를 관통하는 한 문단 스토리."""
    day_stem = pillars.day.stem
    meta = DAY_STEM_METAPHORS.get(day_stem, {})
    day_elem = STEM_OHAENG.get(day_stem, "")

    parts = []

    # 납음 일주
    day_n = naeum.get("day", {})
    if day_n.get("name"):
        parts.append(f"납음으로 보면 '{day_n['name']}({day_n['hanja']})' 명으로, {day_n['description']}.")

    # 일간 + 신강/약
    image = meta.get("image", day_stem)
    if strength.score >= 55:
        desc = meta.get("strong", "에너지가 넘침")
    elif strength.score <= 45:
        desc = meta.get("weak", "에너지가 부족함")
    else:
        desc = meta.get("balanced", "균형잡힘")
    parts.append(f"일간 {day_stem}({image})이 {strength.label}({strength.score}점) 상태이니, {desc}.")

    # 격국
    parts.append(f"격국은 {pattern.name}으로, {pattern.traits}.")

    # 용신 + 조후
    if johu.get("has_johu"):
        parts.append(f"계절적으로 {johu['metaphor']}.")

    parts.append(
        f"용신은 {yongshin.yongshin}이므로, "
        f"이 오행이 들어오는 대운·세운에서 크게 발전하고, "
        f"기신인 {yongshin.gishin or '(없음)'}이 강해지는 시기에는 조심해야 합니다."
    )

    # 일지 십이운성
    day_stage = next((s for s in twelve_stages if s["position"] == "일지"), None)
    if day_stage:
        parts.append(f"일지가 {day_stage['label']}이니, {day_stage['meaning']}.")

    # 공망
    affected = gongmang.get("affected_palaces", [])
    if affected:
        names = [a["palace"] for a in affected]
        parts.append(f"공망이 {', '.join(names)}에 걸려 해당 영역에서 '허(虛)한 기운'이 있습니다.")

    return " ".join(parts)


def _key_points(
    pillars: FourPillars,
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    interactions: list[InteractionEntry],
    twelve_stages: list[dict],
    gongmang: dict,
    johu: dict,
) -> list[str]:
    """핵심 해석 포인트 3~5개."""
    points = []
    day_stem = pillars.day.stem

    # 1. 신강/약 핵심
    if strength.score >= 65:
        points.append(f"매우 신강한 사주입니다. 에너지를 발산할 출구(식상/재성)가 반드시 필요하며, 가만히 있으면 내부 갈등이 커집니다.")
    elif strength.score >= 55:
        points.append(f"적당히 신강한 사주입니다. 자기 주도적으로 살 수 있는 기본 체력이 있으니, 활발한 사회활동이 좋습니다.")
    elif strength.score <= 35:
        points.append(f"많이 신약한 사주입니다. 인성(스승/학문)과 비겁(동료)의 도움이 필수적이며, 혼자 무리하면 쉽게 지칩니다.")
    elif strength.score <= 45:
        points.append(f"약간 신약한 사주입니다. 주변의 지원과 학습을 통해 부족한 에너지를 보충하는 것이 성공의 열쇠입니다.")
    else:
        points.append(f"중화에 가까운 사주입니다. 큰 치우침 없이 안정적이나, 용신 대운에서 더 크게 도약할 수 있습니다.")

    # 2. 충이 있으면 변동성
    chungs = [i for i in interactions if i.type == "충"]
    if chungs:
        chung_desc = ", ".join(i.description for i in chungs[:2])
        points.append(f"원국에 충({chung_desc})이 있어 변동성이 큽니다. 이사/이직/인간관계 변화가 잦을 수 있으나, 정체를 깨는 원동력이기도 합니다.")

    # 3. 합이 있으면 인연
    haps = [i for i in interactions if i.type == "합"]
    if haps:
        hap_desc = ", ".join(i.description for i in haps[:2])
        points.append(f"원국에 합({hap_desc})이 있어 좋은 인연과 결합의 기운이 있습니다. 다만 합으로 인해 본래 기능이 변질(합거)될 수도 있으니 맹신은 금물.")

    # 4. 공망 영향
    affected = gongmang.get("affected_palaces", [])
    if affected:
        for a in affected[:1]:
            points.append(f"{a['palace']} 공망: {a['meaning']}")

    # 5. 조후 핵심
    if johu.get("has_johu"):
        points.append(
            f"조후(계절 조절): {johu['reason']}. "
            f"실생활에서 {johu['needed_element']} 오행과 관련된 환경·직업·색상이 도움됩니다."
        )

    return points[:5]
