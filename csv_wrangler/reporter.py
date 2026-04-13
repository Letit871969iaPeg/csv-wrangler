"""Summary reporting for CSV wrangling operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RuleResult:
    """Outcome of applying a single rule."""
    rule_type: str
    description: str
    rows_affected: int
    skipped: bool = False
    error: Optional[str] = None

    def __str__(self) -> str:
        status = "SKIP" if self.skipped else ("ERROR" if self.error else "OK")
        parts = [f"[{status}] {self.rule_type}: {self.description}"]
        if not self.skipped and not self.error:
            parts.append(f"({self.rows_affected} row(s) affected)")
        if self.error:
            parts.append(f"— {self.error}")
        return " ".join(parts)


@dataclass
class Report:
    """Aggregated report for a full wrangling run."""
    input_rows: int = 0
    output_rows: int = 0
    results: List[RuleResult] = field(default_factory=list)

    def add(self, result: RuleResult) -> None:
        self.results.append(result)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    def summary(self) -> str:
        lines = [
            f"Input rows : {self.input_rows}",
            f"Output rows: {self.output_rows}",
            f"Rules run  : {len(self.results)}",
            f"Errors     : {self.error_count}",
            f"Skipped    : {self.skipped_count}",
            "",
        ]
        for result in self.results:
            lines.append(f"  {result}")
        return "\n".join(lines)

    def print_summary(self) -> None:
        print(self.summary())


def build_rule_result(
    rule_type: str,
    description: str,
    rows_before: int,
    rows_after: int,
    error: Optional[str] = None,
    skipped: bool = False,
) -> RuleResult:
    """Convenience factory that computes rows_affected from before/after counts."""
    affected = abs(rows_before - rows_after) if not skipped and not error else 0
    return RuleResult(
        rule_type=rule_type,
        description=description,
        rows_affected=affected,
        skipped=skipped,
        error=error,
    )
