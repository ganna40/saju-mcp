"""보고서 마크다운 파일 내보내기."""
from __future__ import annotations

import os
from datetime import datetime

from .models import SajuReport, CompatReport


def _verdict_icon(verdict: str) -> str:
    if "대성" in verdict or "성" in verdict:
        return "O"
    if "반반" in verdict:
        return "△"
    return "X"


def export_saju_report(report: SajuReport, output_dir: str = "") -> str:
    """개인 사주 보고서 → 마크다운 파일."""
    if not output_dir:
        output_dir = os.path.expanduser("~/Desktop")
    os.makedirs(output_dir, exist_ok=True)

    bi = report.birth_info
    name_part = f"{bi.get('year','')}{bi.get('month',''):02d}{bi.get('day',''):02d}"
    gender = bi.get('gender', '')
    filename = f"사주보고서_{name_part}_{gender}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(output_dir, filename)

    lines = []
    lines.append(f"# 사주 성패 보고서")
    lines.append("")
    lines.append(f"> 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # 기본정보
    lines.append("## 기본 정보")
    lines.append("")
    lines.append("| 항목 | 내용 |")
    lines.append("|---|---|")
    lines.append(f"| 생년월일시 | {bi.get('year')}년 {bi.get('month')}월 {bi.get('day')}일 {bi.get('hour')}시 {bi.get('minute',0)}분 |")
    lines.append(f"| 성별 | {gender} |")
    lines.append(f"| 사주 | **{report.four_pillars_summary}** |")
    lines.append("")

    # 총평
    if report.overall:
        ov = report.overall
        lines.append("---")
        lines.append("")
        lines.append(f"## 종합점수: {ov.score:.1f} / 100 — {ov.verdict}")
        lines.append("")

        # 요약 테이블
        lines.append("| 영역 | 점수 | 판정 | 한마디 |")
        lines.append("|---|---|---|---|")
        for sec in report.sections:
            icon = _verdict_icon(sec.verdict)
            lines.append(f"| {sec.title} | {sec.score:.0f} | **{sec.verdict}** | {sec.summary[:40]} |")
        lines.append("")

        # 총평 상세
        lines.append("### 총평 상세")
        lines.append("")
        for line in ov.details:
            if line:
                lines.append(f"- {line}")
            else:
                lines.append("")
        lines.append("")

    # 개별 섹션
    for idx, sec in enumerate(report.sections, 1):
        icon = _verdict_icon(sec.verdict)
        lines.append("---")
        lines.append("")
        lines.append(f"## {idx}. {sec.title} — {sec.verdict} ({sec.score:.0f}점)")
        lines.append("")
        lines.append(f"**{sec.summary}**")
        lines.append("")
        for line in sec.details:
            if line:
                lines.append(f"- {line}")
            else:
                lines.append("")
        lines.append("")

    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def export_compat_report(report: CompatReport, output_dir: str = "") -> str:
    """궁합 보고서 → 마크다운 파일."""
    if not output_dir:
        output_dir = os.path.expanduser("~/Desktop")
    os.makedirs(output_dir, exist_ok=True)

    a = report.person_a
    b = report.person_b
    name_a = f"{a.get('year','')}"
    name_b = f"{b.get('year','')}"
    filename = f"궁합보고서_{name_a}_{name_b}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(output_dir, filename)

    lines = []
    lines.append("# 궁합 성패 보고서")
    lines.append("")
    lines.append(f"> 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # 기본정보
    lines.append("## 두 사람의 사주")
    lines.append("")
    lines.append("| | 남자 | 여자 |")
    lines.append("|---|---|---|")
    lines.append(f"| 생년월일 | {a.get('year')}.{a.get('month')}.{a.get('day')} {a.get('hour')}시 | {b.get('year')}.{b.get('month')}.{b.get('day')} {b.get('hour')}시 |")
    lines.append(f"| 사주 | **{report.pillars_a_summary}** | **{report.pillars_b_summary}** |")
    lines.append("")

    # 종합
    lines.append("---")
    lines.append("")
    lines.append(f"## 궁합 총점: {report.total_score:.1f} / 100 — {report.overall_verdict}")
    lines.append("")
    lines.append(f"**{report.grade}** — {report.overall_summary}")
    lines.append("")

    # 요약 테이블
    lines.append("| 항목 | 점수 | 판정 | 한마디 |")
    lines.append("|---|---|---|---|")
    for sec in report.sections:
        lines.append(f"| {sec.title} | {sec.score:.1f} / {sec.max_score:.0f} | **{sec.verdict}** | {sec.summary[:50]} |")
    lines.append("")

    # 개별 섹션
    for idx, sec in enumerate(report.sections, 1):
        lines.append("---")
        lines.append("")
        lines.append(f"## {idx}. {sec.title} — {sec.verdict} ({sec.score:.1f}/{sec.max_score:.0f})")
        lines.append("")
        lines.append(f"**{sec.summary}**")
        lines.append("")
        for line in sec.details:
            if line:
                lines.append(f"- {line}")
            else:
                lines.append("")
        lines.append("")

    # 오행 비교표
    if report.ohaeng_table:
        lines.append("---")
        lines.append("")
        lines.append("## 오행 비교표")
        lines.append("")
        lines.append("| 오행 | 남자 | 여자 | 우세 |")
        lines.append("|---|---|---|---|")
        for row in report.ohaeng_table:
            lines.append(f"| {row['오행']} | {row['남자']} | {row['여자']} | {row['우세']} |")
        lines.append("")

    # 조언
    if report.advice:
        lines.append("---")
        lines.append("")
        lines.append("## 현실 조언")
        lines.append("")
        for adv in report.advice:
            lines.append(f"- {adv}")
        lines.append("")

    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
