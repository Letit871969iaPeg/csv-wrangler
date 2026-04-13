"""Tests for csv_wrangler.progress."""

from __future__ import annotations

import io
import sys

import pytest

from csv_wrangler.progress import ProgressBar, track


def _capture_bar_output(capsys, fn):
    fn()
    return capsys.readouterr().err


def test_progress_bar_renders(capsys):
    bar = ProgressBar(total=4, label="Test")
    bar.update(2)
    bar.finish()
    captured = capsys.readouterr().err
    assert "Test" in captured
    assert "4/4" in captured or "2/4" in captured


def test_progress_bar_reaches_100(capsys):
    bar = ProgressBar(total=3, label="X")
    bar.update(3)
    bar.finish()
    captured = capsys.readouterr().err
    assert "100%" in captured


def test_progress_bar_clamps_overflow(capsys):
    bar = ProgressBar(total=2, label="Y")
    bar.update(10)  # more than total
    bar.finish()
    captured = capsys.readouterr().err
    assert "2/2" in captured


def test_track_yields_all_items(capsys):
    items = [1, 2, 3, 4, 5]
    result = list(track(iter(items), total=len(items), label="Items"))
    assert result == items


def test_track_writes_to_stderr(capsys):
    list(track(iter(["a", "b"]), total=2, label="Letters"))
    captured = capsys.readouterr().err
    assert "Letters" in captured


def test_zero_total_does_not_crash(capsys):
    bar = ProgressBar(total=0, label="Empty")
    bar.finish()
    captured = capsys.readouterr().err
    assert "Empty" in captured


def test_track_empty_iterable(capsys):
    result = list(track(iter([]), total=0, label="None"))
    assert result == []
