"""Forward pruning retains shifted backtrack neighbors and rejects unsafe inputs."""

from pathlib import Path

import pytest
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

from context_feature import append_context_lookups
from spacing_guard import GuardRule
from spacing_lookups import guarded_spacing_lookups
from spacing_optimize import optimize_spacing_font
from spacing_prune import prune_forward_lookahead
from test_context_spacing import feature_merge_font, spacing_shape


def pruning_fixture() -> tuple[TTFont, list[ot.Lookup]]:
    font = feature_merge_font()
    rules = [
        GuardRule(("a",), ("i",), ("a",), -1),
        GuardRule(("a",), ("a.ctxL",), ("m",), 1),
        GuardRule(("a",), ("i",), ("a.ctxR",), 1),
    ]
    lookups = guarded_spacing_lookups(font, ["a"], rules)
    return font, lookups


def test_forward_pruning_keeps_already_shifted_left_neighbors() -> None:
    font, lookups = pruning_fixture()
    removed = prune_forward_lookahead(lookups[0], {"a.ctxL", "a.ctxR"})
    assert removed["rules"] == 1 and removed["lookahead_members"] == 1
    append_context_lookups(font, "ss11", lookups, "Contextual spacing")
    shaped = spacing_shape(font, "iaam", True, {"calt": 0})
    assert [row[0] for row in shaped] == ["i", "a.ctxL", "a.ctxR", "m"]
    assert sum(row[1] for row in shaped) == 4 * 1160


def test_pruning_rejects_reverse_lookups_and_preserves_source_files(
    tmp_path: Path,
) -> None:
    font, lookups = pruning_fixture()
    lookups[0].LookupFlag |= 1
    with pytest.raises(ValueError, match="expected forward"):
        prune_forward_lookahead(lookups[0], {"a.ctxL", "a.ctxR"})
    lookups[0].LookupFlag &= ~1
    append_context_lookups(font, "ss11", lookups, "Contextual spacing")
    source, target = tmp_path / "source.otf", tmp_path / "target.otf"
    font.save(source)
    original = source.read_bytes()
    result = optimize_spacing_font(source, target)
    assert result["removed"]["rules"] == 1 and source.read_bytes() == original
    with pytest.raises(ValueError, match="expected a separate output"):
        optimize_spacing_font(source, source)


def test_encoded_spacing_outputs_make_the_pruning_assumption_invalid(
    tmp_path: Path,
) -> None:
    font, lookups = pruning_fixture()
    append_context_lookups(font, "ss11", lookups, "Contextual spacing")
    for table in font["cmap"].tables:
        table.cmap[0xE000] = "a.ctxL"
    source = tmp_path / "encoded.otf"
    font.save(source)
    with pytest.raises(ValueError, match="expected unencoded glyphs"):
        optimize_spacing_font(source, tmp_path / "out.otf")
