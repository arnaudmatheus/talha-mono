"""Check Ghostty/fontconfig resolution with an isolated candidate-only font set.

python tools/terminal_review.py --review build/reading-review
This resolves faces/codepoints; it does not capture terminal rendering or editing.
"""

import argparse
import json
import os
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict
from xml.sax.saxutils import escape

from reading_review import ReviewFont

ProbeCommand = Callable[[list[str], dict[str, str]], str]
PLAIN_PROBE = "tl1ĩ\u0301"
NF_PROBE = PLAIN_PROBE + "\uf120\ue0b0"
TERMINAL_STYLES = {
    "Regular": "regular",
    "Bold": "bold",
    "Italic": "italic",
    "Bold Italic": "bold_italic",
}


class TerminalResolution(TypedDict):
    font: str
    family: str
    style: str
    resolved_file: str
    ghostty_output: str
    result: str


def resolution_environment(fonts: Path, output: Path) -> dict[str, str]:
    """Use only review copies, without installing fonts; e.g. ``resolution_environment(fonts, out)``."""
    output.mkdir(parents=True, exist_ok=True)
    config = output / "fonts.conf"
    config.write_text(
        '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">'
        f"<fontconfig><dir>{escape(str(fonts.resolve()))}</dir>"
        f"<cachedir>{escape(str((output / 'cache').resolve()))}</cachedir></fontconfig>"
    )
    environment = os.environ.copy()
    environment["FONTCONFIG_FILE"] = str(config.resolve())
    return environment


def run_resolution_command(command: list[str], environment: dict[str, str]) -> str:
    """Run noninteractive font-discovery helpers; e.g. ``run_resolution_command(['ghostty', '+version'], env)``."""
    result = subprocess.run(
        command, env=environment, capture_output=True, text=True, check=True
    )
    return result.stdout


def matches_ghostty_family(output: str, family: str, nf: bool) -> bool:
    """Require the requested face for every text probe; e.g. ``matches_ghostty_family(output, 'Talha Mono', False)``."""
    matches = re.findall("found in face “([^”]+)”", output)
    expected = len(PLAIN_PROBE) + int(nf)
    return len(matches) == expected and set(matches) == {family}


def resolve_terminal_face(
    entry: ReviewFont,
    review: Path,
    environment: dict[str, str],
    run: ProbeCommand = run_resolution_command,
) -> TerminalResolution:
    pattern = f"{entry['family']}:style={entry['style']}"
    matched = run(["fc-match", "-f", "%{file}\n", pattern], environment).strip()
    output = run(_ghostty_face_command(entry), environment)
    valid = Path(matched).resolve() == (review / entry["file"]).resolve()
    valid = valid and matches_ghostty_family(output, entry["family"], entry["nf"])
    return TerminalResolution(
        font=entry["file"],
        family=entry["family"],
        style=entry["style"],
        resolved_file=matched,
        ghostty_output=output,
        result="PASS" if valid else "FAIL",
    )


def _ghostty_face_command(entry: ReviewFont) -> list[str]:
    return [
        "ghostty",
        "+show-face",
        "--config-default-files=false",
        "--font-family=" + entry["family"],
        "--style=" + TERMINAL_STYLES[entry["style"]],
        "--string=" + (NF_PROBE if entry["nf"] else PLAIN_PROBE),
    ]


def terminal_resolution_markdown(results: list[TerminalResolution]) -> str:
    """Keep resolution evidence distinct from rendering claims; e.g. ``terminal_resolution_markdown(results)``."""
    lines = [
        "# Native terminal font resolution",
        "",
        "Isolated fontconfig set; Ghostty default config files disabled. Fontconfig resolves each exact file/style; Ghostty resolves text probes to the requested family. No fonts are installed.",
        "",
        "Ghostty show-face does not account for grapheme clustering. This does not verify terminal pixels, SS11 shaping, cursor placement, selection, or scrolling. Powerline U+E0B0 uses Ghostty internal sprites.",
        "",
        "| Candidate | Style | Resolution |",
        "|---|---|---|",
    ]
    lines += [
        f"| {row['family']} | {row['style']} | {row['result']} |" for row in results
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    """Write native resolution evidence; e.g. ``main(['--review', 'build/reading-review'])``."""
    args = _terminal_review_args(argv)
    entries = json.loads((args.review / "fonts.json").read_text())
    environment = resolution_environment(args.review / "fonts", args.work)
    results = [
        resolve_terminal_face(entry, args.review, environment) for entry in entries
    ]
    report = {
        "ghostty": run_resolution_command(["ghostty", "+version"], environment),
        "faces": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    args.out.with_suffix(".md").write_text(terminal_resolution_markdown(results))
    if any(row["result"] != "PASS" for row in results):
        raise SystemExit(
            "Terminal resolution failed: expected every candidate family/file"
        )
    print(f"Ghostty/fontconfig: {len(results)} candidate faces resolve correctly")


def _terminal_review_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("build/reading-review"))
    parser.add_argument("--work", type=Path, default=Path("build/ghostty-review"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/design/measurements/beta6-terminal-resolution"),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
