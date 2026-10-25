"""Remove impossible future SS11 outputs from a forward, single-input lookup."""

from fontTools.ttLib.tables import otTables as ot


def prune_forward_lookahead(lookup: ot.Lookup, outputs: set[str]) -> dict[str, int]:
    """Keep shifted left neighbors, prune shifted right neighbors; e.g. ``prune_forward_lookahead(lookup, outputs)``."""
    if lookup.LookupFlag & 1 or lookup.LookupType not in (6, 7):
        raise ValueError("Spacing lookup: expected forward chained substitution")
    removed = {"rules": 0, "lookahead_members": 0}
    for wrapped in lookup.SubTable:
        subtable = getattr(wrapped, "ExtSubTable", wrapped)
        _require_forward_classes(subtable)
        before = subtable.LookAheadClassDef.classDefs
        live = {name: cls for name, cls in before.items() if name not in outputs}
        subtable.LookAheadClassDef.classDefs = live
        removed["lookahead_members"] += len(before) - len(live)
        removed["rules"] += _prune_dead_classes(subtable, set(live.values()))
    return removed


def _require_forward_classes(subtable: ot.ChainContextSubst) -> None:
    if subtable.Format != 2:
        raise ValueError(f"{subtable.Format}: expected SS11 class-based format 2")
    for group in subtable.ChainSubClassSet:
        if group is None:
            continue
        for rule in group.ChainSubClassRule:
            counts = (
                rule.BacktrackGlyphCount,
                rule.InputGlyphCount,
                rule.LookAheadGlyphCount,
            )
            if counts != (1, 1, 1) or rule.SubstCount != 1:
                raise ValueError(
                    f"{counts}: expected one backtrack/input/lookahead and one substitution"
                )
            if rule.LookAhead[0] == 0 or rule.SubstLookupRecord[0].SequenceIndex != 0:
                raise ValueError(
                    "Spacing rule: expected explicit lookahead class and substitution at input zero"
                )


def _prune_dead_classes(subtable: ot.ChainContextSubst, live: set[int]) -> int:
    removed = 0
    for group in subtable.ChainSubClassSet:
        if group is None:
            continue
        before = group.ChainSubClassRule
        group.ChainSubClassRule = [rule for rule in before if rule.LookAhead[0] in live]
        group.ChainSubClassRuleCount = len(group.ChainSubClassRule)
        removed += len(before) - group.ChainSubClassRuleCount
    return removed
