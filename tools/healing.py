"""Step 2: texture-healing variants (a.left, m.right, ...) with the pen.

Each variant is the base letter's skeleton, widened or shifted to Radon's
measured extents for that variant, then swept with the nib.
"""

import re

from shapely.ops import unary_union

import pen
from accents import composition_strokes
from build_state import BuildState, ContextForm
from pen_types import Stroke

VARIANT = re.compile(r"^([A-Za-z0-9_]+)\.(left|right|both)$")


def _stretch(state: BuildState, base: str, variant: str) -> tuple[float, float]:
    """(x scale, x shift) from the base letter to Radon's variant.

    The base is already the pen letter by now; the variant is still Radon's.
    """
    bx0, _, bx1, _ = state.writer.bounds(base)
    vx0, _, vx1, _ = state.writer.bounds(variant)
    r = (vx1 - vx0) / (bx1 - bx0)
    shift = (vx0 + vx1) / 2 - (bx0 + bx1) / 2
    # Texture healing re-derived (roadmap D2): Radon's narrow letters step
    # aside and its wide ones grow into the room. Talha's m and w already fill
    # the cell, so growing them made the healed pairs the tightest in the font
    # (mt, wt 7.5 px against a 13.8 mean at 40 px). Measured over a grid of
    # strengths, wide lowercase that doesn't grow is the most even (CV over
    # bigrams and three-letter contexts 0.266 -> 0.247 Regular, 0.290 ->
    # 0.264 Italic); narrow letters keep Radon's step.
    if r > 1 and base.islower():
        return 1.0, 0.0
    return r, shift


def _heal(state: BuildState, base: str, variant: str) -> None:
    w, t = state.nib
    r, shift = _stretch(state, base, variant)
    dx = state.placed[base]
    c = state.opts.cell / 2
    # Skeleton slanted and centred; widen/shift it to Radon's variant, then
    # sweep. The nib angle stays 35° because only the path moves.
    strokes = [
        [(c + (x + dx - c) * r + shift, y) for x, y in pen.slant(st)]
        for st in state.glyphs[base].strokes()
    ]
    state.writer.put(variant, unary_union([pen.sweep(st, w, t) for st in strokes]))
    state.replaced.append(variant)
    state.context_forms[variant] = ContextForm(base, r, c * (1 - r) + shift)


def heal_texture(state: BuildState) -> None:
    for variant in state.font.getGlyphOrder():
        m = VARIANT.match(variant)
        if m and m.group(1) in state.glyphs:
            _heal(state, m.group(1), variant)


def draw_context_strokes(
    state: BuildState, name: str, strokes: list[Stroke], dx: float, form: ContextForm
) -> None:
    """Transform skeletons before sweeping, preserving the nib; e.g. ``draw_context_strokes(s, n, strokes, dx, form)``."""
    placed = [
        [(form.scale * (x + dx) + form.shift, y) for x, y in pen.slant(st)]
        for st in strokes
    ]
    shape = unary_union([pen.sweep(st, *state.nib) for st in placed])
    state.writer.put(name, shape)
    state.replaced.append(name)
    state.context_forms[name] = form


def heal_composites(state: BuildState) -> None:
    """Rebuild accented healing forms from Talha recipes; e.g. ``heal_composites(state)``."""
    for name in state.font.getGlyphOrder():
        match = VARIANT.fullmatch(name)
        if not match or match[1] not in state.compositions:
            continue
        recipe = state.compositions[match[1]]
        source = _composition_context(state, recipe.base, match[2])
        if source is None:
            continue
        strokes = composition_strokes(state, recipe.base, list(recipe.marks))
        form = ContextForm(match[1], source.scale, source.shift)
        draw_context_strokes(state, name, strokes, state.placed[recipe.base], form)


def _composition_context(state: BuildState, base: str, side: str) -> ContextForm | None:
    # Radon has no uni0237.left/right/both. Accented j still needs the same
    # contextual placement as j, with a genuinely dotless pen recipe.
    fallback = {"uni0237": "j", "dotlessi": "i"}.get(base, base)
    primary = state.context_forms.get(f"{base}.{side}")
    return primary or state.context_forms.get(f"{fallback}.{side}")
