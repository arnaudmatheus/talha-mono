"""Append a compiled contextual feature without replacing upstream GSUB."""

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

from gsub_features import _all_langsys, _sort_features
from ot_walk import tables_under


def _relocate_context_lookups(lookups: list[ot.Lookup], offset: int) -> None:
    for table in tables_under(lookups):
        if isinstance(table, ot.SubstLookupRecord):
            table.LookupListIndex += offset


def _compiled_context(
    font: TTFont, feature: str, tag: str
) -> tuple[list[ot.Lookup], ot.FeatureRecord]:
    temporary = TTFont()
    temporary.setGlyphOrder(font.getGlyphOrder())
    addOpenTypeFeaturesFromString(temporary, feature, tables=["GSUB"])
    gsub = temporary["GSUB"].table
    records = [
        record for record in gsub.FeatureList.FeatureRecord if record.FeatureTag == tag
    ]
    if len(records) != 1:
        raise ValueError(f"{tag!r}: expected exactly one compiled contextual feature")
    return gsub.LookupList.Lookup, records[0]


def append_context_feature(font: TTFont, tag: str, feature: str, label: str) -> None:
    """Append isolated feature code, preserving old lookups; e.g. ``append_context_feature(f, 'ss11', code, 'Contextual spacing')``."""
    lookups, record = _compiled_context(font, feature, tag)
    append_context_lookups(font, tag, lookups, label, record)


def append_context_lookups(
    font: TTFont,
    tag: str,
    lookups: list[ot.Lookup],
    label: str,
    record: ot.FeatureRecord | None = None,
) -> None:
    """Append compiled lookups with feature-local indices; e.g. ``append_context_lookups(font, 'ss11', lookups, 'Contextual spacing')``."""
    gsub = font["GSUB"].table
    if any(record.FeatureTag == tag for record in gsub.FeatureList.FeatureRecord):
        raise ValueError(f"{tag!r}: expected an unused feature tag")
    _append_context_tables(font, lookups, record or _lookup_feature_record(tag), label)


def _append_context_tables(
    font: TTFont, lookups: list[ot.Lookup], record: ot.FeatureRecord, label: str
) -> None:
    gsub = font["GSUB"].table
    offset = len(gsub.LookupList.Lookup)
    _relocate_context_lookups(lookups, offset)
    record.Feature.LookupListIndex = [
        index + offset for index in record.Feature.LookupListIndex
    ]
    record.Feature.FeatureParams = _context_feature_parameters(font, label)
    gsub.LookupList.Lookup.extend(lookups)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    _register_context_feature(gsub, record)


def _lookup_feature_record(tag: str) -> ot.FeatureRecord:
    record = ot.FeatureRecord()
    record.FeatureTag = tag
    record.Feature = ot.Feature()
    record.Feature.LookupListIndex = [0]
    record.Feature.LookupCount = 1
    return record


def _context_feature_parameters(
    font: TTFont, label: str
) -> ot.FeatureParamsStylisticSet:
    parameters = ot.FeatureParamsStylisticSet()
    parameters.Version = 0
    parameters.UINameID = font["name"].addName(label, platforms=[(3, 1, 0x409)])
    return parameters


def _register_context_feature(gsub: ot.GSUB, record: ot.FeatureRecord) -> None:
    languages = _all_langsys(gsub)
    for language in languages:
        language.FeatureIndex.append(len(gsub.FeatureList.FeatureRecord))
    gsub.FeatureList.FeatureRecord.append(record)
    _sort_features(gsub, languages)
