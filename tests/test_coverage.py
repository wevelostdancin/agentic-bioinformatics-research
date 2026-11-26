import pytest

from agentic_bioinformatics_research.metrics.coverage import (
    capture_recapture,
    capture_recapture_ci,
    chapman_from_sets,
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
    assert lo <= est <= hi


def test_capture_recapture_ci_respects_observed_lower_bound():
    lo, hi = capture_recapture_ci(10, 8, 0)
    assert lo == 18 and hi == float("inf")
    lo, hi = capture_recapture_ci(10, 10, 5)
    assert lo == 15 and hi > capture_recapture(10, 10, 5)


def test_capture_recapture_ci_has_nonzero_width():
    lo, hi = capture_recapture_ci(5, 5, 5)
    assert hi > lo


def test_saturation_curve():
    assert saturation_curve([1, 1, 2]) == [0.25, 0.5, 1.0]


def test_coverage_matrix_marks_uncovered():
    cells = [("api", "CWE-79"), ("cli", "CWE-78")]
    result = coverage_matrix(cells, {("api", "CWE-79")})
    assert result["covered"] == 1 and result["uncovered"] == 1


def test_chapman_from_sets_counts_intersection():
    result = chapman_from_sets({"a", "b", "c"}, {"b", "c", "d"})
    assert (result["n1"], result["n2"], result["intersection"]) == (3, 3, 2)
    assert result["estimate"] == pytest.approx(16 / 3 - 1)
    assert result["ci_low"] <= result["estimate"] <= result["ci_high"]


def test_chapman_from_sets_zero_intersection_is_undefined():
    result = chapman_from_sets({"a"}, {"b"})
    assert result["intersection"] == 0
    assert result["estimate"] == float("inf")
    assert result["ci_low"] == 2 and result["ci_high"] == float("inf")
