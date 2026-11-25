from agentic_bioinformatics.metrics.coverage import capture_recapture, coverage_matrix


def test_capture_recapture_zero_intersection():
    assert capture_recapture(10, 8, 0) == 0.0


def test_capture_recapture_estimate():
    assert capture_recapture(10, 10, 5) == 20.0


def test_coverage_matrix_marks_uncovered():
    cells = [("api", "CWE-79"), ("cli", "CWE-78")]
    result = coverage_matrix(cells, {("api", "CWE-79")})
    assert result["covered"] == 1 and result["uncovered"] == 1
