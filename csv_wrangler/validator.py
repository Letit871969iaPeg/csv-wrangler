"""Column-level validation for CSV rows using a simple rule DSL."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


class ValidationError(Exception):
    """Raised when one or more rows fail validation."""

    def __init__(self, failures: list[dict[str, Any]]) -> None:
        self.failures = failures
        summary = f"{len(failures)} validation failure(s)"
        super().__init__(summary)


@dataclass
class ColumnSpec:
    """Validation specification for a single column."""

    name: str
    required: bool = True
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    allowed_values: list[str] = field(default_factory=list)

    def validate(self, value: str | None) -> list[str]:
        """Return a list of error messages for *value* (empty means valid)."""
        errors: list[str] = []

        if value is None or value == "":
            if self.required:
                errors.append(f"column '{self.name}' is required but missing or empty")
            return errors

        if self.pattern and not re.fullmatch(self.pattern, value):
            errors.append(
                f"column '{self.name}' value {value!r} does not match pattern {self.pattern!r}"
            )

        if self.min_length is not None and len(value) < self.min_length:
            errors.append(
                f"column '{self.name}' value {value!r} is shorter than min_length {self.min_length}"
            )

        if self.max_length is not None and len(value) > self.max_length:
            errors.append(
                f"column '{self.name}' value {value!r} exceeds max_length {self.max_length}"
            )

        if self.allowed_values and value not in self.allowed_values:
            errors.append(
                f"column '{self.name}' value {value!r} not in allowed values {self.allowed_values}"
            )

        return errors


def validate_rows(
    rows: list[dict[str, str]],
    specs: list[ColumnSpec],
    *,
    raise_on_failure: bool = True,
) -> list[dict[str, Any]]:
    """Validate *rows* against *specs*.

    Returns a list of failure dicts ``{row_index, column, errors}``.
    Raises :class:`ValidationError` when *raise_on_failure* is True and
    there are failures.
    """
    failures: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        for spec in specs:
            value = row.get(spec.name)
            errors = spec.validate(value)
            if errors:
                failures.append(
                    {"row_index": row_index, "column": spec.name, "errors": errors}
                )

    if raise_on_failure and failures:
        raise ValidationError(failures)

    return failures
