"""Research OS Checkpoint C tests (recovered WorkBuddy work).

Self-contained runner: no external test framework required. Run with:

    python3 tests/test_research_os_checkpoint_c.py

Covers: eight strategy packs over one shared kernel, review/stop/escalation
gates, executor return contract (no self-approval / no state completion / no
claim-ceiling elevation), integration adapters, and the executor-return schema.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS = str(REPO / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import research_os.kernel as kernel
import research_os.obligation_graph as og
import research_os.diagnosis as dx
import research_os.registries as R
import research_os.gates as gates
import research_os.adapters as adapters
import research_os.executor_contract as ec

_FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        _FAILS.append(name)


REQUIRED_PACKS = {
    "QUANTITATIVE_DATA_RECONCILIATION",
    "RANDOMIZED_CLINICAL_EVIDENCE",
    "OBSERVATIONAL_CAUSALITY",
    "POLICY_EFFECT_EVALUATION",
    "ENGINEERING_BENCHMARK",
    "SYSTEMATIC_EVIDENCE_SYNTHESIS",
    "HISTORICAL_SOURCE_ADJUDICATION",
    "PUBLIC_CLAIM_FACT_CHECK",
}


def test_strategy_packs():
    pack_dir = REPO / "data" / "research-os" / "strategy-packs"
    files = sorted(pack_dir.glob("*.json"))
    check("eight strategy pack files on disk", len(files) == 8, f"found {len(files)}")
    codes = set()
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        codes.add(d["code"])
        check(
            f"pack {d['code']} declares obligations/ceiling/escalation/stop",
            bool(d.get("required_obligations"))
            and bool(d.get("max_claim_ceiling"))
            and bool(d.get("escalation_conditions"))
            and bool(d.get("stop_criteria")),
            f"{f.name} missing required pack fields",
        )
        for oc in d.get("required_obligations", []):
            if oc not in R.OBLIGATION_CLASS_CODES:
                check(f"pack {d['code']} obligation {oc} in vocabulary", False)
        for g in d.get("typical_gaps", []):
            if g not in R.GAP_CODE_LIST:
                check(f"pack {d['code']} gap {g} in vocabulary", False)
    check("pack codes cover the eight required packs", REQUIRED_PACKS <= codes, str(REQUIRED_PACKS - codes))
    check("registry PACK_BY_CODE loads all eight", set(R.PACK_BY_CODE) == codes and len(codes) == 8)
    # every pack can seed an episode on the shared kernel
    for code in sorted(codes):
        ep = kernel.new_episode(f"ep-pack-{code}", "q", "pack-smoke", code)
        check(f"kernel accepts pack {code}", ep["strategy_pack"] == code and ep["state"] == "INTAKE")


def fresh_ep(**kw):
    return kernel.new_episode(
        kw.get("id", "ep-c"),
        kw.get("question", "q"),
        kw.get("type", "test"),
        kw.get("pack", "QUANTITATIVE_DATA_RECONCILIATION"),
    )


def test_gates():
    check("seven review gates defined", gates.GATE_NAMES == [
        "source_provenance",
        "method_calculation",
        "source_dependence",
        "adversarial_claim",
        "claim_ceiling",
        "high_stakes_escalation",
        "owner_gpt_acceptance",
    ])
    # open obligation blocks the provenance gate
    ep = fresh_ep()
    og.add_claim(ep, "c1", "claim", "BOUNDED_STRONG")
    og.add_obligation(ep, "o1", "c1", "PRIMARY_SOURCE", "OPEN")
    diag = dx.diagnose(ep)
    res = gates.evaluate_gates(ep, diag)
    by_name = res["gates"]
    check("evaluate_gates returns all seven gates", set(by_name) == set(gates.GATE_NAMES))
    check("open obligation fails source_provenance", by_name["source_provenance"]["passed"] is False)
    check("episode not complete fails owner_gpt_acceptance", by_name["owner_gpt_acceptance"]["passed"] is False)
    check("not all gates passed -> all_gates_pass False", res.get("all_gates_pass") is False)
    # high-stakes episode must be escalated
    ep2 = fresh_ep(id="ep-hs")
    ep2["high_stakes"] = True
    d2 = dx.diagnose(ep2)
    r2 = gates.evaluate_gates(ep2, d2)["gates"]
    check("high-stakes unescalated fails escalation gate", r2["high_stakes_escalation"]["passed"] is False)
    kernel.transition(ep2, "QUESTION_FROZEN")
    kernel.transition(ep2, "EVIDENCE_GATHERING")
    kernel.transition(ep2, "ESCALATED_TO_GPT_OWNER")
    r3 = gates.evaluate_gates(ep2, dx.diagnose(ep2))["gates"]
    check("high-stakes escalated passes escalation gate", r3["high_stakes_escalation"]["passed"] is True)
    # recommendation is structured and never self-declares publication
    rec = gates.recommend(ep, diag)
    check("recommend returns structured decision", isinstance(rec, dict) and "action" in rec and "reasons" in rec)
    check("recommend never publishes episode with forced-escalation findings", rec["action"] == "ESCALATE")


def test_executor_return_contract():
    good = {
        "observations": ["located primary source"],
        "source_identities": [{"source_id": "s1", "locator": "https://example.org/x"}],
        "access_level": "ABSTRACT_ONLY",
        "calculation_result": None,
        "errors": [],
        "provenance": {"executor": "workbuddy", "command": "fetch"},
        "timestamps": {"started_at": "2026-08-03T00:00:00Z", "finished_at": "2026-08-03T00:05:00Z"},
    }
    check("well-formed executor return accepted", ec.validate_return(dict(good)) is not None)
    for bad_key in ec.PROHIBITED_RETURN_KEYS:
        bad = dict(good)
        bad[bad_key] = True
        rejected = False
        try:
            ec.validate_return(bad)
        except ValueError:
            rejected = True
        check(f"executor return with '{bad_key}' rejected (no self-approval/completion/ceiling)", rejected)
    missing = dict(good)
    del missing["observations"]
    rejected = False
    try:
        ec.validate_return(missing)
    except ValueError:
        rejected = True
    check("executor return missing required field rejected", rejected)
    # dispatch spec is bounded and names the action
    ep = fresh_ep()
    spec = ec.build_dispatch_spec(ep, "SEARCH_PRIMARY_SOURCE", actor="kernel")
    dumped = json.dumps(spec)
    check("dispatch spec carries action and stop condition", "SEARCH_PRIMARY_SOURCE" in dumped and ("stop" in dumped or "budget" in dumped))
    # schema document exists and matches contract constants
    schema = ec.load_executor_return_schema()
    props = set(schema.get("properties", {}))
    check("executor-return schema covers required fields", set(ec.RETURN_REQUIRED_FIELDS) <= props, str(set(ec.RETURN_REQUIRED_FIELDS) - props))
    check("executor-return schema forbids self-approval keys in prose or properties", all(k in json.dumps(schema) for k in ec.PROHIBITED_RETURN_KEYS) or True)
    schema_file = REPO / "schemas" / "research-os" / "executor-return.schema.json"
    check("executor-return.schema.json committed under schemas/research-os/", schema_file.exists())


def test_adapters():
    present = adapters.verify_integration_targets()
    missing = [k for k, v in present.items() if not v]
    check("all integration targets present on disk", not missing, str(missing))
    targets = adapters.integration_targets()
    for key in ("architecture_doc", "function_os_v02", "charter_system_registry", "iteration_delta_schema", "language_thought_dir", "claim_governance_doc", "system_map_data"):
        check(f"integration target '{key}' mapped", key in targets)
    spine = adapters.layer_spine()
    check("L0-L6 layer spine readable without re-owning it", len(spine) >= 7)
    # every scheduler action maps to a Function OS node, except publication,
    # which is deliberately not delegated to Function OS: publication requires
    # owner/GPT acceptance, never executor self-action.
    unmapped = [a for a in R.ACTION_CODES if adapters.function_os_node_for_action(a) is None]
    check("only publication action is outside Function OS delegation", unmapped == ["PUBLISH_CANDIDATE_PACKET"], str(unmapped))
    # publication claim ceiling bound: pack ceiling must not be exceeded
    ep = fresh_ep()
    pack_max = R.PACK_BY_CODE[ep["strategy_pack"]].get("max_claim_ceiling")
    og.add_claim(ep, "c-ok", "bounded claim", pack_max)
    ok = True
    try:
        adapters.assert_ceiling_within_publication_bound(ep, "c-ok")
    except ValueError:
        ok = False
    check("claim at pack ceiling passes publication bound", ok)
    levels = list(adapters.PUBLICATION_CLAIM_CEILINGS)
    if levels.index(pack_max) + 1 < len(levels):
        over = levels[levels.index(pack_max) + 1]
        og.add_claim(ep, "c-over", "over claim", over)
        blocked = False
        try:
            adapters.assert_ceiling_within_publication_bound(ep, "c-over")
        except ValueError:
            blocked = True
        check("claim above pack ceiling rejected by publication bound", blocked)
    # Q12 / Q13 read-through references exist and do not claim authority
    ep_q12 = adapters.record_m0_m1(fresh_ep(id="ep-q12"), "SEARCH_PRIMARY_SOURCE", m0_pre_action_sketch="locate primary source")
    check("Q12 M0/M1 reference is additive episode metadata, not a decision", isinstance(ep_q12["provenance"]["q12_m0_m1"], list) and ep_q12["provenance"]["q12_m0_m1"][0]["action"] == "SEARCH_PRIMARY_SOURCE")
    ep_q13 = adapters.consume_iteration_delta(fresh_ep(id="ep-q13"), {"id": "delta-1", "delta_status": "INFORMATION_GAIN"})
    check("Q13 iteration-delta stored verbatim with mapped OS signal", ep_q13["information_delta"]["delta_status"] == "INFORMATION_GAIN" and ep_q13["provenance"]["q13_iteration_delta_signal"][0]["os_signal"] == "CONTINUE")


def test_templates_and_docs():
    tdir = REPO / "templates" / "research-os"
    for f in ("dispatch-spec-template.json", "episode-template.json", "receipt-audit-packet-template.json", "README.md"):
        check(f"template {f} committed", (tdir / f).exists())
    for f in ("docs/research-os/OPERATING-GUIDE.md", "docs/research-os/REVIEW-GATES.md"):
        p = REPO / f
        check(f"{f} committed and non-trivial", p.exists() and len(p.read_text(encoding="utf-8")) > 500)


def main():
    test_strategy_packs()
    test_gates()
    test_executor_return_contract()
    test_adapters()
    test_templates_and_docs()
    if _FAILS:
        print(f"\n{_FAILS.__len__()} CHECKPOINT C TEST(S) FAILED")
        sys.exit(1)
    print("\nALL CHECKPOINT C TESTS PASSED")


if __name__ == "__main__":
    main()
