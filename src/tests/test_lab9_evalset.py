"""M0 command-line checks run before completing the M1 taxonomy."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def evalset_cli(tmp_path):
    source = tmp_path / "data/public_claims.jsonl"
    source.parent.mkdir()
    claim = {"claim_id": "C-001", "matrix_id": "T01", "expected": {"refund_vnd": 35000}}
    source.write_text(json.dumps(claim) + "\n", encoding="utf-8")

    def run_evalset(*args):
        return subprocess.run(
            [sys.executable, "-m", "lab9.evalset", *args],
            cwd=tmp_path,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
            capture_output=True,
            text=True,
        )

    return run_evalset


def test_build_writes_items_and_labels_without_checking_tags(tmp_path, evalset_cli):
    result = evalset_cli("--build")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "problem(s)" not in result.stdout
    item = json.loads((tmp_path / "data/eval/eval_set_v1.jsonl").read_text(encoding="utf-8"))
    labels = json.loads((tmp_path / "data/eval/labels_v1.json").read_text(encoding="utf-8"))
    assert item["claim_id"] == "C-001"
    assert "expected" not in item
    assert labels == {"C-001": {"refund_vnd": 35000}}


def test_explicit_check_runs_after_build(tmp_path, evalset_cli):
    result = evalset_cli("--build", "--check")
    item = json.loads((tmp_path / "data/eval/eval_set_v1.jsonl").read_text(encoding="utf-8"))
    expected_problems = int(not item["failure_modes"])
    assert result.returncode == expected_problems, result.stdout + result.stderr
    assert f"{expected_problems} problem(s)" in result.stdout


def test_check_rejects_missing_tags(tmp_path, evalset_cli):
    evalset_cli("--build")
    items_path = tmp_path / "data/eval/eval_set_v1.jsonl"
    item = json.loads(items_path.read_text(encoding="utf-8"))
    item["failure_modes"] = []
    items_path.write_text(json.dumps(item) + "\n", encoding="utf-8")

    result = evalset_cli("--check")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "failure_modes empty" in result.stdout


@pytest.mark.student
@pytest.mark.parametrize("version", ["v1", "v2"])
def test_built_eval_set_hash_matches_lf_checkout(tmp_path, evalset_cli, version):
    assert evalset_cli("--build").returncode == 0
    if version == "v2":
        mapping_path = tmp_path / "config/fm_map.yaml"
        mapping_path.parent.mkdir()
        mapping_path.write_text("clause_sum: FM-04\n", encoding="utf-8")
        claims = [
            {"claim_id": claim_id, "mechanisms": ["clause_sum"], "attack": "sum clauses",
             "expected": {"refund_vnd": 35000}}
            for claim_id in ("C-101", "C-102")
        ]
        (tmp_path / "data/eval/adversarial_v2.json").write_text(
            json.dumps({"claims": claims}), encoding="utf-8")
        result = evalset_cli("--v2", "--build")
        assert result.returncode == 0, result.stdout + result.stderr

    from lab9.evalset import sha12

    path = tmp_path / f"data/eval/eval_set_{version}.jsonl"
    checkout_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in path.read_bytes()
    assert sha12(path) == hashlib.sha256(checkout_bytes).hexdigest()[:12]
