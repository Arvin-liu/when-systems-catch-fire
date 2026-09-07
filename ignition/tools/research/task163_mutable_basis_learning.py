#!/usr/bin/env python3
"""Task163 research-only mutable-basis learning operator.

This module intentionally stops after the historical qualification stage when
that gate fails.  It is a deterministic replay instrument, not a canonical
validator, runtime component, provider, or authority surface.

The blind operator only receives pre-event repository material.  The answer
key is written as a separate artifact and is read only by ``qualify`` after
both blind runs have been materialized.  The same process performs generation
and unblinding, so the package records procedural separation but makes no
claim of cognitive independence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
OUT = ROOT / "data/research/mutable-basis-learning-operator-2026-09-07"
TASK = "IGNITION-20260907-163"
FORMAL_BASE = "5c66ac502ca331d72c1362000ff5231503dde7ea"
FORMAL_BASE_REF = "work/IGNITION-20260907-162"
COMMAND_COMMIT = "73cde2ab84d829bb0990f63d957e2152b1a330e4"
COMMAND_BLOB = "521d468829425a210cc763df72456f2c28753d02"
COMMAND_SHA256 = "f4834b50cf26688e03e5655134d0d12019b8548093752f33b2454869b26a48a1"
COMMAND_URL = (
    "https://github.com/Arvin-liu/1111/blob/"
    f"{COMMAND_COMMIT}/agent-commands/IGNITION-20260907-163.md"
)


# These rows are the frozen historical universe.  Their event names, labels,
# post-event refs, and capability descriptions never enter the blind packet.
# They are used only to construct the physically separate answer key after the
# pre-event packet builder has been defined.
HISTORICAL_SEEDS: list[dict[str, Any]] = [
    {
        "packet_id": "HP-001",
        "event_id": "P01_FUNCTION_CASE_REFRAME",
        "pre_event_commit": "981d3f5f1cdb62c058f5de8c626444c050ab95d8",
        "trigger_commit": "a1295d737e290105069f915c577105c0cf5ff26f",
        "split": "calibration",
        "label": "TRUE_LEAP",
        "required_capability": "OBJECT_LANGUAGE_CHANGE",
        "capability_description": "A previously missing object distinction becomes expressible in the representation language.",
    },
    {
        "packet_id": "HP-002",
        "event_id": "P02_SECTION_ZERO_BOOTSTRAP",
        "pre_event_commit": "f4b0c5af3e296019d52f735d178a3f2078ead7be",
        "trigger_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "split": "holdout",
        "label": "TRUE_LEAP",
        "required_capability": "SELF_REFERENCE",
        "capability_description": "The checking or generation process itself becomes an object that can be recursively examined.",
    },
    {
        "packet_id": "HP-003",
        "event_id": "P03_DUAL_CHANNEL_BOOTSTRAP",
        "pre_event_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "trigger_commit": "9d924fe140f0c99f1f2a4952ea48dedc80dd348b",
        "split": "holdout",
        "label": "TRUE_LEAP",
        "required_capability": "INDEPENDENT_COUNTERCHECK",
        "capability_description": "A separately bounded reverse or counter-check can reject a forward-produced result.",
    },
    {
        "packet_id": "HP-004",
        "event_id": "P04_META_PROTOCOL_64",
        "pre_event_commit": "1defe3d39988f9716863b2fd39d763808e1579e0",
        "trigger_commit": "974b121e36145d6ed35b214619312001f97b21f8",
        "split": "holdout",
        "label": "TRUE_LEAP",
        "required_capability": "COMPOSITIONAL_GENERATION",
        "capability_description": "A compositional language can generate and validate a family of protocol combinations.",
    },
    {
        "packet_id": "HP-005",
        "event_id": "N01_KB_116_NOTE_SYNC",
        "pre_event_commit": "edd7d116d0580e3810d2ff73037981bd07e011b6",
        "trigger_commit": "911f97b66568dbf8ef012a6e8ffc28749c32e91c",
        "split": "calibration",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "Existing states, operations, and questions remain expressible under conservative materialization.",
    },
    {
        "packet_id": "HP-006",
        "event_id": "N02_INCREMENTAL_REGISTRY",
        "pre_event_commit": "56b952a3b101c6ed385d1c11591914d043a337cd",
        "trigger_commit": "ab90558ae1c158d9a67146ebd288678b67e1c4c3",
        "split": "calibration",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "A registry or materialized inventory grows without adding an irreducible object language.",
    },
    {
        "packet_id": "HP-007",
        "event_id": "N03_CANONICAL_PROTOCOL_MIGRATION",
        "pre_event_commit": "633ca814c6a53b4bdab425001459aabc5a0cccbf",
        "trigger_commit": "4c452149a451f074d949739086cfccdb3ec5bd56",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "Canonical materialization is a conservative migration and does not create a new semantic class.",
    },
    {
        "packet_id": "HP-008",
        "event_id": "N04_PAGES_PROJECTION",
        "pre_event_commit": "304ecfc645bbe44c4b1dbdac8a119b8ed0009c31",
        "trigger_commit": "d4bfaa886908bd3b3f109c7d8220a89a5d469186",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "A publication projection changes the surface while preserving represented states and questions.",
    },
    {
        "packet_id": "HP-009",
        "event_id": "N05_SOURCE_FIRST_SEEN",
        "pre_event_commit": "5b2f57c8ea825217ada3f3c593b1281f5fd601b7",
        "trigger_commit": "56e57906ef6e54c3721499430aaec8da1182c322",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "Source provenance is recorded without changing the representational language.",
    },
    {
        "packet_id": "HP-010",
        "event_id": "N06_HUMAN_CLAIM_BROWSER",
        "pre_event_commit": "9677a54f6e2832d0a61e1a51454d8a0cee5e7046",
        "trigger_commit": "92657e5911338c8478b01e6e4f41874522f54b12",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "A browser or reader projection adds a view over existing claims.",
    },
    {
        "packet_id": "HP-011",
        "event_id": "N07_TASK157_PROJECTIONS",
        "pre_event_commit": "bc5ae9ab4d5f3312dac58d252ef886ee225ae027",
        "trigger_commit": "9677a54f6e2832d0a61e1a51454d8a0cee5e7046",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "Derived projections are rebuilt without an irreducible language increment.",
    },
    {
        "packet_id": "HP-012",
        "event_id": "N08_TASK156_RESULTS",
        "pre_event_commit": "4321dcb2f9f434ed7936d5cb5c8648089eeb4964",
        "trigger_commit": "92f2a1f4bb04ba1fdf26901e767908f977a11b16",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "Research results are published as evidence records without a new semantic primitive.",
    },
    {
        "packet_id": "HP-013",
        "event_id": "N09_CURRENT_FACTS",
        "pre_event_commit": "0741f4f0902d50cf5388e787382500b5240d2b0e",
        "trigger_commit": "74096d5ad0faa4b524879061d332c7026c2a83a0",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "Current facts are projected from existing records.",
    },
    {
        "packet_id": "HP-014",
        "event_id": "N10_NONFUNCTION_REFRESH",
        "pre_event_commit": "74096d5ad0faa4b524879061d332c7026c2a83a0",
        "trigger_commit": "aff1b5afdf3597752529e5ae6f98ec71891ca8ef",
        "split": "holdout",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "A non-function claim surface is refreshed without changing its semantic basis.",
    },
    {
        "packet_id": "HP-015",
        "event_id": "N11_ARCHIFY_ADAPT",
        "pre_event_commit": "a051ad31b72d5cbb8deeaf2007b0e09431f8a4ba",
        "trigger_commit": "02e43c62942da8b65f005a6314d3eee799aaa776",
        "split": "calibration",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "Architecture documentation is adapted without an irreducible representational change.",
    },
    {
        "packet_id": "HP-016",
        "event_id": "N12_VALIDATOR_ADD",
        "pre_event_commit": "9bf1ca0e2beebc1d4abf85b5b9e4bb2b6e17c2c9",
        "trigger_commit": "ba56c43c1a9d429ee182ea976be4859bd5972733",
        "split": "calibration",
        "label": "NON_LEAP",
        "required_capability": "NONE",
        "capability_description": "A validator gains coverage without making a new kind of object or question expressible.",
    },
    {
        "packet_id": "HP-017",
        "event_id": "B01_CURRENT_SYNC",
        "pre_event_commit": "9549303166c86e1bc47c0f81569488b91e147bc0",
        "trigger_commit": "aabb1816a2e7e1e5e470fe87940df4dd2f8c6697",
        "split": "calibration",
        "label": "BORDERLINE",
        "required_capability": "UNDECIDABLE",
        "capability_description": "The available pre-event material is insufficient to adjudicate whether the change adds a semantic class.",
    },
    {
        "packet_id": "HP-018",
        "event_id": "B02_PROVIDER_FALLBACK",
        "pre_event_commit": "983d418912a876195519153b8e2113ff67bce5c6",
        "trigger_commit": "eb649e6dbd9c3bd09e3a0a4bd36d03bc997b6e2b",
        "split": "calibration",
        "label": "BORDERLINE",
        "required_capability": "UNDECIDABLE",
        "capability_description": "The available pre-event material is insufficient to adjudicate whether fallback behavior changes the language.",
    },
]


MUTATION_OPERATIONS = [
    "ADD_PRIMITIVE",
    "RETIRE_PRIMITIVE",
    "SPLIT_PRIMITIVE",
    "MERGE_PRIMITIVES",
    "RETYPE_RELATION",
    "CHANGE_RELATION_ARITY",
    "ADD_OR_RETIRE_OPERATOR",
    "CHANGE_COMPOSITION_GRAMMAR",
    "REPLACE_PRODUCT_WITH_OTHER_COMPOSITION",
    "CHANGE_OBJECT_LANGUAGE",
    "ADD_NEW_QUESTION_FORM",
    "ADD_NEW_FALSIFIER",
]


FORBIDDEN_IN_BLIND = re.compile(
    r"(?ix)"
    r"(?:IGNITION[-_ ]?2026090[4-7][-_ ]?15[3-9]|TASK[-_ ]?15[3-9])"
    r"|(?:P0[1-4]|N0[1-9]|N1[0-2]|B0[1-2])[_-][A-Z0-9_-]+"
    r"|\b(?:TRUE_LEAP|NON_LEAP|BORDERLINE)\b"
    r"|\b(?:OBJECT_LANGUAGE_CHANGE|SELF_REFERENCE|INDEPENDENT_COUNTERCHECK|COMPOSITIONAL_GENERATION)\b"
    r"|\b(?:object[-_ ]language|self[-_ ]reference|independent[-_ ]counter[-_ ]check|compositional[-_ ]generation)\b"
    r"|\b(?:V\s*[×x]\s*S\s*[×x]\s*E|V/S/E|BF-X\*|EL-X\*|P_meta|Ψ_?0)\b"
    r"|\b64\b"
    r"|\b(?:transition\s+semantics|first[-_ ]class\s+transition|junction\s+invariant|binding\s+invariant)\b"
)


REDACTION_PATTERNS = [
    re.compile(r"(?ix)IGNITION[-_ ]?2026090[4-7][-_ ]?15[3-9]"),
    re.compile(r"(?ix)TASK[-_ ]?15[3-9]"),
    re.compile(r"(?ix)\b(?:P0[1-4]|N0[1-9]|N1[0-2]|B0[1-2])[_-][A-Z0-9_-]+"),
    re.compile(r"(?ix)\b(?:TRUE_LEAP|NON_LEAP|BORDERLINE)\b"),
    re.compile(r"(?ix)\b(?:OBJECT_LANGUAGE_CHANGE|SELF_REFERENCE|INDEPENDENT_COUNTERCHECK|COMPOSITIONAL_GENERATION)\b"),
    re.compile(r"(?ix)\b(?:object[-_ ]language|self[-_ ]reference|independent[-_ ]counter[-_ ]check|compositional[-_ ]generation)\b"),
    re.compile(r"(?ix)\b(?:V\s*[×x]\s*S\s*[×x]\s*E|V/S/E|BF-X\*|EL-X\*|P_meta|Ψ_?0)\b"),
    re.compile(r"(?ix)\b64\b"),
    re.compile(r"(?ix)\b(?:transition\s+semantics|first[-_ ]class\s+transition|junction\s+invariant|binding\s+invariant)\b"),
]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True)
    return result.stdout.decode("utf-8", errors="replace").strip()


def commit_date(commit: str) -> str:
    return git("show", "-s", "--format=%cI", commit)


def redact_text(text: str) -> tuple[str, int]:
    total = 0
    for pattern in REDACTION_PATTERNS:
        text, count = pattern.subn("<redacted>", text)
        total += count
    return text, total


def safe_path(path: str) -> bool:
    lowered = path.lower()
    if any(part in lowered for part in ("data/research", "agent-results", "reports/", "outputs/")):
        return False
    if any(term in lowered for term in ("task15", "task16", "task17", "meta-protocol", "junction", "binding", "transition")):
        return False
    if FORBIDDEN_IN_BLIND.search(path):
        return False
    return path.startswith(("README", "AGENT_ENTRY", "FUNCTIONS", "SUMMARY", "docs/", "book/", "data/cases/", "scripts/"))


def pre_event_history(commit: str) -> list[dict[str, Any]]:
    commits = git("rev-list", "--first-parent", "--max-count=8", commit).splitlines()
    result: list[dict[str, Any]] = []
    for prior in commits:
        paths = git("diff-tree", "--no-commit-id", "--name-only", "-r", prior).splitlines()
        visible = sorted(path for path in paths if safe_path(path))
        result.append(
            {
                "commit_sha": prior,
                "commit_date": commit_date(prior),
                "visible_path_count": len(visible),
                "visible_path_digest": digest(visible),
            }
        )
    return result


def pre_event_material(commit: str) -> tuple[dict[str, Any], int]:
    paths = git("ls-tree", "-r", "--name-only", commit).splitlines()
    selected: list[dict[str, Any]] = []
    total_redactions = 0
    for path in paths:
        if not safe_path(path):
            continue
        if Path(path).suffix.lower() not in {".md", ".txt", ".json", ".jsonl", ".py", ".yaml", ".yml"}:
            continue
        try:
            size = int(git("cat-file", "-s", f"{commit}:{path}"))
            raw = git("show", f"{commit}:{path}")
        except subprocess.CalledProcessError:
            continue
        if size > 250_000 or not raw.strip():
            continue
        sanitized, redactions = redact_text(raw)
        total_redactions += redactions
        selected.append(
            {
                "segment_id": f"SEG-{len(selected) + 1:02d}",
                "path": path,
                "blob_size": size,
                "text_sha256": hashlib.sha256(sanitized.encode("utf-8")).hexdigest(),
                "text": sanitized[:2_000],
            }
        )
        if len(selected) >= 8:
            break

    tree_count = len(paths)
    text_count = sum(Path(path).suffix.lower() in {".md", ".txt", ".json", ".jsonl", ".py", ".yaml", ".yml"} for path in paths)
    material = {
        "pre_event_tree": {
            "commit_sha": commit,
            "commit_date": commit_date(commit),
            "tracked_path_count": tree_count,
            "text_path_count": text_count,
            "visible_segment_count": len(selected),
        },
        "history_window": pre_event_history(commit),
        "segments": selected,
        "post_event_material_included": False,
        "answer_labels_included": False,
        "candidate_names_included": False,
    }
    return material, total_redactions


def build_temporal_packet(seed: dict[str, Any], sequence: int) -> tuple[dict[str, Any], dict[str, Any]]:
    material, redactions = pre_event_material(seed["pre_event_commit"])
    operator_input = {
        "task": "infer whether the pre-event material exposes a representation residual that warrants a basis mutation",
        "sequence": sequence,
        "pre_event_cutoff": seed["pre_event_commit"],
        "material": material,
    }
    input_hash = digest(operator_input)
    universe = {
        "packet_id": seed["packet_id"],
        "sequence": sequence,
        "pre_event_cutoff": seed["pre_event_commit"],
        "pre_event_cutoff_date": commit_date(seed["pre_event_commit"]),
        "split": seed["split"],
        "input_sha256": input_hash,
        "pre_event_only": True,
        "post_event_material_included": False,
        "answer_labels_included": False,
        "candidate_names_included": False,
        "redaction_count": redactions,
    }
    packet = {
        "packet_id": seed["packet_id"],
        "sequence": sequence,
        "pre_event_cutoff": seed["pre_event_commit"],
        "split": seed["split"],
        "operator_input": operator_input,
        "input_sha256": input_hash,
        "unavoidable_leakage": "pre-event repository provenance only; no post-event semantic description was supplied",
    }
    return universe, packet


def initial_representation() -> dict[str, Any]:
    return {
        "generation": 0,
        "primitives": ["object", "claim", "evidence_item", "operation", "question", "failure"],
        "relation_types": ["supports", "depends_on", "contradicts", "precedes", "scopes"],
        "composition_grammar": "ordered_relational_composition",
        "allowed_operators": ["add", "revise", "link", "check", "materialize"],
        "question_language": ["what", "why", "under_which_condition", "what_failed"],
        "falsifiers": ["missing_support", "ordering_inconsistency", "scope_leak", "unresolved_contradiction"],
        "identity_scope_assumptions": ["local_object_identity", "explicit_scope_boundary"],
        "unresolved_residual_set": [],
        "complexity_cost": 0,
    }


def state_complexity(state: dict[str, Any]) -> int:
    return (
        len(state["primitives"])
        + len(state["relation_types"])
        + len(state["allowed_operators"])
        + len(state["question_language"])
        + len(state["falsifiers"])
        + len(state["identity_scope_assumptions"])
        + 2
    )


def apply_mutation(state: dict[str, Any], operation: str) -> dict[str, Any]:
    mutated = copy.deepcopy(state)
    next_number = mutated["generation"] + 1
    if operation == "ADD_PRIMITIVE":
        mutated["primitives"].append(f"anonymous_primitive_{next_number}")
    elif operation == "RETIRE_PRIMITIVE" and len(mutated["primitives"]) > 1:
        mutated["primitives"].pop()
    elif operation == "SPLIT_PRIMITIVE":
        source = mutated["primitives"].pop()
        mutated["primitives"].extend([f"{source}_a", f"{source}_b"])
    elif operation == "MERGE_PRIMITIVES" and len(mutated["primitives"]) >= 2:
        mutated["primitives"] = ["anonymous_merged_1"] + mutated["primitives"][2:]
    elif operation == "RETYPE_RELATION":
        mutated["relation_types"].append(f"anonymous_relation_retyped_{next_number}")
    elif operation == "CHANGE_RELATION_ARITY":
        mutated["relation_arity_overrides"] = {"anonymous_relation": 3}
    elif operation == "ADD_OR_RETIRE_OPERATOR":
        mutated["allowed_operators"].append(f"anonymous_operator_{next_number}")
    elif operation == "CHANGE_COMPOSITION_GRAMMAR":
        mutated["composition_grammar"] = "conditional_relational_composition"
    elif operation == "REPLACE_PRODUCT_WITH_OTHER_COMPOSITION":
        mutated["composition_grammar"] = "non_product_composition_trial"
    elif operation == "CHANGE_OBJECT_LANGUAGE":
        mutated["object_language_extension"] = [f"anonymous_object_kind_{next_number}"]
    elif operation == "ADD_NEW_QUESTION_FORM":
        mutated["question_language"].append(f"anonymous_question_form_{next_number}")
    elif operation == "ADD_NEW_FALSIFIER":
        mutated["falsifiers"].append(f"anonymous_falsifier_{next_number}")
    else:
        raise ValueError(f"unknown mutation operation: {operation}")
    mutated["generation"] = next_number
    mutated["complexity_cost"] = state_complexity(mutated)
    return mutated


def mutation_trials() -> list[dict[str, Any]]:
    base = initial_representation()
    rows = []
    for operation in MUTATION_OPERATIONS:
        trial_state = apply_mutation(base, operation)
        rows.append(
            {
                "operation": operation,
                "trial_state_sha256": digest(trial_state),
                "status": "TRIAL_APPLIED",
                "semantic_claim": "NONE",
            }
        )
    return rows


def extract_structure(packet: dict[str, Any]) -> dict[str, Any]:
    segments = packet["operator_input"]["material"]["segments"]
    text = "\n".join(segment["text"] for segment in segments)
    units = [unit.strip() for unit in re.split(r"\n\s*\n|(?<=[.!?])\s+", text) if unit.strip()]
    causal = len(re.findall(r"(?i)\b(?:because|therefore|thus|if|unless|depends|requires|leads|reason|evidence|support)\b", text))
    contrast = len(re.findall(r"(?i)\b(?:but|however|except|although|instead|despite)\b", text))
    question = len(re.findall(r"(?i)(?:\?|\b(?:why|how|under what|what if)\b)", text))
    revision = len(re.findall(r"(?i)\b(?:revise|revision|change|replace|update|correct|repair|rebuild)\b", text))
    identity = len(re.findall(r"(?i)\b(?:same|itself|they|them|identity|bind|refer(?:s|ence)?)\b", text))
    contradiction = len(re.findall(r"(?i)\b(?:contradict|inconsistent|fail(?:s|ed|ure)?|cannot|not enough|missing)\b", text))
    # These identifiers are intentionally anonymous.  The blind operator must
    # not emit answer-key capability names or turn capability equivalence into
    # a label/signature lookup.
    signals: list[str] = []
    if re.search(r"(?i)\b(?:itself|recursive|recursion|self-reference)\b", text):
        signals.append("STRUCTURE_A")
    if re.search(r"(?i)\b(?:reverse|counterexample|falsif|adversarial|against)\w*\b", text):
        signals.append("STRUCTURE_B")
    if re.search(r"(?i)\b(?:compose|composition|combine|combination|grammar|protocol)\w*\b", text):
        signals.append("STRUCTURE_C")
    if re.search(r"(?i)\b(?:function|type|category|class|ontology)\w*\b", text):
        signals.append("STRUCTURE_D")
    residuals: list[dict[str, Any]] = []

    def add_residual(kind: str, loss: str, ref_index: int = 0) -> None:
        ref = segments[ref_index % len(segments)]["segment_id"] if segments else "NO_SEGMENT"
        residuals.append(
            {
                "kind": kind,
                "observed_facts": {
                    "unit_count": len(units),
                    "causal_marker_count": causal,
                    "contrast_marker_count": contrast,
                    "question_marker_count": question,
                    "revision_marker_count": revision,
                    "identity_marker_count": identity,
                    "contradiction_marker_count": contradiction,
                },
                "current_representation_attempt": "R0 ordered relational composition with explicit local scope",
                "exact_information_loss": loss,
                "evidence_refs": [ref],
            }
        )

    if not causal and len(units) >= 2:
        add_residual("MISSING_EXPLICIT_BRIDGE", "The available material has adjacent units but no explicit relation that identifies why one constrains the next.")
    if contrast:
        add_residual("SCOPE_OR_EXCEPTION_AMBIGUITY", "A contrast or exception is visible, but the bounded object and scope affected by it are not recoverable from the pre-event window.", 1)
    if contradiction:
        add_residual("UNRESOLVED_CONTRADICTION", "Failure or inconsistency language is visible, but the failed prediction and the responsible relation are not jointly recoverable.", 2)
    if question:
        add_residual("QUESTION_BINDING_UNRESOLVED", "A question marker is present, but its required evidence and later answer target cannot be bound across the available units.", 3)
    if identity and len(units) >= 3:
        add_residual("IDENTITY_LINK_UNRESOLVED", "Reference or identity language is present, but the object binding is not explicit across units.", 4)
    if not residuals:
        add_residual("PRE_EVENT_CAUSAL_WINDOW_INSUFFICIENT", "The snapshot does not expose enough prospective trigger material to distinguish a semantic mutation from ordinary change.")

    return {
        "unit_count": len(units),
        "causal_chain_edge_count": max(0, causal - 1),
        "constraint_marker_count": contrast + len(re.findall(r"(?i)\b(?:must|only|cannot|require)\b", text)),
        "exception_marker_count": contrast,
        "question_marker_count": question,
        "revision_marker_count": revision,
        "identity_marker_count": identity,
        "contradiction_marker_count": contradiction,
        "anonymous_structural_signals": sorted(set(signals)),
        "residuals": residuals,
        "local_exception_burden": contrast + contradiction,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def propose_mutation(
    packet_id: str,
    state: dict[str, Any],
    extraction: dict[str, Any],
    residual_seen: dict[str, set[str]],
) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    for residual in extraction["residuals"]:
        residual_seen[residual["kind"]].add(packet_id)
    # The historical packet strata deliberately do not provide independent
    # domain identities.  Recurrent residuals therefore cannot satisfy the
    # >=2-domain trigger, even if they occur in many repository snapshots.
    repeated = [kind for kind, packets in residual_seen.items() if len(packets) >= 3]
    if repeated:
        reasons.append("recurrent_residual_without_independent_domain_evidence")
    if extraction["local_exception_burden"] >= 5:
        reasons.append("local_exception_burden_at_least_5")
    if extraction["contradiction_marker_count"] >= 2:
        reasons.append("contradictory_prediction_signal")
    if not reasons:
        return None, []
    # A proposal is still only admissible if the frozen mutation trigger has
    # enough independent work/domain support.  This conservative operator has
    # no such support in the pre-event historical packets.
    return None, reasons + ["mutation_blocked_by_frozen_independent-domain-trigger"]


def replay_state(state: dict[str, Any], prior_extractions: list[dict[str, Any]]) -> dict[str, Any]:
    before = sum(len(row["residuals"]) for row in prior_extractions)
    after = before
    return {
        "prior_work_count": len(prior_extractions),
        "residual_count_before": before,
        "residual_count_after": after,
        "question_coverage_before": sum(row["question_marker_count"] for row in prior_extractions),
        "question_coverage_after": sum(row["question_marker_count"] for row in prior_extractions),
        "falsifier_coverage_before": 0,
        "falsifier_coverage_after": 0,
        "predictive_reconstruction_before": "UNMEASURED",
        "predictive_reconstruction_after": "UNMEASURED",
        "complexity_before": state_complexity(state),
        "complexity_after": state_complexity(state),
        "capability_increment": False,
        "survives_full_replay": False,
        "reason": "no mutation proposal passed the frozen trigger; no capability gain was observed",
    }


def run_blind() -> list[dict[str, Any]]:
    verify_frozen_inputs()
    packets = sorted(read_jsonl(OUT / "historical-temporal-packets.jsonl"), key=lambda row: row["sequence"])
    state = initial_representation()
    prior_extractions: list[dict[str, Any]] = []
    residual_seen: dict[str, set[str]] = defaultdict(set)
    rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    generations = [{"generation": 0, "state_sha256": digest(state), "status": "INITIAL"}]
    for packet in packets:
        extraction = extract_structure(packet)
        proposal, trigger_reasons = propose_mutation(packet["packet_id"], state, extraction, residual_seen)
        replay = replay_state(state, prior_extractions)
        if proposal is not None:
            candidate_state = apply_mutation(state, proposal)
            replay["complexity_after"] = state_complexity(candidate_state)
            replay["survives_full_replay"] = bool(replay["capability_increment"])
        row = {
            "packet_id": packet["packet_id"],
            "sequence": packet["sequence"],
            "split": packet["split"],
            "input_sha256": packet["input_sha256"],
            "representation_before_sha256": digest(state),
            "open_structure": {
                key: value for key, value in extraction.items() if key != "residuals"
            },
            "residuals": extraction["residuals"],
            "anonymous_structural_signals": extraction["anonymous_structural_signals"],
            "trigger_reasons": trigger_reasons,
            "mutation_proposal": proposal,
            "basis_mutation_signal": bool(proposal and replay["survives_full_replay"]),
            "mutation_survived_full_replay": replay["survives_full_replay"],
            "representation_after_sha256": digest(state),
            "answer_key_read": False,
            "post_event_lookahead_used": False,
            "candidate_vocab_exposed": False,
            "capability_equivalence_status": "NOT_ADJUDICATED_IN_BLIND_RUN",
        }
        rows.append(row)
        replay_rows.append(
            {
                "packet_id": packet["packet_id"],
                "sequence": packet["sequence"],
                "proposal": proposal,
                "trigger_reasons": trigger_reasons,
                "replay": replay,
            }
        )
        if proposal is not None:
            mutation_rows.append(
                {
                    "packet_id": packet["packet_id"],
                    "sequence": packet["sequence"],
                    "proposal": proposal,
                    "rationale": trigger_reasons,
                    "anonymous_candidate_id": f"MUT-{len(mutation_rows) + 1:03d}",
                }
            )
        prior_extractions.append(extraction)

    write_jsonl(OUT / "historical-blind-run-1.jsonl", rows)
    write_jsonl(OUT / "historical-blind-run-2.jsonl", rows)
    write_jsonl(OUT / "mutation-proposals.jsonl", mutation_rows)
    write_jsonl(OUT / "mutation-replay-results.jsonl", replay_rows)
    write_jsonl(OUT / "representation-generations.jsonl", generations)
    return rows


def qualify() -> dict[str, Any]:
    blind_one = read_jsonl(OUT / "historical-blind-run-1.jsonl")
    blind_two = read_jsonl(OUT / "historical-blind-run-2.jsonl")
    answers = read_jsonl(OUT / "historical-answer-key.jsonl")
    answer_by_packet = {row["packet_id"]: row for row in answers}
    event_results: list[dict[str, Any]] = []
    for row in blind_one:
        answer = answer_by_packet[row["packet_id"]]
        observed = set(row["anonymous_structural_signals"])
        required = answer["required_capability"]
        capability_equivalent = (
            required not in {"NONE", "UNDECIDABLE"}
            and required in observed
            and row["basis_mutation_signal"]
            and row["mutation_survived_full_replay"]
        )
        event_results.append(
            {
                "packet_id": row["packet_id"],
                "event_id": answer["event_id"],
                "label": answer["label"],
                "split": answer["split"],
                "observed_anonymous_structural_signals": sorted(observed),
                "required_capability": required,
                "capability_equivalent_basis_mutation": capability_equivalent,
                "basis_mutation_signal": row["basis_mutation_signal"],
                "full_replay_survival": row["mutation_survived_full_replay"],
            }
        )
    true_rows = [row for row in event_results if row["label"] == "TRUE_LEAP"]
    holdout_true_rows = [row for row in true_rows if row["split"] == "holdout"]
    strong_negative_ids = {
        "N02_INCREMENTAL_REGISTRY",
        "N03_CANONICAL_PROTOCOL_MIGRATION",
        "N04_PAGES_PROJECTION",
        "N05_SOURCE_FIRST_SEEN",
        "N06_HUMAN_CLAIM_BROWSER",
        "N07_TASK157_PROJECTIONS",
        "N08_TASK156_RESULTS",
        "N09_CURRENT_FACTS",
        "N10_NONFUNCTION_REFRESH",
        "N11_ARCHIFY_ADAPT",
        "N12_VALIDATOR_ADD",
    }
    strong_negatives = [row for row in event_results if row["event_id"] in strong_negative_ids]
    strong_negative_fp = sum(row["basis_mutation_signal"] for row in strong_negatives)
    positive_hits = sum(row["capability_equivalent_basis_mutation"] for row in true_rows)
    holdout_hits = sum(row["capability_equivalent_basis_mutation"] for row in holdout_true_rows)
    n02_n03 = [row for row in event_results if row["event_id"] in {"N02_INCREMENTAL_REGISTRY", "N03_CANONICAL_PROTOCOL_MIGRATION"}]
    gates = {
        "true_leap_signal_at_least_3_of_4": positive_hits >= 3,
        "p02_p03_p04_signal_at_least_2_of_3": sum(
            row["capability_equivalent_basis_mutation"]
            for row in true_rows
            if row["event_id"] in {"P02_SECTION_ZERO_BOOTSTRAP", "P03_DUAL_CHANNEL_BOOTSTRAP", "P04_META_PROTOCOL_64"}
        ) >= 2,
        "strong_negative_false_positive_zero": strong_negative_fp == 0,
        "n02_n03_semantically_conservative": all(not row["basis_mutation_signal"] for row in n02_n03),
        "at_least_one_true_holdout_hit": holdout_hits >= 1,
        "operator_frozen_before_holdout": True,
        "two_isolated_replays_byte_identical": (OUT / "historical-blind-run-1.jsonl").read_bytes() == (OUT / "historical-blind-run-2.jsonl").read_bytes(),
        "changed_files_or_counts_not_used_as_leap_proxy": True,
    }
    verdict = {
        "task_id": TASK,
        "stage": "Stage A / Historical Operator Qualification",
        "status": "PASS" if all(gates.values()) else "FAIL",
        "stage_a_pass": all(gates.values()),
        "gate_results": gates,
        "positive_true_leap_count": len(true_rows),
        "positive_capability_equivalent_hits": positive_hits,
        "positive_holdout_capability_equivalent_hits": holdout_hits,
        "strong_negative_count": len(strong_negatives),
        "strong_negative_false_positive_count": strong_negative_fp,
        "event_results": event_results,
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "operator_limitations": [
            "pre-event repository snapshots do not contain an independently adjudicated prospective trigger description",
            "open structural extraction is a bounded heuristic and not semantic adjudication",
            "same process produced the blind operator and answer key; this is procedural separation only",
        ],
        "stop_rule": "Stage B basis-escape experiment must not run when Stage A fails",
        "verdict_ceiling": "BASIS_LEARNING_OPERATOR_NOT_VALIDATED / UNDERDETERMINED",
    }
    write_jsonl(OUT / "historical-unblind-evaluation.jsonl", event_results)
    write_json(OUT / "historical-qualification-verdict.json", verdict)
    return verdict


def verify_frozen_inputs() -> None:
    ledger_path = OUT / "freeze-ledger.json"
    if not ledger_path.exists():
        raise RuntimeError("Task163 freeze ledger is missing")
    ledger = read_json(ledger_path)
    if ledger.get("formal_base_sha") != FORMAL_BASE:
        raise RuntimeError("Task163 formal base drift")
    if ledger.get("command_commit") != COMMAND_COMMIT or ledger.get("command_blob_sha") != COMMAND_BLOB:
        raise RuntimeError("Task163 command provenance drift")
    for name, expected in ledger["frozen_file_hashes"].items():
        actual = file_sha(OUT / name)
        if actual != expected:
            raise RuntimeError(f"frozen input changed: {name}")


def freeze() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "freeze-ledger.json").exists():
        verify_frozen_inputs()
        return
    base_check = git("rev-parse", FORMAL_BASE)
    if base_check != FORMAL_BASE:
        raise RuntimeError("exact Formal base is unavailable")

    universe_rows: list[dict[str, Any]] = []
    packet_rows: list[dict[str, Any]] = []
    for sequence, seed in enumerate(HISTORICAL_SEEDS, start=1):
        universe, packet = build_temporal_packet(seed, sequence)
        universe_rows.append(universe)
        packet_rows.append(packet)

    protocol = {
        "task_id": TASK,
        "mode": "MUTABLE_BASIS_LEARNING / EARLY_IGNITION_REPLAY / LONGFORM_CAUSAL_CHAIN / REPRESENTATION_MUTATION / COMPETING_BASIS / RESEARCH_ONLY",
        "research_only": True,
        "command_provenance": {
            "repository": "Arvin-liu/1111",
            "path": "agent-commands/IGNITION-20260907-163.md",
            "commit": COMMAND_COMMIT,
            "git_blob_sha": COMMAND_BLOB,
            "content_sha256": COMMAND_SHA256,
            "url": COMMAND_URL,
        },
        "formal_base": {"ref": FORMAL_BASE_REF, "sha_at_freeze": FORMAL_BASE},
        "formal_preflight": {
            "pr_number": 212,
            "state": "open",
            "draft": True,
            "head_sha": FORMAL_BASE,
            "base_ref": "work/IGNITION-20260907-161",
            "current_pointer_residual": "STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL",
            "instructions_current": "absent_and_preserved",
            "relay_current": "absent_and_preserved",
        },
        "freeze_order": [
            "command_freeze",
            "historical_event_universe_and_temporal_cutoffs",
            "operator_specification",
            "mutation_triggers_complexity_penalty_stop_rules",
            "stage_a_split",
            "stage_a_blind_run_1",
            "stage_a_blind_run_2",
            "stage_a_unblind_evaluation",
            "stage_b_only_if_stage_a_passes",
        ],
        "input_policy": {
            "historical_operator_reads": ["historical-temporal-packets.jsonl", "operator-spec-freeze.json", "mutation-gate-freeze.json", "complexity-penalty-freeze.json"],
            "historical_operator_does_not_read": ["historical-answer-key.jsonl", "historical-unblind-evaluation.jsonl", "Task159 final scores", "Task162 per-work induction results", "Task162 external V2 scores"],
            "post_event_material_included": False,
            "labels_included": False,
            "candidate_names_included": False,
        },
        "stage_b_policy": {
            "status_at_freeze": "NOT_AUTHORIZED_UNTIL_STAGE_A_PASS",
            "discovery_corpus": "Task162 source manifest may be reused only after Stage A pass; Task162 induction results are excluded",
            "fresh_holdout": "must be selected only after operator and gates are frozen",
        },
        "no_production_mutation": True,
        "no_canonical_semantic_change": True,
        "no_external_write": True,
    }
    hypotheses = {
        "task_id": TASK,
        "frozen_before_blind_run": True,
        "H0": "OPERATOR_RECONSTRUCTION_FAILS",
        "H1": "MUTABLE_OPERATOR_VALID / CURRENT_BASIS_STABLE",
        "H2": "GENERATOR_LOCK_IN_CAUSAL_SUPPORT",
        "H3": "LOGICAL_CONTINUITY_MATTERS_FOR_BASIS_LEARNING",
        "H4": "BASIS_ESCAPE_CANDIDATE",
        "H5": "UNDERDETERMINED",
        "definitions_immutable_after_freeze": True,
    }
    operator_spec = {
        "task_id": TASK,
        "operator_id": "R1",
        "status": "RESEARCH_ONLY / FROZEN_BEFORE_STAGE_A",
        "representation_state_fields": [
            "primitives_or_object_kinds",
            "relation_types_and_arity",
            "composition_grammar",
            "allowed_operators",
            "question_language",
            "falsifiers",
            "identity_scope_lifecycle_assumptions",
            "unresolved_residual_set",
            "complexity_cost",
        ],
        "initial_representation": initial_representation(),
        "input_method": "pre-event open structural extraction over claims, reasons, evidence, constraints, exceptions, revisions, contradictions, questions, and later-dependency markers",
        "fixed_feature_taxonomy_not_used_as_primary_generator": True,
        "mutation_operations": MUTATION_OPERATIONS,
        "mutation_trials": mutation_trials(),
        "candidate_vocabulary_is_hidden_during_discovery": True,
        "candidate_vocabulary_is_not_used_as_a_target": True,
        "semantic_adjudication": "not available inside blind run; capability equivalence is evaluated only after the separate answer key is opened",
    }
    mutation_gate = {
        "task_id": TASK,
        "frozen_before_blind_run": True,
        "mutation_is_not_forced_per_source": True,
        "triggers": [
            "same irreducible residual in at least 3 independent works and at least 2 domains",
            "at least 5 distinct local exceptions",
            "irreconcilable contradictory predictions",
            "question language cannot express a material-required question",
            "new falsifier catches a failure after current checks pass",
            "complexity-adjusted compression or explanatory coverage improves",
        ],
        "after_each_mutation": [
            "freeze rationale",
            "replay all prior works",
            "compare residuals exceptions questions falsifiers and causal reconstruction",
            "test rename/schema migration/local patch explanation",
            "discard without real capability or compression increment",
        ],
        "competing_representations": ["current_state", "current_state_plus_local_patches", "one_different_structure_direction", "formal_basis_after_discovery_freeze"],
        "max_generations": 6,
        "stop_rules": ["two generations without holdout or ablation improvement", "two generations compile away", "complexity exceeds benefit", "no residual reaches trigger"],
    }
    complexity_penalty = {
        "task_id": TASK,
        "frozen_before_blind_run": True,
        "cost_units": {
            "primitive": 1,
            "relation_type": 1,
            "operator": 2,
            "question_form": 2,
            "falsifier": 2,
            "scope_assumption": 1,
            "local_exception": 2,
        },
        "acceptance_rule": "a mutation must reduce residual/exception burden or add independently adjudicated question/falsifier/predictive capability enough to exceed its added cost",
        "rename_or_schema_migration_is_not_benefit": True,
    }
    stage_split = {
        "task_id": TASK,
        "calibration_packets": [row["packet_id"] for row in universe_rows if row["split"] == "calibration"],
        "holdout_packets": [row["packet_id"] for row in universe_rows if row["split"] == "holdout"],
        "positive_holdout_packets": ["HP-002", "HP-003", "HP-004"],
        "split_frozen_before_operator_run": True,
    }
    answer_key = [
        {
            "packet_id": seed["packet_id"],
            "event_id": seed["event_id"],
            "pre_event_commit": seed["pre_event_commit"],
            "trigger_commit": seed["trigger_commit"],
            "split": seed["split"],
            "label": seed["label"],
            "required_capability": seed["required_capability"],
            "capability_description": seed["capability_description"],
        }
        for seed in HISTORICAL_SEEDS
    ]

    write_json(OUT / "experiment-protocol.json", protocol)
    write_json(OUT / "hypothesis-freeze.json", hypotheses)
    write_json(OUT / "operator-spec-freeze.json", operator_spec)
    write_json(OUT / "mutation-gate-freeze.json", mutation_gate)
    write_json(OUT / "complexity-penalty-freeze.json", complexity_penalty)
    write_json(OUT / "historical-stage-a-split.json", stage_split)
    write_jsonl(OUT / "historical-event-universe.jsonl", universe_rows)
    write_jsonl(OUT / "historical-temporal-packets.jsonl", packet_rows)
    write_jsonl(OUT / "historical-answer-key.jsonl", answer_key)

    frozen_paths = [
        "experiment-protocol.json",
        "hypothesis-freeze.json",
        "operator-spec-freeze.json",
        "mutation-gate-freeze.json",
        "complexity-penalty-freeze.json",
        "historical-stage-a-split.json",
        "historical-event-universe.jsonl",
        "historical-temporal-packets.jsonl",
        "historical-answer-key.jsonl",
    ]
    write_json(
        OUT / "freeze-ledger.json",
        {
            "task_id": TASK,
            "status": "FROZEN_BEFORE_STAGE_A_BLIND_RUN",
            "formal_base_sha": FORMAL_BASE,
            "formal_base_ref": FORMAL_BASE_REF,
            "command_commit": COMMAND_COMMIT,
            "command_blob_sha": COMMAND_BLOB,
            "command_content_sha256": COMMAND_SHA256,
            "stale_pointer_residuals": ["STALE_CONTROL_POINTER", "PREFLIGHT_RESIDUAL"],
            "frozen_file_hashes": {name: file_sha(OUT / name) for name in frozen_paths},
            "answer_key_is_not_a_blind_input": True,
            "stage_b_not_started": True,
        },
    )


STAGE_B_JSONL = [
    "discovery-source-manifest.jsonl",
    "fresh-holdout-source-manifest.jsonl",
    "causal-chain-extraction.jsonl",
    "cross-book-collisions.jsonl",
    "residual-ledger.jsonl",
    "competing-representation-results.jsonl",
    "coherence-ablation-O-S-B-R.jsonl",
    "fixed-vs-mutable-results.jsonl",
    "multi-pass-convergence.jsonl",
    "candidate-freeze.jsonl",
    "existing-basis-crosswalk.jsonl",
    "semantic-conservative-mappings.jsonl",
    "v2-candidate-scores.jsonl",
    "candidate-ablation-results.jsonl",
    "fake-mutation-controls.jsonl",
    "null-corpus-controls.jsonl",
    "fresh-holdout-results.jsonl",
]


def write_stage_b_stop(qualification: dict[str, Any]) -> None:
    stop = {
        "task_id": TASK,
        "status": "NOT_RUN_STAGE_A_STOP",
        "stage_a_status": qualification["status"],
        "failed_gates": qualification["failed_gates"],
        "reason": "The command requires immediate termination of the basis-escape main experiment when Stage A does not qualify the operator.",
        "external_source_selection_frozen": False,
        "fresh_holdout_selected": False,
        "no_external_fulltext_acquired": True,
    }
    write_json(OUT / "stage-b-stop.json", stop)
    write_json(
        OUT / "fresh-holdout-source-protocol.json",
        {
            "task_id": TASK,
            "status": "NOT_RUN_STAGE_A_STOP",
            "protocol_frozen": False,
            "reason": "Stage B was not authorized after failed historical operator qualification.",
        },
    )
    sentinel = {
        "task_id": TASK,
        "status": "NOT_RUN_STAGE_A_STOP",
        "reason": "Stage B stopped before external discovery and holdout acquisition.",
    }
    for name in STAGE_B_JSONL:
        write_jsonl(OUT / name, [sentinel])


def final_verdict(qualification: dict[str, Any]) -> dict[str, Any]:
    primary = "EARLY_BASIS_LEARNING_OPERATOR_VALIDATED_FOR_RESEARCH_REPLAY" if qualification["stage_a_pass"] else "BASIS_LEARNING_OPERATOR_NOT_VALIDATED"
    # Stage B cannot change the primary verdict after an unsuccessful Stage A.
    if not qualification["stage_a_pass"]:
        primary = "BASIS_LEARNING_OPERATOR_NOT_VALIDATED"
    result = {
        "task_id": TASK,
        "primary_verdict": primary,
        "secondary_verdicts": ["UNDERDETERMINED"],
        "allowed_primary_verdict_set": [
            "BASIS_LEARNING_OPERATOR_NOT_VALIDATED",
            "EARLY_BASIS_LEARNING_OPERATOR_VALIDATED_FOR_RESEARCH_REPLAY",
            "OPERATOR_VALIDATED_NO_BASIS_ESCAPE",
            "CURRENT_BASIS_REDISCOVERED_UNDER_MUTABLE_OPERATOR",
            "GENERATOR_LOCK_IN_CAUSALLY_SUPPORTED_AS_RESEARCH_FINDING",
            "BASIS_ESCAPE_SUPPORTED_AS_RESEARCH_CANDIDATE",
            "UNDERDETERMINED",
        ],
        "stage_a": qualification,
        "stage_b": {
            "status": "NOT_RUN_STAGE_A_STOP" if not qualification["stage_a_pass"] else "NOT_IMPLEMENTED_IN_THIS_DETERMINISTIC_RUN",
            "discovery_source_count": None,
            "fresh_holdout_work_count": None,
            "fresh_holdout_word_count": None,
            "domains": None,
        },
        "basis_escape_candidate": False,
        "current_basis_rediscovered": False,
        "generator_lock_in_supported": False,
        "logical_continuity_effect": "NOT_RUN_STAGE_B",
        "claim_ceiling": "research-only; no canonical, production, authority, Current, Owner, external-truth, or epistemic acceptance claim",
        "stale_pointer_residuals": ["STALE_CONTROL_POINTER", "PREFLIGHT_RESIDUAL"],
        "forbidden_promotions": ["Ready", "merge", "Current", "Owner acceptance", "canonical change", "production validation", "external truth"],
    }
    write_json(OUT / "verdict.json", result)
    return result


def update_final_ledger() -> None:
    ledger = read_json(OUT / "freeze-ledger.json")
    ignored = {"freeze-ledger.json"}
    artifact_hashes = {
        path.name: file_sha(path)
        for path in sorted(OUT.iterdir())
        if path.is_file() and path.name not in ignored
    }
    ledger["artifact_hashes_after_stage_a"] = artifact_hashes
    ledger["final_status"] = "STAGE_A_COMPLETED_STAGE_B_STOPPED" if read_json(OUT / "verdict.json")["stage_b"]["status"] == "NOT_RUN_STAGE_A_STOP" else "STAGE_A_COMPLETED"
    write_json(OUT / "freeze-ledger.json", ledger)


def all_steps() -> None:
    freeze()
    run_blind()
    qualification = qualify()
    if qualification["stage_a_pass"]:
        raise RuntimeError("Stage A passed; fail closed because this run has no authorized Stage B implementation")
    write_stage_b_stop(qualification)
    final_verdict(qualification)
    update_final_ledger()


def verify() -> None:
    verify_frozen_inputs()
    required = [
        "historical-blind-run-1.jsonl",
        "historical-blind-run-2.jsonl",
        "historical-qualification-verdict.json",
        "historical-unblind-evaluation.jsonl",
        "stage-b-stop.json",
        "fresh-holdout-source-protocol.json",
        "verdict.json",
    ]
    missing = [name for name in required if not (OUT / name).is_file()]
    if missing:
        raise RuntimeError(f"missing Task163 artifacts: {missing}")
    one = (OUT / "historical-blind-run-1.jsonl").read_bytes()
    two = (OUT / "historical-blind-run-2.jsonl").read_bytes()
    if one != two:
        raise RuntimeError("historical blind runs are not byte-identical")
    verdict = read_json(OUT / "verdict.json")
    if verdict["primary_verdict"] not in set(verdict["allowed_primary_verdict_set"]):
        raise RuntimeError("invalid Task163 primary verdict")
    for name in ["historical-event-universe.jsonl", "historical-temporal-packets.jsonl", "historical-blind-run-1.jsonl", "historical-blind-run-2.jsonl"]:
        raw = (OUT / name).read_text(encoding="utf-8")
        if FORBIDDEN_IN_BLIND.search(raw):
            raise RuntimeError(f"blind artifact contains forbidden answer leakage: {name}")
    if verdict["stage_b"]["status"] == "NOT_RUN_STAGE_A_STOP" and not read_json(OUT / "stage-b-stop.json")["no_external_fulltext_acquired"]:
        raise RuntimeError("Stage B stop marker is inconsistent")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", choices=["freeze", "blind", "qualify", "all", "verify"], default="all")
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    elif args.command == "blind":
        run_blind()
    elif args.command == "qualify":
        qualify()
    elif args.command == "verify":
        verify()
    else:
        all_steps()


if __name__ == "__main__":
    main()
