"""Every shipped style receives its own confusable-pair gate."""

from pathlib import Path

from check import _comparison_specs


def test_all_ten_styles_are_measured_independently(tmp_path: Path) -> None:
    faces = [
        f"TalhaMono{family}-{style}.otf"
        for family in ("", "Wide", "Text")
        for style in ("Regular", "Bold", "Italic", "BoldItalic")
        if family != "Text" or style in ("Regular", "Italic")
    ]
    before, after = tmp_path / "old", tmp_path / "new"
    before.mkdir()
    after.mkdir()
    for face in faces:
        (before / face).touch()
        (after / face).touch()
    specs, pairs = _comparison_specs(before, after)
    assert len(pairs) == 10
    independently_measured = {
        spec.split("=", 1)[1].split(":")[0] for spec in specs if spec.startswith("new")
    }
    assert independently_measured == {str(after / face) for face in faces}
