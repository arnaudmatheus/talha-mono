"""Build a portable local browser reviewer without installing fonts.

python tools/reading_review.py --fonts build --out build/reading-review
"""

import argparse
import json
import shutil
from hashlib import sha256
from pathlib import Path
from typing import NotRequired, TypedDict
from zipfile import ZIP_DEFLATED, ZipFile

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).with_name("reading_ui")
UI_FILES = ("index.html", "review.css", "review.mjs", "review-model.mjs")
REVIEW_README = """Talha Mono / local reading review

Start from this directory:
  python -m http.server --bind 127.0.0.1 8765
Then open http://127.0.0.1:8765 in your browser.

No installation or remote services are needed. The local server serves files;
the reviewer keeps observations in memory until you download a JSON export.
Reloading the page loses unsaved observations. The exported data includes the
A/B assignment and whether it was revealed before each preference was saved.

Compare clarity and preference at 100% browser zoom. Spacing mode uses the
same font with SS11 off/on. A paired candidate also enables Letterforms mode,
which compares two font versions at a shared SS11 setting. Editing either
pane updates both samples. The export records each pane's font hash/features.
Repeated reading of the same passage cannot establish a reading-speed benefit.
For timed reading use fresh equivalent passages and counterbalanced order.
Browser results do not establish behavior in a native editor or terminal.
"""


class ReviewFont(TypedDict):
    file: str
    family: str
    style: str
    label: str
    version: str
    sha256: str
    cell: int
    nf: bool
    group: NotRequired[str]
    pair: NotRequired[str]


def review_font_record(path: Path) -> ReviewFont:
    """Describe the exact candidate bytes; e.g. ``review_font_record(Path('TalhaMono-Regular.otf'))``."""
    with TTFont(path) as font:
        family = font["name"].getDebugName(16) or font["name"].getDebugName(1)
        style = font["name"].getDebugName(17) or font["name"].getDebugName(2)
        return ReviewFont(
            file="fonts/" + path.name,
            family=family,
            style=style,
            label=f"{family} · {style}",
            version=font["name"].getDebugName(5) or "Unversioned study",
            sha256=sha256(path.read_bytes()).hexdigest(),
            cell=font["hmtx"]["i"][0],
            nf="NF" in family,
        )


def copy_review_fonts(
    source: Path, output: Path, group: str | None = None
) -> list[ReviewFont]:
    """Copy candidate faces, excluding nested study directories; e.g. ``copy_review_fonts(build, out)``."""
    paths = sorted(source.glob("TalhaMono*.otf"))
    if not paths:
        raise ValueError(f"{source}: expected built Talha Mono OTF faces")
    target = output / "fonts" / group if group else output / "fonts"
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for path in paths:
        destination = target / path.name
        shutil.copy2(path, destination)
        record = review_font_record(destination)
        record["file"] = destination.relative_to(output).as_posix()
        if group:
            record["group"], record["pair"] = group, path.name
        records.append(record)
    return records


def build_reading_review(
    fonts: Path, output: Path, candidate: Path | None = None
) -> list[ReviewFont]:
    """Create a self-contained review directory; e.g. ``build_reading_review(Path('build'), out)``."""
    output.mkdir(parents=True, exist_ok=True)
    records = _review_font_groups(fonts, output, candidate)
    for name in UI_FILES:
        shutil.copy2(ASSETS / name, output / name)
    (output / "fonts.json").write_text(json.dumps(records, indent=2) + "\n")
    (output / "README.txt").write_text(
        REVIEW_README.replace("8765", "8766") if candidate else REVIEW_README
    )
    shutil.copy2(ROOT / "OFL.txt", output / "OFL.txt")
    return records


def _review_font_groups(
    fonts: Path, output: Path, candidate: Path | None
) -> list[ReviewFont]:
    if candidate is None:
        return copy_review_fonts(fonts, output)
    baseline = copy_review_fonts(fonts, output, "baseline")
    refined = copy_review_fonts(candidate, output, "candidate")
    _require_review_pairs(baseline, refined)
    return baseline + refined


def _require_review_pairs(
    baseline: list[ReviewFont], refined: list[ReviewFont]
) -> None:
    old, new = (
        {entry["pair"]: entry for entry in group} for group in (baseline, refined)
    )
    if old.keys() != new.keys():
        raise ValueError(
            "Review candidate: expected matching baseline/candidate face files"
        )
    for name in old:
        if (old[name]["style"], old[name]["cell"]) != (
            new[name]["style"],
            new[name]["cell"],
        ):
            raise ValueError(
                f"{name}: expected matching style and cell width in both versions"
            )


def package_reading_review(output: Path, archive: Path) -> None:
    """Package only generated review files, excluding user exports; e.g. ``package_reading_review(out, zip_path)``."""
    archive.parent.mkdir(parents=True, exist_ok=True)
    files = [
        output / name for name in (*UI_FILES, "fonts.json", "README.txt", "OFL.txt")
    ]
    files += _review_manifest_fonts(output)
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as package:
        for path in files:
            package.write(
                path, "TalhaMono-reading-review/" + str(path.relative_to(output))
            )
    with ZipFile(archive) as package:
        if damaged := package.testzip():
            raise ValueError(f"{damaged}: expected intact reading-review ZIP members")
    digest = sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".sha256").write_text(f"{digest}  {archive.name}\n")


def _review_manifest_fonts(output: Path) -> list[Path]:
    records = json.loads((output / "fonts.json").read_text())
    paths = []
    for record in records:
        path = output / record["file"]
        if sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"{path}: expected unchanged font bytes from fonts.json")
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> None:
    """Build the reviewer and optional download; e.g. ``main(['--fonts', 'build'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, default=Path("build"))
    parser.add_argument("--out", type=Path, default=Path("build/reading-review"))
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args(argv)
    records = build_reading_review(args.fonts, args.out, args.candidate)
    if args.zip:
        package_reading_review(args.out, args.zip)
    print(f"Reading reviewer: {args.out} / {len(records)} faces")


if __name__ == "__main__":
    main()
