#!/usr/bin/env python3
"""Add Nerd Font icons to a Talha Mono build -> "Talha Mono NF".

python nerd.py <talha.otf> <monaspice-nerd.otf> <out.otf>

Without FontForge, the official Nerd Fonts patcher can't run here. MonaspiceRn
Nerd Font (Nerd Fonts' patch of the same Radon) already holds every icon
scaled for this exact cell (2000 UPM, 1240 advance), so the icons are copied
from it: every codepoint it has and Talha Mono lacks. Each icon is redrawn
through a pen, so no CFF subroutine of the source font is carried over."""

import re
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib.tables._c_m_a_p import cmap_format_12

import finish
from pen_types import GlyphSet
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e


def _copy_icon(
    font: TTFont, icons: TTFont, source: str, name: str, glyphs: GlyphSet
) -> None:
    cff = font["CFF "].cff
    td = cff.topDictIndex[0]
    # The icons come from a 1240-unit cell; they follow this font's cell.
    cell = td.Private.defaultWidthX
    ratio = cell / 1240
    width = round(icons["hmtx"][source][0] * ratio)
    pen = T2CharStringPen(None if width == cell else width, glyphs)
    glyphs[source].draw(TransformPen(pen, (ratio, 0, 0, 1, 0, 0)))
    cs = pen.getCharString(private=td.Private, globalSubrs=cff.GlobalSubrs)
    idx = td.CharStrings
    idx.charStringsIndex.append(cs)
    idx.charStrings[name] = len(idx.charStringsIndex) - 1
    font.getGlyphOrder().append(name)
    font["hmtx"][name] = (width, round(icons["hmtx"][source][1] * ratio))


def _icon_glyph_name(source: str, occupied: set[str]) -> str:
    """A unique PostScript-safe name; e.g. ``_icon_glyph_name('cod-add', set())``."""
    stem = re.sub(r"[^A-Za-z0-9_.]", "_", source)
    if not stem or stem[0].isdigit() or stem.startswith("."):
        stem = "nf_" + stem
    name, serial = stem[:63], 0
    while name in occupied:
        serial += 1
        suffix = ".nf" if serial == 1 else f".nf{serial}"
        name = stem[: 63 - len(suffix)] + suffix
    return name


def _copy_missing_icons(font: TTFont, icons: TTFont) -> dict[str, list[int]]:
    cmap = font.getBestCmap()
    glyphs = icons.getGlyphSet()
    have = set(font.getGlyphOrder())
    added: dict[str, list[int]] = {}
    copied: dict[str, str] = {}
    for cp, gname in sorted(icons.getBestCmap().items()):
        if cp in cmap:
            continue
        if gname not in copied:
            name = _icon_glyph_name(gname, have)
            _copy_icon(font, icons, gname, name, glyphs)
            have.add(name)
            copied[gname] = name
            added[name] = []
        added[copied[gname]].append(cp)
    order = font.getGlyphOrder()
    font["CFF "].cff.topDictIndex[0].charset = order
    font.setGlyphOrder(order)
    return added


def _replace_icon_cmaps(font: TTFont, added: dict[str, list[int]]) -> None:
    # Plane-15 Material Design icons need a format 12 subtable.
    full = dict(font.getBestCmap())
    full.update({cp: name for name, cps in added.items() for cp in cps})
    # Radon ships (0,4) and (3,10), and renderers prefer (3,10):
    # every format 12 subtable must get the icons, not only the first.
    if not any(
        t.format == 12 and (t.platformID, t.platEncID) == (3, 10)
        for t in font["cmap"].tables
    ):
        c12 = cmap_format_12(12)
        c12.platformID, c12.platEncID, c12.language = 3, 10, 0
        font["cmap"].tables.append(c12)
    for table in font["cmap"].tables:
        if table.format == 12:
            table.cmap = dict(full)
        elif table.format == 4:
            table.cmap = {cp: g for cp, g in full.items() if cp <= 0xFFFF}


def _rename_icon_records(names: table__n_a_m_e, family: str, ps_family: str) -> None:
    for rec in list(names.names):
        if rec.nameID not in (1, 3, 4, 6, 18):
            continue
        old, new = (
            (ps_family + "-", ps_family + "NF-")
            if rec.nameID in (3, 6)
            else (family, family + " NF")
        )
        names.setName(
            str(rec).replace(old, new),
            rec.nameID,
            rec.platformID,
            rec.platEncID,
            rec.langID,
        )


def _rename_icon_family(font: TTFont) -> None:
    names, cff = font["name"], font["CFF "].cff
    td = cff.topDictIndex[0]
    # The family comes from the font: Wide and Text keep their names.
    family = names.getDebugName(1)
    ps_family = cff.fontNames[0].split("-")[0]
    _rename_icon_records(names, family, ps_family)
    cff.fontNames = [cff.fontNames[0].replace(ps_family + "-", ps_family + "NF-")]
    td.FullName = td.FullName.replace(family, family + " NF")
    td.FamilyName = family + " NF"


def add_icons(font: TTFont, icons: TTFont) -> dict[str, list[int]]:
    """Add missing icons and name the NF family, keeping the letters intact.

    Example: ``added = add_icons(TTFont("talha.otf"), TTFont("icons.otf"))``.
    """
    added = _copy_missing_icons(font, icons)
    _replace_icon_cmaps(font, added)
    _rename_icon_family(font)
    finish.win_metrics(font)  # the icons reach past the letters' bounds
    return added


def main(argv: list[str]) -> None:
    """Build the icon variant; e.g. ``main(["talha.otf", "icons.otf", "nf.otf"])``."""
    src, icons_src, out = argv[:3]
    with TTFont(src) as font, TTFont(icons_src) as icons:
        added = add_icons(font, icons)
        font.save(out)
    print(
        f"{out}: +{len(added)} icon glyphs, {sum(len(v) for v in added.values())} codepoints"
    )


if __name__ == "__main__":
    main(sys.argv[1:])
