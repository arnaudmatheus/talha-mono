"""The importable font scripts preserve mappings, names and hint exclusions."""

import pytest
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import cmap_format_12

import finish
import nerd
import nohint
from conftest import reloaded, square, tiny_font


def icon_font() -> TTFont:
    font = tiny_font({"a": [square(0, 0, 100)], "icon": [square(0, 0, 200)]}, cell=1240)
    font["hmtx"]["icon"] = (1240, 31)
    for table in font["cmap"].tables:
        table.cmap[0xE001] = "a"
        table.cmap[0xE002] = "icon"
    wide = cmap_format_12(12)
    wide.platformID, wide.platEncID, wide.language = 3, 10, 0
    wide.cmap = {0xF0001: "icon"}
    font["cmap"].tables.append(wide)
    return reloaded(font)


def target_font() -> TTFont:
    font = tiny_font({"a": [square(0, 0, 80)]})
    font["CFF "].cff.topDictIndex[0].Private.defaultWidthX = 1160
    font["name"].setName("TestFont-Regular", 6, 3, 1, 0x409)
    return reloaded(font)


def test_icons_preserve_existing_letters_and_scale_only_horizontally() -> None:
    font = target_font()
    icons = icon_font()
    # Include all BMP mappings in the preferred UCS-4 cmap, as Nerd Fonts does.
    icons["cmap"].tables[-1].cmap.update({97: "a", 0xE001: "a", 0xE002: "icon"})
    before = font["CFF "].cff.topDictIndex[0].CharStrings["a"].bytecode
    added = nerd.add_icons(font, icons)
    assert font.getBestCmap()[97] == "a"
    assert font.getBestCmap()[0xE001] == "a.nf"
    assert set(added) == {"a.nf", "icon"}
    assert font.getBestCmap()[0xE002] == font.getBestCmap()[0xF0001] == "icon"
    assert font["hmtx"]["icon"] == (1160, round(31 * (1160 / 1240)))
    font["CFF "].cff.topDictIndex[0].CharStrings["a"].compile()
    assert font["CFF "].cff.topDictIndex[0].CharStrings["a"].bytecode == before
    assert font["name"].getDebugName(1) == "Test Font NF"
    assert font["CFF "].cff.fontNames == ["TestFontNF-Regular"]


def test_every_unicode_cmap_receives_icons_without_non_bmp_in_format4() -> None:
    font = target_font()
    extra = cmap_format_12(12)
    extra.platformID, extra.platEncID, extra.language = 0, 4, 0
    extra.cmap = {97: "a"}
    font["cmap"].tables.append(extra)
    nerd._replace_icon_cmaps(font, {"icon": [0xE001, 0xF0001]})
    full = [t for t in font["cmap"].tables if t.format == 12]
    assert {(t.platformID, t.platEncID) for t in full} == {(0, 4), (3, 10)}
    assert all(t.cmap[0xF0001] == "icon" for t in full)
    assert all(0xF0001 not in t.cmap for t in font["cmap"].tables if t.format == 4)


def test_hint_exclusions_do_not_leak_from_italic_to_regular() -> None:
    font = tiny_font(
        {
            name: []
            for name in ["i", "t", "f", "i.alt", "iacute", "iacute.alt", "bad name"]
        }
    )
    for table in font["cmap"].tables:
        table.cmap[0xED] = "iacute"
    font["post"].italicAngle = -13
    assert nohint.unhinted_glyphs(font) == [
        "f",
        "i",
        "i.alt",
        "iacute",
        "iacute.alt",
        "t",
    ]
    font["post"].italicAngle = 0
    assert nohint.unhinted_glyphs(font) == ["i", "i.alt", "iacute", "iacute.alt"]


@pytest.mark.parametrize(
    "weight, italic, label",
    [(400, False, "Regular"), (450, True, "Text"), (700, True, "Bold")],
)
def test_stat_names_only_its_own_axis_values(
    weight: int, italic: bool, label: str
) -> None:
    font = tiny_font({})
    finish.stat(font, weight, italic, label)
    table = font["STAT"].table
    assert [axis.AxisTag for axis in table.DesignAxisRecord.Axis] == ["wght", "ital"]
    values = table.AxisValueArray.AxisValue
    assert [value.Value for value in values] == [weight, int(italic)]
    assert font["name"].getDebugName(values[0].ValueNameID) == label
    assert getattr(values[0], "LinkedValue", None) == (700 if weight == 400 else None)


@pytest.mark.parametrize("source", ("cod-add", "1 bad/name", ".hidden", "", "x" * 90))
def test_icon_names_are_valid_bounded_and_unique(source: str) -> None:
    import re

    first = nerd._icon_glyph_name(source, set())
    second = nerd._icon_glyph_name(source, {first})
    third = nerd._icon_glyph_name(source, {first, second})
    for name in (first, second, third):
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,62}", name)
    assert len({first, second, third}) == 3


def test_icon_name_normalization_keeps_colliding_sources_and_aliases_distinct() -> None:
    icons = tiny_font(
        {"cod-add": [square(0, 0, 100)], "cod_add": [square(0, 0, 200)]}, 1240
    )
    for table in icons["cmap"].tables:
        table.cmap = {0xE001: "cod-add", 0xE002: "cod_add", 0xE003: "cod-add"}
    font = target_font()
    added = nerd.add_icons(font, reloaded(icons))
    assert added == {"cod_add": [0xE001, 0xE003], "cod_add.nf": [0xE002]}
    assert font.getBestCmap()[0xE001] == font.getBestCmap()[0xE003]
    strings = font["CFF "].cff.topDictIndex[0].CharStrings
    assert strings["cod_add"].program != strings["cod_add.nf"].program
