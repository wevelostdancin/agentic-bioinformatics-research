import pytest

from agentic_bioinformatics.metrics.coverage import (
    capture_recapture,
    capture_recapture_ci,
    coverage_matrix,
    saturation_curve,
)


def test_capture_recapture_zero_intersection_is_undefined():
    assert capture_recapture(10, 8, 0) == float("inf")


def test_capture_recapture_chapman_estimate():
    assert capture_recapture(10, 10, 5) == pytest.approx(121 / 6 - 1)


def test_capture_recapture_rejects_impossible_m():
    with pytest.raises(ValueError):
        capture_recapture(10, 10, 20)


def test_capture_recapture_ci_contains_estimate():
    est = capture_recapture(10, 10, 5)
    lo, hi = capture_recapture_ci(10, 10, 5)
    assert lo < est < hi


def test_saturation_curve():
    assert saturation_curve([1, 1, 2]) == [0.25, 0.5, 1.0]


def test_coverage_matrix_marks_uncovered():
    cells = [("api", "CWE-79"), ("cli", "CWE-78")]
    result = coverage_matrix(cells, {("api", "CWE-79")})
    assert result["covered"] == 1 and result["uncovered"] == 1
