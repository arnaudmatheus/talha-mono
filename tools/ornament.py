"""Ornament, all opt-in (roadmap 0.8.0): nothing here reaches default text.

- Florões (I1): the rocalha leaf, the vine leaf, the bud and the hedera, at
  Unicode's ornament code points (U+2619, U+2766-2767, U+1F650-1F667). The
  C- and S-scroll of Aleijadinho's carving is in every stem.
- Cartelas (I2): frame halves after the painted cartouches of Manuel da
  Costa Ataíde's nave ceiling (São Francisco de Assis, Ouro Preto,
  1801-1812), at the bracket ornaments U+2768-276B, U+2772-2775.
- Filactérios (I3): ribbon ends after the inscribed scrolls of Aleijadinho's
  Twelve Prophets at Congonhas. Unicode has no banner code points, so they
  live at the heavy angle bracket ornaments ❰ ❱ (U+2770-2771).
- Capitulares (I4): titl, carved inline capitals after lettering cut in
  stone; swsh, capitals with Figueiredo's pen flourish (rasgo). Both are
  OpenType features, off by default.

Every motif is one skeleton. Mirrored and turned forms are made on the
skeleton before the nib sweeps it, so the 35° contrast never flips. The
ornaments stay upright: they are drawn, not written."""

import math
from collections.abc import Callable
from functools import partial

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

import pen
from letters import GOTA
from pen import path
from pen_types import Stroke

# A stroke drawn with the full nib, or (points, k) with the nib scaled by k.
NibStroke = Stroke | tuple[Stroke, float]
# A motif: its strokes, and the closed outlines it fills.
Motif = tuple[list[NibStroke], list[Stroke]]
PointMap = Callable[[Stroke], Stroke]

CELL = 1160  # merge.py sets the real cell (1320 in Wide)
CY = 640  # bullets sit on the math axis


def CX() -> float:
    return CELL / 2


FLORAL_SCALE = 1.12  # motifs are drawn in ±430 and stay inside the cell


def _xf(
    pts: Stroke,
    mx: float = 1,
    my: float = 1,
    swap: bool = False,
    cx: float | None = None,
    cy: float = CY,
    k: float = FLORAL_SCALE,
) -> Stroke:
    cx = CX() if cx is None else cx
    out = []
    for x, y in pts:
        if swap:
            x, y = y, x
        out.append((cx + k * mx * x, cy + k * my * y))
    return out


def spiral(
    cx: float,
    cy: float,
    r_out: float,
    r_in: float,
    a0: float,
    turns: float = 1.15,
    cw: bool = True,
    n: int = 48,
) -> Stroke:
    """An open scroll: an Archimedean spiral from r_out to r_in, starting at
    angle a0 (degrees). Every curl in the ornament is one of these, sized so
    the nib (≈140 units) never fills it in: a volute narrower than about 2.5
    nib widths turns into a blot."""
    pts = []
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0) + (-1 if cw else 1) * u * turns * 2 * math.pi
        r = r_out + (r_in - r_out) * u
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


FINE = 0.55  # engraved line: curls, veins, tendrils


def volute(
    cx: float, cy: float, r_out: float, a0: float, cw: bool = True, turns: float = 1.15
) -> list[NibStroke]:
    """A scroll with the drop at its eye, drawn with the fine line."""
    pts = spiral(cx, cy, r_out, r_out * 0.5, a0, turns, cw)
    ex, ey = pts[-1]
    return [(pts, FINE), (GOTA(ex, ey, max(30, r_out * 0.2)), FINE)]


def fine(pts: Stroke) -> tuple[Stroke, float]:
    return (pts, FINE)


def _map(s: NibStroke, fn: PointMap) -> NibStroke:
    """Apply a point transform to a stroke, keeping its nib weight."""
    return (fn(s[0]), s[1]) if isinstance(s, tuple) else fn(s)


def render(
    strokes: list[NibStroke], fills: list[Stroke], w: float, t: float
) -> BaseGeometry:
    """strokes: point lists (the full nib) or (points, k) for a lighter nib."""
    parts = [
        (
            pen.sweep_broad(s[0], w * s[1], t * s[1])
            if isinstance(s, tuple)
            else pen.sweep_broad(s, w, t)
        )
        for s in strokes
    ]
    parts += [Polygon(f).buffer(0) for f in fills]
    return unary_union(parts)


# ---------------------------------------------------------------- florões
def leaf_ne(heavy: bool = False) -> Motif:
    """Rocalha leaf pointing north-east: scalloped lobes, fine ribs, and a
    supporting C-scroll. Display pilot, October 2026."""
    # Keep the study module's helpers outside the core ornament vocabulary.
    from display_motifs import leaf_study

    return leaf_study(heavy=heavy)


def vine_ne(heavy: bool = False) -> Motif:
    """Vine leaf pointing north-east: three lobes and a coiled tendril."""
    edge = path(
        ("M", (-230, -230)),
        ("C", (-330, 0), (-260, 200), (-80, 170)),  # left lobe
        ("C", (-120, 330), (60, 420), (330, 340)),  # tip lobe
        ("C", (420, 60), (330, -120), (170, -80)),  # right lobe
        ("C", (200, -260), (0, -330), (-230, -230)),
    )
    vein = path(("M", (-230, -230)), ("L", (240, 240)))
    tendril = path(("M", (-230, -230)), ("C", (-270, -280), (-320, -330), (-380, -330)))
    curl = volute(-380, -150, 180, -90, cw=False, turns=1.5)
    strokes = [(edge, 0.75), fine(tendril)] + curl + ([] if heavy else [fine(vein)])
    return strokes, ([edge] if heavy else [])


def bud_ne(heavy: bool = False) -> Motif:
    """A closed bud pointing north-east, held by two sepals, on a scrolled stem."""
    body = path(
        ("M", (330, 330)),
        ("C", (180, 330), (-60, 200), (-60, 20)),
        ("C", (-60, -60), (-10, -110), (60, -110)),
        ("C", (220, -110), (330, 160), (330, 330)),
    )
    sepal_a = path(("M", (-150, -150)), ("C", (-170, 0), (-120, 80), (-40, 90)))
    sepal_b = path(("M", (-150, -150)), ("C", (0, -170), (80, -120), (90, -40)))
    stem = path(("M", (-150, -150)), ("C", (-220, -220), (-300, -320), (-380, -320)))
    curl = volute(-380, -150, 170, -90, cw=False)
    strokes = [(body, 0.75), fine(sepal_a), fine(sepal_b), fine(stem)] + curl
    return strokes, ([body] if heavy else [])


def hedera_down() -> Motif:
    """The hedera (floral heart, ❦): a solid heart leaf, point down, its stem
    rising and curling over to the left."""
    heart = path(
        ("M", (0, -400)),
        ("C", (-180, -250), (-370, -70), (-350, 110)),
        ("C", (-330, 270), (-130, 300), (0, 180)),
        ("C", (130, 300), (330, 270), (350, 110)),
        ("C", (370, -70), (180, -250), (0, -400)),
    )
    stem = path(("M", (0, 180)), ("C", (10, 290), (40, 360), (120, 400)))
    curl = volute(-30, 420, 150, 0, cw=False, turns=1.1)
    return [(heart, 0.75), fine(stem)] + curl, [heart]


def _oriented(
    builder: Callable[[bool], Motif],
    direction: str,
    turned: bool = False,
    heavy: bool = False,
) -> Motif:
    """direction: NE, NW, SE, SW. turned: mirrored across the motif's own axis."""
    strokes, fills = builder(heavy)
    mx = -1 if direction in ("NW", "SW") else 1
    my = -1 if direction in ("SE", "SW") else 1

    def f(pts: Stroke) -> Stroke:
        return _xf(pts, mx, my, swap=turned)

    return [_map(s, f) for s in strokes], [f(s) for s in fills]


def _hedera(rot: str) -> Motif:
    strokes, fills = hedera_down()

    def r(pts: Stroke) -> Stroke:
        if rot == "down":
            return _xf(pts)
        k = FLORAL_SCALE
        if rot == "right":  # ❧: rotated, pointing right
            return [(CX() - k * y, CY + k * x) for x, y in pts]
        # ☙: reversed, pointing left
        return [(CX() + k * y, CY - k * x) for x, y in pts]

    return [_map(s, r) for s in strokes], [r(s) for s in fills]


FLOROES: dict[int, Callable[[], Motif]] = {
    0x2766: lambda: _hedera("down"),
    0x2767: lambda: _hedera("right"),
    0x2619: lambda: _hedera("left"),
}
_DIRS = {0: "NW", 1: "SW", 2: "NE", 3: "SE"}
for k in range(4):
    d = _DIRS[k]
    FLOROES[0x1F650 + k] = partial(_oriented, leaf_ne, d)
    FLOROES[0x1F654 + k] = partial(_oriented, leaf_ne, d, turned=True)
    FLOROES[0x1F658 + k] = partial(_oriented, vine_ne, d)
    FLOROES[0x1F65C + k] = partial(_oriented, vine_ne, d, heavy=True)
    FLOROES[0x1F660 + k] = partial(_oriented, bud_ne, d)
    FLOROES[0x1F664 + k] = partial(_oriented, bud_ne, d, heavy=True)

# ---------------------------------------------------------------- cartelas
TOP, BOT = 1520, -320  # a frame half spans the bracket height
MIDY = (TOP + BOT) / 2


def _volute(
    x: float, y: float, s: int = 1, up: int = 1, r: float = 190
) -> list[NibStroke]:
    """The scrolled end of a cartouche frame at (x, y), curling in toward the
    text (s: +1 = to the right) and down from the top (up=-1) or up from the
    bottom (up=1)."""
    cx, cy = x, y + up * r
    a0 = 90 if up == -1 else -90
    cw = (s == 1) == (up == -1)
    return volute(cx, cy, r, a0, cw=cw)


def cartela_paren() -> Motif:
    # A C-scroll bow with scrolled ends and a drop at its outer middle.
    bow = path(("M", (640, TOP)), ("C", (180, TOP - 420), (180, BOT + 420), (640, BOT)))
    return [bow, GOTA(240, MIDY, 60)] + _volute(640, TOP, 1, -1) + _volute(
        640, BOT, 1, 1
    ), []


def cartela_flat() -> Motif:
    bow = path(("M", (660, TOP)), ("C", (420, TOP - 380), (420, BOT + 380), (660, BOT)))
    shell = [
        path(("M", (470, MIDY)), ("L", (330 + 40 * k, MIDY + 160 * (k - 1.5) / 1.5)))
        for k in range(4)
    ]
    rim = path(
        ("M", (330, MIDY - 160)),
        ("C", (260, MIDY - 60), (260, MIDY + 60), (330, MIDY + 160)),
    )
    strokes: list[NibStroke] = [bow, fine(rim)]
    strokes += [fine(s) for s in shell]
    strokes += _volute(660, TOP, 1, -1) + _volute(660, BOT, 1, 1)
    return strokes, []


def cartela_shell() -> Motif:
    frame = path(
        ("M", (760, TOP)),
        ("L", (480, TOP - 160)),
        ("L", (480, BOT + 160)),
        ("L", (760, BOT)),
    )
    return [frame, GOTA(790, TOP + 10, 34), GOTA(790, BOT - 10, 34)], []


def cartela_brace() -> Motif:
    top = path(
        ("M", (760, TOP)),
        ("C", (560, TOP), (520, TOP - 120), (520, TOP - 320)),
        ("L", (520, MIDY + 260)),
        ("C", (520, MIDY + 120), (460, MIDY + 30), (300, MIDY)),
    )
    bot = path(
        ("M", (300, MIDY)),
        ("C", (460, MIDY - 30), (520, MIDY - 120), (520, MIDY - 260)),
        ("L", (520, BOT + 320)),
        ("C", (520, BOT + 120), (560, BOT), (760, BOT)),
    )
    curl = volute(300, MIDY - 150, 150, 90, cw=False)
    return [top, bot] + curl + _volute(760, TOP, 1, -1) + _volute(760, BOT, 1, 1), []


def _mirror(builder: Callable[[], Motif]) -> Motif:
    s, f = builder()

    def m(pts: Stroke) -> Stroke:
        return [(CELL - x, y) for x, y in pts]

    return [_map(p, m) for p in s], [m(p) for p in f]


CARTELAS: dict[int, Callable[[], Motif]] = {
    0x2768: cartela_paren,
    0x2769: lambda: _mirror(cartela_paren),
    0x276A: cartela_flat,
    0x276B: lambda: _mirror(cartela_flat),
    0x2772: cartela_shell,
    0x2773: lambda: _mirror(cartela_shell),
    0x2774: cartela_brace,
    0x2775: lambda: _mirror(cartela_brace),
}

# ---------------------------------------------------------------- filactérios
RT, RB = 1060, 260  # ribbon edges: from x-height down past the baseline


def ribbon_end_left() -> Motif:
    """The end of an inscribed ribbon: a front band, a rear swallowtail,
    and the crease between them. A small margin keeps the Bold inside the cell."""
    from display_motifs import ribbon_study

    return ribbon_study(cell=CELL)


FILACTERIOS: dict[int, Callable[[], Motif]] = {
    0x2770: ribbon_end_left,
    0x2771: lambda: _mirror(ribbon_end_left),
}

ORNAMENTS: dict[int, Callable[[], Motif]] = {**FLOROES, **CARTELAS, **FILACTERIOS}
HEAVY: set[int] = set(range(0x1F65C, 0x1F660)) | set(range(0x1F664, 0x1F668))


# ---------------------------------------------------------------- capitulares
def carved(strokes: list[Stroke], w: float, t: float) -> BaseGeometry:
    """titl: the letter cut in stone. A heavier stroke with a fine groove down
    its centre, as in inscriptions carved with a V-cut: the light catches one
    wall and leaves the groove dark."""
    outer = unary_union([pen.sweep_broad(s, w * 1.25, t * 1.35) for s in strokes])
    groove = unary_union([pen.sweep_broad(s, 34, 34) for s in strokes])
    return outer.difference(groove)


def _flourish_head(minx: float, maxy: float) -> list[NibStroke]:
    entry = path(
        ("M", (minx + 160, maxy - 10)),
        ("C", (minx + 100, maxy + 60), (minx, maxy + 80), (minx - 90, maxy + 40)),
    )
    return [fine(entry)] + volute(minx - 90, maxy - 140, 180, 90, cw=False)


def _flourish_tail(minx: float, miny: float, maxx: float) -> Stroke:
    return path(
        ("M", (minx - 60, miny + 160)),
        (
            "C",
            (minx - 140, miny - 40),
            (minx + 60, miny - 190),
            (minx + 320, miny - 170),
        ),
        (
            "C",
            (maxx - 120, miny - 150),
            (maxx + 120, miny - 110),
            (maxx + 90, miny + 60),
        ),
    )


def flourish(shape: BaseGeometry) -> list[NibStroke]:
    """swsh: Figueiredo's rasgo grows out of the capital, curling over its head
    on the left and running below the baseline before turning up on the right.

    Example: ``strokes = flourish(capital_ink)``.
    """
    minx, miny, maxx, maxy = shape.bounds
    return _flourish_head(minx, maxy) + [fine(_flourish_tail(minx, miny, maxx))]
