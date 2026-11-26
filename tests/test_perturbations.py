import hashlib
import json
from pathlib import Path

import pytest

from agentic_bioinformatics_research.perturbations import (
    PERTURBATIONS,
    apply_perturbation,
)


def _task(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "task.md").write_text("run the pipeline\n", encoding="utf-8")
    (root / "counts.tsv").write_text("gene\tcount\ng1\t10\ng2\t20\n", encoding="utf-8")
    (root / "samples.tsv").write_text("sample\tgroup\ns1\tcontrol\n", encoding="utf-8")
    return root


def test_every_perturbation_is_listed():
    assert PERTURBATIONS == ("none", "prompt_bloat", "corrupted_inputs", "decoy_files")


def test_unknown_perturbation_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        apply_perturbation("noise", _task(tmp_path / "src"), tmp_path / "dst", 1)


def test_none_changes_nothing(tmp_path):
    src = _task(tmp_path / "src")
    manifest = apply_perturbation("none", src, tmp_path / "dst", 1)
    assert manifest["kind"] == "none"
    assert manifest["changes"] == []
    assert (tmp_path / "dst" / "task.md").read_text(encoding="utf-8") == "run the pipeline\n"


def test_source_tree_is_never_mutated(tmp_path):
    src = _task(tmp_path / "src")
    before = {p.name: p.read_bytes() for p in src.iterdir()}
    apply_perturbation("corrupted_inputs", src, tmp_path / "dst", 3)
    after = {p.name: p.read_bytes() for p in src.iterdir()}
    assert before == after


def test_same_seed_is_reproducible(tmp_path):
    src = _task(tmp_path / "src")
    first = apply_perturbation("decoy_files", src, tmp_path / "a", 7)
    second = apply_perturbation("decoy_files", src, tmp_path / "b", 7)
    assert first["sha256"] == second["sha256"]
    assert sorted(p.name for p in (tmp_path / "a").iterdir()) == sorted(
        p.name for p in (tmp_path / "b").iterdir()
    )


def test_different_seeds_differ(tmp_path):
    src = _task(tmp_path / "src")
    first = apply_perturbation("decoy_files", src, tmp_path / "a", 1)
    second = apply_perturbation("decoy_files", src, tmp_path / "b", 2)
    assert first["sha256"] != second["sha256"]


def test_prompt_bloat_adds_context(tmp_path):
    src = _task(tmp_path / "src")
    manifest = apply_perturbation("prompt_bloat", src, tmp_path / "dst", 5)
    added = [c for c in manifest["changes"] if c["action"] == "added"]
    assert added
    blob = (tmp_path / "dst" / added[0]["path"]).read_text(encoding="utf-8")
    assert len(blob) > 5000


def test_corrupted_inputs_rewrite_bytes(tmp_path):
    src = _task(tmp_path / "src")
    manifest = apply_perturbation("corrupted_inputs", src, tmp_path / "dst", 11)
    corrupted = [c for c in manifest["changes"] if c["action"] == "corrupted"]
    assert corrupted
    for change in corrupted:
        original = (src / change["path"]).read_bytes()
        rewritten = (tmp_path / "dst" / change["path"]).read_bytes()
        assert original != rewritten
        assert change["sha256_before"] == hashlib.sha256(original).hexdigest()
        assert change["sha256_after"] == hashlib.sha256(rewritten).hexdigest()


def test_decoy_files_are_added(tmp_path):
    src = _task(tmp_path / "src")
    manifest = apply_perturbation("decoy_files", src, tmp_path / "dst", 2)
    decoys = [c for c in manifest["changes"] if c["action"] == "added"]
    assert len(decoys) >= 2
    for change in decoys:
        assert (tmp_path / "dst" / change["path"]).is_file()


def test_existing_target_is_rejected(tmp_path):
    src = _task(tmp_path / "src")
    (tmp_path / "dst").mkdir()
    with pytest.raises(FileExistsError):
        apply_perturbation("none", src, tmp_path / "dst", 1)


def test_manifest_is_json_serialisable(tmp_path):
    src = _task(tmp_path / "src")
    manifest = apply_perturbation("decoy_files", src, tmp_path / "dst", 1)
    assert json.loads(json.dumps(manifest))["sha256"] == manifest["sha256"]
