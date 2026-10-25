"""Stable signatures for outline resources and OpenType layout audit records."""

import io

from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otBase import BaseTable

HintSignature = tuple[dict[str, object], list[bytes], list[bytes]]


def cff_hint_signature(font: TTFont) -> HintSignature:
    """Protect shared hint parameters/subroutines independently of metadata; e.g. ``cff_hint_signature(font)``."""
    cff = font["CFF "].cff
    private = cff.topDictIndex[0].Private
    return (
        dict(private.rawDict),
        [sub.bytecode for sub in cff.GlobalSubrs],
        [sub.bytecode for sub in getattr(private, "Subrs", [])],
    )


def layout_signature(table: BaseTable, font: TTFont) -> bytes:
    """Compare layout records without sfnt offset differences; e.g. ``layout_signature(lookup, font)``."""
    output = io.BytesIO()
    table.toXML(XMLWriter(output), font)
    return output.getvalue()
