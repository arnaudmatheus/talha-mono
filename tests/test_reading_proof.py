"""Reading proofs retain the renderer's native pixel coverage on both grounds."""

import numpy as np
from PIL import ImageColor

from reading_proof import INK, PAPER, reading_raster


class CoverageRenderer:
    def render(self, markup: str, size: int) -> np.ndarray:
        assert "&lt;" in markup and size == 15
        return np.array([[[0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5]]])


def test_reading_raster_preserves_size_and_reverses_grounds() -> None:
    renderer = CoverageRenderer()
    light = reading_raster(renderer, "<", 15)
    dark = reading_raster(renderer, "<", 15, True)
    assert light.size == dark.size == (3, 1)
    assert light.getpixel((0, 0)) == dark.getpixel((1, 0)) == ImageColor.getrgb(PAPER)
    assert light.getpixel((1, 0)) == dark.getpixel((0, 0)) == ImageColor.getrgb(INK)
    assert light.getpixel((2, 0)) != light.getpixel((0, 0))
