"""Export equivalent SS11 lookup copies without changing outlines or hints.

python tools/spacing_optimize.py --fonts build/beta7-stems --out build/beta7-compact
"""

import argparse
import json
from pathlib import Path

from fontTools.ttLib import TTFont

from gsub_features import feature_lookups, lookup_outputs
from spacing_prune import prune_forward_lookahead
from identical import differing_tables


def optimize_spacing_font(source: Path, target: Path) -> dict[str, object]:
    """Require outputs to originate exclusively in SS11; e.g. ``optimize_spacing_font(src, out)``."""
    if source.resolve() == target.resolve():
        raise ValueError(f"{target}: expected a separate output font")
    removed = _optimized_copy(source, target)
    unrelated = [tag for tag in differing_tables(source, target) if tag != "GSUB"]
    if unrelated:
        raise ValueError(f"{unrelated}: expected only GSUB serialization changes")
    return {
        "font": source.name,
        "before_bytes": source.stat().st_size,
        "after_bytes": target.stat().st_size,
        "removed": removed,
    }


def _optimized_copy(source: Path, target: Path) -> dict[str, int]:
    with TTFont(source) as font:
        outputs = {
            name for name in font.getGlyphOrder() if name.endswith((".ctxL", ".ctxR"))
        }
        _require_private_outputs(font, outputs)
        indices = feature_lookups(font, lambda tag: tag == "ss11")
        if len(indices) != 1:
            raise ValueError(f"{indices}: expected one SS11 entry lookup")
        removed = prune_forward_lookahead(
            font["GSUB"].table.LookupList.Lookup[indices[0]], outputs
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        font.save(target)
    return removed


def _require_private_outputs(font: TTFont, outputs: set[str]) -> None:
    prior = feature_lookups(font, lambda tag: tag != "ss11")
    encoded = set(font.getBestCmap().values())
    if not outputs or outputs & (encoded | lookup_outputs(font, prior)):
        raise ValueError(
            "SS11 outputs: expected unencoded glyphs produced only by SS11"
        )


def main(argv: list[str] | None = None) -> None:
    """Keep source candidates intact while exporting optimized copies; e.g. ``main(['--fonts', 'build', '--out', 'trial'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.fonts.resolve() == args.out.resolve():
        raise ValueError(f"{args.out}: expected an output separate from source fonts")
    sources = sorted(args.fonts.glob("TalhaMono*.otf"))
    if not sources:
        raise ValueError(f"{args.fonts}: expected Talha Mono candidate fonts")
    results = [optimize_spacing_font(path, args.out / path.name) for path in sources]
    (args.out / "optimization.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"Optimized SS11 copies: {len(results)} fonts in {args.out}")


if __name__ == "__main__":
    main()
