"""Contextual forms retain Talha recipes, fixed advances and mark attachment."""

import io
import math
from pathlib import Path

import pytest
import uharfbuzz as hb
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont

import pen
from accents import place_marks, place_precomposed
from build_options import parse_args
from build_state import BuildState
from conftest import reloaded, square, tiny_font
from glyph_table import glyph_table
from glyph_writer import GlyphWriter
from healing import heal_composites, heal_texture
from mark_positioning import position_marks, set_gdef_classes
from place_letters import place_letters

CONTEXT_NAMES = (
    "i dotlessi n m l i.loclTRK i.left dotlessi.left m.left i.right dotlessi.right "
    "m.right l.right j uni0237 j.left j.right j.both jcircumflex jcircumflex.left jcircumflex.right jcircumflex.both itilde itilde.left itilde.right iacute iacute.left "
    "uni1ECB uni1ECB.left acutecomb tildecomb dotbelowcomb"
).split()


CONTEXT_CODEPOINTS = {
    0x129: "itilde",
    0xED: "iacute",
    0x1ECB: "uni1ECB",
    0x135: "jcircumflex",
    0x237: "uni0237",
}
CONTEXT_CODEPOINTS.update(
    {0x301: "acutecomb", 0x303: "tildecomb", 0x323: "dotbelowcomb"}
)


def context_fixture_font() -> TTFont:
    font = tiny_font({n: [square(200, 0, 500)] for n in CONTEXT_NAMES})
    for table in font["cmap"].tables:
        table.cmap.update(CONTEXT_CODEPOINTS)
    addOpenTypeFeaturesFromString(
        font,
        """
        feature calt { sub m i' by i.right; sub m itilde' by itilde.right;
                       sub m l' by l.right; } calt;
        table GDEF { GlyphClassDef [i itilde l m n dotlessi], , , ; } GDEF;
    """,
    )
    return reloaded(font)


@pytest.fixture
def contextual_state(monkeypatch: pytest.MonkeyPatch) -> BuildState:
    monkeypatch.setattr(pen, "ADV", 1160)
    monkeypatch.setattr(pen, "SLANT", math.radians(7))
    monkeypatch.setattr(pen, "OPTICAL", 0)
    font = context_fixture_font()
    state = BuildState(
        parse_args(["in", "out"]),
        font,
        GlyphWriter(font, 1160),
        glyph_table(lambda name: name in font.getGlyphOrder()),
    )
    place_letters(state)
    heal_texture(state)
    place_precomposed(state)
    heal_composites(state)
    place_marks(state)
    position_marks(state)
    set_gdef_classes(state)
    return state


def context_shape(
    state: BuildState, text: str, enabled: bool, features: dict[str, int] | None = None
) -> list[tuple[str, int, int, int]]:
    stream = io.BytesIO()
    state.font.save(stream)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(
        hb.Font(hb.Face(stream.getvalue())),
        buffer,
        {"calt": enabled, **(features or {})},
    )
    return [
        (state.font.getGlyphName(g.codepoint), p.x_advance, p.x_offset, p.y_offset)
        for g, p in zip(buffer.glyph_infos, buffer.glyph_positions)
    ]


def test_accented_healing_forms_are_regenerated(contextual_state: BuildState) -> None:
    state = contextual_state
    for name in (
        "itilde.left",
        "itilde.right",
        "iacute.left",
        "uni1ECB.left",
        "jcircumflex.right",
    ):
        assert name in state.replaced and name in state.context_forms
        assert state.font["hmtx"][name][0] == 1160
        assert state.writer.bounds(name)[3] > 1000
    assert (
        state.context_forms["itilde.left"].scale
        == state.context_forms["dotlessi.left"].scale
    )
    assert (
        state.context_forms["uni1ECB.left"].scale == state.context_forms["i.left"].scale
    )


def test_stacked_marks_attach_after_substitution(contextual_state: BuildState) -> None:
    for enabled in (False, True):
        shaped = context_shape(contextual_state, "mi\u0303\u0301", enabled)
        assert shaped[1][0] == ("itilde.right" if enabled else "itilde")
        assert shaped[-1][0] == "acutecomb" and shaped[-1][1] == 0
        assert shaped[-1][2] < -500 and shaped[-1][3] > 0
        assert sum(row[1] for row in shaped) == 2320
    assert context_shape(contextual_state, "mĩ́", True) == context_shape(
        contextual_state, "mĩ́", True
    )


def test_below_marks_and_local_forms_have_base_coverage(
    contextual_state: BuildState,
) -> None:
    shaped = context_shape(contextual_state, "ml\u0323", True)
    assert shaped[1][0] == "l.right" and shaped[-1][2] < -500
    coverage = {
        name
        for lookup in contextual_state.font["GPOS"].table.LookupList.Lookup
        for table in lookup.SubTable
        if hasattr(table, "BaseCoverage")
        for name in table.BaseCoverage.glyphs
    }
    assert {"uni1ECB", "uni1ECB.left", "i.loclTRK"} <= coverage
    classes = contextual_state.font["GDEF"].table.GlyphClassDef.classDefs
    assert all(classes[name] == 1 for name in ("itilde.right", "i.loclTRK", "uni1ECB"))
    assert classes["acutecomb"] == 3


def test_contextual_coverage_gate_detects_missing_anchors_and_wrong_classes(
    contextual_state: BuildState,
) -> None:
    from context_check import check_context_coverage, expected_context_bases

    state = contextual_state
    assert "jcircumflex.right" in expected_context_bases(state.font)
    assert check_context_coverage(state.font) > 10
    classes = state.font["GDEF"].table.GlyphClassDef.classDefs
    classes["itilde.right"] = 4
    with pytest.raises(ValueError, match="expected GDEF base"):
        check_context_coverage(state.font)
    classes["itilde.right"] = 1
    remove_context_anchor(state.font, "itilde.right")
    with pytest.raises(ValueError, match="expected mark attachment"):
        check_context_coverage(state.font)


def test_nerd_copy_check_detects_changed_text_programs(
    contextual_state: BuildState, tmp_path: Path
) -> None:
    import shutil
    from fontTools.ttLib import TTFont
    from shapely.geometry import box
    from context_check import check_nf_text

    plain = tmp_path / "TalhaMono-Regular.otf"
    nerd = tmp_path / "TalhaMonoNF-Regular.otf"
    contextual_state.font.save(plain)
    shutil.copy2(plain, nerd)
    check_nf_text(nerd)
    with TTFont(nerd) as changed:
        GlyphWriter(changed, 1160).put("i", box(100, 0, 500, 600))
        changed.save(nerd)
    with pytest.raises(ValueError, match="byte-identical NF text"):
        check_nf_text(nerd)


def remove_context_anchor(font: TTFont, name: str) -> None:
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for table in lookup.SubTable:
            if hasattr(table, "BaseCoverage") and name in table.BaseCoverage.glyphs:
                table.BaseCoverage.glyphs.remove(name)
