"""The build audit protects inherited alternates and unrelated attachment records."""

import pytest

from build_state import BuildState
from conftest import reloaded, square, tiny_font
from stem_build_audit import _audit_mark_lookups, _audit_stem_anchors, stem_family_names
from test_context_accents import contextual_state


def test_stem_dependency_closure_excludes_inherited_character_variants() -> None:
    names = "t l one lslash t.ctxL lslash.ctxR l.alt lslash.alt one.alt one.numr lacute lacute.left".split()
    font = tiny_font({name: [square(100, 0, 400)] for name in names})
    for table in font["cmap"].tables:
        table.cmap[0x13A] = "lacute"
    allowed = stem_family_names(font)
    assert {
        "t",
        "l",
        "one",
        "lslash",
        "t.ctxL",
        "lslash.ctxR",
        "lacute",
        "lacute.left",
    } <= allowed
    assert not {"l.alt", "lslash.alt", "one.alt", "one.numr"} & allowed


def test_unrelated_base_anchor_changes_fail_the_family_audit(
    contextual_state: BuildState,
) -> None:
    original, changed = reloaded(contextual_state.font), reloaded(contextual_state.font)
    _audit_stem_anchors(original, changed, {"l"})
    subtable = changed["GPOS"].table.LookupList.Lookup[0].SubTable[0]
    record = subtable.BaseArray.BaseRecord[subtable.BaseCoverage.glyphs.index("i")]
    next(anchor for anchor in record.BaseAnchor if anchor).XCoordinate += 1
    with pytest.raises(ValueError, match="i: expected unchanged unrelated"):
        _audit_stem_anchors(original, changed, {"l"})


def test_mark_anchor_changes_fail_even_when_base_redrawing_is_allowed(
    contextual_state: BuildState,
) -> None:
    original, changed = reloaded(contextual_state.font), reloaded(contextual_state.font)
    _audit_mark_lookups(original, changed)
    subtable = changed["GPOS"].table.LookupList.Lookup[0].SubTable[0]
    subtable.MarkArray.MarkRecord[0].MarkAnchor.YCoordinate += 1
    with pytest.raises(ValueError, match="combining mark anchors"):
        _audit_mark_lookups(original, changed)
