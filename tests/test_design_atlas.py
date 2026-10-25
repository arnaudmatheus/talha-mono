"""Display exports must select real alternates and preserve the mono grid."""

from pathlib import Path
import xml.etree.ElementTree as ET

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
import pytest

import corsiva
import letters
import pen
from atlas_sources import placed_skeleton
from atlas_svg import OutlineFont, Sheet
from conftest import square, tiny_font


@pytest.fixture
def display_font(tmp_path: Path) -> OutlineFont:
    font = tiny_font({"A": [square(100, 0, 500)], "A.swsh": [square(-150, -100, 900)]})
    addOpenTypeFeaturesFromString(font, "feature swsh { sub A by A.swsh; } swsh;")
    path = tmp_path / "display.otf"
    font.save(path)
    return OutlineFont(path)


def test_display_alternate_preserves_the_advance_and_its_overhang(
    display_font: OutlineFont,
) -> None:
    assert display_font.name("A", "swsh") == "A.swsh"
    assert display_font.outline("A", "swsh") != display_font.outline("A")
    assert display_font.bounds("A", "swsh") == (-150, -100, 750, 800)
    assert display_font.width("AA", 100) == pytest.approx(116)


def test_unknown_feature_does_not_silently_export_a_plain_capital(
    display_font: OutlineFont,
) -> None:
    with pytest.raises(ValueError, match="'titl'.*existing display feature"):
        display_font.outline("A", "titl")


def test_missing_character_does_not_silently_export_notdef(
    display_font: OutlineFont,
) -> None:
    with pytest.raises(ValueError, match="'Z'.*character present"):
        display_font.outline("Z")
    with pytest.raises(ValueError, match="' '.+visible ink|character present"):
        display_font.bounds(" ")


def test_atlas_does_not_change_the_production_pen_or_letter_table() -> None:
    settings = (pen.SLANT, pen.ADV, pen.PEN, pen.OPTICAL)
    builders = dict(letters.LETTERS)
    upright = placed_skeleton(letters.strokes_h)
    italic = placed_skeleton(corsiva.c_h, italic=True)
    assert upright != italic
    assert all(len(stroke) > 1 for stroke in upright + italic)
    assert (pen.SLANT, pen.ADV, pen.PEN, pen.OPTICAL) == settings
    assert letters.LETTERS == builders


def test_export_keeps_alternate_paths_and_accessible_text(
    display_font: OutlineFont, tmp_path: Path
) -> None:
    sheet = Sheet("Initial & heading")
    sheet.text(display_font, "AA", 300, 400, 100, feature="swsh", center=True)
    path = tmp_path / "sheet.svg"
    sheet.save(path)
    root = ET.fromstring(path.read_text())
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns).text == "Initial & heading"
    run = root.find("svg:g", ns)
    assert run.attrib["aria-label"] == "AA"
    glyphs = run.findall("svg:path", ns)
    assert len(glyphs) == 2
    assert all(p.attrib["d"] == display_font.outline("A", "swsh") for p in glyphs)
    assert "translate(242.0,400)" in glyphs[0].attrib["transform"]
    assert "translate(300.0,400)" in glyphs[1].attrib["transform"]
