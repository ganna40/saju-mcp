"""1992-05-01 남성 사주보고서 + 큰돈 분석 PDF 생성."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from datetime import datetime
from core.export_pdf import (
    SajuPDF, C_PRIMARY, C_ACCENT, C_TEXT, C_WHITE, C_SUCCESS,
    C_WARNING, C_DANGER, C_GREAT, C_LIGHT, C_DIVIDER, _verdict_color,
)
from core.models import SajuReport
from server import saju_report

report_data = saju_report(year=1992, month=5, day=1, hour=18, minute=0, gender="남")
report = SajuReport(**report_data)

output_dir = r"C:\Users\ganna\OneDrive\바탕 화면"
os.makedirs(output_dir, exist_ok=True)
filename = f"사주보고서_19920501_남_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
pdf._cell_ln(0, 8, "1992년 5월 1일 18시 0분생 (남)", align="C")
pdf.ln(2)

pdf.set_font("gothic", "B", 22)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 12, "임신 갑진 정축 기유", align="C")
pdf.ln(3)

pdf.set_font("gothic", "", 10)
pdf.set_text_color(*C_ACCENT)
pdf._cell_ln(0, 7, "일간: 정화(촛불) / 격국: 상관격 / 신강도: 신약(18.7)", align="C")
pdf._cell_ln(0, 7, "용신: 목(木) / 적성: 창작/표현/기술", align="C")
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
pdf._cell_ln(0, 6, "* 큰돈 시기 분석 포함", align="C")

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
# 큰돈 분석
# ============================================================
pdf.add_page()
pdf._title_bar("Q. 언제쯤 큰돈을 벌 수 있나?", C_QBLUE)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "원국 재물 구조 분석")
pdf.ln(1)

h1 = ["항목", "내용", "점수"]
r1 = [
    ["재물그릇", "D등급 (24점/100점)", "약함"],
    ["재성", "2개 (년지 정재, 시지 편재)", "있음"],
    ["식상생재", "만점 (식상 3개 -> 재성 생)", "15/15"],
    ["재성 통근", "8점 (뿌리 있음)", "8/15"],
    ["신약 보정", "-15점 (신약 18.7점)", "-15"],
    ["합충 보정", "+3점 (합 4개, 충 0개)", "+3"],
]
pdf._table(h1, r1, [35, 105, 50])

pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
structure = [
    "이 사주의 재물 구조 핵심:",
    "",
    "장점: 식상 3개 + 재성 2개 = 능력으로 돈 버는 통로(식상생재)가 열려 있음",
    "      합이 4개로 충이 0개 = 재물이 흩어지지 않는 안정적 구조",
    "",
    "약점: 신약(18.7점) = 몸이 약해서 큰돈을 감당하기 어려움",
    "      진유합(->금=기신) = 재물을 향한 에너지가 기신 방향으로 흐름",
    "      = 돈을 벌수록 체력이 빠지는 구조(설기 과다)",
    "",
    "=> 결론: 큰돈을 한방에 버는 사주가 아니라,",
    "   재능/기술(식상)로 꾸준히 수입을 만드는 전문가형 사주",
]
pdf._detail_lines(structure)

pdf._divider()
pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "대운별 재물 흐름")
pdf.ln(1)

h2 = ["나이", "대운", "십신", "재물 테마"]
r2 = [
    ["22~31", "정미", "비견/식신", "현재. 비견이 힘 보충+식신 활동. 기초 축적기"],
    ["32~41", "무신", "상관/정재", "첫 번째 식상생재 대운! 수입 상승 시작"],
    ["42~51", "기유", "식신/편재", "두 번째 식상생재+도화살 발동. 인맥 수입"],
    ["52~61", "경술", "정재/상관", "세 번째. 정재 직접 대운. 안정적 큰 수입"],
    ["62~71", "신해", "편재/정관", "편재+관 조합. 조직 내 고수입 or 은퇴 자금"],
]
pdf._table(h2, r2, [16, 16, 28, 130])

pdf.set_font("gothic", "B", 9)
pdf.set_text_color(*C_ACCENT)
pdf.multi_cell(190, 5, "=> 32세부터 40년간(32~71세) 4개 대운 연속 재성 대운! 재물 기회가 매우 길게 이어짐.")
pdf.ln(3)

# 큰돈 시점
pdf.add_page()
pdf._title_bar("큰돈 시점 분석", C_QBLUE)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "근거리: 30대 (무신 대운)")
pdf.ln(1)

h3 = ["연도", "나이", "세운", "십신", "재물 신호"]
r3 = [
    ["2027", "35세", "정미", "비견/식신", "식상생재 시작. 자기 힘+기술로 첫 수입원"],
    ["2028", "36세", "무신", "상관/정재", "세운=대운 일치! 에너지 극대화. 상관생재"],
    ["2029", "37세", "기유", "식신/편재", "편재 직접 유입. 큰 한건 가능성"],
    ["2030", "38세", "경술", "정재/상관", "정재+식상생재. 안정적 큰 수입"],
    ["2031", "39세", "신해", "편재/정관", "편재+관 = 조직 내 큰 보상/성과급"],
]
pdf._table(h3, r3, [18, 14, 18, 28, 112])

pdf.set_font("gothic", "B", 9)
pdf.set_text_color(*C_DANGER)
pdf.multi_cell(190, 5, "** 2028~2031 (36~39세) = 30대 큰돈 구간. 특히 2028년은 세운과 대운이 동일(무신)하여 식상생재 에너지가 최대치.")
pdf.ln(1)
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
pdf.multi_cell(190, 5, "단, 기신(금/토) 방향이라 벌면서 빠지는 구조. 건강 관리가 필수.")
pdf.ln(3)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "중거리: 40대 (기유 대운) - 인생 최대 재물기")
pdf.ln(1)

r4 = [
    ["2038", "46세", "무오", "상관/비견", "상관+비견=힘있는 식상생재. 체력 보충됨"],
    ["2039", "47세", "기미", "식신/식신", "쌍식신! 재능 폭발. 다방면 수입"],
    ["2040", "48세", "경신", "정재/정재", "쌍정재+식상생재 = 최대 정재 해"],
    ["2041", "49세", "신유", "편재/편재", "쌍편재+식상생재 = 최대 횡재 해"],
    ["2042", "50세", "임술", "정관/상관", "식상생재+관성 = 직위 연동 큰 수입"],
]
pdf._table(h3, r4, [18, 14, 18, 28, 112])

pdf.set_font("gothic", "B", 9)
pdf.set_text_color(*C_DANGER)
pdf.multi_cell(190, 5, "** 2040~2041 (48~49세) = 인생 최대 재물 포인트!")
pdf.ln(1)
pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
pdf.multi_cell(190, 5, "대운 기유(식신/편재) + 세운 쌍정재/쌍편재 = 식상생재 완전체. 도화살(42~51세 발동)+장성살 = 인맥과 리더십을 활용한 큰 수입. 이 시기가 인생에서 가장 큰 돈을 만질 수 있는 기간.")
pdf.ln(3)

pdf.set_font("gothic", "B", 11)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 8, "원거리: 50대 (경술 대운)")
pdf.ln(1)

r5 = [
    ["2048", "56세", "무진", "상관/상관", "대운 정재+세운 상관 = 식상생재 지속"],
    ["2050", "58세", "경오", "정재/비견", "정재+비견(용신!) = 드물게 용신과 맞는 재물"],
    ["2052", "60세", "임신", "정관/정재", "관+재 동시 = 명예와 재물"],
]
pdf._table(h3, r5, [18, 14, 18, 28, 112])

pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_ACCENT)
pdf.multi_cell(190, 5, "50대는 정재 대운 = 안정적이고 꾸준한 큰 수입. 2050년(58세)이 특별히 좋은 해 - 정재+비견(화=용신)이 동시에 와서 건강도 좋고 돈도 들어옴.")
pdf.ln(3)

# 핵심 요약
pdf._divider()
pdf.set_font("gothic", "B", 12)
pdf.set_text_color(*C_PRIMARY)
pdf._cell_ln(0, 9, "큰돈 핵심 요약")
pdf.ln(2)

h4 = ["순위", "시기", "유형", "강도"]
r4s = [
    ["1위", "2040~2041 (48~49세)", "쌍정재/쌍편재+식상생재+도화살", "최강"],
    ["2위", "2028~2031 (36~39세)", "무신 대운 식상생재 연속", "강"],
    ["3위", "2050 (58세)", "정재+용신(비견화) 동시", "강 (건강+재물)"],
    ["4위", "42~71세 전체", "40년 연속 재성 대운", "지속"],
]
pdf._table(h4, r4s, [18, 48, 80, 44])

pdf.ln(2)
pdf.set_font("gothic", "B", 10)
pdf.set_text_color(*C_ACCENT)
pdf.multi_cell(190, 6, "이 사주의 큰돈 패턴: 한방이 아닌 꾸준한 축적형. 식상(재능/기술)이 곧 돈줄. 건강이 곧 재물운.")
pdf.ln(2)

pdf.set_font("gothic", "", 9)
pdf.set_text_color(*C_TEXT)
advice = [
    "핵심 조언:",
    "",
    "1. 전문 기술/재능을 극대화할 것 (식상생재형)",
    "   - 상관격+식상 3개 = 창작/기술/아이디어가 돈의 원천",
    "   - IT개발, 디자인, 작가, 컨설팅 등 전문 분야에서 단가를 올리는 전략",
    "",
    "2. 건강 관리가 곧 재물 관리 (신약 18.7점)",
    "   - 돈을 벌수록 체력이 빠지는 구조",
    "   - 큰돈 시기(36~49세)에 특히 건강 투자 필수",
    "   - 용신(목) = 간/담 관리, 초록 채소, 산책, 동쪽 방향",
    "",
    "3. 30대에 기반을 닦고, 40대 후반에 수확할 것",
    "   - 2028~2031에 전문성과 인맥을 쌓으면",
    "   - 2040~2041에 가장 큰 열매를 거둘 수 있음",
    "",
    "4. 사업보다 전문직/프리랜서가 체질에 맞음",
    "   - 상관격은 조직보다 자유로운 환경에서 빛남",
    "   - 인세/로열티/컨설팅 수입 = 체력 소모 최소화하며 수입 극대화",
]
pdf._detail_lines(advice)

# 하단 장식
pdf.set_fill_color(*C_PRIMARY)
pdf.rect(10, 283, 190, 3, "F")

pdf.output(filepath)
print(f"저장 완료: {filepath}")
