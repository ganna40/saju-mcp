"""궁합 성패 보고서 — 된다/안된다 관점."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, STEM_YINYANG, BRANCH_OHAENG, BRANCH_ANIMAL,
    OHAENG_LIST, GENERATING, CONTROLLING,
    CHEONGAN_HAP, YUKAP, YUKCHUNG,
    DAY_STEM_TRAITS, TEN_GOD_CATEGORIES,
    ELEM_COLOR, ELEM_FOOD, ELEM_DIRECTION,
)
from .models import (
    FourPillars, StrengthResult, YongshinResult,
    CompatReportSection, CompatReport, InteractionEntry,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch
from .strength import calc_strength
from .pattern_engine import determine_pattern
from .yongshin import determine_yongshin
from .interactions import detect_interactions
from .compatibility import (
    _day_stem_relation, _ohaeng_complement,
    _branch_interactions, _mutual_ten_gods,
)


def _verdict(score: float, max_score: float) -> str:
    ratio = score / max_score if max_score > 0 else 0
    if ratio >= 0.7:
        return "성(成)"
    if ratio >= 0.4:
        return "반반"
    return "패(敗)"


def _overall_verdict(total: float) -> str:
    if total >= 80:
        return "대성(大成)"
    if total >= 65:
        return "성(成)"
    if total >= 50:
        return "반반"
    if total >= 35:
        return "패(敗)"
    return "대패(大敗)"


def _overall_grade(total: float) -> str:
    if total >= 80:
        return "천생연분"
    if total >= 65:
        return "좋은 궁합"
    if total >= 50:
        return "무난한 궁합"
    if total >= 35:
        return "노력이 필요한 궁합"
    return "안 맞는 궁합"


# ── 1. 일간 관계 ──
def _sec_day_stem(stem_a: str, stem_b: str) -> CompatReportSection:
    elem_a = STEM_OHAENG[stem_a]
    elem_b = STEM_OHAENG[stem_b]
    yy_a = STEM_YINYANG[stem_a]
    yy_b = STEM_YINYANG[stem_b]

    lines = [
        f"남자 일간: {stem_a}({elem_a}/{yy_a}) — {DAY_STEM_TRAITS.get(stem_a, '')}",
        f"여자 일간: {stem_b}({elem_b}/{yy_b}) — {DAY_STEM_TRAITS.get(stem_b, '')}",
        "",
    ]

    # 천간합
    key = frozenset({stem_a, stem_b})
    if key in CHEONGAN_HAP:
        score = 25.0
        lines.append(f"{stem_a}+{stem_b} 천간합 → {CHEONGAN_HAP[key]}으로 변화")
        lines.append("천간합은 궁합 최상의 조합. 자연스럽게 하나가 되는 관계")
        summary = f"된다 — {stem_a}+{stem_b} 천간합. 최상의 조합"
    elif elem_a == elem_b:
        if yy_a != yy_b:
            score = 18.0
            lines.append(f"같은 오행({elem_a}) 음양 조화 — 서로 이해하며 보완하는 관계")
            summary = "된다 — 같은 오행 음양 조화"
        else:
            score = 12.0
            lines.append(f"같은 오행({elem_a}) 같은 음양 — 비슷해서 편하지만 경쟁 가능")
            summary = "반반 — 비슷한 성향, 경쟁 주의"
    elif GENERATING.get(elem_a) == elem_b or GENERATING.get(elem_b) == elem_a:
        score = 20.0
        if GENERATING.get(elem_a) == elem_b:
            lines.append(f"{elem_a}→{elem_b} 상생 — 남자가 여자를 도와주는 구도")
        else:
            lines.append(f"{elem_b}→{elem_a} 상생 — 여자가 남자를 도와주는 구도")
        summary = "된다 — 상생 관계. 서로 도움"
    elif CONTROLLING.get(elem_a) == elem_b:
        score = 8.0
        lines.append(f"{elem_a}→{elem_b} 상극(극) — 남자가 주도, 여자가 따르는 구도")
        lines.append("남자가 여자를 억누르는 형상. 여자가 답답함을 느낄 수 있음")
        summary = "안 된다 — 남자가 여자를 극. 억압 구도"
    elif CONTROLLING.get(elem_b) == elem_a:
        score = 8.0
        lines.append(f"{elem_b}→{elem_a} 상극(극) — 여자가 주도, 남자가 따르는 구도")
        summary = "안 된다 — 여자가 남자를 극"
    else:
        score = 10.0
        lines.append("특별한 관계 없음")
        summary = "반반"

    return CompatReportSection(
        title="일간 관계",
        verdict=_verdict(score, 25),
        score=round(score, 1),
        max_score=25,
        summary=summary,
        details=lines,
    )


# ── 2. 상호 십신 ──
def _sec_mutual_ten_gods(stem_a: str, stem_b: str) -> CompatReportSection:
    tg_a_sees_b = calc_ten_god(stem_a, stem_b)
    tg_b_sees_a = calc_ten_god(stem_b, stem_a)
    cat_a = TEN_GOD_CATEGORIES.get(tg_a_sees_b, "")
    cat_b = TEN_GOD_CATEGORIES.get(tg_b_sees_a, "")

    lines = [
        f"남자가 여자를 봄: {tg_a_sees_b}({cat_a})",
        f"여자가 남자를 봄: {tg_b_sees_a}({cat_b})",
        "",
    ]

    score = 0.0

    # 남자→여자
    good_for_man = {"정재": 12, "편재": 8, "식신": 6, "정인": 5}
    bad_for_man = {"편관": -3, "상관": -2, "겁재": -4}
    score += good_for_man.get(tg_a_sees_b, 3)
    score += bad_for_man.get(tg_a_sees_b, 0)

    # 여자→남자
    good_for_woman = {"정관": 12, "편관": 8, "정인": 6, "식신": 5}
    bad_for_woman = {"상관": -3, "겁재": -4, "편재": -2}
    score += good_for_woman.get(tg_b_sees_a, 3)
    score += bad_for_woman.get(tg_b_sees_a, 0)

    score = max(0, min(25, score))

    # 해석
    man_meaning = {
        "정재": "여자를 소중한 아내로 봄. 헌신적",
        "편재": "여자를 소유하려는 강한 끌림. 열정적이나 불안정",
        "식신": "여자에게 잘 해주고 표현함",
        "상관": "여자에게 간섭하고 잔소리",
        "정관": "여자를 존경하고 따름",
        "편관": "여자에게 긴장감을 느낌",
        "정인": "여자에게 배우고 의지함",
        "편인": "여자가 부담스러울 수 있음",
        "비견": "여자를 동료/경쟁자로 봄",
        "겁재": "여자를 빼앗길까 불안해함",
    }
    woman_meaning = {
        "정관": "남자를 이상적 남편감으로 봄. 안정적",
        "편관": "남자에게 강한 끌림이나 부담도 느낌",
        "정재": "남자를 통해 안정을 얻으려 함",
        "편재": "남자에게 물질적 기대",
        "식신": "남자에게 잘 해주고 편안함",
        "상관": "남자에게 불만과 간섭이 많을 수 있음",
        "정인": "남자를 스승처럼 존경",
        "편인": "남자가 답답하게 느껴질 수 있음",
        "비견": "남자를 동료/경쟁자로 봄",
        "겁재": "남자와 주도권 다툼",
    }
    lines.append(f"남자 시각: {man_meaning.get(tg_a_sees_b, '')}")
    lines.append(f"여자 시각: {woman_meaning.get(tg_b_sees_a, '')}")

    # 최고 조합 판정
    best_pairs = {
        ("정재", "정관"): "최고의 부부 조합",
        ("정재", "편관"): "열정적 부부",
        ("편재", "정관"): "현실적 부부",
        ("식신", "정관"): "서로 배려하는 관계",
        ("식신", "정인"): "존경과 배려의 관계",
    }
    pair_desc = best_pairs.get((tg_a_sees_b, tg_b_sees_a), "")
    if pair_desc:
        lines.append(f"조합 평가: {pair_desc}")

    ok = score >= 12
    summary = f"{'된다' if ok else '안 된다'} — 남→여: {tg_a_sees_b}, 여→남: {tg_b_sees_a}"

    return CompatReportSection(
        title="상호 십신",
        verdict=_verdict(score, 25),
        score=round(score, 1),
        max_score=25,
        summary=summary,
        details=lines,
    )


# ── 3. 합충 관계 ──
def _sec_interactions(pillars_a: FourPillars, pillars_b: FourPillars) -> CompatReportSection:
    interactions, raw_score = _branch_interactions(pillars_a, pillars_b)

    hap_list = [i for i in interactions if i.type == "합"]
    chung_list = [i for i in interactions if i.type == "충"]

    lines = []
    if hap_list:
        lines.append(f"합(合) {len(hap_list)}개:")
        for i in hap_list:
            lines.append(f"  {i.description} [{i.positions[0]}↔{i.positions[1]}]")
    if chung_list:
        lines.append(f"충(沖) {len(chung_list)}개:")
        for i in chung_list:
            lines.append(f"  {i.description} [{i.positions[0]}↔{i.positions[1]}]")
    if not hap_list and not chung_list:
        lines.append("특별한 합충 관계 없음")

    lines.append("")

    # 일지끼리 특별 체크
    a_ilji = pillars_a.day.branch
    b_ilji = pillars_b.day.branch
    ilji_key = frozenset({a_ilji, b_ilji})
    if a_ilji == b_ilji:
        lines.append(f"일지 동일({a_ilji}) — 생활 패턴과 가치관이 비슷")
        raw_score += 3
    if ilji_key in YUKAP:
        lines.append(f"일지 육합({a_ilji}+{b_ilji}) — 배우자궁끼리 합! 결합력 매우 강함")
        raw_score += 5
    if ilji_key in YUKCHUNG:
        lines.append(f"일지 육충({a_ilji}↔{b_ilji}) — 배우자궁 충돌. 생활 속 갈등 심함")
        raw_score -= 5

    # 띠 충 (년지)
    year_key = frozenset({pillars_a.year.branch, pillars_b.year.branch})
    if year_key in YUKCHUNG:
        animal_a = BRANCH_ANIMAL.get(pillars_a.year.branch, "")
        animal_b = BRANCH_ANIMAL.get(pillars_b.year.branch, "")
        lines.append(f"년지 육충({animal_a}띠↔{animal_b}띠) — 집안/환경 차이, 주변 반대 가능")

    score = max(0, min(25, raw_score + 12.5))

    ok = score >= 12
    summary = f"{'된다' if ok else '안 된다'} — 합 {len(hap_list)}개 / 충 {len(chung_list)}개"

    return CompatReportSection(
        title="합충 관계",
        verdict=_verdict(score, 25),
        score=round(score, 1),
        max_score=25,
        summary=summary,
        details=lines,
    )


# ── 4. 오행 보완 ──
def _sec_ohaeng(pillars_a: FourPillars, pillars_b: FourPillars,
                strength_a: StrengthResult, strength_b: StrengthResult,
                yongshin_a: YongshinResult, yongshin_b: YongshinResult) -> tuple[CompatReportSection, list[dict]]:
    oh_a = strength_a.ohaeng_scores
    oh_b = strength_b.ohaeng_scores

    table = []
    complement_score = 0.0
    lines = []

    for elem in OHAENG_LIST:
        a_v = oh_a.get(elem, 0)
        b_v = oh_b.get(elem, 0)
        who = "남자↑" if a_v > b_v + 5 else "여자↑" if b_v > a_v + 5 else "비슷"
        table.append({"오행": elem, "남자": round(a_v, 1), "여자": round(b_v, 1), "우세": who})

    # 상호 보완 체크
    for elem in OHAENG_LIST:
        a_v = oh_a.get(elem, 0)
        b_v = oh_b.get(elem, 0)
        if a_v <= 3 and b_v >= 20:
            complement_score += 4
            lines.append(f"남자에게 부족한 {elem}을 여자가 보완 ({a_v:.0f} → {b_v:.0f})")
        if b_v <= 3 and a_v >= 20:
            complement_score += 4
            lines.append(f"여자에게 부족한 {elem}을 남자가 보완 ({b_v:.0f} → {a_v:.0f})")

    # 용신 보완 (가장 중요)
    yong_a = yongshin_a.yongshin
    yong_b = yongshin_b.yongshin
    if yong_a and oh_b.get(yong_a, 0) >= 20:
        complement_score += 5
        lines.append(f"남자 용신({yong_a})을 여자가 풍부하게 보유 — 여자가 남자에게 복")
    if yong_b and oh_a.get(yong_b, 0) >= 20:
        complement_score += 5
        lines.append(f"여자 용신({yong_b})을 남자가 풍부하게 보유 — 남자가 여자에게 복")

    if not lines:
        lines.append("뚜렷한 오행 보완 관계 없음")

    score = max(0, min(25, complement_score))
    ok = score >= 12

    return CompatReportSection(
        title="오행 보완",
        verdict=_verdict(score, 25),
        score=round(score, 1),
        max_score=25,
        summary=f"{'된다' if ok else '안 된다'} — {'서로 용신을 채워주는 관계' if score >= 18 else '부분 보완' if score >= 8 else '보완 미약'}",
        details=lines,
    ), table


# ── 조언 ──
def _build_advice(sections: list[CompatReportSection], stem_a: str, stem_b: str,
                  yongshin_a: YongshinResult, yongshin_b: YongshinResult) -> list[str]:
    advice = []
    elem_a = STEM_OHAENG[stem_a]
    elem_b = STEM_OHAENG[stem_b]

    # 상극이면
    if CONTROLLING.get(elem_a) == elem_b:
        advice.append(f"남자({elem_a})가 여자({elem_b})를 극하는 구도 → 남자가 여자를 존중하고 공간을 줘야 함")
    elif CONTROLLING.get(elem_b) == elem_a:
        advice.append(f"여자({elem_b})가 남자({elem_a})를 극하는 구도 → 여자가 남자 체면을 세워줘야 함")

    # 합충 기반
    for sec in sections:
        if sec.title == "합충 관계":
            if "년지 육충" in "\n".join(sec.details):
                advice.append("띠 충(년지 충) → 집안 갈등 가능. 시댁/처가 문제는 둘만의 독립 공간으로 해결")
            if "일지 육충" in "\n".join(sec.details):
                advice.append("일지 충 → 생활 속 갈등이 잦을 수 있음. 각자 취미/공간 확보")

    # 용신 관련
    yong_a = yongshin_a.yongshin
    yong_b = yongshin_b.yongshin
    if yong_a:
        color = ELEM_COLOR.get(yong_a, "")
        food = ELEM_FOOD.get(yong_a, "")
        direction = ELEM_DIRECTION.get(yong_a, "")
        advice.append(f"남자 보강: {yong_a}({color}, {food}, {direction})")
    if yong_b:
        color = ELEM_COLOR.get(yong_b, "")
        food = ELEM_FOOD.get(yong_b, "")
        direction = ELEM_DIRECTION.get(yong_b, "")
        advice.append(f"여자 보강: {yong_b}({color}, {food}, {direction})")

    advice.append("서로의 부족한 오행을 채워주는 것이 궁합 향상의 핵심")

    return advice


# ── 메인 ──
def generate_compat_report(
    pillars_a: FourPillars, pillars_b: FourPillars,
    gender_a: str = "남", gender_b: str = "여",
    info_a: dict | None = None, info_b: dict | None = None,
) -> CompatReport:
    """궁합 성패 보고서 생성."""
    stem_a = pillars_a.day.stem
    stem_b = pillars_b.day.stem

    strength_a = calc_strength(pillars_a)
    strength_b = calc_strength(pillars_b)
    pattern_a = determine_pattern(pillars_a, strength_a)
    pattern_b = determine_pattern(pillars_b, strength_b)
    yongshin_a = determine_yongshin(strength_a, pattern_a)
    yongshin_b = determine_yongshin(strength_b, pattern_b)

    sections: list[CompatReportSection] = []

    sec1 = _sec_day_stem(stem_a, stem_b)
    sections.append(sec1)

    sec2 = _sec_mutual_ten_gods(stem_a, stem_b)
    sections.append(sec2)

    sec3 = _sec_interactions(pillars_a, pillars_b)
    sections.append(sec3)

    sec4, ohaeng_table = _sec_ohaeng(pillars_a, pillars_b, strength_a, strength_b, yongshin_a, yongshin_b)
    sections.append(sec4)

    total = sum(s.score for s in sections)
    total = max(0, min(100, total))

    advice = _build_advice(sections, stem_a, stem_b, yongshin_a, yongshin_b)

    def fp_summary(p: FourPillars) -> str:
        return f"{p.year.stem}{p.year.branch} {p.month.stem}{p.month.branch} {p.day.stem}{p.day.branch} {p.hour.stem}{p.hour.branch}"

    grade = _overall_grade(total)
    verdict = _overall_verdict(total)

    if total >= 65:
        overall_summary = "좋은 궁합. 함께 있으면 서로에게 힘이 되는 관계"
    elif total >= 50:
        overall_summary = "무난한 궁합. 큰 문제 없이 함께할 수 있음"
    elif total >= 35:
        overall_summary = "노력이 필요한 궁합. 서로 맞추려는 의지가 있다면 가능"
    else:
        overall_summary = "힘든 궁합. 강한 각오와 노력이 필요"

    return CompatReport(
        person_a=info_a or {},
        person_b=info_b or {},
        pillars_a_summary=fp_summary(pillars_a),
        pillars_b_summary=fp_summary(pillars_b),
        total_score=round(total, 1),
        grade=grade,
        overall_verdict=verdict,
        overall_summary=overall_summary,
        sections=sections,
        ohaeng_table=ohaeng_table,
        advice=advice,
    )
