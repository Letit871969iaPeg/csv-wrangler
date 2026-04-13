"""Tests for csv_wrangler.reporter."""
import pytest
from csv_wrangler.reporter import Report, RuleResult, build_rule_result


# ---------------------------------------------------------------------------
# RuleResult
# ---------------------------------------------------------------------------

class TestRuleResult:
    def test_ok_str(self):
        r = RuleResult(rule_type="rename", description="old->new", rows_affected=5)
        assert "[OK]" in str(r)
        assert "5 row(s)" in str(r)

    def test_skip_str(self):
        r = RuleResult(rule_type="drop", description="col", rows_affected=0, skipped=True)
        assert "[SKIP]" in str(r)
        assert "row(s)" not in str(r)

    def test_error_str(self):
        r = RuleResult(rule_type="filter", description="x>0", rows_affected=0, error="bad expr")
        assert "[ERROR]" in str(r)
        assert "bad expr" in str(r)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def _make_report(self) -> Report:
        rpt = Report(input_rows=10, output_rows=8)
        rpt.add(RuleResult("rename", "a->b", rows_affected=10))
        rpt.add(RuleResult("filter", "x>0", rows_affected=2))
        rpt.add(RuleResult("drop", "col", rows_affected=0, skipped=True))
        rpt.add(RuleResult("transform", "upper", rows_affected=0, error="oops"))
        return rpt

    def test_error_count(self):
        rpt = self._make_report()
        assert rpt.error_count == 1

    def test_skipped_count(self):
        rpt = self._make_report()
        assert rpt.skipped_count == 1

    def test_summary_contains_counts(self):
        rpt = self._make_report()
        s = rpt.summary()
        assert "Input rows : 10" in s
        assert "Output rows: 8" in s
        assert "Rules run  : 4" in s

    def test_summary_lists_rules(self):
        rpt = self._make_report()
        s = rpt.summary()
        assert "rename" in s
        assert "filter" in s

    def test_add_increases_results(self):
        rpt = Report()
        assert len(rpt.results) == 0
        rpt.add(RuleResult("drop", "col", rows_affected=0))
        assert len(rpt.results) == 1


# ---------------------------------------------------------------------------
# build_rule_result
# ---------------------------------------------------------------------------

class TestBuildRuleResult:
    def test_rows_affected_computed(self):
        r = build_rule_result("filter", "x>1", rows_before=10, rows_after=7)
        assert r.rows_affected == 3

    def test_skipped_zero_affected(self):
        r = build_rule_result("rename", "a->b", rows_before=5, rows_after=5, skipped=True)
        assert r.rows_affected == 0
        assert r.skipped is True

    def test_error_zero_affected(self):
        r = build_rule_result("transform", "upper", rows_before=5, rows_after=5, error="fail")
        assert r.rows_affected == 0
        assert r.error == "fail"

    def test_no_change_still_ok(self):
        r = build_rule_result("rename", "a->b", rows_before=5, rows_after=5)
        assert r.rows_affected == 0
        assert r.error is None
        assert r.skipped is False
