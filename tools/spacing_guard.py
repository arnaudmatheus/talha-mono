"""Limit width-based shifts to contexts with sufficiently uneven contour gaps."""

import math
from typing import NamedTuple

from fontTools.ttLib import TTFont

from spacing_profiles import ContourProfile, canonical_bodies, contour_gap

GAP_BIN = 80


class NeighborGap(NamedTuple):
    names: tuple[str, ...]
    width_class: int
    before: float
    after: float


class GuardRule(NamedTuple):
    origins: tuple[str, ...]
    before: tuple[str, ...]
    after: tuple[str, ...]
    direction: int


def neighbor_gaps(
    groups: dict[str, list[str]],
    profiles: dict[str, ContourProfile],
    classes: dict[str, int],
    center: str,
    cell: int,
) -> list[NeighborGap]:
    return [
        NeighborGap(
            tuple(names),
            classes[name],
            contour_gap(profiles[name], profiles[center], cell),
            contour_gap(profiles[center], profiles[name], cell),
        )
        for name, names in groups.items()
    ]


def _before_buckets(neighbors: list[NeighborGap]) -> list[list[NeighborGap]]:
    buckets: dict[tuple[int, int], list[NeighborGap]] = {}
    for neighbor in neighbors:
        if not math.isfinite(neighbor.before):
            continue
        bucket = (neighbor.width_class, math.floor(neighbor.before / GAP_BIN))
        buckets.setdefault(bucket, []).append(neighbor)
    return list(buckets.values())


def guarded_neighbors(
    bucket: list[NeighborGap], neighbors: list[NeighborGap], direction: int, shift: int
) -> tuple[str, ...]:
    """Use the strictest gap in a bin, avoiding rounding-based activation; e.g. ``guarded_neighbors(b, n, -1, 40)``."""
    edge = (max if direction > 0 else min)(n.before for n in bucket)
    width = bucket[0].width_class
    return tuple(
        name
        for neighbor in neighbors
        if direction * (width - neighbor.width_class) > 0
        and direction * (neighbor.after - edge) > 2 * shift
        for name in neighbor.names
    )


def center_guard_rules(
    origins: list[str], neighbors: list[NeighborGap], shift: int
) -> list[GuardRule]:
    rules = []
    for bucket in _before_buckets(neighbors):
        before = tuple(name for neighbor in bucket for name in neighbor.names)
        for direction in (-1, 1):
            after = guarded_neighbors(bucket, neighbors, direction, shift)
            if after:
                rules.append(GuardRule(tuple(origins), before, after, direction))
    return rules


def spacing_guard_rules(
    font: TTFont,
    origins: list[str],
    groups: dict[str, list[str]],
    profiles: dict[str, ContourProfile],
    classes: dict[str, int],
    shift: int,
) -> list[GuardRule]:
    """Generate rules without word-specific exceptions; e.g. ``spacing_guard_rules(font, origins, groups, profiles, classes, 40)``."""
    cell, rules = font["hmtx"]["i"][0], []
    for center, names in canonical_bodies(font, origins).items():
        neighbors = neighbor_gaps(groups, profiles, classes, center, cell)
        rules.extend(center_guard_rules(names, neighbors, shift))
    return rules
