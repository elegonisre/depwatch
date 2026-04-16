"""Tests for depwatch.scheduler."""

import pytest
from unittest.mock import MagicMock, patch

from depwatch.scheduler import parse_interval, run_scheduler


# --- parse_interval ---

def test_parse_interval_hours():
    assert parse_interval("2h") == 7200


def test_parse_interval_minutes():
    assert parse_interval("30m") == 1800


def test_parse_interval_seconds():
    assert parse_interval("90s") == 90


def test_parse_interval_invalid_unit():
    with pytest.raises(ValueError, match="Unknown interval unit"):
        parse_interval("10d")


def test_parse_interval_invalid_format():
    with pytest.raises((ValueError, IndexError)):
        parse_interval("abc")


# --- run_scheduler ---

def test_run_scheduler_calls_fn_correct_times():
    fn = MagicMock()
    with patch("depwatch.scheduler.time.sleep"):
        run_scheduler(fn, "1m", max_runs=3)
    assert fn.call_count == 3


def test_run_scheduler_sleeps_between_runs():
    fn = MagicMock()
    with patch("depwatch.scheduler.time.sleep") as mock_sleep:
        run_scheduler(fn, "5m", max_runs=2)
    # sleeps between runs: max_runs-1 times
    assert mock_sleep.call_count == 1
    mock_sleep.assert_called_with(300)


def test_run_scheduler_continues_on_error():
    """Scheduler should not abort when check_fn raises."""
    fn = MagicMock(side_effect=[RuntimeError("boom"), None])
    with patch("depwatch.scheduler.time.sleep"):
        run_scheduler(fn, "10m", max_runs=2)
    assert fn.call_count == 2


def test_run_scheduler_single_run_no_sleep():
    fn = MagicMock()
    with patch("depwatch.scheduler.time.sleep") as mock_sleep:
        run_scheduler(fn, "1h", max_runs=1)
    fn.assert_called_once()
    mock_sleep.assert_not_called()
