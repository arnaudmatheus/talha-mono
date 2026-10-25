"""Steps 3 and 4: accented letters and the combining marks themselves."""

import re
import unicodedata as ud

from shapely import affinity
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

import caps
import pen
from anchors import anchors, final, shifted
from build_state import BuildState, Composition
from marks import CARON_APOSTROPHE, MARKS
from pen_types import Point, Stroke

CARON = 0x30C
# ď ľ ť Ľ take the caron as an apostrophe beside the letter.
CARON_AS_APOSTROPHE = ("d", "l", "t", "L")
# Each further mark above a letter sits this much higher.
STACK_STEP = {"lower": 230, "cap": 200}
# Radon's ready-made Vietnamese stacks: circumflex or breve + another mark.
VIETNAMESE_STACK = re.compile(r"^uni(0302|0306)(030[0-9A-F])$")


def _caron_apostrophe(gname: str, a: dict[str, Point]) -> list[Stroke]:
    special = {"t": (a["caronapos"][0], 1200), "L": (560, caps.CT - 40)}
    ax, ay = special.get(gname, a["caronapos"])
    return shifted(CARON_APOSTROPHE, ax, ay)


def _mark_strokes(state: BuildState, gname: str, marks_cps: list[int]) -> list[Stroke]:
    """The marks' strokes placed on the letter's anchors, stacked upward."""
    kind, a = state.glyphs[gname].kind, anchors(state.glyphs[gname], gname)
    extra, stack = [], 0
    for cp in marks_cps:
        kind_m, strokes = MARKS[cp]
        if cp == CARON and gname in CARON_AS_APOSTROPHE:
            extra += _caron_apostrophe(gname, a)
            continue
        ax, ay = a[kind_m]
        extra += shifted(strokes, ax, ay + stack if kind_m == "above" else ay)
        if kind_m == "above":
            stack += STACK_STEP[kind]
    return extra


def compose(state: BuildState, gname: str, marks_cps: list[int]) -> BaseGeometry:
    """A precomposed letter: the base's strokes plus its marks, one sweep."""
    w, t = state.nib
    strokes = composition_strokes(state, gname, marks_cps)
    shape, _ = pen.place(strokes, w, t, dx=state.placed[gname])
    return shape


def composition_strokes(
    state: BuildState, gname: str, marks_cps: list[int]
) -> list[Stroke]:
    """Share the same pen recipe with healed accents; e.g. ``composition_strokes(s, 'i', [0x328])``."""
    body = state.glyphs[gname].strokes()
    marks = _mark_strokes(state, gname, marks_cps)
    return body + marks


def _base_for(decomposed: str) -> str:
    """i and j lose their dot under a mark above."""
    base = decomposed[0]
    if base in "ij" and any(MARKS[ord(m)][0] == "above" for m in decomposed[1:]):
        return "dotlessi" if base == "i" else "uni0237"
    return base


def _decomposes_to_marks(gname: str, d: str, state: BuildState) -> bool:
    if len(d) < 2 or gname in state.glyphs:
        return False
    base = state.font.getBestCmap().get(ord(d[0]))
    if base not in state.glyphs:
        return False
    return all(ord(m) in MARKS for m in d[1:])


def place_precomposed(state: BuildState) -> None:
    """Step 3: every precomposed accented letter, lower and upper."""
    for cp, gname in sorted(state.font.getBestCmap().items()):
        d = ud.normalize("NFD", chr(cp))
        if not _decomposes_to_marks(gname, d, state):
            continue
        base = _base_for(d)
        if base not in state.glyphs:
            base = state.font.getBestCmap()[ord(d[0])]
        state.writer.put(gname, compose(state, base, [ord(m) for m in d[1:]]))
        state.replaced.append(gname)
        # The precomposed letter is a mark base too: HarfBuzz recomposes u + ¨
        # into ü before positioning, and the acute of ǘ needs an anchor above
        # the dieresis.
        state.compositions[gname] = Composition(base, tuple(ord(m) for m in d[1:]))


def _mark_shape(state: BuildState, strokes: list[Stroke], dx: float) -> BaseGeometry:
    w, t = state.nib
    shape = unary_union([pen.sweep(pen.slant(st), w, t) for st in strokes])
    return affinity.translate(shape, dx, 0)


def _put_mark(
    state: BuildState, gname: str, kind: str, shape: BaseGeometry, anchor: Point
) -> None:
    state.writer.put(gname, shape)
    state.replaced.append(gname)
    state.mark_anchors[gname] = (kind, anchor)


def place_marks(state: BuildState) -> None:
    """Step 4: combining marks, drawn for an x-height letter at the cell centre."""
    cmap = state.font.getBestCmap()
    a, dx = anchors(state.glyphs["n"], "n"), state.placed["n"]
    for cp, (kind, strokes) in MARKS.items():
        if cp not in cmap:
            continue
        ax, ay = a[kind]
        shape = _mark_shape(state, shifted(strokes, ax, ay), dx)
        _put_mark(state, cmap[cp], kind, shape, final((ax, ay), dx))


def _case_mark_cps(gname: str, name_cp: dict[str, int]) -> list[int]:
    """The marks a .case copy or a Vietnamese stack is made of ([] if neither)."""
    stem_name = gname.split(".")[0]
    combo = VIETNAMESE_STACK.match(stem_name)
    if gname.endswith(".case") and stem_name in name_cp:
        return [name_cp[stem_name]]
    if combo and (gname == stem_name or gname.endswith(".case")):
        return [int(combo.group(1), 16), int(combo.group(2), 16)]
    return []


def place_case_marks(state: BuildState) -> None:
    """Step 4b: Radon's ccmp swaps marks after capitals for `.case` copies,
    and uses ready-made stacks for Vietnamese (uni03020301 = circumflex +
    acute). Without pen outlines and anchors those stayed Radon's and never
    attached (G̃ broke)."""
    cmap = state.font.getBestCmap()
    name_cp = {cmap[cp]: cp for cp in MARKS if cp in cmap}
    for gname in state.font.getGlyphOrder():
        cps = _case_mark_cps(gname, name_cp)
        if not cps or any(c not in MARKS or MARKS[c][0] != "above" for c in cps):
            continue
        a, dx = anchors(state.glyphs["n"], "n"), state.placed["n"]
        ax, ay = a["above"]
        strokes = []
        for i, c in enumerate(cps):
            strokes += shifted(MARKS[c][1], ax + (70 if i else 0), ay + 220 * i)
        _put_mark(
            state, gname, "above", _mark_shape(state, strokes, dx), final((ax, ay), dx)
        )
