"""Tests for the CLI entry point."""

import csv
import textwrap
from pathlib import Path

import pytest

from csv_wrangler.cli import run


@pytest.fixture()
def tmp_csv(tmp_path):
    """Write a small CSV and return its path."""
    def _write(rows: list[dict]) -> Path:
        p = tmp_path / "input.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return p
    return _write


@pytest.fixture()
def tmp_rules(tmp_path):
    """Write a rules file and return its path."""
    def _write(content: str) -> Path:
        p = tmp_path / "rules.rules"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p
    return _write


def test_rename_via_cli(tmp_csv, tmp_rules, tmp_path):
    csv_path = tmp_csv([{"first_name": "Alice", "age": "30"}])
    rules_path = tmp_rules("RENAME first_name -> name")
    out_path = tmp_path / "out.csv"

    exit_code = run([str(rules_path), str(csv_path), "-o", str(out_path)])

    assert exit_code == 0
    rows = list(csv.DictReader(out_path.open(encoding="utf-8")))
    assert rows[0]["name"] == "Alice"
    assert "first_name" not in rows[0]


def test_drop_via_cli(tmp_csv, tmp_rules, tmp_path):
    csv_path = tmp_csv([{"name": "Bob", "secret": "x"}])
    rules_path = tmp_rules("DROP secret")
    out_path = tmp_path / "out.csv"

    exit_code = run([str(rules_path), str(csv_path), "-o", str(out_path)])

    assert exit_code == 0
    rows = list(csv.DictReader(out_path.open(encoding="utf-8")))
    assert "secret" not in rows[0]


def test_filter_removes_rows(tmp_csv, tmp_rules, tmp_path):
    csv_path = tmp_csv([
        {"name": "Alice", "active": "true"},
        {"name": "Bob", "active": "false"},
    ])
    rules_path = tmp_rules("FILTER active == true")
    out_path = tmp_path / "out.csv"

    exit_code = run([str(rules_path), str(csv_path), "-o", str(out_path)])

    assert exit_code == 0
    rows = list(csv.DictReader(out_path.open(encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"


def test_missing_rules_file_returns_error(tmp_csv, tmp_path):
    csv_path = tmp_csv([{"a": "1"}])
    exit_code = run([str(tmp_path / "nonexistent.rules"), str(csv_path)])
    assert exit_code == 1


def test_missing_csv_file_returns_error(tmp_rules, tmp_path):
    rules_path = tmp_rules("DROP x")
    exit_code = run([str(rules_path), str(tmp_path / "nope.csv")])
    assert exit_code == 1


def test_skip_errors_flag_continues_on_bad_row(tmp_csv, tmp_rules, tmp_path):
    csv_path = tmp_csv([
        {"name": "Alice", "score": "10"},
        {"name": "Bob", "score": "20"},
    ])
    # DROP a column that doesn't exist — executor raises ExecutionError
    rules_path = tmp_rules("DROP missing_col")
    out_path = tmp_path / "out.csv"

    exit_code = run([str(rules_path), str(csv_path), "-o", str(out_path), "--skip-errors"])

    assert exit_code == 0
