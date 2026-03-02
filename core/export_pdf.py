"""보고서 PDF 내보내기 — 색상 + 표 + 포맷팅."""
from __future__ import annotations

import os
from datetime import datetime
from fpdf import FPDF, XPos, YPos

from .models import SajuReport, CompatReport

# ── 색상 팔레트 ──
C_PRIMARY = (44, 62, 80)
C_ACCENT = (52, 73, 94)
C_SUCCESS = (39, 174, 96)
C_WARNING = (243, 156, 18)
C_DANGER = (231, 76, 60)
C_GREAT = (142, 68, 173)
C_TEXT = (44, 62, 80)
C_LIGHT = (149, 165, 166)
C_TABLE_HEAD = (52, 73, 94)
C_TABLE_ROW1 = (255, 255, 255)
C_TABLE_ROW2 = (241, 245, 249)
C_DIVIDER = (189, 195, 199)
C_WHITE = (255, 255, 255)

OHAENG_COLORS = {
    "목": (76, 175, 80),
    "화": (244, 67, 54),
    "토": (255, 193, 7),
    "금": (158, 158, 158),
    "수": (33, 150, 243),
}

FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FONT_PATH_FALLBACK = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"


def _get_font_path() -> str:
    if os.path.exists(FONT_PATH):
        return FONT_PATH
    return FONT_PATH_FALLBACK


def _verdict_color(verdict: str) -> tuple:
    if "대성" in verdict:
        return C_GREAT
    if "성" in verdict:
        return C_SUCCESS
    if "반반" in verdict:
        return C_WARNING
    if "대패" in verdict:
        return C_DANGER
    if "패" in verdict:
        return C_DANGER
    return C_TEXT


def _verdict_icon(verdict: str) -> str:
    if "대성" in verdict:
        return "[++]"
    if "성" in verdict:
        return "[+]"
    if "반반" in verdict:
        return "[~]"
    if "대패" in verdict:
        return "[--]"
    if "패" in verdict:
        return "[-]"
    return "[ ]"


def _nl(pdf: FPDF):
    """줄바꿈 헬퍼."""
    pdf.set_x(10)


class SajuPDF(FPDF):
    """사주 보고서 전용 PDF."""

    def __init__(self):
        super().__init__()
        font_path = _get_font_path()
        self.add_font("gothic", "", font_path)
        self.add_font("gothic", "B", font_path)
        self.set_auto_page_break(auto=True, margin=20)
        self.set_left_margin(10)
        self.set_right_margin(10)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("gothic", "", 8)
        self.set_text_color(*C_LIGHT)
        self.cell(0, 10, f"- {self.page_no()} -", align="C")

    # ── 유틸 ──
    def _cell_ln(self, w, h, text, **kwargs):
        """cell + 줄바꿈."""
        self.cell(w, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, **kwargs)

    def _title_bar(self, text: str, color: tuple = C_PRIMARY):
        self.set_fill_color(*color)
        self.set_text_color(*C_WHITE)
        self.set_font("gothic", "B", 16)
        self._cell_ln(0, 12, f"  {text}", fill=True)
        self.set_text_color(*C_TEXT)
        self.ln(3)

    def _section_header(self, num: int, title: str, verdict: str, score: float, max_score: float = 100):
        vc = _verdict_color(verdict)
        icon = _verdict_icon(verdict)

        self.set_font("gothic", "B", 13)
        self.set_text_color(*C_ACCENT)
        self._cell_ln(0, 9, f"{num}. {title}")

        self.set_font("gothic", "B", 10)
        self.set_fill_color(*vc)
        self.set_text_color(*C_WHITE)
        badge = f" {icon} {verdict} ({score:.0f}/{max_score:.0f}) "
        w = self.get_string_width(badge) + 6
        self.cell(w, 7, badge, fill=True)
        self.set_text_color(*C_TEXT)
        self.ln(9)

    def _score_bar(self, score: float, max_score: float = 100, width: float = 170):
        bar_h = 5
        ratio = min(score / max_score, 1.0) if max_score > 0 else 0
        x = self.get_x()
        y = self.get_y()

        self.set_fill_color(220, 220, 220)
        self.rect(x, y, width, bar_h, "F")

        if ratio > 0.65:
            c = C_SUCCESS
        elif ratio > 0.4:
            c = C_WARNING
        else:
            c = C_DANGER
        if ratio > 0:
            self.set_fill_color(*c)
            self.rect(x, y, width * ratio, bar_h, "F")

        self.set_draw_color(*C_DIVIDER)
        self.rect(x, y, width, bar_h, "D")
        self.ln(bar_h + 2)

    def _detail_lines(self, lines: list[str]):
        self.set_font("gothic", "", 9)
        self.set_text_color(*C_TEXT)
        for line in lines:
            if not line:
                self.ln(2)
                continue
            indent = 0
            if line.startswith("  "):
                indent = 5
                line = line.strip()
            self.set_x(10 + indent)
            self.multi_cell(190 - indent, 5, line)
        self.ln(2)

    def _summary_line(self, text: str):
        self.set_font("gothic", "B", 10)
        self.set_text_color(*C_ACCENT)
        self.multi_cell(0, 6, text)
        self.set_text_color(*C_TEXT)
        self.ln(1)

    def _divider(self):
        self.set_draw_color(*C_DIVIDER)
        y = self.get_y()
        self.line(10, y, 200, y)
        self.ln(4)

    def _table(self, headers: list[str], rows: list[list[str]],
               col_widths: list[float] | None = None, highlight_col: int = -1):
        if not col_widths:
            w = 190 / len(headers)
            col_widths = [w] * len(headers)

        needed = 8 + len(rows) * 7
        if self.get_y() + needed > 270:
            self.add_page()

        # 헤더
        self.set_font("gothic", "B", 8)
        self.set_fill_color(*C_TABLE_HEAD)
        self.set_text_color(*C_WHITE)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align="C", fill=True)
        self.ln()

        # 행
        self.set_font("gothic", "", 8)
        for r_idx, row in enumerate(rows):
            bg = C_TABLE_ROW1 if r_idx % 2 == 0 else C_TABLE_ROW2
            self.set_fill_color(*bg)

            for c_idx, cell_text in enumerate(row):
                self.set_text_color(*C_TEXT)
                if c_idx == highlight_col:
                    if "대성" in cell_text or "성" in cell_text:
                        self.set_text_color(*C_SUCCESS)
                    elif "패" in cell_text:
                        self.set_text_color(*C_DANGER)
                    elif "반반" in cell_text:
                        self.set_text_color(*C_WARNING)
                self.cell(col_widths[c_idx], 7, cell_text, border=1, align="C", fill=True)
            self.ln()

        self.set_text_color(*C_TEXT)
        self.ln(3)

    def _ohaeng_bar(self, elem: str, value: float, max_val: float):
        c = OHAENG_COLORS.get(elem, C_LIGHT)
        x = self.get_x()
        y = self.get_y()

        self.set_font("gothic", "", 9)
        self.cell(15, 6, elem)

        bar_x = x + 18
        bar_w = 110
        ratio = min(value / max_val, 1.0) if max_val > 0 else 0

        self.set_fill_color(230, 230, 230)
        self.rect(bar_x, y, bar_w, 5, "F")
        if ratio > 0:
            self.set_fill_color(*c)
            self.rect(bar_x, y, bar_w * ratio, 5, "F")
        self.set_draw_color(*C_DIVIDER)
        self.rect(bar_x, y, bar_w, 5, "D")

        self.set_xy(bar_x + bar_w + 3, y)
        self.cell(20, 6, f"{value:.1f}")
        self.ln(7)


# ────────────────────────────────────────
# 개인 보고서 PDF
# ────────────────────────────────────────
def export_saju_pdf(report: SajuReport, output_dir: str = "") -> str:
    if not output_dir:
        output_dir = os.path.expanduser("~/Desktop")
    os.makedirs(output_dir, exist_ok=True)

    bi = report.birth_info
    filename = f"사주보고서_{bi.get('year','')}{bi.get('month',0):02d}{bi.get('day',0):02d}_{bi.get('gender','')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    pdf = SajuPDF()

    # ── 표지 ──
    pdf.add_page()
    pdf.ln(35)

    # 상단 장식 바
    pdf.set_fill_color(*C_PRIMARY)
    pdf.rect(10, 10, 190, 4, "F")

    pdf.set_font("gothic", "B", 28)
    pdf.set_text_color(*C_PRIMARY)
    pdf._cell_ln(0, 15, "사주 성패 보고서", align="C")
    pdf.ln(5)

    pdf.set_font("gothic", "", 13)
    pdf.set_text_color(*C_ACCENT)
    birth_text = f"{bi.get('year')}년 {bi.get('month')}월 {bi.get('day')}일 {bi.get('hour')}시 {bi.get('minute',0)}분생 ({bi.get('gender','')})"
    pdf._cell_ln(0, 10, birth_text, align="C")
    pdf.ln(2)

    pdf.set_font("gothic", "B", 22)
    pdf.set_text_color(*C_PRIMARY)
    pdf._cell_ln(0, 12, report.four_pillars_summary, align="C")
    pdf.ln(12)

    # 종합점수
    if report.overall:
        ov = report.overall
        vc = _verdict_color(ov.verdict)
        pdf.set_font("gothic", "B", 52)
        pdf.set_text_color(*vc)
        pdf._cell_ln(0, 28, f"{ov.score:.0f}", align="C")
        pdf.set_font("gothic", "", 14)
        pdf.set_text_color(*C_ACCENT)
        pdf._cell_ln(0, 10, f"/ 100점   {ov.verdict}", align="C")
        pdf.ln(6)

        pdf.set_font("gothic", "", 11)
        pdf.set_text_color(*C_TEXT)
        pdf._cell_ln(0, 8, ov.summary, align="C")

    pdf.ln(15)
    pdf.set_font("gothic", "", 9)
    pdf.set_text_color(*C_LIGHT)
    pdf._cell_ln(0, 6, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    # ── 요약 테이블 ──
    pdf.add_page()
    pdf._title_bar("종합 성패표")

    headers = ["영역", "점수", "판정", "요약"]
    rows = []
    for sec in report.sections:
        rows.append([sec.title, f"{sec.score:.0f}", sec.verdict, sec.summary[:28]])
    pdf._table(headers, rows, [22, 18, 22, 128], highlight_col=2)

    if report.overall:
        pdf.ln(2)
        pdf.set_font("gothic", "B", 10)
        pdf._cell_ln(0, 7, f"종합점수 {report.overall.score:.0f}/100")
        pdf._score_bar(report.overall.score, 100)

    # ── 개별 섹션 ──
    for idx, sec in enumerate(report.sections, 1):
        if pdf.get_y() > 225:
            pdf.add_page()
        pdf._divider()
        pdf._section_header(idx, sec.title, sec.verdict, sec.score)
        pdf._score_bar(sec.score, 100)
        pdf._summary_line(sec.summary)
        pdf._detail_lines(sec.details)

    # ── 총평 상세 ──
    if report.overall:
        pdf.add_page()
        pdf._title_bar("총평", C_ACCENT)
        pdf._detail_lines(report.overall.details)

    # 하단 장식
    pdf.set_fill_color(*C_PRIMARY)
    pdf.rect(10, 283, 190, 3, "F")

    pdf.output(filepath)
    return filepath


# ────────────────────────────────────────
# 궁합 보고서 PDF
# ────────────────────────────────────────
def export_compat_pdf(report: CompatReport, output_dir: str = "") -> str:
    if not output_dir:
        output_dir = os.path.expanduser("~/Desktop")
    os.makedirs(output_dir, exist_ok=True)

    a = report.person_a
    b = report.person_b
    filename = f"궁합보고서_{a.get('year','')}_{b.get('year','')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    pdf = SajuPDF()

    # ── 표지 ──
    pdf.add_page()
    pdf.set_fill_color(*C_PRIMARY)
    pdf.rect(10, 10, 190, 4, "F")

    pdf.ln(30)
    pdf.set_font("gothic", "B", 28)
    pdf.set_text_color(*C_PRIMARY)
    pdf._cell_ln(0, 15, "궁합 성패 보고서", align="C")
    pdf.ln(10)

    # 두 사람 정보 — 좌우 배치
    pdf.set_font("gothic", "", 11)
    pdf.set_text_color(*C_ACCENT)
    label_a = f"{a.get('gender','남')}  |  {a.get('year')}.{a.get('month')}.{a.get('day')}  {a.get('hour')}시"
    label_b = f"{b.get('gender','여')}  |  {b.get('year')}.{b.get('month')}.{b.get('day')}  {b.get('hour')}시"
    pdf.cell(95, 8, label_a, align="C")
    pdf.cell(95, 8, label_b, align="C")
    pdf.ln()

    pdf.set_font("gothic", "B", 15)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(95, 10, report.pillars_a_summary, align="C")
    pdf.cell(95, 10, report.pillars_b_summary, align="C")
    pdf.ln(15)

    # 총점
    vc = _verdict_color(report.overall_verdict)
    pdf.set_font("gothic", "B", 52)
    pdf.set_text_color(*vc)
    pdf._cell_ln(0, 28, f"{report.total_score:.0f}", align="C")
    pdf.set_font("gothic", "", 14)
    pdf.set_text_color(*C_ACCENT)
    pdf._cell_ln(0, 10, f"/ 100점   {report.overall_verdict}", align="C")
    pdf.ln(3)
    pdf.set_font("gothic", "B", 13)
    pdf.set_text_color(*C_PRIMARY)
    pdf._cell_ln(0, 8, report.grade, align="C")
    pdf.set_font("gothic", "", 10)
    pdf.set_text_color(*C_TEXT)
    pdf._cell_ln(0, 7, report.overall_summary, align="C")

    pdf.ln(12)
    pdf.set_font("gothic", "", 9)
    pdf.set_text_color(*C_LIGHT)
    pdf._cell_ln(0, 6, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    # ── 성패 요약표 ──
    pdf.add_page()
    pdf._title_bar("궁합 성패표")

    headers = ["항목", "점수", "판정", "요약"]
    rows = []
    for sec in report.sections:
        rows.append([sec.title, f"{sec.score:.0f}/{sec.max_score:.0f}", sec.verdict, sec.summary[:32]])
    pdf._table(headers, rows, [28, 22, 22, 118], highlight_col=2)

    pdf.ln(2)
    pdf.set_font("gothic", "B", 10)
    pdf._cell_ln(0, 7, f"궁합 총점 {report.total_score:.0f}/100")
    pdf._score_bar(report.total_score, 100)

    # ── 개별 섹션 ──
    for idx, sec in enumerate(report.sections, 1):
        if pdf.get_y() > 225:
            pdf.add_page()
        pdf._divider()
        pdf._section_header(idx, sec.title, sec.verdict, sec.score, sec.max_score)
        pdf._score_bar(sec.score, sec.max_score)
        pdf._summary_line(sec.summary)
        pdf._detail_lines(sec.details)

    # ── 오행 비교 ──
    if report.ohaeng_table:
        if pdf.get_y() > 180:
            pdf.add_page()
        pdf._divider()
        pdf._title_bar("오행 비교", C_ACCENT)

        headers = ["오행", "남자", "여자", "우세"]
        rows = []
        for row in report.ohaeng_table:
            rows.append([row["오행"], str(row["남자"]), str(row["여자"]), row["우세"]])
        pdf._table(headers, rows, [25, 45, 45, 75])

        max_val = max(
            max((r["남자"] for r in report.ohaeng_table), default=1),
            max((r["여자"] for r in report.ohaeng_table), default=1),
        )

        pdf.ln(2)
        pdf.set_font("gothic", "B", 9)
        pdf._cell_ln(0, 6, "남자 오행 분포")
        for row in report.ohaeng_table:
            pdf._ohaeng_bar(row["오행"], row["남자"], max_val)
        pdf.ln(2)
        pdf.set_font("gothic", "B", 9)
        pdf._cell_ln(0, 6, "여자 오행 분포")
        for row in report.ohaeng_table:
            pdf._ohaeng_bar(row["오행"], row["여자"], max_val)

    # ── 조언 ──
    if report.advice:
        if pdf.get_y() > 225:
            pdf.add_page()
        pdf.ln(3)
        pdf._title_bar("현실 조언", (41, 128, 185))
        pdf.set_font("gothic", "", 9)
        for adv in report.advice:
            pdf.set_text_color(*C_TEXT)
            pdf.multi_cell(190, 6, f"  - {adv}")
            pdf.ln(1)

    # 하단 장식
    pdf.set_fill_color(*C_PRIMARY)
    pdf.rect(10, 283, 190, 3, "F")

    pdf.output(filepath)
    return filepath
