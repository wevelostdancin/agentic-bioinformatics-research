import random

from agentic_bioinformatics.repro import TokenCounter, aggregate, set_seed


def test_set_seed_is_deterministic():
    set_seed(7)
    a = [random.random() for _ in range(3)]
    set_seed(7)
    b = [random.random() for _ in range(3)]
    assert a == b


def test_different_seeds_differ():
    set_seed(1)
    a = [random.random() for _ in range(3)]
    set_seed(2)
    b = [random.random() for _ in range(3)]
    assert a != b


def test_aggregate_reports_mean_std_ci():
    r = aggregate([2, 4, 6, 8])
    assert r["mean"] == 5 and r["n"] == 4
    assert r["ci_low"] is not None and r["ci_low"] < r["mean"] < r["ci_high"]


def test_aggregate_single_value_has_no_ci():
    assert aggregate([5])["ci_low"] is None


def test_token_counter_accumulates():
    counter = TokenCounter()
    counter.add(10, 3)
    counter.add(5, 2)
    assert counter.as_dict() == {"in_tokens": 15, "out_tokens": 5}
