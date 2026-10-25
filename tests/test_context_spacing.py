"""Three-letter alternates compose with existing GSUB and move marks with ink."""

import io

import pytest
import uharfbuzz as hb
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont

from conftest import reloaded, square, tiny_font
from context_feature import append_context_feature
from context_spacing import add_context_spacing, spacing_feature_code
from test_context_accents import contextual_state, context_shape
from mark_positioning import position_marks, set_gdef_classes
from build_state import BuildState


def spacing_shape(
    font: TTFont, text: str, enabled: bool, features: dict[str, int] | None = None
) -> list[tuple[str, int, int, int]]:
    stream = io.BytesIO()
    font.save(stream)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(
        hb.Font(hb.Face(stream.getvalue())),
        buf,
        {"ss11": enabled, "calt": True, **(features or {})},
    )
    return [
        (font.getGlyphName(g.codepoint), p.x_advance, p.x_offset, p.y_offset)
        for g, p in zip(buf.glyph_infos, buf.glyph_positions)
    ]


def feature_merge_font() -> TTFont:
    names = "i a m a.ctxL a.ctxR a.alt f f_i".split()
    font = reloaded(tiny_font({n: [square(100, 0, 500)] for n in names}))
    addOpenTypeFeaturesFromString(
        font,
        """
        languagesystem DFLT dflt; languagesystem latn dflt;
        feature liga { sub f i by f_i; } liga;
        feature calt { sub a a' by a.alt; } calt;
    """,
    )
    return font


def test_new_context_lookups_preserve_and_relocate_nested_substitutions() -> None:
    font = feature_merge_font()
    code = spacing_feature_code(["a"], [["i"], ["a"], ["m"]])
    append_context_feature(font, "ss11", code, "Contextual spacing")
    assert spacing_shape(font, "iam", False)[1][0] == "a"
    assert spacing_shape(font, "iam", True)[1][0] == "a.ctxL"
    assert spacing_shape(font, "mai", True)[1][0] == "a.ctxR"
    assert spacing_shape(font, "fi", True)[0][0] == "f_i"
    assert spacing_shape(font, "aa", True)[1][0] == "a.alt"
    record = next(
        r
        for r in font["GSUB"].table.FeatureList.FeatureRecord
        if r.FeatureTag == "ss11"
    )
    assert (
        font["name"].getDebugName(record.Feature.FeatureParams.UINameID)
        == "Contextual spacing"
    )
    with pytest.raises(ValueError, match="unused feature tag"):
        append_context_feature(font, "ss11", code, "duplicate")


def test_spacing_alternates_keep_cells_and_mark_anchors(
    contextual_state: BuildState,
) -> None:
    state = contextual_state
    before = spacing_shape(state.font, "nin", False)
    add_context_spacing(state, 40)
    position_marks(state)
    set_gdef_classes(state)
    assert spacing_shape(state.font, "nin", False) == before
    assert all(state.font["hmtx"][n][0] == 1160 for n in state.font.getGlyphOrder())
    for name, form in state.context_forms.items():
        if ".ctx" in name:
            assert form.scale == 1 and abs(form.shift) == 40
            original = state.writer.bounds(form.base)
            shifted = state.writer.bounds(name)
            assert shifted[0] == pytest.approx(original[0] + form.shift, abs=1)
    with pytest.raises(ValueError, match="expected contextual shift"):
        add_context_spacing(state, 0)


def test_nested_output_audit_reaches_new_contextual_glyphs() -> None:
    from gsub_features import feature_lookups, lookup_outputs

    font = feature_merge_font()
    code = spacing_feature_code(["a"], [["i"], ["a"], ["m"]])
    append_context_feature(font, "ss11", code, "Contextual spacing")
    indices = feature_lookups(font, lambda tag: tag == "ss11")
    assert lookup_outputs(font, indices) == {"a.ctxL", "a.ctxR"}


def test_optical_width_uses_body_instead_of_terminal_extent() -> None:
    from context_spacing import optical_spans
    from build_options import parse_args
    from glyph_writer import GlyphWriter

    glyphs = {
        "r": [
            square(100, 0, 200),
            [(100, 0), (300, 0), (300, 1080), (100, 1080)],
            [(100, 950), (900, 950), (900, 1080), (100, 1080)],
        ],
        "n": [[(100, 0), (900, 0), (900, 1080), (100, 1080)]],
    }
    font = reloaded(tiny_font(glyphs))
    state = BuildState(parse_args(["in", "out"]), font, GlyphWriter(font, 1160), {})
    widths = optical_spans(state, ["r", "n"])
    assert state.writer.bounds("r")[2] == state.writer.bounds("n")[2]
    assert widths["r"] < widths["n"] / 2


def test_strength_trials_move_marks_and_keep_glyph_ids(
    contextual_state: BuildState,
) -> None:
    from context_trials import change_spacing_strength
    from gsub_features import add_single_subst_feature

    state = contextual_state
    add_context_spacing(state)
    position_marks(state)
    set_gdef_classes(state)
    add_single_subst_feature(state.font, "ss12", {"itilde": "itilde.ctxL"})
    original_order = state.font.getGlyphOrder()[:]
    before = state.writer.bounds("itilde.ctxL")
    change_spacing_strength(state.font, 20)
    after = state.writer.bounds("itilde.ctxL")
    assert state.font.getGlyphOrder() == original_order
    assert after[0] == pytest.approx(before[0] + 20, abs=1)
    assert state.font["hmtx"]["itilde.ctxL"][0] == 1160
    assert "itilde.ctxL" in state.context_forms


def test_strength_trial_moves_the_combining_mark_with_its_base(
    contextual_state: BuildState,
) -> None:
    from context_trials import change_spacing_strength
    from gsub_features import add_single_subst_feature

    state = contextual_state
    add_context_spacing(state)
    position_marks(state)
    set_gdef_classes(state)
    add_single_subst_feature(state.font, "ss12", {"itilde": "itilde.ctxL"})
    before = context_shape(state, "ĩ́", True, {"ss12": 1})
    change_spacing_strength(state.font, 20)
    after = context_shape(state, "ĩ́", True, {"ss12": 1})
    assert before[0][0] == after[0][0] == "itilde.ctxL"
    assert after[-1][2] == before[-1][2] + 20
    assert after[-1][3] == before[-1][3] > 0
