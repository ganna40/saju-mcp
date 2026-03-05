"""1989-02-07 남성 사주보고서 + 5개 질문 PDF 생성."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from datetime import datetime
from core.export_pdf import (
    SajuPDF, C_PRIMARY, C_ACCENT, C_TEXT, C_WHITE, C_SUCCESS,
    C_WARNING, C_DANGER, C_GREAT, C_LIGHT, C_DIVIDER, _verdict_color,
)
from core.models import SajuReport
from server import saju_report

# ── 데이터 ──
report_data = saju_report(year=1989, month=2, day=7, hour=4, minute=35, gender="남")
report = SajuReport(**report_data)

output_dir = r"C:\Users\ganna\OneDrive\바탕 화면"
os.makedirs(output_dir, exist_ok=True)
filename = f"사주보고서_19890207_남_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
filepath = os.path.join(output_dir, filename)

pdf = SajuPDF()
C_QBLUE = (41, 128, 185)

# ============================================================
# 표지
# ============================================================
pdf.add_page()
pdf.ln(30)
pdf.set_fill_color(*C_PRIMARY)
pdf.rect(10, 10, 190, 4, "F")

pdf.set_font("gothic", "B", 28)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 15, "사주 성패 보고서", align="C")
pdf.ln(3)

pdf.set_font("gothic", "", 11)
pdf.set_text_color(*C_ACCENT)
pdf._cell_ln(0, 8, "1989년 2월 7일 4시 35분생 (남)", align="C")
pdf.ln(2)

pdf.set_font("gothic", "B", 22)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 12, "기사 병인 무술 갑인", align="C")
pdf.ln(3)

pdf.set_font("gothic", "", 10)
pdf.set_text_color(*C_ACCENT)
pdf._cell_ln(0, 7, "일간: 무토 / 격국: 편관격 / 신강도: 중화(53.9)", align="C")
pdf._cell_ln(0, 7, "용신: 금(金) / 적성: 조직/관리/권위", align="C")
pdf.ln(8)

ov = report.overall
vc = _verdict_color(ov.verdict)
pdf.set_font("gothic", "B", 52)
pdf.set_text_color(*vc)
pdf._cell_ln(0, 28, f"{ov.score:.0f}", align="C")
pdf.set_font("gothic", "", 14)
pdf.set_text_color(*C_ACCENT)
pdf._cell_ln(0, 10, f"/ 100점   {ov.verdict}", align="C")
pdf.ln(4)
pdf.set_font("gothic", "", 11)
pdf.set_text_color(*C_TEXT)
pdf._cell_ln(0, 8, ov.summary, align="C")

pdf.ln(12)
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_LIGHT)
pdf._cell_ln(0, 6, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")
pdf._cell_ln(0, 6, "* 5개 맞춤 질문 답변 포함", align="C")

# ============================================================
# 종합 성패표
# ============================================================
pdf.add_page()
pdf._title_bar("종합 성패표")

headers = ["영역", "점수", "판정", "요약"]
rows = []
for sec in report.sections:
    rows.append([sec.title, f"{sec.score:.0f}", sec.verdict, sec.summary[:28]])
pdf._table(headers, rows, [22, 18, 22, 128], highlight_col=2)

pdf.ln(2)
pdf.set_font("gothic", "B", 10)
pdf._cell_ln(0, 7, f"종합점수 {ov.score:.0f}/100")
pdf._score_bar(ov.score, 100)

for idx, sec in enumerate(report.sections, 1):
    if pdf.get_y() > 225:
        pdf.add_page()
    pdf._divider()
    pdf._section_header(idx, sec.title, sec.verdict, sec.score)
    pdf._score_bar(sec.score, 100)
    pdf._summary_line(sec.summary)
    pdf._detail_lines(sec.details)

# 총평
pdf.add_page()
pdf._title_bar("총평", C_ACCENT)
pdf._detail_lines(ov.details)

# ============================================================
# Q1: 이직운
# ============================================================
pdf.add_page()
pdf._title_bar("Q1. 이직운 - 왜 안 되었고, 언제 가능한가?", C_QBLUE)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "이직이 안 된 구조적 이유")
pdf.ln(1)

reasons = [
    "1. 편관 3개 = 조직에 강하게 묶이는 구조",
    "   시간(갑), 시지(인), 월지(인) 모두 편관. 조직이 본인을 놓아주지 않음",
    "",
    "2. 식상 0개 = 변화를 만들어내는 에너지가 원국에 전혀 없음",
    "   식상은 새로운 시도/행동력의 별. 0개이면 기존 틀을 깨는 힘이 없음",
    "",
    "3. 재성 0개 = 더 좋은 조건을 끌어당기는 힘이 없음",
    "   이직은 더 좋은 대우(재성)를 찾는 행위인데, 원국에 재성 자체가 없음",
    "",
    "4. 갑기합(시간+년간) = 편관이 겁재와 합하여 안정화",
    "   조직의 압력(편관)이 합에 의해 묶여 있어 변동이 억제됨",
    "",
    "5. 32~41세 임술 대운(현재) = 편재/비견",
    "   비견이 경쟁 환경 -> 현 위치 사수 에너지가 우세",
    "",
    "=> 결론: 조직에 묶인 편관3 + 변화 에너지(식상) 0",
    "   = 불만은 있지만 떠나지 못하는 구조",
]
pdf._detail_lines(reasons)

pdf._divider()
pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "이직 가능 시점 분석")
pdf.ln(1)

h2 = ["연도", "나이", "세운", "십신", "이직 신호"]
r2 = [
    ["2028", "39세", "무신", "비견/식신", "인신충(x2) 원국 편관 깨짐+식신(용신)"],
    ["2029", "40세", "기유", "겁재/상관", "상관(관 제어)+용신 발동"],
    ["2031", "42세", "신해", "상관/편재", "사해충+겁살 발동+상관견관"],
]
pdf._table(h2, r2, [18, 14, 18, 30, 110])

pdf.set_font("gothic", "B", 9)
pdf.set_text_color(*C_DANGER)
pdf.multi_cell(190, 5, "** 최적 이직 시점: 2028년(39세)")
pdf.ln(1)
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
pdf.multi_cell(190, 5, "인신충 2개가 원국 편관(인)을 깨뜨리며, 식신(용신 금)이 변화 에너지를 공급. 사신합도 동시에 걸려 새로운 조직과 결합하는 구조.")
pdf.ln(1)
pdf.multi_cell(190, 5, "2031년(42세)은 대운이 신유(상관)로 바뀌며 더 큰 변동. 사해충+겁살 = 과감한 결단. 이직보다 독립/전직 수준의 큰 변화.")
pdf.ln(1)
pdf.multi_cell(190, 5, "조언: 2028년을 노리되, 글쓰기/발표/대외활동 등 식상(표현력) 보강을 미리 시작할 것. 원국에 식상이 0이므로 자연스럽게는 안 생김.")

# ============================================================
# Q2: IT 대기업 승진
# ============================================================
pdf.add_page()
pdf._title_bar("Q2. IT 대기업 승진 - 어디까지, 임원 시기?", C_QBLUE)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "대기업 적합도 분석")
pdf.ln(1)

h3 = ["요소", "내용", "판정"]
r3 = [
    ["편관격", "카리스마+결단력, 조직 두각", "최적"],
    ["관성 3개", "조직 충성도+책임감 극강", "최적"],
    ["인성 2개(편인)", "전문성/학습력 기반", "적합"],
    ["학당귀인", "학문/기술 이해력", "적합"],
    ["직장운 79점", "조직형 체질 (성)", "적합"],
    ["적성 80점", "조직/관리/권위 대성", "최적"],
    ["식상 0개", "기술 개발은 안 맞음", "관리직 전환 필수"],
]
pdf._table(h3, r3, [38, 90, 62])

pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
pdf.multi_cell(190, 5, "=> IT 대기업에서 개발자가 아닌 관리자/전략가/임원 트랙이 최적. 편관격은 조직의 위계와 권력 구조에서 가장 잘 작동하는 격국.")
pdf.ln(3)

pdf._divider()
pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "대운별 승진 로드맵")
pdf.ln(1)

h4 = ["나이", "대운", "십신", "직장 내 위치"]
r4 = [
    ["32~41", "임술", "편재/비견", "중간관리자. 비견=경쟁 환경. 성과로 어필"],
    ["42~51", "신유", "상관/상관", "핵심! 칠살제화=권력 다루는 능력. 최대 상승기"],
    ["52~61", "경신", "식신/식신", "식신제살=안정적 고위직. 조직의 어른 역할"],
    ["62~71", "기미", "겁재/겁재", "은퇴 or 고문직. 후진 양성"],
]
pdf._table(h4, r4, [22, 18, 30, 120])

pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_DANGER)
pdf.multi_cell(190, 5, "임원 진입 예상 시기: 45~48세 (2034~2037년)")
pdf.ln(1)
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
pdf.multi_cell(190, 5, "42세부터 대운 신유(상관) 시작 = 용신 대운. 조직 내 영향력 극대화.")
pdf.ln(1)
pdf.multi_cell(190, 5, "2035년(46세) 을묘 세운 = 정관/정관 + 술묘합(결합) = 조직과 하나가 되는 해. 임원 발탁 가장 유력.")
pdf.ln(1)
pdf.multi_cell(190, 5, "52세 이후 경신 대운(식신)도 용신 대운 연속 = 60세까지 고위직 유지 가능. 합산 20년간 용신 대운.")
pdf.ln(2)
pdf.set_font("gothic", "B", 9)
pdf.set_text_color(*C_ACCENT)
pdf.multi_cell(190, 5, "=> 예상 최고 직위: 상무~전무급 (임원 10년+). VP/SVP 레벨 도달 가능.")

# ============================================================
# Q3: 자산 규모
# ============================================================
pdf.add_page()
pdf._title_bar("Q3. 직장 성공 시 자산 - 얼마까지?", C_QBLUE)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "원국 재물 구조")
pdf.ln(1)

wealth_lines = [
    "재물그릇: F등급 (5.7/100점) - 원국 재물 축적력 매우 약함",
    "재성 0개 / 식상 0개 / 식상생재 0점 / 재성통근 0점",
    "",
    "=> 사업/투자로 큰 돈을 버는 사주가 절대 아님",
    "=> 높은 직위의 안정적 급여를 꾸준히 모으는 축적형",
]
pdf._detail_lines(wealth_lines)

pdf._divider()
pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "자산 축적 시나리오")
pdf.ln(1)

h5 = ["구분", "시기", "주요 수입원", "예상 축적"]
r5 = [
    ["축적기", "30대~40대 초", "대기업 연봉+성과급", "3~5억 (근로소득)"],
    ["가속기", "45~55세 (임원기)", "임원 연봉+인센티브+RSU", "10~15억 추가"],
    ["안정기", "55~61세", "고위 임원 보상", "5~10억 추가"],
]
pdf._table(h5, r5, [22, 35, 68, 65])

pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_ACCENT)
pdf.multi_cell(190, 5, "예상 순자산: 15~25억 수준 (부동산 포함 시 상향)")
pdf.ln(2)

asset_notes = [
    "이 사주의 자산 축적은 전적으로 직위에 연동됨.",
    "재성이 없으므로 부동산/주식 투자 감각은 약함 - 전문가 위임 필수.",
    "",
    "절대 금물:",
    "  - 사업 (재성 0 + 식상 0 = 돈을 불리는 감각 없음)",
    "  - 동업 (겁재가 년간에 있어 동업자와 갈등)",
    "  - 고위험 투자 (원국에 재물 방어 구조 전무)",
    "",
    "추천 전략:",
    "  - 급여의 일정 비율 자동 적립/인덱스 펀드",
    "  - 스톡옵션/RSU 장기 보유",
    "  - 부동산은 실거주 1채 중심",
    "  - 재테크는 직접 하지 말고 전문가에게 위임",
]
pdf._detail_lines(asset_notes)

# ============================================================
# Q4: 부모와의 인연
# ============================================================
pdf.add_page()
pdf._title_bar("Q4. 부모와의 인연은 어떠한가?", C_QBLUE)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "원국 부모 관련 구조")
pdf.ln(1)

h6 = ["요소", "내용", "해석"]
r6 = [
    ["인성(어머니)", "편인 2개 (년지, 월간)", "어머니 영향 강하나 관계 복잡"],
    ["정인", "0개", "전통적 따뜻한 돌봄 부족"],
    ["재성(아버지)", "0개", "아버지 인연 약하거나 소원"],
    ["년간", "겁재(기토)", "초년 형제/가정 내 경쟁"],
    ["사인해", "년지-월지/시지", "초년 가정 내 불편한 관계"],
    ["갑기합", "시간+년간 천간합", "본인이 가족 중재자 역할"],
]
pdf._table(h6, r6, [30, 52, 108])

pdf.ln(1)
pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 7, "아버지와의 인연")
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
father = [
    "재성(아버지별) 0개 = 아버지와의 인연이 구조적으로 약함.",
    "아버지의 부재, 소원한 관계, 또는 아버지가 가정 내 존재감이 약한 형태.",
    "아버지로부터 물질적/정서적 지원을 받기 어려운 구조.",
    "스스로 일어서야 하는 자수성가형 구조와 연결됨.",
]
pdf._detail_lines(father)

pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 7, "어머니와의 인연")
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
mother = [
    "편인 2개 = 어머니의 영향력은 매우 강하나, 관계의 질이 복잡함.",
    "편인은 비정통적 양육 - 따뜻한 정(정인)보다 기대/간섭/교육열이 높은 형태.",
    "어머니가 본인에게 거는 기대가 크고, 그것이 때로 부담이 될 수 있음.",
    "",
    "하지만 편인은 학문/전문성의 원천이기도 하여,",
    "어머니의 영향으로 학업/커리어의 기초가 다져졌을 가능성이 높음.",
    "",
    "정인 0개이므로 무조건적 사랑/수용보다는 조건부 인정의 패턴.",
    "어머니와의 관계 개선이 이 사주의 정서적 안정에 중요한 열쇠가 됨.",
]
pdf._detail_lines(mother)

pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 7, "초년기 가정 환경")
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
family = [
    "년간 겁재 = 유년기에 형제나 가정 내 경쟁/갈등 환경 존재.",
    "사인해(년지-월지/시지) = 가족 관계 내 미세한 불편함/거리감.",
    "화개살(일지) 2~11세 발동 = 어린 시절 혼자만의 세계에 빠지거나 고독.",
    "",
    "이 구조는 부모로부터 정서적 독립을 일찍 경험한 사주를 의미.",
    "오히려 이것이 편관격 특유의 자립심/책임감을 키운 원동력이 됨.",
]
pdf._detail_lines(family)

# ============================================================
# Q5: 인생의 과업
# ============================================================
pdf.add_page()
pdf._title_bar("Q5. 이 사람의 인생 과업", C_QBLUE)

pdf.set_font("gothic", "B", 13)
pdf.set_text_color(*C_PRIMARY)
pdf.ln(3)
pdf._cell_ln(0, 10, "큰 산이 품은 광석을 세상에 내놓는 것", align="C")
pdf.ln(5)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "무토(戊土) 일간의 본질")
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
nature = [
    "무토 = 큰 산. 움직이지 않으며 주변을 품고 안정시키는 존재.",
    "큰 산은 나무(목)를 키우고, 광물(금)을 품고, 물(수)을 저장함.",
    "이 사주의 본질은 많은 것을 품되, 세상에 필요한 형태로 꺼내는 것.",
]
pdf._detail_lines(nature)

pdf._divider()
pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "핵심 과업: 표현의 통로를 여는 것")
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
mission = [
    "이 사주의 가장 큰 과제는 식상 0개라는 구조적 결핍.",
    "",
    "식상 = 표현력, 아이디어, 자기 배출의 에너지.",
    "원국에 식상이 하나도 없다 = 안에 많은 것을 품고 있지만 꺼내지 못함.",
    "",
    "편관 3개(조직 압력) + 인성 2개(지식 축적) + 식상 0개(표현 제로)",
    "= 할 말은 많은데 표현이 안 되는, 능력은 있는데 어필이 안 되는 삶의 패턴.",
    "",
    "용신이 금(=식상/재성)인 이유가 여기에 있음.",
    "금은 토(본인)를 깎아서 만들어지는 것 - 자신을 깎아내려 결과물을 만들어야 함.",
    "",
    "42세 이후 상관/식신 대운이 시작되면, 비로소 표현의 통로가 열림.",
    "이 시기가 이직, 승진, 인생 전환점이 모두 겹치는 이유.",
]
pdf._detail_lines(mission)

pdf._divider()
pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "구체적 인생 과업 3가지")
pdf.ln(1)

tasks = [
    "1. 리더로서 조직을 이끌고 시스템을 만드는 것",
    "   편관격 + 관성 3개 = 세상의 혼란을 다스리는 것이 천명.",
    "   단순히 높은 자리가 아니라, 조직을 체계화하고 방향을 제시하는 것.",
    "   IT 대기업 임원으로 가야 하는 사주적 이유.",
    "",
    "2. 사람을 키우고 지식을 전달하는 것",
    "   학당귀인(월지+시지) = 가르침/교육과의 인연.",
    "   화개살 = 깊은 학문적 탐구.",
    "   축적한 경험과 지혜를 후배에게 전달하는 멘토 역할이 후반생의 핵심.",
    "   52세 이후 식신 대운에서 이 역할이 본격화됨.",
    "",
    "3. 자기 표현의 훈련 (평생 숙제)",
    "   식상 0개 = 표현에 서투른 것이 아킬레스건.",
    "   보고서 작성, 프레젠테이션, 글쓰기, 대외 강연 등",
    "   의도적으로 식상을 보완하는 활동이 승진/이직/인생 전반의 열쇠.",
    "   42세 이전에 이 훈련을 해놓으면, 대운 식상이 올 때 폭발적 성장.",
]
pdf._detail_lines(tasks)

pdf.ln(2)
pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_ACCENT)
pdf.multi_cell(190, 6, "결론: 42세부터 열리는 용신 대운 20년이 인생의 꽃. 그때까지 식상(표현력)을 키우는 것이 가장 중요한 준비.")

# ============================================================
# 인생 타임라인 종합
# ============================================================
pdf.add_page()
pdf._title_bar("인생 타임라인 종합", C_ACCENT)

h7 = ["나이", "대운", "십신", "핵심 이벤트"]
r7 = [
    ["32~41", "임술", "편재/비견", "현재. 경쟁 속 내실 다지기. 이직 준비기"],
    ["39세", "2028 무신", "식신(용신)", "최적 이직 시점. 인신충 x2 = 조직 변동"],
    ["42세~", "신유", "상관/상관", "용신 대운 시작! 승진 가속기"],
    ["46세", "2035 을묘", "정관+술묘합", "임원 발탁 유력. 조직과 결합"],
    ["52세~", "경신", "식신/식신", "용신 대운 연속. 안정적 고위직"],
    ["55~60", "임원 안정기", "-", "멘토/교육자 역할 본격화"],
    ["62세~", "기미", "겁재/겁재", "은퇴/고문. 후진 양성"],
]
pdf._table(h7, r7, [16, 24, 28, 122])

pdf.ln(3)
pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 7, "핵심 메시지")
pdf.ln(1)
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
msgs = [
    "1) 2028년(39세)까지 식상(표현력) 보강에 집중 -> 이직/승진의 결정적 무기",
    "2) 42세 이후 20년간 용신 대운 = 인생 황금기. 이 시기를 위해 지금 준비",
    "3) 사업/투자는 절대 금물. 직장인으로서의 최고 경지를 목표로",
    "4) 부모(특히 어머니)와의 관계 정리가 정서적 안정의 열쇠",
    "5) 큰 산이 광석을 내놓듯, 경험과 지혜를 세상에 표현하는 것이 인생 과업",
]
for m in msgs:
    pdf.multi_cell(190, 5, m)
    pdf.ln(1)

# 하단 장식
pdf.set_fill_color(*C_PRIMARY)
pdf.rect(10, 283, 190, 3, "F")

pdf.output(filepath)
print(f"저장 완료: {filepath}")
