#!/usr/bin/env python3
"""Validate the 121Q16 sustainability signal pilot interface."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ISSUE_FORMS = {
    "independent_review": ROOT / ".github/ISSUE_TEMPLATE/independent-review.yml",
    "noncommercial_use": ROOT / ".github/ISSUE_TEMPLATE/noncommercial-use-report.yml",
    "sponsorship_or_commercial_license_inquiry": ROOT / ".github/ISSUE_TEMPLATE/sponsorship-or-commercial-license-inquiry.yml",
}

TEXT_FILES = [
    ROOT / "README.md",
    ROOT / "SUPPORT.md",
    ROOT / "docs/participate.md",
    *ISSUE_FORMS.values(),
]

FORBIDDEN_PATTERNS = {
    "payment_platform_link": re.compile(
        r"https?://[^\s]*(paypal|stripe|ko-fi|kofi|patreon|opencollective|buymeacoffee|github\.com/sponsors)",
        re.IGNORECASE,
    ),
    "placeholder_payment": re.compile(r"(TODO|TBD|INSERT|PLACEHOLDER).{0,40}(payment|sponsor|funding|link)", re.IGNORECASE),
    "fake_sponsor": re.compile(r"(sponsored by|funded by|backed by).{1,80}(example|anonymous|unnamed|tbd)", re.IGNORECASE),
    "private_income": re.compile(r"(monthly income|annual income|salary|rent|mortgage).{0,20}[$¥￥][0-9]", re.IGNORECASE),
    "emotional_coercion": re.compile(r"(must sponsor|owe support|if you do not support|world will lose|guilt|shame)", re.IGNORECASE),
    "governance_purchase": re.compile(r"(support|sponsor|commercial license).{0,80}(can buy|may buy|will buy|buys|grants|guarantees).{0,80}(governance|merge|veto|conclusion|evidence grade|exemption)", re.IGNORECASE),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: Path) -> str:
    require(path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load_json(path: str) -> object:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_issue_forms() -> None:
    seen_signal_types: set[str] = set()
    required_types = {"markdown", "dropdown", "input", "textarea", "checkboxes"}
    for signal_type, path in ISSUE_FORMS.items():
        text = read(path)
        rel = path.relative_to(ROOT)
        require("name:" in text, f"{rel}: missing name")
        require("description:" in text, f"{rel}: missing description")
        require("body:" in text, f"{rel}: missing body")
        require("id: signal_type" in text, f"{rel}: missing signal_type field")
        require(f"- {signal_type}" in text, f"{rel}: signal_type value mismatch")
        seen_signal_types.add(signal_type)
        present_types = set(re.findall(r"^\s*-\s+type:\s+([a-z_]+)", text, re.MULTILINE))
        require("markdown" in present_types, f"{rel}: missing markdown guidance")
        require("dropdown" in present_types, f"{rel}: missing dropdown")
        require("checkboxes" in present_types, f"{rel}: missing boundary checkboxes")
        require(present_types <= required_types, f"{rel}: unsupported issue form types {present_types - required_types}")
        require("validations:" in text and "required: true" in text, f"{rel}: missing required validations")
    require(seen_signal_types == set(ISSUE_FORMS), "three signal categories must remain distinct")


def validate_support_boundary() -> None:
    readme = read(ROOT / "README.md").lower()
    support = read(ROOT / "SUPPORT.md").lower()
    participate = read(ROOT / "docs/participate.md").lower()
    combined = support + "\n" + participate
    require("docs/participate.md" in readme, "README must link to participation guidance")
    require("support.md" in readme, "README must link to SUPPORT.md")
    require("独立审查" in readme or "independent review" in readme, "README entry must include independent review")
    require("非商业" in readme or "non-commercial" in readme, "README entry must include non-commercial use")
    for phrase in (
        "maintainer is part of the life community",
        "ai/api quota",
        "basic living support",
        "cannot buy",
        "factual conclusions",
        "evidence grades",
        "merge rights",
        "governance",
        "older versions and forks",
        "mit rights",
        "non-commercial",
        "commercial production use",
    ):
        require(phrase in combined, f"support boundary missing phrase: {phrase}")
    require("no public payment link is declared" in support, "SUPPORT must state no payment link is declared")
    require("not a claim that the project has external recognition" in participate, "participation page must reject prefilled recognition claim")


def validate_forbidden_content() -> None:
    for path in TEXT_FILES:
        text = read(path)
        rel = path.relative_to(ROOT)
        for name, pattern in FORBIDDEN_PATTERNS.items():
            match = pattern.search(text)
            if match is not None:
                raise AssertionError(f"{rel}: forbidden {name}: {match.group(0)!r}")


def validate_observation_plan() -> None:
    plan = load_json("data/reality/121q16-observation-plan.json")
    require(plan["schema"] == "ignition.reality.121q16.observation_plan.v1", "observation plan schema mismatch")
    require(plan["window"]["duration_days"] == 30, "observation duration must remain 30 days")
    require("PR #50 is merged" in plan["window"]["calculation_rule"], "window must start only after merge activation")
    require(plan["prefilled_results"] is False, "observation plan must not prefill results")
    conditions = plan["activation_conditions"]
    require(conditions["candidate_pr_creation_is_not_start"] is True, "candidate PR creation cannot start the window")
    denom = plan["exposure_denominator"]
    for key in (
        "interface_live_days",
        "front_door_link_present",
        "issue_forms_available_on_default_branch",
        "verified_exposure_events",
        "known_referral_contexts",
    ):
        require(key in denom, f"exposure denominator missing {key}")
    require(denom["front_door_link_present"] is True, "front-door link must be present before activation")
    require(denom["zero_signal_interpretation"] == "NO_OBSERVED_SIGNAL_UNDER_AVAILABLE_EXPOSURE", "zero-signal interpretation must be exposure-bounded")
    forbidden = set(denom["forbidden_zero_signal_interpretations"])
    require({"NO_DEMAND", "NO_INTEREST"} <= forbidden, "zero-signal forbidden interpretations incomplete")
    require(not denom["verified_exposure_events"], "candidate plan must not prefill exposure events")
    exposure_rule = denom["counting_rule"].lower()
    for phrase in ("stars", "views", "likes", "ai reading", "ci runs", "repository existence"):
        require(phrase in exposure_rule, f"exposure rule must exclude {phrase}")
    metrics = {metric["id"]: metric for metric in plan["metrics"]}
    expected = {
        "valid_independent_reviews",
        "real_noncommercial_use_reports",
        "sponsorship_or_commercial_inquiries",
        "explicit_resource_commitments",
        "invalid_spam_or_conflict_signals",
        "maintainer_burden",
    }
    require(set(metrics) == expected, "observation metrics mismatch")
    for metric in metrics.values():
        require(metric["current_value"] is None, f"{metric['id']}: current value must be null")
        require(metric["counting_rule"], f"{metric['id']}: counting rule missing")
        require(metric["not_counted"], f"{metric['id']}: exclusion rule missing")
    boundaries = " ".join(plan["signal_boundaries"]).lower()
    for required in ("same org", "oral support", "stars", "views", "likes"):
        require(required in boundaries, f"missing signal boundary: {required}")


def validate_report_and_seal() -> None:
    report = read(ROOT / "reports/reality/121Q16-sustainability-signal-pilot.md")
    require("READY_AS_SUSTAINABILITY_SIGNAL_INTERFACE_CANDIDATE" in report, "report missing final candidate status")
    require("does not claim external recognition" in report, "report must state external recognition ceiling")
    seal = load_json("reports/reality/121Q16-completion-seal.json")
    require(seal["status"] == "READY_AS_SUSTAINABILITY_SIGNAL_INTERFACE_CANDIDATE", "seal status mismatch")
    require(seal["external_signal_results_prefilled"] is False, "seal cannot prefill external signals")
    require(seal["payment_links_added"] is False, "seal cannot add payment links")
    require(seal["claim_ceiling"] == "interface and observation plan established; no external signal result claimed", "claim ceiling mismatch")


def validate_run_state() -> None:
    state = load_json("data/reality/121q16-run-state.json")
    require(state["draft_pr"]["number"] == 50, "run state must point to Draft PR #50")
    require(state["status"] == "READY_AS_SUSTAINABILITY_SIGNAL_INTERFACE_CANDIDATE", "run state status mismatch")
    require([step["step"] for step in state["steps"]] == ["000", "001", "002"], "run state step order mismatch")
    require(all(step["status"] == "complete" for step in state["steps"]), "all 121Q16 steps must be complete")


def main() -> int:
    try:
        validate_issue_forms()
        validate_support_boundary()
        validate_forbidden_content()
        validate_observation_plan()
        validate_report_and_seal()
        validate_run_state()
    except AssertionError as exc:
        print(f"121Q16 sustainability signal validation failed: {exc}", file=sys.stderr)
        return 1
    print("121Q16 sustainability signal validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
