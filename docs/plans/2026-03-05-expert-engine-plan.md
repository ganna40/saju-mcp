# 사주 MCP 전문가 엔진 고도화 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** MCP 서버 내부에 교차 분석 + 과거 역추적 + 질문 기반 상담 + 서사 생성 엔진을 추가하여, 진짜 인간 전문가처럼 인과관계 기반의 깊이 있는 해석을 자동 생성한다.

**Architecture:** 기존 독립 모듈(strength, pattern, yongshin 등)의 결과를 받아서 교차 분석하는 상위 레이어 4개를 추가한다. 기존 계산 엔진은 그대로 유지하고, 새 모듈은 기존 출력을 입력으로 받는 순수 해석 레이어다.

**Tech Stack:** Python 3.11+, Pydantic v2, FastMCP 2.0

---

## Task 1: 새 Pydantic 모델 정의 (models.py 확장)

**Files:**
- Modify: `core/models.py` (맨 아래에 추가)

**Step 1: CrossInsight, Retrodiction, ConsultResponse, SajuNarrative 모델 추가**

`core/models.py` 맨 아래(`CompatReport` 클래스 뒤)에 다음을 추가:

```python
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
```

**Step 2: SajuAnalysisResult에 새 필드 추가**

`SajuAnalysisResult` 클래스의 `interpretation` 필드 아래에 추가:

```python
    # ── 전문가 교차 분석 (v2) ──
    cross_insights: list[CrossInsight] = Field(default_factory=list, description="교차 분석 인사이트")
    retrodictions: list[Retrodiction] = Field(default_factory=list, description="과거 역추적")
    narrative: SajuNarrative | None = Field(default=None, description="종합 서사")
```

**Step 3: 검증**

Run: `cd "C:\Users\ganna\saju-mcp" && python -c "from core.models import CrossInsight, Retrodiction, ConsultResponse, SajuNarrative; print('Models OK')"`
Expected: `Models OK`

**Step 4: Commit**

```bash
cd "C:\Users\ganna\saju-mcp"
git add core/models.py
git commit -m "feat: add CrossInsight, Retrodiction, ConsultResponse, SajuNarrative models"
```

---

## Task 2: 교차 분석 엔진 — `core/cross_analysis.py`

**Files:**
- Create: `core/cross_analysis.py`

**Step 1: 교차 패턴 정의 + 탐지 엔진 구현**

핵심: 십신 조합 패턴을 탐지하고, 격국×용신×신강 맥락에서 인과 체인을 생성한다.

```python
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
```

**Step 2: 검증**

Run: `cd "C:\Users\ganna\saju-mcp" && python -c "
from core.manseryeok import get_four_pillars, get_daeun
from core.ten_gods import get_all_ten_gods, calc_ten_god, calc_ten_god_for_branch
from core.strength import calc_strength
from core.pattern_engine import determine_pattern
from core.yongshin import determine_yongshin
from core.sinsal import detect_sinsal
from core.interactions import detect_interactions
from core.wealth import calc_wealth
from core.cross_analysis import analyze_cross_patterns

p = get_four_pillars(1990, 5, 15, 14)
tg = get_all_ten_gods(p)
d = get_daeun(1990, 5, 15, 14, 0, '남')
for dd in d:
    dd.ten_god_stem = calc_ten_god(p.day.stem, dd.stem)
    dd.ten_god_branch = calc_ten_god_for_branch(p.day.stem, dd.branch)
s = calc_strength(p)
pt = determine_pattern(p, s)
y = determine_yongshin(s, pt)
ss = detect_sinsal(p, d)
ii = detect_interactions(p)
w = calc_wealth(p, s, pt, ii, d)
insights = analyze_cross_patterns(p, tg, s, pt, y, ii, ss, w, d)
for i in insights:
    print(f'[P{i.priority}] {i.pattern_name}: {i.causal_chain[:60]}...')
print(f'Total: {len(insights)} insights')
"`
Expected: 여러 개의 교차 인사이트 출력

**Step 3: Commit**

```bash
git add core/cross_analysis.py
git commit -m "feat: add cross-analysis engine with 11 pattern detectors"
```

---

## Task 3: 과거 역추적 엔진 — `core/retrodiction.py`

**Files:**
- Create: `core/retrodiction.py`

**Step 1: 역추적 엔진 구현**

```python
"""과거 역추적 엔진 — 대운 전환점 기반 과거 사건 추정."""
from __future__ import annotations

from .constants import (
    TEN_GOD_CATEGORIES, STEM_OHAENG, BRANCH_OHAENG,
    YUKCHUNG, EARTHLY_BRANCHES,
)
from .models import (
    FourPillars, DaeunEntry, StrengthResult, YongshinResult,
    InteractionEntry, SinsalEntry, Retrodiction,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


# 대운 십신 → 과거 사건 추정 맵
_DAEUN_EVENT_MAP = {
    "비겁": {
        "youth": "친구/동료 관계가 중요했던 시기. 경쟁, 독립, 또래 집단 활동",
        "early_adult": "독립하거나 독자적으로 무언가를 시작. 경쟁이 심한 환경",
        "mid_adult": "동업이나 파트너십 변화. 형제/친구와의 금전 문제 가능",
        "senior": "자기 사업이나 독립적 활동. 고집이 강해지는 시기",
    },
    "식상": {
        "youth": "재능이 드러나기 시작. 예체능, 글쓰기, 표현 활동",
        "early_adult": "새로운 일 시작, 이직, 창업 아이디어. 자녀 관련 변화(여성)",
        "mid_adult": "전문성 발휘, 새 프로젝트, 사업 확장. 자녀 출산/양육",
        "senior": "후진 양성, 저술, 예술 활동. 자녀와의 관계 변화",
    },
    "재성": {
        "youth": "용돈, 아르바이트, 경제 개념이 생기는 시기",
        "early_adult": "재물 움직임, 투자 시작, 이성 인연(남성). 취업",
        "mid_adult": "부동산, 큰 투자, 사업 확장. 배우자 관련 변화(남성)",
        "senior": "재산 정리, 노후 자금 관리. 경제적 변화",
    },
    "관성": {
        "youth": "학교 규율, 시험, 부모 압박. 규칙 속에서의 성장",
        "early_adult": "취업, 직장 생활 시작. 시험 합격/불합격. 윗사람 관계",
        "mid_adult": "승진, 직책 변화, 직장 스트레스. 배우자 관련(여성)",
        "senior": "은퇴, 건강 관리. 사회적 평가",
    },
    "인성": {
        "youth": "공부, 학업, 어머니 영향. 이사, 전학",
        "early_adult": "자격증, 대학원, 학위. 멘토를 만남. 이사/주거 변화",
        "mid_adult": "재교육, 전직 교육. 부동산(인성=부동산). 어머니 건강",
        "senior": "종교, 철학, 학문 심화. 편안한 안식처",
    },
}

# 질문 후크 템플릿
_QUESTION_TEMPLATES = {
    "비겁": "혹시 {age}세({year}년) 때 독립하시거나, 친한 친구와 크게 다투신 적 있으세요?",
    "식상": "혹시 {age}세({year}년) 때 새로운 일을 시작하셨거나, 뭔가 만들기 시작하신 거 있으세요?",
    "재성": "혹시 {age}세({year}년) 때 돈 때문에 큰 일이 있으셨어요? 투자를 하셨다든지, 직장을 구하셨다든지.",
    "관성": "혹시 {age}세({year}년) 때 직장에서 큰 변화가 있으셨어요? 승진이나 이직이라든지, 시험을 보셨다든지.",
    "인성": "혹시 {age}세({year}년) 때 공부를 다시 시작하셨거나, 이사를 하셨거나, 어머니 관련으로 무슨 일이 있으셨어요?",
}


def _get_age_group(age: int) -> str:
    if age < 15:
        return "youth"
    if age < 30:
        return "early_adult"  # 실제로는 youth~early_adult
    if age < 45:
        return "early_adult"
    if age < 60:
        return "mid_adult"
    return "senior"


def _detect_bogeumbaneum(daeun_branch: str, pillars: FourPillars) -> tuple[str, str]:
    """복음(伏吟) / 반음(反吟) 탐지."""
    il_ji = pillars.day.branch

    # 복음: 대운 지지 == 일지 → 정체, 반복
    if daeun_branch == il_ji:
        return "복음", "같은 에너지가 반복되어 정체감, 답답함을 느끼는 시기. '왜 같은 일이 반복되지?' 싶은 경험"

    # 반음: 대운 지지 ↔ 일지가 충
    pair = frozenset({daeun_branch, il_ji})
    if pair in YUKCHUNG:
        return "반음", "기존 삶이 뒤집히는 큰 변화. 이사, 이직, 이별 등 '이(離)'의 에너지가 강한 시기"

    return "", ""


def generate_retrodictions(
    pillars: FourPillars,
    daeun: list[DaeunEntry],
    birth_year: int,
    interactions: list[InteractionEntry],
    sinsal: list[SinsalEntry],
    strength: StrengthResult,
    yongshin: YongshinResult,
    gender: str = "남",
) -> list[Retrodiction]:
    """대운 전환점 기반 과거 사건 역추적 생성."""
    retros: list[Retrodiction] = []
    current_year = 2026

    for d in daeun:
        actual_year = birth_year + d.age_start - 1
        if actual_year >= current_year:
            continue  # 미래는 skip (역추적이니까)

        age = d.age_start
        age_group = _get_age_group(age)

        # 대운 십신 카테고리
        stem_tg = d.ten_god_stem or calc_ten_god(pillars.day.stem, d.stem)
        branch_tg = d.ten_god_branch or calc_ten_god_for_branch(pillars.day.stem, d.branch)
        stem_cat = TEN_GOD_CATEGORIES.get(stem_tg, "")
        branch_cat = TEN_GOD_CATEGORIES.get(branch_tg, "")

        # 주요 카테고리 (천간 우선)
        main_cat = stem_cat or branch_cat
        if not main_cat:
            continue

        # 사건 추정
        event_map = _DAEUN_EVENT_MAP.get(main_cat, {})
        predicted = event_map.get(age_group, f"{main_cat} 에너지가 작용하는 시기")

        # 복음/반음
        bgba_type, bgba_desc = _detect_bogeumbaneum(d.branch, pillars)

        # 용신/기신 여부
        d_elems = {d.stem_ohaeng, d.branch_ohaeng} - {""}
        favorable = set(yongshin.favorable_elements)
        unfavorable = set(yongshin.unfavorable_elements)
        is_favorable = bool(d_elems & favorable)
        is_unfavorable = bool(d_elems & unfavorable)

        # 근거 수집
        evidence = [
            f"대운 {d.stem}{d.branch} ({stem_tg}/{branch_tg})",
            f"{'용신 대운' if is_favorable else '기신 대운' if is_unfavorable else '보통 대운'}",
        ]
        if bgba_type:
            evidence.append(f"{bgba_type}: {bgba_desc}")
            predicted += f" ({bgba_type} — {bgba_desc})"

        # 확신도
        confidence = "높음" if (bgba_type or is_favorable or is_unfavorable) else "중간"

        # 성별 특화
        if gender == "남" and main_cat == "재성" and age_group in ("early_adult", "mid_adult"):
            predicted += " 또는 중요한 여성과의 인연 변화"
        elif gender == "여" and main_cat == "관성" and age_group in ("early_adult", "mid_adult"):
            predicted += " 또는 중요한 남성과의 인연 변화"

        # 질문 후크
        template = _QUESTION_TEMPLATES.get(main_cat, "혹시 {age}세({year}년) 때 큰 변화가 있으셨어요?")
        question = template.format(age=age, year=actual_year)

        retros.append(Retrodiction(
            age=age,
            year=actual_year,
            daeun_info=f"{d.stem}{d.branch} 대운 시작 ({d.age_start}~{d.age_end}세)",
            ten_god_context=f"{stem_tg}({stem_cat})/{branch_tg}({branch_cat})",
            predicted_event=predicted,
            question_hook=question,
            confidence=confidence,
            evidence=evidence,
        ))

    return retros
```

**Step 2: 검증**

Run: `cd "C:\Users\ganna\saju-mcp" && python -c "
from core.manseryeok import get_four_pillars, get_daeun
from core.ten_gods import calc_ten_god, calc_ten_god_for_branch
from core.strength import calc_strength
from core.yongshin import determine_yongshin
from core.pattern_engine import determine_pattern
from core.sinsal import detect_sinsal
from core.interactions import detect_interactions
from core.retrodiction import generate_retrodictions

p = get_four_pillars(1990, 5, 15, 14)
d = get_daeun(1990, 5, 15, 14, 0, '남')
for dd in d:
    dd.ten_god_stem = calc_ten_god(p.day.stem, dd.stem)
    dd.ten_god_branch = calc_ten_god_for_branch(p.day.stem, dd.branch)
s = calc_strength(p)
pt = determine_pattern(p, s)
y = determine_yongshin(s, pt)
ss = detect_sinsal(p, d)
ii = detect_interactions(p)
retros = generate_retrodictions(p, d, 1990, ii, ss, s, y)
for r in retros:
    print(f'{r.age}세({r.year}): {r.question_hook}')
print(f'Total: {len(retros)} retrodictions')
"`
Expected: 과거 대운별 역추적 질문 출력

**Step 3: Commit**

```bash
git add core/retrodiction.py
git commit -m "feat: add retrodiction engine for past event prediction"
```

---

## Task 4: 서사 생성 엔진 — `core/narrative_engine.py`

**Files:**
- Create: `core/narrative_engine.py`

**Step 1: 서사 엔진 구현**

```python
"""서사 생성 엔진 — 교차 분석 결과를 하나의 스토리로 엮는다."""
from __future__ import annotations

from .constants import (
    DAY_STEM_METAPHORS, DAY_STEM_TRAITS, STEM_OHAENG,
    TEN_GOD_CATEGORIES, PATTERN_TRAITS, CAREER_BY_PATTERN,
)
from .models import (
    FourPillars, StrengthResult, PatternResult, YongshinResult,
    TenGodEntry, CrossInsight, Retrodiction, DaeunEntry,
    WealthResult, SajuNarrative,
)


def generate_narrative(
    pillars: FourPillars,
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    ten_gods: list[TenGodEntry],
    cross_insights: list[CrossInsight],
    retrodictions: list[Retrodiction],
    wealth: WealthResult,
    daeun: list[DaeunEntry],
    gender: str = "남",
    birth_year: int = 0,
) -> SajuNarrative:
    """교차 분석 + 역추적 결과를 종합 서사로 변환."""
    day_stem = pillars.day.stem
    meta = DAY_STEM_METAPHORS.get(day_stem, {})

    return SajuNarrative(
        one_line=_one_line(pattern, strength, cross_insights, wealth),
        personality_story=_personality_story(pillars, strength, pattern, ten_gods, meta, cross_insights),
        life_arc=_life_arc(daeun, yongshin, retrodictions, birth_year, pillars),
        current_chapter=_current_chapter(daeun, birth_year, yongshin, pillars),
        top3_insights=_top3(cross_insights),
        practical_advice=_advice(cross_insights, yongshin, strength, pattern),
    )


def _one_line(pattern, strength, insights, wealth) -> str:
    """이 사주를 한 줄로 정의."""
    # 가장 높은 우선순위 인사이트 기반
    if insights:
        top = insights[0]
        if "식상생재" in top.pattern_name:
            return f"재능으로 돈 버는 팔자 — {pattern.name}, 재물 {wealth.grade}등급"
        if "관인상생" in top.pattern_name:
            return f"공부로 인정받는 팔자 — {pattern.name}, 시험/자격증에 강함"
        if "상관견관" in top.pattern_name:
            return f"자유로운 영혼, 틀을 깨는 팔자 — {pattern.name}"
        if "편인도식" in top.pattern_name:
            return f"숨은 재능이 있는 팔자 — {pattern.name}, 표현 출구 필요"
        if "비겁쟁재" in top.pattern_name:
            return f"혼자 벌어야 지키는 팔자 — {pattern.name}, 동업 금지"
        if "종격" in top.pattern_name:
            return f"흐름을 따라가는 특별한 팔자 — {pattern.name}"

    # 기본 패턴
    if strength.score >= 65:
        return f"에너지 넘치는 {pattern.name} — 발산할 출구 필요"
    if strength.score <= 35:
        return f"지원군이 필요한 {pattern.name} — 혼자보다 함께"

    return f"{pattern.name}, {strength.label}({strength.score}점) — 재물 {wealth.grade}등급"


def _personality_story(pillars, strength, pattern, ten_gods, meta, insights) -> str:
    """성격 서사 2~3문단."""
    day_stem = pillars.day.stem
    parts = []

    # 1문단: 일간 메타포 기반
    image = meta.get("image", day_stem)
    nature = meta.get("nature", "")
    if strength.score >= 55:
        desc = meta.get("strong", "")
    elif strength.score <= 45:
        desc = meta.get("weak", "")
    else:
        desc = meta.get("balanced", "")

    parts.append(
        f"{day_stem} 일간은 {image}에 비유됩니다. "
        f"{nature}이 핵심 본성이고, "
        f"신강도 {strength.score}점({strength.label})이라 {desc}."
    )

    # 2문단: 십신 조합 기반 사회적 행동
    cats = {}
    for tg in ten_gods:
        cats[tg.category] = cats.get(tg.category, 0) + 1
    dominant = max(cats, key=cats.get) if cats else ""

    wolgan_tg = next((tg for tg in ten_gods if tg.position == "월간"), None)
    wolgan_desc = ""
    if wolgan_tg:
        wolgan_desc = f"월간에 {wolgan_tg.ten_god}이 있어 사회생활에서 {_wolgan_style(wolgan_tg.ten_god)}"

    parts.append(
        f"십신 구성을 보면 {dominant}이 {cats.get(dominant, 0)}개로 지배적입니다. "
        f"{wolgan_desc} "
        f"격국은 {pattern.name}으로, {pattern.traits}."
    )

    # 3문단: 교차 분석 기반 핵심 패턴
    personality_insights = [i for i in insights if i.priority <= 2]
    if personality_insights:
        top = personality_insights[0]
        parts.append(
            f"특히 이 사주의 핵심 구조는 '{top.pattern_name}'입니다. "
            f"{top.causal_chain} "
            f"{top.life_impact}"
        )

    return "\n\n".join(parts)


def _wolgan_style(tg_name: str) -> str:
    """월간 십신별 사회 스타일 한 줄."""
    styles = {
        "비견": "독립적으로 일하는 걸 선호합니다.",
        "겁재": "사교적이지만 속내를 잘 안 보여줍니다.",
        "식신": "표현력이 좋고 사람들과 잘 어울립니다.",
        "상관": "틀에 박힌 걸 싫어하고 자기 방식대로 합니다.",
        "편재": "돈 감각이 있고 여러 일을 동시에 벌입니다.",
        "정재": "계획적이고 안정적인 걸 추구합니다.",
        "편관": "겉으로는 온화하지만 속으로는 승부욕이 강합니다.",
        "정관": "원칙적이고 조직 생활에 잘 맞습니다.",
        "편인": "남들과 다른 독특한 시각을 가지고 있습니다.",
        "정인": "배움을 좋아하고 학구적입니다.",
    }
    return styles.get(tg_name, "자신만의 스타일이 있습니다.")


def _life_arc(daeun, yongshin, retros, birth_year, pillars) -> str:
    """인생 전체 흐름 서사."""
    if not retros:
        return ""

    parts = []
    favorable = set(yongshin.favorable_elements)

    past_retros = [r for r in retros if r.year < 2026]

    # 과거 흐름 요약
    if past_retros:
        parts.append("지금까지의 인생 흐름을 보면:")
        for r in past_retros[:4]:
            marker = "★" if r.confidence == "높음" else "·"
            parts.append(f"  {marker} {r.age}세({r.year}년) — {r.predicted_event}")

    # 미래 대운 예측
    future_daeun = [d for d in daeun if birth_year + d.age_start - 1 >= 2026]
    if future_daeun:
        parts.append("")
        parts.append("앞으로의 흐름:")
        for d in future_daeun[:3]:
            d_elems = {d.stem_ohaeng, d.branch_ohaeng} - {""}
            is_good = bool(d_elems & favorable)
            label = "↑ 상승기" if is_good else "→ 안정기"
            parts.append(f"  {label} {d.age_start}~{d.age_end}세({d.stem}{d.branch})")

    return "\n".join(parts)


def _current_chapter(daeun, birth_year, yongshin, pillars) -> str:
    """지금은 인생의 어떤 시기인지."""
    current_age = 2026 - birth_year + 1
    current_daeun = None
    for d in daeun:
        if d.age_start <= current_age <= d.age_end:
            current_daeun = d
            break

    if not current_daeun:
        return ""

    d_elems = {current_daeun.stem_ohaeng, current_daeun.branch_ohaeng} - {""}
    favorable = set(yongshin.favorable_elements)
    unfavorable = set(yongshin.unfavorable_elements)

    if d_elems & favorable:
        tone = "용신이 작용하는 상승기"
    elif d_elems & unfavorable:
        tone = "기신이 작용하여 조심해야 하는 시기"
    else:
        tone = "큰 변동 없이 내실을 다지는 시기"

    tg_s = current_daeun.ten_god_stem or ""
    tg_b = current_daeun.ten_god_branch or ""

    return (
        f"현재 만 {current_age}세, {current_daeun.stem}{current_daeun.branch} 대운 "
        f"({current_daeun.age_start}~{current_daeun.age_end}세) 중입니다. "
        f"대운 십신 {tg_s}/{tg_b}로, {tone}입니다."
    )


def _top3(insights: list[CrossInsight]) -> list[str]:
    """핵심 통찰 3개."""
    result = []
    for i in insights[:3]:
        result.append(f"{i.pattern_name}: {i.life_impact}")
    return result


def _advice(insights, yongshin, strength, pattern) -> list[str]:
    """구체적 실행 조언."""
    advice = []

    # 교차 분석 기반 조언
    for i in insights[:3]:
        if i.warning:
            advice.append(i.warning)

    # 용신 기반 기본 조언
    if yongshin.yongshin:
        from .constants import ELEM_COLOR, ELEM_DIRECTION, ELEM_FOOD
        elem = yongshin.yongshin
        color = ELEM_COLOR.get(elem, "")
        direction = ELEM_DIRECTION.get(elem, "")
        food = ELEM_FOOD.get(elem, "")
        advice.append(f"용신({elem}): {color} 계열 착용, {direction} 방향, {food} 섭취가 도움.")

    return advice[:5]
```

**Step 2: 검증**

Run: `cd "C:\Users\ganna\saju-mcp" && python -c "
from core.manseryeok import get_four_pillars, get_daeun
from core.ten_gods import get_all_ten_gods, calc_ten_god, calc_ten_god_for_branch
from core.strength import calc_strength
from core.pattern_engine import determine_pattern
from core.yongshin import determine_yongshin
from core.sinsal import detect_sinsal
from core.interactions import detect_interactions
from core.wealth import calc_wealth
from core.cross_analysis import analyze_cross_patterns
from core.retrodiction import generate_retrodictions
from core.narrative_engine import generate_narrative

p = get_four_pillars(1990, 5, 15, 14)
tg = get_all_ten_gods(p)
d = get_daeun(1990, 5, 15, 14, 0, '남')
for dd in d:
    dd.ten_god_stem = calc_ten_god(p.day.stem, dd.stem)
    dd.ten_god_branch = calc_ten_god_for_branch(p.day.stem, dd.branch)
s = calc_strength(p)
pt = determine_pattern(p, s)
y = determine_yongshin(s, pt)
ss = detect_sinsal(p, d)
ii = detect_interactions(p)
w = calc_wealth(p, s, pt, ii, d)
ci = analyze_cross_patterns(p, tg, s, pt, y, ii, ss, w, d)
retros = generate_retrodictions(p, d, 1990, ii, ss, s, y)
narr = generate_narrative(p, s, pt, y, tg, ci, retros, w, d, '남', 1990)
print('ONE LINE:', narr.one_line)
print()
print('PERSONALITY:', narr.personality_story[:200], '...')
print()
print('TOP 3:', narr.top3_insights)
print()
print('CURRENT:', narr.current_chapter)
"`
Expected: 한 줄 정의, 성격 서사, 핵심 통찰, 현재 시기 출력

**Step 3: Commit**

```bash
git add core/narrative_engine.py
git commit -m "feat: add narrative engine for expert-level storytelling"
```

---

## Task 5: 질문 기반 상담 엔진 — `core/deep_consult.py`

**Files:**
- Create: `core/deep_consult.py`

**Step 1: 질문 라우터 + 심층 분석 구현**

```python
"""질문 기반 심층 상담 엔진 — 구체적 질문에 맞춤 분석."""
from __future__ import annotations

import re
from .constants import TEN_GOD_CATEGORIES, STEM_OHAENG
from .models import (
    FourPillars, StrengthResult, PatternResult, YongshinResult,
    TenGodEntry, InteractionEntry, SinsalEntry, WealthResult,
    DaeunEntry, CrossInsight, ConsultResponse, TimingAdvice,
    SeunEntry,
)
from .ten_gods import calc_ten_god, calc_ten_god_for_branch


# 질문 키워드 → 분석 유형 매핑
_QUESTION_KEYWORDS = {
    "이직": "career_change",
    "퇴사": "career_change",
    "전직": "career_change",
    "직장": "career",
    "승진": "career",
    "사업": "business",
    "창업": "business",
    "재물": "wealth",
    "돈": "wealth",
    "투자": "wealth",
    "부동산": "wealth",
    "연애": "love",
    "결혼": "marriage",
    "이혼": "marriage",
    "배우자": "marriage",
    "건강": "health",
    "올해": "yearly",
    "내년": "yearly",
    "시기": "timing",
    "언제": "timing",
    "적성": "aptitude",
    "공부": "study",
    "시험": "study",
    "자격증": "study",
}


def _classify_question(question: str) -> str:
    """질문을 분석 유형으로 분류."""
    for keyword, qtype in _QUESTION_KEYWORDS.items():
        if keyword in question:
            return qtype
    return "general"


def deep_consult(
    question: str,
    pillars: FourPillars,
    ten_gods: list[TenGodEntry],
    strength: StrengthResult,
    pattern: PatternResult,
    yongshin: YongshinResult,
    interactions: list[InteractionEntry],
    sinsal: list[SinsalEntry],
    wealth: WealthResult,
    daeun: list[DaeunEntry],
    cross_insights: list[CrossInsight],
    gender: str = "남",
    birth_year: int = 0,
    target_year: int = 2026,
    seun: SeunEntry | None = None,
) -> ConsultResponse:
    """질문에 맞춤 심층 분석."""
    qtype = _classify_question(question)

    # 기본 구조
    resp = ConsultResponse(
        question=question,
        question_type=qtype,
    )

    # 질문 유형별 분석
    if qtype == "career_change":
        _analyze_career_change(resp, pillars, ten_gods, strength, pattern,
                               yongshin, daeun, cross_insights, birth_year, target_year, seun)
    elif qtype in ("career", "business"):
        _analyze_career(resp, pillars, ten_gods, strength, pattern,
                        yongshin, daeun, cross_insights, qtype)
    elif qtype == "wealth":
        _analyze_wealth(resp, wealth, cross_insights, daeun, yongshin, birth_year, target_year)
    elif qtype in ("love", "marriage"):
        _analyze_love(resp, pillars, ten_gods, sinsal, interactions,
                      daeun, gender, cross_insights, birth_year, qtype)
    elif qtype == "health":
        _analyze_health(resp, strength, yongshin, sinsal)
    elif qtype == "yearly":
        _analyze_yearly(resp, daeun, yongshin, birth_year, target_year, seun, cross_insights)
    elif qtype == "study":
        _analyze_study(resp, ten_gods, cross_insights, daeun, yongshin, birth_year, target_year)
    else:
        _analyze_general(resp, cross_insights, strength, pattern)

    # 관련 교차 인사이트 첨부
    resp.cross_insights = _filter_relevant_insights(cross_insights, qtype)

    return resp


def _filter_relevant_insights(insights: list[CrossInsight], qtype: str) -> list[CrossInsight]:
    """질문 유형에 관련된 인사이트만 필터."""
    relevance = {
        "career_change": ["관인상생", "상관견관", "역마", "충돌"],
        "career": ["관인상생", "상관견관", "살인상생", "에너지"],
        "business": ["식상생재", "비겁쟁재", "겁재극재"],
        "wealth": ["식상생재", "비겁쟁재", "겁재극재", "전성기", "주의"],
        "love": ["상관견관", "도화역마", "재관혼잡"],
        "marriage": ["상관견관", "재관혼잡", "궁위"],
        "health": ["에너지", "양인백호"],
        "yearly": ["전성기", "주의"],
        "study": ["관인상생", "살인상생"],
    }
    keywords = relevance.get(qtype, [])
    if not keywords:
        return insights[:3]
    return [i for i in insights if any(k in i.pattern_name for k in keywords)][:5]


def _analyze_career_change(resp, pillars, ten_gods, strength, pattern,
                           yongshin, daeun, insights, birth_year, target_year, seun):
    """이직 분석."""
    current_age = target_year - birth_year + 1

    # 현재 대운
    current_daeun = None
    for d in daeun:
        if d.age_start <= current_age <= d.age_end:
            current_daeun = d
            break

    # 관성 유무 = 직장운
    has_gwanseong = any(tg.category == "관성" for tg in ten_gods)
    has_siksang = any(tg.category == "식상" for tg in ten_gods)
    has_yeokma = False  # 신살에서 확인하려면 별도 체크 필요

    # 판단
    parts = []
    can_change = True
    reasons = []

    if current_daeun:
        d_elems = {current_daeun.stem_ohaeng, current_daeun.branch_ohaeng} - {""}
        favorable = set(yongshin.favorable_elements)
        unfavorable = set(yongshin.unfavorable_elements)

        if d_elems & favorable:
            parts.append(f"현재 대운({current_daeun.stem}{current_daeun.branch})이 용신 대운이라 전반적으로 좋은 흐름입니다.")
            reasons.append("용신 대운")
        elif d_elems & unfavorable:
            parts.append(f"현재 대운({current_daeun.stem}{current_daeun.branch})이 기신 대운이라 신중해야 합니다.")
            can_change = False
            reasons.append("기신 대운")

        # 대운 십신이 관성이면 직장 변화
        tg_s = current_daeun.ten_god_stem or ""
        tg_b = current_daeun.ten_god_branch or ""
        cats = {TEN_GOD_CATEGORIES.get(tg_s, ""), TEN_GOD_CATEGORIES.get(tg_b, "")} - {""}

        if "관성" in cats:
            parts.append("대운에 관성이 들어와 직장 변화 에너지가 있습니다.")
            reasons.append("대운 관성")
        if "식상" in cats:
            parts.append("대운에 식상이 들어와 새로운 시도에 유리합니다.")
            reasons.append("대운 식상")

    # 신강/약 기준
    if strength.score >= 55:
        parts.append("신강하여 변화를 감당할 체력이 있습니다.")
    else:
        parts.append("신약하여 무리한 변화보다는 준비된 이직이 좋습니다.")

    # 상관견관이면 조직 갈등
    sanggwan_insight = next((i for i in insights if "상관견관" in i.pattern_name), None)
    if sanggwan_insight:
        parts.append("상관견관 구조가 있어 현 직장에서의 갈등이 이직 동기일 수 있습니다.")

    if can_change:
        resp.answer_summary = "이직 가능합니다. 시기와 방향이 중요합니다."
    else:
        resp.answer_summary = "지금은 신중하게. 준비 기간을 거친 후 이직하는 것이 좋습니다."

    resp.detailed_analysis = " ".join(parts)

    # 시기 조언
    for d in daeun:
        yr = birth_year + d.age_start - 1
        if yr < target_year:
            continue
        d_elems = {d.stem_ohaeng, d.branch_ohaeng} - {""}
        favorable = set(yongshin.favorable_elements)
        if d_elems & favorable:
            tg_s = d.ten_god_stem or calc_ten_god(pillars.day.stem, d.stem)
            tg_b = d.ten_god_branch or calc_ten_god_for_branch(pillars.day.stem, d.branch)
            resp.timing.append(TimingAdvice(
                period=f"{d.age_start}~{d.age_end}세 ({yr}~{yr + d.age_end - d.age_start}년)",
                action="이직/전직에 유리한 시기",
                reason=f"용신 대운, {tg_s}/{tg_b}",
            ))
            if len(resp.timing) >= 2:
                break

    resp.cautions = [r for r in reasons if "기신" in r]
    resp.action_items = [
        "이직 전 용신 오행과 관련된 업종/환경인지 확인할 것",
        f"신강도가 {strength.score}점이므로 {'과감하게 도전 가능' if strength.score >= 55 else '안정적인 곳으로 이동 권장'}",
    ]


def _analyze_career(resp, pillars, ten_gods, strength, pattern,
                    yongshin, daeun, insights, qtype):
    """직장/사업 분석."""
    cats = {}
    for tg in ten_gods:
        cats[tg.category] = cats.get(tg.category, 0) + 1

    if qtype == "business":
        can_biz = strength.score >= 55 and cats.get("재성", 0) >= 1
        if can_biz:
            resp.answer_summary = "사업 적성이 있습니다."
            resp.detailed_analysis = f"신강({strength.score}점)하고 재성이 {cats.get('재성', 0)}개 있어 사업 체력과 돈 감각이 있습니다."
        else:
            resp.answer_summary = "직장 생활이 더 안정적입니다."
            resp.detailed_analysis = f"신강도 {strength.score}점으로 {'체력은 되나 재성이 부족' if strength.score >= 55 else '사업을 버틸 체력이 부족'}합니다."

        resp.cautions = []
        bigeop_insight = next((i for i in insights if "비겁" in i.pattern_name), None)
        if bigeop_insight:
            resp.cautions.append(bigeop_insight.warning)
    else:
        resp.answer_summary = f"{pattern.name} 기반 직업 적성 분석"
        careers = CAREER_BY_PATTERN.get(pattern.name, [])
        resp.detailed_analysis = f"격국 {pattern.name}에 맞는 직업: {', '.join(careers[:4]) if careers else '다방면'}"


def _analyze_wealth(resp, wealth, insights, daeun, yongshin, birth_year, target_year):
    """재물운 분석."""
    resp.answer_summary = f"재물 그릇 {wealth.grade}등급 ({wealth.total_score:.0f}점)"

    parts = [f"재물 등급: {wealth.grade} ({wealth.grade_label})"]
    if wealth.peak_periods:
        parts.append(f"전성기: {', '.join(wealth.peak_periods)}")
    if wealth.risk_periods:
        parts.append(f"위험기: {', '.join(wealth.risk_periods)}")

    wealth_insights = [i for i in insights if "재" in i.pattern_name or "식상생재" in i.pattern_name]
    for wi in wealth_insights[:2]:
        parts.append(f"{wi.pattern_name}: {wi.life_impact}")

    resp.detailed_analysis = " | ".join(parts)
    resp.cautions = [i.warning for i in wealth_insights if i.warning]


def _analyze_love(resp, pillars, ten_gods, sinsal, interactions,
                  daeun, gender, insights, birth_year, qtype):
    """연애/결혼 분석."""
    target_cat = "재성" if gender == "남" else "관성"
    count = sum(1 for tg in ten_gods if tg.category == target_cat)

    il_ji_tg = next((tg for tg in ten_gods if tg.position == "일지"), None)

    if count >= 2:
        resp.answer_summary = f"이성 인연이 풍부합니다 ({target_cat} {count}개)"
    elif count == 1:
        resp.answer_summary = "적당한 이성 인연이 있습니다"
    else:
        resp.answer_summary = f"이성 인연이 약합니다 ({target_cat} 0개). 대운에서 인연이 옵니다"

    parts = [f"배우자성({target_cat}): {count}개"]
    if il_ji_tg:
        parts.append(f"배우자궁(일지): {il_ji_tg.ten_god}")

    resp.detailed_analysis = " | ".join(parts)

    # 결혼 시기
    if qtype == "marriage":
        for d in daeun:
            tg_s = d.ten_god_stem or calc_ten_god(pillars.day.stem, d.stem)
            tg_b = d.ten_god_branch or calc_ten_god_for_branch(pillars.day.stem, d.branch)
            s_cat = TEN_GOD_CATEGORIES.get(tg_s, "")
            b_cat = TEN_GOD_CATEGORIES.get(tg_b, "")
            if target_cat in (s_cat, b_cat) and 20 <= d.age_start <= 45:
                yr = birth_year + d.age_start - 1
                resp.timing.append(TimingAdvice(
                    period=f"{d.age_start}~{d.age_end}세",
                    action="결혼 인연이 들어오는 시기",
                    reason=f"대운 {d.stem}{d.branch}에 {target_cat}",
                ))


def _analyze_health(resp, strength, yongshin, sinsal):
    """건강 분석."""
    from .constants import ELEM_ORGAN, HEALTH_WEAKNESS_BY_ELEM
    scores = strength.ohaeng_scores
    weakest = min(scores, key=scores.get) if scores else ""
    resp.answer_summary = f"가장 약한 오행: {weakest} — 관련 장기 주의"
    organ = ELEM_ORGAN.get(weakest, {})
    resp.detailed_analysis = f"약한 오행 {weakest}: {organ.get('장기', '')} / {organ.get('신체', '')} 주의. {HEALTH_WEAKNESS_BY_ELEM.get(weakest, '')}"

    has_baekho = any(s.name == "백호대살" for s in sinsal)
    if has_baekho:
        resp.cautions.append("백호대살 보유 — 사고/수술 수가 있으니 안전에 주의")


def _analyze_yearly(resp, daeun, yongshin, birth_year, target_year, seun, insights):
    """올해/내년 운세."""
    current_age = target_year - birth_year + 1
    current_daeun = None
    for d in daeun:
        if d.age_start <= current_age <= d.age_end:
            current_daeun = d
            break

    parts = [f"{target_year}년 만 {current_age}세"]
    if current_daeun:
        parts.append(f"대운: {current_daeun.stem}{current_daeun.branch}")
    if seun:
        parts.append(f"세운: {seun.stem}{seun.branch}")

    resp.answer_summary = " | ".join(parts)
    resp.detailed_analysis = "세부 분석은 saju_yearly 도구를 함께 사용하면 더 구체적입니다."


def _analyze_study(resp, ten_gods, insights, daeun, yongshin, birth_year, target_year):
    """공부/시험 분석."""
    gwanin = next((i for i in insights if "관인상생" in i.pattern_name), None)
    if gwanin:
        resp.answer_summary = "관인상생 구조로 시험/학업에 유리합니다"
        resp.detailed_analysis = gwanin.causal_chain + " " + gwanin.life_impact
    else:
        has_inseong = any(tg.category == "인성" for tg in ten_gods)
        if has_inseong:
            resp.answer_summary = "인성이 있어 학습 능력이 있습니다"
        else:
            resp.answer_summary = "인성이 약하여 학업보다 실무 경험이 맞을 수 있습니다"


def _analyze_general(resp, insights, strength, pattern):
    """일반 질문."""
    resp.answer_summary = f"{pattern.name}, {strength.label}({strength.score}점)"
    if insights:
        resp.detailed_analysis = insights[0].causal_chain + " " + insights[0].life_impact
```

**Step 2: 검증**

Run: `cd "C:\Users\ganna\saju-mcp" && python -c "
from core.manseryeok import get_four_pillars, get_daeun
from core.ten_gods import get_all_ten_gods, calc_ten_god, calc_ten_god_for_branch
from core.strength import calc_strength
from core.pattern_engine import determine_pattern
from core.yongshin import determine_yongshin
from core.sinsal import detect_sinsal
from core.interactions import detect_interactions
from core.wealth import calc_wealth
from core.cross_analysis import analyze_cross_patterns
from core.deep_consult import deep_consult

p = get_four_pillars(1990, 5, 15, 14)
tg = get_all_ten_gods(p)
d = get_daeun(1990, 5, 15, 14, 0, '남')
for dd in d:
    dd.ten_god_stem = calc_ten_god(p.day.stem, dd.stem)
    dd.ten_god_branch = calc_ten_god_for_branch(p.day.stem, dd.branch)
s = calc_strength(p)
pt = determine_pattern(p, s)
y = determine_yongshin(s, pt)
ss = detect_sinsal(p, d)
ii = detect_interactions(p)
w = calc_wealth(p, s, pt, ii, d)
ci = analyze_cross_patterns(p, tg, s, pt, y, ii, ss, w, d)

for q in ['이직해도 될까?', '올해 재물운은?', '결혼 시기가 언제야?']:
    r = deep_consult(q, p, tg, s, pt, y, ii, ss, w, d, ci, '남', 1990)
    print(f'Q: {q}')
    print(f'A: {r.answer_summary}')
    print(f'   {r.detailed_analysis[:80]}...')
    print()
"`
Expected: 각 질문에 대한 맞춤 답변 출력

**Step 3: Commit**

```bash
git add core/deep_consult.py
git commit -m "feat: add question-based deep consultation engine"
```

---

## Task 6: server.py 통합 — 기존 도구 확장 + 신규 도구

**Files:**
- Modify: `server.py`

**Step 1: import 추가**

`server.py` 상단 import 섹션에 추가:

```python
from core.cross_analysis import analyze_cross_patterns
from core.retrodiction import generate_retrodictions
from core.narrative_engine import generate_narrative
from core.deep_consult import deep_consult
```

**Step 2: `saju_analyze` 함수에 교차 분석 + 역추적 + 서사 추가**

`saju_analyze` 함수 내에서 `interpretation = generate_interpretation_hints(...)` 이후, `result = SajuAnalysisResult(...)` 이전에 다음을 추가:

```python
    # ── 교차 분석 + 역추적 + 서사 (v2) ──
    cross_insights = analyze_cross_patterns(
        pillars=pillars, ten_gods=ten_gods, strength=strength,
        pattern=pattern, yongshin=yongshin, interactions=interactions,
        sinsal=sinsal, wealth=wealth, daeun=daeun, gender=gender,
    )
    retrodictions = generate_retrodictions(
        pillars=pillars, daeun=daeun, birth_year=year,
        interactions=interactions, sinsal=sinsal,
        strength=strength, yongshin=yongshin, gender=gender,
    )
    narrative = generate_narrative(
        pillars=pillars, strength=strength, pattern=pattern,
        yongshin=yongshin, ten_gods=ten_gods,
        cross_insights=cross_insights, retrodictions=retrodictions,
        wealth=wealth, daeun=daeun, gender=gender, birth_year=year,
    )
```

그리고 `SajuAnalysisResult(...)` 생성자에 새 필드 추가:

```python
        cross_insights=cross_insights,
        retrodictions=retrodictions,
        narrative=narrative,
```

**Step 3: 신규 도구 `saju_consult` 추가**

`server.py`에서 `saju_knowledge_context` 함수 바로 위(또는 아래)에 추가:

```python
@server.tool()
def saju_consult(
    question: str,
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "남",
    target_year: int = 2026,
) -> dict:
    """질문 기반 심층 상담.

    구체적 질문(이직, 재물, 연애, 건강 등)에 맞춰
    교차 분석 기반의 심층 답변을 생성합니다.

    Args:
        question: 상담 질문 (예: "이직해도 될까?", "올해 재물운은?", "결혼 시기가 언제야?")
        year: 생년 (양력)
        month: 생월
        day: 생일
        hour: 생시 (기본 12)
        minute: 생분 (기본 0)
        gender: 성별 (기본 "남")
        target_year: 기준 연도 (기본 2026)
    """
    pillars = get_four_pillars(year, month, day, hour, minute)
    ten_gods = get_all_ten_gods(pillars)
    daeun_list = get_daeun(year, month, day, hour, minute, gender)

    day_stem = pillars.day.stem
    for d in daeun_list:
        d.ten_god_stem = calc_ten_god(day_stem, d.stem)
        d.ten_god_branch = calc_ten_god_for_branch(day_stem, d.branch)

    strength = calc_strength(pillars)
    pattern = determine_pattern(pillars, strength)
    yongshin = determine_yongshin(strength, pattern)
    sinsal = detect_sinsal(pillars, daeun_list)
    interactions = detect_interactions(pillars)
    wealth = calc_wealth(pillars, strength, pattern, interactions, daeun_list)

    # 교차 분석
    cross_insights = analyze_cross_patterns(
        pillars=pillars, ten_gods=ten_gods, strength=strength,
        pattern=pattern, yongshin=yongshin, interactions=interactions,
        sinsal=sinsal, wealth=wealth, daeun=daeun_list, gender=gender,
    )

    # 세운 (target_year)
    seun_list = get_seun(year, month, day, hour, minute, gender, target_year)
    seun = seun_list[0] if seun_list else None
    if seun:
        seun.ten_god_stem = calc_ten_god(day_stem, seun.stem)
        seun.ten_god_branch = calc_ten_god_for_branch(day_stem, seun.branch)

    result = deep_consult(
        question=question,
        pillars=pillars,
        ten_gods=ten_gods,
        strength=strength,
        pattern=pattern,
        yongshin=yongshin,
        interactions=interactions,
        sinsal=sinsal,
        wealth=wealth,
        daeun=daeun_list,
        cross_insights=cross_insights,
        gender=gender,
        birth_year=year,
        target_year=target_year,
        seun=seun,
    )

    return result.model_dump()
```

**Step 4: 검증**

Run: `cd "C:\Users\ganna\saju-mcp" && python -c "from server import server; print('Server OK, tools:', len(server._tool_manager._tools))"`
Expected: `Server OK, tools: 12` (기존 11 + saju_consult 1)

**Step 5: 통합 테스트**

Run: `cd "C:\Users\ganna\saju-mcp" && python -c "
from server import saju_analyze, saju_consult

# 전체 분석 테스트
result = saju_analyze(1990, 5, 15, 14, 0, '남')
print('=== saju_analyze ===')
print('cross_insights:', len(result.get('cross_insights', [])))
print('retrodictions:', len(result.get('retrodictions', [])))
narr = result.get('narrative', {})
if narr:
    print('one_line:', narr.get('one_line', ''))
    print('top3:', narr.get('top3_insights', []))
print()

# 상담 테스트
consult = saju_consult('이직해도 될까?', 1990, 5, 15, 14, 0, '남')
print('=== saju_consult ===')
print('Q:', consult['question'])
print('A:', consult['answer_summary'])
print('Detail:', consult['detailed_analysis'][:100])
"`
Expected: 교차 분석, 역추적, 서사, 상담 결과 모두 출력

**Step 6: Commit**

```bash
git add server.py
git commit -m "feat: integrate expert engine into saju_analyze + add saju_consult tool"
```

---

## Task 7: MCP 서버 재시작 + 실전 테스트

**Step 1: MCP 서버 재시작**

Claude Code에서 `/mcp` 명령으로 saju-mcp 재연결

**Step 2: 실전 테스트**

`saju_analyze`로 실제 사주 분석 후:
- `cross_insights` 필드에 교차 분석 결과가 나오는지 확인
- `retrodictions` 필드에 과거 역추적이 나오는지 확인
- `narrative` 필드에 종합 서사가 나오는지 확인

`saju_consult`로 질문 기반 상담 테스트:
- "이직해도 될까?"
- "올해 재물운은?"
- "결혼 시기가 언제야?"

**Step 3: 최종 commit**

```bash
git add -A
git commit -m "feat: complete expert engine v2 - cross analysis, retrodiction, narrative, consult"
```
