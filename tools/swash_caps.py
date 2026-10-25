"""Letter-specific display swashes after Figueiredo's plate nº 7.

The three studies keep the capital's structure and attach a fine rasgo at a
real stroke junction: A's crossbar, P's stem, R's leg. Coordinates are upright;
the skeleton is slanted before the fixed nib is swept, as in the normal build.
"""

import math
from collections.abc import Sequence

from shapely.geometry import box
from shapely.geometry.base import BaseGeometry

import caps
import ornament
import pen
from ornament import NibStroke, fine
from pen_types import Stroke

PILOT_CAPITALS = ("A", "P", "R")
SWASH_VARIANTS = (1, 2, 3)
SELECTED_SWASH = {"A": 2, "P": 2, "R": 2}


def a_crossbar(variant: int) -> list[NibStroke]:
    if variant == 1:
        entry = pen.path(("M", (160, 420)), ("C", (240, 540), (320, 500), (420, 500)))
        return [fine(entry), caps.bar(420, 820, 500)]
    loop = pen.path(
        ("M", (180, 830)),
        ("C", (200, 1080), (-190, 1120), (-260, 850)),
        ("C", (-340, 540), (40, 500), (420, 500)),
    )
    return [fine(loop), caps.bar(420, 820, 500)]


def a_exit(variant: int) -> list[NibStroke]:
    if variant < 3:
        return []
    sweep = pen.path(
        ("M", (940, 75)),
        ("C", (1110, -100), (1110, -270), (750, -270)),
        ("C", (340, -270), (10, -220), (-130, -100)),
    )
    return [fine(sweep)]


def a_swash(variant: int) -> list[NibStroke]:
    main = caps.CAPS["A"]()[0]
    return [main] + a_crossbar(variant) + a_exit(variant)


def bowl_entry(variant: int) -> list[NibStroke]:
    reach = (90, 260, 380)[variant - 1]
    entry = pen.path(
        ("M", (100 - reach, 1160)),
        ("C", (-reach, 1430), (80, 1570), (330, caps.CT)),
    )
    return [fine(entry)]


def p_bowl() -> Stroke:
    # The ordinary P and R share this bowl. Keep their counter dimensions.
    return caps.CAPS["P"]()[1]


def p_descent(variant: int) -> list[NibStroke]:
    if variant == 1:
        tail = pen.path(("M", (330, 120)), ("C", (330, -60), (210, -120), (80, -80)))
    else:
        reach = 300 if variant == 2 else 530
        tail = pen.path(
            ("M", (330, 120)),
            ("C", (330, -150), (20, -330), (-reach, -210)),
            ("C", (-reach - 160, -130), (-reach - 100, 120), (-reach + 60, 120)),
        )
    return [fine(tail)]


def p_swash(variant: int) -> list[NibStroke]:
    stem = caps.stem(330, entry=False)
    return [stem, p_bowl()] + bowl_entry(variant) + p_descent(variant)


def r_leg(variant: int) -> list[NibStroke]:
    leg = caps.CAPS["R"]()[2]
    if variant == 1:
        exit = pen.path(
            ("M", (950, caps.FB)), ("C", (1000, -10), (1080, -30), (1170, 30))
        )
    else:
        reach = 1400 if variant == 2 else 1650
        exit = pen.path(
            ("M", (950, caps.FB)),
            ("C", (1040, -100), (reach, -300), (reach + 50, -80)),
            ("C", (reach + 70, 30), (reach - 60, 40), (reach - 80, -40)),
        )
    return [leg, fine(exit)]


def r_swash(variant: int) -> list[NibStroke]:
    return (
        [caps.stem(330, entry=False), p_bowl(), caps.foot(330)]
        + bowl_entry(variant)
        + r_leg(variant)
    )


def swash_strokes(capital: str, variant: int | None = None) -> list[NibStroke]:
    """Upright strokes for a display capital; e.g. ``swash_strokes('P', 2)``."""
    if capital not in PILOT_CAPITALS:
        raise ValueError(f"{capital!r}: expected one of {PILOT_CAPITALS}")
    chosen = SELECTED_SWASH[capital] if variant is None else variant
    if chosen not in SWASH_VARIANTS:
        raise ValueError(f"{chosen!r}: expected a swash variant in {SWASH_VARIANTS}")
    builders = {"A": a_swash, "P": p_swash, "R": r_swash}
    return builders[capital](chosen)


def lean_strokes(
    strokes: Sequence[NibStroke], degrees: float, dx: float
) -> list[NibStroke]:
    """Slant skeletons before sweeping the nib; e.g. ``lean_strokes(strokes, 7, -20)``."""
    shear = math.tan(math.radians(degrees))
    result: list[NibStroke] = []
    for stroke in strokes:
        points, weight = stroke if isinstance(stroke, tuple) else (stroke, 1.0)
        shifted = [(x + y * shear + dx, y) for x, y in points]
        result.append((shifted, weight))
    return result


def swash_shape(
    capital: str,
    nib: tuple[float, float],
    degrees: float,
    dx: float,
    variant: int | None = None,
) -> BaseGeometry:
    """Production swash, including the letter; e.g. ``swash_shape('A', (138, 106), 7, 0)``."""
    strokes = lean_strokes(swash_strokes(capital, variant), degrees, dx)
    return ornament.render(strokes, [], *nib)


def capital_offset(
    capital: str, nib: tuple[float, float], degrees: float, cell: int
) -> float:
    """Use the ordinary capital's centring; e.g. ``capital_offset('A', (138, 106), 7, 1160)``."""
    strokes = lean_strokes(caps.CAPS[capital](), degrees, 0)
    ink = ornament.render(strokes, [], *nib)
    band = ink.intersection(box(-2000, 0, 4000, 1460))
    left, _, right, _ = band.bounds
    return cell / 2 - (left + right) / 2
