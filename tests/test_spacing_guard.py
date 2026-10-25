"""Contour-based eligibility rejects asymmetric and already balanced contexts."""

import math

import numpy as np
import pytest
from fontTools.ttLib import TTFont

from conftest import reloaded, square, tiny_font
from context_feature import append_context_lookups
from spacing_guard import (
    GuardRule,
    NeighborGap,
    center_guard_rules,
    guarded_neighbors,
    neighbor_gaps,
    spacing_guard_rules,
)
from spacing_lookups import guarded_spacing_lookups
from spacing_profiles import canonical_bodies, contour_gap, contour_profiles
from test_context_spacing import feature_merge_font, spacing_shape


def accent_body_font() -> TTFont:
    names = "i a aacute a.left aacute.left a.ctxL aacute.ctxL".split()
    font = reloaded(tiny_font({name: [square(100, 0, 500)] for name in names}))
    for table in font["cmap"].tables:
        table.cmap[0xE1] = "aacute"
    return font


def test_accents_share_body_profiles_and_retain_contextual_placement() -> None:
    font = accent_body_font()
    groups = canonical_bodies(font, font.getGlyphOrder()[1:])
    assert set(groups["a"]) == {"a", "aacute"}
    assert set(groups["a.left"]) == {"a.left", "aacute.left"}
    assert set(groups["a.ctxL"]) == {"a.ctxL", "aacute.ctxL"}
    assert groups["i"] == ["i"]


def test_pair_contours_only_measure_shared_visible_rows() -> None:
    font = reloaded(
        tiny_font({"a": [square(100, 0, 500)], "b": [square(300, 1000, 300)]})
    )
    profiles = contour_profiles(font, ["a", "b"])
    assert contour_gap(profiles["a"], profiles["a"], 1160) == pytest.approx(660)
    assert math.isnan(contour_gap(profiles["a"], profiles["b"], 1160))
    assert np.isnan(profiles["a"].left).any()


def test_guard_uses_the_worst_gap_in_each_bucket() -> None:
    bucket = [NeighborGap(("a",), 2, 100, 0), NeighborGap(("b",), 2, 119, 0)]
    neighbors = [
        NeighborGap(("i",), 0, 0, 195),
        NeighborGap(("j",), 0, 0, 205),
        NeighborGap(("m",), 2, 0, 300),
        NeighborGap(("empty",), 0, 0, float("nan")),
    ]
    assert guarded_neighbors(bucket, neighbors, 1, 40) == ("j",)
    assert guarded_neighbors(bucket, neighbors, -1, 40) == ()


def test_wrong_direction_and_small_imbalances_do_not_activate() -> None:
    neighbors = [
        NeighborGap(("wide",), 2, 100, 195),
        NeighborGap(("narrow",), 0, 0, 170),
        NeighborGap(("empty",), 0, float("nan"), float("nan")),
    ]
    assert center_guard_rules(["a"], neighbors, 40) == []
    neighbors[1] = NeighborGap(("narrow",), 0, 0, 205)
    assert center_guard_rules(["a"], neighbors, 40) == [
        GuardRule(("a",), ("wide",), ("narrow",), 1)
    ]


def test_guard_rules_group_accents_and_use_actual_pair_contours() -> None:
    font = accent_body_font()
    groups = canonical_bodies(font, ["a", "aacute", "i"])
    profiles = contour_profiles(font, list(groups))
    classes = {"a": 2, "i": 0}
    neighbors = neighbor_gaps(groups, profiles, classes, "a", 1160)
    assert neighbors[0].names == ("a", "aacute")
    assert neighbors[0].before == pytest.approx(660)
    assert (
        spacing_guard_rules(font, ["a", "aacute"], groups, profiles, classes, 40) == []
    )


def test_direct_extension_lookups_shape_and_preserve_old_features() -> None:
    font = feature_merge_font()
    rules = [GuardRule(("a",), ("i",), ("m",), -1)]
    lookups = guarded_spacing_lookups(font, ["a"], rules)
    assert lookups[0].LookupType == 7 and lookups[0].LookupFlag == 8
    append_context_lookups(font, "ss11", lookups, "Contextual spacing")
    assert spacing_shape(font, "iam", True)[1][0] == "a.ctxL"
    assert spacing_shape(font, "iam", False)[1][0] == "a"
    assert spacing_shape(font, "mai", True)[1][0] == "a"
    assert spacing_shape(font, "fi", True)[0][0] == "f_i"
    assert spacing_shape(font, "aa", True)[1][0] == "a.alt"


def test_empty_guard_rules_are_rejected() -> None:
    with pytest.raises(ValueError, match="expected at least one contour guard"):
        guarded_spacing_lookups(feature_merge_font(), ["a"], [])


def test_overlapping_right_sets_compile_to_disjoint_classes() -> None:
    font = feature_merge_font()
    rules = [
        GuardRule(("a",), ("i",), ("m", "f"), -1),
        GuardRule(("a",), ("m",), ("i", "f"), 1),
    ]
    lookups = guarded_spacing_lookups(font, ["a"], rules)
    append_context_lookups(font, "ss11", lookups, "Contextual spacing")
    for text in ("iam", "iaf"):
        assert spacing_shape(font, text, True)[1][0] == "a.ctxL"
    for text in ("mai", "maf"):
        assert spacing_shape(font, text, True)[1][0] == "a.ctxR"
    for text in ("iai", "mam", "faf"):
        assert spacing_shape(font, text, True)[1][0] == "a"
