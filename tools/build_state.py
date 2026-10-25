"""What the build steps share while one font is made."""

from dataclasses import dataclass, field
from typing import NamedTuple

from fontTools.ttLib import TTFont

from build_options import BuildOptions
from glyph_table import Letter
from glyph_writer import GlyphWriter
from pen_types import Point


class Composition(NamedTuple):
    base: str
    marks: tuple[int, ...]


class ContextForm(NamedTuple):
    base: str
    scale: float
    shift: float


@dataclass
class BuildState:
    """One font in the making. Each step in merge.py reads and extends it.

    placed: base glyph -> its x offset in the cell (accented forms reuse it).
    mark_anchors: combining mark -> (kind, its anchor in the final glyph).
    compositions: every redrawn precomposed letter -> its drawing recipe.
    context_forms: alternate -> its default and final-coordinate x transform.
    """

    opts: BuildOptions
    font: TTFont
    writer: GlyphWriter
    glyphs: dict[str, Letter]
    placed: dict[str, float] = field(default_factory=dict)
    replaced: list[str] = field(default_factory=list)
    pen_glyphs: list[str] = field(default_factory=list)
    mark_anchors: dict[str, tuple[str, Point]] = field(default_factory=dict)
    compositions: dict[str, Composition] = field(default_factory=dict)
    context_forms: dict[str, ContextForm] = field(default_factory=dict)

    @property
    def nib(self) -> tuple[float, float]:
        return self.opts.nib
