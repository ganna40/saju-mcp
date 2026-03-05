"""공망(空亡) 판별 — 일주 기준 비어있는 지지 2개."""
from __future__ import annotations

from .constants import HEAVENLY_STEMS, EARTHLY_BRANCHES, PALACE_INFO
from .models import FourPillars


def calc_gongmang(pillars: FourPillars) -> dict:
    """일주(일간+일지) 기준 공망 계산.

    60갑자에서 일주가 속한 순(旬)을 찾아, 10천간에 짝지어지지 못한
    지지 2개가 공망.

    Returns:
        {
            "gongmang_branches": ["술", "해"],
            "affected_palaces": [{"palace": "년주", "branch": "해", "meaning": "..."}],
            "interpretation": "...",
        }
    """
    stem_idx = HEAVENLY_STEMS.index(pillars.day.stem)
    branch_idx = EARTHLY_BRANCHES.index(pillars.day.branch)

    # 순(旬)의 시작 지지 인덱스: 일주에서 천간만큼 거슬러 올라감
    start_branch_idx = (branch_idx - stem_idx) % 12

    # 공망 = 순에 포함되지 않는 나머지 2개 지지
    gm1 = EARTHLY_BRANCHES[(start_branch_idx + 10) % 12]
    gm2 = EARTHLY_BRANCHES[(start_branch_idx + 11) % 12]

    gongmang_branches = [gm1, gm2]

    # 어떤 궁위가 공망에 해당하는지
    affected = []
    palace_map = [
        ("년주", pillars.year.branch),
        ("월주", pillars.month.branch),
        ("일주", pillars.day.branch),
        ("시주", pillars.hour.branch),
    ]
    for palace_name, branch in palace_map:
        if branch in gongmang_branches:
            info = PALACE_INFO.get(palace_name, {})
            affected.append({
                "palace": palace_name,
                "palace_name": info.get("name", ""),
                "branch": branch,
                "meaning": _gongmang_palace_meaning(palace_name),
            })

    interpretation = _build_interpretation(gongmang_branches, affected)

    return {
        "gongmang_branches": gongmang_branches,
        "affected_palaces": affected,
        "interpretation": interpretation,
    }


def _gongmang_palace_meaning(palace: str) -> str:
    """궁위별 공망의 의미."""
    meanings = {
        "년주": "조상궁 공망 — 조상 덕이 약하거나 어린 시절 불안정했을 수 있음. 고향/가문과의 인연이 옅음",
        "월주": "부모궁/사회궁 공망 — 부모의 도움이 약하거나 사회생활에서 빈 곳이 있음. 자수성가의 기운",
        "일주": "배우자궁 공망 — 배우자와의 인연에 파란이 있을 수 있음. 결혼이 늦거나 배우자 변동 가능성",
        "시주": "자녀궁/말년궁 공망 — 자녀와의 인연이 옅거나 말년에 외로울 수 있음. 정신적 세계에 몰두할 가능성",
    }
    return meanings.get(palace, "")


def _build_interpretation(branches: list[str], affected: list[dict]) -> str:
    """종합 해석 생성."""
    if not affected:
        return (
            f"공망 지지({branches[0]}, {branches[1]})가 원국 4주에 없어 "
            "공망의 직접적 영향이 약합니다. "
            "다만 대운·세운에서 해당 지지가 올 때 '허(虛)한 기운'이 작용할 수 있습니다."
        )

    parts = [f"공망: {branches[0]}·{branches[1]}."]
    for a in affected:
        parts.append(f"{a['palace']}({a['branch']})가 공망에 해당. {a['meaning']}")

    parts.append(
        "공망은 '비어있음'을 뜻하지만, 오히려 물질적 욕심을 내려놓고 "
        "정신적·학문적·예술적 영역에서 빛을 발할 수 있는 기운이기도 합니다."
    )
    return " ".join(parts)
