#!/usr/bin/env python3
"""Regression fixtures for the Evidence Program (Task 103 §9).

Exercises every schema and every cross-file integrity check the live pilot uses,
without network access. Run: python -m pytest evidence-program/tests/ -q
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # repo root
EP = os.path.join(ROOT, "evidence-program")
sys.path.insert(0, os.path.join(EP, "tools"))

import validate_evidence_program as V  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def test_schemas_parse():
    for name, rel in V.SCHEMA_FILES.items():
        sch = load(os.path.join(EP, rel))
        assert "$schema" in sch


def test_live_portfolio_valid():
    rows = V.load_jsonl(os.path.join(EP, "registry", "candidate-portfolio.jsonl"))
    assert len(rows) >= 3
    for ln, row in rows:
        errs = V.check_instance(row, V.load_json(os.path.join(EP, V.SCHEMA_FILES["candidate-portfolio"])))
        assert not errs, f"portfolio row {ln}: {errs}"


def test_live_prereg_valid():
    pre = load(os.path.join(EP, "preregistration",
                            "IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION.prereg.json"))
    errs = V.check_instance(pre, V.load_json(os.path.join(EP, V.SCHEMA_FILES["preregistration"])))
    assert not errs, errs


def test_fixtures_valid_against_schemas():
    pre = load(os.path.join(FIX, "prereg_fixture.json"))
    errs = V.check_instance(pre, V.load_json(os.path.join(EP, V.SCHEMA_FILES["preregistration"])))
    assert not errs, errs
    res = load(os.path.join(FIX, "result_fixture.json"))
    errs = V.check_instance(res, V.load_json(os.path.join(EP, V.SCHEMA_FILES["result-adjudication"])))
    assert not errs, errs
    for ln, row in V.load_jsonl(os.path.join(FIX, "source_fixture.jsonl")):
        errs = V.check_instance(row, V.load_json(os.path.join(EP, V.SCHEMA_FILES["evidence-source-manifest"])))
        assert not errs, f"source {ln}: {errs}"


def test_posthoc_threshold_equality():
    pre = load(os.path.join(FIX, "prereg_fixture.json"))
    res = load(os.path.join(FIX, "result_fixture.json"))
    used = res["thresholds_used"]
    pre_subset = {k: pre.get(k) for k in ("success_conditions", "partial_support_conditions",
                                          "null_conditions", "contradiction_conditions", "invalid_test_conditions")}
    assert V.canon(used) == V.canon(pre_subset)
    # negative: tampered threshold must differ
    bad = json.loads(json.dumps(used))
    bad["success_conditions"]["rate_min"] = 0.5
    assert V.canon(bad) != V.canon(pre_subset)


def test_leakage_no_unregistered_metrics():
    pre = load(os.path.join(FIX, "prereg_fixture.json"))
    res = load(os.path.join(FIX, "result_fixture.json"))
    pre_metrics = set(pre["metrics"]["secondary_metrics"]) | {pre["metrics"]["primary_metric"]}
    obs = set(res["metrics_observed"].keys())
    assert not (obs - pre_metrics)


def test_source_provenance_completeness():
    for ln, row in V.load_jsonl(os.path.join(FIX, "source_fixture.jsonl")):
        if row["acquisition_status"] == "OK":
            miss = [k for k in ("response_sha256", "licence", "retrieval_timestamp_utc", "canonical_identifier") if not row.get(k)]
            assert not miss, f"source {ln} missing {miss}"
        else:
            assert row["acquisition_status"], f"source {ln} has no explicit status"


def test_preregistration_before_result_ordering():
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init", "-q", d], check=True)
        subprocess.run(["git", "-c", f"user.name=test", "-c",
                        f"user.email=test@example.com", "commit", "--allow-empty", "-q",
                        "-m", "init"], cwd=d, check=True)
        # commit A: preregistration
        with open(os.path.join(d, "prereg.json"), "w") as fh:
            fh.write(json.dumps(load(os.path.join(FIX, "prereg_fixture.json"))))
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
                        "add", "prereg.json"], cwd=d, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
                        "commit", "-q", "-m", "prereg"], cwd=d, check=True)
        a = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        # commit B: run-manifest referencing A
        run = {
            "run_id": "FIX-RUN", "pilot_id": "FIX-PILOT", "preregistration_ref": "FIX-PREREG",
            "preregistration_commit": a, "preregistration_commit_timestamp": "2026-07-30T00:00:00Z",
            "results_generated_at_utc": "2026-07-30T01:00:00Z",
            "environment": {"python_version": "3.x", "os": "x", "network_access": "yes"},
            "commands": ["x"], "seeds": {}, "deviations_ref": "",
            "reproduction": {"from_clean_environment": True, "command": "x"},
        }
        with open(os.path.join(d, "run-manifest.json"), "w") as fh:
            fh.write(json.dumps(run))
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
                        "add", "run-manifest.json"], cwd=d, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
                        "commit", "-q", "-m", "run"], cwd=d, check=True)
        b = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        assert V.git_is_ancestor(a, b, d) is True
        # negative: B is not an ancestor of A
        assert V.git_is_ancestor(b, a, d) is False
        # time ordering
        assert run["preregistration_commit_timestamp"] < run["results_generated_at_utc"]


def test_validator_end_to_end_on_fixtures(tmp_path):
    """Assemble a minimal evidence-program tree from fixtures and run the validator."""
    ep = tmp_path / "evidence-program"
    ep.mkdir()
    for sch in V.SCHEMA_FILES:
        import shutil
        shutil.copy(os.path.join(EP, V.SCHEMA_FILES[sch]), str(ep / os.path.basename(V.SCHEMA_FILES[sch])))
    (ep / "schemas").mkdir(exist_ok=True)
    # move schemas into schemas/ subdir as the validator expects
    for f in os.listdir(str(ep)):
        if f.endswith(".schema.json"):
            os.replace(str(ep / f), str(ep / "schemas" / f))
    os.makedirs(ep / "registry", exist_ok=True)
    os.makedirs(ep / "preregistration", exist_ok=True)
    os.makedirs(ep / "runs" / "FIX-PILOT", exist_ok=True)
    import shutil
    shutil.copy(os.path.join(FIX, "prereg_fixture.json"), str(ep / "preregistration" / "x.prereg.json"))
    shutil.copy(os.path.join(FIX, "candidate_fixture.jsonl"), str(ep / "registry" / "candidate-portfolio.jsonl"))
    shutil.copy(os.path.join(FIX, "source_fixture.jsonl"), str(ep / "runs" / "FIX-PILOT" / "source-manifest.jsonl"))
    shutil.copy(os.path.join(FIX, "result_fixture.json"), str(ep / "runs" / "FIX-PILOT" / "result-adjudication.json"))
    # run-manifest needs a real git ancestor; place tree in a git repo
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e.com", "add", "-A"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e.com", "commit", "-q", "-m", "fixtures"], cwd=str(tmp_path), check=True)
    a = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), capture_output=True, text=True).stdout.strip()
    run = {
        "run_id": "FIX-RUN", "pilot_id": "FIX-PILOT", "preregistration_ref": "FIX-PREREG",
        "preregistration_commit": a, "preregistration_commit_timestamp": "2026-07-30T00:00:00Z",
        "results_generated_at_utc": "2026-07-30T01:00:00Z",
        "environment": {"python_version": "3.x", "os": "x", "network_access": "yes"},
        "commands": ["x"], "seeds": {}, "deviations_ref": "",
        "reproduction": {"from_clean_environment": True, "command": "x"},
    }
    with open(str(ep / "runs" / "FIX-PILOT" / "run-manifest.json"), "w") as fh:
        fh.write(json.dumps(run))
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e.com", "add", "-A"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e.com", "commit", "-q", "-m", "run"], cwd=str(tmp_path), check=True)
    with pytest.raises(SystemExit) as ex:
        V.main(argv=["--root", str(ep)])
    assert ex.value.code == 0, "validator should pass on compliant fixtures"
