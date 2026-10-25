"""Step 1: the base letters, capitals and figures, drawn and centred."""

import pen
from build_state import BuildState, ContextForm
from glyph_table import band_top

# Optical centring (roadmap D1): r and k sit on their ink's centre of mass,
# not on their bounding box (their arm and leg reach right, so the box put
# the stem too far left and left a hole before the next letter). Measured one
# letter at a time: r alone took spacing variation 0.283 -> 0.265; applied to
# every letter it made i/l, l/I, t/f worse (narrow letters lined up alike in
# the cell), and c e s b h each traded one pair for another.
OPTICAL = {"r": 1.0, "k": 1.0}


def place_letters(state: BuildState) -> None:
    """Draws every glyph of the table and records where it sits in the cell."""
    w, t = state.nib
    for gname, (fn, kind) in state.glyphs.items():
        pen.OPTICAL = OPTICAL.get(gname, 0)
        shape, dx = pen.place(fn(), w, t, band_top=band_top(kind))
        pen.OPTICAL = 0
        state.writer.put(gname, shape)
        state.placed[gname] = dx
        state.replaced.append(gname)
        # The Turkish i (locl) is the same dotted i.
        if gname == "i" and state.writer.has("i.loclTRK"):
            state.writer.put("i.loclTRK", shape)
            state.replaced.append("i.loclTRK")
            state.context_forms["i.loclTRK"] = ContextForm("i", 1.0, 0.0)
