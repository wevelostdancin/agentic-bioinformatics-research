from agentic_bioinformatics_research.judge.validation import (
    cohen_kappa,
    position_swap_agreement,
)


def test_cohen_kappa_perfect():
    assert cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0


def test_cohen_kappa_known_value():
    assert cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == 0.5


def test_position_swap_agreement():
    assert position_swap_agreement([1, 0, 1], [1, 0, 1]) == 1.0
