"""DSL parser for csv-wrangler transformation rules."""

import re
from dataclasses import dataclass
from typing import List, Optional


SUPPORTED_OPS = {"rename", "drop", "filter", "transform", "validate"}


@dataclass
class Rule:
    """Represents a single parsed DSL rule."""

    operation: str
    column: str
    value: Optional[str] = None
    expression: Optional[str] = None

    def __repr__(self) -> str:
        parts = [f"op={self.operation!r}", f"col={self.column!r}"]
        if self.value is not None:
            parts.append(f"value={self.value!r}")
        if self.expression is not None:
            parts.append(f"expr={self.expression!r}")
        return f"Rule({', '.join(parts)})"


class ParseError(Exception):
    """Raised when a DSL rule cannot be parsed."""


def parse_rule(line: str) -> Rule:
    """
    Parse a single DSL rule line into a Rule object.

    Supported syntax examples:
        rename old_name -> new_name
        drop column_name
        filter age > 18
        transform price * 1.1
        validate email ~= ^[\\w.+-]+@[\\w-]+\\.[\\w.]+$
    """
    line = line.strip()
    if not line or line.startswith("#"):
        raise ParseError(f"Empty or comment line: {line!r}")

    parts = line.split(None, 1)
    if len(parts) < 2:
        raise ParseError(f"Rule must have at least operation and column: {line!r}")

    operation, rest = parts[0].lower(), parts[1].strip()

    if operation not in SUPPORTED_OPS:
        raise ParseError(
            f"Unknown operation {operation!r}. Supported: {sorted(SUPPORTED_OPS)}"
        )

    if operation == "rename":
        match = re.match(r"^(\S+)\s*->\s*(\S+)$", rest)
        if not match:
            raise ParseError(f"rename expects 'old_name -> new_name', got: {rest!r}")
        return Rule(operation=operation, column=match.group(1), value=match.group(2))

    if operation == "drop":
        return Rule(operation=operation, column=rest)

    # filter, transform, validate: column + expression
    expr_parts = rest.split(None, 1)
    if len(expr_parts) < 2:
        raise ParseError(f"{operation} expects 'column expression', got: {rest!r}")
    return Rule(operation=operation, column=expr_parts[0], expression=expr_parts[1])


def parse_rules(text: str) -> List[Rule]:
    """Parse a multi-line DSL string into a list of Rule objects."""
    rules: List[Rule] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            rules.append(parse_rule(stripped))
        except ParseError as exc:
            raise ParseError(f"Line {lineno}: {exc}") from exc
    return rules
