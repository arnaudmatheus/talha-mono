"""Audit that display-preview exports change only the thirteen intended glyphs."""

import argparse
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from swash_caps import PILOT_CAPITALS
from identical import head_without_timestamps
from font_preservation import cff_hint_signature

AUDIT_HEADING = (
    "# Display pilot: outline and feature audit",
    "",
    "Only A.swsh, P.swsh, R.swsh, eight directional leaf forms, and two ribbon ends may change.",
    "Every other CFF program, including its hints, must remain byte-identical. All advances and non-outline tables are checked.",
    "",
    "| Face | Changed glyphs | Other outlines + hints | Advances / GSUB / GPOS | Bounds |",
    "|---|---|---|---|---|",
)
AUDIT_FOOTER = (
    "",
    "Bounds: every pilot glyph fits the existing ascent/descent; explicit Unicode ornaments fit their cells.",
    "Swash capitals may overhang horizontally, as the display feature already permits.",
    "",
)


def require_pilot(condition: bool, problem: str) -> None:
    if not condition:
        raise ValueError(
            f"Display pilot: {problem}; expected only the documented glyph changes"
        )


def allowed_pilot_glyphs(font: TTFont) -> set[str]:
    """The feature targets and explicit ornaments; e.g. ``allowed_pilot_glyphs(font)``."""
    codepoints = list(range(0x1F650, 0x1F658)) + [0x2770, 0x2771]
    cmap = font.getBestCmap()
    return {f"{cap}.swsh" for cap in PILOT_CAPITALS} | {cmap[cp] for cp in codepoints}


def changed_charstrings(before: TTFont, after: TTFont) -> set[str]:
    """Find changed outline programs, including hints; e.g. ``changed_charstrings(old, new)``."""
    old = before["CFF "].cff.topDictIndex[0].CharStrings
    new = after["CFF "].cff.topDictIndex[0].CharStrings
    return {
        name
        for name in before.getGlyphOrder()
        if old[name].bytecode != new[name].bytecode
    }


def assert_pilot_metrics(font: TTFont, changed: set[str]) -> None:
    """Check line containment and ornament cell bounds; e.g. ``assert_pilot_metrics(font, names)``."""
    glyphs = font.getGlyphSet()
    for name in changed:
        bounds = BoundsPen(glyphs)
        glyphs[name].draw(bounds)
        require_pilot(bounds.bounds is not None, f"{name}: no visible ink")
        if bounds.bounds is None:
            continue
        left, bottom, right, top = bounds.bounds
        require_pilot(
            bottom >= font["hhea"].descent and top <= font["hhea"].ascent,
            f"{name}: exceeds line bounds {bounds.bounds}",
        )
        if not name.endswith(".swsh"):
            require_pilot(
                left >= 0 and right <= font["hmtx"][name][0],
                f"{name}: exceeds its cell {bounds.bounds}",
            )


def assert_untouched_tables(before: TTFont, after: TTFont) -> None:
    require_pilot(
        before.getGlyphOrder() == after.getGlyphOrder(), "glyph order changed"
    )
    require_pilot(
        set(before.reader.keys()) == set(after.reader.keys()), "table set changed"
    )
    for tag in before.reader.keys():
        if tag not in ("CFF ", "head", "hmtx"):
            require_pilot(
                before.reader[tag] == after.reader[tag],
                f"{tag}: unexpected table change",
            )
    assert_pilot_resources(before, after)
    for name, (advance, lsb) in before["hmtx"].metrics.items():
        require_pilot(after["hmtx"][name][0] == advance, f"{name}: advance changed")
        if name not in allowed_pilot_glyphs(before):
            require_pilot(after["hmtx"][name][1] == lsb, f"{name}: sidebearing changed")


def assert_pilot_resources(before: TTFont, after: TTFont) -> None:
    """Protect shared hints, subroutines, and head metrics; e.g. ``assert_pilot_resources(old, new)``."""
    require_pilot(
        head_without_timestamps(before) == head_without_timestamps(after),
        "head metrics changed",
    )
    old, new = cff_hint_signature(before), cff_hint_signature(after)
    require_pilot(old[0] == new[0], "CFF Private parameters changed")
    require_pilot(old[1:] == new[1:], "CFF subroutines changed")


def validate_pilot_pair(before_path: Path, after_path: Path) -> str:
    """Audit one exported face; e.g. ``validate_pilot_pair(old, new)``."""
    with TTFont(before_path) as before, TTFont(after_path) as after:
        assert_untouched_tables(before, after)
        changed = changed_charstrings(before, after)
        require_pilot(
            changed == allowed_pilot_glyphs(before),
            f"unexpected changed glyphs: {sorted(changed)}",
        )
        assert_pilot_metrics(after, changed)
    return f"| {before_path.name} | {len(changed)} | unchanged | unchanged | pass |"


def validation_report(before: Path, after: Path) -> str:
    """Audit all faces and report the permitted changes; e.g. ``validation_report(old_dir, new_dir)``."""
    paths = sorted(before.glob("*.otf"))
    if not paths:
        raise ValueError(f"{before}: expected a directory containing OTF files")
    rows = [validate_pilot_pair(path, after / path.name) for path in paths]
    return "\n".join([*AUDIT_HEADING, *rows, *AUDIT_FOOTER])


def main(argv: list[str] | None = None) -> None:
    """Write the pilot audit; e.g. ``main(['--base', 'fonts/otf', '--new', 'build/swash-pilot/selected'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--report", default="docs/design/pilot-audit.md", type=Path)
    args = parser.parse_args(argv)
    report = validation_report(args.base, args.new)
    args.report.write_text(report)
    print(
        f"Validated {len(list(args.base.glob('*.otf')))} faces; report: {args.report}"
    )


if __name__ == "__main__":
    main()
