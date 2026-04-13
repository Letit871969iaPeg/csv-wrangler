"""Tests for csv_wrangler.pipeline."""

from __future__ import annotations

import io
import textwrap

import pytest

from csv_wrangler.pipeline import PipelineConfig, PipelineError, run_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_source(content: str) -> io.StringIO:
    return io.StringIO(textwrap.dedent(content).strip())


def _make_rules_file(tmp_path, content: str) -> str:
    p = tmp_path / "rules.wrangle"
    p.write_text(textwrap.dedent(content).strip())
    return str(p)


def _make_schema_file(tmp_path, content: str) -> str:
    import json
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(content))
    return str(p)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rename_via_pipeline(tmp_path):
    rules_path = _make_rules_file(tmp_path, "rename old_name -> new_name")
    source = _make_source("""
        old_name,age
        Alice,30
        Bob,25
    """)
    dest = io.StringIO()
    config = PipelineConfig(rules_path=rules_path)
    report = run_pipeline(source, dest, config)
    assert report.error_count() == 0
    dest.seek(0)
    lines = dest.read().splitlines()
    assert lines[0] == "new_name,age"
    assert "Alice" in lines[1]


def test_drop_via_pipeline(tmp_path):
    rules_path = _make_rules_file(tmp_path, "drop secret")
    source = _make_source("""
        name,secret
        Alice,hunter2
    """)
    dest = io.StringIO()
    config = PipelineConfig(rules_path=rules_path)
    run_pipeline(source, dest, config)
    dest.seek(0)
    header = dest.read().splitlines()[0]
    assert "secret" not in header
    assert "name" in header


def test_missing_rules_file_raises(tmp_path):
    config = PipelineConfig(rules_path=str(tmp_path / "nonexistent.wrangle"))
    with pytest.raises(PipelineError, match="Failed to load rules"):
        run_pipeline(io.StringIO("a\n1"), io.StringIO(), config)


def test_execution_error_stops_pipeline(tmp_path):
    rules_path = _make_rules_file(tmp_path, "drop missing_col")
    source = _make_source("""
        name
        Alice
    """)
    dest = io.StringIO()
    config = PipelineConfig(rules_path=rules_path)
    report = run_pipeline(source, dest, config)
    assert report.error_count() > 0


def test_skip_invalid_continues(tmp_path):
    rules_path = _make_rules_file(tmp_path, "drop missing_col")
    source = _make_source("""
        name
        Alice
        Bob
    """)
    dest = io.StringIO()
    config = PipelineConfig(rules_path=rules_path, skip_invalid=True)
    report = run_pipeline(source, dest, config)
    # errors recorded but pipeline completed
    assert report.error_count() >= 1


def test_empty_csv_produces_no_output(tmp_path):
    rules_path = _make_rules_file(tmp_path, "rename a -> b")
    source = io.StringIO("a,c\n")
    dest = io.StringIO()
    config = PipelineConfig(rules_path=rules_path)
    run_pipeline(source, dest, config)
    dest.seek(0)
    assert dest.read().strip() == ""
