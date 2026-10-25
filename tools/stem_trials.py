"""Export zero/control and 20-unit t/l/1 studies for all ten ordinary faces.

python tools/stem_trials.py --fonts build --out build/stem-trials
"""

import argparse
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from nohint import unhinted_glyphs
from stem_study import STEM_NAMES, replace_stem_trial


def hint_stem_trial(path: Path) -> None:
    """Hint only eligible study glyphs; e.g. ``hint_stem_trial(path)``."""
    with TTFont(path) as font:
        targets = sorted(set(STEM_NAMES) - set(unhinted_glyphs(font)))
    if not targets:
        return
    executable = Path(sys.executable).with_name("otfautohint")
    if not executable.is_file():
        raise ValueError(f"{executable}: expected otfautohint beside Python")
    subprocess.run(
        [str(executable), "-p", "1", "-g", ",".join(targets), str(path)], check=True
    )


def export_stem_trials(source: Path, output: Path) -> list[Path]:
    """Keep study copies separate from installable candidates; e.g. ``export_stem_trials(src, out)``."""
    paths = []
    for label, strength, flag in (("0", 0, 0), ("20", 20, 20), ("20-flag10", 20, 10)):
        target = output / label / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        with TTFont(source) as font:
            replace_stem_trial(font, strength, flag)
            font.save(target)
        hint_stem_trial(target)
        paths.append(target)
    return paths


def main(argv: list[str] | None = None) -> None:
    """Export every ordinary face, excluding NF duplicates; e.g. ``main(['--fonts', 'build'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, default=Path("build"))
    parser.add_argument("--out", type=Path, default=Path("build/stem-trials"))
    args = parser.parse_args(argv)
    sources = sorted(
        path for path in args.fonts.glob("TalhaMono*.otf") if "NF-" not in path.name
    )
    if not sources:
        raise ValueError(f"{args.fonts}: expected built Talha Mono OTF faces")
    for source in sources:
        for target in export_stem_trials(source, args.out):
            print(target)


if __name__ == "__main__":
    main()
