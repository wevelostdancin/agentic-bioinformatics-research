import pytest

from agentic_bioinformatics_research.evidence import Evidence, require_confirmed


def test_executed_test_evidence_passes(tmp_path):
    proof = tmp_path / "poc.txt"
    proof.write_text("ok", encoding="utf-8")
    require_confirmed(Evidence("reproducible_test", proof, "pytest -q", 0))


def test_missing_artifact_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        require_confirmed(
            Evidence("reproducible_poc", tmp_path / "no.py", "pytest -q", 0)
        )


def test_failed_command_fails(tmp_path):
    proof = tmp_path / "poc.txt"
    proof.write_text("ok", encoding="utf-8")
    with pytest.raises(ValueError):
        require_confirmed(Evidence("reproducible_test", proof, "pytest -q", 1))


def test_missing_command_fails(tmp_path):
    proof = tmp_path / "poc.txt"
    proof.write_text("ok", encoding="utf-8")
    with pytest.raises(ValueError):
        require_confirmed(Evidence("reproducible_test", proof, "", 0))


def test_reference_match_accepted(tmp_path):
    proof = tmp_path / "results.csv"
    proof.write_text("id,f1\n1,0.9", encoding="utf-8")
    require_confirmed(Evidence("reference_match", proof, "grader.py", 0))
