"""Shape a complete text run once, then rasterize its glyphs at their positions."""

import math
from dataclasses import dataclass
from pathlib import Path

import freetype
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont


@dataclass(frozen=True)
class RunGlyph:
    name: str
    glyph_id: int
    cluster: int
    advance: int
    x_offset: int
    y_offset: int


@dataclass(frozen=True)
class InkBitmap:
    cluster: int
    x: int
    y: int
    pixels: np.ndarray


@dataclass
class RasterRun:
    glyphs: list[RunGlyph]
    masks: dict[int, np.ndarray]
    advance_px: float
    image: np.ndarray


class RunRasterizer:
    """An isolated font, HarfBuzz shaping and native hinted FreeType pixels.

    Example: ``RunRasterizer(path).render('tipiti', 15, {'ss11': 1})``.
    """

    def __init__(self, path: Path) -> None:
        self.font = TTFont(path)
        self.harf = hb.Font(hb.Face(path.read_bytes()))
        self.face = freetype.Face(str(path))
        self.upm = self.font["head"].unitsPerEm

    def shape(self, text: str, features: dict[str, int]) -> list[RunGlyph]:
        buffer = text_buffer(text)
        hb.shape(self.harf, buffer, features)
        if any(glyph.codepoint == 0 for glyph in buffer.glyph_infos):
            raise ValueError(
                f"{text!r}: expected complete font coverage, found .notdef"
            )
        return [
            RunGlyph(
                self.font.getGlyphName(g.codepoint),
                g.codepoint,
                g.cluster,
                p.x_advance,
                p.x_offset,
                p.y_offset,
            )
            for g, p in zip(buffer.glyph_infos, buffer.glyph_positions)
        ]

    def _bitmap(self, glyph: RunGlyph, x: float, y: float) -> InkBitmap:
        origin_x, origin_y = math.floor(x), math.floor(y)
        delta = freetype.Vector(round((x - origin_x) * 64), round((y - origin_y) * 64))
        self.face.set_transform(freetype.Matrix(65536, 0, 0, 65536), delta)
        flags = (
            freetype.FT_LOAD_RENDER
            | freetype.FT_LOAD_TARGET_LIGHT
            | freetype.FT_LOAD_NO_AUTOHINT
        )
        self.face.load_glyph(glyph.glyph_id, flags)
        slot = self.face.glyph
        return InkBitmap(
            glyph.cluster,
            origin_x + slot.bitmap_left,
            -origin_y - slot.bitmap_top,
            bitmap_pixels(slot.bitmap),
        )

    def render(self, text: str, px: int, features: dict[str, int]) -> RasterRun:
        if px <= 0:
            raise ValueError(f"{px}: expected a positive pixel size")
        glyphs = self.shape(text, features)
        self.face.set_pixel_sizes(0, px)
        scale, advance = px / self.upm, 0
        bitmaps = []
        for glyph in glyphs:
            bitmaps.append(
                self._bitmap(
                    glyph, (advance + glyph.x_offset) * scale, glyph.y_offset * scale
                )
            )
            advance += glyph.advance
        masks = cluster_masks(bitmaps, advance * scale)
        image = np.maximum.reduce(list(masks.values()))
        return RasterRun(glyphs, masks, advance * scale, image)


def text_buffer(text: str) -> hb.Buffer:
    """Use explicit LTR single-line inputs; e.g. ``text_buffer('tipiti')``."""
    if not text or "\n" in text:
        raise ValueError(f"{text!r}: expected a nonempty single-line text run")
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    if buffer.direction != "ltr":
        raise ValueError(f"{text!r}: expected a left-to-right text run")
    return buffer


def bitmap_pixels(bitmap: freetype.Bitmap) -> np.ndarray:
    """Respect FreeType row pitch, including empty glyphs; e.g. ``bitmap_pixels(slot.bitmap)``."""
    pixels = np.array(bitmap.buffer, dtype=np.uint8).reshape(
        bitmap.rows, abs(bitmap.pitch)
    )
    if bitmap.pitch < 0:
        pixels = pixels[::-1]
    return pixels[:, : bitmap.width]


def bitmap_box(bitmaps: list[InkBitmap], advance: float) -> tuple[int, int, int, int]:
    """Shared run bounds include spaces and overhangs; e.g. ``bitmap_box(bitmaps, 35.0)``."""
    ink = [bitmap for bitmap in bitmaps if bitmap.pixels.size]
    left = min([0] + [bitmap.x for bitmap in ink]) - 6
    top = min([0] + [bitmap.y for bitmap in ink]) - 6
    right = (
        max(
            [math.ceil(advance)] + [bitmap.x + bitmap.pixels.shape[1] for bitmap in ink]
        )
        + 6
    )
    bottom = max([0] + [bitmap.y + bitmap.pixels.shape[0] for bitmap in ink]) + 6
    return left, top, right, bottom


def cluster_masks(bitmaps: list[InkBitmap], advance: float) -> dict[int, np.ndarray]:
    """Group marks and ligature ink without reshaping substrings; e.g. ``cluster_masks(bitmaps, 35)``."""
    left, top, right, bottom = bitmap_box(bitmaps, advance)
    masks = {
        bitmap.cluster: np.zeros((bottom - top, right - left), np.uint8)
        for bitmap in bitmaps
    }
    for bitmap in bitmaps:
        height, width = bitmap.pixels.shape
        x, y = bitmap.x - left, bitmap.y - top
        target = masks[bitmap.cluster][y : y + height, x : x + width]
        np.maximum(target, bitmap.pixels, out=target)
    return dict(sorted(masks.items()))
