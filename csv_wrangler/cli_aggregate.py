"""CLI subcommand: aggregate — compute column statistics."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List

from csv_wrangler.aggregator import AggSpec, AggregateError, aggregate


def add_aggregate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "aggregate",
        help="Compute sum/mean/min/max/count for one or more columns.",
    )
    p.add_argument("source", help="Input CSV file (use '-' for stdin).")
    p.add_argument(
        "--spec",
        dest="specs",
        metavar="COLUMN:OP",
        action="append",
        required=True,
        help="Aggregation spec, e.g. price:sum or qty:mean. Repeatable.",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "csv"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=_run_aggregate)


def _parse_specs(raw: List[str]) -> List[AggSpec]:
    specs: List[AggSpec] = []
    for item in raw:
        parts = item.split(":")
        if len(parts) != 2:
            raise AggregateError(
                f"Invalid spec '{item}'. Expected COLUMN:OP format."
            )
        col, op = parts[0].strip(), parts[1].strip()
        specs.append(AggSpec(column=col, op=op))  # type: ignore[arg-type]
    return specs


def _run_aggregate(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except AggregateError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.source == "-":
            reader = csv.DictReader(sys.stdin)
            rows = list(reader)
        else:
            with open(args.source, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
    except OSError as exc:
        print(f"Error reading '{args.source}': {exc}", file=sys.stderr)
        return 1

    try:
        results = aggregate(rows, specs)
    except AggregateError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["column", "op", "value", "row_count"])
        for r in results:
            writer.writerow([r.spec.column, r.spec.op, r.value, r.row_count])
    else:
        for r in results:
            print(r)

    return 0
