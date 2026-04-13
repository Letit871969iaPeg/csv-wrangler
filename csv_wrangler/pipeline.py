"""Pipeline: orchestrate parsing, validation, execution, and reporting."""

from __future__ import annotations

import csv
import io
from typing import Iterable, Iterator, List, Optional

from .executor import ExecutionError, apply_rules
from .parser import ParseError, parse_rules
from .reporter import Report, RuleResult
from .schema import SchemaError, load_schema
from .validator import ValidationError, validate_rows


class PipelineError(Exception):  # noqa: D101
    pass


class PipelineConfig:
    """Holds all settings needed to run a pipeline."""

    def __init__(
        self,
        rules_path: str,
        schema_path: Optional[str] = None,
        delimiter: str = ",",
        encoding: str = "utf-8",
        skip_invalid: bool = False,
    ) -> None:
        self.rules_path = rules_path
        self.schema_path = schema_path
        self.delimiter = delimiter
        self.encoding = encoding
        self.skip_invalid = skip_invalid


def _iter_rows(source: io.TextIOBase, delimiter: str) -> Iterator[dict]:
    reader = csv.DictReader(source, delimiter=delimiter)
    for row in reader:
        yield dict(row)


def run_pipeline(
    source: io.TextIOBase,
    destination: io.TextIOBase,
    config: PipelineConfig,
) -> Report:
    """Execute the full CSV-wrangler pipeline and return a Report."""
    report = Report()

    # 1. Parse rules
    try:
        with open(config.rules_path, encoding=config.encoding) as fh:
            rules_text = fh.read()
        rules = parse_rules(rules_text)
    except (ParseError, OSError) as exc:
        raise PipelineError(f"Failed to load rules: {exc}") from exc

    # 2. Optionally load schema
    specs = None
    if config.schema_path:
        try:
            specs = load_schema(config.schema_path)
        except (SchemaError, OSError) as exc:
            raise PipelineError(f"Failed to load schema: {exc}") from exc

    rows: List[dict] = list(_iter_rows(source, config.delimiter))

    # 3. Validate (if schema provided)
    if specs is not None:
        try:
            validate_rows(rows, specs)
            report.add(RuleResult(rule="schema-validation", status="ok"))
        except ValidationError as exc:
            report.add(RuleResult(rule="schema-validation", status="error", message=str(exc)))
            if not config.skip_invalid:
                return report

    # 4. Apply rules row by row
    output_rows: List[dict] = []
    for idx, row in enumerate(rows):
        try:
            transformed = apply_rules(row, rules)
            output_rows.append(transformed)
        except ExecutionError as exc:
            report.add(RuleResult(rule="execution", status="error", message=f"row {idx}: {exc}"))
            if not config.skip_invalid:
                return report

    for rule in rules:
        report.add(RuleResult(rule=repr(rule), status="ok"))

    # 5. Write output
    if output_rows:
        writer = csv.DictWriter(
            destination,
            fieldnames=list(output_rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    return report
