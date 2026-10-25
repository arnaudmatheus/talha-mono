"""Check SS11 optimization equivalence on exhaustive and Unicode contexts.

python tools/shaping_equivalence.py --base build/beta7-stems --new build/beta7-compact
"""

import argparse
import itertools
import json
import random
import unicodedata
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from context_check import MARK_SAMPLES, context_feature_matrix
from identical import differing_tables
from spacing_review import REVIEW_CORPUS
from word_measure import READING_CORPUS

ShapeSignature = tuple[tuple[int, int, int, int, int, int], ...]


def shape_signature(
    font: hb.Font, text: str, features: dict[str, int], language: str = "en"
) -> ShapeSignature:
    """Compare glyph IDs, input clusters and every position field; e.g. ``shape_signature(font, 'tipiti', features)``."""
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    buffer.language = language
    hb.shape(font, buffer, features)
    return tuple(
        (g.codepoint, g.cluster, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
        for g, p in zip(buffer.glyph_infos, buffer.glyph_positions)
    )


def unicode_contexts(font: TTFont) -> list[str]:
    """Cover supported Latin bodies and normalization variants deterministically; e.g. ``unicode_contexts(font)``."""
    cmap = font.getBestCmap()
    alphabet = [
        chr(cp)
        for cp in sorted(cmap)
        if "LATIN" in unicodedata.name(chr(cp), "") and chr(cp).isalpha()
    ]
    randomizer = random.Random(20261023)
    contexts = ["".join(randomizer.choices(alphabet, k=7)) for _ in range(2048)]
    normalized = [unicodedata.normalize("NFD", text) for text in contexts]
    contexts += [text for text in normalized if all(ord(cp) in cmap for cp in text)]
    return contexts


def _require_optimization_copy(source: Path, target: Path) -> None:
    unrelated = [tag for tag in differing_tables(source, target) if tag != "GSUB"]
    if unrelated:
        raise ValueError(
            f"{source.name}/{unrelated}: expected only a GSUB optimization"
        )
    with TTFont(source) as before, TTFont(target) as after:
        if before.getGlyphOrder() != after.getGlyphOrder():
            raise ValueError(f"{source.name}: expected identical glyph IDs")


def _compare_contexts(
    before: hb.Font,
    after: hb.Font,
    texts: list[str],
    features: dict[str, int],
    language: str = "en",
) -> int:
    for text in texts:
        if shape_signature(before, text, features, language) != shape_signature(
            after, text, features, language
        ):
            raise ValueError(
                f"{text!r}/{features}/{language}: expected identical shaping"
            )
    return len(texts)


def compare_shape_fonts(source: Path, target: Path) -> dict[str, object]:
    """Check one ordinary face and its exact optimization copy; e.g. ``compare_shape_fonts(src, out)``."""
    _require_optimization_copy(source, target)
    before, after = (hb.Font(hb.Face(path.read_bytes())) for path in (source, target))
    contexts, stress = _equivalence_inputs(source)
    count = sum(
        _compare_contexts(before, after, contexts, {"calt": calt, "ss11": 1})
        for calt in (0, 1)
    )
    count += sum(
        _compare_contexts(before, after, stress, features, language)
        for features in context_feature_matrix(code=True)
        for language in ("en", "pt", "tr")
    )
    return {"face": source.name, "comparisons": count, "result": "PASS"}


def _equivalence_inputs(source: Path) -> tuple[list[str], list[str]]:
    triples = [
        "".join(chars)
        for chars in itertools.product("abcdefghijklmnopqrstuvwxyz", repeat=3)
    ]
    with TTFont(source) as font:
        contexts = triples + unicode_contexts(font)
    stress = list(READING_CORPUS + REVIEW_CORPUS + MARK_SAMPLES) + [
        "tipitiantigofilterlittle" * 8,
        "iaam" * 16,
    ]
    return contexts, stress


def main(argv: list[str] | None = None) -> None:
    """Keep compact lookup evidence separate from letterform changes; e.g. ``main(['--base', 'old', '--new', 'new'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path, default=Path("build/shaping-equivalence.json")
    )
    args = parser.parse_args(argv)
    paths = sorted(
        path for path in args.base.glob("TalhaMono*.otf") if "NF-" not in path.name
    )
    if not paths:
        raise ValueError(f"{args.base}: expected ordinary Talha Mono faces")
    results = []
    for source in paths:
        results.append(compare_shape_fonts(source, args.new / source.name))
        print(source.name, "PASS", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
