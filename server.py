"""사주팔자 MCP 서버 — FastMCP 기반 5개 도구."""
import sys
import os

# core 패키지를 찾을 수 있도록 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP

from core.constants import (
    DAY_STEM_TRAITS, STEM_OHAENG,
    ELEM_ORGAN, ELEM_FOOD, ELEM_COLOR, ELEM_DIRECTION, ELEM_SEASON,
    SINSAL_DESCRIPTIONS,
)
from core.models import (
    BirthInfo, SajuAnalysisResult, WealthResult,
    CompatibilityResult, YearlyResult, SinsalResult,
)
from core.manseryeok import get_four_pillars, get_daeun, get_seun
from core.ten_gods import get_all_ten_gods, calc_ten_god, calc_ten_god_for_branch
from core.strength import calc_strength
from core.pattern_engine import determine_pattern
from core.yongshin import determine_yongshin
from core.sinsal import detect_sinsal
from core.interactions import detect_interactions, detect_interactions_with_branch
from core.wealth import calc_wealth
from core.life_events import calc_life_events
from core.radar import calc_radar
from core.compatibility import calc_compatibility
from core.report import generate_report
from core.compatibility_report import generate_compat_report
from core.export import export_saju_report, export_compat_report
from core.export_pdf import export_saju_pdf, export_compat_pdf
from core.yearly_events import predict_yearly_events

server = FastMCP(
    name="saju-mcp",
    instructions=(
        "사주팔자(四柱八字) 분석 서버입니다. "
        "양력 생년월일시를 입력하면 구조화된 사주 분석 데이터를 반환합니다. "
        "LLM이 반환된 데이터를 해석하여 사용자에게 자연어로 설명해 주세요."
    ),
)


@server.tool()
def saju_analyze(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "남",
) -> dict:
    """사주팔자 전체 분석.

    양력 생년월일시를 입력하면 사주 전체 분석 결과를 반환합니다.
    포함: 4주(사주), 십신, 격국, 신강/신약, 용신, 신살, 합충형파해,
    재물그릇, 인생이벤트 타임라인, 6축 운세 레이더, 대운.

    Args:
        year: 생년 (양력, 1900~2100)
        month: 생월 (1~12)
        day: 생일 (1~31)
        hour: 생시 (0~23, 기본값 12)
        minute: 생분 (0~59, 기본값 0)
        gender: 성별 ("남" 또는 "여", 기본값 "남")
    """
    pillars = get_four_pillars(year, month, day, hour, minute)
    ten_gods = get_all_ten_gods(pillars)
    daeun = get_daeun(year, month, day, hour, minute, gender)

    # 대운 십신 추가
    day_stem = pillars.day.stem
    for d in daeun:
        d.ten_god_stem = calc_ten_god(day_stem, d.stem)
        d.ten_god_branch = calc_ten_god_for_branch(day_stem, d.branch)

    strength = calc_strength(pillars)
    pattern = determine_pattern(pillars, strength)
    yongshin = determine_yongshin(strength, pattern)
    sinsal = detect_sinsal(pillars, daeun)
    interactions = detect_interactions(pillars)
    wealth = calc_wealth(pillars, strength, pattern, interactions, daeun)
    life_events = calc_life_events(pillars, daeun, strength, yongshin)
    radar = calc_radar(pillars, strength, yongshin)

    # 용신 오행 관련 정보
    yong_elem = yongshin.yongshin
    elem_info = {}
    if yong_elem:
        elem_info = {
            "용신오행": yong_elem,
            "건강": ELEM_ORGAN.get(yong_elem, {}),
            "음식": ELEM_FOOD.get(yong_elem, ""),
            "색상": ELEM_COLOR.get(yong_elem, ""),
            "방향": ELEM_DIRECTION.get(yong_elem, ""),
            "계절": ELEM_SEASON.get(yong_elem, ""),
        }

    result = SajuAnalysisResult(
        birth_info={"year": year, "month": month, "day": day,
                     "hour": hour, "minute": minute, "gender": gender},
        four_pillars=pillars,
        ten_gods=ten_gods,
        strength=strength,
        pattern=pattern,
        yongshin=yongshin,
        sinsal=sinsal,
        interactions=interactions,
        wealth=wealth,
        life_events=life_events,
        radar=radar,
        daeun=daeun,
        day_stem_traits=DAY_STEM_TRAITS.get(day_stem, ""),
        elem_info=elem_info,
    )
    return result.model_dump()


@server.tool()
def saju_wealth(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "남",
) -> dict:
    """재물그릇 집중 분석.

    9항목(재성투출, 재성통근, 재고, 식상생재, 신강보정, 종격, 합충보정,
    관성제어, 대운재성기)을 채점하여 재물운 등급과 전성기/위험기를 반환합니다.

    Args:
        year: 생년 (양력)
        month: 생월
        day: 생일
        hour: 생시 (기본 12)
        minute: 생분 (기본 0)
        gender: 성별 (기본 "남")
    """
    pillars = get_four_pillars(year, month, day, hour, minute)
    daeun = get_daeun(year, month, day, hour, minute, gender)
    strength = calc_strength(pillars)
    pattern = determine_pattern(pillars, strength)
    interactions = detect_interactions(pillars)
    wealth = calc_wealth(pillars, strength, pattern, interactions, daeun)

    return {
        "birth_info": {"year": year, "month": month, "day": day,
                       "hour": hour, "minute": minute, "gender": gender},
        "four_pillars": pillars.model_dump(),
        "strength": {"score": strength.score, "label": strength.label},
        "pattern": {"name": pattern.name, "is_special": pattern.is_special},
        "wealth": wealth.model_dump(),
    }


@server.tool()
def saju_compatibility(
    year_a: int, month_a: int, day_a: int, hour_a: int,
    year_b: int, month_b: int, day_b: int, hour_b: int,
    minute_a: int = 0,
    minute_b: int = 0,
) -> dict:
    """궁합 분석.

    두 사람의 양력 생년월일시를 입력하면 궁합 분석 결과를 반환합니다.
    포함: 일간 관계, 오행 보완, 합충 관계, 상호 십신.

    Args:
        year_a: A의 생년
        month_a: A의 생월
        day_a: A의 생일
        hour_a: A의 생시
        year_b: B의 생년
        month_b: B의 생월
        day_b: B의 생일
        hour_b: B의 생시
        minute_a: A의 생분 (기본 0)
        minute_b: B의 생분 (기본 0)
    """
    pillars_a = get_four_pillars(year_a, month_a, day_a, hour_a, minute_a)
    pillars_b = get_four_pillars(year_b, month_b, day_b, hour_b, minute_b)
    result = calc_compatibility(pillars_a, pillars_b)
    return {
        "person_a": {"year": year_a, "month": month_a, "day": day_a, "hour": hour_a,
                      "four_pillars": pillars_a.model_dump()},
        "person_b": {"year": year_b, "month": month_b, "day": day_b, "hour": hour_b,
                      "four_pillars": pillars_b.model_dump()},
        "compatibility": result.model_dump(),
    }


@server.tool()
def saju_yearly(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "남",
    target_year: int = 2026,
) -> dict:
    """세운(연운) 분석.

    특정 연도의 운세를 분석합니다.
    포함: 해당 연도 세운 간지, 신살 발동, 합충 관계, 6축 레이더.

    Args:
        year: 생년 (양력)
        month: 생월
        day: 생일
        hour: 생시 (기본 12)
        minute: 생분 (기본 0)
        gender: 성별 (기본 "남")
        target_year: 분석 대상 연도 (기본 2026)
    """
    pillars = get_four_pillars(year, month, day, hour, minute)
    daeun = get_daeun(year, month, day, hour, minute, gender)
    strength = calc_strength(pillars)
    pattern = determine_pattern(pillars, strength)
    yongshin = determine_yongshin(strength, pattern)

    # 세운 가져오기
    seun_list = get_seun(year, month, day, hour, minute, gender, target_year)
    seun = seun_list[0] if seun_list else None

    if seun:
        day_stem = pillars.day.stem
        seun.ten_god_stem = calc_ten_god(day_stem, seun.stem)
        seun.ten_god_branch = calc_ten_god_for_branch(day_stem, seun.branch)

    # 세운과의 합충
    seun_interactions = []
    if seun:
        seun_interactions = detect_interactions_with_branch(pillars, seun.branch, f"세운({target_year})")

    # 신살 발동
    sinsal = detect_sinsal(pillars, daeun)
    activated = []
    if seun:
        from core.constants import (
            YEOKMA, DOHWA, HWAGAE, GWIMUN, BAEKHO,
            JANGSEONG, GEOPSAL,
        )
        lookup_map = {
            "역마살": YEOKMA, "도화살": DOHWA, "화개살": HWAGAE,
            "귀문관살": GWIMUN, "백호대살": BAEKHO,
            "장성살": JANGSEONG, "겁살": GEOPSAL,
        }
        for s in sinsal:
            lookup = lookup_map.get(s.name)
            if lookup:
                target = lookup.get(pillars.day.branch)
                if target and target == seun.branch:
                    activated.append(s)

    radar = calc_radar(pillars, strength, yongshin, seun)

    # 현재 대운 찾기
    current_daeun = None
    target_age = target_year - year + 1
    for d in daeun:
        if d.age_start <= target_age <= d.age_end:
            current_daeun = d
            break
    if current_daeun:
        day_stem = pillars.day.stem
        current_daeun.ten_god_stem = calc_ten_god(day_stem, current_daeun.stem)
        current_daeun.ten_god_branch = calc_ten_god_for_branch(day_stem, current_daeun.branch)

    # 구체적 사건 예측
    yearly_events = []
    person_encounters = []
    overall_fortune = ""
    if seun:
        yearly_events, person_encounters, overall_fortune = predict_yearly_events(
            pillars=pillars,
            seun=seun,
            daeun=current_daeun,
            strength=strength,
            yongshin=yongshin,
            pattern=pattern,
            activated_sinsal=activated,
            seun_interactions=seun_interactions,
            gender=gender,
        )

    # 요약
    summary_parts = []
    if seun:
        summary_parts.append(f"{target_year}년 세운: {seun.stem}{seun.branch} ({seun.stem_ohaeng}/{seun.branch_ohaeng})")
        summary_parts.append(f"세운 십신: {seun.ten_god_stem}/{seun.ten_god_branch}")
    if activated:
        summary_parts.append(f"발동 신살: {', '.join(s.name for s in activated)}")
    if seun_interactions:
        summary_parts.append(f"합충: {', '.join(i.description for i in seun_interactions)}")

    result = YearlyResult(
        birth_info={"year": year, "month": month, "day": day,
                     "hour": hour, "minute": minute, "gender": gender},
        target_year=target_year,
        seun=seun,
        sinsal_activations=activated,
        interactions_with_seun=seun_interactions,
        radar=radar,
        summary=" | ".join(summary_parts),
        yearly_events=yearly_events,
        person_encounters=person_encounters,
        current_daeun=current_daeun,
        overall_fortune=overall_fortune,
    )
    return result.model_dump()


@server.tool()
def saju_sinsal(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "남",
) -> dict:
    """신살 12종 집중 분석.

    원국의 신살 12종을 판별하고, 대운에서의 발동 시기를 분석합니다.

    Args:
        year: 생년 (양력)
        month: 생월
        day: 생일
        hour: 생시 (기본 12)
        minute: 생분 (기본 0)
        gender: 성별 (기본 "남")
    """
    pillars = get_four_pillars(year, month, day, hour, minute)
    daeun = get_daeun(year, month, day, hour, minute, gender)
    sinsal = detect_sinsal(pillars, daeun)

    # 대운별 발동 요약
    daeun_activations = []
    for d in daeun:
        activated_names = []
        for s in sinsal:
            for period in s.activation_periods:
                if f"{d.age_start}~{d.age_end}" in period:
                    activated_names.append(s.name)
                    break
        if activated_names:
            daeun_activations.append({
                "period": f"{d.age_start}~{d.age_end}세 ({d.stem}{d.branch})",
                "activated_sinsal": activated_names,
            })

    result = SinsalResult(
        birth_info={"year": year, "month": month, "day": day,
                     "hour": hour, "minute": minute, "gender": gender},
        four_pillars=pillars,
        sinsal=sinsal,
        total_count=len(sinsal),
        daeun_activations=daeun_activations,
    )
    return result.model_dump()


@server.tool()
def saju_report(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = "남",
) -> dict:
    """사주 성패 보고서.

    성격, 재물운, 직장운, 연애운, 결혼운, 자녀운, 적성, 총평을
    '된다/안된다' 성패 관점으로 판정한 종합 보고서를 반환합니다.
    각 항목마다 점수(0~100)와 판정(대성/성/반반/패/대패)을 포함합니다.

    Args:
        year: 생년 (양력, 1900~2100)
        month: 생월 (1~12)
        day: 생일 (1~31)
        hour: 생시 (0~23, 기본값 12)
        minute: 생분 (0~59, 기본값 0)
        gender: 성별 ("남" 또는 "여", 기본값 "남")
    """
    pillars = get_four_pillars(year, month, day, hour, minute)
    ten_gods = get_all_ten_gods(pillars)
    daeun = get_daeun(year, month, day, hour, minute, gender)

    day_stem = pillars.day.stem
    for d in daeun:
        d.ten_god_stem = calc_ten_god(day_stem, d.stem)
        d.ten_god_branch = calc_ten_god_for_branch(day_stem, d.branch)

    strength = calc_strength(pillars)
    pattern = determine_pattern(pillars, strength)
    yongshin = determine_yongshin(strength, pattern)
    sinsal = detect_sinsal(pillars, daeun)
    interactions = detect_interactions(pillars)
    wealth = calc_wealth(pillars, strength, pattern, interactions, daeun)
    life_events = calc_life_events(pillars, daeun, strength, yongshin)
    radar = calc_radar(pillars, strength, yongshin)

    birth_info = {"year": year, "month": month, "day": day,
                  "hour": hour, "minute": minute, "gender": gender}

    report = generate_report(
        pillars=pillars,
        ten_gods=ten_gods,
        strength=strength,
        pattern=pattern,
        yongshin=yongshin,
        sinsal=sinsal,
        interactions=interactions,
        wealth=wealth,
        radar=radar,
        daeun=daeun,
        life_events=life_events,
        gender=gender,
        birth_info=birth_info,
    )
    return report.model_dump()


@server.tool()
def saju_compat_report(
    year_a: int, month_a: int, day_a: int, hour_a: int,
    year_b: int, month_b: int, day_b: int, hour_b: int,
    minute_a: int = 0,
    minute_b: int = 0,
    gender_a: str = "남",
    gender_b: str = "여",
) -> dict:
    """궁합 성패 보고서.

    두 사람의 궁합을 일간관계, 상호십신, 합충관계, 오행보완 4개 항목으로
    '된다/안된다' 성패 관점에서 판정한 보고서를 반환합니다.

    Args:
        year_a: A의 생년
        month_a: A의 생월
        day_a: A의 생일
        hour_a: A의 생시
        year_b: B의 생년
        month_b: B의 생월
        day_b: B의 생일
        hour_b: B의 생시
        minute_a: A의 생분 (기본 0)
        minute_b: B의 생분 (기본 0)
        gender_a: A의 성별 (기본 "남")
        gender_b: B의 성별 (기본 "여")
    """
    pillars_a = get_four_pillars(year_a, month_a, day_a, hour_a, minute_a)
    pillars_b = get_four_pillars(year_b, month_b, day_b, hour_b, minute_b)

    info_a = {"year": year_a, "month": month_a, "day": day_a,
              "hour": hour_a, "minute": minute_a, "gender": gender_a}
    info_b = {"year": year_b, "month": month_b, "day": day_b,
              "hour": hour_b, "minute": minute_b, "gender": gender_b}

    report = generate_compat_report(pillars_a, pillars_b, gender_a, gender_b, info_a, info_b)
    return report.model_dump()


@server.tool()
def saju_export(
    report_type: str,
    year: int = 0,
    month: int = 0,
    day: int = 0,
    hour: int = 12,
    minute: int = 0,
    gender: str = "남",
    year_b: int = 0,
    month_b: int = 0,
    day_b: int = 0,
    hour_b: int = 12,
    minute_b: int = 0,
    gender_b: str = "여",
    output_dir: str = "",
    file_format: str = "pdf",
) -> dict:
    """사주/궁합 보고서를 PDF 또는 마크다운 파일로 내보내기.

    report_type이 "individual"이면 개인 사주 보고서,
    "compatibility"이면 궁합 보고서를 파일로 저장합니다.
    file_format이 "pdf"이면 색상/표가 포함된 PDF, "md"이면 마크다운.
    파일은 기본적으로 바탕화면(~/Desktop)에 저장됩니다.

    Args:
        report_type: "individual" (개인) 또는 "compatibility" (궁합)
        year: 생년 (개인 또는 A)
        month: 생월
        day: 생일
        hour: 생시 (기본 12)
        minute: 생분 (기본 0)
        gender: 성별 (기본 "남")
        year_b: B의 생년 (궁합 시)
        month_b: B의 생월
        day_b: B의 생일
        hour_b: B의 생시 (기본 12)
        minute_b: B의 생분 (기본 0)
        gender_b: B의 성별 (기본 "여")
        output_dir: 저장 경로 (기본: ~/Desktop)
        file_format: "pdf" (기본) 또는 "md" (마크다운)
    """
    use_pdf = file_format.lower() == "pdf"

    if report_type == "compatibility":
        pillars_a = get_four_pillars(year, month, day, hour, minute)
        pillars_b = get_four_pillars(year_b, month_b, day_b, hour_b, minute_b)
        info_a = {"year": year, "month": month, "day": day,
                  "hour": hour, "minute": minute, "gender": gender}
        info_b = {"year": year_b, "month": month_b, "day": day_b,
                  "hour": hour_b, "minute": minute_b, "gender": gender_b}
        report = generate_compat_report(pillars_a, pillars_b, gender, gender_b, info_a, info_b)
        if use_pdf:
            filepath = export_compat_pdf(report, output_dir)
        else:
            filepath = export_compat_report(report, output_dir)
        return {"filepath": filepath, "type": "compatibility", "format": file_format,
                "message": f"궁합 보고서가 저장되었습니다: {filepath}"}

    else:  # individual
        pillars = get_four_pillars(year, month, day, hour, minute)
        ten_gods = get_all_ten_gods(pillars)
        daeun = get_daeun(year, month, day, hour, minute, gender)
        day_stem = pillars.day.stem
        for d in daeun:
            d.ten_god_stem = calc_ten_god(day_stem, d.stem)
            d.ten_god_branch = calc_ten_god_for_branch(day_stem, d.branch)
        strength = calc_strength(pillars)
        pattern = determine_pattern(pillars, strength)
        yongshin = determine_yongshin(strength, pattern)
        sinsal = detect_sinsal(pillars, daeun)
        interactions = detect_interactions(pillars)
        wealth = calc_wealth(pillars, strength, pattern, interactions, daeun)
        life_events = calc_life_events(pillars, daeun, strength, yongshin)
        radar = calc_radar(pillars, strength, yongshin)
        birth_info = {"year": year, "month": month, "day": day,
                      "hour": hour, "minute": minute, "gender": gender}
        report = generate_report(
            pillars=pillars, ten_gods=ten_gods, strength=strength,
            pattern=pattern, yongshin=yongshin, sinsal=sinsal,
            interactions=interactions, wealth=wealth, radar=radar,
            daeun=daeun, life_events=life_events, gender=gender,
            birth_info=birth_info,
        )
        if use_pdf:
            filepath = export_saju_pdf(report, output_dir)
        else:
            filepath = export_saju_report(report, output_dir)
        return {"filepath": filepath, "type": "individual", "format": file_format,
                "message": f"사주 보고서가 저장되었습니다: {filepath}"}


if __name__ == "__main__":
    server.run(transport="stdio")
