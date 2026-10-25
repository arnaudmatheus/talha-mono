"""Portable review packages preserve candidate bytes and exclude user data."""

import json
import shutil
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest

from conftest import square, tiny_font
from reading_review import build_reading_review, package_reading_review


@pytest.fixture
def built_reviewer(tmp_path: Path) -> tuple[Path, Path]:
    directory = tmp_path / "source"
    directory.mkdir()
    source = directory / "TalhaMono-Regular.otf"
    tiny_font({"i": [square(100, 0, 300)]}).save(source)
    (directory / "trials").mkdir()
    (directory / "trials" / source.name).write_bytes(b"not a candidate font")
    output = tmp_path / "review"
    build_reading_review(directory, output)
    return source, output


def test_review_manifest_identifies_exact_copies_and_excludes_nested_studies(
    built_reviewer: tuple[Path, Path],
) -> None:
    source, output = built_reviewer
    records = json.loads((output / "fonts.json").read_text())
    assert len(records) == 1 and records[0]["cell"] == 1160
    assert records[0]["sha256"] == sha256(source.read_bytes()).hexdigest()
    assert (output / records[0]["file"]).read_bytes() == source.read_bytes()
    assert (output / "review-model.mjs").is_file()
    assert "No installation" in (output / "README.txt").read_text()


def test_review_zip_contains_required_assets_but_never_user_exports(
    built_reviewer: tuple[Path, Path],
) -> None:
    source, output = built_reviewer
    archive = output.parent / "review.zip"
    (output / "my-observations.json").write_text('{"private":"reading notes"}')
    (output / "fonts/TalhaMono-user-study.otf").write_bytes(b"unlisted study")
    package_reading_review(output, archive)
    with ZipFile(archive) as package:
        assert package.testzip() is None
        assert not any(
            "my-observations" in name or "user-study" in name
            for name in package.namelist()
        )
        assert (
            package.read("TalhaMono-reading-review/fonts/" + source.name)
            == source.read_bytes()
        )
    checksum = archive.with_suffix(".sha256").read_text()
    assert checksum.startswith(sha256(archive.read_bytes()).hexdigest())


def test_modified_candidate_bytes_cannot_be_packaged_as_the_reviewed_font(
    built_reviewer: tuple[Path, Path],
) -> None:
    source, output = built_reviewer
    (output / "fonts" / source.name).write_bytes(b"changed font")
    with pytest.raises(ValueError, match="expected unchanged font bytes"):
        package_reading_review(output, output.parent / "review.zip")


def test_paired_reviewer_keeps_both_versions_and_matches_styles(
    built_reviewer: tuple[Path, Path],
) -> None:
    source, output = built_reviewer
    candidate = output.parent / "candidate"
    candidate.mkdir()
    shutil.copy2(source, candidate / source.name)
    records = build_reading_review(source.parent, output, candidate)
    assert len(records) == 2
    assert {row["group"] for row in records} == {"baseline", "candidate"}
    assert {row["pair"] for row in records} == {source.name}
    assert {row["file"] for row in records} == {
        f"fonts/{group}/{source.name}" for group in ("baseline", "candidate")
    }
    (candidate / source.name).rename(candidate / "TalhaMono-Italic.otf")
    with pytest.raises(ValueError, match="matching baseline/candidate"):
        build_reading_review(source.parent, output, candidate)
