"""Capitals, figures and the extra Latin letters, in the same pen as the lowercase.

Capitals follow Roman inscriptional structure (stems, bowls, true diagonals)
adapted to the mono cell and sloped by the same 7°. Instead of carved serifs,
left stems open with the same hairline lead-in as the lowercase: the pen's
serif. Figures are lining and tabular by construction: 1 carries a flag and a
foot, 0 a pen-stroke slash, so neither can be read as l / I / O."""

from collections.abc import Sequence

import letters
from letters import ENTRY, T, B, A, D, BOWL_R, ARCH
from pen import path, ellipse
from pen_types import PathCmd, Stroke, StrokesFn

CT, CB, FB = 1385, 58, 75  # cap top, round bottom, flat bottom (skeleton)
MID = 740


def stem(x: float, top: float = CT, bot: float = FB, entry: bool = True) -> Stroke:
    return (
        path(*ENTRY(x, top), ("L", (x, bot)))
        if entry
        else path(("M", (x, top)), ("L", (x, bot)))
    )


def bar(x0: float, x1: float, y: float) -> Stroke:
    return path(("M", (x0, y)), ("L", (x1, y)))


# Lapidary foot: the serif a stonecutter leaves at the base of a stem, as in
# the Latin capitals carved on Aleijadinho's Prophets (Congonhas, 1800–05).
def foot(x: float, w: float = 95) -> Stroke:
    return bar(x - w, x + w, FB)


# The ball terminal, the same drop as the lowercase's.
BALL = letters.BALLAT


def C_curve(end_cmds: Sequence[PathCmd] = ()) -> Stroke:
    return path(
        ("M", (930, 1180)),
        ("C", (880, 1330), (760, CT), (640, CT)),
        ("C", (420, CT), (310, 1100), (310, 720)),
        ("C", (310, 300), (430, CB), (650, CB)),
        *(end_cmds or [("C", (780, CB), (880, 120), (940, 260))])
    )


CAPS: dict[str, StrokesFn] = {
    "A": lambda: [
        path(("M", (300, FB)), ("L", (620, CT + 10)), ("L", (940, FB))),
        bar(420, 820, 500),
    ],
    "B": lambda: [
        stem(330),
        path(
            ("M", (330, CT)),
            ("L", (600, CT)),
            ("C", (790, CT), (860, 1300), (860, 1160)),
            ("C", (860, 1000), (770, MID), (600, MID)),
            ("L", (330, MID)),
        ),
        path(
            ("M", (330, MID)),
            ("L", (640, MID)),
            ("C", (840, MID), (920, 620), (920, 420)),
            ("C", (920, 190), (800, FB), (600, FB)),
            ("L", (330, FB)),
        ),
    ],
    "C": lambda: [C_curve(), BALL(932, 1170)],
    "D": lambda: [
        stem(330),
        path(
            ("M", (330, CT)),
            ("L", (560, CT)),
            ("C", (820, CT), (930, 1080), (930, 720)),
            ("C", (930, 320), (800, FB), (560, FB)),
            ("L", (330, FB)),
        ),
    ],
    "E": lambda: [stem(340), bar(340, 900, CT), bar(340, 800, MID), bar(340, 920, FB)],
    "F": lambda: [stem(340), bar(340, 900, CT), bar(340, 800, MID), foot(340)],
    "G": lambda: [
        BALL(932, 1170),
        C_curve([("C", (800, CB), (920, 150), (920, 320)), ("L", (920, 620))]),
        bar(680, 940, 620),
    ],
    "H": lambda: [stem(320), stem(920), bar(320, 920, MID), foot(320), foot(920)],
    # B3: wide bars (l/I).
    "I": lambda: [
        stem(620, entry=False),
        bar(370, 870, CT),
        bar(370, 870, FB),
    ],
    "J": lambda: [
        bar(480, 860, CT),
        path(
            ("M", (760, CT)),
            ("L", (760, 300)),
            ("C", (760, 120), (660, CB), (530, CB)),
            ("C", (420, CB), (340, 110), (300, 200)),
        ),
        BALL(300, 205),
    ],
    "K": lambda: [
        stem(330),
        path(("M", (900, CT)), ("L", (340, 600))),
        path(("M", (520, 790)), ("L", (950, FB))),
        foot(330),
    ],
    "L": lambda: [stem(340), bar(340, 920, FB)],
    "M": lambda: [
        path(
            ("M", (270, FB)),
            ("L", (270, CT)),
            ("L", (620, 400)),
            ("L", (970, CT)),
            ("L", (970, FB)),
        ),
        foot(270, 80),
        foot(970, 80),
    ],
    "N": lambda: [
        path(*ENTRY(330, CT), ("L", (330, FB))),
        path(("M", (330, CT)), ("L", (910, FB)), ("L", (910, CT))),
        foot(330, 80),
    ],
    "O": lambda: [ellipse(620, 720, 320, 662)],
    "P": lambda: [
        stem(330),
        path(
            ("M", (330, CT)),
            ("L", (600, CT)),
            ("C", (820, CT), (910, 1260), (910, 1060)),
            ("C", (910, 840), (800, 680), (600, 680)),
            ("L", (330, 680)),
        ),
        foot(330),
    ],
    "Q": lambda: [
        ellipse(620, 720, 320, 662),
        path(("M", (600, 260)), ("C", (700, 110), (820, -60), (980, -130))),
    ],
    "R": lambda: [
        stem(330),
        path(
            ("M", (330, CT)),
            ("L", (600, CT)),
            ("C", (820, CT), (910, 1260), (910, 1060)),
            ("C", (910, 840), (800, 680), (600, 680)),
            ("L", (330, 680)),
        ),
        path(("M", (600, 680)), ("C", (760, 640), (860, 300), (950, FB))),
        foot(330),
    ],
    "S": lambda: [
        path(
            ("M", (890, 1220)),
            ("C", (840, 1340), (740, CT), (620, CT)),
            ("C", (450, CT), (340, 1290), (340, 1110)),
            ("C", (340, 900), (520, 820), (660, 770)),
            ("C", (830, 710), (920, 600), (920, 420)),
            ("C", (920, 190), (780, CB), (600, CB)),
            ("C", (440, CB), (330, 120), (290, 250)),
        ),
        BALL(892, 1215),
        BALL(290, 255),
    ],
    # The T's bar fills nearly the whole cell, as in Radon: at 300–940 it left
    # a hole between two T's (TT had a 13.2 px gap at bar height against 7.8
    # for HH, at 40 px), and "TT" read as "T T".
    "T": lambda: [bar(200, 1040, CT), stem(620, entry=False), foot(620)],
    "U": lambda: [
        path(
            *ENTRY(320, CT),
            ("L", (320, 450)),
            ("C", (320, 180), (450, CB), (620, CB)),
            ("C", (790, CB), (920, 180), (920, 450)),
            ("L", (920, CT))
        )
    ],
    "V": lambda: [path(("M", (300, CT)), ("L", (620, CB - 10)), ("L", (940, CT)))],
    "W": lambda: [
        path(
            ("M", (250, CT)),
            ("L", (430, CB - 10)),
            ("L", (620, 900)),
            ("L", (810, CB - 10)),
            ("L", (990, CT)),
        )
    ],
    "X": lambda: [
        path(("M", (310, CT)), ("L", (930, FB))),
        path(("M", (930, CT)), ("L", (310, FB))),
    ],
    "Y": lambda: [
        path(("M", (300, CT)), ("L", (620, 700)), ("L", (940, CT))),
        path(("M", (620, 700)), ("L", (620, FB))),
    ],
    # Z wider for the same reason (ZZ 13.7 px against 9.8 in Radon).
    "Z": lambda: [
        path(("M", (270, CT)), ("L", (970, CT)), ("L", (270, FB)), ("L", (990, FB)))
    ],
}

FIGURES: dict[str, StrokesFn] = {
    "zero": lambda: [
        ellipse(620, 720, 290, 662),
        path(("M", (450, 330)), ("L", (790, 1110))),
    ],
    # B3: a longer flag (1/l). Longer again in 1.0.0-beta.2 (from (330, 1110)),
    # so 1 stays apart from the roman t's crossing bar: t/1 at 20 px +0.104
    # instead of +0.125, and 1/l 0.888 -> 0.816 at 20 px. The foot stays: a
    # footless 1 read as the new t (t/1 +0.19 at 20 px).
    "one": lambda: [
        path(("M", (250, 1010)), ("L", (640, CT)), ("L", (640, FB))),
        bar(430, 850, FB),
    ],
    "two": lambda: [
        path(
            ("M", (340, 1150)),
            ("C", (380, 1320), (500, CT), (630, CT)),
            ("C", (800, CT), (900, 1290), (900, 1120)),
            ("C", (900, 900), (700, 700), (340, FB)),
            ("L", (930, FB)),
        ),
        BALL(345, 1145),
    ],
    "three": lambda: [
        path(
            ("M", (350, 1250)),
            ("C", (420, 1350), (520, CT), (630, CT)),
            ("C", (790, CT), (880, 1290), (880, 1140)),
            ("C", (880, 960), (760, 780), (560, 780)),
            ("C", (800, 780), (910, 640), (910, 430)),
            ("C", (910, 200), (770, CB), (600, CB)),
            ("C", (450, CB), (350, 120), (300, 230)),
        ),
        BALL(352, 1245),
        BALL(300, 235),
    ],
    "four": lambda: [
        path(("M", (780, FB)), ("L", (780, CT)), ("L", (300, 450)), ("L", (950, 450)))
    ],
    "five": lambda: [
        path(
            ("M", (880, CT)),
            ("L", (420, CT)),
            ("L", (380, 820)),
            ("C", (450, 880), (560, 900), (640, 900)),
            ("C", (820, 900), (920, 740), (920, 500)),
            ("C", (920, 220), (780, CB), (590, CB)),
            ("C", (450, CB), (350, 110), (300, 230)),
        ),
        BALL(300, 235),
    ],
    "six": lambda: [
        BALL(862, 1295),
        path(
            ("M", (860, 1300)),
            ("C", (800, 1360), (720, CT), (640, CT)),
            ("C", (440, CT), (320, 1100), (320, 680)),
            ("C", (320, 250), (450, CB), (630, CB)),
            ("C", (810, CB), (920, 220), (920, 440)),
            ("C", (920, 680), (790, 830), (630, 830)),
            ("C", (470, 830), (360, 720), (330, 600)),
        ),
    ],
    "seven": lambda: [
        path(
            ("M", (320, CT)),
            ("L", (920, CT)),
            ("C", (760, 1000), (600, 500), (540, FB)),
        )
    ],
    "eight": lambda: [
        path(
            ("M", (620, 780)),
            ("C", (440, 780), (360, 920), (360, 1080)),
            ("C", (360, 1260), (480, CT), (620, CT)),
            ("C", (760, CT), (880, 1260), (880, 1080)),
            ("C", (880, 920), (800, 780), (620, 780)),
            ("C", (420, 780), (320, 620), (320, 420)),
            ("C", (320, 190), (450, CB), (620, CB)),
            ("C", (790, CB), (920, 190), (920, 420)),
            ("C", (920, 620), (820, 780), (620, 780)),
        )
    ],
    "nine": lambda: [
        BALL(378, 104),
        path(
            ("M", (380, 100)),
            ("C", (440, 40), (520, CB), (600, CB)),
            ("C", (800, CB), (920, 340), (920, 760)),
            ("C", (920, 1190), (790, CT), (610, CT)),
            ("C", (430, CT), (320, 1220), (320, 1000)),
            ("C", (320, 760), (450, 610), (610, 610)),
            ("C", (770, 610), (880, 720), (910, 840)),
        ),
    ],
}

L = letters.LETTERS


def crossed_lower(drawings: dict[str, StrokesFn]) -> dict[str, StrokesFn]:
    """Resolve crossed-letter bodies from the active style; e.g. ``crossed_lower(lower)['lslash']()``."""
    return {
        "lslash": lambda: drawings["l"]()
        + [path(("M", (400, 600)), ("L", (740, 860)))],
        "dcroat": lambda: drawings["d"]() + [bar(740, 1060, 1250)],
        "hbar": lambda: drawings["h"]() + [bar(190, 480, 1250)],
        "oslash": lambda: drawings["o"]() + [path(("M", (360, 60)), ("L", (880, 980)))],
    }


EXTRAS_LOWER: dict[str, StrokesFn] = {
    **crossed_lower(L),
    "kgreenlandic": lambda: [
        path(*ENTRY(330, T), ("L", (330, 40))),
        path(("M", (880, T)), ("L", (340, 480))),
        path(("M", (520, 600)), ("L", (930, 50))),
    ],
    "eng": lambda: [
        path(*ENTRY(330, T), ("L", (330, 40))),
        path(
            ("M", (330, 640)),
            *ARCH,
            ("L", (905, -150)),
            ("C", (905, -290), (800, D), (650, D))
        ),
    ],
    "thorn": lambda: [
        path(*ENTRY(330, A), ("L", (330, D - 10))),
        path(("M", (330, 620)), *BOWL_R),
    ],
    "eth": lambda: [
        ellipse(615, 470, 295, 412),
        path(("M", (440, 1440)), ("C", (700, 1300), (905, 1000), (905, 560))),
        bar(500, 840, 1260),
    ],
    "germandbls": lambda: [
        path(
            ("M", (330, 40)),
            ("L", (330, 1150)),
            ("C", (330, 1380), (450, A), (600, A)),
            ("C", (780, A), (880, 1380), (880, 1230)),
            ("C", (880, 1080), (740, 990), (640, 980)),
            ("C", (830, 950), (930, 800), (930, 520)),
            ("C", (930, 230), (790, B), (620, B)),
            ("C", (560, B), (510, 70), (480, 100)),
        )
    ],
    "ae": lambda: [
        path(
            ("M", (620, 880)),
            ("C", (560, 950), (470, T), (400, T)),
            ("C", (290, T), (240, 760), (240, 520)),
            ("C", (240, 240), (300, B), (400, B)),
            ("C", (500, B), (580, 150), (620, 330)),
        ),
        path(("M", (620, T)), ("L", (620, 300))),
        path(
            ("M", (620, 470)),
            ("C", (760, 480), (930, 560), (960, 680)),
            ("C", (990, 820), (900, T), (790, T)),
            ("C", (680, T), (620, 800), (620, 600)),
            ("C", (620, 240), (700, B), (820, B)),
            ("C", (900, B), (960, 100), (1000, 180)),
        ),
    ],
    "oe": lambda: [
        ellipse(430, 515, 190, 457),
        path(
            ("M", (620, 470)),
            ("C", (760, 480), (930, 560), (960, 680)),
            ("C", (990, 820), (900, T), (790, T)),
            ("C", (680, T), (620, 800), (620, 600)),
            ("C", (620, 240), (700, B), (820, B)),
            ("C", (900, B), (960, 100), (1000, 180)),
        ),
    ],
}

EXTRAS_UPPER: dict[str, StrokesFn] = {
    "Lslash": lambda: CAPS["L"]() + [path(("M", (200, 560)), ("L", (560, 860)))],
    "Dcroat": lambda: CAPS["D"]() + [bar(200, 520, MID)],
    "Eth": lambda: CAPS["D"]() + [bar(200, 520, MID)],
    "Hbar": lambda: CAPS["H"]() + [bar(200, 1040, 1150)],
    "Oslash": lambda: CAPS["O"]() + [path(("M", (330, 80)), ("L", (910, 1360)))],
    "Eng": lambda: [
        path(*ENTRY(330, CT), ("L", (330, FB))),
        path(
            ("M", (330, CT)),
            ("L", (910, 400)),
            ("L", (910, -120)),
            ("C", (910, -260), (800, -330), (660, -330)),
        ),
    ],
    "Thorn": lambda: [
        stem(330),
        path(
            ("M", (330, 1150)),
            ("L", (600, 1150)),
            ("C", (820, 1150), (910, 1030), (910, 830)),
            ("C", (910, 610), (800, 450), (600, 450)),
            ("L", (330, 450)),
        ),
    ],
    "AE": lambda: [
        path(("M", (240, FB)), ("L", (620, CT))),
        bar(620, 960, CT),
        path(("M", (620, CT)), ("L", (620, FB))),
        bar(620, 900, MID),
        bar(620, 980, FB),
        bar(400, 620, 520),
    ],
    "OE": lambda: [
        path(
            ("M", (640, CT)),
            ("L", (520, CT)),
            ("C", (350, CT), (240, 1100), (240, 720)),
            ("C", (240, 330), (350, FB), (520, FB)),
            ("L", (640, FB)),
        ),
        path(("M", (640, CT)), ("L", (640, FB))),
        bar(640, 980, CT),
        bar(640, 920, MID),
        bar(640, 1000, FB),
    ],
}
