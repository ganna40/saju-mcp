# 연도별 구체적 사건 예측 엔진 설계

## 목적

기존 `saju_yearly` 도구의 세운 분석에 **구체적 사건 시나리오**와 **만남의 인물 유형** 예측을 추가한다. 현재는 세운 간지/십신/신살 발동/합충 같은 구조적 데이터만 반환하지만, 이를 조합하여 "이 해에 이런 일이 일어날 가능성이 높다"는 수준의 구체적 예측을 생성한다.

## 핵심 설계

### 새 모듈: `core/yearly_events.py`

세운 십신 + 대운 십신 + 신살 발동 + 합충 + 용신 관계 + 연령대 + 성별을 조합하여 이벤트를 생성하는 규칙 엔진.

### 이벤트 카테고리 6개

| 카테고리 | 예측 근거 |
|---------|----------|
| career | 관성/식상 + 역마살/장성살 |
| wealth | 재성 + 식상생재 + 재고 |
| relationship | 비겁/인성 + 도화살/천을귀인 |
| love | 정재/정관 + 도화살 + 배우자궁 |
| health | 기신 + 백호대살 + 오행 불균형 |
| change | 충/형 + 역마살 + 겁살 |

### 이벤트 생성 입력

```
세운 십신(천간/지지 카테고리)
+ 현재 대운 십신(천간/지지 카테고리)
+ 세운↔원국 합충형파해
+ 세운에서 발동하는 신살
+ 용신/기신 관계 (세운 오행이 용신인지 기신인지)
+ 연령대 (청년/중년/장년)
+ 성별
→ 구체적 이벤트 시나리오 리스트
```

### 인물 유형 매핑

세운의 십신을 만남의 인물 유형으로 변환:
- 비견 → 동료/친구/경쟁자
- 겁재 → 라이벌/사업 파트너
- 식신 → 제자/후배/자녀
- 상관 → 자유로운 예술가/반항적 인물
- 편재 → 사업가/투자자
- 정재 → 성실한 배우자감/재무 관련 인물
- 편관 → 상사/권력자/엄격한 사람
- 정관 → 신뢰할 수 있는 리더/남편감
- 편인 → 특이한 스승/비주류 멘토
- 정인 → 어머니 같은 인물/전통적 스승

### 조합 규칙 (핵심)

약 50~60개 규칙. 우선순위:
1. 세운+대운 십신 조합 규칙 (관인상생, 식상생재, 상관견관 등)
2. 신살 발동 규칙 (역마살+충 → 이동, 도화살+재성 → 연애)
3. 합충 규칙 (배우자궁 충 → 이별, 월주 합 → 직장 변화)
4. 용신/기신 보정 (용신이면 확률↑, 기신이면 주의)
5. 연령대 필터 (20대 결혼 vs 50대 건강)

## 모델 변경

```python
class YearlyEvent(BaseModel):
    category: str       # career/wealth/relationship/love/health/change
    title: str          # "승진 가능성 높음"
    description: str    # 구체적 설명 2~3문장
    probability: str    # 높음/중간/낮음
    trigger: str        # "세운 정관 + 대운 인성 = 관인상생"
    advice: str         # "적극적으로 시험/승진에 도전하세요"

class PersonEncounter(BaseModel):
    ten_god: str        # "정관"
    person_type: str    # "신뢰할 수 있는 리더"
    context: str        # "직장에서 좋은 상사를 만날 가능성"
    influence: str      # 긍정적/부정적/중립

# YearlyResult 확장
yearly_events: list[YearlyEvent] = []
person_encounters: list[PersonEncounter] = []
current_daeun: DaeunEntry | None = None
overall_fortune: str = ""
```

## 파일 변경 범위

| 파일 | 변경 내용 |
|------|----------|
| `core/yearly_events.py` | 새 파일 — 이벤트 예측 엔진 |
| `core/constants.py` | 인물 유형 매핑, 이벤트 규칙 테이블 추가 |
| `core/models.py` | YearlyEvent, PersonEncounter 추가, YearlyResult 확장 |
| `server.py` | saju_yearly에 새 로직 연결 |
