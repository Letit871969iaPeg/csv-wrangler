"""CLI sub-command: fill — fill missing values in CSV columns."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List

from csv_wrangler.filler import FillError, FillSpec, fill_rows


def _parse_specs(raw: List[str]) -> list[FillSpec]:
    """Parse specs of the form ``column:strategy[:value]``."""
    specs: list[FillSpec] = []
    for item in raw:
        parts = item.split(":")
        if len(parts) < 2:
            raise FillError(
                f"Invalid fill spec {item!r}. Expected column:strategy[:value]"
            )
        column = parts[0]
        strategy = parts[1]
        value = parts[2] if len(parts) >= 3 else ""
        specs.append(FillSpec(column=column, strategy=strategy, value=value))
    return specs


def add_fill_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("fill", help="Fill missing values in CSV columns")
    p.add_argument("input", help="Input CSV file (use '-' for stdin)")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout)")
    p.add_argument(
        "-s",
        "--spec",
        dest="specs",
        action="append",
        default=[],
        metavar="COL:STRATEGY[:VALUE]",
        help="Fill spec, e.g. age:constant:0 or city:forward. Repeatable.",
    )
    p.set_defaults(func=_run_fill)


def _run_fill(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except FillError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    in_fh = sys.stdin if args.input == "-" else open(args.input, newline="", encoding="utf-8")
    out_fh = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")

    try:
        reader = csv.DictReader(in_fh)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

        try:
            filled, summary = fill_rows(rows, specs)
        except FillError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        writer = csv.DictWriter(out_fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filled)

        print(summary, file=sys.stderr)
        return 0
    finally:
        if in_fh is not sys.stdin:
            in_fh.close()
        if out_fh is not sys.stdout:
            out_fh.close()
