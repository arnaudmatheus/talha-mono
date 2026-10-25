"""Check real-font contextual accents, spacing alternates and fixed advances.

python tools/context_check.py --fonts build --base build/beta4-baseline
"""

import argparse
import json
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.cffLib import TopDict

from glyph_table import glyph_table
from marks import MARKS
from run_raster import RunGlyph, RunRasterizer
from glyph_writer import GlyphWriter
from mark_positioning import STACK_GAP

MARK_SAMPLES = ("mĩ́", "mî́", "mḷ", "tĩ́p", "pĩ́t", "mĺ̃m", "mḷ̌m", "it̃́p", "mł̣")
CODE_SAMPLE = "if item != nil { filter(list, 1); }"


def context_feature_matrix(code: bool = False) -> list[dict[str, int]]:
    """Exercise calt/SS11 independently, plus liga for code; e.g. ``context_feature_matrix(True)``."""
    return [
        {"calt": calt, "ss11": spacing, "liga": liga}
        for calt in (0, 1)
        for spacing in (0, 1)
        for liga in ((0, 1) if code else (1,))
    ]


def mark_base_names(font: TTFont) -> set[str]:
    """Collect actual GPOS attachment coverage; e.g. ``mark_base_names(font)``."""
    names: set[str] = set()
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            if hasattr(subtable, "BaseCoverage"):
                names.update(subtable.BaseCoverage.glyphs)
    return names


def expected_context_bases(font: TTFont) -> set[str]:
    """Find supported default, accented and contextual Latin bases; e.g. ``expected_context_bases(font)``."""
    cmap = font.getBestCmap()
    drawings = set(glyph_table(lambda name: name in font.getGlyphOrder()))
    bases = {
        name for cp, name in cmap.items() if chr(cp).isalpha() and name in drawings
    }
    for cp, name in cmap.items():
        decomposed = unicodedata.normalize("NFD", chr(cp))
        if len(decomposed) > 1 and cmap.get(ord(decomposed[0])) in drawings:
            if all(ord(mark) in MARKS for mark in decomposed[1:]):
                bases.add(name)
    variants = {
        name
        for name in font.getGlyphOrder()
        if name.endswith((".left", ".right", ".both", ".ctxL", ".ctxR"))
        and name.rsplit(".", 1)[0] in bases
    }
    return bases | variants | ({"i.loclTRK"} & set(font.getGlyphOrder()))


def check_context_coverage(font: TTFont) -> int:
    """Require anchors and GDEF for every supported contextual base; e.g. ``check_context_coverage(font)``."""
    expected = expected_context_bases(font)
    missing = sorted(expected - mark_base_names(font))
    if missing:
        raise ValueError(
            f"{missing[:8]}: expected mark attachment on supported letter forms"
        )
    classes = font["GDEF"].table.GlyphClassDef.classDefs
    wrong = sorted(name for name in expected if classes.get(name) != 1)
    if wrong:
        raise ValueError(f"{wrong[:8]}: expected GDEF base class 1")
    return len(expected)


def _placement_signature(glyphs: list[RunGlyph]) -> list[tuple[str, int, int, int]]:
    # Cluster indices refer to input codepoints, so NFC/NFD indices can differ
    # even when the same glyphs occupy precisely the same positions.
    return [(g.name, g.advance, g.x_offset, g.y_offset) for g in glyphs]


def _check_normalizations(
    raster: RunRasterizer, text: str, features: dict[str, int]
) -> None:
    expected = _placement_signature(raster.shape(text, features))
    for form in ("NFC", "NFD"):
        shaped = raster.shape(unicodedata.normalize(form, text), features)
        if _placement_signature(shaped) != expected:
            raise ValueError(f"{text!r}: expected identical NFC/NFD shaping")


def _check_mark_sample(
    raster: RunRasterizer, text: str, features: dict[str, int]
) -> None:
    glyphs = raster.shape(text, features)
    marks = [glyph for glyph in glyphs if glyph.advance == 0]
    cell = raster.font["hmtx"]["i"][0]
    if not marks or any(mark.x_offset >= -cell / 2 for mark in marks):
        raise ValueError(f"{text!r}: expected marks attached to the preceding base")
    _check_normalizations(raster, text, features)


def check_context_samples(path: Path) -> None:
    """Verify marks after calt/SS11 substitutions in actual shaping; e.g. ``check_context_samples(path)``."""
    raster = RunRasterizer(path)
    for features in context_feature_matrix():
        for text in MARK_SAMPLES:
            _check_mark_sample(raster, text, features)
        _check_uncomposed_stack(raster, features)
    _check_code_cells(raster)
    off = raster.shape("tipiti", {"ss11": 0})
    on = raster.shape("tipiti", {"ss11": 1})
    if off == on or sum(g.advance for g in off) != sum(g.advance for g in on):
        raise ValueError(
            f"{path.name}: expected SS11 to change ink and preserve total advance"
        )


def _check_uncomposed_stack(raster: RunRasterizer, features: dict[str, int]) -> None:
    glyphs = raster.shape("it̃́p", features)
    marks = [glyph for glyph in glyphs if glyph.advance == 0]
    if len(marks) != 2:
        raise ValueError(f"{features}: expected two separate marks on t")
    writer = GlyphWriter(raster.font, raster.font["hmtx"]["i"][0])
    first_top = writer.bounds(marks[0].name)[3] + marks[0].y_offset
    next_bottom = writer.bounds(marks[1].name)[1] + marks[1].y_offset
    if next_bottom < first_top + STACK_GAP - 1:
        raise ValueError(
            f"{features}: expected at least {STACK_GAP - 1} units between stacked marks"
        )


def _check_code_cells(raster: RunRasterizer) -> None:
    cell = raster.font["hmtx"]["i"][0]
    for features in context_feature_matrix(code=True):
        shaped = raster.shape(CODE_SAMPLE, features)
        if sum(glyph.advance for glyph in shaped) != len(CODE_SAMPLE) * cell:
            raise ValueError(
                f"{features}: expected fixed columns in code with liga off/on"
            )


def _check_previous_widths(font: TTFont, before: TTFont) -> None:
    if before.getBestCmap() != font.getBestCmap():
        raise ValueError(
            "Changed Unicode mappings: expected identical baseline coverage"
        )
    wrong = [
        name
        for name, (advance, _) in before["hmtx"].metrics.items()
        if font["hmtx"].metrics.get(name, (None, 0))[0] != advance
    ]
    if wrong:
        raise ValueError(f"{wrong[:8]}: expected unchanged baseline advances")


def _check_spacing_widths(font: TTFont) -> int:
    cell = font["hmtx"]["i"][0]
    alternates = [
        name for name in font.getGlyphOrder() if name.endswith((".ctxL", ".ctxR"))
    ]
    if any(font["hmtx"][name][0] != cell for name in alternates):
        raise ValueError(
            "Changed contextual widths: expected single-cell spacing alternates"
        )
    return len(alternates)


def check_context_file(path: Path, baseline: Path | None) -> dict[str, object]:
    """Audit feature coverage and old/new widths; e.g. ``check_context_file(path, baseline)``."""
    with TTFont(path) as font:
        count = check_context_coverage(font)
        if baseline:
            with TTFont(baseline / path.name) as before:
                _check_previous_widths(font, before)
        alternates = _check_spacing_widths(font)
    check_context_samples(path)
    check_nf_text(path)
    return {
        "face": path.name,
        "attachment_bases": count,
        "spacing_alternates": alternates,
        "mark_feature_combinations": len(context_feature_matrix()),
        "mark_samples": len(MARK_SAMPLES),
        "code_feature_combinations": len(context_feature_matrix(code=True)),
        "result": "PASS",
    }


def check_nf_text(path: Path) -> None:
    """Require identical text programs, hints and features in NF copies; e.g. ``check_nf_text(path)``."""
    if "NF-" not in path.name:
        return
    plain_path = path.with_name(path.name.replace("NF-", "-"))
    with TTFont(plain_path) as plain, TTFont(path) as nerd:
        for tag in ("GSUB", "GPOS"):
            if plain[tag].compile(plain) != nerd[tag].compile(nerd):
                raise ValueError(f"{path.name}: expected the ordinary font's {tag}")
        first, second = plain["CFF "].cff, nerd["CFF "].cff
        _check_nf_programs(
            first.topDictIndex[0], second.topDictIndex[0], plain.getGlyphOrder()
        )
        if [sub.bytecode for sub in first.GlobalSubrs] != [
            sub.bytecode for sub in second.GlobalSubrs
        ]:
            raise ValueError(f"{path.name}: expected identical global CFF subroutines")


def _check_nf_programs(plain: TopDict, nerd: TopDict, names: list[str]) -> None:
    if plain.Private.rawDict != nerd.Private.rawDict:
        raise ValueError(
            "Changed NF hint parameters: expected the ordinary CFF Private dictionary"
        )
    first = [sub.bytecode for sub in getattr(plain.Private, "Subrs", [])]
    second = [sub.bytecode for sub in getattr(nerd.Private, "Subrs", [])]
    if first != second:
        raise ValueError("Changed NF local hints: expected identical CFF subroutines")
    changed = [
        name
        for name in names
        if plain.CharStrings[name].bytecode != nerd.CharStrings[name].bytecode
    ]
    if changed:
        raise ValueError(f"{changed[:8]}: expected byte-identical NF text programs")


def main(argv: list[str] | None = None) -> None:
    """Write actual-font audit results; e.g. ``main(['--fonts', 'build'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, required=True)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--out", type=Path, default=Path("build/context-check.json"))
    args = parser.parse_args(argv)
    paths = sorted(args.fonts.glob("TalhaMono*.otf"))
    if not paths:
        raise ValueError(f"{args.fonts}: expected Talha Mono OTF files")
    results = [check_context_file(path, args.base) for path in paths]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Contextual shaping and advances: {len(results)} faces PASS; {args.out}")


if __name__ == "__main__":
    main()
