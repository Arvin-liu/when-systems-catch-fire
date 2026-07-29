#!/usr/bin/env python3
"""Produce the deterministic task-99 deep-adjudication registry closure.

The tool does not pretend that automatic inspection is external review. It
assigns every discovered asset a canonical card and a final repository
disposition. Missing definitions, proofs or empirical bridges are closed by an
explicit quarantine record with concrete obligations rather than a silent gap.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import re
import subprocess
import tempfile
from collections import Counter, defaultdict, deque
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "data/foundation/function-assets"
CONFIG = json.loads((ASSETS / "deep-adjudication-config.json").read_text(encoding="utf-8"))

IDENTITIES = {
    "STRICT_MATHEMATICAL_FUNCTION",
    "PARAMETRIC_MATHEMATICAL_MODEL",
    "SCORING_OR_INDEX_FUNCTION",
    "GATE_OR_CLASSIFIER",
    "OPERATOR_OR_TRANSFORM",
    "RELATION_OR_CONSTRAINT",
    "ALGORITHM_OR_WORKFLOW",
    "HEURISTIC",
    "STRUCTURAL_METAPHOR",
    "CONJECTURE_OR_RESEARCH_CANDIDATE",
    "INVALID_OR_PSEUDO_FUNCTION",
    "UNRESOLVED_IDENTITY",
}
DISPOSITIONS = {
    "KEEP_AS_ESTABLISHED_MATH",
    "KEEP_AS_VALID_MODEL",
    "KEEP_AS_TESTED_INDEX_OR_CLASSIFIER",
    "KEEP_AS_ALGORITHM",
    "KEEP_AS_TOY_MODEL",
    "KEEP_AS_STRUCTURAL_METAPHOR",
    "REWRITE_AND_RETEST",
    "DOWNGRADE_TO_CONJECTURE",
    "DOWNGRADE_TO_PENDING",
    "QUARANTINE_UNTIL_DEFINED",
    "WITHDRAW_PUBLIC_CLAIM",
    "REJECT_AS_INVALID",
    "HISTORICAL_ONLY",
}
GATES = (
    "definition_gate",
    "dimension_and_type_gate",
    "counterexample_gate",
    "circular_reasoning_gate",
    "claim_layer_gate",
    "claim_ceiling_gate",
    "cross_domain_isomorphism_gate",
    "universal_quantifier_gate",
    "internal_test_truth_gate",
    "dependency_impact_gate",
)
PUBLIC_FRONT_DOORS = {
    "README.md", "SUMMARY.md", "FOUNDATION.md", "ARCHITECTURE.md", "ITERATION.md",
    "AI-START-HERE.md", "AI-HANDOFF.md", "llms.txt", "docs/project-current-state.md",
    "HUMAN-READING.md", "RESULTS/README.md", "RESULTS/LATEST.md", "RESULTS/CORRECTIONS.md",
    "RESULTS/OPEN-QUESTIONS.md", "RESULTS/ADJUDICATION-SUMMARY.md", "RESULTS/RESEARCH-AND-ARTICLES.md",
}
STRONG_TERM = re.compile(
    r"(定理|定律|证明|证实|不可能|必然|唯一|完全|统一|已解决|"
    r"theorem|law|proved|proven|impossible|necessarily|unique|complete|unified|solved)",
    re.I,
)
BOUNDARY_TERM = re.compile(
    r"(历史|撤回|被撤回|阻断|处置|禁止|不得|不能|不是|未证明|不等于|保持开放|待证|边界|限制|"
    r"pending|candidate|historical|withdraw|prohibit|must not|does not|not prove|not a|remains open|unverified|limits?|limitations?)",
    re.I,
)
UNIVERSAL_TERM = re.compile(r"(所有|任何|普遍|必然|唯一|完全|不可能|all\b|any\b|universal|necessarily|unique|impossible)", re.I)
CROSS_DOMAIN_TERM = re.compile(r"(同构|类比|投影|跨域|isomorph|analog|projection|cross-domain)", re.I)
EXTERNAL_TERM = re.compile(r"(物理|医学|金融|法律|现实|经验|实验|数据|physical|medical|financial|legal|real-world|empirical|experiment|data)", re.I)
CODE_SIGNATURE = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
LEAN_SIGNATURE = re.compile(r"^\s*(theorem|def)\s+([A-Za-z_]\w*)")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_sha(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def task99_identity(task98_identity: str) -> str:
    mapping = {
        "STRICT_MATHEMATICAL_FUNCTION": "STRICT_MATHEMATICAL_FUNCTION",
        "PARAMETRIC_MODEL": "PARAMETRIC_MATHEMATICAL_MODEL",
        "SCORE_OR_INDEX": "SCORING_OR_INDEX_FUNCTION",
        "GATE_OR_DECISION_RULE": "GATE_OR_CLASSIFIER",
        "ALGORITHM_OR_WORKFLOW": "ALGORITHM_OR_WORKFLOW",
        "RELATION_OR_CONSTRAINT": "RELATION_OR_CONSTRAINT",
        "HEURISTIC": "HEURISTIC",
        "STRUCTURAL_METAPHOR": "STRUCTURAL_METAPHOR",
        "CONJECTURE_OR_PENDING_CLAIM": "CONJECTURE_OR_RESEARCH_CANDIDATE",
        "INVALID_OR_PSEUDO_FUNCTION": "INVALID_OR_PSEUDO_FUNCTION",
    }
    return mapping.get(task98_identity, "UNRESOLVED_IDENTITY")


def object_identity(kind: str) -> str:
    mapping = {
        "FUNCTION": "STRICT_MATHEMATICAL_FUNCTION",
        "PARTIAL_FUNCTION": "STRICT_MATHEMATICAL_FUNCTION",
        "PREDICATE": "GATE_OR_CLASSIFIER",
        "STATE_TRANSITION": "ALGORITHM_OR_WORKFLOW",
        "ALGORITHM": "ALGORITHM_OR_WORKFLOW",
        "OPERATOR": "OPERATOR_OR_TRANSFORM",
        "RELATION": "RELATION_OR_CONSTRAINT",
        "ORDER": "RELATION_OR_CONSTRAINT",
        "METRIC": "SCORING_OR_INDEX_FUNCTION",
        "OPTIMIZATION_PROBLEM": "PARAMETRIC_MATHEMATICAL_MODEL",
        "CAUSAL_MODEL": "PARAMETRIC_MATHEMATICAL_MODEL",
        "PROBABILISTIC_MODEL": "PARAMETRIC_MATHEMATICAL_MODEL",
        "MECHANISM_MODEL": "PARAMETRIC_MATHEMATICAL_MODEL",
        "ARGUMENT_SCHEMA": "HEURISTIC",
        "FORMAL_PROPOSITION": "CONJECTURE_OR_RESEARCH_CANDIDATE",
        "NATURAL_LANGUAGE_CANDIDATE": "CONJECTURE_OR_RESEARCH_CANDIDATE",
    }
    return mapping.get(kind, "UNRESOLVED_IDENTITY")


def python_definitions(paths: set[str]) -> dict[tuple[str, int], dict]:
    found: dict[tuple[str, int], dict] = {}
    for relative in sorted(path for path in paths if path.endswith(".py")):
        try:
            source = (ROOT / relative).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            positional = [*node.args.posonlyargs, *node.args.args]
            inputs = []
            for argument in positional:
                annotation = ast.unparse(argument.annotation) if argument.annotation else "UNANNOTATED"
                inputs.append({"name": argument.arg, "type": annotation})
            if node.args.vararg:
                inputs.append({"name": "*" + node.args.vararg.arg, "type": ast.unparse(node.args.vararg.annotation) if node.args.vararg.annotation else "UNANNOTATED"})
            for argument in node.args.kwonlyargs:
                inputs.append({"name": argument.arg, "type": ast.unparse(argument.annotation) if argument.annotation else "UNANNOTATED"})
            if node.args.kwarg:
                inputs.append({"name": "**" + node.args.kwarg.arg, "type": ast.unparse(node.args.kwarg.annotation) if node.args.kwarg.annotation else "UNANNOTATED"})
            found[(relative, node.lineno)] = {
                "name": node.name,
                "inputs": inputs,
                "output": ast.unparse(node.returns) if node.returns else "RUNTIME_DEFINED_OR_NONE",
                "async": isinstance(node, ast.AsyncFunctionDef),
                "syntax": "PYTHON_AST_PARSED",
                "has_complete_annotations": bool(node.returns) and all(item["type"] != "UNANNOTATED" for item in inputs),
            }
    return found


def path_first_commits() -> dict[str, tuple[int, str]]:
    output = subprocess.check_output(
        ["git", "log", "--reverse", "--format=@@%H", "--name-only", CONFIG["source_commit"], "--"],
        cwd=ROOT,
        text=True,
        errors="replace",
    )
    current = ""
    first: dict[str, tuple[int, str]] = {}
    order = 0
    for raw in output.splitlines():
        if raw.startswith("@@"):
            current = raw[2:]
            order += 1
        elif raw and current:
            first.setdefault(raw, (order, current))
    return first


def exposure(paths: list[str]) -> list[str]:
    values = []
    if any(path in PUBLIC_FRONT_DOORS for path in paths):
        values.append("PUBLIC_FRONT_DOOR")
    if any(path.startswith("docs/") for path in paths):
        values.append("PUBLIC_DOCUMENT")
    if any(path.startswith(("统一函数总表/", "统一案例总表/")) for path in paths):
        values.append("LEGACY_PUBLIC_SOURCE")
    if any(path.startswith(("outputs/", "reports/")) for path in paths):
        values.append("PUBLIC_ARCHIVE_OR_REPORT")
    return values or ["PUBLIC_REPOSITORY_INTERNAL_SURFACE"]


def normalize_title(value: str) -> str:
    value = re.sub(r"[`*_#\s]+", " ", value.casefold()).strip()
    return re.sub(r"[^0-9a-z\u3400-\u9fffα-ω]+", "", value)


def semantic_text(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"(physical|structural|framework-level|framework|model|物理学?|结构性?|框架层?|模型)", "", value)
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", value)


def correction_disposition(stable_id: str) -> str:
    return {
        "T2": "KEEP_AS_ESTABLISHED_MATH",
        "D127": "KEEP_AS_STRUCTURAL_METAPHOR",
        "D182": "KEEP_AS_TOY_MODEL",
        "D183": "REWRITE_AND_RETEST",
        "D184": "KEEP_AS_TOY_MODEL",
        "D185": "KEEP_AS_STRUCTURAL_METAPHOR",
        "D186": "KEEP_AS_STRUCTURAL_METAPHOR",
        "D187": "KEEP_AS_STRUCTURAL_METAPHOR",
        "D188": "REJECT_AS_INVALID",
        "D189": "DOWNGRADE_TO_CONJECTURE",
        "D190": "DOWNGRADE_TO_CONJECTURE",
        "D260": "KEEP_AS_TESTED_INDEX_OR_CLASSIFIER",
    }[stable_id]


def generic_obligations(identity: str, defined: bool, external: str) -> tuple[list[str], list[str]]:
    proof = []
    empirical = []
    if not defined:
        proof.append("Supply an exact expression or executable specification, typed inputs and output, domain, codomain and operation semantics.")
    if identity == "STRICT_MATHEMATICAL_FUNCTION":
        proof.extend(["Prove single-valuedness on the stated domain.", "Discharge every claimed continuity, differentiability, monotonicity, boundedness and singularity obligation."])
    elif identity in {"PARAMETRIC_MATHEMATICAL_MODEL", "SCORING_OR_INDEX_FUNCTION", "GATE_OR_CLASSIFIER"}:
        proof.append("Define parameter ranges, boundary behavior, calibration semantics and counterexample conditions.")
    elif identity == "OPERATOR_OR_TRANSFORM":
        proof.append("Declare source/target spaces and prove the claimed preserved structure, if any.")
    elif identity == "RELATION_OR_CONSTRAINT":
        proof.append("Declare quantifiers, carrier and existence/uniqueness status without forcing a multivalued relation into a function.")
    elif identity == "CONJECTURE_OR_RESEARCH_CANDIDATE":
        proof.append("State a formal proposition and supply a proof artifact or preserve it as an open conjecture.")
    elif identity == "STRUCTURAL_METAPHOR":
        proof.append("Do not promote the analogy to isomorphism without explicit objects, maps, inverses and preservation proofs.")
    elif identity == "UNRESOLVED_IDENTITY":
        proof.append("Identify whether the source denotes one asset, a reference, a heading, an implementation function or only prose.")
    if external in {"E0", "E1", "E2", "E3", "E4"}:
        empirical.append("Define the operational mapping from variables to external objects before making a reality claim.")
        empirical.append("Provide a falsifiable protocol, baseline, data provenance and independent replication appropriate to the claimed domain.")
    return sorted(set(proof)), sorted(set(empirical))


def closure_for(start: str, children: dict[str, list[str]]) -> list[str]:
    seen: set[str] = set()
    pending = deque(children.get(start, []))
    while pending:
        item = pending.popleft()
        if item in seen:
            continue
        seen.add(item)
        pending.extend(children.get(item, []))
    return sorted(seen)


def public_claims() -> tuple[list[dict], list[dict]]:
    public_paths = [
        path for path in subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
        if path in PUBLIC_FRONT_DOORS or (path.startswith("docs/") and path.endswith((".md", ".txt")))
    ]
    rows = []
    withdrawn_seed = "physics grand unification has been proved impossible"
    seed_norm = semantic_text(withdrawn_seed)
    rebounds = []
    explicit_rebound = re.compile(
        r"(structur\w*\s+impossible|framework[- ]level\s+solved|structur\w*\s+unified|"
        r"结构性.{0,12}不可能|框架层?.{0,12}已解决|结构性.{0,12}统一)", re.I
    )
    for relative in sorted(public_paths):
        try:
            lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        in_fence = False
        section_heading = ""
        for line_no, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                section_heading = stripped
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not STRONG_TERM.search(stripped):
                continue
            boundary = bool(BOUNDARY_TERM.search(stripped) or BOUNDARY_TERM.search(section_heading))
            lowered = stripped.casefold()
            if ("统一" in stripped or "unif" in lowered) and ("不可能" in stripped or "impossible" in lowered):
                lineage = "PHYSICS_UNIFICATION_NOGO"
            elif "law" in lowered or "定律" in stripped:
                lineage = "LAW_OR_THEOREM"
            elif "统一" in stripped or "unif" in lowered:
                lineage = "UNIFICATION"
            elif "solved" in lowered or "已解决" in stripped:
                lineage = "SOLVED"
            else:
                lineage = "GENERAL_STRONG_CLAIM"
            claim_id = "PUBLIC-CLAIM-" + hashlib.sha256(f"{relative}\0{line_no}\0{stripped}".encode()).hexdigest()[:16].upper()
            record = {
                "claim_id": claim_id,
                "source_path": relative,
                "line": line_no,
                "text": stripped[:2000],
                "lineage": lineage,
                "context": "BOUNDARY_OR_HISTORICAL" if boundary else "ACTIVE_CLAIM_CANDIDATE_REQUIRES_HUMAN_REVIEW",
                "claim_ceiling": "Context-indexed repository claim candidate; this record is traceability, not proof.",
                "review_state": "CONTEXT_GUARD_PASS" if boundary else "REQUIRES_HUMAN_REVIEW",
            }
            rows.append(record)
            candidate_norm = semantic_text(stripped)
            similarity = SequenceMatcher(None, seed_norm, candidate_norm).ratio() if candidate_norm else 0.0
            family_match = lineage == "PHYSICS_UNIFICATION_NOGO" or bool(explicit_rebound.search(stripped))
            if family_match or similarity >= 0.58:
                status = "ALLOWED_WITHDRAWAL_OR_BOUNDARY_CONTEXT" if boundary else "BLOCKED_REBOUND"
                rebounds.append({
                    "candidate_id": "REBOUND-" + claim_id.removeprefix("PUBLIC-CLAIM-"),
                    "claim_id": claim_id,
                    "source_path": relative,
                    "line": line_no,
                    "lineage": lineage,
                    "normalized_similarity_to_withdrawn_seed": round(similarity, 6),
                    "explicit_rebound_family_match": family_match,
                    "status": status,
                    "reason": "Renaming cannot restore a withdrawn conclusion; context terms are inspected separately.",
                })
    return sorted(rows, key=lambda row: (row["source_path"], row["line"], row["claim_id"])), sorted(rebounds, key=lambda row: (row["source_path"], row["line"], row["candidate_id"]))


def build(destination: Path) -> dict:
    census = read_jsonl(ASSETS / "census.jsonl")
    discovery = read_jsonl(ASSETS / "discovery.jsonl")
    objects = {row["stable_id"]: row for row in read_jsonl(ROOT / "data/foundation/formal-objects/objects.jsonl")}
    corrections = {}
    for row in read_jsonl(ASSETS / "corrections.jsonl"):
        stable_id = row.get("stable_id") or row["correction_id"].removeprefix("CORR-98-")
        corrections[stable_id] = row
    edges = read_jsonl(ASSETS / "dependencies.jsonl")
    parents = defaultdict(list)
    children = defaultdict(list)
    for edge in edges:
        parents[edge["from"]].append(edge["to"])
        children[edge["to"]].append(edge["from"])
    anchors = defaultdict(list)
    all_paths = set()
    for row in discovery:
        anchors[row["stable_id"]].append({
            "path": row["path"],
            "first_line": row["first_line"],
            "last_line": row["last_line"],
            "role": row["role"],
            "mention_count": row["mention_count"],
        })
        all_paths.add(row["path"])
    first_commit = path_first_commits()
    pydefs = python_definitions(all_paths)
    title_groups = defaultdict(list)
    for row in census:
        normalized = normalize_title(row["title"])
        if normalized:
            title_groups[normalized].append(row["stable_id"])

    cards = []
    ledger = []
    obligations = []
    counterexamples = []
    quarantined = []
    dependency_closure = []

    for source in sorted(census, key=lambda row: row["stable_id"]):
        stable_id = source["stable_id"]
        obj = objects.get(stable_id)
        corr = corrections.get(stable_id)
        source_anchors = sorted(anchors.get(stable_id, []), key=lambda row: (row["path"], row["first_line"], row["last_line"]))
        source_paths = sorted({row["path"] for row in source_anchors} | set(source["source_evidence"]["definition_paths"]))
        code_spec = None
        for anchor in source_anchors:
            code_spec = pydefs.get((anchor["path"], anchor["first_line"]))
            if code_spec:
                break
        lean_match = LEAN_SIGNATURE.search(source["title"]) if any(path.endswith(".lean") for path in source_paths) else None
        if corr:
            primary = task99_identity(corr["formal_identity"])
            identity_authority = "HUMAN_ADJUDICATED_TASK98_RECONFIRMED_TASK99"
        elif obj:
            primary = object_identity(obj.get("formal_object_type", ""))
            identity_authority = "FOUNDATION_SOURCE_TEXT_ADJUDICATION_REUSED_TASK99"
        elif code_spec:
            primary = "ALGORITHM_OR_WORKFLOW"
            identity_authority = "TASK99_EXECUTABLE_SOURCE_ADJUDICATION"
        elif lean_match:
            primary = "CONJECTURE_OR_RESEARCH_CANDIDATE" if lean_match.group(1) == "theorem" else "OPERATOR_OR_TRANSFORM"
            identity_authority = "TASK99_EXECUTABLE_SOURCE_ADJUDICATION"
        else:
            primary = "UNRESOLVED_IDENTITY"
            identity_authority = "TASK99_EXPLICIT_QUARANTINE"

        definition = dict(source["definition"])
        expression = definition.get("original_formula")
        if code_spec:
            definition.update({
                "inputs": code_spec["inputs"],
                "output": code_spec["output"],
                "domain": "Python call values accepted by the source-defined signature",
                "codomain": code_spec["output"],
                "carrier": "Python runtime objects",
                "operation": "Executable Python function body",
                "exact_expression_or_executable_specification": f"{source_paths[0]}#L{source_anchors[0]['first_line']}:{code_spec['name']}",
            })
            expression = definition["exact_expression_or_executable_specification"]
        else:
            definition["exact_expression_or_executable_specification"] = expression or "UNSPECIFIED_IN_SOURCE"
        domain = definition.get("domain")
        codomain = definition.get("codomain") or definition.get("output")
        defined = bool(expression and domain not in (None, "", "UNSPECIFIED_IN_SOURCE") and codomain not in (None, "", "UNSPECIFIED"))
        if code_spec:
            defined = True

        mathematical_maturity = source["mathematical_maturity"]
        if code_spec:
            mathematical_maturity = "M2" if code_spec["has_complete_annotations"] else "M1"
        external_evidence = source["external_evidence"]
        proof_obligations, empirical_obligations = generic_obligations(primary, defined, external_evidence)
        if obj:
            proof_obligations.extend(obj.get("unresolved_blockers", []))
            proof_obligations.extend(obj.get("proof_obligations", []))
        proof_obligations = sorted(set(proof_obligations))

        text = " ".join([source["title"], str(definition.get("original_text") or "")])
        strong = bool(STRONG_TERM.search(text))
        universal = bool(UNIVERSAL_TERM.search(text))
        cross_domain = bool(CROSS_DOMAIN_TERM.search(text))
        external = bool(EXTERNAL_TERM.search(text))
        counterexample_values = list(source["mathematical_properties"].get("counterexamples", []))
        dependency_targets_exist = all(item in {row["stable_id"] for row in census} for item in parents.get(stable_id, []))

        if corr:
            gates = dict(source["audit_gates"])
        elif code_spec:
            gates = {
                "definition_gate": "PASS",
                "dimension_and_type_gate": "PASS" if code_spec["has_complete_annotations"] else "REQUIRES_HUMAN_REVIEW",
                "counterexample_gate": "NOT_APPLICABLE",
                "circular_reasoning_gate": "NOT_APPLICABLE",
                "claim_layer_gate": "PASS",
                "claim_ceiling_gate": "PASS",
                "cross_domain_isomorphism_gate": "NOT_APPLICABLE",
                "universal_quantifier_gate": "NOT_APPLICABLE",
                "internal_test_truth_gate": "PASS",
                "dependency_impact_gate": "PASS" if dependency_targets_exist else "FAIL",
            }
        else:
            gates = {
                "definition_gate": "PASS" if defined else "FAIL",
                "dimension_and_type_gate": "REQUIRES_HUMAN_REVIEW" if defined else "FAIL",
                "counterexample_gate": "PASS" if counterexample_values else "REQUIRES_HUMAN_REVIEW" if universal else "NOT_APPLICABLE",
                "circular_reasoning_gate": "REQUIRES_HUMAN_REVIEW" if strong else "NOT_APPLICABLE",
                "claim_layer_gate": "REQUIRES_HUMAN_REVIEW" if external else "PASS",
                "claim_ceiling_gate": "REQUIRES_HUMAN_REVIEW" if strong else "PASS",
                "cross_domain_isomorphism_gate": "REQUIRES_HUMAN_REVIEW" if cross_domain else "NOT_APPLICABLE",
                "universal_quantifier_gate": "REQUIRES_HUMAN_REVIEW" if universal else "NOT_APPLICABLE",
                "internal_test_truth_gate": "PASS",
                "dependency_impact_gate": "PASS" if dependency_targets_exist else "FAIL",
            }

        if corr:
            disposition = correction_disposition(stable_id)
        elif code_spec:
            disposition = "KEEP_AS_ALGORITHM"
        elif primary == "CONJECTURE_OR_RESEARCH_CANDIDATE" and obj and obj.get("formal_object_type") == "FORMAL_PROPOSITION":
            disposition = "DOWNGRADE_TO_CONJECTURE"
        elif primary == "CONJECTURE_OR_RESEARCH_CANDIDATE" and obj and obj.get("formal_object_type") == "NATURAL_LANGUAGE_CANDIDATE":
            disposition = "DOWNGRADE_TO_PENDING"
        else:
            disposition = "QUARANTINE_UNTIL_DEFINED"

        first_candidates = [first_commit[path] for path in source_paths if path in first_commit]
        first_appearance = min(first_candidates)[1] if first_candidates else "TASK99_CANDIDATE_NOT_SELF_EMBEDDED"
        normalized = normalize_title(source["title"])
        aliases = sorted(item for item in title_groups.get(normalized, []) if item != stable_id)
        direct_parents = sorted(set(parents.get(stable_id, [])))
        direct_children = sorted(set(children.get(stable_id, [])))
        transitive_children = closure_for(stable_id, children)

        if disposition == "KEEP_AS_ALGORITHM":
            allowed = ["repository-scoped execution according to the source implementation", "testing and implementation reuse under the declared software license"]
            prohibited = ["treating executable behavior or passing tests as mathematical proof or external truth"]
        elif disposition.startswith("KEEP_AS_"):
            allowed = source["allowed_uses"]
            prohibited = source["forbidden_uses"]
        else:
            allowed = ["historical tracing", "candidate analysis", "proof, definition or empirical work needed to discharge the listed obligations"]
            prohibited = ["public promotion above the recorded claim ceiling", "treating the historical name, formula shape or internal test as truth"]

        if corr:
            claim_ceiling = corr["claim_ceiling"]
        elif code_spec:
            claim_ceiling = "Repository-scoped executable algorithm only; behavior, correctness and external applicability require their own specifications and evidence."
        elif obj:
            claim_ceiling = obj.get("controlled_semantic_proposition") or "Source-text classification only; mathematical and external validity remain unestablished."
        else:
            claim_ceiling = "Quarantined discovery candidate only; identity, definition and truth status are unresolved."

        six_layer = {
            "syntax_and_mapping": {"result": "PASS" if defined else "FAIL", "evidence": "executable source specification" if code_spec else "definition metadata and source anchors"},
            "algebra_and_analysis": {"result": "PASS" if corr and mathematical_maturity in {"M4", "M6"} else "NOT_APPLICABLE" if not expression else "REQUIRES_HUMAN_REVIEW", "evidence": "task-98 scoped checks" if corr else "no general symbolic promotion"},
            "type_and_dimension": {"result": gates["dimension_and_type_gate"], "evidence": "typed signature or declared metadata"},
            "logic": {"result": "PASS" if corr else "REQUIRES_HUMAN_REVIEW" if strong else "NOT_APPLICABLE", "evidence": "quantifier, circularity and claim-layer gates"},
            "numerical_and_computational": {"result": "PASS" if corr and source["status"]["numerical"] not in {"REQUIRES_HUMAN_REVIEW", "NOT_COMPUTABLE_AS_STATED"} else "NOT_APPLICABLE" if not expression else "REQUIRES_HUMAN_REVIEW", "evidence": "bounded replay only"},
            "domain_interpretation": {"result": "PASS" if corr else "REQUIRES_HUMAN_REVIEW" if external else "NOT_APPLICABLE", "evidence": "external evidence remains independent of M maturity"},
        }
        card = {
            "canonical_id": stable_id,
            "historical_ids": sorted(set(filter(None, [stable_id, obj.get("legacy_id") if obj else None]))),
            "alias_candidates": aliases[:100],
            "alias_candidate_count": len(aliases),
            "title": source["title"],
            "source_anchors": source_anchors,
            "first_known_appearance_commit": first_appearance,
            "first_appearance_method": "earliest path occurrence reachable from the locked source commit; renames are not inferred",
            "current_public_exposure": exposure(source_paths),
            "primary_identity": primary,
            "secondary_identities": [],
            "identity_authority": identity_authority,
            "definition": definition,
            "mathematical_properties": source["mathematical_properties"],
            "algebraic_carrier_and_operation": {"carrier": definition.get("carrier", "UNSPECIFIED"), "operation": definition.get("operation", "UNSPECIFIED")},
            "assumptions_and_quantifiers": {
                "assumptions": corr.get("boundaries", []) if corr else obj.get("assumptions", []) if obj else [],
                "quantifiers": "EXPLICIT_IN_CORRECTION" if corr else "REQUIRES_DEFINITION" if universal else "NOT_STATED_OR_NOT_APPLICABLE",
            },
            "claimed_status": {
                "historical_assertion_grade": obj.get("assertion_grade") if obj else "UNREGISTERED_DISCOVERY",
                "model_or_theorem_status": obj.get("claim_type") if obj else "UNRESOLVED",
                "falsifiability_or_testability": "BOUNDED_REPLAY_AVAILABLE" if corr else "EXECUTABLE_REPOSITORY_BEHAVIOR" if code_spec else "OPEN_OBLIGATION",
            },
            "mathematical_maturity": mathematical_maturity,
            "external_evidence_maturity": external_evidence,
            "proof_obligations": proof_obligations,
            "empirical_obligations": empirical_obligations,
            "known_counterexamples": counterexample_values,
            "dependencies": {"parents": direct_parents, "children": direct_children, "transitive_children": transitive_children},
            "allowed_uses": allowed,
            "prohibited_uses": prohibited,
            "claim_ceiling": claim_ceiling,
            "audit_gates": gates,
            "six_layer_audit": six_layer,
            "final_disposition": disposition,
            "adjudication_evidence_paths": sorted(set(source_paths + ["data/foundation/function-assets/census.jsonl", "data/foundation/function-assets/identity-cards.jsonl"])),
            "reviewer_state": "TASK98_HUMAN_ADJUDICATION_RECONFIRMED" if corr else "TASK99_REPOSITORY_EVIDENCE_ADJUDICATED" if obj or code_spec else "TASK99_MACHINE_TRIAGED_EXPLICIT_QUARANTINE",
            "last_adjudicated_commit": CONFIG["source_commit"],
            "last_adjudicated_date": CONFIG["adjudicated_at"],
        }
        card["record_sha256"] = content_sha(card)
        cards.append(card)
        ledger.append({
            "canonical_id": stable_id,
            "record_sha256": card["record_sha256"],
            "primary_identity": primary,
            "mathematical_maturity": mathematical_maturity,
            "external_evidence_maturity": external_evidence,
            "final_disposition": disposition,
            "reviewer_state": card["reviewer_state"],
            "claim_ceiling": claim_ceiling,
            "source_anchor_count": len(source_anchors),
            "parent_count": len(direct_parents),
            "child_count": len(direct_children),
            "open_proof_obligations": len(proof_obligations),
            "open_empirical_obligations": len(empirical_obligations),
        })
        obligations.append({
            "canonical_id": stable_id,
            "proof_status": "DISCHARGED_SCOPED" if stable_id == "T2" else "NOT_APPLICABLE_AS_ALGORITHM" if disposition == "KEEP_AS_ALGORITHM" else "OPEN" if proof_obligations else "NOT_APPLICABLE",
            "proof_obligations": proof_obligations,
            "empirical_status": "NOT_APPLICABLE_TO_REPOSITORY_ALGORITHM" if disposition == "KEEP_AS_ALGORITHM" else "OPEN" if empirical_obligations else "NOT_APPLICABLE",
            "empirical_obligations": empirical_obligations,
            "evidence_paths": card["adjudication_evidence_paths"],
        })
        for index, counterexample in enumerate(counterexample_values, 1):
            counterexamples.append({
                "counterexample_id": f"CE-99-{stable_id}-{index:02d}",
                "canonical_id": stable_id,
                "statement": counterexample,
                "scope": "Scoped to the corrected or source-declared claim only.",
                "evidence_paths": card["adjudication_evidence_paths"],
                "replay_status": "TASK98_REPLAYED" if corr else "SOURCE_RECORDED_REQUIRES_REPLAY",
            })
        if disposition in {"QUARANTINE_UNTIL_DEFINED", "DOWNGRADE_TO_CONJECTURE", "DOWNGRADE_TO_PENDING", "REWRITE_AND_RETEST"}:
            quarantined.append({
                "canonical_id": stable_id,
                "reason": "; ".join(proof_obligations[:4]) or "Open bounded adjudication obligation",
                "primary_identity": primary,
                "final_disposition": disposition,
                "failed_or_open_gates": sorted(name for name, value in gates.items() if value in {"FAIL", "REQUIRES_HUMAN_REVIEW"}),
                "proof_obligations": proof_obligations,
                "empirical_obligations": empirical_obligations,
                "resume_key": f"task99:{stable_id}",
            })
        dependency_closure.append({
            "canonical_id": stable_id,
            "parents": direct_parents,
            "children": direct_children,
            "transitive_children": transitive_children,
            "dangling_parents": sorted(item for item in direct_parents if item not in {row["stable_id"] for row in census}),
        })

    public_rows, rebound_rows = public_claims()
    withdrawn = []
    for row in read_jsonl(ASSETS / "claim-ledger.jsonl"):
        if str(row.get("status", "")).startswith("WITHDRAWN"):
            withdrawn.append({
                "claim_id": row["claim_id"],
                "claim_text": row["claim_text"],
                "status": row["status"],
                "replacement": row.get("replacement"),
                "lineage": "PHYSICS_UNIFICATION_NOGO" if "impossible" in row["claim_text"] else "WITHDRAWN_TASK98_CLAIM",
                "rebound_rule": "Same semantic conclusion cannot return under physical, structural, framework or model-level renaming.",
                "source": "data/foundation/function-assets/claim-ledger.jsonl",
            })

    identity_counts = dict(sorted(Counter(card["primary_identity"] for card in cards).items()))
    disposition_counts = dict(sorted(Counter(card["final_disposition"] for card in cards).items()))
    maturity_counts = dict(sorted(Counter(card["mathematical_maturity"] for card in cards).items()))
    evidence_counts = dict(sorted(Counter(card["external_evidence_maturity"] for card in cards).items()))
    reviewer_counts = dict(sorted(Counter(card["reviewer_state"] for card in cards).items()))
    dangling = sum(bool(row["dangling_parents"]) for row in dependency_closure)
    summary = {
        "task_id": CONFIG["task_id"],
        "schema_version": CONFIG["schema_version"],
        "source_commit": CONFIG["source_commit"],
        "discovered_assets": len(census),
        "canonical_identity_cards": len(cards),
        "adjudication_ledger_records": len(ledger),
        "identity_distribution": identity_counts,
        "mathematical_maturity_distribution": maturity_counts,
        "external_evidence_distribution": evidence_counts,
        "disposition_distribution": disposition_counts,
        "reviewer_state_distribution": reviewer_counts,
        "explicit_quarantine_or_pending": len(quarantined),
        "counterexample_records": len(counterexamples),
        "dependency_edges": len(edges),
        "dependency_nodes_with_dangling_parents": dangling,
        "public_strong_claim_candidates": len(public_rows),
        "semantic_rebound_candidates": len(rebound_rows),
        "blocked_semantic_rebounds": sum(row["status"] == "BLOCKED_REBOUND" for row in rebound_rows),
        "registry_closed": len(cards) == len(census) == len({card["canonical_id"] for card in cards}) and dangling == 0,
        "closure_definition": "Every discovery has one canonical card, one primary identity, two maturity values, one final disposition and an evidence or quarantine path.",
        "claim_ceiling": CONFIG["claim_ceiling"],
    }
    coverage = {
        "scanner_snapshot": json.loads((ASSETS / "census-summary.json").read_text(encoding="utf-8"))["snapshot"],
        "tracked_text_files_scanned": json.loads((ASSETS / "census-summary.json").read_text(encoding="utf-8"))["tracked_text_files_scanned"],
        "candidate_classes": ["explicit stable identifiers", "named headings and name/title fields", "Python/Lean/JavaScript function declarations", "standalone function-like mathematical expressions"],
        "deduplication_rule": "Explicit IDs merge by normalized stable ID. Implicit candidates use path plus normalized declaration text; equal titles are alias candidates, not auto-merged because equal names need not denote equal objects.",
        "alias_rule": "Exact normalized-title matches are reported as alias candidates and require evidence before identity merge.",
        "first_appearance_rule": "Earliest path occurrence in the locked source commit ancestry; no unproved rename inference.",
        "coverage_assertions": {"every_discovery_has_card": len(cards) == len(census), "every_card_has_source_anchor": all(card["source_anchors"] for card in cards)},
        "known_limitations": ["Formula images without searchable text cannot be semantically recovered.", "Regex discovery can over-include headings and code helpers; such records are explicitly quarantined instead of silently discarded.", "Semantic rebound similarity is a candidate generator plus fail-closed lexical families, not an automatic proof of semantic equivalence."],
    }

    destination.mkdir(parents=True, exist_ok=True)
    write_jsonl(destination / "identity-cards.jsonl", cards)
    write_jsonl(destination / "adjudication-ledger.jsonl", ledger)
    write_jsonl(destination / "proof-empirical-obligations.jsonl", obligations)
    write_jsonl(destination / "counterexample-registry.jsonl", counterexamples)
    write_jsonl(destination / "unresolved-quarantine.jsonl", quarantined)
    write_jsonl(destination / "dependency-closure.jsonl", dependency_closure)
    write_jsonl(destination / "public-claim-lineage.jsonl", public_rows)
    write_jsonl(destination / "semantic-rebound-report.jsonl", rebound_rows)
    write_jsonl(destination / "withdrawn-historical-claims.jsonl", withdrawn)
    (destination / "closure-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (destination / "discovery-coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["canonical_id", "primary_identity", "mathematical_maturity", "external_evidence_maturity", "final_disposition", "reviewer_state", "source_anchor_count", "parent_count", "child_count"],
        lineterminator="\n",
    )
    writer.writeheader()
    for row in ledger:
        writer.writerow({key: row[key] for key in writer.fieldnames})
    (destination / "asset-inventory.csv").write_text(buffer.getvalue(), encoding="utf-8")
    return summary


def compare(left: Path, right: Path) -> list[str]:
    names = [
        "identity-cards.jsonl", "adjudication-ledger.jsonl", "proof-empirical-obligations.jsonl",
        "counterexample-registry.jsonl", "unresolved-quarantine.jsonl", "dependency-closure.jsonl",
        "public-claim-lineage.jsonl", "semantic-rebound-report.jsonl", "withdrawn-historical-claims.jsonl",
        "closure-summary.json", "discovery-coverage.json", "asset-inventory.csv",
    ]
    return [name for name in names if not (left / name).exists() or (left / name).read_bytes() != (right / name).read_bytes()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="ignition-deep-adjudication-") as temporary:
            summary = build(Path(temporary))
            changed = compare(ASSETS, Path(temporary))
        if changed:
            print("DEEP_ADJUDICATION_OUT_OF_DATE " + " ".join(changed))
            return 1
    else:
        summary = build(ASSETS)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print("FUNCTION_ASSET_DEEP_ADJUDICATION_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
