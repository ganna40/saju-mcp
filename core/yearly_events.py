"""연도별 구체적 사건 예측 엔진.

세운 십신 + 대운 십신 + 신살 발동 + 합충 + 용신 관계 + 연령대 + 성별을
조합하여 구체적 이벤트 시나리오와 만남의 인물 유형을 생성한다.
"""
from __future__ import annotations

from .constants import (
    TEN_GOD_CATEGORIES, PERSON_TYPE_MAP, HEALTH_WEAKNESS_BY_ELEM,
)
from .models import (
    FourPillars, DaeunEntry, SeunEntry, StrengthResult,
    YongshinResult, PatternResult, SinsalEntry, InteractionEntry,
    YearlyEvent, PersonEncounter,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


# ── 연령대 분류 ──

def _get_age_group(age: int) -> str:
    if age < 15:
        return "child"
    if age < 30:
        return "youth"
    if age < 40:
        return "early_adult"
    if age < 55:
        return "mid_adult"
    return "senior"


# ── 컨텍스트 수집 ──

class _Ctx:
    """이벤트 생성에 필요한 모든 컨텍스트."""

    def __init__(self, pillars: FourPillars, seun: SeunEntry,
                 daeun: DaeunEntry | None, strength: StrengthResult,
                 yongshin: YongshinResult, pattern: PatternResult,
                 activated_sinsal: list[SinsalEntry],
                 seun_interactions: list[InteractionEntry],
                 gender: str):
        self.pillars = pillars
        self.seun = seun
        self.daeun = daeun
        self.strength = strength
        self.yongshin = yongshin
        self.pattern = pattern
        self.gender = gender

        day_stem = pillars.day.stem

        # 세운 십신
        self.seun_stem_tg = seun.ten_god_stem or calc_ten_god(day_stem, seun.stem)
        self.seun_branch_tg = seun.ten_god_branch or calc_ten_god_for_branch(day_stem, seun.branch)
        self.seun_stem_cat = TEN_GOD_CATEGORIES.get(self.seun_stem_tg, "")
        self.seun_branch_cat = TEN_GOD_CATEGORIES.get(self.seun_branch_tg, "")
        self.seun_cats = {self.seun_stem_cat, self.seun_branch_cat} - {""}

        # 대운 십신
        self.daeun_stem_cat = ""
        self.daeun_branch_cat = ""
        self.daeun_cats: set[str] = set()
        if daeun:
            dtg_s = daeun.ten_god_stem or calc_ten_god(day_stem, daeun.stem)
            dtg_b = daeun.ten_god_branch or calc_ten_god_for_branch(day_stem, daeun.branch)
            self.daeun_stem_cat = TEN_GOD_CATEGORIES.get(dtg_s, "")
            self.daeun_branch_cat = TEN_GOD_CATEGORIES.get(dtg_b, "")
            self.daeun_cats = {self.daeun_stem_cat, self.daeun_branch_cat} - {""}

        # 신살
        self.sinsal_names = {s.name for s in activated_sinsal}

        # 합충
        self.has_chung = any(i.type == "충" for i in seun_interactions)
        self.has_hap = any(i.type == "합" for i in seun_interactions)
        self.has_hyung = any(i.type == "형" for i in seun_interactions)
        self.chung_positions: list[str] = []
        for i in seun_interactions:
            if i.type == "충":
                self.chung_positions.extend(i.positions)
        self.interactions = seun_interactions

        # 용신/기신
        seun_elems = {seun.stem_ohaeng, seun.branch_ohaeng} - {""}
        self.seun_is_yongshin = bool(seun_elems & set(yongshin.favorable_elements))
        self.seun_is_gishin = bool(seun_elems & set(yongshin.unfavorable_elements))

        # 연령대
        self.age = seun.age
        self.age_group = _get_age_group(seun.age)

        # 배우자궁 충 여부
        self.spouse_palace_chung = "일지" in self.chung_positions


# ── 직업/커리어 이벤트 ──

def _generate_career_events(ctx: _Ctx) -> list[YearlyEvent]:
    events: list[YearlyEvent] = []

    # 관인상생: 세운 관성 + 대운 인성 (or 반대)
    if ("관성" in ctx.seun_cats and "인성" in ctx.daeun_cats) or \
       ("인성" in ctx.seun_cats and "관성" in ctx.daeun_cats):
        events.append(YearlyEvent(
            category="career",
            title="시험 합격 / 승진에 매우 유리한 해",
            description="관인상생(官印相生) 구조가 형성됩니다. 공부한 것이 인정받고, 시험·승진·자격증 취득에 최적의 시기입니다. 준비해 온 것이 있다면 올해 반드시 도전하세요.",
            probability="높음",
            trigger="세운+대운 관인상생",
            advice="시험, 승진, 자격증 취득에 적극 도전하세요. 준비한 만큼 결과가 나옵니다.",
        ))

    # 세운에 관성 + 장성살
    if "관성" in ctx.seun_cats and "장성살" in ctx.sinsal_names:
        events.append(YearlyEvent(
            category="career",
            title="리더십을 발휘하는 해",
            description="관성 세운에 장성살이 발동하여, 조직에서 주도적 역할을 맡거나 승진/임명의 기회가 올 수 있습니다.",
            probability="높음",
            trigger="세운 관성 + 장성살 발동",
            advice="주어진 역할에 최선을 다하세요. 리더십이 인정받는 시기입니다.",
        ))
    elif "관성" in ctx.seun_cats and not any(e.trigger == "세운+대운 관인상생" for e in events):
        prob = "높음" if ctx.seun_is_yongshin else "중간"
        suffix = " 용신과 맞아 좋은 방향입니다." if ctx.seun_is_yongshin else ""
        events.append(YearlyEvent(
            category="career",
            title="직장/조직 관련 변화가 있는 해",
            description=f"관성 에너지가 들어옵니다. 직장 내 승진, 부서 이동, 새로운 책임 등 조직 관련 변화가 예상됩니다.{suffix}",
            probability=prob,
            trigger=f"세운 {ctx.seun_stem_tg}/{ctx.seun_branch_tg}",
            advice="조직 내 기회를 적극적으로 잡으세요." if ctx.seun_is_yongshin else "직장 변동에 대비하되, 무리한 도전은 삼가세요.",
        ))

    # 역마살 + 관성/충 → 이직/전근
    if "역마살" in ctx.sinsal_names:
        if ctx.has_chung or "관성" in ctx.seun_cats:
            reason = "충의 에너지가 겹쳐" if ctx.has_chung else "관성이 들어와"
            events.append(YearlyEvent(
                category="career",
                title="이직, 전근, 또는 업무 환경 변화",
                description=f"역마살이 발동하고 {reason} 직장 환경이 바뀔 가능성이 높습니다. 이직, 전근, 출장이 잦아지거나 업무 분야가 바뀔 수 있습니다.",
                probability="높음",
                trigger="역마살 발동 + " + ("세운 충" if ctx.has_chung else "세운 관성"),
                advice="변화를 두려워하지 마세요. 더 좋은 환경으로의 이동일 수 있습니다.",
            ))
        elif ctx.age_group in ("youth", "early_adult"):
            events.append(YearlyEvent(
                category="career",
                title="해외 출장/유학/원거리 이동 가능성",
                description="역마살이 발동하는 해입니다. 해외와 관련된 기회가 올 수 있고, 출장이 잦아지거나 원거리 이동이 있을 수 있습니다.",
                probability="중간",
                trigger="역마살 발동",
                advice="해외 관련 기회에 열린 마음을 가지세요.",
            ))

    # 식상 세운 → 창업/기술
    if "식상" in ctx.seun_cats and ctx.age_group in ("early_adult", "mid_adult"):
        events.append(YearlyEvent(
            category="career",
            title="새로운 기술/아이디어를 펼치는 해",
            description="식상의 기운이 강해져 창의적 능력이 부각됩니다. 새로운 프로젝트 시작, 사업 아이디어 구상, 기술 개발 등에 유리합니다.",
            probability="높음" if ctx.seun_is_yongshin else "중간",
            trigger=f"세운 식상({ctx.seun_stem_tg}/{ctx.seun_branch_tg})",
            advice="아이디어를 실행에 옮기세요. 표현하고 만들어내는 것이 성과로 이어집니다.",
        ))

    # 상관견관
    if ctx.seun_stem_tg == "상관" or ctx.seun_branch_tg == "상관":
        if "관성" in ctx.daeun_cats:
            events.append(YearlyEvent(
                category="career",
                title="직장 내 갈등/충돌 주의",
                description="상관견관(傷官見官) 구조가 형성됩니다. 상사와의 마찰, 조직 내 갈등, 불합리한 상황에 대한 반발이 생길 수 있습니다. 감정적 대응은 피하세요.",
                probability="높음",
                trigger="세운 상관 + 대운 관성 = 상관견관",
                advice="참을 인(忍) 자 세 번. 감정적 대응 대신 실력으로 증명하세요.",
            ))

    return events


# ── 재물 이벤트 ──

def _generate_wealth_events(ctx: _Ctx) -> list[YearlyEvent]:
    events: list[YearlyEvent] = []

    # 식상생재
    if ("재성" in ctx.seun_cats and "식상" in ctx.daeun_cats) or \
       ("식상" in ctx.seun_cats and "재성" in ctx.daeun_cats):
        events.append(YearlyEvent(
            category="wealth",
            title="새로운 수입원이 열리는 해",
            description="식상생재(食傷生財) 구조입니다. 아이디어나 기술이 돈이 되는 시기입니다. 부업, 투자, 사업 확장 등 새로운 수입원이 생길 가능성이 높습니다.",
            probability="높음",
            trigger="세운+대운 식상생재",
            advice="재능을 돈으로 바꿀 기회입니다. 부업이나 사업 아이디어를 실행하세요.",
        ))

    # 재성 세운
    if "재성" in ctx.seun_cats:
        if ctx.seun_is_yongshin:
            events.append(YearlyEvent(
                category="wealth",
                title="재물운이 상승하는 해",
                description="재성이 용신과 맞물려 재물운이 좋습니다. 급여 인상, 보너스, 투자 수익 등 금전적 이득이 기대됩니다.",
                probability="높음",
                trigger=f"세운 재성({ctx.seun_stem_tg}/{ctx.seun_branch_tg}) = 용신",
                advice="적극적으로 재테크에 나서세요. 다만 과욕은 금물입니다.",
            ))
        elif ctx.seun_is_gishin:
            events.append(YearlyEvent(
                category="wealth",
                title="예상치 못한 지출/재물 손실 주의",
                description="재성이 기신이므로 돈이 들어오는 만큼 나가기 쉬운 해입니다. 충동 구매, 투자 손실, 보증 관련 피해에 주의하세요.",
                probability="중간",
                trigger=f"세운 재성({ctx.seun_stem_tg}/{ctx.seun_branch_tg}) = 기신",
                advice="큰 투자나 보증은 삼가고, 지출 관리에 신경 쓰세요.",
            ))

    # 겁재 → 재물 유출
    if ctx.seun_stem_tg == "겁재" or ctx.seun_branch_tg == "겁재":
        events.append(YearlyEvent(
            category="wealth",
            title="재물 유출 주의 — 동업/보증 조심",
            description="겁재가 재성을 극하는 형상입니다. 친구나 지인에 의한 금전 손실, 동업 분쟁, 보증 피해가 생길 수 있습니다.",
            probability="중간",
            trigger="세운 겁재",
            advice="돈 거래는 가까운 사람일수록 더 조심하세요. 동업과 보증은 피하는 것이 좋습니다.",
        ))

    return events


# ── 연애/결혼 이벤트 ──

def _generate_love_events(ctx: _Ctx) -> list[YearlyEvent]:
    events: list[YearlyEvent] = []
    target_cat = "재성" if ctx.gender == "남" else "관성"

    # 배우자성 + 도화살
    if target_cat in ctx.seun_cats and "도화살" in ctx.sinsal_names:
        events.append(YearlyEvent(
            category="love",
            title="운명적인 이성을 만날 가능성이 높은 해",
            description="배우자성과 도화살이 동시에 작용합니다. 매력이 최고조에 달하고, 좋은 이성을 만나 깊은 인연으로 발전할 가능성이 높습니다.",
            probability="높음",
            trigger=f"세운 {target_cat} + 도화살 발동",
            advice="적극적으로 사교 활동에 나서세요. 소개팅이나 모임에서 좋은 인연을 만날 수 있습니다.",
        ))
    elif target_cat in ctx.seun_cats:
        if ctx.age_group in ("youth", "early_adult"):
            cat_label = "재성" if ctx.gender == "남" else "관성"
            events.append(YearlyEvent(
                category="love",
                title="새로운 이성 인연이 들어오는 해",
                description=f"{cat_label}이 세운에 나타나 이성 인연이 활발해집니다. 새로운 만남이 있거나 기존 관계가 진전될 수 있습니다.",
                probability="중간",
                trigger=f"세운 {target_cat}",
                advice="마음을 열고 새로운 만남을 받아들이세요.",
            ))
        elif ctx.age_group in ("early_adult", "mid_adult"):
            events.append(YearlyEvent(
                category="love",
                title="결혼을 구체적으로 생각하게 되는 해",
                description="배우자성이 들어오는 해로, 기존 교제 중이라면 결혼 이야기가 나올 수 있고, 미혼이라면 결혼을 전제로 한 만남이 생길 수 있습니다.",
                probability="중간",
                trigger=f"세운 {target_cat} + 결혼 적령기",
                advice="결혼에 대한 결심을 하기 좋은 시기입니다.",
            ))

    # 도화살만 (배우자성 없이)
    if "도화살" in ctx.sinsal_names and target_cat not in ctx.seun_cats:
        events.append(YearlyEvent(
            category="love",
            title="이성에게 매력이 높아지는 해",
            description="도화살이 발동하여 이성에게 인기가 높아집니다. 다만 배우자성 없이 도화살만 있으면, 가벼운 인연이나 유혹에 주의해야 합니다.",
            probability="중간",
            trigger="도화살 발동",
            advice="기혼자는 이성 관계에 더욱 주의하세요. 미혼자는 진지한 만남을 추구하세요.",
        ))

    # 배우자궁 충
    if ctx.spouse_palace_chung:
        events.append(YearlyEvent(
            category="love",
            title="배우자/연인과의 갈등 주의",
            description="세운이 배우자궁(일지)을 충합니다. 연인이나 배우자와 의견 충돌, 잠시 떨어져 지내는 시기, 또는 관계의 전환점이 될 수 있습니다.",
            probability="높음",
            trigger="세운↔일지 충",
            advice="대화와 양보가 중요합니다. 감정적으로 대응하면 관계가 악화됩니다.",
        ))

    return events


# ── 인간관계 이벤트 ──

def _generate_relationship_events(ctx: _Ctx) -> list[YearlyEvent]:
    events: list[YearlyEvent] = []

    # 천을귀인
    if "천을귀인" in ctx.sinsal_names:
        events.append(YearlyEvent(
            category="relationship",
            title="귀인(도움을 주는 사람)을 만나는 해",
            description="천을귀인이 발동하여 위기에서 도움을 주는 사람을 만나거나, 좋은 기회를 가져다주는 인연이 생깁니다. 어려운 상황도 누군가의 도움으로 해결됩니다.",
            probability="높음",
            trigger="천을귀인 발동",
            advice="주변 사람의 호의를 열린 마음으로 받아들이세요. 네트워킹이 중요합니다.",
        ))

    # 비겁 세운
    if "비겁" in ctx.seun_cats:
        if ctx.seun_is_gishin:
            events.append(YearlyEvent(
                category="relationship",
                title="주변 사람과의 경쟁·갈등 심화",
                description="비겁이 기신으로 작용하여 동료나 친구와의 경쟁이 심해지거나, 가까운 사람과 갈등이 생길 수 있습니다.",
                probability="중간",
                trigger="세운 비겁 = 기신",
                advice="남과 비교하지 말고 자신의 길에 집중하세요.",
            ))
        else:
            events.append(YearlyEvent(
                category="relationship",
                title="뜻이 맞는 동료·친구와의 만남",
                description="비겁의 에너지가 긍정적으로 작용하여, 함께 성장할 수 있는 동료나 친구를 만나기 좋은 해입니다.",
                probability="중간",
                trigger="세운 비겁",
                advice="팀 활동이나 동호회 참여가 좋은 인연으로 이어질 수 있습니다.",
            ))

    # 인성 + 문창/학당귀인
    if "인성" in ctx.seun_cats:
        if "문창귀인" in ctx.sinsal_names or "학당귀인" in ctx.sinsal_names:
            events.append(YearlyEvent(
                category="relationship",
                title="학업/진로에 도움을 주는 스승을 만남",
                description="인성과 학문 관련 귀인이 함께 발동합니다. 좋은 스승, 멘토, 또는 학습 동반자를 만나 크게 성장하는 시기입니다.",
                probability="높음",
                trigger="세운 인성 + 문창/학당귀인 발동",
                advice="배움에 투자하세요. 강의, 세미나, 독서 모임에서 귀인을 만날 수 있습니다.",
            ))

    return events


# ── 건강 이벤트 ──

def _generate_health_events(ctx: _Ctx) -> list[YearlyEvent]:
    events: list[YearlyEvent] = []

    # 기신 세운
    if ctx.seun_is_gishin:
        weak_elem = ctx.seun.stem_ohaeng if ctx.seun.stem_ohaeng in ctx.yongshin.unfavorable_elements else ctx.seun.branch_ohaeng
        weakness = HEALTH_WEAKNESS_BY_ELEM.get(weak_elem, "전반적인 건강 관리에 신경 쓸 것")
        first_part = weakness.split(",")[0] if "," in weakness else weakness.split(".")[0]
        events.append(YearlyEvent(
            category="health",
            title=f"건강 주의 — {first_part}",
            description=f"세운 오행이 기신이므로 건강에 신호등이 켜지는 해입니다. {weakness}",
            probability="중간",
            trigger=f"세운 {weak_elem} = 기신",
            advice="정기 건강검진을 받고, 해당 장기에 좋은 음식과 생활습관을 유지하세요.",
        ))

    # 백호대살 + 충
    if "백호대살" in ctx.sinsal_names and ctx.has_chung:
        events.append(YearlyEvent(
            category="health",
            title="사고/수술 가능성 — 안전에 각별히 주의",
            description="백호대살이 발동하고 충의 에너지가 겹칩니다. 교통사고, 부상, 수술 등 신체에 큰 영향을 주는 사건이 있을 수 있습니다.",
            probability="중간",
            trigger="백호대살 발동 + 세운 충",
            advice="위험한 활동, 야간 운전, 무리한 운동을 피하세요. 안전벨트, 보험 확인.",
        ))

    # 장년기 + 관성
    if ctx.age_group in ("mid_adult", "senior") and "관성" in ctx.seun_cats:
        events.append(YearlyEvent(
            category="health",
            title="스트레스/과로로 인한 건강 악화 주의",
            description="관성이 강하게 작용하는 해로, 업무 스트레스가 건강을 해칠 수 있습니다. 특히 혈압, 심장, 소화기 관련 문제에 주의하세요.",
            probability="중간",
            trigger=f"세운 관성 + {ctx.age_group}",
            advice="무리하지 말고, 정기적인 운동과 충분한 휴식을 취하세요.",
        ))

    return events


# ── 변동/변화 이벤트 ──

def _generate_change_events(ctx: _Ctx) -> list[YearlyEvent]:
    events: list[YearlyEvent] = []

    # 충 + 역마살
    if ctx.has_chung and "역마살" in ctx.sinsal_names:
        events.append(YearlyEvent(
            category="change",
            title="삶의 큰 전환점 — 이사, 이직, 환경 변화",
            description="충과 역마살이 동시에 작용하여 현재 환경이 크게 바뀌는 해입니다. 이사, 이직, 해외 이동, 또는 생활 방식의 대전환이 예상됩니다.",
            probability="높음",
            trigger="세운 충 + 역마살 발동",
            advice="변화를 거부하면 오히려 더 힘들어집니다. 주도적으로 변화를 이끌어가세요.",
        ))
    elif ctx.has_chung:
        chung_details = [i.description for i in ctx.interactions if i.type == "충"]
        positions_hit = set()
        for i in ctx.interactions:
            if i.type == "충":
                positions_hit.update(i.positions)
        context = ""
        if "월지" in positions_hit:
            context = "월주(직장/사회)에 충이 들어와 직장 환경 변화가 예상됩니다."
        elif "년지" in positions_hit:
            context = "년주(가문/외부환경)에 충이 들어와 가정 환경이나 사회적 변화가 있을 수 있습니다."
        elif "일지" in positions_hit:
            context = "일주(배우자궁/자기자신)에 충이 들어와 개인적 변동이 있을 수 있습니다."
        elif "시지" in positions_hit:
            context = "시주(자녀궁/미래)에 충이 들어와 자녀 관련 변화나 미래 계획의 수정이 있을 수 있습니다."
        events.append(YearlyEvent(
            category="change",
            title="충(衝)으로 인한 변동이 있는 해",
            description=f"세운이 원국과 충을 이룹니다. {context} 기존 상황이 흔들리거나 갑작스러운 변화가 생길 수 있습니다.",
            probability="높음",
            trigger="; ".join(chung_details) if chung_details else "세운 충",
            advice="변화에 대비하되, 감정적 결정은 삼가세요.",
        ))

    # 형 → 법적 문제/시련
    if ctx.has_hyung:
        events.append(YearlyEvent(
            category="change",
            title="법적 분쟁, 계약 문제, 또는 시련 가능성",
            description="형(刑)의 에너지가 작용하여 법적 분쟁, 계약 관련 문제, 또는 인간관계에서 오는 고통이 있을 수 있습니다.",
            probability="중간",
            trigger="세운↔원국 형",
            advice="계약서를 꼼꼼히 확인하고, 법적 문제에 미리 대비하세요.",
        ))

    # 겁살
    if "겁살" in ctx.sinsal_names:
        events.append(YearlyEvent(
            category="change",
            title="과감한 결단을 내리게 되는 해",
            description="겁살이 발동하여 모험적인 결정을 내리게 될 수 있습니다. 창업, 대출, 이민, 큰 투자 등 인생의 중요한 결단이 있을 수 있습니다.",
            probability="중간",
            trigger="겁살 발동",
            advice="용기는 좋지만, 철저한 준비와 계획이 뒷받침되어야 합니다.",
        ))

    # 합 (충 없을 때)
    if ctx.has_hap and not ctx.has_chung:
        hap_details = [i.description for i in ctx.interactions if i.type == "합"]
        events.append(YearlyEvent(
            category="change",
            title="안정과 결합의 해 — 좋은 인연·계약·합의",
            description="세운이 원국과 합을 이루어 안정적인 에너지가 흐릅니다. 결혼, 계약, 합의, 파트너십 등 '합쳐지는' 일이 생기기 좋습니다.",
            probability="중간",
            trigger="; ".join(hap_details) if hap_details else "세운 합",
            advice="좋은 제안이 오면 적극적으로 수용하세요.",
        ))

    return events


# ── 만남의 인물 유형 ──

def _generate_person_encounters(ctx: _Ctx) -> list[PersonEncounter]:
    encounters: list[PersonEncounter] = []
    seen: set[str] = set()

    for tg in [ctx.seun_stem_tg, ctx.seun_branch_tg]:
        if tg in seen or tg not in PERSON_TYPE_MAP:
            continue
        seen.add(tg)
        info = PERSON_TYPE_MAP[tg]
        is_positive = ctx.seun_is_yongshin
        context = info["context_positive"] if is_positive else info["context_negative"]
        influence = "긍정적" if is_positive else ("부정적" if ctx.seun_is_gishin else "중립")

        encounters.append(PersonEncounter(
            ten_god=tg,
            person_type=info["type"],
            context=context,
            influence=influence,
        ))

    return encounters


# ── 종합 운세 판단 ──

def _determine_overall_fortune(ctx: _Ctx, events: list[YearlyEvent]) -> str:
    positive_count = sum(
        1 for e in events
        if e.probability == "높음"
        and "주의" not in e.title and "갈등" not in e.title and "손실" not in e.title
    )
    negative_count = sum(
        1 for e in events
        if "주의" in e.title or "갈등" in e.title or "손실" in e.title or "분쟁" in e.title
    )
    change_count = sum(1 for e in events if e.category == "change")

    if ctx.seun_is_yongshin and positive_count >= 2:
        return "길한 해 — 용신이 작용하여 전반적으로 좋은 흐름"
    if ctx.seun_is_gishin and negative_count >= 2:
        return "주의가 필요한 해 — 기신이 작용하여 조심해야 할 시기"
    if change_count >= 2:
        return "변화의 해 — 환경이 크게 바뀌는 전환점"
    if ctx.has_chung:
        return "변동의 해 — 충(衝)의 에너지로 기존 상황이 흔들림"
    if ctx.has_hap:
        return "안정의 해 — 합(合)의 에너지로 좋은 인연과 결합"
    if positive_count > negative_count:
        return "보통 이상 — 좋은 기회를 잘 잡으면 발전하는 해"
    if negative_count > positive_count:
        return "보통 이하 — 무리하지 않고 내실을 다지는 해"
    return "평탄한 해 — 큰 변동 없이 꾸준히 나아가는 시기"


# ── 메인 함수 ──

def predict_yearly_events(
    pillars: FourPillars,
    seun: SeunEntry,
    daeun: DaeunEntry | None,
    strength: StrengthResult,
    yongshin: YongshinResult,
    pattern: PatternResult,
    activated_sinsal: list[SinsalEntry],
    seun_interactions: list[InteractionEntry],
    gender: str = "남",
) -> tuple[list[YearlyEvent], list[PersonEncounter], str]:
    """연도별 구체적 사건 예측.

    Returns:
        (yearly_events, person_encounters, overall_fortune)
    """
    ctx = _Ctx(pillars, seun, daeun, strength, yongshin, pattern,
               activated_sinsal, seun_interactions, gender)

    events: list[YearlyEvent] = []
    events.extend(_generate_career_events(ctx))
    events.extend(_generate_wealth_events(ctx))
    events.extend(_generate_love_events(ctx))
    events.extend(_generate_relationship_events(ctx))
    events.extend(_generate_health_events(ctx))
    events.extend(_generate_change_events(ctx))

    encounters = _generate_person_encounters(ctx)
    overall = _determine_overall_fortune(ctx, events)

    return events, encounters, overall
