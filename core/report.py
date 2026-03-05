"""성패 보고서 — 된다/안된다 관점의 사주 종합 보고서 생성."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, STEM_YINYANG, BRANCH_OHAENG,
    DAY_STEM_TRAITS, PATTERN_TRAITS, CAREER_BY_PATTERN,
    ELEM_ORGAN, ELEM_FOOD, ELEM_COLOR, ELEM_DIRECTION,
    TEN_GOD_CATEGORIES, GENERATING, CONTROLLING,
    CHEONGAN_HAP, YUKAP, YUKCHUNG,
)
from .models import (
    FourPillars, StrengthResult, PatternResult, YongshinResult,
    WealthResult, RadarResult, DaeunEntry, InteractionEntry,
    SinsalEntry, TenGodEntry, LifeEvent,
    ReportSection, SajuReport,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


# ── 판정 기준 ──
def _verdict(score: float, threshold: float = 60.0) -> str:
    """점수 기반 성/패 판정."""
    if score >= 80:
        return "대성(大成)"
    if score >= threshold:
        return "성(成)"
    if score >= 40:
        return "반반"
    if score >= 20:
        return "패(敗)"
    return "대패(大敗)"


def _pass_fail(ok: bool) -> str:
    return "된다" if ok else "안 된다"


# ────────────────────────────────────────
# 1. 성격
# ────────────────────────────────────────
def _section_personality(pillars: FourPillars, strength: StrengthResult,
                         ten_gods: list[TenGodEntry], pattern: PatternResult) -> ReportSection:
    day_stem = pillars.day.stem
    day_elem = STEM_OHAENG[day_stem]
    yy = STEM_YINYANG[day_stem]

    cats = {}
    for tg in ten_gods:
        c = tg.category
        cats[c] = cats.get(c, 0) + 1

    dominant = max(cats, key=cats.get) if cats else "비겁"

    personality_map = {
        "비겁": ("자기주장이 강하고 독립적", "고집이 세고 타협이 어려움"),
        "식상": ("표현력과 재능이 뛰어남", "변덕스럽고 끈기가 부족할 수 있음"),
        "재성": ("현실적이고 재물 감각이 좋음", "물질에 집착할 수 있음"),
        "관성": ("책임감 있고 조직적", "스트레스에 약하고 융통성이 부족"),
        "인성": ("학구적이고 사려 깊음", "우유부단하고 행동력이 부족할 수 있음"),
    }

    plus, minus = personality_map.get(dominant, ("보통", "보통"))
    base_trait = DAY_STEM_TRAITS.get(day_stem, "")

    # 성패 판정: 사회 적응력 관점
    social_score = 50.0
    if strength.label == "중화":
        social_score += 15  # 균형잡힌 성격
    if "정관" in [tg.ten_god for tg in ten_gods] or "정인" in [tg.ten_god for tg in ten_gods]:
        social_score += 10
    if cats.get("관성", 0) >= 3 or cats.get("비겁", 0) >= 4:
        social_score -= 15  # 극단적 편중
    if "상관" in [tg.ten_god for tg in ten_gods]:
        social_score += 5  # 재능은 있음
    social_score = max(0, min(100, social_score))

    verdict = _verdict(social_score)

    lines = [
        f"일간: {day_stem}({day_elem}/{yy}) — {base_trait}",
        f"격국: {pattern.name} — {PATTERN_TRAITS.get(pattern.name, '')}",
        f"신강도: {strength.score}점 ({strength.label})",
        f"",
        f"지배 십신: {dominant} ({cats.get(dominant, 0)}개)",
        f"장점: {plus}",
        f"단점: {minus}",
        f"",
        f"사회적응력: {social_score:.0f}점",
    ]

    return ReportSection(
        title="성격",
        verdict=verdict,
        score=round(social_score, 1),
        summary=f"{day_stem}일간 {pattern.name}. {base_trait.split('.')[0]}",
        details=lines,
    )


# ────────────────────────────────────────
# 2. 재물운
# ────────────────────────────────────────
def _section_wealth(wealth: WealthResult) -> ReportSection:
    score = wealth.total_score
    verdict = _verdict(score, 50.0)

    lines = []
    for item in wealth.items:
        sign = "+" if item.score >= 0 else ""
        lines.append(f"{item.category}. {item.label}: {sign}{item.score}/{item.max_score}점 {item.description}")
    lines.append("")
    lines.append(f"총점: {score:.1f}/100점 → {wealth.grade}등급 ({wealth.grade_label})")

    if wealth.peak_periods:
        lines.append(f"전성기: {', '.join(wealth.peak_periods)}")
    if wealth.risk_periods:
        lines.append(f"위험기: {', '.join(wealth.risk_periods)}")

    ok = score >= 50
    summary = f"재물그릇 {wealth.grade}등급 ({score:.0f}점). {_pass_fail(ok)} — {'큰 돈을 만질 팔자' if score >= 65 else '꾸준한 노력형 재물운' if score >= 40 else '재물 복이 약하니 기술/전문직으로 승부'}"

    return ReportSection(
        title="재물운",
        verdict=verdict,
        score=round(score, 1),
        summary=summary,
        details=lines,
    )


# ────────────────────────────────────────
# 3. 직장운
# ────────────────────────────────────────
def _section_career(pillars: FourPillars, ten_gods: list[TenGodEntry],
                    pattern: PatternResult, strength: StrengthResult,
                    radar: RadarResult) -> ReportSection:
    day_stem = pillars.day.stem
    cats = {}
    for tg in ten_gods:
        cats[tg.category] = cats.get(tg.category, 0) + 1

    gwanseong = cats.get("관성", 0)
    inseong = cats.get("인성", 0)
    siksang = cats.get("식상", 0)
    bigeop = cats.get("비겁", 0)
    jaeseong = cats.get("재성", 0)

    score = radar.axes.get("직업운", 50.0)

    # 관성 유무 = 직장운의 핵심
    has_jeonggwan = any(tg.ten_god == "정관" for tg in ten_gods)
    has_pyeongwan = any(tg.ten_god == "편관" for tg in ten_gods)

    if has_jeonggwan:
        score += 10
    if has_pyeongwan:
        score += 5

    # 정관+정인 = 직장 최고 조합
    has_jeongin = any(tg.ten_god == "정인" for tg in ten_gods)
    if has_jeonggwan and has_jeongin:
        score += 10

    # 상관견관 = 직장 불리
    has_sanggwan = any(tg.ten_god == "상관" for tg in ten_gods)
    if has_sanggwan and has_jeonggwan:
        score -= 10  # 상관견관

    # 비겁 과다 = 독립/사업 체질
    if bigeop >= 3:
        score -= 5

    score = max(0, min(100, score))
    verdict = _verdict(score, 60.0)

    careers = CAREER_BY_PATTERN.get(pattern.name, [])
    if gwanseong >= 2:
        job_type = "조직형 (대기업/공무원/관리직 적합)"
    elif siksang >= 2:
        job_type = "전문직/기술형 (프리랜서/예술가/기술자 적합)"
    elif jaeseong >= 2:
        job_type = "사업형 (자영업/투자/영업 적합)"
    elif bigeop >= 3:
        job_type = "독립형 (1인기업/프리랜서 적합)"
    else:
        job_type = "균형형 (다양한 분야 적응 가능)"

    ok = score >= 55
    lines = [
        f"관성: {gwanseong}개 / 인성: {inseong}개 / 식상: {siksang}개",
        f"정관 유무: {'있음' if has_jeonggwan else '없음'} / 편관: {'있음' if has_pyeongwan else '없음'}",
        f"상관견관: {'해당' if has_sanggwan and has_jeonggwan else '비해당'}",
        f"",
        f"직업 체질: {job_type}",
        f"추천 직업: {', '.join(careers[:4]) if careers else '다양한 분야 가능'}",
        f"",
        f"직장운 점수: {score:.0f}점",
    ]

    summary = f"{_pass_fail(ok)} — {job_type.split('(')[0].strip()}"

    return ReportSection(
        title="직장운",
        verdict=verdict,
        score=round(score, 1),
        summary=summary,
        details=lines,
    )


# ────────────────────────────────────────
# 4. 연애운
# ────────────────────────────────────────
def _section_romance(pillars: FourPillars, ten_gods: list[TenGodEntry],
                     sinsal: list[SinsalEntry], gender: str,
                     interactions: list[InteractionEntry]) -> ReportSection:
    day_stem = pillars.day.stem
    il_ji = pillars.day.branch

    # 배우자궁(일지) 십신
    spouse_tg = calc_ten_god_for_branch(day_stem, il_ji)
    spouse_cat = TEN_GOD_CATEGORIES.get(spouse_tg, "")

    # 남자: 재성 = 여자/연인, 여자: 관성 = 남자/연인
    target_cat = "재성" if gender == "남" else "관성"
    target_count = sum(1 for tg in ten_gods if tg.category == target_cat)

    has_dohwa = any(s.name == "도화살" for s in sinsal)
    has_cheonul = any(s.name == "천을귀인" for s in sinsal)

    # 일지 합/충
    ilji_hap = any(i.type == "합" and "일지" in i.positions for i in interactions)
    ilji_chung = any(i.type == "충" and "일지" in i.positions for i in interactions)

    score = 50.0
    details_lines = []

    # 배우자성 있는지
    if target_count >= 2:
        score += 15
        details_lines.append(f"이성인연({target_cat}): {target_count}개 — 이성 인연 풍부")
    elif target_count == 1:
        score += 8
        details_lines.append(f"이성인연({target_cat}): {target_count}개 — 적당한 인연")
    else:
        score -= 10
        details_lines.append(f"이성인연({target_cat}): 0개 — 이성 인연이 약함")

    # 배우자궁 상태
    if spouse_cat == target_cat:
        score += 10
        details_lines.append(f"배우자궁(일지 {il_ji}): {spouse_tg} — 배우자궁에 배우자성 좌정, 매우 좋음")
    else:
        details_lines.append(f"배우자궁(일지 {il_ji}): {spouse_tg}({spouse_cat})")

    if ilji_hap:
        score += 8
        details_lines.append("배우자궁 합 — 배우자와 조화로운 관계")
    if ilji_chung:
        score -= 12
        details_lines.append("배우자궁 충 — 배우자와 갈등/이별 가능성")

    if has_dohwa:
        score += 8
        details_lines.append("도화살 보유 — 이성에게 매력적, 연애 기회 많음")
    if has_cheonul:
        score += 3
        details_lines.append("천을귀인 — 좋은 인연을 만날 행운")

    # 상관 과다 (여자: 관성 극파)
    sanggwan_count = sum(1 for tg in ten_gods if tg.ten_god == "상관")
    if gender == "여" and sanggwan_count >= 2:
        score -= 12
        details_lines.append(f"상관 {sanggwan_count}개 — 남편성(관성)을 극하여 연애/결혼 불리")
    if gender == "남" and sum(1 for tg in ten_gods if tg.ten_god == "겁재") >= 2:
        score -= 8
        details_lines.append("겁재 과다 — 재성(여자)을 빼앗기는 형상, 경쟁자 출현")

    score = max(0, min(100, score))
    verdict = _verdict(score, 55.0)
    ok = score >= 55

    return ReportSection(
        title="연애운",
        verdict=verdict,
        score=round(score, 1),
        summary=f"{_pass_fail(ok)} — {'이성 인연이 좋고 매력적' if ok else '인연이 약하거나 장애물이 있음. 노력 필요'}",
        details=details_lines,
    )


# ────────────────────────────────────────
# 5. 결혼운
# ────────────────────────────────────────
def _section_marriage(pillars: FourPillars, ten_gods: list[TenGodEntry],
                      sinsal: list[SinsalEntry], gender: str,
                      interactions: list[InteractionEntry],
                      daeun: list[DaeunEntry]) -> ReportSection:
    day_stem = pillars.day.stem
    il_ji = pillars.day.branch

    target_cat = "재성" if gender == "남" else "관성"
    target_count = sum(1 for tg in ten_gods if tg.category == target_cat)

    spouse_tg = calc_ten_god_for_branch(day_stem, il_ji)
    spouse_cat = TEN_GOD_CATEGORIES.get(spouse_tg, "")

    ilji_chung = any(i.type == "충" and "일지" in i.positions for i in interactions)
    ilji_hyung = any(i.type == "형" and "일지" in i.positions for i in interactions)

    score = 50.0
    lines = []

    # 배우자성 존재
    if target_count >= 1:
        score += 10
        lines.append(f"배우자성({target_cat}): {target_count}개 — 결혼 인연 있음")
    else:
        score -= 15
        lines.append(f"배우자성({target_cat}): 없음 — 결혼이 늦거나 인연이 약함")

    # 배우자궁 = 배우자성이면 최상
    if spouse_cat == target_cat:
        score += 12
        lines.append("배우자궁에 배우자성 — 배우자복이 좋음")

    # 배우자궁 충/형 = 이혼 위험
    if ilji_chung:
        score -= 15
        lines.append("배우자궁 충 — 결혼생활 갈등, 이혼 가능성 높음")
    if ilji_hyung:
        score -= 10
        lines.append("배우자궁 형 — 배우자와의 고통/시련")

    # 배우자성 과다 (3개 이상) = 다정다감하나 바람끼
    if target_count >= 3:
        score -= 8
        lines.append(f"배우자성 과다({target_count}개) — 여러 이성과 인연, 결혼 후 유혹")

    # 결혼 적기 (대운에서 배우자성 오는 시기)
    marriage_periods = []
    for d in daeun:
        stem_tg = calc_ten_god(day_stem, d.stem)
        branch_tg = calc_ten_god_for_branch(day_stem, d.branch)
        stem_cat = TEN_GOD_CATEGORIES.get(stem_tg, "")
        branch_cat = TEN_GOD_CATEGORIES.get(branch_tg, "")
        if target_cat in (stem_cat, branch_cat):
            if 20 <= d.age_start <= 45:
                marriage_periods.append(f"{d.age_start}~{d.age_end}세")
                score += 3

    if marriage_periods:
        lines.append(f"결혼 적기 대운: {', '.join(marriage_periods)}")
    else:
        score -= 5
        lines.append("대운에서 뚜렷한 결혼 시기가 보이지 않음")

    # 양인살/괴강살 = 결혼 불리
    has_yangin = any(s.name == "양인살" for s in sinsal)
    has_goegang = any(s.name == "괴강살" for s in sinsal)
    if has_yangin:
        score -= 5
        lines.append("양인살 — 강한 성격이 결혼생활에 마찰을 줄 수 있음")
    if has_goegang:
        score -= 5
        lines.append("괴강살 — 독립적 성향이 강해 배우자와 충돌 가능")

    score = max(0, min(100, score))
    verdict = _verdict(score, 55.0)
    ok = score >= 55

    summary_parts = [_pass_fail(ok)]
    if ok:
        if marriage_periods:
            summary_parts.append(f"결혼 적기 {marriage_periods[0]}")
        summary_parts.append("결혼생활 유지 가능")
    else:
        if ilji_chung:
            summary_parts.append("배우자궁 충으로 결혼 유지 어려움")
        elif target_count == 0:
            summary_parts.append("배우자 인연이 약해 만혼 또는 독신 가능")
        else:
            summary_parts.append("결혼은 가능하나 노력 필요")

    return ReportSection(
        title="결혼운",
        verdict=verdict,
        score=round(score, 1),
        summary=" — ".join(summary_parts),
        details=lines,
    )


# ────────────────────────────────────────
# 6. 자녀운
# ────────────────────────────────────────
def _section_children(pillars: FourPillars, ten_gods: list[TenGodEntry],
                      gender: str, interactions: list[InteractionEntry]) -> ReportSection:
    day_stem = pillars.day.stem

    # 자녀성: 남자=관성, 여자=식상
    child_cat = "관성" if gender == "남" else "식상"
    child_count = sum(1 for tg in ten_gods if tg.category == child_cat)

    # 시주(시간+시지) = 자녀궁
    si_stem_tg = calc_ten_god(day_stem, pillars.hour.stem)
    si_branch_tg = calc_ten_god_for_branch(day_stem, pillars.hour.branch)
    si_stem_cat = TEN_GOD_CATEGORIES.get(si_stem_tg, "")
    si_branch_cat = TEN_GOD_CATEGORIES.get(si_branch_tg, "")

    # 시주 충
    siju_chung = any(i.type == "충" and "시지" in i.positions for i in interactions)

    score = 50.0
    lines = []

    if child_count >= 2:
        score += 12
        lines.append(f"자녀성({child_cat}): {child_count}개 — 자녀복 좋음")
    elif child_count == 1:
        score += 5
        lines.append(f"자녀성({child_cat}): 1개 — 자녀 인연 보통")
    else:
        score -= 12
        lines.append(f"자녀성({child_cat}): 없음 — 자녀 인연이 약함")

    # 시주에 자녀성이 있으면 가산
    if child_cat in (si_stem_cat, si_branch_cat):
        score += 10
        lines.append("자녀궁(시주)에 자녀성 — 자녀와 인연이 깊음")
    else:
        lines.append(f"자녀궁(시주): {si_stem_tg}/{si_branch_tg}")

    # 시주에 인성(편인) = 자녀 극하는 구조 (여자)
    if gender == "여" and si_stem_cat == "인성":
        score -= 8
        lines.append("시주에 인성 — 식상(자녀성)을 극하여 자녀 불리")

    if siju_chung:
        score -= 10
        lines.append("시주 충 — 자녀와의 갈등 또는 자녀 문제 발생 가능")

    # 식상 과다 (여자)
    siksang_count = sum(1 for tg in ten_gods if tg.category == "식상")
    if gender == "여" and siksang_count >= 3:
        score += 3
        lines.append(f"식상 {siksang_count}개 — 자녀가 여럿일 가능성")

    score = max(0, min(100, score))
    verdict = _verdict(score, 55.0)
    ok = score >= 50

    return ReportSection(
        title="자녀운",
        verdict=verdict,
        score=round(score, 1),
        summary=f"{_pass_fail(ok)} — {'자녀복이 있는 팔자' if ok else '자녀 인연이 약하거나 늦게 얻을 수 있음'}",
        details=lines,
    )


# ────────────────────────────────────────
# 7. 적성
# ────────────────────────────────────────
def _section_aptitude(pillars: FourPillars, pattern: PatternResult,
                      ten_gods: list[TenGodEntry], strength: StrengthResult) -> ReportSection:
    cats = {}
    for tg in ten_gods:
        cats[tg.category] = cats.get(tg.category, 0) + 1

    dominant = max(cats, key=cats.get) if cats else "비겁"

    aptitude_map = {
        "비겁": ("리더십/독립/스포츠", "경영, 프리랜서, 운동선수, 독립사업"),
        "식상": ("창작/표현/기술", "예술가, 작가, 개발자, 요리사, 디자이너"),
        "재성": ("재물/거래/관리", "사업가, 투자자, 영업, 유통, 재테크"),
        "관성": ("조직/관리/권위", "공무원, 군인, 경찰, 판사, 대기업"),
        "인성": ("학문/연구/교육", "교수, 연구원, 의사, 상담사, 학자"),
    }

    field, jobs = aptitude_map.get(dominant, ("다방면", "다양한 분야"))
    careers = CAREER_BY_PATTERN.get(pattern.name, [])

    # 적성 명확도 = 지배 십신이 얼마나 뚜렷한가
    total = sum(cats.values())
    dominant_ratio = cats.get(dominant, 0) / total if total > 0 else 0
    clarity = dominant_ratio * 100

    score = 50.0
    if clarity >= 40:
        score += 20  # 방향이 뚜렷
    elif clarity >= 30:
        score += 10
    else:
        score -= 5  # 방향 불분명

    # 격국과 지배 십신이 일치하면 가산
    pattern_cat_map = {
        "비견격": "비겁", "겁재격": "비겁",
        "식신격": "식상", "상관격": "식상",
        "편재격": "재성", "정재격": "재성",
        "편관격": "관성", "정관격": "관성",
        "편인격": "인성", "정인격": "인성",
    }
    if pattern_cat_map.get(pattern.name) == dominant:
        score += 10

    score = max(0, min(100, score))
    verdict = _verdict(score, 55.0)

    lines = [
        f"지배 십신: {dominant} ({cats.get(dominant, 0)}개/{total}개, {clarity:.0f}%)",
        f"적성 분야: {field}",
        f"추천 직업: {jobs}",
        f"격국 기반 추천: {', '.join(careers[:4]) if careers else '-'}",
        f"",
        f"적성 명확도: {clarity:.0f}% — {'방향이 뚜렷' if clarity >= 35 else '다방면 가능하나 선택과 집중 필요'}",
    ]

    return ReportSection(
        title="적성",
        verdict=verdict,
        score=round(score, 1),
        summary=f"{field} 분야 적합 — {', '.join(careers[:3]) if careers else jobs.split(',')[0]}",
        details=lines,
    )


# ────────────────────────────────────────
# 8. 총평
# ────────────────────────────────────────
def _section_overall(sections: list[ReportSection], strength: StrengthResult,
                     pattern: PatternResult, yongshin: YongshinResult,
                     pillars: FourPillars) -> ReportSection:
    avg = sum(s.score for s in sections) / len(sections) if sections else 50

    # 가중 평균 (재물/직장에 좀 더 비중)
    weights = {"성격": 1.0, "재물운": 1.5, "직장운": 1.3, "연애운": 1.0,
               "결혼운": 1.2, "자녀운": 0.8, "적성": 1.0}
    weighted_sum = 0.0
    weight_total = 0.0
    for s in sections:
        w = weights.get(s.title, 1.0)
        weighted_sum += s.score * w
        weight_total += w
    weighted_avg = weighted_sum / weight_total if weight_total > 0 else avg

    verdict = _verdict(weighted_avg, 55.0)

    # 최강/최약
    best = max(sections, key=lambda s: s.score)
    worst = min(sections, key=lambda s: s.score)

    success_count = sum(1 for s in sections if s.score >= 55)
    fail_count = sum(1 for s in sections if s.score < 40)

    day_stem = pillars.day.stem

    lines = [
        f"종합점수: {weighted_avg:.1f}/100점",
        f"",
        f"일간: {day_stem} / 격국: {pattern.name} / 신강도: {strength.label}({strength.score}점)",
        f"용신: {yongshin.yongshin} ({yongshin.yongshin_reason})",
        f"",
        f"가장 강한 운: {best.title} ({best.score:.0f}점, {best.verdict})",
        f"가장 약한 운: {worst.title} ({worst.score:.0f}점, {worst.verdict})",
        f"",
        f"성(成) 영역: {success_count}개 / 패(敗) 영역: {fail_count}개 / 전체: {len(sections)}개",
    ]

    for s in sections:
        marker = "O" if s.score >= 55 else "△" if s.score >= 40 else "X"
        lines.append(f"  [{marker}] {s.title}: {s.score:.0f}점 — {s.verdict}")

    if weighted_avg >= 65:
        conclusion = "전반적으로 좋은 사주. 타고난 복이 있으니 자신감을 가지고 밀고 나갈 것"
    elif weighted_avg >= 50:
        conclusion = "보통 이상의 사주. 노력 여하에 따라 성공 가능. 용신 오행을 보강할 것"
    else:
        conclusion = "약한 부분이 많으나 강한 영역에 집중하면 충분히 성공 가능"

    lines.append(f"")
    lines.append(f"결론: {conclusion}")

    return ReportSection(
        title="총평",
        verdict=verdict,
        score=round(weighted_avg, 1),
        summary=conclusion,
        details=lines,
    )


# ────────────────────────────────────────
# 메인 보고서 생성
# ────────────────────────────────────────
def generate_report(
    pillars: FourPillars,
    ten_gods: list[TenGodEntry],
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    sinsal: list[SinsalEntry],
    interactions: list[InteractionEntry],
    wealth: WealthResult,
    radar: RadarResult,
    daeun: list[DaeunEntry],
    life_events: list[LifeEvent],
    gender: str = "남",
    birth_info: dict | None = None,
    # ── 전문가 분석 데이터 (선택) ──
    day_stem_traits: str = "",
    elem_info: dict | None = None,
    twelve_stages: list[dict] | None = None,
    gongmang: dict | None = None,
    johu: dict | None = None,
    naeum: dict | None = None,
    palace: list[dict] | None = None,
    interpretation: dict | None = None,
) -> SajuReport:
    """성패 관점 종합 보고서 생성."""
    sections: list[ReportSection] = []

    # 개별 섹션
    sec_personality = _section_personality(pillars, strength, ten_gods, pattern)
    sections.append(sec_personality)

    sec_wealth = _section_wealth(wealth)
    sections.append(sec_wealth)

    sec_career = _section_career(pillars, ten_gods, pattern, strength, radar)
    sections.append(sec_career)

    sec_romance = _section_romance(pillars, ten_gods, sinsal, gender, interactions)
    sections.append(sec_romance)

    sec_marriage = _section_marriage(pillars, ten_gods, sinsal, gender, interactions, daeun)
    sections.append(sec_marriage)

    sec_children = _section_children(pillars, ten_gods, gender, interactions)
    sections.append(sec_children)

    sec_aptitude = _section_aptitude(pillars, pattern, ten_gods, strength)
    sections.append(sec_aptitude)

    # 총평 (다른 섹션 점수 기반)
    sec_overall = _section_overall(sections, strength, pattern, yongshin, pillars)

    return SajuReport(
        birth_info=birth_info or {},
        four_pillars_summary=f"{pillars.year.stem}{pillars.year.branch} {pillars.month.stem}{pillars.month.branch} {pillars.day.stem}{pillars.day.branch} {pillars.hour.stem}{pillars.hour.branch}",
        overall=sec_overall,
        sections=sections,
        # ── 전문가 분석 데이터 ──
        four_pillars=pillars,
        strength=strength,
        pattern=pattern,
        yongshin=yongshin,
        ten_gods=ten_gods,
        interactions=interactions,
        sinsal=sinsal,
        daeun=daeun,
        radar=radar,
        day_stem_traits=day_stem_traits,
        elem_info=elem_info or {},
        twelve_stages=twelve_stages or [],
        gongmang=gongmang or {},
        johu=johu or {},
        naeum=naeum or {},
        palace=palace or [],
        interpretation=interpretation or {},
    )
