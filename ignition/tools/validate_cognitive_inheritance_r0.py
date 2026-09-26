#!/usr/bin/env python3
"""Validate the repository-local Cognitive Inheritance Architecture R0.

The validator is intentionally mechanical.  It validates contracts and
provenance bindings, but it never emits an inheritance, capability or model
improvement verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


IGNITION_ROOT = Path(__file__).resolve().parents[1]
if str(IGNITION_ROOT) not in sys.path:
    sys.path.insert(0, str(IGNITION_ROOT))

from agent_runtime.cognitive_inheritance_r0.src.contracts import (  # noqa: E402
    canonical_json,
    keys_preserved,
    load_json,
    migrate_r0a_to_r0b,
    validate_no_forbidden_fields,
)


TASK_ID = "IGNITION-20260916-179"
BASELINE = "68565f2afb50989d2c2b0d346d774e3388702743"
FINAL_STATE = "READY_FOR_INDEPENDENT_EVALUATION"
R0_RELATIVE = Path("agent_runtime/cognitive_inheritance_r0")
TASK217_FREEZE_RELATIVE = Path(
    "ignition/reports/evaluations/ignition-217-method-dependency-benchmark-r0/freeze/FREEZE-MANIFEST.json"
)
TASK217_FREEZE_SIDECAR_RELATIVE = Path(
    "ignition/reports/evaluations/ignition-217-method-dependency-benchmark-r0/freeze/FREEZE-MANIFEST.sha256"
)
TASK220_FREEZE_RELATIVE = Path(
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/freeze/FREEZE-MANIFEST.json"
)
TASK220_FREEZE_SIDECAR_RELATIVE = Path(
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/freeze/FREEZE-MANIFEST.sha256"
)
ALLOWED_CHANGED_PREFIXES = (
    "ignition/agent_runtime/cognitive_inheritance_r0/",
    # Evaluation-plane work is a separate, non-canonical evidence surface.
    # Keep it eligible as auditable task output without admitting it to R0.
    "ignition/evaluation/",
    "ignition/reports/evaluations/",
)
ALLOWED_CHANGED_FILES = frozenset({
    "ignition/tools/validate_cognitive_inheritance_r0.py",
    "ignition/tests/test_cognitive_inheritance_r0.py",
    "ignition/tests/test_target_repository_preflight_r0_1.py",
    "ignition/tests/test_evaluation_plane_r0_1.py",
    "ignition/tests/test_knowledge_corpus_admission.py",
    "ignition/tools/foundation/validate_repository_path_classification.py",
    "ignition/tools/validate_knowledge_corpus_admission.py",
    "ignition/tools/governance/run_self_correction.py",
    "ignition/data/governance/self-correction/config.json",
    "ignition/data/foundation/schemas/repository-path-classification.schema.json",
    "ignition/data/foundation/knowledge-corpus-admission-policy.json",
    "ignition/data/foundation/repository-path-classification/classification-manifest.jsonl",
    "ignition/data/foundation/nonfunction-claims/closure-summary.json",
    "ignition/data/foundation/nonfunction-claims/discovery-coverage.json",
    "ignition/data/foundation/nonfunction-claims/source-discovery.jsonl",
    "ignition/docs/foundation/nonfunction-claim-adjudication-index.md",
    "ignition/data/architecture/current-facts.json",
    "ignition/data/governance/self-correction/claim-delta.jsonl",
    "ignition/data/governance/self-correction/impact-analysis.jsonl",
    "ignition/data/governance/self-correction/history.jsonl",
    "ignition/data/governance/self-correction/summary.json",
    "ignition/RESULTS/CLAIM-DELTA.md",
    "ignition/RESULTS/IMPACT-ANALYSIS.md",
    # These are deterministic, navigation-only products over reports; their
    # records retain the HUMAN_INDEX_ONLY disposition and do not change R0.
    "ignition/RESULTS/CHRONOLOGY.md",
    "ignition/data/governance/human-results/census.json",
    "ignition/data/governance/human-results/result-ledger.jsonl",
    # Task207-only human-results isolation config exception; do not widen config allowances.
    "ignition/data/governance/human-results/config.json",
    "ignition/data/governance/knowledge-experience/asset-cards.jsonl",
    # Task187 evaluation reports are explicitly excluded from Knowledge
    # Experience; allow the exact source policy and its generated coverage.
    "ignition/data/governance/knowledge-experience/config.json",
    "ignition/data/governance/knowledge-experience/coverage.json",
    # This provenance-only map still covers every human-results ledger source;
    # Task187 evaluation reports remain excluded from Knowledge Experience.
    "ignition/data/governance/knowledge-experience/source-first-seen.json",
    "ignition/data/governance/knowledge-experience/layered-reading.jsonl",
    "ignition/data/governance/knowledge-experience/manifest.json",
    "ignition/data/governance/knowledge-experience/search-index.jsonl",
    "ignition/data/governance/knowledge-experience/alias-index.jsonl",
    "ignition/data/governance/knowledge-experience/changes.jsonl",
    "ignition/data/governance/self-correction/audit-findings.jsonl",
    "ignition/RESULTS/SELF-CORRECTION-AUDIT.md",
    # Task190 generated Knowledge markdown remains navigation-only and is not canonical admission.
    "ignition/KNOWLEDGE/ASSET-CARDS.md",
    "ignition/KNOWLEDGE/COVERAGE.md",
    "ignition/KNOWLEDGE/MAP.md",
    "ignition/KNOWLEDGE/READING-LAYERS.md",
    "ignition/KNOWLEDGE/README.md",
    "ignition/KNOWLEDGE/SEARCH.md",
    "ignition/KNOWLEDGE/WHATS-NEW.md",
    # Task198 full-clone regeneration also refreshes these deterministic,
    # navigation-only Knowledge partitions; they do not admit claims to R0.
    "ignition/KNOWLEDGE/cards/part-002.md",
    "ignition/KNOWLEDGE/cards/part-003.md",
    "ignition/KNOWLEDGE/cards/part-004.md",
    "ignition/KNOWLEDGE/cards/part-005.md",
    "ignition/KNOWLEDGE/cards/part-006.md",
    "ignition/KNOWLEDGE/cards/part-007.md",
    "ignition/KNOWLEDGE/cards/part-008.md",
    "ignition/KNOWLEDGE/cards/part-009.md",
    "ignition/KNOWLEDGE/cards/part-010.md",
    "ignition/KNOWLEDGE/cards/part-011.md",
    "ignition/KNOWLEDGE/cards/part-012.md",
    "ignition/KNOWLEDGE/cards/part-013.md",
    "ignition/KNOWLEDGE/cards/part-014.md",
    "ignition/KNOWLEDGE/cards/part-015.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-003.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-004.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-005.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-006.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-007.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-008.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-009.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-010.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-011.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-012.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-013.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-014.md",
    "ignition/KNOWLEDGE/indexes/architecture_governance/part-015.md",
    "ignition/KNOWLEDGE/indexes/operations_evidence.md",
    "ignition/KNOWLEDGE/indexes/operations_evidence/part-003.md",
    "ignition/KNOWLEDGE/indexes/operations_evidence/part-004.md",
    "ignition/KNOWLEDGE/indexes/operations_evidence/part-005.md",
    "ignition/KNOWLEDGE/indexes/operations_evidence/part-006.md",
    "ignition/KNOWLEDGE/indexes/operations_evidence/part-007.md",
    "ignition/KNOWLEDGE/indexes/systems.md",
    "ignition/KNOWLEDGE/indexes/systems/part-003.md",
    "ignition/KNOWLEDGE/indexes/systems/part-004.md",
    "ignition/KNOWLEDGE/indexes/systems/part-005.md",
    "ignition/KNOWLEDGE/indexes/systems/part-006.md",
    "ignition/KNOWLEDGE/indexes/writing_publication.md",
    "ignition/KNOWLEDGE/indexes/writing_publication/part-001.md",
    "ignition/KNOWLEDGE/reading-layers/part-001.md",
    "ignition/KNOWLEDGE/reading-layers/part-002.md",
    "ignition/KNOWLEDGE/reading-layers/part-003.md",
    "ignition/KNOWLEDGE/reading-layers/part-004.md",
    "ignition/KNOWLEDGE/reading-layers/part-005.md",
    "ignition/KNOWLEDGE/reading-layers/part-006.md",
    "ignition/KNOWLEDGE/reading-layers/part-007.md",
    "ignition/KNOWLEDGE/reading-layers/part-008.md",
    "ignition/KNOWLEDGE/reading-layers/part-009.md",
    "ignition/KNOWLEDGE/reading-layers/part-010.md",
    "ignition/KNOWLEDGE/reading-layers/part-011.md",
    "ignition/KNOWLEDGE/reading-layers/part-012.md",
    "ignition/KNOWLEDGE/reading-layers/part-013.md",
    "ignition/data/publication/fire-seeds/seed-census.json",
    ".github/workflows/foundation-validation.yml",
    ".github/workflows/current-state-sync-validation.yml",
    ".github/workflows/iteration-lifecycle-validation.yml",
    ".github/workflows/iteration-planner-ci.yml",
    ".github/workflows/q33-governance-validation.yml",
    "ignition/data/agent-federation/build-vs-integrate-policy-r1.json",
    "ignition/tests/test_federation_ownership.py",
})


class ValidationFailure(Exception):
    """A concise mechanical validation failure."""


def read_json(path: Path) -> Any:
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"cannot read JSON {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationFailure(message)


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - CI installs foundation requirements
        raise ValidationFailure(f"jsonschema is required for {label}") from exc
    schema = read_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(
            f"{label} at {'.'.join(str(part) for part in error.path) or '$'}: {error.message}"
            for error in errors[:5]
        )
        raise ValidationFailure(details)


def validate_ref_integrity(ir_package: dict[str, Any], label: str) -> None:
    object_ids = {item["stable_id"] for item in ir_package["objects"]}
    relation_ids = {item["stable_id"] for item in ir_package["relations"]}
    for relation in ir_package["relations"]:
        for endpoint in (relation["from"], relation["to"]):
            if endpoint["ref_kind"] == "OBJECT":
                require(endpoint["stable_id"] in object_ids, f"{label}: missing object ref {endpoint['stable_id']}")
            elif endpoint["ref_kind"] == "RELATION":
                require(endpoint["stable_id"] in relation_ids, f"{label}: missing relation ref {endpoint['stable_id']}")
    for ref in ir_package["transition_refs"]:
        require(ref["ref_kind"] == "TRANSITION", f"{label}: transition ref kind is not TRANSITION")


def validate_transition(transition: dict[str, Any], ir_package: dict[str, Any], label: str) -> None:
    validate_ref_integrity(ir_package, label)
    object_ids = {item["stable_id"] for item in ir_package["objects"]}
    refs = [transition["previous_cognitive_model"]] + transition["observed_anomaly_or_failure"]
    refs += transition["new_representation"] + transition["new_method"]
    for ref in refs:
        if ref is not None and ref["ref_kind"] == "OBJECT":
            require(ref["stable_id"] in object_ids, f"{label}: transition ref is not in fixture: {ref['stable_id']}")
    require(transition["builder_verdict"] == "NOT_EVALUATED_BY_BUILDER", f"{label}: Builder verdict escaped ceiling")
    require(transition["final_state"] == FINAL_STATE, f"{label}: final state is not {FINAL_STATE}")


def validate_real_source_bindings(root: Path, content_fixture: dict[str, Any], engineering_fixture: dict[str, Any]) -> None:
    for fixture in (content_fixture, engineering_fixture):
        human_path = root.parent / fixture["human_readable_output"]
        require(human_path.is_file(), f"missing human-readable output: {human_path}")
        require(fixture["provenance_map"], f"missing provenance map: {fixture['fixture_id']}")
        require(fixture["open_obligations"], f"missing open obligations: {fixture['fixture_id']}")
    content_binding = content_fixture["real_source_binding"]
    require(content_binding["sha256"] == "6d92ac39669875a0d2a0c5aeb887df319a712d1886313c394da5f50daf4202d1", "content source hash drift")
    require(content_binding["body_republished"] is False, "content body was republished")
    baseline_audit = read_json(root / "data/operations/iterations/172/step00-baseline-audit.json")
    rest_input = next(item for item in baseline_audit["r1_input_provenance"]["inputs"] if item["input_id"] == "got-brain-03-rest")
    require(rest_input["sha256"] == content_binding["sha256"], "content source hash does not match baseline audit")
    require(rest_input["bytes"] == content_binding["bytes"], "content source byte count does not match baseline audit")
    replay = read_json(root / "data/operations/iterations/172/step11-ab-replay.json")
    case = next(item for item in replay["b_current_path"]["cases"] if item["case_id"] == "rest-evidence-boundary")
    observation = content_fixture["retrieval_observation"]
    for key in ("candidate_count", "selected_count", "valid_canonical_ids", "invalid_or_orphan_ids", "fallback", "exact_canonical_validation_rate", "unresolved_rate"):
        require(case[key] == observation[key], f"content replay field drift: {key}")
    require(observation["a_comparison_metrics"] == "NOT_MEASURED", "content fixture fabricated A metrics")
    require(observation["generalized_performance_claim"] is False, "content fixture widened performance claim")

    freeze = read_json(root / "data/operations/iterations/172/step13-final-freeze.json")
    binding = engineering_fixture["real_source_binding"]
    require(binding["baseline_exact_head"] == BASELINE, "engineering baseline exact head drift")
    require(freeze["freeze_status"] == "FINAL_SCAN_INPUT_FREEZE_RECORDED", "engineering freeze status drift")
    require(freeze["official_derivation_chain"]["second_run_no_diff"] is True, "engineering fixed-point evidence missing")
    require(freeze["next_generation_work_started"] is False, "engineering fixture widened generation scope")
    require(len(engineering_fixture["ci_evidence"]) == 7, "engineering fixture does not contain seven CI runs")
    require(all(item["conclusion"] == "success" for item in engineering_fixture["ci_evidence"]), "engineering fixture CI evidence is not all success")


def validate_changed_paths(root: Path) -> None:
    git_dir = root.parent / ".git"
    if not git_dir.exists() and not (root / ".git").exists():
        return
    result = subprocess.run(
        ["git", "diff", "--name-only", BASELINE, "HEAD"],
        cwd=root.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return
    changed = [line for line in result.stdout.splitlines() if line]
    # Later Task217 closure may add deterministic Knowledge Experience shards
    # and Fire Seeds machine projections outside this R0 task's original fixed
    # list. Admit only exact outputs whose hashes are recorded in Task217's
    # freeze and checksum sidecar.
    task217_projection_paths = (
        task217_generated_knowledge_paths(root.parent)
        | task217_generated_fire_seed_paths(root.parent)
    )
    unexpected = [
        path for path in changed
        if not is_allowed_changed_path(path, exact_extra_paths=task217_projection_paths)
    ]
    require(not unexpected, f"R0 changed protected or out-of-scope paths: {unexpected}")


def load_task217_freeze(repo_root: Path) -> dict[str, Any] | None:
    freeze_path = repo_root / TASK217_FREEZE_RELATIVE
    sidecar_path = repo_root / TASK217_FREEZE_SIDECAR_RELATIVE
    if not freeze_path.exists() and not sidecar_path.exists():
        return None
    require(freeze_path.is_file() and sidecar_path.is_file(), "Task217 projection freeze or sidecar is missing")
    freeze_bytes = freeze_path.read_bytes()
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    expected_sidecar = f"{freeze_sha}  {TASK217_FREEZE_RELATIVE.as_posix()}\n"
    require(sidecar_path.read_text(encoding="utf-8") == expected_sidecar, "Task217 projection freeze sidecar mismatch")
    try:
        return json.loads(freeze_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationFailure(f"Task217 projection freeze is invalid JSON: {exc}") from exc


def load_task220_freeze(repo_root: Path) -> dict[str, Any] | None:
    freeze_path = repo_root / TASK220_FREEZE_RELATIVE
    sidecar_path = repo_root / TASK220_FREEZE_SIDECAR_RELATIVE
    if not freeze_path.exists() and not sidecar_path.exists():
        return None
    require(freeze_path.is_file() and sidecar_path.is_file(), "Task220 projection freeze or sidecar is missing")
    freeze_bytes = freeze_path.read_bytes()
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    expected_sidecar = f"{freeze_sha}  {TASK220_FREEZE_RELATIVE.as_posix()}\n"
    require(sidecar_path.read_text(encoding="utf-8") == expected_sidecar, "Task220 projection freeze sidecar mismatch")
    try:
        freeze = json.loads(freeze_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationFailure(f"Task220 projection freeze is invalid JSON: {exc}") from exc
    require(freeze.get("task_id") == "IGNITION-20260926-220", "Task220 projection freeze task ID differs")
    return freeze


def task220_projection_hashes(repo_root: Path, section_name: str) -> dict[str, str]:
    freeze = load_task220_freeze(repo_root)
    if freeze is None:
        return {}
    section = freeze.get(section_name, {})
    entries = section.get("files", [])
    paths: dict[str, str] = {}
    for entry in entries:
        path = entry.get("path")
        expected_sha = entry.get("sha256")
        if section_name == "external_generated_knowledge_experience":
            require(
                isinstance(path, str)
                and (path.startswith("ignition/KNOWLEDGE/") or path.startswith("ignition/data/governance/knowledge-experience/")),
                "Task220 freeze contains a non-knowledge-experience projection path",
            )
        elif section_name == "external_generated_fire_seed_census":
            require(
                path in {
                    "ignition/data/publication/fire-seeds/seed-census.json",
                    "ignition/data/publication/fire-seeds/CHANGELOG.jsonl",
                },
                "Task220 freeze contains a non-Fire-Seeds projection path",
            )
        require(isinstance(expected_sha, str) and len(expected_sha) == 64, f"Task220 freeze has invalid SHA-256 for {path}")
        require(path not in paths, f"Task220 freeze duplicates projection path {path}")
        artifact = repo_root / path
        require(artifact.is_file(), f"Task220 frozen projection is missing: {path}")
        actual_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
        require(actual_sha == expected_sha, f"Task220 frozen projection hash mismatch: {path}")
        paths[path] = expected_sha
    if section_name == "external_generated_fire_seed_census" and entries:
        require(
            set(paths) == {
                "ignition/data/publication/fire-seeds/seed-census.json",
                "ignition/data/publication/fire-seeds/CHANGELOG.jsonl",
            },
            "Task220 Fire Seeds projection inventory differs",
        )
    return paths


def task217_generated_knowledge_paths(repo_root: Path) -> set[str]:
    freeze = load_task217_freeze(repo_root)
    if freeze is None:
        return set()
    task220_hashes = task220_projection_hashes(repo_root, "external_generated_knowledge_experience")
    knowledge = freeze.get("external_generated_knowledge_experience", {})
    entries = knowledge.get("files", [])
    paths: set[str] = set()
    for entry in entries:
        path = entry.get("path")
        expected_sha = entry.get("sha256")
        require(
            isinstance(path, str)
            and (path.startswith("ignition/KNOWLEDGE/") or path.startswith("ignition/data/governance/knowledge-experience/")),
            "Task217 freeze contains a non-knowledge-experience projection path",
        )
        require(path not in paths, f"Task217 freeze duplicates knowledge-experience path {path}")
        artifact = repo_root / path
        require(artifact.is_file(), f"Task217 frozen knowledge-experience projection is missing: {path}")
        actual_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
        require(
            actual_sha == expected_sha or task220_hashes.get(path) == actual_sha,
            f"Task217 frozen knowledge-experience projection hash mismatch without a Task220 frozen replacement: {path}",
        )
        paths.add(path)
    for path in task220_hashes:
        paths.add(path)
    return paths


def task217_generated_fire_seed_paths(repo_root: Path) -> set[str]:
    freeze = load_task217_freeze(repo_root)
    if freeze is None:
        return set()
    task220_hashes = task220_projection_hashes(repo_root, "external_generated_fire_seed_census")
    expected_paths = {
        "ignition/data/publication/fire-seeds/seed-census.json",
        "ignition/data/publication/fire-seeds/CHANGELOG.jsonl",
    }
    projection = freeze.get("external_generated_fire_seed_census", {})
    entries = projection.get("files", [])
    paths: set[str] = set()
    for entry in entries:
        path = entry.get("path")
        expected_sha = entry.get("sha256")
        require(path in expected_paths, "Task217 freeze contains a non-Fire-Seeds projection path")
        require(path not in paths, f"Task217 freeze duplicates Fire Seeds projection path {path}")
        artifact = repo_root / path
        require(artifact.is_file(), f"Task217 frozen Fire Seeds projection is missing: {path}")
        actual_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
        require(
            actual_sha == expected_sha or task220_hashes.get(path) == actual_sha,
            f"Task217 frozen Fire Seeds projection hash mismatch without a Task220 frozen replacement: {path}",
        )
        paths.add(path)
    require(paths == expected_paths, "Task217 Fire Seeds projection inventory differs")
    require(projection.get("scope") == "machine source census only; no human Fire Seeds entry changed", "Task217 Fire Seeds projection scope differs")
    paths.update(task220_hashes)
    return paths


def validate_foundation_discovery_boundary(root: Path, r0: Path) -> int:
    repo_root = root.parent
    expected_pathspecs = [
        r0.relative_to(repo_root).as_posix(),
        (root / "tests/test_cognitive_inheritance_r0.py").relative_to(repo_root).as_posix(),
        (root / "tools/validate_cognitive_inheritance_r0.py").relative_to(repo_root).as_posix(),
    ]
    tracked = subprocess.run(
        ["git", "ls-files", "--", *expected_pathspecs],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    require(tracked.returncode == 0, f"cannot enumerate tracked R0 paths: {tracked.stderr.strip()}")
    root_from_repo = Path(root.relative_to(repo_root).as_posix())
    expected = {Path(path).relative_to(root_from_repo).as_posix() for path in tracked.stdout.splitlines() if path}
    require(expected, "R0 tracked path inventory is empty")

    discovery_path = root / "data/foundation/nonfunction-claims/source-discovery.jsonl"
    actual: dict[str, dict[str, Any]] = {}
    try:
        lines = discovery_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValidationFailure(f"cannot read Foundation source discovery: {exc}") from exc
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationFailure(f"invalid Foundation source-discovery JSONL: {exc}") from exc
        path = record.get("path")
        if path in expected:
            require(path not in actual, f"Foundation source discovery duplicates {path}")
            actual[path] = record

    require(set(actual) == expected, f"Foundation source discovery does not cover exact R0 inventory: missing={sorted(expected - set(actual))}, extra={sorted(set(actual) - expected)}")
    for path, record in actual.items():
        require(record["coverage_status"] == "EXCLUDED_PLATFORM_CODE_EXCLUDED", f"R0 path entered Foundation claim discovery: {path}")
        require(record["candidate_fragments"] == 0, f"R0 path produced Foundation claim fragments: {path}")
        require(record["canonical_claim_ids"] == [], f"R0 path gained canonical claim IDs: {path}")
    return len(expected)


def is_allowed_changed_path(path: str, exact_extra_paths: set[str] | frozenset[str] = frozenset()) -> bool:
    """Keep R0 changes bounded while recognizing the typed evaluation surface."""
    return path in ALLOWED_CHANGED_FILES or path.startswith(ALLOWED_CHANGED_PREFIXES) or path in exact_extra_paths


def validate_migration(r0: Path, migration_record: dict[str, Any]) -> None:
    source = read_json(r0 / "fixtures/migration-r0a.json")
    expected = read_json(r0 / "fixtures/migration-r0b.expected.json")
    migrated = migrate_r0a_to_r0b(source)
    require(keys_preserved(source, migrated), "migration dropped a top-level source key")
    require(canonical_json(migrated) == canonical_json(expected), "migration output differs from expected fixture")
    require(any(item["relation_type"] == "UNKNOWN_RELATION" for item in migrated["relations"]), "migration dropped UNKNOWN_RELATION")
    require(migration_record["adapter"]["destructive_rewrite"] is False, "migration record permits destructive rewrite")


def validate_successor_package(package: dict[str, Any], label: str) -> None:
    require(package["task_id"] == TASK_ID, f"{label}: task id drift")
    require(package["status"] == FINAL_STATE, f"{label}: status drift")
    contract = package["reconstruction_contract"]
    require(contract["start_without_chat_history"] is True, f"{label}: chat history is an implicit input")
    require(package["handoff"]["builder_final_verdict"] == "NOT_EVALUATED_BY_BUILDER", f"{label}: Builder can self-evaluate")
    require(package["handoff"]["stop_condition"] == FINAL_STATE, f"{label}: stop state drift")


def validate_all(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    r0 = root / R0_RELATIVE
    schema = r0 / "schema"
    fixtures = r0 / "fixtures"
    packages = r0 / "packages"
    require(r0.is_dir(), f"missing R0 directory: {r0}")

    content_fixture = read_json(fixtures / "content-research-rest.json")
    engineering_fixture = read_json(fixtures / "engineering-baseline-freeze.json")
    content_ir = content_fixture["ir_package"]
    engineering_ir = engineering_fixture["ir_package"]
    validate_schema(content_ir, schema / "cognitive-ir-r0.schema.json", "content IR")
    validate_schema(engineering_ir, schema / "cognitive-ir-r0.schema.json", "engineering IR")
    validate_schema(read_json(fixtures / "content-research-transition.json"), schema / "cognitive-transition-r0.schema.json", "content transition")
    validate_schema(read_json(fixtures / "engineering-baseline-transition.json"), schema / "cognitive-transition-r0.schema.json", "engineering transition")
    evaluation = read_json(packages / "independent-evaluation-package.json")
    validate_schema(evaluation, schema / "independent-evaluation-package-r0.schema.json", "evaluation package")
    validate_schema(read_json(packages / "capability-interface-r0.json"), schema / "capability-interface-r0.schema.json", "capability interface")
    validate_schema(read_json(packages / "complexity-budget-r0.json"), schema / "complexity-budget-r0.schema.json", "complexity budget")
    migration_record = read_json(fixtures / "migration-record-r0.json")
    validate_schema(migration_record, schema / "migration-record-r0.schema.json", "migration record")

    validate_transition(read_json(fixtures / "content-research-transition.json"), content_ir, "content transition")
    validate_transition(read_json(fixtures / "engineering-baseline-transition.json"), engineering_ir, "engineering transition")
    validate_real_source_bindings(root, content_fixture, engineering_fixture)
    validate_migration(r0, migration_record)
    validate_successor_package(read_json(packages / "successor-content-rest.json"), "content successor")
    validate_successor_package(read_json(packages / "successor-engineering-baseline.json"), "engineering successor")

    self_model = read_json(packages / "current-self-model-r0.json")
    require(self_model["model_id"] == "CURRENT_SELF_MODEL_R0", "self-model id drift")
    require(self_model["status"] == FINAL_STATE, "self-model status drift")
    require(self_model["provisional"] is True, "self-model is no longer provisional")
    require(len(self_model["planes"]) == 7, "self-model plane count drift")
    require(self_model["cognitive_evolution"]["independent_evaluation_required"] is True, "self-model permits builder self-evaluation")
    require(evaluation["experiment_status"] == FINAL_STATE, "evaluation status drift")
    require(evaluation["final_verdict"]["cognitive_inheritance_verdict"] == "NOT_EVALUATED_BY_BUILDER", "evaluation package contains a Builder inheritance verdict")
    require(evaluation["final_verdict"]["owner_acceptance"] == "NOT_REQUESTED", "Owner acceptance was inferred")
    expected_metrics = {
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
    actual_metrics = {metric["metric_id"] for metric in evaluation["metrics"]}
    require(actual_metrics == expected_metrics, "R0 metric instrumentation set is incomplete or widened")

    all_json = list(r0.rglob("*.json"))
    for path in all_json:
        validate_no_forbidden_fields(read_json(path))
    foundation_discovery_paths = validate_foundation_discovery_boundary(root, r0)
    validate_changed_paths(root)

    return {
        "status": "PASS",
        "task_id": TASK_ID,
        "final_state": FINAL_STATE,
        "baseline_exact_head": BASELINE,
        "fixtures": [content_fixture["fixture_id"], engineering_fixture["fixture_id"]],
        "independent_evaluation": "NOT_RUN",
        "builder_verdict": "NOT_EVALUATED_BY_BUILDER",
        "foundation_canonical_mutation": "NONE",
        "foundation_nonfunction_discovery": {
            "tracked_paths": foundation_discovery_paths,
            "candidate_fragments": 0,
            "canonical_claim_ids": 0,
        },
        "model_rsi_or_weight_training": "NOT_PRESENT",
        "checked_json_files": len(all_json),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=IGNITION_ROOT, help="Formal repository ignition directory")
    args = parser.parse_args()
    try:
        result = validate_all(args.repo_root)
    except ValidationFailure as exc:
        print(json.dumps({"status": "FAIL", "task_id": TASK_ID, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
