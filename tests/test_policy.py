"""Tests for depwatch.policy."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.policy import Policy, evaluate_policy


def _s(pkg, current, latest, outdated):
    return DependencyStatus(
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def test_empty_statuses_passes():
    result = evaluate_policy(Policy(max_outdated=0), [])
    assert result.passed


def test_max_outdated_passes():
    statuses = [_s("a", "1.0", "1.1", True), _s("b", "2.0", "2.0", False)]
    result = evaluate_policy(Policy(max_outdated=1), statuses)
    assert result.passed


def test_max_outdated_fails():
    statuses = [_s("a", "1.0", "1.1", True), _s("b", "1.0", "1.1", True)]
    result = evaluate_policy(Policy(max_outdated=1), statuses)
    assert not result.passed
    assert "max_outdated=1" in result.reason


def test_max_ratio_passes():
    statuses = [_s("a", "1.0", "2.0", True)] + [_s(f"x{i}", "1.0", "1.0", False) for i in range(9)]
    result = evaluate_policy(Policy(max_outdated_ratio=0.2), statuses)
    assert result.passed


def test_max_ratio_fails():
    statuses = [_s("a", "1.0", "2.0", True), _s("b", "1.0", "2.0", True), _s("c", "1.0", "1.0", False)]
    result = evaluate_policy(Policy(max_outdated_ratio=0.5), statuses)
    assert not result.passed
    assert "max_outdated_ratio" in result.reason


def test_block_major_behind_passes():
    statuses = [_s("django", "3.2.0", "4.0.0", True)]
    result = evaluate_policy(Policy(block_major_behind=2), statuses)
    assert result.passed


def test_block_major_behind_fails():
    statuses = [_s("django", "2.0.0", "4.0.0", True)]
    result = evaluate_policy(Policy(block_major_behind=2), statuses)
    assert not result.passed
    assert "django" in result.reason


def test_no_policy_set_always_passes():
    statuses = [_s("a", "1.0", "9.0", True)] * 10
    result = evaluate_policy(Policy(), statuses)
    assert result.passed


def test_combined_policies_first_failure_wins():
    statuses = [_s("a", "1.0", "2.0", True), _s("b", "1.0", "2.0", True)]
    result = evaluate_policy(Policy(max_outdated=1, max_outdated_ratio=0.9), statuses)
    assert not result.passed
    assert "max_outdated=1" in result.reason
