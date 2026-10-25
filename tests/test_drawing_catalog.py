"""Profile-local recipes propagate to dependencies without double height mapping."""

import pytest

import caps
import letters
from build_options import parse_args
from drawing_catalog import drawing_catalog
from glyph_table import glyph_table, vmap
from stem_recipes import adjust_stem_recipe
from stem_study import stem_skeleton


@pytest.mark.parametrize("italic", [False, True])
@pytest.mark.parametrize("name,strength", [("t", 20), ("l", 20), ("one", 10)])
def test_full_build_matches_the_screened_plain_glyph_recipe(
    italic: bool, name: str, strength: int
) -> None:
    catalog = glyph_table(lambda glyph: True, italic, True)
    assert catalog[name].strokes() == stem_skeleton(name, strength, italic)
    baseline = glyph_table(lambda glyph: True, italic, False)
    assert catalog[name].strokes() != baseline[name].strokes()


@pytest.mark.parametrize("italic", [False, True])
def test_crossed_l_inherits_the_refined_body_once(italic: bool) -> None:
    refined = glyph_table(lambda glyph: True, italic, True)
    assert refined["lslash"].strokes()[:-1] == refined["l"].strokes()
    raw = drawing_catalog(italic, True)
    expected = [
        [(x, vmap(y)) for x, y in stroke] for stroke in raw.extra_lower["lslash"]()
    ]
    assert refined["lslash"].strokes() == expected


def test_roman_italic_roman_catalogs_do_not_mutate_or_leak_style() -> None:
    original = dict(letters.LETTERS)
    first = drawing_catalog(False, False)
    italic = drawing_catalog(True, True)
    last = drawing_catalog(False, False)
    assert first.lower["l"]() == last.lower["l"]()
    assert first.lower["l"]() != italic.lower["l"]()
    assert italic.extra_lower["lslash"]()[:-1] == italic.lower["l"]()
    assert letters.LETTERS == original and caps.L is letters.LETTERS
    assert first.lower["l"]() == letters.strokes_l()


def test_stem_transform_does_not_mutate_shared_raw_strokes() -> None:
    source = letters.strokes_l()
    expected = [list(stroke) for stroke in source]
    adjusted = adjust_stem_recipe("l", source, 20)
    adjusted[0][0] = (0, 0)
    assert source == expected
    assert adjust_stem_recipe("l", source, 0) == source


@pytest.mark.parametrize("name,strength", [("t", 20), ("l", 20), ("one", 10)])
def test_default_catalog_draws_the_beta7_stems(name: str, strength: int) -> None:
    assert glyph_table(lambda glyph: True)[name].strokes() == stem_skeleton(
        name, strength, False
    )


def test_release_builds_use_the_ordinary_family_names() -> None:
    opts = parse_args(["in", "out", "--wide", "--text"])
    assert (opts.family, opts.ps_family, opts.cell) == (
        "Talha Mono Wide Text",
        "TalhaMonoWideText",
        1320,
    )
    with pytest.raises(SystemExit, match="--refined-stems"):
        parse_args(["in", "out", "--refined-stems"])
