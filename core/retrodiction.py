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
