"""Tests for csv_wrangler.tokenizer."""
from __future__ import annotations

import pytest

from csv_wrangler.tokenizer import (
    TokenizeError,
    TokenizeResult,
    TokenizeSpec,
    tokenize_rows,
    tokenize_rows_with_result,
)


def _row(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# TokenizeSpec
# ---------------------------------------------------------------------------

class TestTokenizeSpec:
    def test_valid_spec_creates_ok(self):
        spec = TokenizeSpec(column="text")
        assert spec.column == "text"
        assert spec.dest == "text_tokens"

    def test_custom_dest(self):
        spec = TokenizeSpec(column="body", dest="words")
        assert spec.dest == "words"

    def test_empty_column_raises(self):
        with pytest.raises(TokenizeError, match="column"):
            TokenizeSpec(column="")

    def test_both_delimiter_and_pattern_raises(self):
        with pytest.raises(TokenizeError, match="not both"):
            TokenizeSpec(column="x", delimiter=",", pattern=r"\s+")

    def test_whitespace_split_default(self):
        spec = TokenizeSpec(column="text")
        assert spec.tokenize("hello world") == ["hello", "world"]

    def test_delimiter_split(self):
        spec = TokenizeSpec(column="tags", delimiter=",")
        assert spec.tokenize("a,b,c") == ["a", "b", "c"]

    def test_pattern_split(self):
        spec = TokenizeSpec(column="text", pattern=r"[,;]+")
        assert spec.tokenize("a,b;;c") == ["a", "b", "c"]

    def test_lower_flag(self):
        spec = TokenizeSpec(column="text", lower=True)
        assert spec.tokenize("Hello World") == ["hello", "world"]

    def test_empty_tokens_filtered(self):
        spec = TokenizeSpec(column="text", delimiter=",")
        assert spec.tokenize("a,,b") == ["a", "b"]


# ---------------------------------------------------------------------------
# tokenize_rows
# ---------------------------------------------------------------------------

class TestTokenizeRows:
    def test_dest_column_added(self):
        rows = [_row(text="hello world")]
        spec = TokenizeSpec(column="text")
        result = list(tokenize_rows(rows, [spec]))
        assert "text_tokens" in result[0]

    def test_tokens_joined_by_pipe(self):
        rows = [_row(text="foo bar baz")]
        spec = TokenizeSpec(column="text")
        result = list(tokenize_rows(rows, [spec]))
        assert result[0]["text_tokens"] == "foo|bar|baz"

    def test_missing_column_raises(self):
        rows = [_row(other="value")]
        spec = TokenizeSpec(column="text")
        with pytest.raises(TokenizeError, match="text"):
            list(tokenize_rows(rows, [spec]))

    def test_original_column_preserved(self):
        rows = [_row(text="hello world")]
        spec = TokenizeSpec(column="text")
        result = list(tokenize_rows(rows, [spec]))
        assert result[0]["text"] == "hello world"

    def test_multiple_specs(self):
        rows = [_row(title="foo bar", tags="a,b")]
        specs = [
            TokenizeSpec(column="title"),
            TokenizeSpec(column="tags", delimiter=","),
        ]
        result = list(tokenize_rows(rows, specs))
        assert result[0]["title_tokens"] == "foo|bar"
        assert result[0]["tags_tokens"] == "a|b"


# ---------------------------------------------------------------------------
# tokenize_rows_with_result
# ---------------------------------------------------------------------------

class TestTokenizeRowsWithResult:
    def test_result_tracks_tokenized_count(self):
        rows = [_row(text="a b"), _row(text="c d")]
        spec = TokenizeSpec(column="text")
        result, it = tokenize_rows_with_result(rows, [spec])
        list(it)
        assert result.tokenized_count == 2

    def test_columns_created_listed(self):
        rows = [_row(text="a b")]
        spec = TokenizeSpec(column="text", dest="words")
        result, it = tokenize_rows_with_result(rows, [spec])
        list(it)
        assert "words" in result.columns_created

    def test_str_representation(self):
        r = TokenizeResult(tokenized_count=3, skipped_count=1, columns_created=["x"])
        assert "tokenized=3" in str(r)
        assert "skipped=1" in str(r)
