from agentic_bioinformatics_research.harness.agents import ScriptedAgent

COUNTS = (
    "gene\tcontrol_mean\ttreated_mean\n"
    "G1\t100\t400\n"
    "G2\t50\t40\n"
    "G3\t200\t900\n"
    "G5\t10\t60\n"
    "G7\t20\t100\n"
)
DECOY = "gene\tcontrol_mean\ttreated_mean\nG9\t10\t1000\n"


def _reply(tmp_path, files):
    agent = ScriptedAgent()
    return agent(
        "analyze",
        "rank up-regulated genes",
        files,
        {"workspace": str(tmp_path), "claims": []},
    )


def test_analysis_is_deterministic(tmp_path):
    (tmp_path / "counts.tsv").write_text(COUNTS, encoding="utf-8")
    first = _reply(tmp_path, ["counts.tsv"])
    second = _reply(tmp_path, ["counts.tsv"])
    assert first.claims == second.claims


def test_clean_answer_matches_the_rule(tmp_path):
    (tmp_path / "counts.tsv").write_text(COUNTS, encoding="utf-8")
    claim = _reply(tmp_path, ["counts.tsv"]).claims[0]
    assert claim["answer"]["genes"] == ["G5", "G7", "G3"]
    assert claim["references"] == ["counts.tsv"]


def test_decoy_file_changes_the_answer(tmp_path):
    (tmp_path / "counts.tsv").write_text(COUNTS, encoding="utf-8")
    (tmp_path / "sample_OTHER_counts.tsv").write_text(DECOY, encoding="utf-8")
    claim = _reply(tmp_path, ["counts.tsv", "sample_OTHER_counts.tsv"]).claims[0]
    assert claim["answer"]["genes"] != ["G5", "G7", "G3"]
    assert "sample_OTHER_counts.tsv" in claim["references"]
