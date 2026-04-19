"""CLI subcommand: condense multiple columns into one."""
from __future__ import annotations
import argparse
import csv
import sys
from csv_wrangler.condenser import CondenserError, CondenserSpec, condense_rows


def add_condense_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "condense",
        help="Merge multiple columns into a single destination column.",
    )
    p.add_argument("input", help="Input CSV file (use - for stdin)")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout)")
    p.add_argument("-c", "--columns", required=True, nargs="+", metavar="COL",
                   help="Source columns to condense")
    p.add_argument("-d", "--dest", required=True, help="Destination column name")
    p.add_argument("--delimiter", default=" ", help="Value delimiter (default: space)")
    p.add_argument("--keep-sources", action="store_true",
                   help="Keep source columns in output")
    p.set_defaults(func=_run_condense)


def _iter_csv(path: str) -> list[dict[str, str]]:
    opener = open(path, newline="") if path != "-" else sys.stdin
    with opener as fh:
        return list(csv.DictReader(fh))


def _run_condense(args: argparse.Namespace) -> int:
    try:
        spec = CondenserSpec(
            columns=args.columns,
            dest=args.dest,
            delimiter=args.delimiter,
            drop_sources=not args.keep_sources,
        )
    except CondenserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows = _iter_csv(args.input)
    if not rows:
        return 0

    out_rows, result = condense_rows(rows, spec)
    fieldnames = list(out_rows[0].keys()) if out_rows else []

    opener = open(args.output, "w", newline="") if args.output != "-" else sys.stdout
    with opener as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    if result.skipped_rows:
        print(f"warning: {result.skipped_rows} row(s) skipped (missing columns)",
              file=sys.stderr)
    return 0
