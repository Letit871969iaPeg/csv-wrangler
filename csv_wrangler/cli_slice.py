"""CLI sub-command: slice — keep rows in a given index range."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterator

from csv_wrangler.slicer import SliceError, slice_rows


def add_slice_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "slice",
        help="Keep only rows whose 0-based index falls in [start, end).",
    )
    p.add_argument("input", help="Input CSV file (use '-' for stdin).")
    p.add_argument("--start", type=int, default=0, metavar="N",
                   help="First row index to include (default 0).")
    p.add_argument("--end", type=int, default=None, metavar="N",
                   help="One-past-last row index (default: no limit).")
    p.add_argument("-o", "--output", default="-",
                   help="Output CSV file (default: stdout).")
    p.set_defaults(func=_run_slice)


def _iter_csv(path: str) -> Iterator[dict]:
    fh = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        yield from csv.DictReader(fh)
    finally:
        if path != "-":
            fh.close()


def _run_slice(args: argparse.Namespace) -> int:
    try:
        result = slice_rows(_iter_csv(args.input), start=args.start, end=args.end)
    except SliceError as exc:
        print(f"slice error: {exc}", file=sys.stderr)
        return 1

    if not result.rows:
        print("slice: no rows in range", file=sys.stderr)
        return 0

    out_fh = sys.stdout if args.output == "-" else open(
        args.output, "w", newline="", encoding="utf-8"
    )
    try:
        writer = csv.DictWriter(out_fh, fieldnames=list(result.rows[0].keys()))
        writer.writeheader()
        writer.writerows(result.rows)
    finally:
        if args.output != "-":
            out_fh.close()

    print(
        f"slice: kept {result.kept_count}/{result.total_input} rows",
        file=sys.stderr,
    )
    return 0
