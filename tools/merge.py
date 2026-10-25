#!/usr/bin/env python3
"""Build one Talha Mono font: the pen's letters merged into Monaspace Radon.

python merge.py <upstream.otf> <out.otf> [--style Regular|Bold|Italic|"Bold Italic"]
                [--wide] [--text] [--cell N]

Redrawn with the pen: a–z, A–Z, figures, the extra Latin letters, every
precomposed accented letter and the combining marks (which gain real mark
positioning and the GDEF "mark" class Radon lacks), punctuation, code
symbols and ligatures, and the opt-in ornament. Radon's own: box drawing,
braille, blocks and the remaining symbols (rescaled to the cell), and the
OpenType features, extended here.

Each step lives in its own module and runs in this order. The order matters:
some steps measure glyphs that earlier steps have already replaced.
"""

import sys

from fontTools.ttLib import TTFont

import pen
from accents import place_case_marks, place_marks, place_precomposed
from build_options import BuildOptions, configure_pen, parse_args
from build_state import BuildState
from cell import rescale_cell
from context_spacing import add_context_spacing
from glyph_table import glyph_table
from glyph_writer import GlyphWriter
from gsub_features import merge_into_liga, stylistic_set_lookups
from healing import heal_composites, heal_texture
from mark_positioning import position_marks, set_gdef_classes
from naming import name_font
from place_letters import place_letters
from place_ornaments import place_ornaments
from place_symbols import place_symbols
from zones import set_zones

VERSION = "1.0.0-beta.7"


def start(opts: BuildOptions) -> BuildState:
    """Radon, rescaled to the cell, with the pen set up for this style."""
    configure_pen(opts)
    font = TTFont(opts.src)
    rescale_cell(font, opts.src, opts.cell)
    pen.ADV = opts.cell
    writer = GlyphWriter(font, opts.cell)
    drawings = glyph_table(writer.has, opts.italic)
    return BuildState(opts, font, writer, drawings)


def draw(state: BuildState) -> None:
    """Every pen-drawn glyph, then its positioning and hinting data."""
    stylistic_sets = stylistic_set_lookups(state.font)
    place_letters(state)
    place_symbols(state)
    place_ornaments(state)
    heal_texture(state)
    place_precomposed(state)
    heal_composites(state)
    place_marks(state)
    place_case_marks(state)
    add_context_spacing(state)
    position_marks(state)
    # Ligatures on by default (roadmap E2, decision 2026-10-16): Radon keeps
    # most of them behind ss01-ss10; they move into liga, so they need no
    # feature flag and -liga still turns every one of them off. Texture
    # healing stays in calt.
    merge_into_liga(state.font, stylistic_sets)
    set_gdef_classes(state)
    set_zones(state)


def main(argv: list[str]) -> None:
    opts = parse_args(argv)
    state = start(opts)
    draw(state)
    name_font(state.font, opts, VERSION)
    state.font.save(opts.out)
    print(
        f"{opts.out}: replaced {len(state.replaced)} glyphs ({len(state.placed)} base,"
        f" {len(state.mark_anchors)} marks), {len(state.pen_glyphs)}"
        " punctuation/symbols/ligatures"
    )


if __name__ == "__main__":
    main(sys.argv[1:])
