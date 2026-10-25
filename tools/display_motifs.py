"""Display studies for a lobed rocaille leaf and a folded inscription ribbon."""

import ornament
from ornament import Motif, NibStroke, fine
from pen import path

SELECTED_MOTIF = 2


def leaf_edges(variant: int) -> list[NibStroke]:
    upper = path(
        ("M", (-250, -250)),
        ("C", (-370, -50), (-340, 200), (-170, 170)),
        ("C", (-250, 350), (-60, 420), (40, 290)),
        ("C", (100, 440), (250, 430), (340, 340)),
    )
    lower = path(
        ("M", (-250, -250)),
        ("C", (-30, -350), (210, -270), (150, -100)),
        ("C", (350, -180), (410, 80), (270, 100)),
        ("C", (420, 150), (420, 270), (340, 340)),
    )
    weight = 0.65 if variant < 3 else 0.8
    return [(upper, weight), (lower, weight)]


def leaf_ribs(variant: int) -> list[NibStroke]:
    vein = path(("M", (-250, -250)), ("C", (-80, -40), (160, 80), (310, 310)))
    if variant == 1:
        return [fine(vein)]
    upper = path(("M", (-60, -60)), ("C", (-160, 0), (-170, 90), (-170, 170)))
    lower = path(("M", (80, 40)), ("C", (130, -20), (160, -50), (150, -100)))
    return [fine(vein), fine(upper), fine(lower)]


def leaf_study(variant: int = SELECTED_MOTIF, heavy: bool = False) -> Motif:
    """A scalloped leaf with a supporting scroll; e.g. ``leaf_study(2)``."""
    if variant not in (1, 2, 3):
        raise ValueError(f"{variant!r}: expected a leaf study in (1, 2, 3)")
    stem = path(("M", (-250, -250)), ("C", (-300, -300), (-400, -280), (-400, -230)))
    scroll = ornament.volute(-400, -80, 150, -90, cw=False)
    strokes = leaf_edges(variant) + [fine(stem)] + scroll
    if not heavy:
        return strokes + leaf_ribs(variant), []
    outlines = [
        stroke[0] if isinstance(stroke, tuple) else stroke
        for stroke in leaf_edges(variant)
    ]
    return strokes, [outlines[0] + list(reversed(outlines[1]))]


def ribbon_planes(cell: int) -> list[NibStroke]:
    edge = cell - 110
    face = path(
        ("M", (edge, 1060)), ("L", (480, 1060)), ("L", (480, 260)), ("L", (edge, 260))
    )
    rear = path(
        ("M", (480, 860)),
        ("L", (150, 860)),
        ("L", (300, 460)),
        ("L", (150, 60)),
        ("L", (650, 60)),
        ("L", (480, 260)),
    )
    return [(face, 0.7), (rear, 0.6)]


def ribbon_study(variant: int = SELECTED_MOTIF, cell: int = 1160) -> Motif:
    """A front band, rear tail and readable fold; e.g. ``ribbon_study(2, 1320)``."""
    if variant not in (1, 2, 3):
        raise ValueError(f"{variant!r}: expected a ribbon study in (1, 2, 3)")
    edge = cell - 110
    strokes = ribbon_planes(cell)
    if variant > 1:
        fold = path(("M", (650, 60)), ("L", (650, 260)))
        strokes.append(fine(fold))
    if variant == 3:
        inset = path(("M", (edge, 930)), ("L", (610, 930)), ("L", (610, 390)))
        strokes.append((inset, 0.35))
    return strokes, []
