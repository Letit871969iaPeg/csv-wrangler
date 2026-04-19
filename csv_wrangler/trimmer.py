"""Column value trimmer — removes leading/trailing characters from cell values."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class TrimError(Exception):
    pass


@dataclass
class TrimSpec:
    column: str
    chars: str | None = None  # None → whitespace
    side: str = "both"  # left | right | both

    def __post_init__(self) -> None:
        if not self.column:
            raise TrimError("column must not be empty")
        if self.side not in ("left", "right", "both"):
            raise TrimError(f"side must be left, right, or both; got {self.side!r}")


@dataclass
class TrimResult:
    trimmed_count: int = 0
    skipped_columns: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"trimmed={self.trimmed_count}"]
        if self.skipped_columns:
            parts.append(f"skipped={self.skipped_columns}")
        return f"TrimResult({', '.join(parts)})"


def _trim_value(value: str, spec: TrimSpec) -> str:
    if spec.side == "left":
        return value.lstrip(spec.chars)
    if spec.side == "right":
        return value.rstrip(spec.chars)
    return value.strip(spec.chars)


def trim_rows(
    rows: Iterable[dict[str, str]],
    specs: list[TrimSpec],
) -> tuple[list[dict[str, str]], TrimResult]:
    result = TrimResult()
    output: list[dict[str, str]] = []
    checked: set[str] = set()
    missing: set[str] = set()

    for row in rows:
        if not checked:
            checked = set(row.keys())
            for spec in specs:
                if spec.column not in checked:
                    missing.add(spec.column)
                    result.skipped_columns.append(spec.column)

        new_row = dict(row)
        for spec in specs:
            if spec.column in missing:
                continue
            original = new_row.get(spec.column, "")
            trimmed = _trim_value(original, spec)
            if trimmed != original:
                result.trimmed_count += 1
            new_row[spec.column] = trimmed
        output.append(new_row)

    return output, result
