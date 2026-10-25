"""Small SVG drawing surface for the source atlas and display studies.

Talha text is exported from the selected OTF's actual outlines, including
its single-substitution display features. No installed font is required.
"""

import base64
import io
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image

from pen_types import Stroke

PAPER = "#F3EEE2"
INK = "#152B45"
BLUE = "#355F88"
RED = "#AD492F"
GOLD = "#C7A267"
MUTED = "#596776"
RULE = "#C9C5B8"


class OutlineFont:
    """Read outline text from one OTF; e.g. ``OutlineFont(path).width('OURO', 80)``."""

    def __init__(self, path: Path) -> None:
        self.font = TTFont(path)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def name(self, character: str, feature: str = "") -> str:
        if ord(character) not in self.cmap:
            raise ValueError(f"{character!r}: expected a character present in the OTF")
        name = self.cmap[ord(character)]
        if not feature:
            return name
        records = self.font["GSUB"].table.FeatureList.FeatureRecord
        selected = [r for r in records if r.FeatureTag == feature]
        if not selected:
            raise ValueError(f"{feature!r}: expected an existing display feature")
        for index in selected[0].Feature.LookupListIndex:
            for table in self.font["GSUB"].table.LookupList.Lookup[index].SubTable:
                name = table.mapping.get(name, name)
        return name

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        advances = [self.font["hmtx"][self.name(c)][0] for c in text]
        return sum(advances) * size / self.upm + max(0, len(text) - 1) * tracking

    def outline(self, character: str, feature: str = "") -> str:
        drawing = SVGPathPen(self.glyphs)
        self.glyphs[self.name(character, feature)].draw(drawing)
        return drawing.getCommands()

    def bounds(self, character: str, feature: str = "") -> tuple[float, ...]:
        drawing = BoundsPen(self.glyphs)
        self.glyphs[self.name(character, feature)].draw(drawing)
        if drawing.bounds is None:
            raise ValueError(f"{character!r}: expected a glyph with visible ink")
        return drawing.bounds


@dataclass
class Sheet:
    """One self-contained SVG; e.g. ``Sheet('Atlas', 1400, 1800).save(path)``."""

    title: str
    width: int = 1400
    height: int = 1800
    background: str = PAPER
    parts: list[str] = field(default_factory=list)

    def rect(self, x: float, y: float, w: float, h: float, fill: str) -> None:
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
        )

    def line(self, x: float, y: float, x2: float, y2: float, color: str = RULE) -> None:
        self.parts.append(
            f'<path d="M{x},{y} L{x2},{y2}" fill="none" stroke="{color}"/>'
        )

    def label(
        self,
        text: str,
        x: float,
        y: float,
        size: int = 18,
        color: str = MUTED,
        anchor: str = "start",
    ) -> None:
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="DejaVu Sans,sans-serif" '
            f'font-size="{size}" fill="{color}" text-anchor="{anchor}">'
            f"{escape(text)}</text>"
        )

    def text(
        self,
        font: OutlineFont,
        text: str,
        x: float,
        y: float,
        size: float,
        color: str = INK,
        feature: str = "",
        tracking: float = 0,
        center: bool = False,
    ) -> None:
        if center:
            x -= font.width(text, size, tracking) / 2
        scale = size / font.upm
        self.parts.append(f'<g role="img" aria-label="{escape(text, quote=True)}">')
        for character in text:
            self.parts.append(
                f'<path d="{font.outline(character, feature)}" fill="{color}" '
                f'transform="translate({x},{y}) scale({scale}, {-scale})"/>'
            )
            x += self.font_advance(font, character) * scale + tracking
        self.parts.append("</g>")

    @staticmethod
    def font_advance(font: OutlineFont, character: str) -> float:
        return float(font.font["hmtx"][font.name(character)][0])

    def glyph(
        self,
        font: OutlineFont,
        character: str,
        box: tuple[float, ...],
        color: str = GOLD,
        feature: str = "",
    ) -> None:
        x, y, width, height = box
        left, bottom, right, top = font.bounds(character, feature)
        scale = min(width / (right - left), height / (top - bottom))
        tx = x + (width - (right - left) * scale) / 2 - left * scale
        ty = y + (height - (top - bottom) * scale) / 2 + top * scale
        self.parts.append(
            f'<path d="{font.outline(character, feature)}" fill="{color}" '
            f'transform="translate({tx},{ty}) scale({scale}, {-scale})"/>'
        )

    def strokes(
        self,
        strokes: list[Stroke],
        x: float,
        baseline: float,
        scale: float,
        color: str = RED,
    ) -> None:
        for points in strokes:
            coordinates = " ".join(f"{a:.3f},{b:.3f}" for a, b in points)
            self.parts.append(
                f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
                f'stroke-width="2" vector-effect="non-scaling-stroke" '
                f'transform="translate({x},{baseline}) scale({scale},{-scale})"/>'
            )

    def photo(
        self,
        path: Path,
        box: tuple[int, int, int, int],
        crop: tuple[int, int, int, int] | None = None,
    ) -> None:
        x, y, width, height = box
        with Image.open(path) as source:
            picture = source.crop(crop) if crop else source.copy()
        picture.thumbnail((width * 2, height * 2))
        buffer = io.BytesIO()
        picture.convert("RGB").save(buffer, format="JPEG", quality=90)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        self.parts.append(
            f'<image x="{x}" y="{y}" width="{width}" height="{height}" '
            f'href="data:image/jpeg;base64,{encoded}" preserveAspectRatio="xMidYMid meet"/>'
        )

    def save(self, path: Path) -> None:
        description = "Historical sources and Talha Mono outlines. Credits: README.md."
        content = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img">'
            f"<title>{escape(self.title)}</title><desc>{description}</desc>"
            f'<rect width="100%" height="100%" fill="{self.background}"/>'
            + "".join(self.parts)
            + "</svg>\n"
        )
        path.write_text(content)
