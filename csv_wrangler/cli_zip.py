"""CLI subcommand: zip — merge two CSV files side-by-side by row position."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List, Dict

from csv_wrangler.zipper import ZipError, zip_rows


def _iter_csv(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def add_zip_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "zip",
        help="Merge two CSV files side-by-side by row position.",
    )
    p.add_argument("left", help="Path to the left CSV file.")
    p.add_argument("right", help="Path to the right CSV file.")
    p.add_argument(
        "--left-prefix",
        default="left_",
        metavar="PREFIX",
        help="Prefix for left-side columns (default: 'left_').",
    )
    p.add_argument(
        "--right-prefix",
        default="right_",
        metavar="PREFIX",
        help="Prefix for right-side columns (default: 'right_').",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Raise an error if the two files have different row counts.",
    )
    p.add_argument(
        "-o", "--output",
        default="-",
        metavar="FILE",
        help="Output CSV path (default: stdout).",
    )
    p.set_defaults(func=_run_zip)


def _run_zip(args: argparse.Namespace) -> int:
    try:
        left_rows = _iter_csv(args.left)
        right_rows = _iter_csv(args.right)
    except OSError as exc:
        print(f"zip: cannot open file: {exc}", file=sys.stderr)
        return 1

    try:
        result = zip_rows(
            left_rows,
            right_rows,
            prefix_left=args.left_prefix,
            prefix_right=args.right_prefix,
            strict=args.strict,
        )
    except ZipError as exc:
        print(f"zip: {exc}", file=sys.stderr)
        return 1

    if not result.rows:
        return 0

    fieldnames = list(result.rows[0].keys())

    if args.output == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result.rows)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(result.rows)

    if result.truncated:
        print(
            f"zip: warning: row counts differ "
            f"(left={result.left_count}, right={result.right_count}); "
            "output truncated to shorter side.",
            file=sys.stderr,
        )
    return 0
