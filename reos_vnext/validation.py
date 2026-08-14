"""Fail-closed structural validation for the R1 case document."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .contract import (
    CASE_STATES,
    EVIDENCE_STATES,
    MODES,
    OBLIGATION_STATES,
    PRIVACY_CLASSES,
    REVIEW_VERDICTS,
    SCHEMA_VERSION,
)

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HANDOFF_NONCANONICAL_STATUSES = frozenset({"CANDIDATE_NOT_CANONICAL", "NONCANONICAL", "RESEARCH_STAGE_ONLY"})
_HANDOFF_REQUIRED_BOUNDARIES = (
    "truth",
    "caus",
    "external validity",
    "owner acceptance",
    "epistemic",
)

_FORBIDDEN_KEYS = frozenset(
    {
        "truth",
        "truth_status",
        "epistemic_status",
        "epistemic_acceptance",
        "epistemically_accepted",
        "owner_acceptance",
        "owner_accepted",
        "canonical",
        "canonical_claim",
        "proof_status",
        "proof_result",
        "causal_identification",
        "external_validity",
        "evidence_maturity",
    }
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class ContractError(ValueError):
    """Raised when a case or handoff violates the frozen contract."""

    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = tuple(issues)
        summary = "; ".join(f"{issue.code} at {issue.path}" for issue in self.issues)
        super().__init__(summary or "REOS contract validation failed")

    @property
    def code(self) -> str | None:
        return self.issues[0].code if self.issues else None


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _issue(issues: list[ValidationIssue], code: str, path: str, message: str) -> None:
    issues.append(ValidationIssue(code, path, message))


def _mapping(value: Any, path: str, issues: list[ValidationIssue]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        _issue(issues, "TYPE", path, "expected an object")
        return None
    return value


def _list(value: Any, path: str, issues: list[ValidationIssue]) -> list[Any] | None:
    if not isinstance(value, list):
        _issue(issues, "TYPE", path, "expected an array")
        return None
    return value


def _required(record: Mapping[str, Any], names: Iterable[str], path: str, issues: list[ValidationIssue]) -> None:
    for name in names:
        if name not in record:
            _issue(issues, "MISSING_FIELD", f"{path}.{name}", "required field is missing")


def _keys(record: Mapping[str, Any], allowed: set[str], path: str, issues: list[ValidationIssue]) -> None:
    for name in sorted(set(record) - allowed):
        _issue(issues, "UNKNOWN_FIELD", f"{path}.{name}", "field is outside the frozen R1 contract")


def _id(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        _issue(issues, "IDENTITY", path, "must be a bounded identifier")


def _nonempty_string(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not value.strip():
        _issue(issues, "VALUE", path, "must be a non-empty string")


def _strings(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    values = _list(value, path, issues)
    if values is not None:
        for index, item in enumerate(values):
            _nonempty_string(item, f"{path}[{index}]", issues)


def _check_forbidden_keys(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_KEYS:
                if "evidence_requests" in path:
                    code = "EVIDENCE_TRUTH_UPGRADE"
                elif ".decision" in path and key in {"owner_acceptance", "owner_accepted", "epistemic_acceptance", "epistemically_accepted"}:
                    code = "REVIEW_OWNER_ACCEPTANCE"
                elif "claim_candidates" in path and key in {"canonical", "canonical_claim"}:
                    code = "CANONICAL_CLAIM_MASQUERADE"
                else:
                    code = "NO_UPGRADE"
                _issue(issues, code, f"{path}.{key}", "REOS cannot carry this authority field")
            _check_forbidden_keys(child, f"{path}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_forbidden_keys(child, f"{path}[{index}]", issues)


def _check_json_values(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        _issue(issues, "NON_DETERMINISTIC_VALUE", path, "NaN and Infinity are not legal canonical JSON values")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            _check_json_values(child, f"{path}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_json_values(child, f"{path}[{index}]", issues)


def _validate_activation(activation: Any, path: str, issues: list[ValidationIssue]) -> None:
    record = _mapping(activation, path, issues)
    if record is None:
        return
    allowed = {"mode", "reason", "observed_need", "simpler_baseline", "unnecessary_modules"}
    _required(record, allowed, path, issues)
    _keys(record, allowed, path, issues)
    mode = record.get("mode")
    if mode not in MODES:
        _issue(issues, "MODE_INVALID", f"{path}.mode", "unknown activation mode")
    elif mode == "REOS_FULL":
        _issue(issues, "FULL_UNAVAILABLE", f"{path}.mode", "REOS_FULL is deferred and unavailable in R1")
    _nonempty_string(record.get("reason"), f"{path}.reason", issues)
    _strings(record.get("observed_need"), f"{path}.observed_need", issues)
    _nonempty_string(record.get("simpler_baseline"), f"{path}.simpler_baseline", issues)
    _strings(record.get("unnecessary_modules"), f"{path}.unnecessary_modules", issues)


def _validate_question(question: Any, path: str, issues: list[ValidationIssue]) -> None:
    record = _mapping(question, path, issues)
    if record is None:
        return
    allowed = {
        "preregistration_ref",
        "preregistration_digest",
        "frozen_validation_summary",
        "initial_validation_summary_digest",
        "validation_summary_digest",
        "version",
        "amendments",
    }
    _required(record, allowed, path, issues)
    _keys(record, allowed, path, issues)
    _nonempty_string(record.get("preregistration_ref"), f"{path}.preregistration_ref", issues)
    for digest_name in (
        "preregistration_digest",
        "initial_validation_summary_digest",
        "validation_summary_digest",
    ):
        value = record.get(digest_name)
        if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
            _issue(issues, "QUESTION_MUTATION", f"{path}.{digest_name}", "must be a sha256 digest")
    summary = _mapping(record.get("frozen_validation_summary"), f"{path}.frozen_validation_summary", issues)
    if summary is not None:
        summary_allowed = {
            "question",
            "scope",
            "estimand",
            "measurement_boundaries",
            "claim_ceiling",
            "stop_conditions",
        }
        _required(summary, summary_allowed, f"{path}.frozen_validation_summary", issues)
        _keys(summary, summary_allowed, f"{path}.frozen_validation_summary", issues)
        for name in ("question", "scope", "estimand", "claim_ceiling"):
            _nonempty_string(summary.get(name), f"{path}.frozen_validation_summary.{name}", issues)
        for name in ("measurement_boundaries", "stop_conditions"):
            _strings(summary.get(name), f"{path}.frozen_validation_summary.{name}", issues)
        try:
            expected = sha256_json(summary)
        except ValueError:
            expected = None
        if expected is not None and record.get("validation_summary_digest") != expected:
            _issue(issues, "QUESTION_MUTATION", f"{path}.validation_summary_digest", "digest does not match the frozen validation summary")
    version = record.get("version")
    if not isinstance(version, int) or version < 1:
        _issue(issues, "QUESTION_MUTATION", f"{path}.version", "version must be a positive integer")
    amendments = _list(record.get("amendments"), f"{path}.amendments", issues)
    if amendments is None:
        return
    previous = record.get("initial_validation_summary_digest")
    for index, amendment in enumerate(amendments):
        amendment_path = f"{path}.amendments[{index}]"
        item = _mapping(amendment, amendment_path, issues)
        if item is None:
            continue
        allowed_amendment = {"amendment_id", "from_digest", "to_digest", "reason", "version"}
        _required(item, allowed_amendment, amendment_path, issues)
        _keys(item, allowed_amendment, amendment_path, issues)
        _id(item.get("amendment_id"), f"{amendment_path}.amendment_id", issues)
        for digest_name in ("from_digest", "to_digest"):
            value = item.get(digest_name)
            if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
                _issue(issues, "QUESTION_MUTATION", f"{amendment_path}.{digest_name}", "must be a sha256 digest")
        if item.get("from_digest") != previous:
            _issue(issues, "QUESTION_MUTATION", f"{amendment_path}.from_digest", "amendments must form a digest chain")
        if item.get("to_digest") == item.get("from_digest"):
            _issue(issues, "QUESTION_MUTATION", f"{amendment_path}.to_digest", "amendment must change the validation summary digest")
        _nonempty_string(item.get("reason"), f"{amendment_path}.reason", issues)
        if item.get("version") != index + 2:
            _issue(issues, "QUESTION_MUTATION", f"{amendment_path}.version", "amendment version is not append-only")
        previous = item.get("to_digest")
    if amendments and previous != record.get("validation_summary_digest"):
        _issue(issues, "QUESTION_MUTATION", f"{path}.amendments", "last amendment does not reach current validation summary digest")
    if not amendments and record.get("initial_validation_summary_digest") != record.get("validation_summary_digest"):
        _issue(issues, "QUESTION_MUTATION", f"{path}.initial_validation_summary_digest", "unamended summary must have equal initial/current digest")
    if isinstance(version, int) and version != len(amendments) + 1:
        _issue(issues, "QUESTION_MUTATION", f"{path}.version", "version does not match amendment count")


def _validate_obligations(
    obligations: Any,
    question_ref: str,
    path: str,
    issues: list[ValidationIssue],
) -> tuple[list[Mapping[str, Any]], set[str]]:
    values = _list(obligations, path, issues) or []
    allowed = {
        "obligation_id",
        "type",
        "question_ref",
        "depends_on",
        "inputs",
        "required_capabilities",
        "permission_scope",
        "completion_contract",
        "stop_fail_conditions",
        "status",
        "output_artifact_refs",
        "review_required",
    }
    ids: set[str] = set()
    records: list[Mapping[str, Any]] = []
    for index, obligation in enumerate(values):
        item_path = f"{path}[{index}]"
        record = _mapping(obligation, item_path, issues)
        if record is None:
            continue
        records.append(record)
        _required(record, allowed, item_path, issues)
        _keys(record, allowed, item_path, issues)
        _id(record.get("obligation_id"), f"{item_path}.obligation_id", issues)
        obligation_id = record.get("obligation_id")
        if obligation_id in ids:
            _issue(issues, "DUPLICATE_ID", f"{item_path}.obligation_id", "obligation id is not unique")
        ids.add(obligation_id)
        _nonempty_string(record.get("type"), f"{item_path}.type", issues)
        if record.get("question_ref") != question_ref:
            _issue(issues, "QUESTION_REF", f"{item_path}.question_ref", "obligation is outside the case question")
        for name in ("depends_on", "inputs", "required_capabilities", "stop_fail_conditions", "output_artifact_refs"):
            _strings(record.get(name), f"{item_path}.{name}", issues)
        _nonempty_string(record.get("permission_scope"), f"{item_path}.permission_scope", issues)
        _nonempty_string(record.get("completion_contract"), f"{item_path}.completion_contract", issues)
        if record.get("status") not in OBLIGATION_STATES:
            _issue(issues, "OBLIGATION_STATE", f"{item_path}.status", "unknown obligation state")
        if not isinstance(record.get("review_required"), bool):
            _issue(issues, "TYPE", f"{item_path}.review_required", "must be boolean")
        capabilities = record.get("required_capabilities")
        if isinstance(capabilities, list):
            for capability in capabilities:
                if isinstance(capability, str) and capability.lower().startswith(("provider:", "model:")):
                    _issue(issues, "PROVIDER_HARD_DEPENDENCY", f"{item_path}.required_capabilities", "provider/model names are telemetry only")
    for index, record in enumerate(records):
        for dependency in record.get("depends_on", []) if isinstance(record.get("depends_on"), list) else []:
            if dependency not in ids:
                _issue(issues, "UNKNOWN_DEPENDENCY", f"{path}[{index}].depends_on", "dependency does not exist")
    graph = {record.get("obligation_id"): record.get("depends_on", []) for record in records}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            _issue(issues, "CYCLE", path, "obligation dependencies must be acyclic")
            return
        if node in visited or node not in graph:
            return
        visiting.add(node)
        for dependency in graph[node] if isinstance(graph[node], list) else []:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return records, ids


def _validate_artifacts(artifacts: Any, path: str, issues: list[ValidationIssue]) -> tuple[list[Mapping[str, Any]], set[str]]:
    values = _list(artifacts, path, issues) or []
    allowed = {
        "artifact_id",
        "ref",
        "sha256",
        "provenance",
        "scope",
        "privacy_class",
        "source_family",
        "derivation_refs",
        "limitations",
    }
    ids: set[str] = set()
    records: list[Mapping[str, Any]] = []
    for index, artifact in enumerate(values):
        item_path = f"{path}[{index}]"
        record = _mapping(artifact, item_path, issues)
        if record is None:
            continue
        records.append(record)
        _required(record, allowed, item_path, issues)
        _keys(record, allowed, item_path, issues)
        _id(record.get("artifact_id"), f"{item_path}.artifact_id", issues)
        artifact_id = record.get("artifact_id")
        if artifact_id in ids:
            _issue(issues, "DUPLICATE_ID", f"{item_path}.artifact_id", "artifact id is not unique")
        ids.add(artifact_id)
        _nonempty_string(record.get("ref"), f"{item_path}.ref", issues)
        sha = record.get("sha256")
        if not isinstance(sha, str) or not _SHA256_RE.fullmatch(sha):
            _issue(issues, "ARTIFACT_IDENTITY", f"{item_path}.sha256", "artifact must carry a sha256 identity")
        provenance = record.get("provenance")
        if not isinstance(provenance, Mapping) or not provenance:
            _issue(issues, "ARTIFACT_PROVENANCE", f"{item_path}.provenance", "artifact provenance is required")
        _nonempty_string(record.get("scope"), f"{item_path}.scope", issues)
        if record.get("privacy_class") not in PRIVACY_CLASSES:
            _issue(issues, "PRIVACY_CLASS", f"{item_path}.privacy_class", "unknown privacy/publication class")
        _nonempty_string(record.get("source_family"), f"{item_path}.source_family", issues)
        _strings(record.get("derivation_refs"), f"{item_path}.derivation_refs", issues)
        _strings(record.get("limitations"), f"{item_path}.limitations", issues)
    return records, ids


def _validate_evidence(
    requests: Any,
    obligation_ids: set[str],
    artifact_ids: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> set[str]:
    values = _list(requests, path, issues) or []
    allowed = {
        "request_id",
        "obligation_id",
        "question",
        "desired_evidence_type",
        "source_family_requirement",
        "retrieval_state",
        "access_limitation",
        "result_artifact_ids",
    }
    ids: set[str] = set()
    for index, request in enumerate(values):
        item_path = f"{path}[{index}]"
        record = _mapping(request, item_path, issues)
        if record is None:
            continue
        _required(record, allowed, item_path, issues)
        _keys(record, allowed, item_path, issues)
        _id(record.get("request_id"), f"{item_path}.request_id", issues)
        request_id = record.get("request_id")
        if request_id in ids:
            _issue(issues, "DUPLICATE_ID", f"{item_path}.request_id", "evidence request id is not unique")
        ids.add(request_id)
        if record.get("obligation_id") not in obligation_ids:
            _issue(issues, "UNKNOWN_REF", f"{item_path}.obligation_id", "evidence request obligation is unknown")
        for name in ("question", "desired_evidence_type", "source_family_requirement"):
            _nonempty_string(record.get(name), f"{item_path}.{name}", issues)
        if record.get("retrieval_state") not in EVIDENCE_STATES:
            _issue(issues, "EVIDENCE_STATE", f"{item_path}.retrieval_state", "unknown retrieval state")
        _nonempty_string(record.get("access_limitation"), f"{item_path}.access_limitation", issues)
        results = record.get("result_artifact_ids")
        _strings(results, f"{item_path}.result_artifact_ids", issues)
        if isinstance(results, list):
            for result in results:
                if result not in artifact_ids:
                    _issue(issues, "UNKNOWN_REF", f"{item_path}.result_artifact_ids", "result artifact is unknown")
    return ids


def _validate_claims(claims: Any, artifact_ids: set[str], path: str, issues: list[ValidationIssue]) -> set[str]:
    values = _list(claims, path, issues) or []
    allowed = {
        "candidate_id",
        "proposition",
        "scope",
        "supporting_artifact_ids",
        "contradicting_artifact_ids",
        "alternative_explanations",
        "measurement_definition",
        "claim_ceiling",
        "uncertainty",
        "foundation_handoff_route",
        "canonical_status",
    }
    ids: set[str] = set()
    for index, claim in enumerate(values):
        item_path = f"{path}[{index}]"
        record = _mapping(claim, item_path, issues)
        if record is None:
            continue
        _required(record, allowed, item_path, issues)
        _keys(record, allowed, item_path, issues)
        _id(record.get("candidate_id"), f"{item_path}.candidate_id", issues)
        candidate_id = record.get("candidate_id")
        if candidate_id in ids:
            _issue(issues, "DUPLICATE_ID", f"{item_path}.candidate_id", "claim candidate id is not unique")
        ids.add(candidate_id)
        for name in ("proposition", "scope", "measurement_definition", "claim_ceiling", "foundation_handoff_route"):
            _nonempty_string(record.get(name), f"{item_path}.{name}", issues)
        if record.get("canonical_status") != "NONCANONICAL":
            _issue(issues, "CANONICAL_CLAIM_MASQUERADE", f"{item_path}.canonical_status", "claim candidates are never canonical")
        for name in ("supporting_artifact_ids", "contradicting_artifact_ids"):
            _strings(record.get(name), f"{item_path}.{name}", issues)
            values_for_ref = record.get(name)
            if isinstance(values_for_ref, list):
                for ref in values_for_ref:
                    if ref not in artifact_ids:
                        _issue(issues, "UNKNOWN_REF", f"{item_path}.{name}", "claim artifact reference is unknown")
        _strings(record.get("alternative_explanations"), f"{item_path}.alternative_explanations", issues)
        _strings(record.get("uncertainty"), f"{item_path}.uncertainty", issues)
    return ids


def _validate_reviews(
    reviews: Any,
    obligation_ids: set[str],
    known_refs: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> set[str]:
    values = _list(reviews, path, issues) or []
    ids: set[str] = set()
    request_allowed = {"review_id", "named_question", "input_refs", "independence_requirement", "forbidden_assumptions"}
    decision_allowed = {
        "review_id",
        "reviewer_ref",
        "exact_input_refs",
        "independent",
        "verdict",
        "material_findings",
        "repair_obligation_ids",
        "residuals",
        "scope_ceiling",
    }
    for index, review in enumerate(values):
        item_path = f"{path}[{index}]"
        entry = _mapping(review, item_path, issues)
        if entry is None:
            continue
        _required(entry, {"request", "decision"}, item_path, issues)
        _keys(entry, {"request", "decision"}, item_path, issues)
        request = _mapping(entry.get("request"), f"{item_path}.request", issues)
        if request is None:
            continue
        _required(request, request_allowed, f"{item_path}.request", issues)
        _keys(request, request_allowed, f"{item_path}.request", issues)
        _id(request.get("review_id"), f"{item_path}.request.review_id", issues)
        review_id = request.get("review_id")
        if review_id in ids:
            _issue(issues, "DUPLICATE_ID", f"{item_path}.request.review_id", "review id is not unique")
        ids.add(review_id)
        for name in ("named_question", "independence_requirement"):
            _nonempty_string(request.get(name), f"{item_path}.request.{name}", issues)
        _strings(request.get("input_refs"), f"{item_path}.request.input_refs", issues)
        _strings(request.get("forbidden_assumptions"), f"{item_path}.request.forbidden_assumptions", issues)
        input_refs = request.get("input_refs")
        if isinstance(input_refs, list):
            for ref in input_refs:
                if ref not in known_refs:
                    _issue(issues, "UNKNOWN_REF", f"{item_path}.request.input_refs", "review input reference is unknown")
        decision = entry.get("decision")
        if decision is None:
            continue
        decision_record = _mapping(decision, f"{item_path}.decision", issues)
        if decision_record is None:
            continue
        _required(decision_record, decision_allowed, f"{item_path}.decision", issues)
        _keys(decision_record, decision_allowed, f"{item_path}.decision", issues)
        if decision_record.get("review_id") != review_id:
            _issue(issues, "REVIEW_ID", f"{item_path}.decision.review_id", "decision must match request")
        _nonempty_string(decision_record.get("reviewer_ref"), f"{item_path}.decision.reviewer_ref", issues)
        _strings(decision_record.get("exact_input_refs"), f"{item_path}.decision.exact_input_refs", issues)
        exact_input_refs = decision_record.get("exact_input_refs")
        if isinstance(exact_input_refs, list):
            for ref in exact_input_refs:
                if ref not in known_refs:
                    _issue(issues, "UNKNOWN_REF", f"{item_path}.decision.exact_input_refs", "review input reference is unknown")
        if not isinstance(decision_record.get("independent"), bool) or not decision_record.get("independent"):
            _issue(issues, "REVIEW_INDEPENDENCE", f"{item_path}.decision.independent", "independent review is required")
        if decision_record.get("verdict") not in REVIEW_VERDICTS:
            _issue(issues, "REVIEW_STATE", f"{item_path}.decision.verdict", "unknown review verdict")
        for name in ("material_findings", "repair_obligation_ids", "residuals"):
            _strings(decision_record.get(name), f"{item_path}.decision.{name}", issues)
        _nonempty_string(decision_record.get("scope_ceiling"), f"{item_path}.decision.scope_ceiling", issues)
        repair_ids = decision_record.get("repair_obligation_ids")
        if isinstance(repair_ids, list):
            for repair_id in repair_ids:
                if repair_id not in obligation_ids:
                    _issue(issues, "UNKNOWN_REF", f"{item_path}.decision.repair_obligation_ids", "repair obligation is unknown")
        if decision_record.get("verdict") == "MATERIAL_REPAIR_REQUIRED" and not repair_ids and not decision_record.get("residuals"):
            _issue(issues, "REVIEW_REPAIR_ROUTE", f"{item_path}.decision", "material finding needs repair obligation or residual")
    return ids


def collect_case_errors(document: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(document, Mapping):
        return [ValidationIssue("TYPE", "$", "case document must be an object")]
    _check_json_values(document, "$", issues)
    _check_forbidden_keys(document, "$", issues)
    allowed_top = {"schema_version", "case"}
    _required(document, allowed_top, "$", issues)
    _keys(document, allowed_top, "$", issues)
    if document.get("schema_version") != SCHEMA_VERSION:
        _issue(issues, "SCHEMA_VERSION", "$.schema_version", "unexpected REOS schema version")
    case = _mapping(document.get("case"), "$.case", issues)
    if case is None:
        return issues
    case_allowed = {
        "case_id",
        "activation",
        "question_contract",
        "owner_boundary",
        "budget_contract",
        "stop_conditions",
        "case_state",
        "obligations",
        "artifact_refs",
        "evidence_requests",
        "claim_candidates",
        "reviews",
    }
    _required(case, case_allowed, "$.case", issues)
    _keys(case, case_allowed, "$.case", issues)
    _id(case.get("case_id"), "$.case.case_id", issues)
    _validate_activation(case.get("activation"), "$.case.activation", issues)
    _validate_question(case.get("question_contract"), "$.case.question_contract", issues)
    _nonempty_string(case.get("owner_boundary"), "$.case.owner_boundary", issues)
    if not isinstance(case.get("budget_contract"), Mapping):
        _issue(issues, "TYPE", "$.case.budget_contract", "budget contract must be an object")
    _strings(case.get("stop_conditions"), "$.case.stop_conditions", issues)
    case_state = case.get("case_state")
    if case_state == "SUCCESS":
        _issue(issues, "GENERIC_SUCCESS", "$.case.case_state", "generic SUCCESS is not a legal terminal state")
    conflicting_states = (OBLIGATION_STATES | EVIDENCE_STATES | REVIEW_VERDICTS) - {"OPEN", "ABSTAINED"}
    if case_state in conflicting_states:
        _issue(issues, "CONFLICTING_STATE_NAMESPACE", "$.case.case_state", "case state cannot use another object state namespace")
    if case_state not in CASE_STATES:
        _issue(issues, "CASE_STATE", "$.case.case_state", "unknown case state")
    question = case.get("question_contract") if isinstance(case.get("question_contract"), Mapping) else {}
    question_ref = question.get("preregistration_ref", "")
    obligations, obligation_ids = _validate_obligations(case.get("obligations"), question_ref, "$.case.obligations", issues)
    artifacts, artifact_ids = _validate_artifacts(case.get("artifact_refs"), "$.case.artifact_refs", issues)
    for index, obligation in enumerate(obligations):
        output_refs = obligation.get("output_artifact_refs")
        if isinstance(output_refs, list):
            for ref in output_refs:
                if ref not in artifact_ids:
                    _issue(issues, "UNKNOWN_REF", f"$.case.obligations[{index}].output_artifact_refs", "output artifact reference is unknown")
    for index, artifact in enumerate(artifacts):
        derivation_refs = artifact.get("derivation_refs")
        if isinstance(derivation_refs, list):
            for ref in derivation_refs:
                if ref not in artifact_ids:
                    _issue(issues, "UNKNOWN_REF", f"$.case.artifact_refs[{index}].derivation_refs", "derivation artifact reference is unknown")
    _validate_evidence(case.get("evidence_requests"), obligation_ids, artifact_ids, "$.case.evidence_requests", issues)
    claim_ids = _validate_claims(case.get("claim_candidates"), artifact_ids, "$.case.claim_candidates", issues)
    known_refs = {case.get("case_id"), *obligation_ids, *artifact_ids, *claim_ids}
    _validate_reviews(case.get("reviews"), obligation_ids, known_refs, "$.case.reviews", issues)
    return issues


def validate_case(document: Any) -> None:
    issues = collect_case_errors(document)
    if issues:
        raise ContractError(issues)


def validate_handoff(bundle: Any) -> None:
    issues: list[ValidationIssue] = []
    record = _mapping(bundle, "$", issues)
    if record is None:
        raise ContractError(issues)
    _check_forbidden_keys(record, "$", issues)
    allowed = {
        "bundle_id",
        "bundle_type",
        "receiving_authority",
        "object_refs",
        "allowed_claims",
        "noncanonical_status",
        "scope",
        "prohibited_inference",
        "residuals",
        "independent_review_required",
    }
    _required(record, allowed, "$", issues)
    _keys(record, allowed, "$", issues)
    _id(record.get("bundle_id"), "$.bundle_id", issues)
    for name in ("bundle_type", "receiving_authority", "noncanonical_status", "scope"):
        _nonempty_string(record.get(name), f"$.{name}", issues)
    if record.get("noncanonical_status") not in _HANDOFF_NONCANONICAL_STATUSES:
        _issue(issues, "HANDOFF_STATUS", "$.noncanonical_status", "handoff must remain a noncanonical research-stage status")
    for name in ("object_refs", "allowed_claims", "prohibited_inference", "residuals"):
        _strings(record.get(name), f"$.{name}", issues)
    if not record.get("prohibited_inference"):
        _issue(issues, "HANDOFF_PROHIBITED_INFERENCE", "$.prohibited_inference", "handoff must state forbidden inference")
    else:
        boundary_text = " ".join(record.get("prohibited_inference", [])).lower()
        missing_boundaries = [marker for marker in _HANDOFF_REQUIRED_BOUNDARIES if marker not in boundary_text]
        if missing_boundaries:
            _issue(issues, "HANDOFF_PROHIBITED_INFERENCE", "$.prohibited_inference", f"missing boundary markers: {missing_boundaries}")
    if not isinstance(record.get("independent_review_required"), bool):
        _issue(issues, "TYPE", "$.independent_review_required", "must be boolean")
    if issues:
        raise ContractError(issues)
