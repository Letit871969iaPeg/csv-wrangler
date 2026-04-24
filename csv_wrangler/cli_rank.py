"""CLI sub-command: rank — add a rank column based on a numeric field."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterator

from csv_wrangler.ranker import RankError, RankSpec, rank_rows


def add_rank_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rank",
        help="Add a rank column derived from a numeric field.",
    )
    p.add_argument("column", help="Column to rank by.")
    p.add_argument(
        "--dest",
        default="rank",
        metavar="DEST",
        help="Name of the output rank column (default: rank).",
    )
    p.add_argument(
        "--group-by",
        default=None,
        metavar="COL",
        help="Partition ranking by this column.",
    )
    p.add_argument(
        "--desc",
        action="store_true",
        help="Rank in descending order (highest value = rank 1).",
    )
    p.add_argument(
        "--method",
        choices=["dense", "row"],
        default="dense",
        help="Ranking method: dense (ties share a rank) or row (unique ranks).",
    )
    p.add_argument("input", nargs="?", default="-", help="Input CSV (default: stdin).")
    p.add_argument("-o", "--output", default="-", help="Output CSV (default: stdout).")
    p.set_defaults(func=_run_rank)


def _iter_csv(path: str) -> Iterator[dict[str, str]]:
    fh = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        reader = csv.DictReader(fh)
        yield from reader
    finally:
        if path != "-":
            fh.close()


def _run_rank(args: argparse.Namespace) -> int:
    try:
        spec = RankSpec(
            column=args.column,
            dest=args.dest,
            group_by=args.group_by,
            ascending=not args.desc,
            method=args.method,
        )
    except RankError as exc:
        print(f"rank: {exc}", file=sys.stderr)
        return 1

    rows = list(_iter_csv(args.input))
    if not rows:
        return 0

    try:
        out_rows, result = rank_rows(rows, spec)
    except RankError as exc:
        print(f"rank: {exc}", file=sys.stderr)
        return 1

    fh = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    finally:
        if args.output != "-":
            fh.close()

    print(
        f"Ranked {result.ranked_count} row(s), skipped {result.skipped_count}.",
        file=sys.stderr,
    )
    return 0
