"""Export native-hinted spacing strengths without rebuilding the entire font.

python tools/context_trials.py --font build/TalhaMono-Regular.otf
"""

import argparse
import copy
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

from glyph_writer import GlyphWriter
from nohint import unhinted_glyphs


def change_spacing_strength(font: TTFont, strength: int) -> set[str]:
    """Move existing SS11 outlines and their anchors together; e.g. ``change_spacing_strength(font, 20)``."""
    if strength not in (20, 40, 60):
        raise ValueError(f"{strength}: expected spacing strength 20, 40 or 60")
    names = [name for name in font.getGlyphOrder() if name.endswith((".ctxL", ".ctxR"))]
    if not names:
        raise ValueError("No contextual alternates: expected a font containing SS11")
    writer = GlyphWriter(font, font["hmtx"]["i"][0])
    deltas = {}
    for name in names:
        source = name.rsplit(".", 1)[0]
        shift = -strength if name.endswith(".ctxL") else strength
        previous = font["hmtx"][name][1] - font["hmtx"][source][1]
        deltas[name] = shift - previous
        writer.put_shifted(name, source, shift)
    _shift_context_anchors(font, deltas)
    return set(names)


def _shift_context_anchors(font: TTFont, deltas: dict[str, int]) -> None:
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            if hasattr(subtable, "BaseCoverage"):
                _shift_base_records(subtable, deltas)


def _shift_base_records(subtable: ot.MarkBasePos, deltas: dict[str, int]) -> None:
    for index, name in enumerate(subtable.BaseCoverage.glyphs):
        if name not in deltas:
            continue
        record = copy.deepcopy(subtable.BaseArray.BaseRecord[index])
        for anchor in record.BaseAnchor:
            if anchor:
                anchor.XCoordinate += deltas[name]
        subtable.BaseArray.BaseRecord[index] = record


def _hint_context_trial(path: Path, names: set[str]) -> None:
    with TTFont(path) as font:
        targets = sorted(names - set(unhinted_glyphs(font)))
    executable = Path(sys.executable).with_name("otfautohint")
    if not executable.is_file():
        raise ValueError(
            f"{executable}: expected the project's autohinter beside Python"
        )
    subprocess.run(
        [str(executable), "-p", "1", "-g", ",".join(targets), str(path)], check=True
    )


def export_spacing_trials(
    source: Path, output: Path, strengths: list[int]
) -> list[Path]:
    """Keep other outlines and features intact in trial copies; e.g. ``export_spacing_trials(path, out, [20, 40, 60])``."""
    paths = []
    for strength in strengths:
        target = output / str(strength) / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if strength == 40:
            shutil.copy2(source, target)
        else:
            with TTFont(source) as font:
                names = change_spacing_strength(font, strength)
                font.save(target)
            _hint_context_trial(target, names)
        paths.append(target)
    return paths


def main(argv: list[str] | None = None) -> None:
    """Export strength comparisons; e.g. ``main(['--font', 'build/TalhaMono-Regular.otf'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("build/context-trials"))
    parser.add_argument("--strengths", type=int, nargs="+", default=[20, 40, 60])
    args = parser.parse_args(argv)
    for path in export_spacing_trials(args.font, args.out, args.strengths):
        print(path)


if __name__ == "__main__":
    main()
