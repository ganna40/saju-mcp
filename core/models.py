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


class YearlyResult(BaseModel):
    birth_info: dict = Field(default_factory=dict)
    target_year: int = 0
    seun: SeunEntry | None = None
    sinsal_activations: list[SinsalEntry] = Field(default_factory=list)
    interactions_with_seun: list[InteractionEntry] = Field(default_factory=list)
    radar: RadarResult | None = None
    summary: str = ""


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
