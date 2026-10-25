"""The lowercase, drawn as broad-nib skeletons (cubic Béziers, upright).

Each function returns a letter's strokes as point lists; tools/pen.py sweeps
the nib along them. The Italic replaces some of these with the corsiva
(tools/corsiva.py); capitals and figures are in tools/caps.py.
"""

from pen import ellipse, path
from pen_types import PathCmd, Stroke, StrokesFn

# Skeleton vocabulary: stems at 330/905, x-height band 58..972
T, B = 972, 58


def strokes_a() -> list[Stroke]:
    # B3: a narrower bowl, a notch where it meets the stem, and a long exit;
    # at 12 px the 0.2.0 a was nearly an o (similarity 0.979).
    bowl = path(
        ("M", (880, 760)),
        ("C", (830, 920), (730, T), (640, T)),
        ("C", (470, T), (390, 760), (390, 520)),
        ("C", (390, 240), (470, B), (600, B)),
        ("C", (720, B), (840, 170), (905, 330)),
    )
    stem = path(
        ("M", (905, T)), ("L", (905, 170)), ("C", (905, 80), (960, 40), (1080, 100))
    )
    return [bowl, stem]


def strokes_e() -> list[Stroke]:
    return [
        path(
            ("M", (330, 470)),
            ("C", (560, 480), (820, 560), (880, 680)),
            ("C", (940, 820), (820, T), (630, T)),
            ("C", (430, T), (320, 760), (320, 520)),
            ("C", (320, 240), (440, B), (620, B)),
            ("C", (760, B), (860, 130), (925, 230)),
        )
    ]


def strokes_o() -> list[Stroke]:
    return [ellipse(615, 515, 325, 457)]


def strokes_n() -> list[Stroke]:
    entry = path(("M", (240, 885)), ("L", (330, T)), ("L", (330, 40)))
    arch = path(
        ("M", (330, 760)),
        ("C", (390, 930), (520, T), (650, T)),
        ("C", (810, T), (905, 880), (905, 700)),
        ("L", (905, 170)),
        ("C", (905, 90), (950, 55), (1030, 95)),
    )
    return [entry, arch]


def strokes_u() -> list[Stroke]:
    left = path(
        ("M", (240, 885)),
        ("L", (330, T)),
        ("L", (330, 300)),
        ("C", (330, 140), (430, B), (560, B)),
        ("C", (700, B), (830, 150), (905, 320)),
    )
    stem = path(
        ("M", (905, T)), ("L", (905, 170)), ("C", (905, 90), (950, 55), (1030, 95))
    )
    return [left, stem]


def strokes_y() -> list[Stroke]:
    left = path(
        ("M", (240, 885)),
        ("L", (330, T)),
        ("L", (330, 300)),
        ("C", (330, 140), (430, B), (560, B)),
        ("C", (700, B), (830, 150), (905, 320)),
    )
    stem = path(
        ("M", (905, T)),
        ("L", (905, -150)),
        ("C", (905, -290), (800, -368), (650, -368)),
        ("C", (520, -368), (420, -320), (360, -240)),
    )
    return [left, stem, BALLAT(358, -232)]


def strokes_g() -> list[Stroke]:
    # Inspired by (not copied from) Michelangelo's signature: the descender
    # loops and closes in one gesture, crossing back over the stem.
    bowl = path(
        ("M", (905, 880)),
        ("C", (840, 955), (720, T), (620, T)),
        ("C", (420, T), (320, 760), (320, 560)),
        ("C", (320, 300), (430, 160), (590, 160)),
        ("C", (730, 160), (850, 260), (905, 400)),
    )
    stem = path(
        ("M", (905, T)),
        ("L", (905, -120)),
        ("C", (905, -300), (780, -368), (620, -368)),
        ("C", (430, -368), (300, -300), (300, -200)),
        ("C", (300, -110), (430, -62), (600, -62)),
        ("C", (780, -62), (900, -100), (1010, -170)),
    )
    return [bowl, stem]


def strokes_f() -> list[Stroke]:
    # B3: a wide bar, a bigger top hook and a SHORT bottom hook: the j keeps
    # the big hook; at 12 px the two were nearly identical (0.887).
    hook = path(
        ("M", (1010, 1330)),
        ("C", (960, 1450), (850, 1482), (750, 1482)),
        ("C", (620, 1482), (560, 1400), (560, 1250)),
        ("L", (560, -170)),
        ("C", (560, -290), (510, -350), (430, -355)),
    )
    ball = BALLAT(1012, 1318)
    bar = path(("M", (280, T - 10)), ("L", (900, T - 10)))
    return [hook, bar, ball]


def strokes_dotlessi() -> list[Stroke]:
    # Balanced entry/exit expansion (beta.4): the old 400..760 skeleton left
    # holes in ti/li/ri/fi. Extending only the foot made i/l much more alike;
    # extending both ends to 320..840 keeps every measured pair within 0.01
    # across the roman weights and cells, and separates i/j more clearly.
    return [
        path(
            ("M", (320, 865)),
            ("L", (560, T)),
            ("L", (560, 170)),
            ("C", (560, 80), (630, 40), (840, 100)),
        )
    ]


def strokes_idot() -> list[Stroke]:
    return strokes_dotlessi() + [DOT()]


# Ascender/descender skeleton limits (outline lands ≈ at Radon's 1550 / −426).
A, D = 1482, -360


# The chancery lead-in.
def ENTRY(x: float, top: float) -> list[PathCmd]:
    return [("M", (x - 90, top - 85)), ("L", (x, top))]


# Ascender top after Figueiredo's calm hand (Nova Escola, plate nº 9): the
# stroke starts with a small hook curling right, then comes down as the stem.
# Used on b d h k. The Regular takes his forms but keeps the broad nib: his
# pressure quill, measured on the Regular, cost legibility at 12 px (five
# confusable pairs worse) and made it too close to the Italic — the quill is
# the Italic's signature.
def ASC(x: float) -> list[PathCmd]:
    return [
        ("M", (x + 215, A - 175)),
        ("C", (x + 250, A - 60), (x + 180, A + 25), (x + 95, A + 25)),
        ("C", (x + 30, A + 25), (x, A - 30), (x, A - 110)),
    ]


# Ball terminal — the signature of Baroque type (c. 1700–1760) and of the
# ball under Figueiredo's ascender curl: a short dab of the same pen.
def GOTA(x: float, y: float, r: float) -> Stroke:
    """The drop (gota): a small teardrop loop, point up and to the right along
    the pen angle. The same shape as the punctuation's drop (tools/punct.py);
    at these sizes the nib fills the loop by itself."""
    tip = (x + 0.75 * r, y + 1.15 * r)
    return path(
        ("M", tip),
        ("C", (x + 0.2 * r, y + 1.5 * r), (x - r, y + 0.7 * r), (x - r, y)),
        ("C", (x - r, y - 0.75 * r), (x - 0.4 * r, y - r), (x + 0.15 * r, y - r)),
        (
            "C",
            (x + 0.8 * r, y - r),
            (x + 1.05 * r, y - 0.35 * r),
            (x + 0.9 * r, y + 0.35 * r),
        ),
        ("C", (x + 0.85 * r, y + 0.75 * r), tip, tip),
    )


# The dots of i j and the diacritics stay a short diagonal dab. Tried as
# drops (r 35/45/55): every size made i/l and f/j worse (i/l +0.028 to
# +0.047), since a rounder, heavier dot fills the room above the stem that
# tells i from l. The ball terminals do take the drop: as drops they read
# a little better (i/j, f/j -0.005 to -0.008) and nothing got worse.
def DOT(x: float = 575, y: float = 1285) -> Stroke:
    return path(("M", (x - 18, y - 18)), ("L", (x + 18, y + 18)))


def BALLAT(x: float, y: float, r: float = 26) -> Stroke:
    return GOTA(x, y, r)


# The plate's ascender ends in a small ball under the curl; drawn as a dab.
def BALL(x: float) -> Stroke:
    return path(("M", (x + 196, A - 182)), ("L", (x + 230, A - 150)))


# The hairline exit flick.
def EXIT(x: float) -> list[PathCmd]:
    return [("L", (x, 170)), ("C", (x, 90), (x + 45, 55), (x + 125, 95))]


BOWL_R: list[PathCmd] = [
    ("C", (400, 880), (510, T), (640, T)),
    ("C", (820, T), (910, 800), (910, 520)),
    ("C", (910, 250), (780, B), (600, B)),
    ("C", (470, B), (380, 100), (330, 170)),
]
ARCH: list[PathCmd] = [
    ("C", (400, 900), (520, T), (640, T)),
    ("C", (800, T), (905, 880), (905, 700)),
]


def strokes_b() -> list[Stroke]:
    return [
        path(*ASC(330), ("L", (330, 70)), ("C", (330, 30), (290, 10), (230, 20))),
        BALL(330),
        path(("M", (330, 620)), *BOWL_R),
    ]


def strokes_c() -> list[Stroke]:
    return [
        BALLAT(892, 828, 18),
        path(
            ("M", (890, 836)),
            ("C", (840, 940), (740, T), (630, T)),
            ("C", (430, T), (320, 760), (320, 520)),
            ("C", (320, 240), (440, B), (620, B)),
            ("C", (760, B), (860, 130), (925, 230)),
        ),
    ]


def strokes_d() -> list[Stroke]:
    return [strokes_a()[0], path(*ASC(905), *EXIT(905)), BALL(905)]


def strokes_h() -> list[Stroke]:
    return [
        BALL(330),
        path(*ASC(330), ("L", (330, 40))),
        path(
            ("M", (330, 640)),
            *ARCH,
            ("L", (905, 170)),
            ("C", (905, 80), (960, 40), (1080, 100))
        ),
    ]


def strokes_dotlessj() -> list[Stroke]:
    return [
        path(
            ("M", (430, 880)),
            ("L", (560, T)),
            ("L", (560, -150)),
            ("C", (560, -300), (440, D), (330, D)),
            ("C", (240, D), (190, -310), (185, -250)),
        ),
        BALLAT(188, -240),
    ]


def strokes_j() -> list[Stroke]:
    return strokes_dotlessj() + [DOT()]


def strokes_k() -> list[Stroke]:
    stem = path(*ASC(330), ("L", (330, 40)))
    ball = BALL(330)
    loop = path(
        ("M", (330, 430)),
        ("C", (480, 650), (760, 990), (870, 885)),
        ("C", (950, 805), (830, 600), (470, 520)),
    )
    leg = path(
        ("M", (600, 545)),
        ("C", (720, 420), (790, 130), (880, 75)),
        ("C", (930, 45), (980, 60), (1030, 100)),
    )
    return [stem, ball, loop, leg]


def strokes_l() -> list[Stroke]:
    # B3: a long tail rising to the right; nothing else in the font has that
    # shape, so l stops looking like I, 1 or i at 12 px.
    # l keeps the chancery lead-in: with Figueiredo's hook at the top, l/I got
    # worse (0.903 → 0.919); the tail and the lead-in are what set it apart
    # from I.
    return [
        path(
            *ENTRY(560, A),
            ("L", (560, 260)),
            ("C", (560, 110), (630, 45), (730, 55)),
            ("C", (810, 65), (860, 120), (885, 190))
        )
    ]


def strokes_m() -> list[Stroke]:
    # Three stems in one cell, at 300/600/900 (they were 250/600/950): mm, mw,
    # ww were the tightest pairs in the font (6.5 px at 40 px against a 14
    # mean), and texture healing can't reach wide-beside-wide. Measured:
    # spacing variation 0.252 -> 0.232, no pair worse.
    first = path(*ENTRY(300, T), ("L", (300, 40)))
    arch1 = path(
        ("M", (300, 640)),
        ("C", (345, 890), (405, T), (465, T)),
        ("C", (562, T), (600, 880), (600, 700)),
        ("L", (600, 40)),
    )
    arch2 = path(
        ("M", (600, 640)),
        ("C", (645, 890), (705, T), (765, T)),
        ("C", (862, T), (900, 880), (900, 700)),
        *EXIT(900)
    )
    return [first, arch1, arch2]


def strokes_p() -> list[Stroke]:
    return [
        path(*ENTRY(330, T), ("L", (330, D - 10))),
        path(("M", (330, 620)), *BOWL_R),
    ]


def strokes_q() -> list[Stroke]:
    return [strokes_a()[0], path(("M", (905, T)), ("L", (905, D - 10)))]


def strokes_r() -> list[Stroke]:
    return [
        path(*ENTRY(330, T), ("L", (330, 40))),
        path(
            ("M", (330, 640)),
            ("C", (400, 880), (520, T), (650, T)),
            ("C", (740, T), (810, 945), (850, 895)),
        ),
        BALLAT(852, 888, 18),
    ]


def strokes_s() -> list[Stroke]:
    return [
        path(
            ("M", (860, 880)),
            ("C", (800, 950), (700, T), (610, T)),
            ("C", (470, T), (380, 900), (380, 780)),
            ("C", (380, 640), (520, 600), (620, 560)),
            ("C", (760, 505), (860, 430), (860, 280)),
            ("C", (860, 130), (740, B), (590, B)),
            ("C", (470, B), (370, 100), (310, 190)),
        )
    ]


def strokes_t() -> list[Stroke]:
    # B3: a short stem, a short exit; three distinct silhouettes: f (long
    # symmetric bar), l (no bar, long tail), t (bar, short tail).
    #
    # The bar crosses the stem (330-800 around the stem at 560), as in
    # JetBrains Mono and Iosevka, the fonts with the most distinct t/r of the
    # eleven measured. The 0.8.0 bar (430-880) was pulled right, so t and r
    # both had their weight right of a short stem; a reader found them hard
    # to tell apart (t/r 0.936 at 12 px, Radon 0.790). Beier & Larson (2010)
    # saw the same: their t without a crossing bar or tail was misread as r.
    # Measured on 1.0.0-beta.2 (Regular): t/r 0.936 -> 0.916 at 12 px,
    # 0.901 -> 0.849 at 20 px, paid for by t/1 (+0.104 at 20 px, from the
    # font's most distinct pair) and t/f (+0.02); accepted by the user, see
    # tools/gate_waivers.json. Taller necks, longer tails and a redrawn r
    # were measured too and helped less (ROADMAP, 1.0). The corsiva keeps
    # the 0.8.0 t (corsiva.c_t_pulled_right).
    return [
        path(("M", (560, 1180)), *EXIT(560)),
        path(("M", (330, T - 10)), ("L", (800, T - 10))),
    ]


def strokes_v() -> list[Stroke]:
    # A pointed vertex on the baseline: with a round bottom, v read as u at 12 px.
    return [
        path(
            *ENTRY(330, T),
            ("C", (360, 640), (470, 260), (600, 40)),
            ("C", (700, 260), (860, 560), (900, 800)),
            ("C", (910, 880), (890, 940), (850, 975))
        )
    ]


def strokes_w() -> list[Stroke]:
    # Narrower for the same reason as the m (wide-beside-wide pairs).
    left = path(
        *ENTRY(300, T),
        ("L", (300, 400)),
        ("C", (300, 190), (355, B), (435, B)),
        ("C", (528, B), (600, 180), (600, 420)),
        ("L", (600, 760))
    )
    right = path(
        ("M", (600, 420)),
        ("C", (600, 190), (672, B), (760, B)),
        ("C", (865, B), (930, 280), (930, 650)),
        ("C", (930, 820), (913, 900), (878, 960)),
    )
    return [left, right]


def strokes_x() -> list[Stroke]:
    return [
        path(
            ("M", (260, 880)),
            ("C", (330, 960), (430, T), (500, 860)),
            ("L", (760, 160)),
            ("C", (820, 70), (900, 50), (1000, 110)),
        ),
        path(("M", (950, 920)), ("L", (280, 60))),
    ]


def strokes_z() -> list[Stroke]:
    return [
        path(
            ("M", (300, 940)),
            ("C", (400, T), (800, 960), (900, 960)),
            ("L", (320, 70)),
            ("C", (500, 90), (800, 60), (930, 60)),
        )
    ]


LETTERS: dict[str, StrokesFn] = {
    "a": strokes_a,
    "b": strokes_b,
    "c": strokes_c,
    "d": strokes_d,
    "e": strokes_e,
    "f": strokes_f,
    "g": strokes_g,
    "h": strokes_h,
    "i": strokes_idot,
    "j": strokes_j,
    "k": strokes_k,
    "l": strokes_l,
    "m": strokes_m,
    "n": strokes_n,
    "o": strokes_o,
    "p": strokes_p,
    "q": strokes_q,
    "r": strokes_r,
    "s": strokes_s,
    "t": strokes_t,
    "u": strokes_u,
    "v": strokes_v,
    "w": strokes_w,
    "x": strokes_x,
    "y": strokes_y,
    "z": strokes_z,
    "dotlessi": strokes_dotlessi,
    "dotlessj": strokes_dotlessj,
}
