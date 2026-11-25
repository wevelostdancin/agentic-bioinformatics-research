from agentic_bioinformatics_research.judge.rubric import rubric


def test_rubric_has_required_keys():
    r = rubric()
    assert {"evidence", "coverage", "novelty"} <= set(r)
