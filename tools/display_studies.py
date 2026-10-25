"""Two display compositions made from Talha's existing titl/swsh and ornaments."""

from atlas_svg import BLUE, GOLD, INK, MUTED, PAPER, RED, OutlineFont, Sheet


def corner_leaves(sheet: Sheet, regular: OutlineFont) -> None:
    for character, x, y in (
        ("🙐", 130, 240),
        ("🙒", 1080, 240),
        ("🙑", 130, 1290),
        ("🙓", 1080, 1290),
    ):
        sheet.glyph(regular, character, (x, y, 190, 190), GOLD)


def title_frame(sheet: Sheet, regular: OutlineFont) -> None:
    sheet.rect(70, 175, 1260, 1405, INK)
    for inset in (95, 108):
        top, bottom = 200 + inset - 95, 1555 - inset + 95
        for x1, y1, x2, y2 in (
            (inset, top, 1400 - inset, top),
            (inset, bottom, 1400 - inset, bottom),
            (inset, top, inset, bottom),
            (1400 - inset, top, 1400 - inset, bottom),
        ):
            sheet.line(x1, y1, x2, y2, GOLD)
    corner_leaves(sheet, regular)
    sheet.glyph(regular, "❨", (135, 560, 140, 590), GOLD)
    sheet.glyph(regular, "❩", (1125, 560, 140, 590), GOLD)


def mixed_title(sheet: Sheet, regular: OutlineFont, italic: OutlineFont) -> None:
    sheet.text(regular, "OURO", 700, 760, 340, GOLD, "titl", center=True)
    size = 270
    start = 700 - regular.width("Preto", size) / 2
    sheet.text(regular, "P", start, 1045, size, PAPER, "swsh")
    sheet.text(italic, "reto", start + regular.width("P", size), 1045, size, PAPER)
    sheet.text(italic, "Da pena à pedra", 700, 1170, 52, GOLD, center=True)


def cover_caption(sheet: Sheet) -> None:
    sheet.label(
        "Carved capitals · one flourished initial · paired cartelas · corner leaves",
        700,
        1660,
        20,
        INK,
        "middle",
    )
    sheet.label(
        "October display pilot · letter-specific swashes and a scalloped scroll leaf.",
        700,
        1700,
        17,
        MUTED,
        "middle",
    )
    sheet.label("FOLHA I", 700, 1760, 15, BLUE, "middle")


def cover_study(regular: OutlineFont, italic: OutlineFont) -> Sheet:
    """Build a title-page treatment; e.g. ``cover_study(regular, italic)``."""
    sheet = Sheet("Talha Mono display study: Ouro Preto title page")
    sheet.label("TALHA MONO", 70, 75, 18, BLUE)
    sheet.label("DISPLAY STUDY  /  I", 1330, 75, 18, BLUE, "end")
    title_frame(sheet, regular)
    sheet.text(
        regular, "CADERNO DAS LETRAS", 700, 425, 40, PAPER, tracking=4, center=True
    )
    sheet.label("MINAS GERAIS", 700, 475, 17, GOLD, "middle")
    mixed_title(sheet, regular, italic)
    sheet.text(regular, "❧", 700, 1300, 110, GOLD, center=True)
    sheet.text(regular, "1722  ·  2026", 700, 1430, 34, PAPER, center=True)
    cover_caption(sheet)
    return sheet


def chapter_heading(sheet: Sheet, regular: OutlineFont, italic: OutlineFont) -> None:
    sheet.text(regular, "❨", 90, 330, 180, BLUE)
    sheet.text(regular, "01", 200, 297, 55, BLUE)
    sheet.text(regular, "❩", 290, 330, 180, BLUE)
    sheet.text(regular, "DA PENA", 95, 490, 153, INK, "titl")
    sheet.text(italic, "à pedra", 100, 675, 160, RED)
    sheet.glyph(regular, "🙒", (1000, 335, 225, 270), BLUE)
    sheet.line(100, 750, 1300, 750, GOLD)


def initial_paragraph(sheet: Sheet, regular: OutlineFont) -> None:
    sheet.glyph(regular, "A", (85, 815, 220, 255), RED, "swsh")
    lines = [
        ("letra começa no gesto da mão.", 350, 865),
        ("A curva encontra a fibra, a pena", 350, 920),
        ("deixa o seu peso sobre o papel.", 350, 975),
        ("Na pedra, o mesmo movimento ganha outra duração.", 105, 1120),
        ("Entre a linha escrita e a talha, ficam o ritmo,", 105, 1175),
        ("o intervalo e a luz que atravessa cada forma.", 105, 1230),
    ]
    for text, x, baseline in lines:
        sheet.text(regular, text, x, baseline, 40)


def chapter_recipe(sheet: Sheet) -> None:
    sheet.label("DISPLAY RECIPE", 100, 1530, 16, BLUE)
    sheet.label(
        "titl for the heading · swsh on the initial A · ordinary Regular for the paragraph",
        100,
        1580,
        19,
        INK,
    )
    sheet.label(
        "One ornament family per passage. Give flourishes their own margin and line space.",
        100,
        1620,
        18,
    )
    sheet.label(
        "Original specimen text · heading and initial are composed separately",
        100,
        1735,
        16,
    )


def chapter_footer(sheet: Sheet, regular: OutlineFont, italic: OutlineFont) -> None:
    sheet.text(regular, "☙", 275, 1370, 100, BLUE, center=True)
    sheet.text(italic, "A curva guarda o gesto.", 700, 1360, 42, BLUE, center=True)
    sheet.text(regular, "❧", 1125, 1370, 100, BLUE, center=True)
    sheet.line(100, 1450, 1300, 1450, GOLD)
    chapter_recipe(sheet)
    sheet.text(regular, "01", 1290, 1740, 30, BLUE, center=True)


def chapter_study(regular: OutlineFont, italic: OutlineFont) -> Sheet:
    """Build a chapter opening; e.g. ``chapter_study(regular, italic)``."""
    sheet = Sheet("Talha Mono display study: a chapter opening")
    sheet.label("TALHA MONO  /  CADERNO DAS LETRAS", 100, 80, 17, BLUE)
    sheet.label("DISPLAY STUDY  /  II", 1300, 80, 17, BLUE, "end")
    sheet.line(100, 120, 1300, 120, GOLD)
    chapter_heading(sheet, regular, italic)
    initial_paragraph(sheet, regular)
    chapter_footer(sheet, regular, italic)
    return sheet
