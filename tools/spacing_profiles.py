"""Shared-height contour gaps keep spacing decisions sensitive to asymmetry."""

import unicodedata
from typing import NamedTuple

import numpy as np
from fontTools.ttLib import TTFont
from shapely.geometry import LineString

from punct import outline

PROFILE_ROWS = range(-400, 2001, 16)


class ContourProfile(NamedTuple):
    left: np.ndarray
    right: np.ndarray


def canonical_bodies(font: TTFont, names: list[str]) -> dict[str, list[str]]:
    """Group accents with their letter bodies; e.g. ``canonical_bodies(font, ['a', 'aacute'])``."""
    cmap, decomposed = font.getBestCmap(), {}
    for cp, name in cmap.items():
        sequence = unicodedata.normalize("NFD", chr(cp))
        if len(sequence) > 1 and ord(sequence[0]) in cmap:
            decomposed[name] = cmap[ord(sequence[0])]
    order = set(font.getGlyphOrder())
    groups: dict[str, list[str]] = {}
    for name in sorted(names):
        root, *suffix = name.split(".")
        body = decomposed.get(root, root)
        candidate = ".".join([body] + suffix)
        groups.setdefault(candidate if candidate in order else body, []).append(name)
    return groups


def contour_profiles(font: TTFont, names: list[str]) -> dict[str, ContourProfile]:
    """Sample visible edges on common font-unit rows; e.g. ``contour_profiles(font, ['l', 't'])``."""
    glyphs, profiles = font.getGlyphSet(), {}
    for name in names:
        ink = outline(glyphs, name)
        bounds = [
            ink.intersection(LineString([(-2000, y), (5000, y)])).bounds
            for y in PROFILE_ROWS
        ]
        edges = np.array(
            [(b[0], b[2]) if len(b) == 4 else (np.nan, np.nan) for b in bounds]
        )
        profiles[name] = ContourProfile(edges[:, 0], edges[:, 1])
    return profiles


def contour_gap(left: ContourProfile, right: ContourProfile, cell: int) -> float:
    """Average only rows containing both bodies; e.g. ``contour_gap(profiles['t'], profiles['l'], 1160)``."""
    valid = np.isfinite(left.right) & np.isfinite(right.left)
    if not valid.any():
        return float("nan")
    return float(np.mean(cell + right.left[valid] - left.right[valid]))
