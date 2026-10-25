"""Reading and extending GSUB (tools/gsub_features.py)."""

import pytest
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

import gsub_features
from conftest import square, tiny_font

# Radon's shape in miniature: one ligature on by default, one behind ss01
# that calls a nested lookup, under two scripts.
FEATURES = """
languagesystem DFLT dflt;
languagesystem latn dflt;
lookup NESTED { sub b by b.alt; } NESTED;
feature liga { sub f i by f_i; } liga;
feature ss01 { sub a' lookup NESTED b; sub a by a.ss01; } ss01;
"""


@pytest.fixture
def font():
    names = ["a", "b", "f", "i", "a.ss01", "b.alt", "f_i", "A", "A.titl"]
    font = tiny_font({n: [square(100, 0, 400)] for n in names})
    addOpenTypeFeaturesFromString(font, FEATURES)
    return font


def test_lookup_outputs_follow_nested_lookups(font):
    sets = gsub_features.stylistic_set_lookups(font)
    assert gsub_features.lookup_outputs(font, sets) == {"a.ss01", "b.alt"}


def test_liga_outputs(font):
    liga = gsub_features.liga_lookups(font)
    assert gsub_features.lookup_outputs(font, liga) == {"f_i"}


def test_new_feature_is_registered_everywhere_and_sorted(font):
    gsub_features.add_single_subst_feature(font, "titl", {"A": "A.titl"})
    gsub = font["GSUB"].table
    tags = [fr.FeatureTag for fr in gsub.FeatureList.FeatureRecord]
    assert tags == sorted(tags) and "titl" in tags
    titl = tags.index("titl")
    for sr in gsub.ScriptList.ScriptRecord:
        assert titl in sr.Script.DefaultLangSys.FeatureIndex


def test_stylistic_sets_merge_into_liga(font):
    sets = gsub_features.stylistic_set_lookups(font)
    gsub_features.merge_into_liga(font, sets)
    liga = gsub_features.liga_lookups(font)
    assert set(sets) <= set(liga)
    assert gsub_features.lookup_outputs(font, liga) == {"f_i", "a.ss01", "b.alt"}


def test_class_based_context_records_are_followed_and_relocated_once() -> None:
    from fontTools.ttLib.tables import otTables as ot
    from context_feature import _relocate_context_lookups

    record = ot.SubstLookupRecord()
    record.LookupListIndex, record.SequenceIndex = 7, 0
    rule = ot.ChainSubClassRule()
    rule.SubstLookupRecord = [record]
    rules = ot.ChainSubClassSet()
    rules.ChainSubClassRule = [rule, rule]
    subtable = ot.ChainContextSubst()
    subtable.Format, subtable.ChainSubClassSet = 2, [rules]
    lookup = ot.Lookup()
    lookup.LookupType, lookup.LookupFlag, lookup.SubTable = 6, 0, [subtable]
    assert gsub_features._nested_lookups(subtable) == [7]
    _relocate_context_lookups([lookup], 5)
    assert record.LookupListIndex == 12
