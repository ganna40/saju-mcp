"""Pydantic 반환 스키마 — 모든 MCP 도구의 입출력 모델."""
from __future__ import annotations

from pydantic import BaseModel, Field


# ── 공통 입력 ──
class BirthInfo(BaseModel):
    year: int = Field(..., ge=1900, le=2100, description="생년 (양력)")
    month: int = Field(..., ge=1, le=12, description="생월")
    day: int = Field(..., ge=1, le=31, description="생일")
    hour: int = Field(default=12, ge=0, le=23, description="생시 (0~23, 기본 12시)")
    minute: int = Field(default=0, ge=0, le=59, description="생분 (기본 0)")
    gender: str = Field(default="남", description="성별 (남/여)")


# ── 사주 기본 ──
class Pillar(BaseModel):
    stem: str = Field(..., description="천간 (한글)")
    branch: str = Field(..., description="지지 (한글)")
    stem_hanja: str = ""
    branch_hanja: str = ""
    stem_ohaeng: str = ""
    branch_ohaeng: str = ""
    hidden_stems: list[dict] = Field(default_factory=list, description="지장간 [{stem, ohaeng, weight}]")


class FourPillars(BaseModel):
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar


class TenGodEntry(BaseModel):
    position: str = Field(..., description="위치 (년간/년지/월간/월지/일지/시간/시지)")
    char: str = Field(..., description="해당 글자")
    ten_god: str = Field(..., description="십신 이름")
    category: str = Field(..., description="카테고리 (비겁/식상/재성/관성/인성)")


class DaeunEntry(BaseModel):
    age_start: int
    age_end: int
    stem: str
    branch: str
    stem_ohaeng: str
    branch_ohaeng: str
    ten_god_stem: str = ""
    ten_god_branch: str = ""


class SeunEntry(BaseModel):
    year: int
    age: int
    stem: str
    branch: str
    stem_ohaeng: str = ""
    branch_ohaeng: str = ""
    ten_god_stem: str = ""
    ten_god_branch: str = ""


# ── 격국/신강 ──
class StrengthResult(BaseModel):
    score: float = Field(..., description="신강/신약 점수 0~100 (50 이상 신강)")
    label: str = Field(..., description="신강/중화/신약")
    day_stem: str
    day_stem_ohaeng: str
    ohaeng_scores: dict[str, float] = Field(default_factory=dict, description="오행별 점수")
    helping_elements: list[str] = Field(default_factory=list, description="도와주는 오행")
    draining_elements: list[str] = Field(default_factory=list, description="빼앗는 오행")


class PatternResult(BaseModel):
    name: str = Field(..., description="격국 이름")
    description: str = ""
    traits: str = ""
    careers: list[str] = Field(default_factory=list)
    is_special: bool = Field(default=False, description="특수격 여부 (종격 등)")


class YongshinResult(BaseModel):
    yongshin: str = Field(..., description="용신 오행")
    yongshin_reason: str = ""
    heeshin: str = Field(default="", description="희신 오행")
    gishin: str = Field(default="", description="기신 오행")
    gushin: str = Field(default="", description="구신 오행")
    favorable_elements: list[str] = Field(default_factory=list)
    unfavorable_elements: list[str] = Field(default_factory=list)


# ── 신살 ──
class SinsalEntry(BaseModel):
    name: str = Field(..., description="신살 이름")
    description: str = ""
    positions: list[str] = Field(default_factory=list, description="발견된 위치")
    activation_periods: list[str] = Field(default_factory=list, description="대운/세운 발동 시기")


# ── 합충형파해 ──
class InteractionEntry(BaseModel):
    type: str = Field(..., description="합/충/형/파/해")
    subtype: str = Field(default="", description="세부 (육합/삼합/육충 등)")
    positions: list[str] = Field(default_factory=list, description="관여 위치")
    elements: list[str] = Field(default_factory=list, description="관여 글자")
    result: str = Field(default="", description="결과 (오행변환 등)")
    description: str = ""


# ── 재물그릇 ──
class WealthItem(BaseModel):
    category: str
    label: str
    score: float
    max_score: float
    description: str = ""


class WealthResult(BaseModel):
    total_score: float = Field(..., description="총점 (0~100)")
    grade: str = Field(..., description="등급 (S/A/B+/B/C/D/F)")
    grade_label: str = ""
    items: list[WealthItem] = Field(default_factory=list)
    peak_periods: list[str] = Field(default_factory=list, description="재물 전성기")
    risk_periods: list[str] = Field(default_factory=list, description="재물 위험기")


# ── 인생이벤트 ──
class LifeEvent(BaseModel):
    age_range: str
    period: str = Field(default="", description="대운 간지")
    events: list[str] = Field(default_factory=list, description="예상 이벤트")
    key_element: str = ""
    favorability: str = Field(default="보통", description="길/보통/흉")


# ── 레이더 ──
class RadarResult(BaseModel):
    axes: dict[str, float] = Field(default_factory=dict, description="6축 점수 (0~100)")
    strongest: str = ""
    weakest: str = ""


# ── 연도별 이벤트 예측 ──
class YearlyEvent(BaseModel):
    category: str = Field(..., description="카테고리 (career/wealth/relationship/love/health/change)")
    title: str = Field(..., description="이벤트 제목 (예: 승진 가능성 높음)")
    description: str = Field(default="", description="구체적 설명 2~3문장")
    probability: str = Field(default="중간", description="확률 (높음/중간/낮음)")
    trigger: str = Field(default="", description="근거 (예: 세운 정관 + 대운 인성 = 관인상생)")
    advice: str = Field(default="", description="조언")


class PersonEncounter(BaseModel):
    ten_god: str = Field(..., description="세운 십신")
    person_type: str = Field(..., description="인물 유형 (예: 신뢰할 수 있는 리더)")
    context: str = Field(default="", description="만남의 맥락")
    influence: str = Field(default="중립", description="영향 (긍정적/부정적/중립)")


# ── 궁합 ──
class CompatibilityResult(BaseModel):
    total_score: float = Field(..., description="궁합 총점 (0~100)")
    grade: str = ""
    day_stem_relation: str = Field(default="", description="일간 관계")
    ohaeng_complement: str = Field(default="", description="오행 보완 분석")
    interactions: list[InteractionEntry] = Field(default_factory=list)
    mutual_ten_gods: dict[str, str] = Field(default_factory=dict)
    summary: str = ""
    details: list[str] = Field(default_factory=list)


# ── 통합 결과 ──
class SajuAnalysisResult(BaseModel):
    birth_info: dict = Field(default_factory=dict)
    four_pillars: FourPillars | None = None
    ten_gods: list[TenGodEntry] = Field(default_factory=list)
    strength: StrengthResult | None = None
    pattern: PatternResult | None = None
    yongshin: YongshinResult | None = None
    sinsal: list[SinsalEntry] = Field(default_factory=list)
    interactions: list[InteractionEntry] = Field(default_factory=list)
    wealth: WealthResult | None = None
    life_events: list[LifeEvent] = Field(default_factory=list)
    radar: RadarResult | None = None
    daeun: list[DaeunEntry] = Field(default_factory=list)
    day_stem_traits: str = ""
    elem_info: dict = Field(default_factory=dict, description="용신 오행 관련 건강/음식/색상/방향 정보")
    # ── 신규 전문가 분석 ──
    twelve_stages: list[dict] = Field(default_factory=list, description="십이운성 (4주 각 지지)")
    gongmang: dict = Field(default_factory=dict, description="공망 (비어있는 지지)")
    johu: dict = Field(default_factory=dict, description="조후용신 (계절 조절)")
    naeum: dict = Field(default_factory=dict, description="납음오행 (60갑자 소리오행)")
    palace: list[dict] = Field(default_factory=list, description="궁위 분석 (4궁)")
    interpretation: dict = Field(default_factory=dict, description="해석 힌트 (메타포/맥락/스토리)")
    # ── 전문가 교차 분석 (v2) ──
    cross_insights: list[CrossInsight] = Field(default_factory=list, description="교차 분석 인사이트")
    retrodictions: list[Retrodiction] = Field(default_factory=list, description="과거 역추적")
    narrative: SajuNarrative | None = Field(default=None, description="종합 서사")


class YearlyResult(BaseModel):
    birth_info: dict = Field(default_factory=dict)
    target_year: int = 0
    seun: SeunEntry | None = None
    sinsal_activations: list[SinsalEntry] = Field(default_factory=list)
    interactions_with_seun: list[InteractionEntry] = Field(default_factory=list)
    radar: RadarResult | None = None
    summary: str = ""
    yearly_events: list[YearlyEvent] = Field(default_factory=list, description="구체적 사건 예측")
    person_encounters: list[PersonEncounter] = Field(default_factory=list, description="만남의 인물 유형")
    current_daeun: DaeunEntry | None = Field(default=None, description="해당 연도가 속한 대운")
    overall_fortune: str = Field(default="", description="종합 운세 한 줄")


class SinsalResult(BaseModel):
    birth_info: dict = Field(default_factory=dict)
    four_pillars: FourPillars | None = None
    sinsal: list[SinsalEntry] = Field(default_factory=list)
    total_count: int = 0
    daeun_activations: list[dict] = Field(default_factory=list)


# ── 성패 보고서 ──
class ReportSection(BaseModel):
    title: str = Field(..., description="섹션 제목 (성격/재물운/직장운/연애운/결혼운/자녀운/적성)")
    verdict: str = Field(..., description="판정 (대성/성/반반/패/대패)")
    score: float = Field(..., description="점수 (0~100)")
    summary: str = Field(default="", description="한 줄 요약 (된다/안된다 포함)")
    details: list[str] = Field(default_factory=list, description="상세 분석 라인")


class SajuReport(BaseModel):
    birth_info: dict = Field(default_factory=dict)
    four_pillars_summary: str = Field(default="", description="사주 요약 (예: 경오 신사 경진 계미)")
    overall: ReportSection | None = Field(default=None, description="총평")
    sections: list[ReportSection] = Field(default_factory=list, description="개별 섹션 (성격~적성)")
    # ── 전문가 분석 데이터 ──
    four_pillars: FourPillars | None = Field(default=None, description="사주 원국 전체")
    strength: StrengthResult | None = Field(default=None, description="신강/신약")
    pattern: PatternResult | None = Field(default=None, description="격국")
    yongshin: YongshinResult | None = Field(default=None, description="용신")
    ten_gods: list[TenGodEntry] = Field(default_factory=list, description="십신 목록")
    interactions: list[InteractionEntry] = Field(default_factory=list, description="합충형파해")
    sinsal: list[SinsalEntry] = Field(default_factory=list, description="신살")
    daeun: list[DaeunEntry] = Field(default_factory=list, description="대운")
    radar: RadarResult | None = Field(default=None, description="6축 레이더")
    day_stem_traits: str = Field(default="", description="일간 성격")
    elem_info: dict = Field(default_factory=dict, description="용신 오행 관련 건강/음식/색상/방향 정보")
    twelve_stages: list[dict] = Field(default_factory=list, description="십이운성 (4주 각 지지)")
    gongmang: dict = Field(default_factory=dict, description="공망 (비어있는 지지)")
    johu: dict = Field(default_factory=dict, description="조후용신 (계절 조절)")
    naeum: dict = Field(default_factory=dict, description="납음오행 (60갑자 소리오행)")
    palace: list[dict] = Field(default_factory=list, description="궁위 분석 (4궁)")
    interpretation: dict = Field(default_factory=dict, description="해석 힌트 (메타포/맥락/스토리)")


# ── 궁합 보고서 ──
class CompatReportSection(BaseModel):
    title: str
    verdict: str = Field(..., description="판정 (성/패/반반)")
    score: float
    max_score: float = 25.0
    summary: str = ""
    details: list[str] = Field(default_factory=list)


class CompatReport(BaseModel):
    person_a: dict = Field(default_factory=dict)
    person_b: dict = Field(default_factory=dict)
    pillars_a_summary: str = ""
    pillars_b_summary: str = ""
    total_score: float = 0
    grade: str = ""
    overall_verdict: str = ""
    overall_summary: str = ""
    sections: list[CompatReportSection] = Field(default_factory=list)
    ohaeng_table: list[dict] = Field(default_factory=list, description="오행별 비교표")
    advice: list[str] = Field(default_factory=list, description="현실 조언")


# ── 교차 분석 ──
class CrossInsight(BaseModel):
    pattern_name: str = Field(..., description="패턴 이름 (예: 식상생재, 관인상생)")
    evidence: list[str] = Field(default_factory=list, description="근거 데이터")
    causal_chain: str = Field(default="", description="인과 체인 (~이므로 → ~하게 되고 → ~)")
    life_impact: str = Field(default="", description="실생활 영향")
    warning: str = Field(default="", description="주의사항")
    priority: int = Field(default=3, ge=1, le=5, description="중요도 1(최고)~5")


# ── 과거 역추적 ──
class Retrodiction(BaseModel):
    age: int = Field(..., description="해당 나이")
    year: int = Field(..., description="서력 연도")
    daeun_info: str = Field(default="", description="대운 정보 (예: 갑인 대운 시작)")
    ten_god_context: str = Field(default="", description="십신 맥락 설명")
    predicted_event: str = Field(default="", description="추정 사건")
    question_hook: str = Field(default="", description="상담 화법 (혹시 ~세 때...)")
    confidence: str = Field(default="중간", description="확신도 (높음/중간/낮음)")
    evidence: list[str] = Field(default_factory=list, description="근거")


# ── 시기 조언 ──
class TimingAdvice(BaseModel):
    period: str = Field(..., description="시기 (예: 2026년 상반기)")
    action: str = Field(default="", description="구체적 행동")
    reason: str = Field(default="", description="사주 근거")


# ── 질문 기반 상담 ──
class ConsultResponse(BaseModel):
    question: str = Field(..., description="원래 질문")
    question_type: str = Field(default="", description="질문 분류")
    answer_summary: str = Field(default="", description="한 줄 답변")
    detailed_analysis: str = Field(default="", description="상세 분석")
    cross_insights: list[CrossInsight] = Field(default_factory=list)
    timing: list[TimingAdvice] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


# ── 서사 ──
class SajuNarrative(BaseModel):
    one_line: str = Field(default="", description="한 줄 정의 (예: 기술자 팔자)")
    personality_story: str = Field(default="", description="성격 서사 2~3문단")
    life_arc: str = Field(default="", description="인생 전체 흐름 서사")
    current_chapter: str = Field(default="", description="지금 인생의 어떤 시기인지")
    top3_insights: list[str] = Field(default_factory=list, description="핵심 통찰 3개")
    practical_advice: list[str] = Field(default_factory=list, description="구체적 실행 조언")
