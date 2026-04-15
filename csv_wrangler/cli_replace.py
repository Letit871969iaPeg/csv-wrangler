"""CLI sub-command: replace — find-and-replace values in CSV columns."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List

from csv_wrangler.replacer import ReplaceError, ReplaceSpec, replace_rows


def _parse_specs(raw: List[str]) -> List[ReplaceSpec]:
    """Parse specs of the form ``column:find:replacement`` or
    ``column:find:replacement:whole``.

    Append ``:whole`` (case-insensitive) to enable whole-cell matching.
    """
    specs: List[ReplaceSpec] = []
    for token in raw:
        parts = token.split(":")
        if len(parts) < 3:
            raise ReplaceError(
                f"Invalid replace spec {token!r}. "
                "Expected column:find:replacement[:whole]"
            )
        column, find, replacement = parts[0], parts[1], parts[2]
        whole_cell = len(parts) >= 4 and parts[3].lower() == "whole"
        specs.append(ReplaceSpec(column=column, find=find, replacement=replacement, whole_cell=whole_cell))
    return specs


def add_replace_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "replace",
        help="Find-and-replace string values in one or more columns.",
    )
    p.add_argument("input", nargs="?", default="-", help="Input CSV file (default: stdin)")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout)")
    p.add_argument(
        "-s",
        "--spec",
        dest="specs",
        metavar="SPEC",
        action="append",
        required=True,
        help="Replacement spec: column:find:replacement[:whole]",
    )
    p.set_defaults(func=_run_replace)


def _iter_csv(path: str):
    if path == "-":
        reader = csv.DictReader(sys.stdin)
        yield from reader
    else:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            yield from reader


def _run_replace(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except ReplaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows = list(_iter_csv(args.input))
    if not rows:
        return 0

    try:
        out_rows, result = replace_rows(rows, specs)
    except ReplaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
            writer.writeheader()
            writer.writerows(out_rows)

    if result.skipped_columns:
        print(
            f"warning: columns not found and skipped: {result.skipped_columns}",
            file=sys.stderr,
        )

    return 0
