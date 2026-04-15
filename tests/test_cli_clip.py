"""Integration-level tests for the clip CLI sub-command."""
import csv
import io
import textwrap
from argparse import ArgumentParser
from pathlib import Path

import pytest

from csv_wrangler.cli_clip import _parse_specs, add_clip_subcommand, _run_clip
from csv_wrangler.clipper import ClipError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parser() -> ArgumentParser:
    p = ArgumentParser()
    sub = p.add_subparsers()
    add_clip_subcommand(sub)
    return p


def _write_csv(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content))


def _read_csv(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(newline="")))


# ---------------------------------------------------------------------------
# _parse_specs unit tests
# ---------------------------------------------------------------------------

def test_parse_spec_low_and_high():
    specs = _parse_specs(["score:0:100"])
    assert specs[0].column == "score"
    assert specs[0].low == 0.0
    assert specs[0].high == 100.0


def test_parse_spec_low_only():
    specs = _parse_specs(["age:0:"])
    assert specs[0].low == 0.0
    assert specs[0].high is None


def test_parse_spec_high_only():
    specs = _parse_specs(["val::50"])
    assert specs[0].low is None
    assert specs[0].high == 50.0


def test_parse_spec_bad_format_raises():
    with pytest.raises(ClipError, match="Invalid clip spec"):
        _parse_specs(["nodots"])


# ---------------------------------------------------------------------------
# CLI round-trip tests
# ---------------------------------------------------------------------------

def test_clip_low_via_cli(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "age\n-5\n25\n30\n")

    parser = _make_parser()
    args = parser.parse_args(["clip", str(src), "-o", str(dst), "-c", "age:0:"])
    rc = args.func(args)

    assert rc == 0
    rows = _read_csv(dst)
    assert rows[0]["age"] == "0"
    assert rows[1]["age"] == "25"


def test_clip_high_via_cli(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "score\n50\n120\n99\n")

    parser = _make_parser()
    args = parser.parse_args(["clip", str(src), "-o", str(dst), "-c", "score::100"])
    rc = args.func(args)

    assert rc == 0
    rows = _read_csv(dst)
    assert rows[1]["score"] == "100"
    assert rows[2]["score"] == "99"


def test_clip_non_numeric_strict_returns_error(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "val\nabc\n")

    parser = _make_parser()
    args = parser.parse_args(["clip", str(src), "-o", str(dst), "-c", "val:0:10"])
    rc = args.func(args)
    assert rc == 1


def test_clip_non_numeric_lenient_succeeds(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    _write_csv(src, "val\nabc\n5\n")

    parser = _make_parser()
    args = parser.parse_args(
        ["clip", str(src), "-o", str(dst), "-c", "val:0:10", "--lenient"]
    )
    rc = args.func(args)
    assert rc == 0
    rows = _read_csv(dst)
    assert rows[0]["val"] == "abc"
    assert rows[1]["val"] == "5"
