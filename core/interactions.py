"""합충형파해(合沖刑破害) 7종 판별."""
from __future__ import annotations

from .constants import (
    CHEONGAN_HAP, YUKAP, SAMHAP, BANSAMHAP, SAMHOE,
    CHEONGAN_CHUNG, YUKCHUNG, HYUNG, PA, HAE,
)
from .models import FourPillars, InteractionEntry


def _stem_pairs(pillars: FourPillars) -> list[tuple[str, str, str, str]]:
    """천간 쌍: (글자A, 글자B, 위치A, 위치B)."""
    stems = [
        (pillars.year.stem, "년간"),
        (pillars.month.stem, "월간"),
        (pillars.day.stem, "일간"),
        (pillars.hour.stem, "시간"),
    ]
    pairs = []
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            pairs.append((stems[i][0], stems[j][0], stems[i][1], stems[j][1]))
    return pairs


def _branch_pairs(pillars: FourPillars) -> list[tuple[str, str, str, str]]:
    """지지 쌍: (글자A, 글자B, 위치A, 위치B)."""
    branches = [
        (pillars.year.branch, "년지"),
        (pillars.month.branch, "월지"),
        (pillars.day.branch, "일지"),
        (pillars.hour.branch, "시지"),
    ]
    pairs = []
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pairs.append((branches[i][0], branches[j][0], branches[i][1], branches[j][1]))
    return pairs


def _branch_list(pillars: FourPillars) -> list[tuple[str, str]]:
    """(지지, 위치) 리스트."""
    return [
        (pillars.year.branch, "년지"),
        (pillars.month.branch, "월지"),
        (pillars.day.branch, "일지"),
        (pillars.hour.branch, "시지"),
    ]


def detect_interactions(pillars: FourPillars) -> list[InteractionEntry]:
    """원국의 합충형파해 전체 판별."""
    results: list[InteractionEntry] = []

    # ── 1. 천간합 ──
    for a, b, pos_a, pos_b in _stem_pairs(pillars):
        key = frozenset({a, b})
        if key in CHEONGAN_HAP:
            results.append(InteractionEntry(
                type="합", subtype="천간합",
                positions=[pos_a, pos_b],
                elements=[a, b],
                result=f"→ {CHEONGAN_HAP[key]}",
                description=f"{a}+{b} 천간합 → {CHEONGAN_HAP[key]}으로 변화",
            ))

    # ── 2. 천간충 ──
    for a, b, pos_a, pos_b in _stem_pairs(pillars):
        key = frozenset({a, b})
        if key in CHEONGAN_CHUNG:
            results.append(InteractionEntry(
                type="충", subtype="천간충",
                positions=[pos_a, pos_b],
                elements=[a, b],
                description=f"{a}↔{b} 천간충",
            ))

    # ── 3. 육합 ──
    for a, b, pos_a, pos_b in _branch_pairs(pillars):
        key = frozenset({a, b})
        if key in YUKAP:
            results.append(InteractionEntry(
                type="합", subtype="육합",
                positions=[pos_a, pos_b],
                elements=[a, b],
                result=f"→ {YUKAP[key]}",
                description=f"{a}+{b} 육합 → {YUKAP[key]}",
            ))

    # ── 4. 삼합 ──
    bl = _branch_list(pillars)
    branch_set = {b for b, _ in bl}
    branch_pos = {b: p for b, p in bl}
    for trio, elem in SAMHAP:
        if trio.issubset(branch_set):
            positions = [branch_pos[b] for b in trio if b in branch_pos]
            results.append(InteractionEntry(
                type="합", subtype="삼합",
                positions=positions,
                elements=list(trio),
                result=f"→ {elem}",
                description=f"{'·'.join(trio)} 삼합 → {elem}",
            ))

    # ── 5. 반삼합 ──
    for pair, elem in BANSAMHAP:
        if pair.issubset(branch_set):
            # 이미 삼합이 있으면 반삼합은 생략
            already_samhap = False
            for trio, _ in SAMHAP:
                if pair.issubset(trio) and trio.issubset(branch_set):
                    already_samhap = True
                    break
            if not already_samhap:
                positions = [branch_pos[b] for b in pair if b in branch_pos]
                results.append(InteractionEntry(
                    type="합", subtype="반삼합",
                    positions=positions,
                    elements=list(pair),
                    result=f"→ {elem}",
                    description=f"{'·'.join(pair)} 반삼합 → {elem}",
                ))

    # ── 6. 삼회 ──
    for trio, elem in SAMHOE:
        if trio.issubset(branch_set):
            positions = [branch_pos[b] for b in trio if b in branch_pos]
            results.append(InteractionEntry(
                type="합", subtype="삼회",
                positions=positions,
                elements=list(trio),
                result=f"→ {elem}",
                description=f"{'·'.join(trio)} 삼회(방합) → {elem}",
            ))

    # ── 7. 육충 ──
    for a, b, pos_a, pos_b in _branch_pairs(pillars):
        key = frozenset({a, b})
        if key in YUKCHUNG:
            results.append(InteractionEntry(
                type="충", subtype="육충",
                positions=[pos_a, pos_b],
                elements=[a, b],
                description=f"{a}↔{b} 육충",
            ))

    # ── 8. 형 ──
    for condition, name in HYUNG:
        if len(condition) == 2:
            cond_set = set(condition)
            if cond_set.issubset(branch_set):
                positions = [branch_pos[b] for b in cond_set if b in branch_pos]
                results.append(InteractionEntry(
                    type="형", subtype=name,
                    positions=positions,
                    elements=list(cond_set),
                    description=f"{'·'.join(cond_set)} {name}",
                ))
        elif len(condition) == 3:
            cond_set = set(condition)
            if cond_set.issubset(branch_set):
                positions = [branch_pos[b] for b in cond_set if b in branch_pos]
                results.append(InteractionEntry(
                    type="형", subtype=name,
                    positions=positions,
                    elements=list(cond_set),
                    description=f"{'·'.join(cond_set)} {name}",
                ))
        else:
            # 자형 (같은 글자 2개 이상)
            cond_list = list(condition)
            if len(cond_list) == 1:
                target = cond_list[0]
                count = sum(1 for b, _ in bl if b == target)
                if count >= 2:
                    results.append(InteractionEntry(
                        type="형", subtype=name,
                        positions=[p for b, p in bl if b == target],
                        elements=[target],
                        description=f"{target}+{target} {name}",
                    ))

    # ── 9. 파 ──
    for a, b, pos_a, pos_b in _branch_pairs(pillars):
        key = frozenset({a, b})
        if key in PA:
            results.append(InteractionEntry(
                type="파", subtype="파",
                positions=[pos_a, pos_b],
                elements=[a, b],
                description=f"{a}↔{b} 파",
            ))

    # ── 10. 해 ──
    for a, b, pos_a, pos_b in _branch_pairs(pillars):
        key = frozenset({a, b})
        if key in HAE:
            results.append(InteractionEntry(
                type="해", subtype="해",
                positions=[pos_a, pos_b],
                elements=[a, b],
                description=f"{a}↔{b} 해",
            ))

    return results


def detect_interactions_with_branch(pillars: FourPillars, extra_branch: str,
                                     extra_label: str = "세운") -> list[InteractionEntry]:
    """원국 지지와 외부 지지(세운/대운) 사이의 합충형파해."""
    results: list[InteractionEntry] = []
    bl = _branch_list(pillars)

    for b, pos in bl:
        key = frozenset({b, extra_branch})

        # 육합
        if key in YUKAP:
            results.append(InteractionEntry(
                type="합", subtype="육합",
                positions=[pos, extra_label],
                elements=[b, extra_branch],
                result=f"→ {YUKAP[key]}",
                description=f"{b}+{extra_branch} 육합 → {YUKAP[key]}",
            ))

        # 육충
        if key in YUKCHUNG:
            results.append(InteractionEntry(
                type="충", subtype="육충",
                positions=[pos, extra_label],
                elements=[b, extra_branch],
                description=f"{b}↔{extra_branch} 육충",
            ))

        # 형
        for condition, name in HYUNG:
            pair = {b, extra_branch}
            if len(condition) == 2 and pair == set(condition):
                results.append(InteractionEntry(
                    type="형", subtype=name,
                    positions=[pos, extra_label],
                    elements=[b, extra_branch],
                    description=f"{b}↔{extra_branch} {name}",
                ))

        # 파
        if key in PA:
            results.append(InteractionEntry(
                type="파", subtype="파",
                positions=[pos, extra_label],
                elements=[b, extra_branch],
                description=f"{b}↔{extra_branch} 파",
            ))

        # 해
        if key in HAE:
            results.append(InteractionEntry(
                type="해", subtype="해",
                positions=[pos, extra_label],
                elements=[b, extra_branch],
                description=f"{b}↔{extra_branch} 해",
            ))

    return results
