"""Opt-in three-letter spacing: SS11 moves ink while keeping fixed cells."""

import statistics

from shapely.geometry import LineString

from build_state import BuildState, ContextForm
from context_feature import append_context_lookups
from glyph_table import XH_NEW
from punct import outline
from spacing_guard import spacing_guard_rules
from spacing_lookups import guarded_spacing_lookups
from spacing_profiles import canonical_bodies, contour_profiles

CONTEXT_SHIFT = 40
CONTEXT_TAG = "ss11"


def _spacing_origins(state: BuildState) -> list[str]:
    encoded = {
        name for cp, name in state.font.getBestCmap().items() if chr(cp).isalpha()
    }
    defaults = set(state.placed) | set(state.compositions)
    return sorted(defaults & encoded)


def optical_spans(state: BuildState, names: list[str]) -> dict[str, float]:
    """Measure body spans, avoiding dot/shoulder bounding-box bias; e.g. ``optical_spans(state, ['r', 'n'])``."""
    glyphs = state.font.getGlyphSet()
    widths = {}
    for name in names:
        ink = outline(glyphs, name)
        slices = [
            ink.intersection(
                LineString([(-2000, XH_NEW * i / 20), (4000, XH_NEW * i / 20)])
            )
            for i in range(3, 18)
        ]
        spans = [
            section.bounds[2] - section.bounds[0]
            for section in slices
            if not section.is_empty
        ]
        widths[name] = statistics.mean(spans) if spans else 0.0
    return widths


def _ink_thresholds(state: BuildState, spans: dict[str, float]) -> tuple[float, float]:
    widths = sorted(
        spans[name] for name in "abcdefghijklmnopqrstuvwxyz" if name in state.placed
    )
    if not widths:
        raise ValueError(
            "No lowercase ink: expected letters for contextual width classes"
        )
    return widths[len(widths) // 3], widths[2 * len(widths) // 3]


def _spacing_alternates(state: BuildState, origins: list[str], shift: int) -> None:
    for name in origins:
        for suffix, distance in (("ctxL", -shift), ("ctxR", shift)):
            alternate = f"{name}.{suffix}"
            state.writer.add_shifted(alternate, name, distance)
            state.context_forms[alternate] = ContextForm(name, 1.0, distance)
    state.writer.commit_glyph_order()


def _spacing_class_code(origins: list[str], classes: list[list[str]]) -> list[str]:
    lines = [f"@CTX_ORIGIN = [{' '.join(origins)}];"]
    lines += [
        f"@CTX_{suffix} = [{' '.join(name + '.' + suffix for name in origins)}];"
        for suffix in ("ctxL", "ctxR")
    ]
    lines += [
        f"@CTX_WIDTH{index} = [{' '.join(names)}];"
        for index, names in enumerate(classes)
    ]
    return lines


def _spacing_rules() -> list[str]:
    return [
        f"sub @CTX_WIDTH{left} @CTX_ORIGIN' @CTX_WIDTH{right} by @CTX_{'ctxR' if left > right else 'ctxL'};"
        for left in range(3)
        for right in range(3)
        if left != right
    ]


def spacing_feature_code(origins: list[str], classes: list[list[str]]) -> str:
    """Use both neighbors; shifted forms remain eligible neighbors; e.g. ``spacing_feature_code(names, classes)``."""
    return "\n".join(
        _spacing_class_code(origins, classes)
        + [
            f"feature {CONTEXT_TAG} {{",
            "lookupflag IgnoreMarks;",
            *_spacing_rules(),
            f"}} {CONTEXT_TAG};",
        ]
    )


def add_context_spacing(state: BuildState, shift: int = CONTEXT_SHIFT) -> None:
    """Add a switchable SS11 spacing trial; e.g. ``add_context_spacing(state, 40)``."""
    if shift not in (20, 40, 60):
        raise ValueError(f"{shift}: expected contextual shift 20, 40 or 60 font units")
    origins = _spacing_origins(state)
    if not origins:
        return
    _spacing_alternates(state, origins, shift)
    _add_guarded_spacing(state, origins, shift)


def _add_guarded_spacing(state: BuildState, origins: list[str], shift: int) -> None:
    neighbors = sorted(set(origins) | set(state.context_forms))
    groups = canonical_bodies(state.font, neighbors)
    profiles = contour_profiles(state.font, list(groups))
    spans = optical_spans(state, list(groups))
    thresholds = _ink_thresholds(state, spans)
    classes = {
        name: sum(width > threshold for threshold in thresholds)
        for name, width in spans.items()
    }
    rules = spacing_guard_rules(state.font, origins, groups, profiles, classes, shift)
    if rules:
        lookups = guarded_spacing_lookups(state.font, origins, rules, True)
        append_context_lookups(state.font, CONTEXT_TAG, lookups, "Contextual spacing")
