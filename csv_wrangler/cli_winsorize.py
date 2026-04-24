"""CLI sub-command: winsorize — clamp numeric outliers at given percentiles."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterator

from csv_wrangler.winsorizer import WinsorizeError, WinsorizeSpec, winsorize_rows


def _iter_csv(path: str) -> Iterator[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def _parse_specs(raw: list[str]) -> list[WinsorizeSpec]:
    """Parse strings like ``score``, ``score:0.05:0.95``, or ``score::0.9``."""
    specs: list[WinsorizeSpec] = []
    for token in raw:
        parts = token.split(":")
        column = parts[0]
        lower = float(parts[1]) if len(parts) > 1 and parts[1] else 0.05
        upper = float(parts[2]) if len(parts) > 2 and parts[2] else 0.95
        try:
            specs.append(WinsorizeSpec(column=column, lower=lower, upper=upper))
        except WinsorizeError as exc:
            raise SystemExit(f"Invalid winsorize spec '{token}': {exc}") from exc
    return specs


def add_winsorize_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "winsorize",
        help="Clamp numeric outliers at given percentiles.",
    )
    p.add_argument("input", help="Input CSV file (use - for stdin).")
    p.add_argument(
        "--col",
        dest="cols",
        metavar="COL[:LOWER[:UPPER]]",
        action="append",
        default=[],
        required=True,
        help="Column to winsorize, optionally with lower/upper percentiles (default 0.05/0.95).",
    )
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default stdout).")
    p.add_argument("--quiet", action="store_true", help="Suppress summary output.")
    p.set_defaults(func=_run_winsorize)


def _run_winsorize(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.cols)
    except SystemExit:
        raise

    if args.input == "-":
        reader = csv.DictReader(sys.stdin)
        rows = list(reader)
    else:
        rows = list(_iter_csv(args.input))

    if not rows:
        if not args.quiet:
            print("No rows to process.", file=sys.stderr)
        return 0

    try:
        out_rows, result = winsorize_rows(rows, specs)
    except WinsorizeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    fieldnames = list(out_rows[0].keys()) if out_rows else []
    if args.output == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out_rows)

    if not args.quiet:
        print(str(result), file=sys.stderr)

    return 0
