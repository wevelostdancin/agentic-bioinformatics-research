import pytest

from agentic_bioinformatics_research.matrix import expand_matrix


def test_cartesian_product():
    cells = expand_matrix({"protocol": ["a", "b"], "perturbation": ["x", "y", "z"]})
    assert len(cells) == 6
    assert cells[0] == {"perturbation": "x", "protocol": "a"}
    assert {"perturbation": "z", "protocol": "b"} in cells


def test_order_is_deterministic():
    first = expand_matrix({"protocol": ["a", "b"], "seed": [1, 2]})
    second = expand_matrix({"seed": [1, 2], "protocol": ["a", "b"]})
    assert first == second


def test_fixed_values_are_copied():
    assert expand_matrix({"seed": [1]}, fixed={"model": "m"}) == [{"model": "m", "seed": 1}]


def test_empty_factor_is_rejected():
    with pytest.raises(ValueError):
        expand_matrix({"protocol": []})


def test_no_factors_yields_one_cell():
    assert expand_matrix({}, fixed={"a": 1}) == [{"a": 1}]
