"""Independent raw drawing functions for each style and stem profile.

The refined t/l/1 stems became the default in 1.0.0-beta.7, chosen by the
user on 2026-10-24 (docs/design/beta7.md, "Release").
"""

from typing import NamedTuple

import caps
import corsiva
import letters
from pen_types import StrokesFn
from stem_recipes import stem_drawing


class DrawingCatalog(NamedTuple):
    lower: dict[str, StrokesFn]
    figures: dict[str, StrokesFn]
    extra_lower: dict[str, StrokesFn]


def drawing_catalog(italic: bool = False, refined_stems: bool = True) -> DrawingCatalog:
    """Resolve all dependent recipes in one style-local catalog; e.g. ``drawing_catalog(True, True)``."""
    lower, figures = dict(letters.LETTERS), dict(caps.FIGURES)
    if italic:
        lower.update(corsiva.CORSIVA)
    if refined_stems:
        for name in ("t", "l"):
            lower[name] = stem_drawing(name, lower[name], 20)
        figures["one"] = stem_drawing("one", figures["one"], 10)
    extra = dict(caps.EXTRAS_LOWER)
    extra.update(caps.crossed_lower(lower))
    return DrawingCatalog(lower, figures, extra)
