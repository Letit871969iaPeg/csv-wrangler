"""CLI entry point for csv-wrangler."""

import sys
import csv
import argparse
from pathlib import Path

from csv_wrangler.parser import parse_rules, ParseError
from csv_wrangler.executor import apply_rules, ExecutionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csv-wrangler",
        description="Fast, opinionated CSV transformations and validation.",
    )
    parser.add_argument(
        "rules_file",
        type=Path,
        help="Path to a .rules file containing transformation DSL rules.",
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Path to the output CSV file (default: stdout).",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Skip rows that fail execution instead of aborting.",
    )
    return parser


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        rules_text = args.rules_file.read_text(encoding="utf-8")
        rules = parse_rules(rules_text)
    except FileNotFoundError:
        print(f"Error: rules file not found: {args.rules_file}", file=sys.stderr)
        return 1
    except ParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    try:
        in_file = args.input_csv.open(newline="", encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: input CSV not found: {args.input_csv}", file=sys.stderr)
        return 1

    out_file = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout

    try:
        reader = csv.DictReader(in_file)
        writer = None
        rows_written = 0

        for row in reader:
            try:
                result = apply_rules(dict(row), rules)
            except ExecutionError as exc:
                if args.skip_errors:
                    print(f"Warning: skipping row — {exc}", file=sys.stderr)
                    continue
                print(f"Execution error: {exc}", file=sys.stderr)
                return 1

            if result is None:
                continue  # filtered out

            if writer is None:
                writer = csv.DictWriter(out_file, fieldnames=list(result.keys()))
                writer.writeheader()

            writer.writerow(result)
            rows_written += 1

        if writer is None and rows_written == 0:
            print("Warning: no rows written (all filtered or empty input).", file=sys.stderr)
    finally:
        in_file.close()
        if args.output and out_file is not sys.stdout:
            out_file.close()

    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
