"""CLI sub-command: clip — clamp numeric column values to [low, high]."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List

from csv_wrangler.clipper import ClipError, ClipSpec, clip_rows


def _parse_specs(raw: List[str]) -> List[ClipSpec]:
    """Parse strings like 'col:low:high', 'col::high', or 'col:low:'."""
    specs: List[ClipSpec] = []
    for token in raw:
        parts = token.split(":")
        if len(parts) != 3:  # noqa: PLR2004
            raise ClipError(
                f"Invalid clip spec '{token}'. Expected 'column:low:high' "
                "(use empty string to omit a bound, e.g. 'age:0:')."
            )
        col, low_s, high_s = parts
        low = float(low_s) if low_s.strip() else None
        high = float(high_s) if high_s.strip() else None
        specs.append(ClipSpec(column=col, low=low, high=high))
    return specs


def add_clip_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "clip",
        help="Clamp numeric column values to a [low, high] range.",
    )
    p.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input CSV file (default: stdin).",
    )
    p.add_argument(
        "-o", "--output",
        default="-",
        help="Output CSV file (default: stdout).",
    )
    p.add_argument(
        "-c", "--clip",
        dest="specs",
        metavar="COL:LOW:HIGH",
        action="append",
        required=True,
        help="Clip spec (repeatable). Use empty bound to omit, e.g. 'age:0:'.",
    )
    p.add_argument(
        "--lenient",
        action="store_true",
        help="Skip non-numeric / missing values instead of raising an error.",
    )
    p.set_defaults(func=_run_clip)


def _run_clip(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except ClipError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    in_fh = open(args.input, newline="") if args.input != "-" else sys.stdin
    out_fh = open(args.output, "w", newline="") if args.output != "-" else sys.stdout

    try:
        reader = csv.DictReader(in_fh)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

        gen, result = clip_rows(rows, specs, strict=not args.lenient)
        writer = csv.DictWriter(out_fh, fieldnames=fieldnames)
        writer.writeheader()
        try:
            for row in gen:
                writer.writerow(row)
        except ClipError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    finally:
        if args.input != "-":
            in_fh.close()
        if args.output != "-":
            out_fh.close()

    print(
        f"Clipped {result.clipped_count} value(s) across "
        f"{len(result.columns_affected)} column(s).",
        file=sys.stderr,
    )
    return 0
