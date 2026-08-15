#!/usr/bin/env python3
"""Build the task-100 corpus-wide non-function claim registry.

The builder is deliberately conservative.  It discovers claim-like source
fragments reproducibly, maps exact duplicates to one stable ID, inherits the
task-98/99 function-asset authority when an identifier resolves there, and
quarantines missing proof/evidence instead of manufacturing it.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
# See the corresponding boundary in the function census: production fixtures
# can make the application directory itself the temporary Git root.
GIT_ROOT = ROOT if (ROOT / ".git").exists() else REPO_ROOT
OUT = ROOT / "data/foundation/nonfunction-claims"
INDEX = ROOT / "docs/foundation/nonfunction-claim-adjudication-index.md"

PUBLIC_SURFACES = {
    ".github/README.md", ".github/CONTRIBUTING.md", "FOUNDATION.md", "ITERATION.md", "SUMMARY.md",
    "AI-START-HERE.md", "AI-HANDOFF.md", "AGENTS.md", "llms.txt",
    "HUMAN-READING.md", "docs/project-current-state.md", "docs/foundation/README.md",
    "RESULTS/README.md", "RESULTS/LATEST.md", "RESULTS/CORRECTIONS.md",
    "RESULTS/OPEN-QUESTIONS.md", "RESULTS/ADJUDICATION-SUMMARY.md",
    "RESULTS/RESEARCH-AND-ARTICLES.md",
}
TEXT_SUFFIXES = {".md", ".txt", ".rst", ".json", ".jsonl", ".csv", ".yml", ".yaml", ".toml", ".py", ".sage", ".lean", ".js", ".jsx", ".ts", ".tsx", ".sh", ".html"}
SELF_EXCLUDES = {
    ".github/README.md",
    ".github/CONTRIBUTING.md",
    "tools/generate_overall_architecture.py",
    "tools/governance/build_claim_browsers.py",
    "tools/publication/validate_fire_seeds.py",
    "tools/publication/build_fire_seed_census.py",
    "tests/test_overall_architecture.py",
    "tests/test_fire_seeds.py",
    "data/architecture/overall-architecture.json",
    "data/foundation/project-state.json",
    "data/foundation/registry-manifest.json",
    "data/foundation/migration-summary.json",
    "docs/foundation/nonfunction-claim-adjudication-index.md",
    "reports/foundation-architecture/100-nonfunction-claim-evidence-lineage-closure.md",
    "schemas/foundation/nonfunction-claim.schema.json",
    "data/foundation/schemas/nonfunction-claim.schema.json",
    "RESULTS/CHRONOLOGY.md",
    "RESULTS/CLAIM-DELTA.md",
    "RESULTS/IMPACT-ANALYSIS.md",
    "RESULTS/EVIDENCE-LINEAGE.md",
    "RESULTS/SELF-CORRECTION-AUDIT.md",
    # Task 102 (knowledge-experience clone-independence) generation tooling: these are
    # code, not knowledge-content claim sources; exclude so discovery stays accountable
    # without spawning claims from docstrings/comments.
    "tools/governance/gen_source_first_seen.py",
    "tools/governance/check_knowledge_experience_determinism.py",
    # Task 108 (two-phase iteration terminalization, R1 20260801) lifecycle subsystem:
    # these are propagation tooling/schema/tests/docs/reports scoped to iteration
    # lifecycle accounting only. They are NOT authoritative claim sources; exclude so
    # discovery/governance stay accountable without fabricating claims from their text.
    "data/operations/derived-lifecycle-view.json",
    "data/operations/lifecycle-events.jsonl",
    "data/operations/propagation/108-impact/system-map-nonimpact-proof.json",
    "docs/operations/lifecycle-readme.md",
    "reports/operations/lifecycle-audit-108.md",
    "schemas/operations/lifecycle-event.schema.json",
    "tests/test_lifecycle_events.py",
    "tests/test_terminalization_allowlist.py",
    "tools/propagation/derived_lifecycle_view.py",
    "tools/propagation/lifecycle_events.py",
    "tools/propagation/tag_validator.py",
    "tools/propagation/terminalization_allowlist.py",
    "tools/propagation/terminalization_generator.py",
    # Task 108 CI workflow: new in this PR; tooling/spec, not an authoritative
    # claim source. Excluded so discovery stays accountable without spawning
    # claims from workflow YAML. (Pre-existing scanned files such as the
    # foundation generators or current_truth_projection.py remain scanned; their
    # edits regenerate deterministic foundation outputs per the task-107 pattern.)
    ".github/workflows/iteration-lifecycle-validation.yml",
}
MACHINE_EXCLUDE_PREFIXES = (
    "data/foundation/nonfunction-claims/",
    "data/foundation/function-assets/",
    # The manifest is a path-accounting projection, not an authoritative claim
    # source.  Keep it accounted for by its own validator without allowing its
    # serialized paths and categories to create registry claims.
    "data/foundation/repository-path-classification/",
    "data/governance/",
    # Generated root-layout inventories are structural projections, not
    # authoritative natural-language claim sources.
    "data/operations/root-normalization/",
    "KNOWLEDGE/",
    "docs/human/",
    "data/publication/fire-seeds/",
)
# Task 107 (R1 20260731) generator-input boundary: these prefixes are governed
# records, narrative/reference surfaces, benchmark candidate data/code or analysis
# output. They are NOT authoritative claim sources and must never be scanned for
# claim-like fragments (anti-backflow, contract §3.1/§3.2). They remain accounted
# for in source-discovery.jsonl (listed with an EXCLUDED status + reason) so the
# every-repository-path-accounted gate stays closed without fabricating claims.
NON_AUTHORITATIVE_PREFIXES = (
    "docs/editorial/",
    "function-os-candidate/",
    "analysis/",
    "data/operations/",
    "data/publication/fire-seeds/",
    # Published prose is an output/reference surface.  It must remain
    # auditable without feeding its own claims back into the Foundation
    # discovery registry.
    "PUBLICATIONS/",
)
EXPLICIT_IMPORTS = {
    "data/foundation/claims/claims.jsonl",
}

SIGNALS = re.compile(
    r"(?:theorem|lemma|axiom|law|principle|proof|proved|verified|validated|solved|"
    r"impossible|necessary|sufficient|universal|inevitable|always|never|caus(?:e|al)|"
    r"mechanism|isomorph|homomorph|correspond|projection|analogy|predict|forecast|"
    r"empirical|evidence|experiment|dataset|literature|ontology|metaphys|conscious|"
    r"physics|society|social|life|intelligen|truth|fact|unif(?:y|ication)|"
    r"定理|引理|公理|规律|法则|原理|证明|证实|验证|已解决|解决了|不可能|必然|必要|充分|"
    r"普遍|万能|永远|从不|因果|导致|决定|机制|同构|同态|对应|投影|类比|预测|预言|"
    r"实证|证据|实验|数据|文献|本体|形而上|意识|物理|社会|生命|智能|真理|事实|大一统|统一)",
    re.IGNORECASE,
)
STRONG = re.compile(
    r"(?:proved|proof|verified|validated|solved|impossible|necessary|sufficient|"
    r"universal|inevitable|always|never|isomorph|causal|theorem|law|"
    r"证明|证实|验证|已解决|不可能|必然|必要|充分|普遍|万能|永远|同构|因果|定理|规律)",
    re.IGNORECASE,
)
CAVEAT = re.compile(
    r"(?:\bnot\b|\bno\b|unless|does not|never|only|historical|withdrawn|withdraws|quarantin|pending|merely because|"
    r"未(?:证明|证实|验证|建立)|不(?:证明|代表|等于|意味着|构成|是|能|可|得)|不能|不得|并非|"
    r"未|不|不能|不得|不会|并非|禁止|仅|只限|历史|撤回|隔离|待验证|开放问题|区分)",
    re.IGNORECASE,
)
PUBLIC_OVERCLAIM = re.compile(
    r"(?:has been proved|is proved|proved that|is a theorem|is impossible|universally impossible|"
    r"is isomorphic|\bcauses?\s+(?:the|a|an|this|that)\b|\bcauses?\s+.{1,80}\s+to\b|solved (?:the|all)|已(?:被)?证明|证明了|是(?:一个)?定理|"
    r"普遍不可能|不可能定理|严格同构|导致了|解决了)", re.IGNORECASE,
)
UNIVERSAL = re.compile(r"(?:all|every|always|never|universal|impossible|inevitable|任何|全部|所有|永远|从不|普遍|不可能|必然)", re.IGNORECASE)
THEOREM = re.compile(r"(?:theorem|lemma|proof|proved|axiom|定理|引理|证明|公理)", re.IGNORECASE)
LAW = re.compile(r"(?:\blaw\b|principle|规律|法则|原理)", re.IGNORECASE)
CAUSAL = re.compile(r"(?:caus(?:e|al)|mechanism|leads? to|results? in|因果|导致|决定|机制)", re.IGNORECASE)
CROSS_DOMAIN = re.compile(r"(?:isomorph|homomorph|correspond|projection|analogy|同构|同态|对应|投影|类比)", re.IGNORECASE)
PREDICTION = re.compile(r"(?:predict|forecast|prediction|预测|预言)", re.IGNORECASE)
EMPIRICAL = re.compile(r"(?:empirical|evidence|experiment|dataset|data show|literature|study shows|实证|证据|实验|数据表明|文献|研究表明)", re.IGNORECASE)
ONTOLOGY = re.compile(r"(?:ontology|metaphys|essence|conscious|life|本体|形而上|本质|意识|生命)", re.IGNORECASE)
NORMATIVE = re.compile(r"(?:must|shall|required|prohibited|should|不得|必须|应当|禁止|要求)", re.IGNORECASE)
REPOSITORY = re.compile(r"(?:repository|registry|workflow|validator|CI|Pages|pull request|仓库|注册表|工作流|校验器|回执)", re.IGNORECASE)
EXTERNAL = re.compile(r"(?:physics|quantum|gravity|matter|energy|cosm|society|social|conscious|life|biology|AI|物理|量子|引力|物质|能量|宇宙|社会|意识|生命|生物|人工智能)", re.IGNORECASE)
NEW_DISCOVERY = re.compile(r"(?:new discovery|novel theorem|first proof|首次证明|新发现|原创定理)", re.IGNORECASE)
MODEL_FAILURE_NOGO = re.compile(r"(?:model|模型).{0,100}(?:fail|失败|不成立).{0,100}(?:impossible|不可能)|(?:impossible|不可能).{0,100}(?:because|由于).{0,100}(?:model|模型)", re.IGNORECASE)
UNIFICATION_NOGO = re.compile(r"(?:grand unification|unification|大一统|统一).{0,80}(?:proved impossible|impossible|不可能|不可行)|(?:proved impossible|impossible|不可能).{0,80}(?:grand unification|大一统|统一)", re.IGNORECASE)
IDENT = re.compile(r"(?<![A-Za-z0-9_])(?:MF\d+|[ATDNPY]\d+)(?![A-Za-z0-9_])")

JSON_KEYS = {
    "statement", "claim", "claim_text", "conclusion", "finding", "interpretation",
    "candidate_text", "title", "summary", "description", "reason", "claim_ceiling",
    "original_text", "proposition", "prediction", "mechanism", "hypothesis",
}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_hash(row: dict) -> str:
    payload = dict(row)
    payload.pop("record_sha256", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    text = re.sub(r"[`*_#>|\[\](){}]", " ", text.casefold())
    text = re.sub(r"https?://\S+", " ", text)
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", text)


def semantic_rebound_text(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"(?:physical|structural|meta|framework(?:-internal)?|deep|higher-order|物理|结构性|元|框架内|深层|高阶)", "", text)
    return normalize(text)


def tracked_paths() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=GIT_ROOT)
    return sorted(item.decode("utf-8")[len("ignition/"):] if item.decode("utf-8").startswith("ignition/") else item.decode("utf-8") for item in raw.split(b"\0") if item)


def repo_path(path: str) -> Path:
    return REPO_ROOT / path if path.startswith(".github/") else ROOT / path


def source_context(path: str, text: str) -> str:
    if path in PUBLIC_SURFACES:
        return "CURRENT_PUBLIC_SURFACE"
    if path.startswith(("统一函数总表/", "统一案例总表/", "reports/", "archive/", "data/foundation/migrations/", "data/foundation/audits/")):
        return "HISTORICAL_OR_AUDIT_RECORD"
    if CAVEAT.search(text):
        return "BOUNDARY_OR_CORRECTION_RECORD"
    return "CURRENT_REPOSITORY_RECORD"


def candidate(text: str) -> bool:
    compact = " ".join(text.strip().split())
    if len(compact) < 8 or compact.startswith(("```", "<!--")):
        return False
    return bool(SIGNALS.search(compact))


def walk_json_strings(value: object, pointer: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key in sorted(value):
            child = value[key]
            next_pointer = f"{pointer}/{key}"
            if isinstance(child, str) and key.casefold() in JSON_KEYS:
                yield next_pointer, child
            else:
                yield from walk_json_strings(child, next_pointer)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json_strings(child, f"{pointer}/{index}")


def text_fragments(path: str) -> tuple[list[dict], str]:
    source = repo_path(path)
    suffix = source.suffix.casefold()
    try:
        raw = source.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return [], "EXCLUDED_NON_UTF8_OR_UNREADABLE"
    fragments: list[dict] = []
    if path in EXPLICIT_IMPORTS:
        return fragments, "EXPLICIT_CANONICAL_IMPORT"
    if path in SELF_EXCLUDES or path.startswith(MACHINE_EXCLUDE_PREFIXES):
        return fragments, "EXCLUDED_GENERATED_OR_FUNCTION_ASSET_REGISTRY"
    if path.startswith(NON_AUTHORITATIVE_PREFIXES):
        return fragments, "EXCLUDED_NON_AUTHORITATIVE_RECORD"
    if suffix not in TEXT_SUFFIXES:
        return fragments, "EXCLUDED_NON_TEXT_SUFFIX"
    if suffix == ".jsonl":
        for line_no, line in enumerate(raw.splitlines(), 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                value = None
            if value is not None:
                for pointer, text in walk_json_strings(value):
                    if candidate(text):
                        fragments.append({"text": " ".join(text.split()), "line": line_no, "locator": pointer})
            elif candidate(line[:2000]):
                fragments.append({"text": " ".join(line[:2000].split()), "line": line_no, "locator": "raw-line"})
    elif suffix == ".json":
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = None
        if value is not None:
            lines = raw.splitlines()
            for pointer, text in walk_json_strings(value):
                if candidate(text):
                    short = " ".join(text.split())
                    line_no = next((i for i, line in enumerate(lines, 1) if short[:60] in " ".join(line.split())), 1)
                    fragments.append({"text": short, "line": line_no, "locator": pointer})
        else:
            for line_no, line in enumerate(raw.splitlines(), 1):
                if candidate(line):
                    fragments.append({"text": " ".join(line.split())[:2000], "line": line_no, "locator": "raw-line"})
    elif suffix == ".csv":
        try:
            reader = csv.DictReader(io.StringIO(raw))
            for row_no, row in enumerate(reader, 2):
                for key, text in sorted(row.items()):
                    if text and candidate(text):
                        fragments.append({"text": " ".join(text.split())[:2000], "line": row_no, "locator": f"column:{key}"})
        except csv.Error:
            pass
    else:
        for line_no, line in enumerate(raw.splitlines(), 1):
            line = " ".join(line.strip().split())
            if not line or len(line) > 12000:
                continue
            pieces = re.split(r"(?<=[。！？.!?])\s+", line) if len(line) > 600 else [line]
            for index, piece in enumerate(pieces):
                piece = piece[:2000]
                if candidate(piece):
                    fragments.append({"text": piece, "line": line_no, "locator": f"line-fragment:{index}"})
    return fragments, "SCANNED_REGISTERED" if fragments else "SCANNED_NO_CANDIDATE"


def classify(text: str) -> str:
    if UNIFICATION_NOGO.search(text):
        return "IMPOSSIBILITY_OR_UNIVERSAL_CLAIM"
    if THEOREM.search(text):
        return "THEOREM_OR_MATHEMATICAL_CLAIM"
    if LAW.search(text):
        return "LAW_OR_PRINCIPLE_CLAIM"
    if CAUSAL.search(text):
        return "MECHANISM_OR_CAUSAL_CLAIM"
    if CROSS_DOMAIN.search(text):
        return "CROSS_DOMAIN_CORRESPONDENCE"
    if PREDICTION.search(text):
        return "PREDICTION_OR_FORECAST"
    if EMPIRICAL.search(text):
        return "EMPIRICAL_OR_LITERATURE_CLAIM"
    if ONTOLOGY.search(text):
        return "ONTOLOGICAL_OR_METAPHYSICAL_CLAIM"
    if UNIVERSAL.search(text):
        return "IMPOSSIBILITY_OR_UNIVERSAL_CLAIM"
    if NORMATIVE.search(text):
        return "NORMATIVE_OR_GOVERNANCE_CLAIM"
    if REPOSITORY.search(text):
        return "DESCRIPTIVE_REPOSITORY_CLAIM"
    if re.search(r"(?:framework|model|interpret|框架|模型|解释)", text, re.I):
        return "INTERPRETATION_OR_FRAMEWORK_CLAIM"
    return "UNRESOLVED_CLAIM"


def assertion_type(claim_class: str) -> str:
    return {
        "THEOREM_OR_MATHEMATICAL_CLAIM": "MATHEMATICAL",
        "LAW_OR_PRINCIPLE_CLAIM": "UNRESOLVED",
        "MECHANISM_OR_CAUSAL_CLAIM": "EMPIRICAL",
        "IMPOSSIBILITY_OR_UNIVERSAL_CLAIM": "UNRESOLVED",
        "CROSS_DOMAIN_CORRESPONDENCE": "INTERPRETIVE",
        "PREDICTION_OR_FORECAST": "EMPIRICAL",
        "EMPIRICAL_OR_LITERATURE_CLAIM": "EMPIRICAL",
        "ONTOLOGICAL_OR_METAPHYSICAL_CLAIM": "METAPHYSICAL",
        "INTERPRETATION_OR_FRAMEWORK_CLAIM": "INTERPRETIVE",
        "NORMATIVE_OR_GOVERNANCE_CLAIM": "NORMATIVE",
        "DESCRIPTIVE_REPOSITORY_CLAIM": "DESCRIPTIVE",
        "UNRESOLVED_CLAIM": "UNRESOLVED",
    }[claim_class]


def is_rebound(text: str) -> bool:
    if not UNIFICATION_NOGO.search(text):
        return False
    return not CAVEAT.search(text)


def disposition_for(claim_class: str, context: str, text: str, existing: dict | None, function_card: dict | None) -> str:
    if function_card:
        return {
            "KEEP_AS_ESTABLISHED_MATH": "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT",
            "KEEP_AS_TOY_MODEL": "RETAINED_AS_TOY_MODEL",
            "KEEP_AS_STRUCTURAL_METAPHOR": "RETAINED_AS_STRUCTURAL_METAPHOR",
            "DOWNGRADE_TO_CONJECTURE": "RETAINED_AS_RESEARCH_HYPOTHESIS",
            "DOWNGRADE_TO_PENDING": "PENDING_PROOF",
            "REWRITE_AND_RETEST": "REWRITE_AND_RETEST",
            "REJECT_AS_INVALID": "REJECTED_FALSE_OR_INVALID",
            "KEEP_AS_TESTED_INDEX_OR_CLASSIFIER": "RETAINED_AS_TOY_MODEL",
        }.get(function_card.get("final_disposition"), "RETAINED_AS_HEURISTIC")
    if is_rebound(text):
        return "WITHDRAWN_UNSUPPORTED"
    if context == "HISTORICAL_OR_AUDIT_RECORD":
        return "HISTORICAL_ONLY"
    if context == "BOUNDARY_OR_CORRECTION_RECORD":
        return "ACCEPTED_AS_DEFINITION"
    if CAVEAT.search(text) and re.search(r"(?:repository|registry|workflow|internal tests?|仓库|注册表|工作流|内部测试)", text, re.I):
        return "ACCEPTED_AS_DEFINITION"
    if existing and existing.get("status", {}).get("semantic_status") in {"DECLARATION_ONLY", "ADJUDICATED_NOT_VALIDATED"}:
        return "ACCEPTED_AS_DEFINITION" if REPOSITORY.search(text) else "RETAINED_AS_HEURISTIC"
    return {
        "THEOREM_OR_MATHEMATICAL_CLAIM": "PENDING_PROOF",
        "LAW_OR_PRINCIPLE_CLAIM": "PENDING_PROOF",
        "MECHANISM_OR_CAUSAL_CLAIM": "PENDING_EMPIRICAL_TEST",
        "IMPOSSIBILITY_OR_UNIVERSAL_CLAIM": "QUARANTINED_AMBIGUOUS",
        "CROSS_DOMAIN_CORRESPONDENCE": "RETAINED_AS_STRUCTURAL_METAPHOR",
        "PREDICTION_OR_FORECAST": "PENDING_EMPIRICAL_TEST",
        "EMPIRICAL_OR_LITERATURE_CLAIM": "PENDING_LITERATURE_ADJUDICATION",
        "ONTOLOGICAL_OR_METAPHYSICAL_CLAIM": "RETAINED_AS_RESEARCH_HYPOTHESIS",
        "INTERPRETATION_OR_FRAMEWORK_CLAIM": "RETAINED_AS_HEURISTIC",
        "NORMATIVE_OR_GOVERNANCE_CLAIM": "ACCEPTED_AS_DEFINITION",
        "DESCRIPTIVE_REPOSITORY_CLAIM": "ACCEPTED_AS_DEFINITION",
        "UNRESOLVED_CLAIM": "QUARANTINED_AMBIGUOUS",
    }[claim_class]


def claim_ceiling(disposition: str) -> str:
    return {
        "ACCEPTED_AS_DEFINITION": "May be stated only as a repository definition, policy, status record or explicitly scoped convention; it is not external truth.",
        "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT": "May be stated only with its declared carrier, assumptions and proof scope; it has no automatic physical or empirical implication.",
        "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT": "May be stated only to the exact scope supported by cited external evidence and replication status.",
        "RETAINED_AS_TOY_MODEL": "Toy-model result only; no inference to nature, society or universal ontology.",
        "RETAINED_AS_HEURISTIC": "Heuristic or framework-internal reading only; no theorem, causal or external-truth wording.",
        "RETAINED_AS_STRUCTURAL_METAPHOR": "Analogy or structural metaphor only; no homomorphism, isomorphism or causal identity is established.",
        "RETAINED_AS_RESEARCH_HYPOTHESIS": "Open research hypothesis only; external truth and novelty remain unestablished.",
        "PENDING_PROOF": "Candidate mathematical statement only; no theorem or proved-result wording until a scoped proof passes review.",
        "PENDING_EMPIRICAL_TEST": "Testable candidate only; no causal, predictive or established-fact wording until evidence and replication obligations are met.",
        "PENDING_LITERATURE_ADJUDICATION": "Source or literature-dependent assertion only; support, novelty and exact scope remain unadjudicated.",
        "REWRITE_AND_RETEST": "Current formulation is not publishable as a result; rewrite definitions and rerun the relevant gates.",
        "QUARANTINED_AMBIGUOUS": "Unresolved historical or current claim candidate; it cannot appear as current knowledge.",
        "WITHDRAWN_UNSUPPORTED": "Withdrawn unsupported conclusion retained for lineage only; aliases and renamed structural forms are prohibited.",
        "REJECTED_FALSE_OR_INVALID": "Rejected formulation retained for counterexample and history only.",
        "HISTORICAL_ONLY": "Historical source wording only; it is not a current repository endorsement.",
    }[disposition]


def audits_for(claim_class: str, kind: str, text: str, disposition: str, context: str) -> dict:
    accepted_definition = disposition == "ACCEPTED_AS_DEFINITION"
    theorem = claim_class in {"THEOREM_OR_MATHEMATICAL_CLAIM", "LAW_OR_PRINCIPLE_CLAIM"}
    empirical = kind == "EMPIRICAL"
    cross = claim_class == "CROSS_DOMAIN_CORRESPONDENCE"
    prediction = claim_class == "PREDICTION_OR_FORECAST"
    universal = bool(UNIVERSAL.search(text))
    external = bool(EXTERNAL.search(text)) or empirical
    rebound = is_rebound(text)
    model_nogo = bool(MODEL_FAILURE_NOGO.search(text))
    current_public = context == "CURRENT_PUBLIC_SURFACE"
    inherited_boundary_bullet = bool(re.match(r"^\s*-\s+(?:that|to)\b", text, re.I))
    question = text.rstrip().endswith(("?", "？"))
    public_violation = current_public and bool(PUBLIC_OVERCLAIM.search(text)) and not CAVEAT.search(text) and not inherited_boundary_bullet and not question and disposition not in {"ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT", "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT"}
    return {
        "definition_audit": "PASS" if accepted_definition else ("REQUIRES_HUMAN_REVIEW" if claim_class != "UNRESOLVED_CLAIM" else "FAIL"),
        "quantifier_audit": "FAIL" if universal and not CAVEAT.search(text) else "PASS",
        "proof_audit": "FAIL" if theorem and disposition != "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT" else ("PASS" if theorem else "NOT_APPLICABLE"),
        "counterexample_audit": "REQUIRES_HUMAN_REVIEW" if theorem or universal or cross else "NOT_APPLICABLE",
        "type_dimension_audit": "REQUIRES_HUMAN_REVIEW" if theorem or cross else "NOT_APPLICABLE",
        "internal_external_audit": "FAIL" if external and disposition not in {"HISTORICAL_ONLY", "WITHDRAWN_UNSUPPORTED"} and not CAVEAT.search(text) else "PASS",
        "model_class_audit": "FAIL" if model_nogo else ("REQUIRES_HUMAN_REVIEW" if universal else "NOT_APPLICABLE"),
        "cross_domain_audit": "FAIL" if cross and re.search(r"(?:isomorph|同构)", text, re.I) and not CAVEAT.search(text) else ("REQUIRES_HUMAN_REVIEW" if cross else "NOT_APPLICABLE"),
        "evidence_audit": "FAIL" if empirical or external else "NOT_APPLICABLE",
        "novelty_audit": "FAIL" if NEW_DISCOVERY.search(text) else "NOT_APPLICABLE",
        "prediction_audit": "FAIL" if prediction else "NOT_APPLICABLE",
        "conclusion_rebound_audit": "FAIL" if rebound else "PASS",
        "public_surface_audit": "FAIL" if public_violation else ("PASS" if current_public else "NOT_APPLICABLE"),
    }


def obligations_for(claim_class: str, kind: str) -> dict:
    proof = []
    empirical = []
    literature = []
    prediction = []
    if claim_class in {"THEOREM_OR_MATHEMATICAL_CLAIM", "LAW_OR_PRINCIPLE_CLAIM", "IMPOSSIBILITY_OR_UNIVERSAL_CLAIM"}:
        proof = ["State typed definitions, assumptions and quantifiers; provide a checkable proof or delimit the statement as conjectural.", "Search for countermodels inside and outside the declared model class."]
    if kind in {"EMPIRICAL", "METAPHYSICAL"} or claim_class == "MECHANISM_OR_CAUSAL_CLAIM":
        empirical = ["Define operational variables, intervention or identification assumptions, dataset provenance, baselines and failure criteria.", "Document independent replication before any replication claim."]
    if claim_class in {"EMPIRICAL_OR_LITERATURE_CLAIM", "ONTOLOGICAL_OR_METAPHYSICAL_CLAIM"}:
        literature = ["Adjudicate primary sources for the exact proposition, scope, date, novelty and contrary evidence."]
    if claim_class == "PREDICTION_OR_FORECAST":
        prediction = ["Pre-register parameters, data-access cutoff, evaluation rule, uncertainty interval and disconfirming outcome."]
    return {"proof": proof, "empirical": empirical, "literature": literature, "prediction": prediction}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def anchor(path: str, fragment: dict, context: str) -> dict:
    return {"path": path, "first_line": fragment["line"], "last_line": fragment["line"], "locator": fragment["locator"], "source_context": context}


def build() -> dict[Path, str]:
    existing_claims = load_jsonl(ROOT / "data/foundation/claims/claims.jsonl")
    function_cards = load_jsonl(ROOT / "data/foundation/function-assets/identity-cards.jsonl")
    function_by_id = {row["canonical_id"]: row for row in function_cards}
    function_ids = set(function_by_id)
    existing_by_norm = {normalize(row["statement"]): row for row in existing_claims}

    grouped: dict[str, dict] = {}
    discovery_by_path: list[dict] = []

    for row in existing_claims:
        cid = f"CLAIM-{row['id']}"
        text = " ".join(row["statement"].split())
        source = "data/foundation/claims/claims.jsonl"
        line_no = len(grouped) + 1
        grouped[cid] = {
            "canonical_id": cid,
            "text": text,
            "anchors": [anchor(source, {"line": line_no, "locator": f"jsonl:id={row['id']}"}, "CURRENT_REPOSITORY_RECORD")],
            "existing": row,
        }
    discovery_by_path.append({
        "path": "data/foundation/claims/claims.jsonl", "coverage_status": "EXPLICIT_CANONICAL_IMPORT",
        "candidate_fragments": len(existing_claims), "canonical_claim_ids": sorted(grouped),
        "exclusion_reason": None,
    })

    for path in tracked_paths():
        if path == "data/foundation/claims/claims.jsonl":
            continue
        fragments, status = text_fragments(path)
        ids_for_path: set[str] = set()
        for fragment in fragments:
            text = fragment["text"]
            norm = normalize(text)
            if not norm:
                continue
            existing = existing_by_norm.get(norm)
            if existing:
                cid = f"CLAIM-{existing['id']}"
            else:
                cid = f"NFC-{hashlib.sha256(norm.encode('utf-8')).hexdigest()[:16]}"
            context = source_context(path, text)
            if cid not in grouped:
                grouped[cid] = {"canonical_id": cid, "text": text, "anchors": [], "existing": existing}
            candidate_anchor = anchor(path, fragment, context)
            if candidate_anchor not in grouped[cid]["anchors"]:
                grouped[cid]["anchors"].append(candidate_anchor)
            ids_for_path.add(cid)
        discovery_by_path.append({
            "path": path,
            "coverage_status": status,
            "candidate_fragments": len(fragments),
            "canonical_claim_ids": sorted(ids_for_path),
            "exclusion_reason": status if status.startswith("EXCLUDED") else None,
        })

    claims: list[dict] = []
    for cid in sorted(grouped):
        item = grouped[cid]
        text = item["text"]
        anchors = sorted(item["anchors"], key=lambda row: (row["path"], row["first_line"], row["locator"]))
        contexts = {row["source_context"] for row in anchors}
        if "CURRENT_PUBLIC_SURFACE" in contexts:
            context = "CURRENT_PUBLIC_SURFACE"
        elif "CURRENT_REPOSITORY_RECORD" in contexts:
            context = "CURRENT_REPOSITORY_RECORD"
        elif "BOUNDARY_OR_CORRECTION_RECORD" in contexts:
            context = "BOUNDARY_OR_CORRECTION_RECORD"
        else:
            context = "HISTORICAL_OR_AUDIT_RECORD"
        existing = item.get("existing")
        refs = sorted(set(IDENT.findall(text)))
        direct_function_refs = [ref for ref in refs if ref in function_ids]
        authority_card = function_by_id.get(existing["id"]) if existing and existing["id"] in function_ids else None
        claim_class = classify(text)
        kind = assertion_type(claim_class)
        if authority_card:
            primary = authority_card["primary_identity"]
            if authority_card["canonical_id"] == "T2":
                claim_class = "THEOREM_OR_MATHEMATICAL_CLAIM"
            elif primary in {"STRUCTURAL_METAPHOR"}:
                claim_class = "CROSS_DOMAIN_CORRESPONDENCE"
            elif primary in {"PARAMETRIC_MATHEMATICAL_MODEL", "RELATION_OR_CONSTRAINT", "SCORING_OR_INDEX_FUNCTION"}:
                claim_class = "THEOREM_OR_MATHEMATICAL_CLAIM"
            elif primary == "CONJECTURE_OR_RESEARCH_CANDIDATE":
                claim_class = "INTERPRETATION_OR_FRAMEWORK_CLAIM"
            elif primary == "INVALID_OR_PSEUDO_FUNCTION":
                claim_class = "UNRESOLVED_CLAIM"
            kind = assertion_type(claim_class)
        disposition = disposition_for(claim_class, context, text, existing, authority_card)
        audits = audits_for(claim_class, kind, text, disposition, context)
        if authority_card:
            task99_gates = authority_card["audit_gates"]
            audits.update({
                "definition_audit": task99_gates["definition_gate"],
                "quantifier_audit": task99_gates["universal_quantifier_gate"],
                "counterexample_audit": task99_gates["counterexample_gate"],
                "type_dimension_audit": task99_gates["dimension_and_type_gate"],
                "cross_domain_audit": task99_gates["cross_domain_isomorphism_gate"],
                "proof_audit": "PASS" if disposition == "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT" else audits["proof_audit"],
                "internal_external_audit": "PASS" if authority_card["external_evidence_maturity"] in {"E0", "E1", "E2"} and disposition != "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT" else audits["internal_external_audit"],
            })
        edges = []
        for ref in refs:
            if ref in function_ids:
                edges.append({"relation": "MENTIONS_OR_DEPENDS_ON", "target": ref, "target_kind": "FUNCTION_ASSET", "resolution": "RESOLVED"})
            elif f"CLAIM-{ref}" in grouped:
                edges.append({"relation": "MENTIONS_OR_DEPENDS_ON", "target": f"CLAIM-{ref}", "target_kind": "REGISTERED_CLAIM", "resolution": "RESOLVED"})
            else:
                edges.append({"relation": "MENTIONS_OR_DEPENDS_ON", "target": ref, "target_kind": "EXTERNAL_OR_UNRESOLVED", "resolution": "EXPLICITLY_UNRESOLVED"})
        inherited = authority_card is not None
        math_maturity = authority_card["mathematical_maturity"] if inherited else ("M1" if kind == "MATHEMATICAL" else "M0")
        external_maturity = authority_card["external_evidence_maturity"] if inherited else ("E1" if context == "HISTORICAL_OR_AUDIT_RECORD" else "E0")
        if kind == "EMPIRICAL" or EXTERNAL.search(text):
            internal_external = "EXTERNAL"
        elif claim_class == "CROSS_DOMAIN_CORRESPONDENCE":
            internal_external = "MIXED_OR_UNRESOLVED"
        else:
            internal_external = "MODEL_INTERNAL"
        source_refs = [{"kind": "SOURCE_TEXT", "path": row["path"], "line": row["first_line"], "supports_exact_claim": False} for row in anchors]
        if authority_card:
            source_refs.append({"kind": "FUNCTION_ASSET_AUTHORITY", "canonical_id": authority_card["canonical_id"], "supports_exact_claim": disposition == "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT"})
        title = re.sub(r"^[#>*\-\s\d.]+", "", text).strip()[:120] or cid
        scope = "Exact source-defined repository scope" if context != "HISTORICAL_OR_AUDIT_RECORD" else "Historical source wording only"
        quantifier = "UNRESOLVED_OR_OVERBROAD" if UNIVERSAL.search(text) and not CAVEAT.search(text) else "BOUNDED_OR_NO_UNIVERSAL_QUANTIFIER_DETECTED"
        row = {
            "canonical_id": cid,
            "canonical_title": title,
            "minimal_atomic_claim": text,
            "claim_class": claim_class,
            "assertion_type": kind,
            "internal_external_status": internal_external,
            "scope_and_quantifiers": {"scope": scope, "quantifier_status": quantifier, "model_class": "SOURCE_DECLARED_OR_UNRESOLVED"},
            "assumptions": authority_card["assumptions_and_quantifiers"]["assumptions"] if authority_card else ["No assumption beyond the exact source fragment is inferred automatically."],
            "definitions": [authority_card["definition"]["exact_expression_or_executable_specification"]] if authority_card else ["UNRESOLVED: consult the cited source and linked function identity cards; discovery does not supply missing definitions."],
            "obligations": {"proof": authority_card["proof_obligations"], "empirical": authority_card["empirical_obligations"], "literature": [], "prediction": []} if authority_card else obligations_for(claim_class, kind),
            "counterexamples_and_defeaters": authority_card["known_counterexamples"] if authority_card else (["No counterexample is invented by the registry; applicable counterexample search remains an explicit audit obligation."] if audits["counterexample_audit"] != "NOT_APPLICABLE" else []),
            "dependency_edges": edges,
            "mathematical_maturity": math_maturity,
            "external_evidence_maturity": external_maturity,
            "replication_status": "NOT_APPLICABLE" if kind in {"MATHEMATICAL", "NORMATIVE", "DESCRIPTIVE", "INTERPRETIVE"} else "NO_REPLICATION_CLAIMED",
            "final_disposition": disposition,
            "claim_ceiling": authority_card["claim_ceiling"] if authority_card else claim_ceiling(disposition),
            "prohibited_wording": authority_card["prohibited_uses"] if authority_card else ["Do not present registry presence, internal tests, AI agreement or formal appearance as proof, external validation, novelty, peer review or replication."],
            "supersession_lineage": {
                "status": "WITHDRAWN_NO_REBOUND" if disposition == "WITHDRAWN_UNSUPPORTED" else ("HISTORICAL_PRESERVED" if disposition == "HISTORICAL_ONLY" else "CURRENT_SCOPED_RECORD"),
                "supersedes": [],
                "superseded_by": [],
                "lineage_key": "PHYSICS_UNIFICATION_NOGO" if UNIFICATION_NOGO.search(text) else None,
            },
            "evidence_references": source_refs,
            "source_anchors": anchors,
            "audit_gates": audits,
            "reviewer_state": "TASK98_99_AUTHORITY_INHERITED" if inherited else ("EXISTING_CANONICAL_CLAIM_MAPPED" if existing else ("EXPLICITLY_QUARANTINED" if disposition == "QUARANTINED_AMBIGUOUS" else "SOURCE_TEXT_RULE_ADJUDICATED")),
            "record_sha256": "",
        }
        row["record_sha256"] = record_hash(row)
        claims.append(row)

    claim_ids = {row["canonical_id"] for row in claims}
    reverse: dict[str, set[str]] = defaultdict(set)
    graph = []
    for row in claims:
        for edge in row["dependency_edges"]:
            reverse[edge["target"]].add(row["canonical_id"])
        graph.append({
            "canonical_id": row["canonical_id"],
            "outgoing": row["dependency_edges"],
            "incoming_claims": [],
            "all_edges_resolved_or_explicit": all(edge["resolution"] in {"RESOLVED", "EXPLICITLY_UNRESOLVED"} for edge in row["dependency_edges"]),
        })
    for row in graph:
        row["incoming_claims"] = sorted(reverse.get(row["canonical_id"], set()))

    evidence_lineage = [{
        "canonical_id": row["canonical_id"],
        "source_evidence": row["evidence_references"],
        "external_evidence_status": "NO_EXTERNAL_EVIDENCE_LINKED_OR_ADJUDICATED" if row["external_evidence_maturity"] in {"E0", "E1", "E2"} else "SEE_REFERENCES",
        "replication_status": row["replication_status"],
        "supports_exact_claim": row["final_disposition"] in {"ACCEPTED_AS_DEFINITION", "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT"},
        "limitation": "A source anchor proves provenance only. It does not by itself establish truth, novelty, causation, prediction or replication.",
    } for row in claims]

    ledger = [{
        "canonical_id": row["canonical_id"], "claim_class": row["claim_class"],
        "mathematical_maturity": row["mathematical_maturity"], "external_evidence_maturity": row["external_evidence_maturity"],
        "replication_status": row["replication_status"], "final_disposition": row["final_disposition"],
        "failed_audits": sorted(name for name, result in row["audit_gates"].items() if result == "FAIL"),
        "claim_ceiling": row["claim_ceiling"], "reviewer_state": row["reviewer_state"],
    } for row in claims]

    risks = [{
        "canonical_id": row["canonical_id"],
        "risk_gates": {name: result for name, result in row["audit_gates"].items() if result in {"FAIL", "REQUIRES_HUMAN_REVIEW"}},
        "blocked_by_disposition": row["final_disposition"] not in {"ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT", "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT"},
        "downstream_claim_count": len(reverse.get(row["canonical_id"], set())),
    } for row in claims if any(value in {"FAIL", "REQUIRES_HUMAN_REVIEW"} for value in row["audit_gates"].values())]

    rebound_rows = []
    for row in claims:
        if UNIFICATION_NOGO.search(row["minimal_atomic_claim"]):
            rebound_rows.append({
                "canonical_id": row["canonical_id"], "lineage": "PHYSICS_UNIFICATION_NOGO",
                "semantic_key": semantic_rebound_text(row["minimal_atomic_claim"]),
                "candidate": is_rebound(row["minimal_atomic_claim"]),
                "status": "BLOCKED_BY_DISPOSITION" if is_rebound(row["minimal_atomic_claim"]) else "BOUNDARY_OR_HISTORY_ONLY",
                "final_disposition": row["final_disposition"],
            })

    public_rows = []
    for row in claims:
        for item in row["source_anchors"]:
            if item["path"] in PUBLIC_SURFACES:
                violation = row["audit_gates"]["public_surface_audit"] == "FAIL"
                public_rows.append({
                    "canonical_id": row["canonical_id"], "source_path": item["path"], "line": item["first_line"],
                    "claim_ceiling": row["claim_ceiling"], "final_disposition": row["final_disposition"],
                    "current_violation": violation, "status": "VIOLATION_REQUIRES_SOURCE_CORRECTION" if violation else "WITHIN_CEILING",
                })

    quarantine_dispositions = {
        "PENDING_PROOF", "PENDING_EMPIRICAL_TEST", "PENDING_LITERATURE_ADJUDICATION", "REWRITE_AND_RETEST",
        "QUARANTINED_AMBIGUOUS", "WITHDRAWN_UNSUPPORTED", "REJECTED_FALSE_OR_INVALID",
    }
    quarantine = [{
        "canonical_id": row["canonical_id"], "final_disposition": row["final_disposition"],
        "reason": row["claim_ceiling"], "resume_key": f"task100:{row['canonical_id']}",
        "required_obligations": row["obligations"],
    } for row in claims if row["final_disposition"] in quarantine_dispositions]

    supersession = [{
        "canonical_id": row["canonical_id"], "lineage_status": row["supersession_lineage"]["status"],
        "lineage_key": row["supersession_lineage"]["lineage_key"],
        "source_anchors": row["source_anchors"], "current_disposition": row["final_disposition"],
    } for row in claims if row["supersession_lineage"]["status"] != "CURRENT_SCOPED_RECORD"]

    class_counts = Counter(row["claim_class"] for row in claims)
    type_counts = Counter(row["assertion_type"] for row in claims)
    disposition_counts = Counter(row["final_disposition"] for row in claims)
    m_counts = Counter(row["mathematical_maturity"] for row in claims)
    e_counts = Counter(row["external_evidence_maturity"] for row in claims)
    coverage_counts = Counter(row["coverage_status"] for row in discovery_by_path)
    total_candidates = sum(row["candidate_fragments"] for row in discovery_by_path)
    active_rebounds = sum(row["status"] not in {"BLOCKED_BY_DISPOSITION", "BOUNDARY_OR_HISTORY_ONLY"} for row in rebound_rows)
    summary = {
        "task_id": "IGNITION-CORPUS-WIDE-NONFUNCTION-CLAIM-ADJUDICATION-AND-EVIDENCE-LINEAGE-CLOSURE-R1-20260729",
        "source_base_commit": "ebe723fbf544f3fa1a87706e82493319d9f0af7e",
        "tracked_files_accounted": len(discovery_by_path),
        "candidate_fragments": total_candidates,
        "canonical_claims": len(claims),
        "existing_claims_mapped": len(existing_claims),
        "explicit_quarantine_or_pending": len(quarantine),
        "dependency_edges": sum(len(row["dependency_edges"]) for row in claims),
        "explicitly_unresolved_dependency_edges": sum(edge["resolution"] == "EXPLICITLY_UNRESOLVED" for row in claims for edge in row["dependency_edges"]),
        "public_surface_records": len(public_rows),
        "public_surface_violations": sum(row["current_violation"] for row in public_rows),
        "conclusion_rebound_candidates": len(rebound_rows),
        "blocked_conclusion_rebounds": sum(row["status"] == "BLOCKED_BY_DISPOSITION" for row in rebound_rows),
        "active_conclusion_rebounds": active_rebounds,
        "claim_class_distribution": dict(sorted(class_counts.items())),
        "assertion_type_distribution": dict(sorted(type_counts.items())),
        "disposition_distribution": dict(sorted(disposition_counts.items())),
        "mathematical_maturity_distribution": dict(sorted(m_counts.items())),
        "external_evidence_distribution": dict(sorted(e_counts.items())),
        "source_coverage_distribution": dict(sorted(coverage_counts.items())),
        "registry_closed": True,
        "closure_semantics": "Registry accounting is closed by explicit disposition or quarantine. Mathematical proof, external evidence, novelty and replication obligations remain independently open.",
    }
    coverage = {
        "tracked_files": len(discovery_by_path), "candidate_fragments": total_candidates,
        "canonical_claims": len(claims), "coverage_status_counts": dict(sorted(coverage_counts.items())),
        "assertions": {
            "every_tracked_path_accounted": len({row["path"] for row in discovery_by_path}) == len(discovery_by_path),
            "every_candidate_maps_to_canonical_claim": all(cid in claim_ids for row in discovery_by_path for cid in row["canonical_claim_ids"]),
            "every_claim_has_source_anchor": all(row["source_anchors"] for row in claims),
            "generated_and_prior_function_registries_excluded_explicitly": True,
        },
    }

    out: dict[Path, str] = {}
    def jsonl(name: str, rows: list[dict]) -> None:
        out[OUT / name] = "".join(canonical_json(row) + "\n" for row in rows)
    jsonl("claim-registry.jsonl", claims)
    jsonl("source-discovery.jsonl", discovery_by_path)
    jsonl("adjudication-ledger.jsonl", ledger)
    jsonl("evidence-lineage.jsonl", evidence_lineage)
    jsonl("dependency-graph.jsonl", graph)
    jsonl("inference-risk-report.jsonl", risks)
    jsonl("conclusion-rebound-report.jsonl", rebound_rows)
    jsonl("public-surface-report.jsonl", public_rows)
    jsonl("unresolved-quarantine.jsonl", quarantine)
    jsonl("supersession-lineage.jsonl", supersession)
    out[OUT / "closure-summary.json"] = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out[OUT / "discovery-coverage.json"] = json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(["canonical_id", "claim_class", "assertion_type", "mathematical_maturity", "external_evidence_maturity", "replication_status", "final_disposition", "source_anchor_count", "failed_audits", "claim_ceiling"])
    for row in claims:
        writer.writerow([row["canonical_id"], row["claim_class"], row["assertion_type"], row["mathematical_maturity"], row["external_evidence_maturity"], row["replication_status"], row["final_disposition"], len(row["source_anchors"]), ";".join(name for name, result in row["audit_gates"].items() if result == "FAIL"), row["claim_ceiling"]])
    out[OUT / "claim-inventory.csv"] = csv_buffer.getvalue()

    high_risk = sorted(risks, key=lambda row: (-len(row["risk_gates"]), -row["downstream_claim_count"], row["canonical_id"]))[:80]
    lines = [
        "# 全语料非函数型断言裁决索引",
        "",
        "> 本索引是任务 100 的生成视图。注册表闭合只表示每个可复现发现的候选已有显式处置或隔离；不表示语料为真、定理已证明、外部证据充分、通过同行评审或获得独立复现。",
        "",
        "## 闭合摘要",
        "",
        f"- 已核算跟踪文件：{summary['tracked_files_accounted']}",
        f"- 候选片段：{summary['candidate_fragments']}",
        f"- 规范断言：{summary['canonical_claims']}",
        f"- 既有断言映射：{summary['existing_claims_mapped']}",
        f"- 显式隔离或待决：{summary['explicit_quarantine_or_pending']}",
        f"- 依赖边：{summary['dependency_edges']}",
        f"- 公共表面当前越界：{summary['public_surface_violations']}",
        f"- 活跃结论回弹：{summary['active_conclusion_rebounds']}",
        "",
        "## 处置分布",
        "",
        "|处置|数量|",
        "|---|---:|",
    ]
    lines.extend(f"|{key}|{value}|" for key, value in sorted(disposition_counts.items()))
    lines.extend(["", "## 高风险队列（机器完整表的有限视图）", "", "|ID|失败/待审门禁|下游数量|是否由处置阻断|", "|---|---|---:|---|"])
    lines.extend(f"|{row['canonical_id']}|{', '.join(f'{key}:{value}' for key, value in row['risk_gates'].items())}|{row['downstream_claim_count']}|{str(row['blocked_by_disposition']).lower()}|" for row in high_risk)
    lines.extend([
        "", "## 权威边界", "",
        "- 任务 98—99 已人工裁决的函数身份优先于本轮自动发现；依赖只继承其 M/E 和断言上限，不继承外部真实性。",
        "- 类比不是同构；同构必须给出对象、映射、双射与结构保持证明。",
        "- 一个模型类失败不能推出所有统一理论都不可能。物理学大一统仍是开放研究问题。",
        "- 本地测试和生成器确定性只验证登记与门禁，不验证自然、社会、生命、意识或 AI 的外部断言。",
        "", "机器完整表：`data/foundation/nonfunction-claims/`。未来断言入口：`docs/foundation/future-claim-admission-protocol.md`。", "",
    ])
    out[INDEX] = "\n".join(lines)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    if args.check:
        mismatches = [str(path.relative_to(ROOT)) for path, content in outputs.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
        if mismatches:
            print("NONFUNCTION_CLAIM_OUTPUT_DRIFT")
            for path in mismatches:
                print(path)
            return 1
        print(f"NONFUNCTION_CLAIM_GENERATION_DETERMINISTIC files={len(outputs)}")
        return 0
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    summary = json.loads(outputs[OUT / "closure-summary.json"])
    print(canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
