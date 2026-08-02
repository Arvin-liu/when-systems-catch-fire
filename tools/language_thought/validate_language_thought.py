#!/usr/bin/env python3
"""Validate the explicit contracts of the Language–Thought Logic Plane.

This gate validates declared frame annotations and their dispositions.  It does
not infer the meaning, naturalness or literary quality of arbitrary prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "language-thought"
MANIFEST_PATH = DATA / "manifest.json"
REQUIRED_DIMENSIONS = [f"d{index:02d}" for index in range(1, 13)]
REQUIRED_LAYERS = [f"L{index}" for index in range(7)]
REQUIRED_PROFILES = {
    "zh-hans-modern-written-r1": "FULL",
    "en-contemporary-written-r1": "FULL",
    "ja-modern-standard-pilot-r1": "BOUNDED_PRELIMINARY",
    "tr-modern-standard-pilot-r1": "BOUNDED_PRELIMINARY",
}
REQUIRED_PHENOMENA = {
    "agentive_accident",
    "aspect_endpoint",
    "topic_chain",
    "zero_anaphora",
    "explicit_implicit_connective",
    "evidential_source",
    "nominalization_event_realization",
    "lawful_long_sentence",
    "lawful_short_sentence",
    "purposeful_marked_syntax",
    "back_translation_framing",
    "cross_layer_l0_l6",
}
ALLOWED_STRENGTHS = {
    "grammatically_required",
    "strong_default",
    "productive_option",
    "marked_option",
    "context_dependent",
    "not_profiled",
}
PRODUCTION_DISPOSITIONS = {
    "preserved_with_explicit_change",
    "corrected",
    "retained_as_residue",
    "human_adjudicated_and_accepted",
}
FORBIDDEN_SILENT_DISPOSITIONS = {"silent", "ignored", "unresolved", "none"}
AUDIT_CLASSIFICATIONS = {
    "meaning_or_claim_changed",
    "agency_or_causality_changed",
    "uncertainty_changed",
    "discourse_logic_changed",
    "naturalness_or_style_only",
    "allowed_marked_syntax",
    "no_action",
}


@dataclass
class FixtureMetrics:
    true_positive: int = 0
    true_negative: int = 0
    false_positive: int = 0
    false_negative: int = 0
    unsupported: int = 0

    @property
    def precision(self) -> float | None:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else None

    @property
    def recall(self) -> float | None:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else None

    def as_dict(self) -> dict[str, int | float | None]:
        return {
            "true_positive": self.true_positive,
            "true_negative": self.true_negative,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "unsupported": self.unsupported,
            "precision": self.precision,
            "recall": self.recall,
        }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.relative_to(ROOT)}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.relative_to(ROOT)}:{line_number}: JSONL record must be an object")
        records.append(value)
    return records


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def required_string(record: dict[str, Any], key: str, prefix: str, errors: list[str]) -> None:
    require(isinstance(record.get(key), str) and bool(record[key].strip()), f"{prefix}: missing non-empty {key}", errors)


def validate_manifest(manifest: dict[str, Any], errors: list[str]) -> None:
    require(manifest.get("schema_version") == "1.0.0", "manifest: schema_version must be 1.0.0", errors)
    require(manifest.get("plane_id") == "language-thought-logic-plane", "manifest: wrong plane_id", errors)
    require(manifest.get("architecture_decision") == "ORTHOGONAL_PLANE_ACROSS_L0_L6_NOT_L7", "manifest: plane must be orthogonal across L0-L6, not L7", errors)
    require(manifest.get("cross_layer_coverage") == REQUIRED_LAYERS, "manifest: cross_layer_coverage must be exact ordered L0-L6", errors)
    require(manifest.get("required_dimensions") == REQUIRED_DIMENSIONS, "manifest: required_dimensions must be exact ordered d01-d12", errors)
    profiles = manifest.get("profiles")
    require(isinstance(profiles, list) and len(profiles) == 4, "manifest: exactly four pilot profiles are required", errors)
    if isinstance(profiles, list):
        ids = [entry.get("profile_id") for entry in profiles if isinstance(entry, dict)]
        require(set(ids) == set(REQUIRED_PROFILES), "manifest: required zh-Hans, en, ja and tr profiles missing or duplicated", errors)
    for key in ("dimension_registry", "evidence_registry", "transformation_registry", "fixture_registry", "audit_population", "audit_findings", "validator"):
        value = manifest.get(key)
        require(isinstance(value, str) and (ROOT / value).is_file(), f"manifest: {key} target is missing: {value}", errors)
    for path in manifest.get("schemas", []):
        require(isinstance(path, str) and (ROOT / path).is_file(), f"manifest: schema target is missing: {path}", errors)


def validate_evidence(records: list[dict[str, Any]], errors: list[str]) -> set[str]:
    ids: list[str] = []
    classes: set[str] = set()
    for index, record in enumerate(records, 1):
        prefix = f"evidence[{index}]"
        for key in ("evidence_id", "kind", "citation", "locator", "finding_class", "bounded_use", "limitations"):
            required_string(record, key, prefix, errors)
        require(record.get("consulted") is True, f"{prefix}: consulted must be true; search snippets are not evidence", errors)
        require(isinstance(record.get("supports_dimensions"), list) and bool(record["supports_dimensions"]), f"{prefix}: supports_dimensions required", errors)
        require(set(record.get("supports_dimensions", [])) <= set(REQUIRED_DIMENSIONS), f"{prefix}: unknown dimension", errors)
        ids.append(record.get("evidence_id", ""))
        classes.add(record.get("finding_class", ""))
    require(len(ids) == len(set(ids)), "evidence: duplicate evidence_id", errors)
    require(any("positive" in item for item in classes), "evidence: positive finding missing", errors)
    require(any("null" in item for item in classes), "evidence: null finding missing", errors)
    require(any("mixed" in item for item in classes), "evidence: mixed finding missing", errors)
    return set(ids)


def validate_dimensions(document: dict[str, Any], evidence_ids: set[str], errors: list[str]) -> set[str]:
    require(document.get("schema_version") == "1.0.0", "dimensions: wrong schema_version", errors)
    dimensions = document.get("dimensions")
    require(isinstance(dimensions, list) and len(dimensions) == 12, "dimensions: exactly twelve dimensions required", errors)
    ids: list[str] = []
    if not isinstance(dimensions, list):
        return set()
    for index, dimension in enumerate(dimensions, 1):
        prefix = f"dimension[{index}]"
        for key in ("dimension_id", "label_en", "label_zh", "definition", "evidence_status"):
            required_string(dimension, key, prefix, errors)
        for key, minimum in (("observable_transformations", 2), ("pointfire_risks", 1), ("authored_examples", 1), ("validation_fixture_ids", 1), ("counterexamples_and_variation", 2), ("evidence_ids", 1)):
            require(isinstance(dimension.get(key), list) and len(dimension[key]) >= minimum, f"{prefix}: {key} needs at least {minimum}", errors)
        require(set(dimension.get("evidence_ids", [])) <= evidence_ids, f"{prefix}: references unknown evidence", errors)
        ids.append(dimension.get("dimension_id", ""))
    require(ids == REQUIRED_DIMENSIONS, "dimensions: ids must be exact ordered d01-d12", errors)
    return set(ids)


def validate_profile(profile: dict[str, Any], dimension_ids: set[str], evidence_ids: set[str], errors: list[str]) -> None:
    prefix = f"profile[{profile.get('profile_id', '?')}]"
    for key in ("profile_id", "language_tag", "language_name", "bounded_scope", "coverage", "status", "nonessentialist_limit"):
        required_string(profile, key, prefix, errors)
    expected_coverage = REQUIRED_PROFILES.get(profile.get("profile_id"))
    require(expected_coverage is not None, f"{prefix}: unexpected profile", errors)
    require(profile.get("coverage") == expected_coverage, f"{prefix}: wrong coverage", errors)
    strata = profile.get("calibration_strata")
    require(isinstance(strata, dict), f"{prefix}: calibration_strata required", errors)
    if isinstance(strata, dict):
        for key in ("descriptive_grammar_typology", "ordinary_discourse", "literary_calibration"):
            require(isinstance(strata.get(key), list) and bool(strata[key]), f"{prefix}: calibration stratum {key} required", errors)
    items = profile.get("dimensions")
    require(isinstance(items, list) and len(items) == 12, f"{prefix}: exact twelve-dimensional coverage required", errors)
    if not isinstance(items, list):
        return
    ids: list[str] = []
    for item in items:
        item_prefix = f"{prefix}.{item.get('dimension_id', '?')}"
        ids.append(item.get("dimension_id", ""))
        require(item.get("obligation_strength") in ALLOWED_STRENGTHS, f"{item_prefix}: invalid obligation_strength", errors)
        for key in ("grammar_or_convention",):
            required_string(item, key, item_prefix, errors)
        for key in ("ordinary_realizations", "transformation_risks", "counterexamples_and_variation", "evidence_ids", "open_questions"):
            require(isinstance(item.get(key), list) and bool(item[key]), f"{item_prefix}: non-empty {key} required", errors)
        require(set(item.get("evidence_ids", [])) <= evidence_ids, f"{item_prefix}: unknown evidence id", errors)
    require(ids == REQUIRED_DIMENSIONS, f"{prefix}: dimensions must be exact ordered d01-d12", errors)
    require(set(ids) == dimension_ids, f"{prefix}: dimension basis mismatch", errors)
    if profile.get("coverage") == "FULL":
        require(not any(item.get("obligation_strength") == "not_profiled" for item in items), f"{prefix}: full profile cannot contain not_profiled", errors)
    if profile.get("coverage") == "BOUNDED_PRELIMINARY":
        require("PUBLICATION_REVIEW_REQUIRED" in profile.get("status", ""), f"{prefix}: preliminary profile must require language-specific publication review", errors)


def validate_transformation(record: dict[str, Any], production: bool) -> list[str]:
    errors: list[str] = []
    prefix = f"transformation[{record.get('record_id', '?')}]"
    for key in ("record_id", "record_kind", "version", "source_language_profile", "target_language_profile", "claim_ceiling"):
        required_string(record, key, prefix, errors)
    require(record.get("record_kind") in {"production", "fixture"}, f"{prefix}: invalid record_kind", errors)
    layers = record.get("layers")
    require(isinstance(layers, list) and bool(layers) and set(layers) <= set(REQUIRED_LAYERS), f"{prefix}: invalid layers", errors)
    for form_key in ("source_form", "target_form"):
        form = record.get(form_key)
        require(isinstance(form, dict), f"{prefix}: {form_key} must be object", errors)
        if isinstance(form, dict):
            for key in ("text", "language_tag", "form_status"):
                required_string(form, key, f"{prefix}.{form_key}", errors)
    candidate = record.get("normalized_meaning_candidate")
    require(isinstance(candidate, dict), f"{prefix}: normalized_meaning_candidate required", errors)
    if isinstance(candidate, dict):
        require(candidate.get("status") == "CANDIDATE_PROJECTION_NOT_NEUTRAL_MEANING", f"{prefix}: normalized meaning must declare candidate status", errors)
        required_string(candidate, "candidate_id", f"{prefix}.normalized_meaning_candidate", errors)
        required_string(candidate, "text", f"{prefix}.normalized_meaning_candidate", errors)
    source_frame = record.get("source_frame")
    target_frame = record.get("target_frame")
    require(isinstance(source_frame, dict) and bool(source_frame), f"{prefix}: source_frame required", errors)
    require(isinstance(target_frame, dict) and bool(target_frame), f"{prefix}: target_frame required", errors)
    if not isinstance(source_frame, dict) or not isinstance(target_frame, dict):
        return errors
    require(set(source_frame) <= set(REQUIRED_DIMENSIONS), f"{prefix}: source_frame has unknown dimensions", errors)
    require(set(target_frame) <= set(REQUIRED_DIMENSIONS), f"{prefix}: target_frame has unknown dimensions", errors)
    require(set(source_frame) == set(target_frame), f"{prefix}: source and target frames must annotate the same dimensions", errors)
    changed = {key for key in source_frame if source_frame[key] != target_frame[key]}
    deltas = record.get("framing_deltas")
    require(isinstance(deltas, list), f"{prefix}: framing_deltas must be list", errors)
    if not isinstance(deltas, list):
        return errors
    declared = [delta.get("dimension_id") for delta in deltas if isinstance(delta, dict)]
    require(len(declared) == len(set(declared)), f"{prefix}: duplicate framing delta dimension", errors)
    require(set(declared) == changed, f"{prefix}: silent or spurious frame changes observed={sorted(changed)} declared={sorted(set(declared))}", errors)
    residues = record.get("unmapped_residue")
    require(isinstance(residues, list), f"{prefix}: unmapped_residue must be list", errors)
    residue_dimensions = {item.get("dimension_id") for item in residues if isinstance(item, dict)} if isinstance(residues, list) else set()
    for delta in deltas:
        if not isinstance(delta, dict):
            errors.append(f"{prefix}: framing delta must be object")
            continue
        dimension_id = delta.get("dimension_id")
        delta_prefix = f"{prefix}.{dimension_id}"
        for key in ("delta_type", "source_value", "target_value", "disposition", "justification"):
            required_string(delta, key, delta_prefix, errors)
        require(isinstance(delta.get("epistemic_relevance"), bool), f"{delta_prefix}: epistemic_relevance must be boolean", errors)
        if dimension_id in source_frame:
            require(delta.get("source_value") == source_frame[dimension_id], f"{delta_prefix}: source_value does not match source_frame", errors)
            require(delta.get("target_value") == target_frame[dimension_id], f"{delta_prefix}: target_value does not match target_frame", errors)
        disposition = delta.get("disposition")
        require(disposition not in FORBIDDEN_SILENT_DISPOSITIONS, f"{delta_prefix}: forbidden silent/unresolved disposition", errors)
        if production and delta.get("epistemic_relevance") is True:
            require(disposition in PRODUCTION_DISPOSITIONS, f"{delta_prefix}: epistemically relevant production change lacks closed disposition", errors)
        if disposition == "retained_as_residue":
            require(dimension_id in residue_dimensions, f"{delta_prefix}: retained_as_residue lacks matching residue", errors)
    if isinstance(residues, list):
        for index, residue in enumerate(residues, 1):
            residue_prefix = f"{prefix}.residue[{index}]"
            require(isinstance(residue, dict), f"{residue_prefix}: must be object", errors)
            if not isinstance(residue, dict):
                continue
            for key in ("residue_id", "dimension_id", "text", "disposition"):
                required_string(residue, key, residue_prefix, errors)
            require(residue.get("dimension_id") in REQUIRED_DIMENSIONS, f"{residue_prefix}: unknown dimension", errors)
            require(isinstance(residue.get("affects_claim"), bool), f"{residue_prefix}: affects_claim must be boolean", errors)
            if production and residue.get("affects_claim") is True:
                require(residue.get("disposition") not in FORBIDDEN_SILENT_DISPOSITIONS, f"{residue_prefix}: claim-affecting residue unresolved", errors)
    provenance = record.get("provenance")
    require(isinstance(provenance, dict), f"{prefix}: provenance required", errors)
    if isinstance(provenance, dict):
        for key in ("created_by", "source_locator"):
            required_string(provenance, key, f"{prefix}.provenance", errors)
        require(isinstance(provenance.get("transformation_chain"), list) and bool(provenance["transformation_chain"]), f"{prefix}: transformation_chain required", errors)
    return errors


def evaluate_fixtures(fixtures: list[dict[str, Any]]) -> tuple[FixtureMetrics, list[str], set[str], set[str]]:
    metrics = FixtureMetrics()
    errors: list[str] = []
    phenomena: set[str] = set()
    layers: set[str] = set()
    ids: list[str] = []
    for fixture in fixtures:
        fixture_id = fixture.get("record_id", "?")
        ids.append(fixture_id)
        phenomena.update(fixture.get("phenomena", []))
        layers.update(fixture.get("layers", []))
        expected = fixture.get("expected_gate")
        if expected == "UNSUPPORTED":
            metrics.unsupported += 1
            require(isinstance(fixture.get("unsupported_reason"), str) and bool(fixture["unsupported_reason"].strip()), f"fixture[{fixture_id}]: unsupported_reason required", errors)
            continue
        actual_errors = validate_transformation(fixture, production=False)
        actual_fail = bool(actual_errors)
        if expected == "FAIL" and actual_fail:
            metrics.true_positive += 1
        elif expected == "PASS" and not actual_fail:
            metrics.true_negative += 1
        elif expected == "PASS" and actual_fail:
            metrics.false_positive += 1
            errors.append(f"fixture[{fixture_id}]: false positive: {'; '.join(actual_errors)}")
        elif expected == "FAIL" and not actual_fail:
            metrics.false_negative += 1
            errors.append(f"fixture[{fixture_id}]: false negative; invalid transformation was accepted")
        else:
            errors.append(f"fixture[{fixture_id}]: expected_gate must be PASS, FAIL or UNSUPPORTED")
    require(len(ids) == len(set(ids)), "fixtures: duplicate record_id", errors)
    require(REQUIRED_PHENOMENA <= phenomena, f"fixtures: missing phenomena {sorted(REQUIRED_PHENOMENA - phenomena)}", errors)
    require(set(REQUIRED_LAYERS) <= layers, f"fixtures: missing layer coverage {sorted(set(REQUIRED_LAYERS) - layers)}", errors)
    require(metrics.true_positive > 0 and metrics.true_negative > 0, "fixtures: both rejection and permission examples required", errors)
    return metrics, errors, phenomena, layers


def validate_audit(population: dict[str, Any], findings: list[dict[str, Any]], errors: list[str]) -> None:
    require(population.get("status") == "FROZEN_BOUNDED_POPULATION", "audit population: status must be FROZEN_BOUNDED_POPULATION", errors)
    items = population.get("items")
    require(isinstance(items, list) and bool(items), "audit population: items required", errors)
    population_ids = {item.get("population_item_id") for item in items if isinstance(item, dict)} if isinstance(items, list) else set()
    require(len(population_ids) == len(items or []), "audit population: duplicate or missing item id", errors)
    finding_ids: list[str] = []
    seen_population: set[str] = set()
    for index, finding in enumerate(findings, 1):
        prefix = f"audit[{index}]"
        for key in ("finding_id", "population_item_id", "path", "scope_locator", "classification", "finding", "action", "status", "historical_preservation"):
            required_string(finding, key, prefix, errors)
        require(finding.get("classification") in AUDIT_CLASSIFICATIONS, f"{prefix}: invalid classification", errors)
        require(finding.get("population_item_id") in population_ids, f"{prefix}: outside frozen population", errors)
        require(set(finding.get("dimensions", [])) <= set(REQUIRED_DIMENSIONS), f"{prefix}: unknown dimension", errors)
        finding_ids.append(finding.get("finding_id", ""))
        seen_population.add(finding.get("population_item_id", ""))
    require(len(finding_ids) == len(set(finding_ids)), "audit: duplicate finding_id", errors)
    require(population_ids <= seen_population, f"audit: population items without disposition {sorted(population_ids - seen_population)}", errors)
    require(set(AUDIT_CLASSIFICATIONS) <= {item.get("classification") for item in findings}, "audit: every required classification needs at least one finding", errors)


def validate_repository(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    manifest = load_json(root / "data/language-thought/manifest.json")
    validate_manifest(manifest, errors)
    evidence = load_jsonl(root / manifest["evidence_registry"])
    evidence_ids = validate_evidence(evidence, errors)
    dimensions_document = load_json(root / manifest["dimension_registry"])
    dimension_ids = validate_dimensions(dimensions_document, evidence_ids, errors)
    profiles: list[dict[str, Any]] = []
    profile_ids: set[str] = set()
    for entry in manifest["profiles"]:
        profile = load_json(root / entry["path"])
        profiles.append(profile)
        profile_ids.add(profile.get("profile_id", ""))
        validate_profile(profile, dimension_ids, evidence_ids, errors)
        require(profile.get("profile_id") == entry.get("profile_id"), f"manifest/profile identity mismatch at {entry.get('path')}", errors)
        require(profile.get("coverage") == entry.get("coverage"), f"manifest/profile coverage mismatch at {entry.get('path')}", errors)
    require(profile_ids == set(REQUIRED_PROFILES), "profiles: required set mismatch", errors)
    transformations = load_jsonl(root / manifest["transformation_registry"])
    production_ids: list[str] = []
    production_layers: set[str] = set()
    for record in transformations:
        production_ids.append(record.get("record_id", ""))
        production_layers.update(record.get("layers", []))
        require(record.get("record_kind") == "production", f"transformation[{record.get('record_id')}]: registry accepts production only", errors)
        require(record.get("source_language_profile") in profile_ids, f"transformation[{record.get('record_id')}]: unknown source profile", errors)
        require(record.get("target_language_profile") in profile_ids, f"transformation[{record.get('record_id')}]: unknown target profile", errors)
        errors.extend(validate_transformation(record, production=True))
    require(len(production_ids) == len(set(production_ids)), "transformations: duplicate record_id", errors)
    require(set(REQUIRED_LAYERS) <= production_layers, f"transformations: production ledger lacks layer coverage {sorted(set(REQUIRED_LAYERS)-production_layers)}", errors)
    fixtures = load_jsonl(root / manifest["fixture_registry"])
    metrics, fixture_errors, phenomena, fixture_layers = evaluate_fixtures(fixtures)
    errors.extend(fixture_errors)
    population = load_json(root / manifest["audit_population"])
    findings = load_jsonl(root / manifest["audit_findings"])
    validate_audit(population, findings, errors)
    required_human_docs = [
        "docs/architecture/language-thought-logic-plane.md",
        "docs/language-thought/README.md",
        "docs/language-thought/research-boundary.md",
        "docs/language-thought/dimensional-basis.md",
        "docs/language-thought/cross-layer-contract.md",
        "docs/language-thought/translation-and-residue.md",
        "docs/language-thought/validation-and-audit.md",
        "docs/language-thought/profiles/zh-hans.md",
        "docs/language-thought/profiles/en.md",
        "docs/language-thought/profiles/ja.md",
        "docs/language-thought/profiles/tr.md",
        "docs/language-thought/chinese-literary-calibration.md",
        "docs/language-thought/task-113-defect-before-after.md",
    ]
    for path in required_human_docs:
        require((root / path).is_file(), f"human documentation missing: {path}", errors)
    return {
        "status": "PASS" if not errors else "FAIL",
        "claim_ceiling": "declared-annotation contract validation only; no arbitrary-text understanding or literary-quality proof",
        "dimensions": len(dimension_ids),
        "profiles": len(profiles),
        "evidence_records": len(evidence),
        "production_transformations": len(transformations),
        "fixtures": len(fixtures),
        "fixture_metrics": metrics.as_dict(),
        "fixture_phenomena": sorted(phenomena),
        "fixture_layers": sorted(fixture_layers),
        "audit_population": len(population.get("items", [])),
        "audit_findings": len(findings),
        "errors": errors,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the full validation report as JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        report = validate_repository()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        report = {"status": "FAIL", "errors": [str(exc)]}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["status"] == "PASS":
        metrics = report["fixture_metrics"]
        print(
            "LANGUAGE_THOUGHT_PLANE_OK "
            f"dimensions={report['dimensions']} profiles={report['profiles']} "
            f"transformations={report['production_transformations']} fixtures={report['fixtures']} "
            f"tp={metrics['true_positive']} tn={metrics['true_negative']} "
            f"fp={metrics['false_positive']} fn={metrics['false_negative']} "
            f"unsupported={metrics['unsupported']} precision={metrics['precision']:.3f} recall={metrics['recall']:.3f}"
        )
    else:
        print("LANGUAGE_THOUGHT_PLANE_FAIL", file=sys.stderr)
        for error in report.get("errors", []):
            print(f"- {error}", file=sys.stderr)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
