"""Audit complete stem candidates against beta.6 and the screened plain study."""

import argparse
import json
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otBase import BaseTable

from font_preservation import cff_hint_signature, layout_signature
from gsub_features import feature_lookups
from identical import head_without_timestamps
from marks import MARKS
from pilot_validation import changed_charstrings
from stem_recipes import STEM_NAMES

ALLOWED_TABLES = {"CFF ", "hmtx", "head", "name", "GPOS", "GSUB"}
STEM_SUFFIXES = {"left", "right", "both", "ctxL", "ctxR"}
AnchorMap = dict[str, list[tuple[int, int, int]]]


def stem_family_names(font: TTFont) -> set[str]:
    """Enumerate supported recipes and their rebuilt variants; e.g. ``stem_family_names(font)``."""
    roots = {"t", "l", "one", "lslash"}
    for cp, name in font.getBestCmap().items():
        sequence = unicodedata.normalize("NFD", chr(cp))
        if sequence[0] in "tl" and all(ord(mark) in MARKS for mark in sequence[1:]):
            roots.add(name)
    return {
        name
        for name in font.getGlyphOrder()
        if name in roots
        or (
            name.rsplit(".", 1)[0] in roots and name.rsplit(".", 1)[-1] in STEM_SUFFIXES
        )
    }


def _audit_stem_metrics(before: TTFont, after: TTFont, allowed: set[str]) -> None:
    if (
        before.getGlyphOrder() != after.getGlyphOrder()
        or before.getBestCmap() != after.getBestCmap()
    ):
        raise ValueError(
            "Stem candidate: expected identical glyph IDs and Unicode mappings"
        )
    for name, (advance, lsb) in before["hmtx"].metrics.items():
        expected = (advance, after["hmtx"][name][1] if name in allowed else lsb)
        if after["hmtx"][name] != expected:
            raise ValueError(
                f"{name}: expected fixed advance and unaffected sidebearing"
            )
    original, updated = head_without_timestamps(before), head_without_timestamps(after)
    original.pop("fontRevision")
    updated.pop("fontRevision")
    if original != updated:
        raise ValueError("Stem candidate: expected unchanged head metrics")


def _audit_stem_tables(before: TTFont, after: TTFont) -> None:
    if set(before.reader.keys()) != set(after.reader.keys()):
        raise ValueError("Stem candidate: expected identical sfnt table coverage")
    for tag in before.reader.keys():
        if tag not in ALLOWED_TABLES and before.reader[tag] != after.reader[tag]:
            raise ValueError(f"{tag}: expected unchanged non-design table")
    if cff_hint_signature(before) != cff_hint_signature(after):
        raise ValueError("Stem candidate: expected unchanged shared CFF hint resources")


def _audit_stem_substitutions(before: TTFont, after: TTFont) -> None:
    roots = feature_lookups(before, lambda tag: tag == "ss11")
    if len(roots) != 1 or roots != feature_lookups(after, lambda tag: tag == "ss11"):
        raise ValueError("Stem candidate: expected one stable SS11 entry index")
    old, new = before["GSUB"].table, after["GSUB"].table
    for key in ("FeatureList", "ScriptList"):
        if layout_signature(getattr(old, key), before) != layout_signature(
            getattr(new, key), after
        ):
            raise ValueError(f"{key}: expected unchanged feature/language registration")
    if len(old.LookupList.Lookup) != len(new.LookupList.Lookup):
        raise ValueError("Stem candidate: expected stable lookup count")
    for index, (original, updated) in enumerate(
        zip(old.LookupList.Lookup, new.LookupList.Lookup)
    ):
        if index not in roots and layout_signature(
            original, before
        ) != layout_signature(updated, after):
            raise ValueError(f"GSUB {index}: expected unchanged non-SS11 lookup")


def base_anchor_map(font: TTFont) -> AnchorMap:
    """Read actual base records rather than table offsets; e.g. ``base_anchor_map(font)``."""
    anchors: AnchorMap = {}
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for wrapped in lookup.SubTable:
            subtable = getattr(wrapped, "ExtSubTable", wrapped)
            if not hasattr(subtable, "BaseCoverage"):
                continue
            for name, record in zip(
                subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord
            ):
                anchors[name] = [
                    (index, anchor.XCoordinate, anchor.YCoordinate)
                    for index, anchor in enumerate(record.BaseAnchor)
                    if anchor
                ]
    return anchors


def _audit_stem_anchors(before: TTFont, after: TTFont, allowed: set[str]) -> None:
    original, updated = base_anchor_map(before), base_anchor_map(after)
    if set(original) != set(updated):
        raise ValueError("Stem candidate: expected unchanged base attachment coverage")
    for name in original:
        if name not in allowed and original[name] != updated[name]:
            raise ValueError(f"{name}: expected unchanged unrelated attachment anchors")


def audit_stem_build(
    source: Path, target: Path, study: Path | None = None
) -> dict[str, object]:
    """Enforce the declared dependency closure in a complete build; e.g. ``audit_stem_build(old, new)``."""
    with TTFont(source) as before, TTFont(target) as after:
        allowed, changed = _stem_program_changes(before, after)
        _audit_stem_metrics(before, after, allowed)
        _audit_stem_tables(before, after)
        _audit_stem_substitutions(before, after)
        _audit_stem_anchors(before, after, allowed)
        _audit_mark_lookups(before, after)
        if study:
            _audit_screened_glyphs(after, study)
    return {
        "face": target.name,
        "changed_programs": sorted(changed),
        "allowed_family_size": len(allowed),
        "result": "PASS",
    }


def _stem_program_changes(before: TTFont, after: TTFont) -> tuple[set[str], set[str]]:
    allowed, changed = stem_family_names(before), changed_charstrings(before, after)
    required = set(STEM_NAMES) | {"lslash"}
    if not changed <= allowed or not required <= changed:
        raise ValueError(
            f"{sorted(changed - allowed)}: expected only the complete stem family"
        )
    return allowed, changed


def _audit_mark_lookups(before: TTFont, after: TTFont) -> None:
    original, updated = before["GPOS"].table, after["GPOS"].table
    for key in ("ScriptList", "FeatureList"):
        if layout_signature(getattr(original, key), before) != layout_signature(
            getattr(updated, key), after
        ):
            raise ValueError(
                f"GPOS {key}: expected unchanged mark feature registration"
            )
    old, new = original.LookupList.Lookup, updated.LookupList.Lookup
    if len(old) != len(new):
        raise ValueError("GPOS: expected the same attachment lookup count")
    for first, second in zip(old, new):
        _require_lookup_structure(first, second)
        for left, right in zip(first.SubTable, second.SubTable):
            _audit_mark_subtable(left, right, before, after)


def _require_lookup_structure(first: BaseTable, second: BaseTable) -> None:
    old = (first.LookupType, first.LookupFlag, len(first.SubTable))
    new = (second.LookupType, second.LookupFlag, len(second.SubTable))
    if old != new:
        raise ValueError(f"{new}: expected unchanged attachment lookup structure {old}")


def _audit_mark_subtable(
    left: BaseTable, right: BaseTable, before: TTFont, after: TTFont
) -> None:
    left = getattr(left, "ExtSubTable", left)
    right = getattr(right, "ExtSubTable", right)
    if hasattr(left, "BaseCoverage"):
        for key in ("MarkCoverage", "MarkArray"):
            if layout_signature(getattr(left, key), before) != layout_signature(
                getattr(right, key), after
            ):
                raise ValueError(
                    f"GPOS {key}: expected unchanged combining mark anchors"
                )
    elif layout_signature(left, before) != layout_signature(right, after):
        raise ValueError("GPOS: expected unchanged mark-to-mark positioning")


def _audit_screened_glyphs(font: TTFont, study: Path) -> None:
    with TTFont(study) as screened:
        original = screened["CFF "].cff.topDictIndex[0].CharStrings
        updated = font["CFF "].cff.topDictIndex[0].CharStrings
        for name in STEM_NAMES:
            if original[name].bytecode != updated[name].bytecode:
                raise ValueError(
                    f"{name}: expected the exact screened plain glyph program"
                )


def main(argv: list[str] | None = None) -> None:
    """Write all-face audit evidence; e.g. ``main(['--base', 'old', '--new', 'new'])``."""
    args = _stem_build_args(argv)
    sources = sorted(args.base.glob("TalhaMono*.otf"))
    results = [
        audit_stem_build(
            source,
            args.new / source.name,
            (args.study / source.name.replace("NF-", "-")) if args.study else None,
        )
        for source in sources
    ]
    if not results:
        raise ValueError(f"{args.base}: expected Talha Mono baseline faces")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Complete stem-family audit: {len(results)} faces PASS")


def _stem_build_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--study", type=Path)
    parser.add_argument("--out", type=Path, default=Path("build/stem-build-audit.json"))
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
