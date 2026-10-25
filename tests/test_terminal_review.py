"""Native helper probes reject fallback faces and inspect no user configuration."""

from pathlib import Path

import pytest

from reading_review import ReviewFont
from terminal_review import (
    PLAIN_PROBE,
    matches_ghostty_family,
    resolution_environment,
    resolve_terminal_face,
)


class FakeResolution:
    def __init__(self, expected: Path, family: str = "Talha Mono") -> None:
        self.expected, self.family = expected, family

    def __call__(self, command: list[str], environment: dict[str, str]) -> str:
        if command[0] == "fc-match":
            return str(self.expected) + "\n"
        assert "--config-default-files=false" in command
        return "\n".join(
            f"U+{ord(cp):X} found in face “{self.family}”." for cp in PLAIN_PROBE
        )


@pytest.fixture
def terminal_entry() -> ReviewFont:
    return ReviewFont(
        file="fonts/TalhaMono-Regular.otf",
        family="Talha Mono",
        style="Regular",
        label="Regular",
        version="beta.6",
        sha256="known",
        cell=1160,
        nf=False,
    )


def test_native_face_probe_rejects_fallback_and_does_not_load_user_config(
    tmp_path: Path, terminal_entry: ReviewFont
) -> None:
    expected = tmp_path / terminal_entry["file"]
    environment = resolution_environment(tmp_path / "fonts", tmp_path / "work")
    config = Path(environment["FONTCONFIG_FILE"]).read_text()
    assert str((tmp_path / "fonts").resolve()) in config and "<include>" not in config
    probes = [
        FakeResolution(expected),
        FakeResolution(expected, "Fallback"),
        FakeResolution(tmp_path / "other.otf"),
    ]
    results = [
        resolve_terminal_face(terminal_entry, tmp_path, environment, probe)["result"]
        for probe in probes
    ]
    assert results == ["PASS", "FAIL", "FAIL"]


def test_missing_marks_and_fallback_families_cannot_pass_the_native_probe() -> None:
    valid = "\n".join("found in face “Talha Mono”." for _ in PLAIN_PROBE)
    assert matches_ghostty_family(valid, "Talha Mono", False)
    assert not matches_ghostty_family(valid, "Talha Mono", True)
    assert not matches_ghostty_family(
        valid.replace("Talha Mono", "Fallback", 1), "Talha Mono", False
    )
    assert not matches_ghostty_family("", "Talha Mono", False)
