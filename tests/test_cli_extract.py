"""Tests for csv_wrangler.cli_extract."""
import argparse
import csv
import io
import os
import tempfile

import pytest

from csv_wrangler.cli_extract import _parse_specs, add_extract_subcommand, _run_extract
from csv_wrangler.extractor import ExtractError


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_extract_subcommand(sub)
    return p


def _write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestParseSpecs:
    def test_two_part_spec(self):
        specs = _parse_specs(["email:@(.+)"])
        assert specs[0].column == "email"
        assert specs[0].pattern == "@(.+)"
        assert specs[0].dest == "email"  # defaults

    def test_three_part_spec(self):
        specs = _parse_specs(["email:@(.+):domain"])
        assert specs[0].dest == "domain"

    def test_four_part_spec(self):
        specs = _parse_specs(["url:https://([^/]+)/([^/]+):host:1"])
        assert specs[0].group == 1

    def test_missing_pattern_raises(self):
        with pytest.raises(ExtractError):
            _parse_specs(["onlycolumn"])

    def test_multiple_specs(self):
        specs = _parse_specs(["a:(\\d+):num", "b:([A-Z]+):upper"])
        assert len(specs) == 2


class TestRunExtract:
    def test_extract_via_cli(self, tmp_path):
        src = str(tmp_path / "in.csv")
        dst = str(tmp_path / "out.csv")
        _write_csv(src, [
            {"email": "alice@example.com"},
            {"email": "bob@corp.org"},
        ])
        p = _make_parser()
        args = p.parse_args(["extract", src, "-o", dst, "-s", "email:@(.+):domain"])
        rc = args.func(args)
        assert rc == 0
        rows = _read_csv(dst)
        assert rows[0]["domain"] == "example.com"
        assert rows[1]["domain"] == "corp.org"

    def test_bad_spec_returns_error(self, tmp_path):
        src = str(tmp_path / "in.csv")
        _write_csv(src, [{"col": "val"}])
        p = _make_parser()
        args = p.parse_args(["extract", src, "-s", "nocolon"])
        rc = args.func(args)
        assert rc == 1

    def test_subcommand_registered(self):
        p = _make_parser()
        args = p.parse_args(["extract", "dummy.csv", "-s", "x:(\\d+)"])
        assert hasattr(args, "func")
