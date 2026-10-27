"""Integration adapters (Checkpoint C / Task #636).

Non-duplicative *reference* layer. The Research OS is a cross-layer controller,
not a truth authority, executor, gate, information-gain signal or map owner. It
references the seven existing components by their canonical paths and maps its
own concepts onto the existing vocabulary:

  - L0-L6 truth spine            -> ARCHITECTURE.md + obligation-class layer ownership
  - Function OS (N1-N9)          -> function-os-candidate/v0.2 (executor target)
  - Q12 Charter Gate + M0/M1     -> docs/governance/charter-system-r1.*
  - Q13 IterationDelta           -> schemas/architecture/iteration-delta.schema.json
  - language-thought logic       -> docs/language-thought (source normalization only)
  - publication claim ceiling    -> docs/foundation/claim-governance-... + claim_ceiling_gate
  - Q14 system map               -> data/architecture/interactive-system-map.json

Design rule: the adapters *read and reference* the existing contracts; they never
re-implement Q12, Q13, Function OS, the claim-ceiling gate, the language-thought
logic or Q14. If a referenced contract is moved or changed incompatibly, the
adapters fail loudly (``verify_integration_targets`` / presence checks) instead
of silently drifting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import kernel
from . import registries as R

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Canonical integration-target locators (read-only references).
# ---------------------------------------------------------------------------
FUNCTION_OS_V02_DIR = REPO_ROOT / "function-os-candidate" / "v0.2"
FUNCTION_OS_SCHEMA_DIR = FUNCTION_OS_V02_DIR / "schemas"
CHARTER_SYSTEM_SCHEMA = REPO_ROOT / "docs" / "governance" / "charter-system-r1.schema.json"
CHARTER_SYSTEM_REGISTRY = REPO_ROOT / "docs" / "governance" / "charter-system-registry.json"
CHARTER_SYSTEM_DOC = REPO_ROOT / "docs" / "governance" / "charter-system-r1.md"
ITERATION_DELTA_SCHEMA = REPO_ROOT / "schemas" / "architecture" / "iteration-delta.schema.json"
SYSTEM_MAP_DATA = REPO_ROOT / "data" / "architecture" / "interactive-system-map.json"
SYSTEM_MAP_LAYOUT_SCHEMA = REPO_ROOT / "schemas" / "architecture" / "interactive-system-map-layout.schema.json"
SYSTEM_MAP_GENERATOR = REPO_ROOT / "tools" / "generate_interactive_system_map.py"
LANGUAGE_THOUGHT_DIR = REPO_ROOT / "docs" / "language-thought"
LANGUAGE_THOUGHT_ZH_PROFILE = LANGUAGE_THOUGHT_DIR / "profiles" / "zh-hans.md"
CLAIM_GOVERNANCE_DOC = REPO_ROOT / "docs" / "foundation" / "claim-governance-and-function-identity.md"
CANDIDATE_PORTFOLIO_SCHEMA = REPO_ROOT / "evidence-program" / "schemas" / "candidate-portfolio.schema.json"
ARCHITECTURE_DOC = REPO_ROOT / "ARCHITECTURE.md"

# L0-L6 truth spine (reference only; the spine holds truth, the OS does not).
LAYER_SPINE: dict[str, str] = {
    "L0": "Source & evidence — provenance, source identities, access levels",
    "L1": "Controlled semantic propositions — disambiguated claim language",
    "L2": "Formal objects — constructs, outcomes, denominators",
    "L3": "Logical argument — argument structure",
    "L4": "Mathematical model & proof — models, recomputation targets",
    "L5": "Validation & validity — verification, validity checks",
    "L6": "Interpretation, application, publication — output + claim-ceiling bound",
}

# Function OS N1-N9 node registry (reference; executor target, not re-implemented).
FUNCTION_OS_NODES: dict[str, dict] = {
    "N1": {"name": "FunctionSpec", "role": "安全表达式与语义检查", "schema": "n1-functionspec-schema.json"},
    "N2": {"name": "Representation", "role": "编码为机器可读中间表示并生成哈希", "schema": "n2-representation-schema.json"},
    "N3": {"name": "Compiler", "role": "编译为可包装符号 payload", "schema": "n3-compiler-schema.json"},
    "N4": {"name": "Artifact Packager", "role": "生成带版本/哈希的 artifact", "schema": "n4-artifact-schema.json"},
    "N5": {"name": "Interpreter", "role": "用 artifact 与输入执行函数", "schema": "n5-interpreter-schema.json"},
    "N6": {"name": "Execution Trace", "role": "记录执行事件与 trace hash", "schema": "n6-trace-schema.json"},
    "N7": {"name": "Validator / Feedback", "role": "一致性验证与修订反馈", "schema": "n7-validator-schema.json"},
    "N8": {"name": "Composer / Router", "role": "生成顺序执行计划（非自动发现/调度）", "schema": "n8-router-schema.json"},
    "N9": {"name": "Registry / revision / rollback", "role": "登记通过边界的修订与回滚审计链", "schema": "n9-registry-schema.json"},
}

# Map a Research OS action (24-vocab) to the Function OS node that would *execute*
# it. This is a conceptual routing reference, not an execution re-implementation.
ACTION_TO_FUNCTION_OS_NODE: dict[str, str] = {
    "SEARCH_PRIMARY_SOURCE": "N1",
    "FETCH_FULL_TEXT": "N1",
    "LOCATE_RAW_DATA": "N1",
    "LOCATE_ANALYSIS_CODE": "N1",
    "READ_METHODS": "N1",
    "READ_SUPPLEMENT": "N1",
    "RECOMPUTE_RESULT": "N5",
    "REPRODUCE_ANALYSIS": "N5",
    "BUILD_DEFINITION_CROSSWALK": "N2",
    "COMPARE_OUTCOMES_OR_DENOMINATORS": "N2",
    "COMPARE_POPULATIONS_OR_JURISDICTIONS": "N2",
    "CHECK_SOURCE_DEPENDENCE": "N8",
    "SEEK_REPLICATION": "N8",
    "SEEK_NULL_OR_CONTRADICTORY_RESULT": "N8",
    "TEST_ALTERNATIVE_MECHANISM": "N5",
    "RUN_ADVERSARIAL_REVIEW": "N8",
    "SEEK_METHODOLOGICAL_CRITIQUE": "N8",
    "FREEZE_OR_NARROW_QUESTION": "N1",
    "DOWNGRADE_CLAIM": "N8",
    "PAUSE_AND_CHECKPOINT": "N9",
    "BRANCH_QUESTION": "N8",
    "STOP_WITH_INSUFFICIENT_EVIDENCE": "N9",
    "ESCALATE_TO_GPT_OWNER": "N9",
    "REOPENED": "N9",
}

# Q13 IterationDelta delta_status -> Research OS stop/continue signal consumed by
# the deterministic diagnosis engine (diagnosis.py). Q13's richer enum is mapped
# onto the engine's two loop signals; we do not re-derive the loop logic here.
DELTA_STATUS_TO_OS_SIGNAL: dict[str, str] = {
    "INFORMATION_GAIN": "CONTINUE",
    "NO_INFORMATION_GAIN": "NO_INFORMATION_GAIN",
    "ATTRACTOR_LOOP": "ATTRACTOR_LOOP_RISK",
    "RUMINATION_RISK": "ATTRACTOR_LOOP_RISK",
    "PARTIAL_DELTA": "CONTINUE",
}

# Foundation claim-ceiling gate permitted levels (claim-governance doc §6).
PUBLICATION_CLAIM_CEILINGS = R.CLAIM_CEILING_ENUM  # SPECULATIVE..BOUNDED_STRONG, NOT_ASSERTED


# ---------------------------------------------------------------------------
# Presence / consistency verification (used by tests and self-audit).
# ---------------------------------------------------------------------------
def integration_targets() -> dict[str, str]:
    """Return the canonical locator map: target name -> absolute path string."""
    return {
        "architecture_doc": str(ARCHITECTURE_DOC),
        "function_os_v02": str(FUNCTION_OS_V02_DIR),
        "function_os_schemas": str(FUNCTION_OS_SCHEMA_DIR),
        "charter_system_schema": str(CHARTER_SYSTEM_SCHEMA),
        "charter_system_registry": str(CHARTER_SYSTEM_REGISTRY),
        "charter_system_doc": str(CHARTER_SYSTEM_DOC),
        "iteration_delta_schema": str(ITERATION_DELTA_SCHEMA),
        "system_map_data": str(SYSTEM_MAP_DATA),
        "system_map_layout_schema": str(SYSTEM_MAP_LAYOUT_SCHEMA),
        "system_map_generator": str(SYSTEM_MAP_GENERATOR),
        "language_thought_dir": str(LANGUAGE_THOUGHT_DIR),
        "claim_governance_doc": str(CLAIM_GOVERNANCE_DOC),
        "candidate_portfolio_schema": str(CANDIDATE_PORTFOLIO_SCHEMA),
    }


def verify_integration_targets() -> dict[str, bool]:
    """Report which referenced integration targets are present on disk.

    A ``False`` here means a referenced contract moved and the adapter must be
    updated — never silently ignore it.
    """
    out: dict[str, bool] = {}
    for name, path in integration_targets().items():
        out[name] = Path(path).exists()
    # Function OS N1-N9 schemas must all be present.
    for node, meta in FUNCTION_OS_NODES.items():
        out[f"function_os_{node}_schema"] = (FUNCTION_OS_SCHEMA_DIR / meta["schema"]).exists()
    return out


# ---------------------------------------------------------------------------
# L0-L6 layer adapter (read-through; never re-owns the spine).
# ---------------------------------------------------------------------------
def layer_spine() -> dict[str, str]:
    return dict(LAYER_SPINE)


def layer_for_obligation_class(klass: str) -> str:
    """Reference the layer that owns a given obligation class's evidence.

    The 12 Research OS obligation classes all resolve onto the L0-L6 spine via
    their evidence type; this is a stable cross-reference, not a redefinition of
    L0-L6. Heuristic mapping by class semantics (source -> L0, compute -> L4,
    definitions -> L2, review -> L5/L6, etc.).
    """
    R.assert_obligation_class(klass)
    source_like = {"PRIMARY_SOURCE", "FULL_TEXT_OR_METHODS_OR_SUPPLEMENT", "DATA_OR_TABLE_ACCESS", "SOURCE_INDEPENDENCE_CHECK"}
    compute_like = {"NUMERIC_RECOMPUTATION", "REPLICATION_NULL_CONTRADICTORY"}
    definition_like = {"CONSTRUCT_AND_OUTCOME_DEFINITION", "POPULATION_JURISDICTION_TIME_SCOPE"}
    causal_like = {"CAUSAL_IDENTIFICATION", "MECHANISM_ALTERNATIVE"}
    review_like = {"ADVERSE_EFFECT_COST_HARMED", "EXTERNAL_HUMAN_OR_DOMAIN_REVIEW"}
    if klass in source_like:
        return "L0"
    if klass in compute_like:
        return "L4"
    if klass in definition_like:
        return "L2"
    if klass in causal_like:
        return "L3"
    if klass in review_like:
        return "L5"
    return "L0"


# ---------------------------------------------------------------------------
# Function OS executor adapter (reference only).
# ---------------------------------------------------------------------------
def function_os_nodes() -> dict[str, dict]:
    """Return the N1-N9 node registry as a reference map (does not execute)."""
    return dict(FUNCTION_OS_NODES)


def function_os_node_for_action(action_code: str) -> str | None:
    """Map a Research OS dispatch action to the Function OS node that executes it."""
    R.assert_action(action_code)
    return ACTION_TO_FUNCTION_OS_NODE.get(action_code)


def function_os_executor_reference(action_code: str) -> dict:
    """Build a read-only reference record describing how a dispatch reaches Function OS.

    The OS sends a bounded dispatch spec (see executor_contract); Function OS
    executes it. This adapter only records *which* node would act — it does not
    run N1-N9 or decide whether the action is worth doing (that is Q12's job).
    """
    R.assert_action(action_code)
    node = function_os_node_for_action(action_code)
    return {
        "mechanism": "Function OS (executor target)",
        "target_dir": str(FUNCTION_OS_V02_DIR),
        "target_node": node,
        "target_node_name": FUNCTION_OS_NODES.get(node, {}).get("name") if node else None,
        "execute_action": action_code,
        "owner": "Function OS v0.2 candidate (function-os-candidate/v0.2)",
        "note": "Function OS executes the bounded action; Research OS decides whether to dispatch it.",
    }


# ---------------------------------------------------------------------------
# Q12 Charter Gate + M0/M1 adapter (route-through; never re-implements the gate).
# ---------------------------------------------------------------------------
def charter_gate_reference(action_code: str) -> dict:
    """Record that a state-changing dispatch must pass the Q12 Charter Gate.

    The gate itself lives in the Charter System R1; Research OS only records the
    routing obligation and the canonical schema/registry it must satisfy.
    """
    R.assert_action(action_code)
    return {
        "mechanism": "Q12 / Charter Gate",
        "schema": str(CHARTER_SYSTEM_SCHEMA),
        "registry": str(CHARTER_SYSTEM_REGISTRY),
        "doc": str(CHARTER_SYSTEM_DOC),
        "action": action_code,
        "must_pass_before_dispatch": True,
        "owner": "Charter System R1 (docs/governance/charter-system-r1.md)",
        "note": "Research OS routes dispatch through Charter Gate; it does not re-implement the gate.",
    }


def record_m0_m1(
    ep: dict,
    action_code: str,
    m0_pre_action_sketch: str | None = None,
    m1_post_action_adjudication: str | None = None,
    actor: str = "adapter",
) -> dict:
    """Additively record Q12 M0 (pre-action sketch) / M1 (post-action adjudication).

    This is metadata stored in the episode provenance; it references Q12's
    effectual-action plane without re-implementing it.
    """
    R.assert_action(action_code)
    rec = {
        "action": action_code,
        "m0_pre_action_sketch": m0_pre_action_sketch,
        "m1_post_action_adjudication": m1_post_action_adjudication,
    }
    ep.setdefault("provenance", {}).setdefault("q12_m0_m1", []).append(rec)
    kernel._append_event(ep, "adapter_q12_m0_m1", rec, actor=actor)
    return ep


# ---------------------------------------------------------------------------
# Q13 IterationDelta adapter (consume the canonical information-gain signal).
# ---------------------------------------------------------------------------
def load_iteration_delta_schema() -> dict:
    """Load the canonical Q13 IterationDelta schema (read-only)."""
    with open(ITERATION_DELTA_SCHEMA, "r", encoding="utf-8") as fh:
        return json.load(fh)


def map_delta_status_to_os_signal(delta_status: str) -> str:
    """Map a Q13 IterationDelta delta_status onto a Research OS stop/continue signal.

    The deterministic diagnosis engine (diagnosis.py) already emits
    NO_INFORMATION_GAIN / ATTRACTOR_LOOP_RISK from the episode's own information
    delta; this adapter keeps the Q13 vocabulary as the canonical source and
    translates it so the two stay consistent.
    """
    schema = load_iteration_delta_schema()
    allowed = set(schema["properties"]["delta_status"]["enum"])
    if delta_status not in allowed:
        raise ValueError(f"unknown Q13 delta_status: {delta_status}")
    return DELTA_STATUS_TO_OS_SIGNAL[delta_status]


def consume_iteration_delta(ep: dict, delta: dict, actor: str = "adapter") -> dict:
    """Record a Q13 IterationDelta and the resulting OS signal into the episode.

    The delta is stored verbatim (canonical Q13 object); only its mapping is
    added. Research OS honors the stop/branch/downgrade response; it does not
    re-derive the information-gain signal.
    """
    signal = map_delta_status_to_os_signal(delta.get("delta_status"))
    # kernel.new_episode initializes information_delta to None, so setdefault
    # would silently drop the delta; assign explicitly (mirrors
    # kernel.append_information_delta).
    ep["information_delta"] = delta
    ep.setdefault("provenance", {}).setdefault("q13_iteration_delta_signal", []).append(
        {"delta_id": delta.get("id"), "delta_status": delta.get("delta_status"), "os_signal": signal}
    )
    kernel._append_event(
        ep, "adapter_q13_iteration_delta", {"delta_id": delta.get("id"), "os_signal": signal}, actor=actor
    )
    return ep


# ---------------------------------------------------------------------------
# language-thought logic adapter (source-language normalization only).
# ---------------------------------------------------------------------------
def language_thought_reference() -> dict:
    return {
        "mechanism": "language-thought logic plane",
        "dir": str(LANGUAGE_THOUGHT_DIR),
        "zh_profile": str(LANGUAGE_THOUGHT_ZH_PROFILE),
        "use": "source-language normalization adapter only; never a reasoning substitute",
        "owner": "docs/language-thought",
    }


def normalize_source_language(
    ep: dict, source_ref: str, from_lang: str | None = None, to_lang: str = "zh-hans", actor: str = "adapter"
) -> dict:
    """Record a source-language normalization reference for a source.

    The normalization logic itself stays in the language-thought plane; the OS
    only records that a profile was applied so provenance is auditable.
    """
    rec = {"source_ref": source_ref, "from_lang": from_lang, "to_lang": to_lang, "profile": str(LANGUAGE_THOUGHT_ZH_PROFILE)}
    ep.setdefault("provenance", {}).setdefault("language_thought_normalization", []).append(rec)
    kernel._append_event(ep, "adapter_language_thought", rec, actor=actor)
    return ep


# ---------------------------------------------------------------------------
# publication claim-ceiling adapter (reference the Foundation claim_ceiling_gate).
# ---------------------------------------------------------------------------
def publication_claim_ceiling_reference() -> dict:
    """Reference the Foundation claim-ceiling gate (claim-governance doc §6)."""
    return {
        "mechanism": "Foundation claim_ceiling_gate",
        "doc": str(CLAIM_GOVERNANCE_DOC),
        "candidate_portfolio_schema": str(CANDIDATE_PORTFOLIO_SCHEMA),
        "permitted_levels": list(PUBLICATION_CLAIM_CEILINGS),
        "owner": "docs/foundation/claim-governance-and-function-identity.md",
        "note": "Research OS candidate packet must respect the Foundation claim ceiling.",
    }


def assert_ceiling_within_publication_bound(ep: dict, claim_id: str) -> None:
    """Assert a candidate claim ceiling is within the Foundation-permitted levels.

    The pack's max claim ceiling (registries) and the Foundation gate together
    bound the ceiling; the OS never raises it on its own.
    """
    claim = next((c for c in ep.get("candidate_claims", []) if c["claim_id"] == claim_id), None)
    if claim is None:
        raise KeyError(f"claim_id not found: {claim_id}")
    ceiling = claim["claim_ceiling"]
    if ceiling not in PUBLICATION_CLAIM_CEILINGS:
        raise ValueError(f"claim {claim_id} ceiling {ceiling} outside Foundation-permitted levels")
    pack = R.PACK_BY_CODE.get(ep.get("strategy_pack"), {})
    max_ceiling = pack.get("max_claim_ceiling")
    rank = {c: i for i, c in enumerate(PUBLICATION_CLAIM_CEILINGS)}
    if max_ceiling and rank[ceiling] > rank[max_ceiling]:
        raise ValueError(
            f"claim {claim_id} ceiling {ceiling} exceeds pack max {max_ceiling}"
        )


# ---------------------------------------------------------------------------
# Q14 system map adapter (topology reference; never owns the map).
# ---------------------------------------------------------------------------
def system_map_reference() -> dict:
    return {
        "mechanism": "Q14 ignition map atlas",
        "data": str(SYSTEM_MAP_DATA),
        "layout_schema": str(SYSTEM_MAP_LAYOUT_SCHEMA),
        "generator": str(SYSTEM_MAP_GENERATOR),
        "owner": "data/architecture/interactive-system-map.json",
        "note": "Research OS references the current map for component registration; it does not own the map.",
    }


def register_component_reference(ep: dict, component_id: str, layer: str | None = None, actor: str = "adapter") -> dict:
    """Additively note a component registration against the Q14 topology reference."""
    rec = {"component_id": component_id, "layer": layer, "map_data": str(SYSTEM_MAP_DATA)}
    ep.setdefault("provenance", {}).setdefault("q14_component_registration", []).append(rec)
    kernel._append_event(ep, "adapter_q14_registration", rec, actor=actor)
    return ep
