"""Word metrics retain shaping contexts, ligatures, marks and word spaces."""

from pathlib import Path

import numpy as np
import pytest
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from conftest import square, tiny_font
from run_raster import InkBitmap, RunRasterizer, bitmap_box, cluster_masks
from word_measure import (
    feature_settings,
    mask_gap,
    measure_word,
    word_measure_args,
    word_measurements,
)


def word_fixture_path(tmp_path: Path) -> Path:
    names = "a b i m space f f_i a.ctxL".split()
    glyphs = {
        name: ([] if name == "space" else [square(100, 0, 400)]) for name in names
    }
    glyphs["a.ctxL"] = [square(-60, 0, 400)]
    font = tiny_font(glyphs)
    for table in font["cmap"].tables:
        table.cmap[32] = "space"
    addOpenTypeFeaturesFromString(
        font,
        """
        feature liga { sub f i by f_i; } liga;
        feature ss11 { sub i a' m by a.ctxL; } ss11;
    """,
    )
    path = tmp_path / "word-font.otf"
    font.save(path)
    return path


def test_native_bitmap_masks_preserve_ink_and_shared_clusters() -> None:
    first = InkBitmap(0, -2, -3, np.array([[200, 100]], np.uint8))
    mark = InkBitmap(0, -2, -5, np.array([[255]], np.uint8))
    second = InkBitmap(1, 4, -3, np.array([[255]], np.uint8))
    assert bitmap_box([first, mark, second], 8) == (-8, -11, 14, 6)
    masks = cluster_masks([first, mark, second], 8)
    assert list(masks) == [0, 1] and np.count_nonzero(masks[0]) == 3
    gap, overlap = mask_gap(masks[0], masks[1])
    assert gap == 4 and overlap == 0
    assert mask_gap(masks[0], masks[0])[1] == 3
    assert mask_gap(np.zeros((1, 4)), np.zeros((1, 4))) == (None, 0)


def test_entire_word_is_shaped_once_with_requested_features(tmp_path: Path) -> None:
    raster = RunRasterizer(word_fixture_path(tmp_path))
    assert raster.shape("iam", {"ss11": 1})[1].name == "a.ctxL"
    assert raster.shape("iam", {"ss11": 0})[1].name == "a"
    off = measure_word(raster, "iam", 20, {"ss11": 0})
    on = measure_word(raster, "iam", 20, {"ss11": 1})
    assert off["advance_px"] == on["advance_px"]
    assert off["gaps"][0]["mean_gap_px"] > on["gaps"][0]["mean_gap_px"]
    ligature = raster.render("fi", 15, {})
    assert len(ligature.glyphs) == len(ligature.masks) == 1
    assert ligature.glyphs[0].name == "f_i" and ligature.image.any()
    assert measure_word(raster, "a b", 20, {})["gaps"][0]["word_boundary"]
    normal = measure_word(raster, "ab", 20, {})
    assert normal["advance_px"] == pytest.approx(23.2)
    assert normal["cv"] == 0 and normal["gaps"][0]["mean_gap_px"] > 0
    with pytest.raises(ValueError, match="nonempty single-line"):
        raster.shape("a\nb", {})
    with pytest.raises(ValueError, match="positive pixel"):
        raster.render("a", 0, {})


def test_cli_compares_features_and_keeps_measurements_machine_readable(
    tmp_path: Path,
) -> None:
    path = word_fixture_path(tmp_path)
    arguments = ["--font", f"fixture={path}", "--compare-spacing", "--text", "iam"]
    args = word_measure_args(arguments + ["--sizes", "12"])
    results = word_measurements(args)
    assert set(results) == {"fixture / ss11=0", "fixture / ss11=1"}
    assert results["fixture / ss11=1"][0]["glyphs"][1]["name"] == "a.ctxL"
    assert feature_settings("calt=1,ss11=0") == {"calt": 1, "ss11": 0}
    with pytest.raises(ValueError, match="LABEL=PATH"):
        args.font = ["bad-spec"]
        word_measurements(args)


def test_measurements_reject_missing_glyphs_and_unhandled_direction(
    tmp_path: Path,
) -> None:
    from run_raster import text_buffer

    raster = RunRasterizer(word_fixture_path(tmp_path))
    with pytest.raises(ValueError, match="complete font coverage"):
        raster.shape("not-in-fixture", {})
    with pytest.raises(ValueError, match="left-to-right"):
        text_buffer("العربية")
