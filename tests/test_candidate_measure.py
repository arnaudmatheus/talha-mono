"""Drawing comparisons isolate shaping changes while preserving columns and collision safety."""

from copy import deepcopy
from pathlib import Path

import uharfbuzz as hb

from candidate_measure import (
    CandidateCase,
    candidate_case,
    candidate_markdown,
    candidate_safety_errors,
)
from run_raster import RunRasterizer
from shaping_equivalence import shape_signature
from test_word_measure import word_fixture_path


def test_candidate_measurements_allow_design_changes_but_reject_column_drift(
    tmp_path: Path,
) -> None:
    raster = RunRasterizer(word_fixture_path(tmp_path))
    case: CandidateCase = candidate_case(raster, raster, "fixture", "iam", 15)
    assert candidate_safety_errors([case]) == []
    assert "fixture" in candidate_markdown([case]) and "PASS" in candidate_markdown(
        [case]
    )
    altered = deepcopy(case)
    altered["candidate_off"]["advance_px"] += 1
    assert "fixed advance changed" in candidate_safety_errors([altered])[0]
    altered = deepcopy(case)
    altered["candidate_on"]["overlap_pixels"] += 1
    assert "overlap increased" in candidate_safety_errors([altered])[0]


def test_equivalence_signature_tracks_features_and_positions(tmp_path: Path) -> None:
    font = hb.Font(hb.Face(word_fixture_path(tmp_path).read_bytes()))
    off = shape_signature(font, "iam", {"ss11": 0})
    on = shape_signature(font, "iam", {"ss11": 1})
    assert off != on and off[1][0] != on[1][0]
    assert sum(row[2] for row in off) == sum(row[2] for row in on)
    assert shape_signature(font, "fi", {"liga": 1}) != shape_signature(
        font, "fi", {"liga": 0}
    )
