"""Spacing review distinguishes diagnostic tradeoffs from fixed-cell failures."""

import copy
from pathlib import Path

import pytest

from spacing_review import (
    SpacingCase,
    compare_spacing_case,
    spacing_deltas,
    spacing_review_markdown,
    spacing_safety_errors,
)
from context_feature import append_context_lookups
from run_raster import RunRasterizer
from spacing_guard import GuardRule
from spacing_lookups import guarded_spacing_lookups
from test_context_spacing import feature_merge_font


@pytest.fixture
def review_case() -> SpacingCase:
    return SpacingCase(
        face="Regular",
        corpus="review",
        text="leitura",
        size_px=15,
        baseline_off={"cv": 0.2, "advance_px": 40, "overlap_pixels": 0},
        baseline_on={"cv": 0.3, "advance_px": 40, "overlap_pixels": 0},
        candidate_on={"cv": 0.1, "advance_px": 40, "overlap_pixels": 0},
        default_pixels_equal=True,
    )


def test_review_distinguishes_optional_feature_tradeoffs(
    review_case: SpacingCase,
) -> None:
    assert spacing_safety_errors([review_case]) == []
    assert spacing_deltas([review_case], "baseline_on") == pytest.approx([-0.2])
    report = spacing_review_markdown([review_case])
    assert "review / Regular | 1 | 1 → 0 | 1 / 0 | -0.20000" in report
    assert "Safety checks: PASS (0 errors)" in report
    with pytest.raises(ValueError, match="expected baseline_off or baseline_on"):
        spacing_deltas([review_case], "candidate_off")


def test_review_gates_default_pixels_advance_and_overlap(
    review_case: SpacingCase,
) -> None:
    broken = copy.deepcopy(review_case)
    broken["default_pixels_equal"] = False
    broken["candidate_on"]["advance_px"] += 1
    broken["candidate_on"]["overlap_pixels"] += 1
    errors = spacing_safety_errors([broken])
    assert len(errors) == 3
    assert all("leitura" in error and "15 px" in error for error in errors)
    assert "Safety checks: FAIL (3 errors)" in spacing_review_markdown([broken])


def test_review_skips_undefined_cv_without_reporting_false_changes(
    review_case: SpacingCase,
) -> None:
    review_case["candidate_on"]["cv"] = None
    assert spacing_deltas([review_case], "baseline_on") == []
    assert "| n/a |" in spacing_review_markdown([review_case])
    assert spacing_safety_errors([review_case]) == []


def test_review_renders_real_shaped_runs_and_preserves_default_pixels(
    tmp_path: Path,
) -> None:
    font = feature_merge_font()
    source, candidate = tmp_path / "before.otf", tmp_path / "after.otf"
    font.save(source)
    rules = [GuardRule(("a",), ("i",), ("m",), -1)]
    lookups = guarded_spacing_lookups(font, ["a"], rules)
    append_context_lookups(font, "ss11", lookups, "Contextual spacing")
    font.save(candidate)
    case = compare_spacing_case(
        RunRasterizer(source), RunRasterizer(candidate), "Regular", "review", "iam", 15
    )
    assert case["default_pixels_equal"]
    assert case["baseline_off"]["advance_px"] == case["candidate_on"]["advance_px"]
    assert spacing_safety_errors([case]) == []


def test_cv_tolerance_boundary_is_stable_under_float_arithmetic(
    review_case: SpacingCase,
) -> None:
    review_case["baseline_on"]["cv"] = 0.2001
    review_case["candidate_on"]["cv"] = 0.2001
    assert spacing_deltas([review_case], "baseline_off") == [0.0001]
    assert "review / Regular | 1 | 0 → 0 | 0 / 0 |" in spacing_review_markdown(
        [review_case]
    )
