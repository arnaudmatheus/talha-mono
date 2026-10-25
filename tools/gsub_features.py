"""Reading and extending Radon's GSUB: ligature lookups and new features."""

import re
from collections.abc import Callable

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import BaseTable
from ot_walk import tables_under

# Radon's stylistic sets that hold ligatures (ss01-ss10).
STYLISTIC_SET = re.compile(r"ss(0[1-9]|10)")
EXTENSION_LOOKUP = 7
NO_REQUIRED_FEATURE = 0xFFFF


def feature_lookups(font: TTFont, matches: Callable[[str], bool]) -> list[int]:
    """Lookup indices of every feature whose tag `matches` accepts."""
    records = font["GSUB"].table.FeatureList.FeatureRecord
    return [
        i
        for fr in records
        if matches(fr.FeatureTag)
        for i in fr.Feature.LookupListIndex
    ]


def liga_lookups(font: TTFont) -> list[int]:
    return feature_lookups(font, lambda tag: tag == "liga")


def stylistic_set_lookups(font: TTFont) -> list[int]:
    return feature_lookups(font, lambda tag: bool(STYLISTIC_SET.fullmatch(tag)))


def _subtable_outputs(subtable: BaseTable) -> set[str]:
    out: set[str] = set()
    for v in (getattr(subtable, "mapping", None) or {}).values():
        out.update(v if isinstance(v, (list, tuple)) else [v])
    for ligatures in (getattr(subtable, "ligatures", None) or {}).values():
        out.update(lig.LigGlyph for lig in ligatures)
    return out


def _nested_lookups(subtable: BaseTable) -> list[int]:
    return [
        table.LookupListIndex
        for table in tables_under([subtable])
        if isinstance(table, ot.SubstLookupRecord)
    ]


def _subtables(lookup: ot.Lookup) -> list[BaseTable]:
    """A lookup's subtables, unwrapped from extension lookups."""
    if lookup.LookupType == EXTENSION_LOOKUP:
        return [st.ExtSubTable for st in lookup.SubTable]
    return list(lookup.SubTable)


def lookup_outputs(font: TTFont, indices: list[int]) -> set[str]:
    """Every glyph these lookups (and the lookups they call) can produce."""
    lookups = font["GSUB"].table.LookupList.Lookup
    out, seen, todo = set(), set(), list(indices)
    while todo:
        i = todo.pop()
        if i in seen:
            continue
        seen.add(i)
        for st in _subtables(lookups[i]):
            out |= _subtable_outputs(st)
            todo += _nested_lookups(st)
    return out


def _all_langsys(gsub: ot.GSUB) -> list[ot.LangSys]:
    return [
        lang
        for sr in gsub.ScriptList.ScriptRecord
        for lang in [sr.Script.DefaultLangSys]
        + [r.LangSys for r in sr.Script.LangSysRecord]
        if lang
    ]


def _single_subst_lookup(mapping: dict[str, str]) -> ot.Lookup:
    lk = ot.Lookup()
    lk.LookupType, lk.LookupFlag = 1, 0
    st = ot.SingleSubst()
    st.mapping = dict(mapping)
    lk.SubTable, lk.SubTableCount = [st], 1
    return lk


def _feature_record(tag: str, lookup_index: int) -> ot.FeatureRecord:
    fr = ot.FeatureRecord()
    fr.FeatureTag = tag
    fr.Feature = ot.Feature()
    fr.Feature.FeatureParams = None
    fr.Feature.LookupListIndex = [lookup_index]
    fr.Feature.LookupCount = 1
    return fr


def _sort_features(gsub: ot.GSUB, langs: list[ot.LangSys]) -> None:
    """FeatureList stays sorted by tag (the OpenType spec asks for it)."""
    recs = gsub.FeatureList.FeatureRecord
    perm = sorted(range(len(recs)), key=lambda i: recs[i].FeatureTag)
    remap = {old: new for new, old in enumerate(perm)}
    gsub.FeatureList.FeatureRecord = [recs[i] for i in perm]
    gsub.FeatureList.FeatureCount = len(recs)
    for lang in langs:
        lang.FeatureIndex = sorted(remap[i] for i in lang.FeatureIndex)
        lang.FeatureCount = len(lang.FeatureIndex)
        if lang.ReqFeatureIndex != NO_REQUIRED_FEATURE:
            lang.ReqFeatureIndex = remap[lang.ReqFeatureIndex]


def add_single_subst_feature(font: TTFont, tag: str, mapping: dict[str, str]) -> None:
    """A single-substitution feature, registered for every script and
    language, off unless the application asks for it (titl, swsh).

    >>> add_single_subst_feature(font, "titl", {"A": "A.titl"})
    """
    gsub = font["GSUB"].table
    gsub.LookupList.Lookup.append(_single_subst_lookup(mapping))
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    recs = gsub.FeatureList.FeatureRecord
    recs.append(_feature_record(tag, len(gsub.LookupList.Lookup) - 1))
    langs = _all_langsys(gsub)
    for lang in langs:
        lang.FeatureIndex.append(len(recs) - 1)
    _sort_features(gsub, langs)


def merge_into_liga(font: TTFont, indices: list[int]) -> None:
    """Adds these lookups to the liga feature (ligatures on by default)."""
    for fr in font["GSUB"].table.FeatureList.FeatureRecord:
        if fr.FeatureTag == "liga":
            fr.Feature.LookupListIndex = sorted(
                set(fr.Feature.LookupListIndex) | set(indices)
            )
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
