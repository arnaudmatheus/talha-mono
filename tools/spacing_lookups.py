"""Compile contour guards directly into compact extension lookup subtables."""

from fontTools.otlLib.builder import (
    buildCoverage,
    buildLookup,
    buildSingleSubstSubtable,
)
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

from spacing_guard import GuardRule
from spacing_prune import prune_forward_lookahead


def _guard_record(direction: int) -> ot.SubstLookupRecord:
    record = ot.SubstLookupRecord()
    record.SequenceIndex = 0
    record.LookupListIndex = 1 if direction < 0 else 2
    return record


def _class_definition(groups: list[tuple[str, ...]]) -> ot.ClassDef:
    definition = ot.ClassDef()
    definition.classDefs = {
        name: index for index, group in enumerate(groups, 1) for name in group
    }
    return definition


def _after_partitions(rules: list[GuardRule]) -> dict[tuple[int, ...], tuple[str, ...]]:
    membership: dict[str, list[int]] = {}
    for index, rule in enumerate(rules):
        for name in rule.after:
            membership.setdefault(name, []).append(index)
    partitions: dict[tuple[int, ...], list[str]] = {}
    for name, indices in membership.items():
        partitions.setdefault(tuple(indices), []).append(name)
    return {indices: tuple(names) for indices, names in partitions.items()}


def _class_rule(before: int, after: int, direction: int) -> ot.ChainSubClassRule:
    rule = ot.ChainSubClassRule()
    rule.BacktrackGlyphCount = rule.InputGlyphCount = rule.LookAheadGlyphCount = 1
    rule.Backtrack = [before]
    rule.Input = []
    rule.LookAhead = [after]
    rule.SubstCount = 1
    rule.SubstLookupRecord = [_guard_record(direction)]
    return rule


def _guard_class_set(
    rules: list[GuardRule],
    before: list[tuple[str, ...]],
    partitions: dict[tuple[int, ...], tuple[str, ...]],
) -> ot.ChainSubClassSet:
    classes = {group: index for index, group in enumerate(before, 1)}
    class_set = ot.ChainSubClassSet()
    class_set.ChainSubClassRule = [
        _class_rule(classes[rules[index].before], after, rules[index].direction)
        for after, indices in enumerate(partitions, 1)
        for index in indices
    ]
    class_set.ChainSubClassRuleCount = len(class_set.ChainSubClassRule)
    return class_set


def _guard_subtable(
    rules: list[GuardRule], glyph_map: dict[str, int]
) -> ot.ChainContextSubst:
    before = list(dict.fromkeys(rule.before for rule in rules))
    partitions = _after_partitions(rules)
    subtable = ot.ChainContextSubst()
    subtable.Format = 2
    subtable.Coverage = buildCoverage(rules[0].origins, glyph_map)
    subtable.BacktrackClassDef = _class_definition(before)
    subtable.InputClassDef = _class_definition([rules[0].origins])
    subtable.LookAheadClassDef = _class_definition(list(partitions.values()))
    subtable.ChainSubClassSet = [None, _guard_class_set(rules, before, partitions)]
    subtable.ChainSubClassSetCount = 2
    return subtable


def guarded_spacing_lookups(
    font: TTFont,
    origins: list[str],
    rules: list[GuardRule],
    prune_lookahead: bool = False,
) -> list[ot.Lookup]:
    """Share substitutions and use 32-bit subtable offsets; e.g. ``guarded_spacing_lookups(font, names, rules)``."""
    lookups = [_grouped_spacing_lookup(font, rules)]
    if prune_lookahead:
        outputs = {f"{name}.{side}" for name in origins for side in ("ctxL", "ctxR")}
        prune_forward_lookahead(lookups[0], outputs)
    for side in ("ctxL", "ctxR"):
        mapping = {name: f"{name}.{side}" for name in origins}
        lookups.append(buildLookup([buildSingleSubstSubtable(mapping)], flags=8))
    return lookups


def _grouped_spacing_lookup(font: TTFont, rules: list[GuardRule]) -> ot.Lookup:
    if not rules:
        raise ValueError("0 spacing rules: expected at least one contour guard")
    centers: dict[tuple[str, ...], list[GuardRule]] = {}
    for rule in rules:
        centers.setdefault(rule.origins, []).append(rule)
    subtables = [
        _guard_subtable(group, font.getReverseGlyphMap()) for group in centers.values()
    ]
    return buildLookup(subtables, flags=8, table="GSUB", extension=True)
