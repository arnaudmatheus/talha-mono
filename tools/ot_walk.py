"""Walk OpenType tables, including class-based and extension lookup records."""

from collections.abc import Iterable, Iterator

from fontTools.ttLib.tables.otBase import BaseTable


def table_children(table: BaseTable) -> list[BaseTable]:
    """Direct OpenType child tables; e.g. ``table_children(lookup)``."""
    values = [
        getattr(table, converter.name, None) for converter in table.getConverters()
    ]
    return [
        child
        for value in values
        for child in (value if isinstance(value, list) else [value])
        if isinstance(child, BaseTable)
    ]


def tables_under(roots: Iterable[BaseTable]) -> Iterator[BaseTable]:
    """Visit nested records once, without assuming a context format; e.g. ``tables_under([lookup])``."""
    pending = list(roots)
    seen: set[int] = set()
    while pending:
        table = pending.pop()
        if id(table) in seen:
            continue
        seen.add(id(table))
        yield table
        pending.extend(table_children(table))
