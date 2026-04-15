"""CLI sub-command: transpose — flip CSV rows and columns."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterator

from csv_wrangler.transposer import TransposeError, transpose_rows


def add_transpose_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "transpose",
        help="Flip rows and columns in a CSV file.",
    )
    p.add_argument("input", help="Input CSV file (use '-' for stdin).")
    p.add_argument(
        "-o", "--output",
        default="-",
        help="Output CSV file (default: stdout).",
    )
    p.add_argument(
        "--index-column",
        default="field",
        metavar="NAME",
        help="Name for the column that holds original field names (default: 'field').",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output on stderr.",
    )
    p.set_defaults(func=_run_transpose)


def _iter_csv(path: str) -> Iterator[dict[str, str]]:
    fh = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        reader = csv.DictReader(fh)
        yield from reader
    finally:
        if path != "-":
            fh.close()


def _run_transpose(args: argparse.Namespace) -> int:
    try:
        result = transpose_rows(
            _iter_csv(args.input),
            index_column=args.index_column,
        )
    except TransposeError as exc:
        print(f"transpose error: {exc}", file=sys.stderr)
        return 1

    if not result.output_rows:
        if not args.quiet:
            print("transpose: no rows to write.", file=sys.stderr)
        return 0

    out_headers = list(result.output_rows[0].keys())

    if args.output == "-":
        out_fh = sys.stdout
        close_out = False
    else:
        out_fh = open(args.output, "w", newline="", encoding="utf-8")  # type: ignore[assignment]
        close_out = True

    try:
        writer = csv.DictWriter(out_fh, fieldnames=out_headers)
        writer.writeheader()
        writer.writerows(result.output_rows)
    finally:
        if close_out:
            out_fh.close()

    if not args.quiet:
        print(
            f"transpose: {result.rows_in} row(s) x {result.columns_in} col(s) "
            f"→ {result.rows_out} row(s) x {result.columns_out} col(s)",
            file=sys.stderr,
        )
    return 0
