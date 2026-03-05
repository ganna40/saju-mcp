"""교차 분석 엔진 — 독립 모듈 결과를 교차 분석하여 인과관계 인사이트 생성."""
from __future__ import annotations

from .constants import (
    STEM_OHAENG, TEN_GOD_CATEGORIES, GENERATING, CONTROLLING,
    DAY_STEM_METAPHORS,
)
from .models import (
    FourPillars, StrengthResult, PatternResult, YongshinResult,
    TenGodEntry, InteractionEntry, SinsalEntry, WealthResult,
    DaeunEntry, CrossInsight,
)


def analyze_cross_patterns(
    pillars: FourPillars,
    ten_gods: list[TenGodEntry],
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    interactions: list[InteractionEntry],
    sinsal: list[SinsalEntry],
    wealth: WealthResult,
    daeun: list[DaeunEntry],
    gender: str = "남",
) -> list[CrossInsight]:
    """모든 분석 결과를 교차 분석하여 인사이트 리스트 반환."""
    insights: list[CrossInsight] = []

    # 십신 카테고리별 카운트
    cats: dict[str, int] = {}
    tg_names: set[str] = set()
    for tg in ten_gods:
        cats[tg.category] = cats.get(tg.category, 0) + 1
        tg_names.add(tg.ten_god)

    day_elem = STEM_OHAENG.get(pillars.day.stem, "")

    # ── 패턴 탐지 ──
    insights.extend(_check_siksang_saengjae(cats, tg_names, strength, yongshin, wealth))
    insights.extend(_check_gwanin_sangsaeng(cats, tg_names, strength, pattern))
    insights.extend(_check_sanggwan_gyeongwan(cats, tg_names, strength, gender))
    insights.extend(_check_pyeonin_dosik(cats, tg_names, strength, yongshin))
    insights.extend(_check_bigeop_jaengjae(cats, tg_names, strength, wealth))
    insights.extend(_check_salin_sangsaeng(cats, tg_names, strength))
    insights.extend(_check_jaegwan_ssangmi(pillars, ten_gods, gender))
    insights.extend(_check_strength_pattern_tension(strength, pattern, yongshin))
    insights.extend(_check_interaction_palace(interactions, pillars))
    insights.extend(_check_sinsal_clusters(sinsal, strength, pattern))
    insights.extend(_check_daeun_flow(daeun, yongshin, strength, pillars))

    # 우선순위 정렬
    insights.sort(key=lambda x: x.priority)
    return insights


# ── 1. 식상생재 구조 ──
def _check_siksang_saengjae(cats, tg_names, strength, yongshin, wealth):
    insights = []
    has_siksang = cats.get("식상", 0) >= 1
    has_jaeseong = cats.get("재성", 0) >= 1

    if has_siksang and has_jaeseong:
        chain = "식상(아이디어/기술)이 재성(돈)을 생하는 구조"
        if strength.score >= 55:
            chain += " → 신강하니 체력도 뒷받침되어 실행력까지 갖춤"
            impact = "콘텐츠 제작, 교육, 기술 기반 사업에서 돈을 벌 수 있는 최적의 구조. 본인 재능을 상품화하는 것이 핵심."
            priority = 1
        elif strength.score <= 45:
            chain += " → 신약하여 아이디어는 있으나 체력/실행력이 부족"
            impact = "재능은 있지만 혼자 다 하면 번아웃. 파트너나 조직의 지원 속에서 기술력을 발휘해야 함."
            priority = 2
        else:
            chain += " → 중화 상태로 균형잡힌 식상생재"
            impact = "아이디어와 실행력이 균형잡혀 있어 꾸준한 수입 창출 가능."
            priority = 2

        warning = ""
        if "편인" in tg_names:
            warning = "편인이 식상을 극하여(편인도식) 식상생재 구조를 방해할 수 있음. 창의적 표현이 억눌리는 시기 주의."

        insights.append(CrossInsight(
            pattern_name="식상생재(食傷生財)",
            evidence=[
                f"식상 {cats.get('식상', 0)}개",
                f"재성 {cats.get('재성', 0)}개",
                f"신강도 {strength.score}점({strength.label})",
            ],
            causal_chain=chain,
            life_impact=impact,
            warning=warning,
            priority=priority,
        ))
    return insights


# ── 2. 관인상생 구조 ──
def _check_gwanin_sangsaeng(cats, tg_names, strength, pattern):
    insights = []
    has_gwanseong = cats.get("관성", 0) >= 1
    has_inseong = cats.get("인성", 0) >= 1

    if has_gwanseong and has_inseong:
        chain = "관성(직장/시험)이 인성(학습/자격)을 생하고, 인성이 일간을 도와주는 순환 구조"
        if strength.score <= 45:
            chain += " → 신약한 일간에게 인성이 힘을 주니, 공부하면 할수록 인정받는 구조"
            impact = "시험, 자격증, 학위 취득에 매우 유리. 공무원, 교수, 연구직, 전문직에서 성공할 확률이 높음."
            priority = 1
        else:
            chain += " → 신강하여 관성의 압력을 견딜 수 있으니, 조직에서 빠르게 승진하는 타입"
            impact = "관리직, 임원급으로 올라가는 구조. 조직 내에서 인정받고 승진하는 데 유리."
            priority = 2

        warning = ""
        if "상관" in tg_names:
            warning = "상관이 관성을 극하여(상관견관) 관인상생 구조가 불안정해질 수 있음. 윗사람과의 갈등 주의."

        insights.append(CrossInsight(
            pattern_name="관인상생(官印相生)",
            evidence=[
                f"관성 {cats.get('관성', 0)}개",
                f"인성 {cats.get('인성', 0)}개",
                f"신강도 {strength.score}점",
            ],
            causal_chain=chain,
            life_impact=impact,
            warning=warning,
            priority=priority,
        ))
    return insights


# ── 3. 상관견관 구조 ──
def _check_sanggwan_gyeongwan(cats, tg_names, strength, gender):
    insights = []
    if "상관" in tg_names and "정관" in tg_names:
        chain = "상관이 정관을 극하는 구조 → 자유로운 표현 욕구가 규범/질서와 충돌"

        if gender == "여":
            chain += " → 여성 사주에서 상관견관은 남편성(정관)을 극하므로 연애/결혼에서 갈등 패턴"
            impact = "무의식적으로 남자를 평가하고 까다롭게 구는 패턴이 있을 수 있음. 연애 시작은 잘 되는데 유지가 어려운 구조."
            warning = "남자에게 맞추는 게 아니라, '이 사람의 장점을 인정하는 연습'이 필요."
            priority = 1
        else:
            impact = "직장에서 윗사람과 부딪히기 쉬운 구조. '왜 이렇게 해야 하는데?'라는 생각이 자주 들고, 부당한 지시에 참지 못함."
            warning = "감정적 반발 대신 실력으로 증명하는 전략이 필요. 조직보다 전문직/프리랜서가 맞을 수 있음."
            priority = 2

        insights.append(CrossInsight(
            pattern_name="상관견관(傷官見官)",
            evidence=["상관 있음", "정관 있음", f"성별: {gender}"],
            causal_chain=chain,
            life_impact=impact,
            warning=warning,
            priority=priority,
        ))
    return insights


# ── 4. 편인도식 구조 ──
def _check_pyeonin_dosik(cats, tg_names, strength, yongshin):
    insights = []
    if "편인" in tg_names and "식신" in tg_names:
        chain = "편인이 식신을 극하는 구조(편인도식/효신탈식) → 하고 싶은 말, 표현하고 싶은 것이 억눌림"
        impact = "창의적 재능이 있는데 발휘를 못하는 답답함. 직장에서 자기 의견을 말 못하고 삼키는 패턴. 속으로 쌓다가 한꺼번에 터지기도."
        warning = "편인을 제어하는 재성(돈/현실)이 있으면 완화됨. 현실적 목표를 세우면 편인이 학습 에너지로 전환."
        priority = 1 if cats.get("재성", 0) == 0 else 2

        insights.append(CrossInsight(
            pattern_name="편인도식(偏印倒食)",
            evidence=[
                "편인 있음", "식신 있음",
                f"재성 {cats.get('재성', 0)}개 ({'제어 없음' if cats.get('재성', 0) == 0 else '재성으로 완화'})",
            ],
            causal_chain=chain,
            life_impact=impact,
            warning=warning,
            priority=priority,
        ))
    return insights


# ── 5. 비겁쟁재 구조 ──
def _check_bigeop_jaengjae(cats, tg_names, strength, wealth):
    insights = []
    bigeop = cats.get("비겁", 0)
    jaeseong = cats.get("재성", 0)

    if bigeop >= 3 and jaeseong >= 1:
        chain = f"비겁이 {bigeop}개로 매우 강한데 재성도 있음 → 돈은 벌지만 경쟁자가 빼앗아가는 구조"
        impact = "동업하면 돈 때문에 싸우게 되고, 친구한테 돈 빌려주면 못 받음. 보증도 위험. 혼자 벌고 혼자 관리하는 게 최선."
        warning = "절대 동업/보증/공동투자 금지. 돈은 혼자 벌고 혼자 쓸 것."
        priority = 1

        insights.append(CrossInsight(
            pattern_name="비겁쟁재(比劫爭財)",
            evidence=[
                f"비겁 {bigeop}개", f"재성 {jaeseong}개",
                f"재물등급 {wealth.grade}",
            ],
            causal_chain=chain,
            life_impact=impact,
            warning=warning,
            priority=priority,
        ))
    elif "겁재" in tg_names and jaeseong >= 1:
        insights.append(CrossInsight(
            pattern_name="겁재극재(劫財剋財)",
            evidence=["겁재 있음", f"재성 {jaeseong}개"],
            causal_chain="겁재가 재성을 빼앗으려 함 → 주변 사람에 의한 금전 손실 가능성",
            life_impact="가까운 사람(친구, 형제)에게 돈을 잃거나, 충동 소비 패턴이 있을 수 있음.",
            warning="돈 관련 인간관계에 선을 명확히 그을 것.",
            priority=3,
        ))
    return insights


# ── 6. 살인상생 구조 ──
def _check_salin_sangsaeng(cats, tg_names, strength):
    insights = []
    if "편관" in tg_names and "편인" in tg_names:
        chain = "편관(위기/압박)이 편인(학습/지혜)을 생하는 구조 → 위기를 겪을수록 지혜가 쌓이는 타입"
        if strength.score >= 55:
            impact = "위기 상황에서 오히려 빛나는 사람. 군인, 경찰, 의사, 법조인 등 위기 대응 직종에서 능력 발휘."
            priority = 2
        else:
            impact = "편관의 압박을 편인이 학습으로 전환하지만, 신약하면 스트레스가 건강에 영향."
            priority = 3

        insights.append(CrossInsight(
            pattern_name="살인상생(殺印相生)",
            evidence=["편관 있음", "편인 있음", f"신강도 {strength.score}점"],
            causal_chain=chain,
            life_impact=impact,
            warning="편관의 에너지가 너무 강하면 편인이 감당 못 함. 적절한 스트레스 관리 필요.",
            priority=priority,
        ))
    return insights


# ── 7. 재관쌍미 (진술축미에 재성+관성이 묻힘) ──
def _check_jaegwan_ssangmi(pillars, ten_gods, gender):
    insights = []
    # 일지가 토(진/술/축/미)이고, 지장간에 재성+관성이 함께 있는지 체크
    il_ji = pillars.day.branch
    if il_ji in ("진", "술", "축", "미"):
        ilji_tgs = [tg for tg in ten_gods if tg.position == "일지"]
        has_jae_in_hidden = False
        has_gwan_in_hidden = False
        for hs in pillars.day.hidden_stems:
            # 지장간의 각 천간이 일간 기준 재성/관성인지 확인
            from .ten_gods import calc_ten_god
            tg = calc_ten_god(pillars.day.stem, hs["stem"])
            cat = TEN_GOD_CATEGORIES.get(tg, "")
            if cat == "재성":
                has_jae_in_hidden = True
            if cat == "관성":
                has_gwan_in_hidden = True

        if has_jae_in_hidden and has_gwan_in_hidden:
            chain = "일지(배우자궁) 토 지장간에 재성과 관성이 함께 숨어있음 → 배우자궁이 복잡한 구조"
            if gender == "남":
                impact = "배우자궁에 여자(재성)와 직장(관성)이 함께 있어, 일과 가정 사이에서 갈등. 워커홀릭이 되거나 배우자와 시간 다툼."
            else:
                impact = "배우자궁에 남자(관성)와 돈(재성)이 함께 있어, 경제적으로 능력 있는 배우자를 만나지만 바쁜 사람."
            insights.append(CrossInsight(
                pattern_name="재관혼잡(財官混雜) - 배우자궁",
                evidence=[f"일지 {il_ji}(토)", "지장간에 재성+관성 공존"],
                causal_chain=chain,
                life_impact=impact,
                warning="배우자와의 역할 분담을 명확히 하고, 서로의 영역을 존중하는 것이 핵심.",
                priority=3,
            ))
    return insights


# ── 8. 신강/약 × 격국 긴장관계 ──
def _check_strength_pattern_tension(strength, pattern, yongshin):
    insights = []
    score = strength.score

    if pattern.is_special:
        # 종격은 흐름을 따라가야
        chain = f"{pattern.name}(종격) → 강한 기운을 거스르지 말고 따라가야(從) 성공하는 구조"
        impact = "일반적 사주 해석법과 반대로 적용해야 함. 용신도 일반격과 반대."
        insights.append(CrossInsight(
            pattern_name=f"종격 운용법 — {pattern.name}",
            evidence=[f"격국: {pattern.name}", f"특수격: {pattern.is_special}"],
            causal_chain=chain,
            life_impact=impact,
            warning="종격인데 억지로 균형을 맞추려 하면 오히려 안 좋음. 강한 쪽을 더 밀어줘야 함.",
            priority=1,
        ))
    elif score >= 70:
        chain = f"매우 신강({score}점)한 {pattern.name} → 에너지가 넘쳐서 출구가 없으면 내부 폭발"
        impact = "가만히 있으면 안 되는 사주. 운동, 사업, 창작 등 에너지를 쏟을 곳이 반드시 필요."
        insights.append(CrossInsight(
            pattern_name="극신강 에너지 관리",
            evidence=[f"신강도 {score}점", f"격국 {pattern.name}"],
            causal_chain=chain,
            life_impact=impact,
            warning="에너지 출구 없이 직장에만 갇히면 스트레스, 화병, 폭음 등으로 나타남.",
            priority=2,
        ))
    elif score <= 30:
        chain = f"매우 신약({score}점)한 {pattern.name} → 혼자 힘으로는 격국의 장점을 살리기 어려움"
        impact = "든든한 후원자(인성), 함께하는 동료(비겁)가 반드시 필요. 혼자 사업하면 체력이 버티지 못함."
        insights.append(CrossInsight(
            pattern_name="극신약 지원 필요",
            evidence=[f"신강도 {score}점", f"격국 {pattern.name}"],
            causal_chain=chain,
            life_impact=impact,
            warning="무리하면 건강이 먼저 무너짐. 인성(학습/자격) 대운 때 기반을 잡는 전략.",
            priority=2,
        ))

    return insights


# ── 9. 합충 × 궁위 교차 ──
def _check_interaction_palace(interactions, pillars):
    insights = []
    palace_map = {
        "년간": "조상/어린시절", "년지": "조상/어린시절",
        "월간": "부모/사회", "월지": "부모/사회",
        "일간": "본인", "일지": "배우자",
        "시간": "자녀/말년", "시지": "자녀/말년",
    }

    for inter in interactions:
        if inter.type == "충" and len(inter.positions) >= 2:
            palaces = [palace_map.get(p, p) for p in inter.positions]
            unique_palaces = list(set(palaces))
            if len(unique_palaces) >= 2:
                chain = f"{inter.description} → {unique_palaces[0]}과 {unique_palaces[1]} 영역이 충돌하는 구조"
                impact = f"인생에서 {unique_palaces[0]}과 {unique_palaces[1]} 사이의 갈등이 반복되는 패턴."

                insights.append(CrossInsight(
                    pattern_name=f"궁위 충돌 — {'/'.join(unique_palaces)}",
                    evidence=[inter.description] + inter.positions,
                    causal_chain=chain,
                    life_impact=impact,
                    warning="충은 변화의 에너지이기도 함. 정체된 상황을 깨뜨리는 원동력으로 활용할 것.",
                    priority=3,
                ))
    return insights


# ── 10. 신살 클러스터 (여러 신살이 겹칠 때) ──
def _check_sinsal_clusters(sinsal, strength, pattern):
    insights = []
    names = {s.name for s in sinsal}

    # 도화살 + 역마살 = 이동하며 인연을 만남
    if "도화살" in names and "역마살" in names:
        insights.append(CrossInsight(
            pattern_name="도화역마(桃花驛馬)",
            evidence=["도화살", "역마살"],
            causal_chain="이성 매력(도화)과 이동 에너지(역마)가 합쳐짐 → 여행/출장 중 인연을 만나거나, 먼 곳의 이성과 인연",
            life_impact="해외 인연, 출장 중 만남, 원거리 연애의 가능성이 높음.",
            warning="도화 에너지가 강하면 여러 곳에서 인연이 생겨 복잡해질 수 있음.",
            priority=3,
        ))

    # 화개살 + 편인 = 깊은 정신세계
    if "화개살" in names and any(s.name == "귀문관살" for s in sinsal):
        insights.append(CrossInsight(
            pattern_name="화개귀문(華蓋鬼門)",
            evidence=["화개살", "귀문관살"],
            causal_chain="영적 감수성(화개)과 예민한 직감(귀문)이 합쳐짐 → 남들이 못 느끼는 것을 느끼는 사람",
            life_impact="상담, 심리, 종교, 예술 분야에서 탁월한 감각. 다만 예민함으로 인한 수면 장애나 스트레스 가능.",
            warning="명상, 운동 등으로 과민한 에너지를 정리하는 습관이 필요.",
            priority=3,
        ))

    # 양인살 + 백호살 = 사고/수술 주의
    if "양인살" in names and "백호대살" in names:
        insights.append(CrossInsight(
            pattern_name="양인백호(羊刃白虎)",
            evidence=["양인살", "백호대살"],
            causal_chain="강한 결단력(양인)과 돌발 에너지(백호)가 합쳐짐 → 과감하지만 사고 위험도 높음",
            life_impact="외과의사, 군인, 소방관 등 위험을 다루는 직업에 적합. 일반 직장인이면 교통사고, 수술 수가 있음.",
            warning="고위험 활동(야간운전, 익스트림스포츠) 주의. 보험 필수.",
            priority=2,
        ))

    return insights


# ── 11. 대운 흐름 분석 ──
def _check_daeun_flow(daeun, yongshin, strength, pillars):
    insights = []
    if not daeun:
        return insights

    # 용신 대운 vs 기신 대운 흐름 파악
    yong_elem = yongshin.yongshin
    favorable = set(yongshin.favorable_elements)
    unfavorable = set(yongshin.unfavorable_elements)

    golden_periods = []
    danger_periods = []

    for d in daeun:
        d_elems = {d.stem_ohaeng, d.branch_ohaeng} - {""}
        if d_elems & favorable:
            golden_periods.append(f"{d.age_start}~{d.age_end}세({d.stem}{d.branch})")
        elif d_elems & unfavorable:
            danger_periods.append(f"{d.age_start}~{d.age_end}세({d.stem}{d.branch})")

    if golden_periods:
        insights.append(CrossInsight(
            pattern_name="인생 전성기 대운",
            evidence=[f"용신: {yong_elem}"] + golden_periods[:3],
            causal_chain=f"용신({yong_elem}) 오행이 들어오는 대운에서 크게 발전 → {', '.join(golden_periods[:3])}",
            life_impact="이 시기에 승진, 사업 확장, 재물 획득, 좋은 인연 등 긍정적 변화가 집중됨.",
            warning="전성기라고 무리하면 안 됨. 기반을 다지는 시기로 활용.",
            priority=2,
        ))

    if danger_periods:
        insights.append(CrossInsight(
            pattern_name="주의 필요 대운",
            evidence=[f"기신: {yongshin.gishin}"] + danger_periods[:3],
            causal_chain=f"기신 오행이 강해지는 대운 → {', '.join(danger_periods[:3])}",
            life_impact="이 시기에 건강, 재물, 인간관계 문제가 생기기 쉬움.",
            warning="큰 투자, 이직, 결혼 등 중요 결정은 이 시기를 피하는 것이 좋음.",
            priority=3,
        ))

    return insights
