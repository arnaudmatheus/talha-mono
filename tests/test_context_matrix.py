"""Feature-matrix coverage keeps healing independent of optional spacing."""

from pathlib import Path

from context_check import _check_mark_sample, context_feature_matrix
from context_spacing import add_context_spacing
from mark_positioning import position_marks, set_gdef_classes
from run_raster import RunRasterizer
from build_state import BuildState
from test_context_accents import contextual_state


def test_mark_and_code_matrices_include_all_independent_settings() -> None:
    marks, code = context_feature_matrix(), context_feature_matrix(code=True)
    assert len(marks) == 4 and len(code) == 8
    assert {(f["calt"], f["ss11"]) for f in marks} == {(0, 0), (1, 0), (0, 1), (1, 1)}
    assert {f["liga"] for f in marks} == {1}
    assert {(f["calt"], f["ss11"], f["liga"]) for f in code} == {
        (c, s, l) for c in (0, 1) for s in (0, 1) for l in (0, 1)
    }


def test_nfc_nfd_marks_attach_with_healing_and_spacing_independently(
    contextual_state: BuildState, tmp_path: Path
) -> None:
    state = contextual_state
    add_context_spacing(state)
    position_marks(state)
    set_gdef_classes(state)
    path = tmp_path / "matrix.otf"
    state.font.save(path)
    raster = RunRasterizer(path)
    for features in context_feature_matrix():
        _check_mark_sample(raster, "mĩ́", features)
