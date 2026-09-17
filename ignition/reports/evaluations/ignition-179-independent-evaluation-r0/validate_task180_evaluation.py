#!/usr/bin/env python3
"""Mechanical integrity checks for the Task180 evaluator result.

This checker validates artifact completeness, frozen labels, boundary fields, and
repository write scope. It does not decide whether cognitive inheritance exists.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = REPORT_DIR.parents[3]
EVALUATED_HEAD = "12e133c6d58a5e22437e42bb75fd912607bb4540"
BASELINE_HEAD = "68565f2afb50989d2c2b0d346d774e3388702743"
EXPECTED_BRANCH = "eval/IGNITION-20260917-180-cognitive-inheritance-r0-independent-evaluation"
EXPECTED_REPORT_PREFIX = "ignition/reports/evaluations/ignition-179-independent-evaluation-r0/"
REQUIRED_JSON = (
    "e0-remote-and-evaluator-freeze.json",
    "blind-content-reconstruction.json",
    "blind-engineering-reconstruction.json",
    "blind-evaluation-log.json",
    "unblind-comparison.json",
    "continuation-content.json",
    "continuation-engineering.json",
    "negative-controls.json",
    "metrics.json",
    "verdict.json",
)
ARTIFACTS_WITHOUT_TASK_ID = {
    "blind-content-reconstruction.json",
    "blind-engineering-reconstruction.json",
    "continuation-content.json",
    "continuation-engineering.json",
}
CLASSIFICATIONS = {
    "EXACT",
    "SEMANTICALLY_EQUIVALENT",
    "PARTIAL",
    "MISSING",
    "INCORRECT",
    "UNJUSTIFIED_ADDITION",
}
CRITERIA = {
    "RECONSTRUCTION_FIDELITY",
    "CONTINUATION_CORRECTNESS",
    "NON_EQUIVALENCE_CONTROL",
}
VERDICT_LABELS = {
    "R0_INHERITANCE_EVIDENCE_SUPPORTED",
    "R0_INHERITANCE_EVIDENCE_PARTIAL",
    "R0_INHERITANCE_EVIDENCE_NOT_SUPPORTED",
    "INCONCLUSIVE",
}
METRIC_IDS = {
    "reconstruction_fidelity",
    "continuation_correctness",
    "provenance_resolution_rate",
    "structural_compression_ratio",
    "inheritance_lag",
    "migration_cost",
    "regression_retention",
    "governance_overhead",
    "evaluator_disagreement",
    "schema_pressure",
    "boundary_retention",
}


class ValidationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_json(name: str) -> dict[str, Any]:
    path = REPORT_DIR / name
    require(path.is_file(), f"missing required artifact: {name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON in {name}: {exc}") from exc
    require(isinstance(value, dict), f"{name} must contain a JSON object")
    return value


def validate_artifacts() -> dict[str, Any]:
    data = {name: read_json(name) for name in REQUIRED_JSON}
    for name in REQUIRED_JSON:
        artifact = data[name]
        if name not in ARTIFACTS_WITHOUT_TASK_ID:
            require(
                artifact.get("task_id") == "IGNITION-20260917-180",
                f"{name} has wrong or missing task_id",
            )

    e0 = data["e0-remote-and-evaluator-freeze.json"]
    require(e0.get("task_id") == "IGNITION-20260917-180", "E0 task_id mismatch")
    require(e0.get("branch_start_sha") == EVALUATED_HEAD, "evaluator branch did not start at exact Task179 head")
    require(e0.get("evaluator_branch") == EXPECTED_BRANCH, "evaluator branch name mismatch")
    require(e0.get("draft_pr", {}).get("number") == 220, "evaluator PR identity mismatch")
    require(e0.get("draft_pr", {}).get("draft") is True, "evaluator PR was not frozen as Draft")
    require(e0.get("draft_pr", {}).get("merged") is False, "E0 records evaluator PR as merged")
    require(e0.get("scope", {}).get("private_email_used") is False, "E0 does not affirm private-email exclusion")
    require(e0.get("scope", {}).get("builder_mutation") == "NONE", "E0 records Builder mutation")

    blind_log = data["blind-evaluation-log.json"]
    require(blind_log.get("sequence", {}).get("remote_preflight_complete") is True, "remote preflight is not recorded")
    require(blind_log.get("sequence", {}).get("task_only_complete") is True, "TASK_ONLY is not recorded")
    require(blind_log.get("sequence", {}).get("successor_packages_and_source_fixtures_read") is True, "blind packet read is not recorded")
    require(blind_log.get("sequence", {}).get("blind_reconstructions_written") is True, "blind reconstructions are not recorded")
    require(blind_log.get("sequence", {}).get("unblind_material_read_before_checkpoint") is False, "unblind material was read before checkpoint")
    require(blind_log.get("unblind_authorization") == "AFTER_E1_REMOTE_PUSH_VERIFICATION_ONLY", "unblind authorization order mismatch")
    require(blind_log.get("private_email_used") is False, "blind log records private-email use")
    require(blind_log.get("no_hidden_chain_of_thought") is True, "blind log does not affirm no hidden chain-of-thought")
    require(
        blind_log.get("contamination", {}).get("status") == "BLINDING_CONTAMINATION",
        "limited contamination is not disclosed",
    )
    require(blind_log.get("contamination", {}).get("task179_builder_narrative_exposed") is False, "log claims Builder narrative exposure")

    for name in ("blind-content-reconstruction.json", "blind-engineering-reconstruction.json"):
        blind = data[name]
        for key in (
            "reconstructed_objects",
            "reconstructed_relations",
            "reconstructed_provenance",
            "claim_ceiling",
            "explicit_unknowns",
            "forbidden_inferences",
            "reconstructed_method_action_sequence",
            "counterexample_or_overclaim_trap",
            "unresolved_obligations",
            "source_fields_used",
            "fields_not_recoverable",
        ):
            require(key in blind, f"{name} missing required blind field: {key}")

    unblind = data["unblind-comparison.json"]
    require(unblind.get("evaluated_head") == EVALUATED_HEAD, "unblind comparison target head mismatch")
    checkpoint = unblind.get("blind_checkpoint", {})
    require(checkpoint.get("commit") == "cf37d6d33707870514c3e62249ac3b8cbebf2526", "blind checkpoint SHA mismatch")
    require(checkpoint.get("remote_push_verified") is True, "blind checkpoint remote verification missing")
    require(checkpoint.get("message") == "task180 blind: freeze independent reconstructions before unblinding", "blind checkpoint message mismatch")
    require(len(unblind.get("cases", [])) == 2, "unblind comparison must contain exactly two cases")

    observed_counts: Counter[str] = Counter()
    observed_case_counts: dict[str, Counter[str]] = {}
    for case in unblind["cases"]:
        case_id = case.get("case_id")
        fields = case.get("field_comparison", [])
        require(case_id in {"CONTENT-REST-01", "ENGINEERING-BASELINE-01"}, f"unexpected comparison case: {case_id}")
        require(bool(fields), f"{case_id} has no field comparison")
        counts = Counter(entry.get("classification") for entry in fields)
        require(set(counts).issubset(CLASSIFICATIONS), f"{case_id} uses a non-frozen classification")
        observed_case_counts[case_id] = counts
        observed_counts.update(counts)

    metrics = data["metrics.json"]
    metric_records = metrics.get("metrics", [])
    seen_metric_ids = [record.get("metric_id") for record in metric_records]
    require(set(seen_metric_ids) == METRIC_IDS, "metrics.json does not contain exactly the 11 frozen metrics")
    require(len(seen_metric_ids) == len(METRIC_IDS), "metrics.json repeats a frozen metric")
    metric_by_id = {record["metric_id"]: record for record in metric_records}
    reconstruction = metric_by_id["reconstruction_fidelity"].get("value", {})
    recorded_counts = reconstruction.get("classification_counts_across_both_cases", {})
    for classification in CLASSIFICATIONS:
        require(
            recorded_counts.get(classification, 0) == observed_counts.get(classification, 0),
            f"reconstruction metric count mismatch for {classification}",
        )
    recorded_by_case = reconstruction.get("by_case", {})
    for case_id, observed in observed_case_counts.items():
        recorded = recorded_by_case.get(case_id, {})
        require(recorded.get("field_count") == sum(observed.values()), f"{case_id} field_count mismatch")
        for classification in CLASSIFICATIONS:
            require(
                recorded.get(classification, 0) == observed.get(classification, 0),
                f"{case_id} metric count mismatch for {classification}",
            )

    provenance = metric_by_id["provenance_resolution_rate"].get("value", {})
    require(provenance.get("resolved") == 4 and provenance.get("total") == 4, "provenance reference count mismatch")
    require(provenance.get("ratio") == 1.0, "provenance ratio must be the observed 4/4")
    content_size = metric_by_id["structural_compression_ratio"].get("value", {}).get("CONTENT-REST-01", {})
    engineering_size = metric_by_id["structural_compression_ratio"].get("value", {}).get("ENGINEERING-BASELINE-01", {})
    for sample in (content_size, engineering_size):
        require(sample.get("package_bytes", 0) > 0 and sample.get("source_fixture_bytes", 0) > 0, "byte proxy lacks exact sizes")
        expected_ratio = sample["package_bytes"] / sample["source_fixture_bytes"]
        require(abs(sample.get("ratio", 0) - expected_ratio) < 1e-9, "structural byte ratio mismatch")

    content = data["continuation-content.json"]
    engineering = data["continuation-engineering.json"]
    require(content.get("faster_than_A", {}).get("decision") == "NO", "content continuation overclaims A speedup")
    require(content.get("capability_or_external_truth", {}).get("decision") == "NO", "content continuation overclaims capability or truth")
    require(content.get("input_observation", {}).get("A_baseline_executable_metrics") == "UNAVAILABLE", "content continuation loses missing A baseline")
    require(content.get("input_observation", {}).get("source_body_available") is False, "content continuation loses source-body boundary")
    require(content.get("forbidden_inferences"), "content continuation has no explicit forbidden inferences")
    require(engineering.get("current_reverification", {}).get("can_claim_current_7_of_7") == "NO", "engineering continuation overclaims current 7/7")
    require(engineering.get("outage_record", {}).get("classification") == "UNAVAILABLE, not success and not workflow failure", "engineering outage is misclassified")
    require(engineering.get("baseline_content_change", {}).get("needed") is False, "engineering continuation mutates baseline")
    require(engineering.get("forbidden_inferences"), "engineering continuation has no explicit forbidden inferences")

    for case_record in (content, engineering):
        unknowns = case_record.get("explicit_unknowns") or case_record.get("unknown_or_not_currently_verified")
        ceiling = case_record.get("claim_ceiling") or case_record.get("provenance", {}).get("claim_ceiling")
        require(bool(unknowns), f"{case_record.get('case_id')} loses explicit unknowns")
        require(bool(case_record.get("overclaim_counterexample")), f"{case_record.get('case_id')} lacks counterexample")
        require(bool(ceiling), f"{case_record.get('case_id')} lacks claim ceiling")
        require(bool(case_record.get("provenance")), f"{case_record.get('case_id')} lacks provenance")
        require(bool(case_record.get("unresolved_obligations")), f"{case_record.get('case_id')} lacks unresolved obligations")

    controls = data["negative-controls.json"].get("controls", [])
    require(len(controls) == 8, "negative controls must contain exactly eight frozen claims")
    require({item.get("id") for item in controls} == {f"NEC-{i:02d}" for i in range(1, 9)}, "negative-control IDs mismatch")
    require(all(item.get("disposition") == "REJECTED" and item.get("rationale") for item in controls), "negative control missing rejection rationale")

    verdict = data["verdict.json"]
    criterion_records = verdict.get("frozen_criterion_dispositions", [])
    require({item.get("criterion_id") for item in criterion_records} == CRITERIA, "verdict criteria differ from frozen criteria")
    require(all(item.get("disposition") in {"PASS", "PARTIAL", "FAIL", "INCONCLUSIVE"} for item in criterion_records), "criterion disposition invalid")
    require(verdict.get("overall_evaluator_verdict") in VERDICT_LABELS, "overall evaluator verdict invalid")
    require(verdict.get("owner_gpt_adjudication") == "NOT_YET_RUN", "verdict prematurely claims adjudication")
    require(verdict.get("builder_and_canonical_mutations", {}).get("task179_r0_artifacts") == "NONE", "verdict records Builder artifact mutation")
    require(verdict.get("blinding_contamination", {}).get("status") == "BLINDING_CONTAMINATION", "verdict omits contamination status")
    require(verdict.get("evaluated_head") == EVALUATED_HEAD, "verdict target head mismatch")

    return {
        "status": "PASS",
        "json_artifacts_checked": len(REQUIRED_JSON),
        "frozen_metrics_checked": len(METRIC_IDS),
        "comparison_fields_checked": sum(observed_counts.values()),
        "negative_controls_checked": len(controls),
        "frozen_criteria_checked": len(criterion_records),
        "builder_claims_or_artifacts_rewritten": False,
    }


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_repository_boundaries(require_clean: bool = False) -> dict[str, Any]:
    head = git_output("rev-parse", "HEAD")
    branch = git_output("branch", "--show-current")
    require(branch == EXPECTED_BRANCH, f"unexpected evaluator branch: {branch}")
    changed = git_output("diff", "--name-only", f"{EVALUATED_HEAD}..HEAD").splitlines()
    outside = [path for path in changed if not path.startswith(EXPECTED_REPORT_PREFIX)]
    require(not outside, f"changes outside evaluator report directory: {outside}")
    git_output("merge-base", "--is-ancestor", BASELINE_HEAD, EVALUATED_HEAD)
    git_output("merge-base", "--is-ancestor", EVALUATED_HEAD, "HEAD")
    if require_clean:
        status = git_output("status", "--porcelain")
        require(not status, f"worktree is not clean: {status}")
    return {
        "status": "PASS",
        "head": head,
        "branch": branch,
        "task179_head_is_ancestor": True,
        "task172_baseline_is_ancestor": True,
        "changed_paths": len(changed),
        "changes_outside_evaluator_report_directory": 0,
        "clean_worktree_required": require_clean,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-git-boundary", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    try:
        result: dict[str, Any] = {"artifacts": validate_artifacts()}
        if not args.skip_git_boundary:
            result["repository"] = validate_repository_boundaries(require_clean=args.require_clean)
        print(json.dumps(result, sort_keys=True))
        return 0
    except ValidationError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
