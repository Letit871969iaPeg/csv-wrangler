"""Tests for csv_wrangler.stacker."""
import pytest
from csv_wrangler.stacker import StackError, StackResult, stack_rows


def _row(**kw):
    return {k: str(v) for k, v in kw.items()}


class TestStackResult:
    def test_defaults(self):
        r = StackResult()
        assert r.input_rows == 0
        assert r.output_rows == 0
        assert r.value_columns == []

    def test_str_shows_counts(self):
        r = StackResult(input_rows=3, output_rows=9, value_columns=["a", "b", "c"])
        s = str(r)
        assert "3" in s
        assert "9" in s
        assert "a" in s

    def test_str_no_value_columns(self):
        r = StackResult(input_rows=0, output_rows=0, value_columns=[])
        assert "(none)" in str(r)


class TestStackRows:
    def _run(self, rows, id_cols, **kw):
        it, result = stack_rows(rows, id_cols, **kw)
        return list(it), result

    def test_basic_melt(self):
        rows = [_row(id="1", jan="10", feb="20")]
        out, res = self._run(rows, ["id"])
        assert len(out) == 2
        assert res.output_rows == 2
        assert res.input_rows == 1

    def test_key_and_value_columns_present(self):
        rows = [_row(id="1", jan="10", feb="20")]
        out, _ = self._run(rows, ["id"], key_column="month", value_column="amount")
        assert "month" in out[0]
        assert "amount" in out[0]
        assert out[0]["month"] == "jan"
        assert out[0]["amount"] == "10"

    def test_id_columns_preserved(self):
        rows = [_row(id="42", name="alice", x="1")]
        out, _ = self._run(rows, ["id", "name"])
        assert out[0]["id"] == "42"
        assert out[0]["name"] == "alice"

    def test_multiple_input_rows(self):
        rows = [_row(id="1", a="1", b="2"), _row(id="2", a="3", b="4")]
        out, res = self._run(rows, ["id"])
        assert len(out) == 4
        assert res.output_rows == 4

    def test_empty_input_returns_empty(self):
        out, res = self._run([], ["id"])
        assert out == []
        assert res.input_rows == 0

    def test_missing_id_column_raises(self):
        rows = [_row(a="1", b="2")]
        with pytest.raises(StackError, match="id columns not found"):
            stack_rows(rows, ["missing"])

    def test_no_value_columns_raises(self):
        rows = [_row(id="1")]
        with pytest.raises(StackError, match="No value columns"):
            stack_rows(rows, ["id"])

    def test_value_columns_reported(self):
        rows = [_row(id="1", x="1", y="2", z="3")]
        _, res = self._run(rows, ["id"])
        assert set(res.value_columns) == {"x", "y", "z"}
