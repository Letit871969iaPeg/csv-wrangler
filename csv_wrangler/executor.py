"""Executor: applies parsed rules to CSV rows."""

from typing import Any, Callable, Dict, List, Optional
from csv_wrangler.parser import Rule


class ExecutionError(Exception):
    """Raised when a rule cannot be applied to a row."""


# Built-in transform functions available in the DSL
_BUILTIN_TRANSFORMS: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "title": str.title,
}


def apply_rule(rule: Rule, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Apply a single rule to a row dict.

    Returns the (possibly modified) row, or None if the row should be dropped.
    """
    if rule.action == "rename":
        src, dst = rule.args
        if src not in row:
            raise ExecutionError(f"rename: column '{src}' not found in row")
        row[dst] = row.pop(src)

    elif rule.action == "drop":
        col = rule.args[0]
        if col not in row:
            raise ExecutionError(f"drop: column '{col}' not found in row")
        del row[col]

    elif rule.action == "filter":
        col, op, value = rule.args
        if col not in row:
            raise ExecutionError(f"filter: column '{col}' not found in row")
        cell = row[col]
        keep = _evaluate_filter(cell, op, value)
        if not keep:
            return None

    elif rule.action == "transform":
        col, func_name = rule.args
        if col not in row:
            raise ExecutionError(f"transform: column '{col}' not found in row")
        if func_name not in _BUILTIN_TRANSFORMS:
            raise ExecutionError(
                f"transform: unknown function '{func_name}'. "
                f"Available: {sorted(_BUILTIN_TRANSFORMS)}"
            )
        row[col] = _BUILTIN_TRANSFORMS[func_name](row[col])

    else:
        raise ExecutionError(f"Unknown action: '{rule.action}'")

    return row


def _evaluate_filter(cell: str, op: str, value: str) -> bool:
    """Evaluate a filter condition."""
    if op == "==":
        return cell == value
    if op == "!=":
        return cell != value
    if op == "contains":
        return value in cell
    if op == "startswith":
        return cell.startswith(value)
    if op == "endswith":
        return cell.endswith(value)
    raise ExecutionError(f"filter: unknown operator '{op}'")


def apply_rules(rules: List[Rule], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply a list of rules to every row, returning surviving rows."""
    result: List[Dict[str, Any]] = []
    for row in rows:
        current = dict(row)  # work on a copy
        for rule in rules:
            current = apply_rule(rule, current)
            if current is None:
                break
        if current is not None:
            result.append(current)
    return result
