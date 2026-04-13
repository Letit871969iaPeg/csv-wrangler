"""CLI sub-command: dedup — remove duplicate rows from a CSV file."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List, Optional

from csv_wrangler.deduplicator import DeduplicationError, deduplicate_rows


def add_dedup_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *dedup* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "dedup",
        help="Remove duplicate rows from a CSV file.",
    )
    p.add_argument("input", help="Path to input CSV file (use '-' for stdin).")
    p.add_argument(
        "-o", "--output",
        default="-",
        help="Path to output CSV file (default: stdout).",
    )
    p.add_argument(
        "-k", "--key",
        dest="key_columns",
        metavar="COLUMN",
        action="append",
        default=None,
        help="Column(s) to use as the deduplication key (repeatable). "
             "Omit to compare entire rows.",
    )
    p.add_argument(
        "--keep",
        choices=["first", "last"],
        default="first",
        help="Which occurrence to keep when a duplicate is found (default: first).",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print deduplication statistics to stderr.",
    )
    p.set_defaults(func=_run_dedup)


def _run_dedup(args: argparse.Namespace) -> int:
    """Entry point for the *dedup* sub-command."""
    try:
        in_fh = sys.stdin if args.input == "-" else open(args.input, newline="")
        try:
            reader = csv.DictReader(in_fh)
            rows = list(reader)
            fieldnames: List[str] = list(reader.fieldnames or [])
        finally:
            if in_fh is not sys.stdin:
                in_fh.close()

        result = deduplicate_rows(
            rows,
            key_columns=args.key_columns,
            keep=args.keep,
        )

        out_fh = sys.stdout if args.output == "-" else open(args.output, "w", newline="")
        try:
            writer = csv.DictWriter(out_fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(result.kept)
        finally:
            if out_fh is not sys.stdout:
                out_fh.close()

        if args.stats:
            print(
                f"dedup: kept {len(result.kept)}, "
                f"dropped {result.duplicate_count} duplicate(s) "
                f"(total input: {result.total_input})",
                file=sys.stderr,
            )

        return 0

    except DeduplicationError as exc:
        print(f"dedup error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"I/O error: {exc}", file=sys.stderr)
        return 1
