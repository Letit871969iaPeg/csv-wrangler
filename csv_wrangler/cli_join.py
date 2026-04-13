"""CLI sub-command: join two CSV files on a common key column."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List

from csv_wrangler.joiner import JoinError, join_rows


def add_join_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "join",
        help="Join two CSV files on a shared key column.",
    )
    p.add_argument("left", help="Path to the left CSV file.")
    p.add_argument("right", help="Path to the right CSV file.")
    p.add_argument("--key", required=True, help="Column name to join on.")
    p.add_argument(
        "--how",
        choices=["inner", "left", "right"],
        default="inner",
        help="Join strategy (default: inner).",
    )
    p.add_argument("-o", "--output", default="-", help="Output file path (default: stdout).")
    p.set_defaults(func=_run_join)


def _read_csv(path: str) -> List[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _run_join(args: argparse.Namespace) -> int:
    try:
        left_rows = _read_csv(args.left)
        right_rows = _read_csv(args.right)
        result = join_rows(left_rows, right_rows, key=args.key, how=args.how)
    except (JoinError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not result.rows:
        print("warning: join produced no rows.", file=sys.stderr)
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

    print(
        f"joined {len(result.rows)} rows "
        f"(left_unmatched={result.left_unmatched}, right_unmatched={result.right_unmatched})",
        file=sys.stderr,
    )
    return 0
