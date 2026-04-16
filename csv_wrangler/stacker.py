"""Vertical stacking (unpivot/melt) of CSV columns into key-value rows."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class StackError(Exception):
    pass


@dataclass
class StackResult:
    input_rows: int = 0
    output_rows: int = 0
    value_columns: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        cols = ", ".join(self.value_columns) if self.value_columns else "(none)"
        return (
            f"Stack: {self.input_rows} input rows → {self.output_rows} output rows "
            f"| value columns: {cols}"
        )


def stack_rows(
    rows: Iterable[dict[str, str]],
    id_columns: list[str],
    key_column: str = "key",
    value_column: str = "value",
) -> tuple[Iterator[dict[str, str]], StackResult]:
    """Melt *value_columns* (all columns not in *id_columns*) into key/value rows."""
    collected = list(rows)
    if not collected:
        return iter([]), StackResult()

    all_cols = list(collected[0].keys())
    missing = [c for c in id_columns if c not in all_cols]
    if missing:
        raise StackError(f"id columns not found: {missing}")

    value_cols = [c for c in all_cols if c not in id_columns]
    if not value_cols:
        raise StackError("No value columns remain after excluding id columns.")

    result = StackResult(
        input_rows=len(collected),
        output_rows=len(collected) * len(value_cols),
        value_columns=value_cols,
    )

    def _iter() -> Iterator[dict[str, str]]:
        for row in collected:
            for vc in value_cols:
                new_row = {c: row[c] for c in id_columns}
                new_row[key_column] = vc
                new_row[value_column] = row.get(vc, "")
                yield new_row

    return _iter(), result
