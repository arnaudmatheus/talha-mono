"""Shared raw-grid stem refinements, before lowercase height mapping."""

from pen_types import Stroke, StrokesFn

STEM_NAMES = ("t", "l", "one")


def adjust_stem_recipe(name: str, strokes: list[Stroke], strength: int) -> list[Stroke]:
    """Keep recipes immutable and in their original grid; e.g. ``adjust_stem_recipe('t', fn(), 20)``."""
    allowed = (0, 10, 20) if name == "one" else (0, 20)
    if name not in STEM_NAMES or strength not in allowed:
        raise ValueError(f"{name!r}/{strength}: expected t/l at 0/20 or one at 0/10/20")
    changed = [list(stroke) for stroke in strokes]
    if name == "t":
        changed[1] = [(x, y - strength) for x, y in changed[1]]
    elif name == "l":
        changed[0] = [(x + strength * max(0, 1 - y / 300), y) for x, y in changed[0]]
    else:
        changed[0] = [
            (x - strength * (640 - x) / 390 if x < 640 else x, y) for x, y in changed[0]
        ]
    return changed


def stem_drawing(name: str, original: StrokesFn, strength: int) -> StrokesFn:
    """Capture a per-build source without mutating global catalogs; e.g. ``stem_drawing('l', fn, 20)``."""

    def draw() -> list[Stroke]:
        return adjust_stem_recipe(name, original(), strength)

    return draw
