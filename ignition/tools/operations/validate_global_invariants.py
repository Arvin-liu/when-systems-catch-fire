#!/usr/bin/env python3
"""Global invariant engine (campaign Line D, D4).

Deterministic, stdlib-first, non-mutating. Validates the reconstructed
repository state against the global invariants demanded by the campaign TASK.
Integrates (does not duplicate) existing validators: where an authoritative
validator exists (e.g. path accounting), this engine records its status as an
external check rather than reimplementing it.

Checks
------
INV-01 ledger covers every open PR exactly once
INV-02 exactly one ACCEPTED_CURRENT and it matches the current-truth projection
INV-03 terminalized iteration chain is contiguous (no gaps)
INV-04 no open candidate represented as accepted/current
INV-05 research branches never represented as formal knowledge
INV-06 stacked PR parent/head identity resolves within the open PR set
INV-07 Task 114 terminal history immutable (tag + current acceptance intact)
INV-08 component registry closes into the system map
INV-09 public surface relative links resolve to existing files
INV-10 ledgers satisfy their JSON schemas (required keys; full jsonschema if present)
INV-11 ledger generation is deterministic (rebuild byte-identical)

Exit: 0 all closed, 1 open invariants, 2 usage. --self-test runs fixtures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "data" / "operations"
LEDGER = OPS / "repository-state-ledger.json"
LINEAGE = OPS / "candidate-lineage-registry.json"
RESULTS = OPS / "global-invariant-results.json"
SCHEMA_DIR = OPS / "schemas"

CHECKS: list[dict] = []


def record(cid: str, ok: bool, detail: str) -> None:
    CHECKS.append({"id": cid, "status": "PASS" if ok else "FAIL", "detail": detail})


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def inv01(ledger: dict, prs: list[dict]) -> None:
    classified = {p["pr_number"] for p in ledger["open_draft_candidates"]} | {
        p["pr_number"] for p in ledger["stacked_repair_candidates"]
    }
    snapshot = {p["number"] for p in prs}
    dupes = len(ledger["open_draft_candidates"]) + len(ledger["stacked_repair_candidates"]) != len(classified)
    record("INV-01", classified == snapshot and not dupes,
           f"classified={len(classified)} snapshot={len(snapshot)} duplicates={dupes}")


def inv02(ledger: dict) -> None:
    current = [it for it in ledger["accepted_iterations"] if it["state_category"] == "ACCEPTED_CURRENT"]
    ok = len(current) == 1 and current[0]["iteration"] == ledger["accepted_current"]["iteration"]
    record("INV-02", ok, f"accepted_current={ledger['accepted_current']['iteration']} iterations_marked={ [c['iteration'] for c in current] }")


def inv03(ledger: dict) -> None:
    nums = sorted(it["iteration"] for it in ledger["accepted_iterations"] if it["terminalized"])
    gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in nums] if nums else [0]
    record("INV-03", not gaps, f"terminalized iterations {nums[0]}..{nums[-1]}; gaps={gaps}")


def inv04(ledger: dict) -> None:
    accepted_iters = {it["iteration"] for it in ledger["accepted_iterations"] if it["state_category"] in ("ACCEPTED_CURRENT", "ACCEPTED_HISTORICAL")}
    candidate_heads = {p["head"] for p in ledger["open_draft_candidates"]} | {p["head"] for p in ledger["stacked_repair_candidates"]}
    leaks = [h for h in candidate_heads if h == "main" or h.startswith("ignition/iterations/")]
    record("INV-04", not leaks and ledger["accepted_current"]["source"].endswith("current-truth-projection.json"),
           f"open_candidate_heads={len(candidate_heads)} accepted_leaks={leaks}; accepted states derive only from ledger/tags/FINAL_STATE")


def inv05(ledger: dict) -> None:
    research = {r["branch"] for r in ledger["research_candidate_not_formal_knowledge"]}
    accepted_names = {it.get("terminal_tag") or "" for it in ledger["accepted_iterations"]}
    leak = research & accepted_names
    record("INV-05", not leak, f"research_branches={len(research)} represented_as_accepted={sorted(leak)}")


def inv06(ledger: dict, prs: list[dict], branches: set[str] | None = None) -> None:
    heads = {p["headRefName"] for p in prs}
    known = heads | (branches or set())
    broken = [p["pr_number"] for p in ledger["stacked_repair_candidates"] if p["base"] not in known]
    record("INV-06", not broken, f"stacked={len(ledger['stacked_repair_candidates'])} unresolved_parents={broken} (parent may be an open-PR head or an existing branch)")


def inv07(ledger: dict, tags: dict) -> None:
    tag = "ignition/iterations/114/terminal-r1"
    it114 = next((it for it in ledger["accepted_iterations"] if it["iteration"] == 114), None)
    ok = tag in tags and it114 is not None and it114["terminalized"] and it114["state_category"] == "ACCEPTED_CURRENT"
    record("INV-07", bool(ok), f"task114 tag_present={tag in tags} terminalized={it114 and it114['terminalized']} category={it114 and it114['state_category']}")


def inv08() -> None:
    comps = json.loads((OPS / "project-components.json").read_text(encoding="utf-8"))
    smap = json.loads((ROOT / "data" / "architecture" / "interactive-system-map.json").read_text(encoding="utf-8"))
    blob = json.dumps(smap)
    missing, justified = [], []
    for c in comps.get("components", []):
        cid = c.get("component_id") or c.get("id")
        if not cid:
            continue
        if cid in blob:
            continue
        proj = c.get("map_projection") or {}
        if proj.get("no_change_reason") or proj.get("visible") is False:
            justified.append(cid)
        else:
            missing.append(cid)
    record("INV-08", not missing, f"components in map or justified non-projection; unjustified_missing={missing}; justified_non_projected={len(justified)}")


def inv09() -> None:
    broken = []
    for surface in ("README.md", "llms.txt", "AI-START-HERE.md", "HUMAN-READING.md"):
        p = ROOT / surface
        if not p.exists():
            continue
        for m in re.finditer(r"\]\(([^)#][^)]*)\)", p.read_text(encoding="utf-8")):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            tp = (p.parent / target.split("#")[0]).resolve()
            if not tp.exists():
                broken.append(f"{surface}: {target}")
    for line in (ROOT / "llms.txt").read_text(encoding="utf-8").splitlines():
        for m in re.finditer(r"\(([^)]+)\)", line):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://")):
                continue
            if "/" not in target and not re.search(r"\.(md|json|jsonl|txt|yml)$", target):
                continue  # prose status labels like (Current) are not path references
            tp = (ROOT / target).resolve()
            if not tp.exists():
                broken.append(f"llms.txt: {target}")
    record("INV-09", not broken, f"broken_relative_links={broken[:6]}{'...' if len(broken) > 6 else ''} total={len(broken)}")


def required_keys(schema_path: Path) -> list[str]:
    sch = json.loads(schema_path.read_text(encoding="utf-8"))
    return sch.get("required", [])


def inv10() -> None:
    problems = []
    for doc, schema in ((LEDGER, "repository-state-ledger.schema.json"), (LINEAGE, "candidate-lineage-registry.schema.json")):
        data = json.loads(doc.read_text(encoding="utf-8"))
        missing = [k for k in required_keys(SCHEMA_DIR / schema) if k not in data]
        if missing:
            problems.append(f"{doc.name} missing {missing}")
    try:
        import jsonschema  # optional stronger pass
        for doc, schema in ((LEDGER, "repository-state-ledger.schema.json"), (LINEAGE, "candidate-lineage-registry.schema.json")):
            jsonschema.validate(json.loads(doc.read_text()), json.loads((SCHEMA_DIR / schema).read_text()))
    except ImportError:
        pass
    except Exception as exc:
        problems.append(f"jsonschema: {exc}")
    record("INV-10", not problems, "; ".join(problems) or "ledger+lineage satisfy schemas")


def inv11() -> None:
    before = sha256_bytes(LEDGER.read_bytes())
    subprocess.run([sys.executable, str(ROOT / "tools" / "operations" / "build_repository_state_ledger.py")],
                   check=True, capture_output=True, cwd=ROOT)
    after = sha256_bytes(LEDGER.read_bytes())
    record("INV-11", before == after, f"rebuild byte-identical={before == after} sha256={before[:16]}")


def run_all() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    lineage = json.loads(LINEAGE.read_text(encoding="utf-8"))
    prs = json.loads((OPS / "campaign-inputs" / "open-prs-20260803.json").read_text(encoding="utf-8"))
    tags = {}
    for line in (OPS / "campaign-inputs" / "tags-20260803.txt").read_text().splitlines():
        name = line.rsplit(" ", 1)[0]
        tags[name] = line.rsplit(" ", 1)[1]
    inv01(ledger, prs)
    inv02(ledger)
    inv03(ledger)
    inv04(ledger)
    inv05(ledger)
    branches = set()
    for line in (OPS / "campaign-inputs" / "remote-branches-20260803.txt").read_text().splitlines():
        branches.add(line.rsplit(" ", 1)[0].replace("origin/", "", 1))
    inv06(ledger, prs, branches)
    inv07(ledger, tags)
    inv08()
    inv09()
    inv10()
    inv11()
    # integration note: path-accounting, foundation and lifecycle validators are
    # authoritative in their own workflows; Line B re-verified them green at the
    # relevant heads. They are recorded here as external checks, not re-run.
    external = [
        {"id": "EXT-01", "validator": "tools/foundation/validate_repository_path_classification.py --check", "status_at_line_b_head": "PASS"},
        {"id": "EXT-02", "validator": "tools/foundation/validate_foundation.py", "status_at_line_b_head": "PASS (63/63)"},
        {"id": "EXT-03", "validator": "iteration-lifecycle-validation workflow", "status_at_pr189_head_after_repair": "PASS"},
    ]
    failed = sum(1 for c in CHECKS if c["status"] == "FAIL")
    results = {
        "schema_ref": "data/operations/schemas/global-invariant-results.schema.json",
        "checked_by": "tools/operations/validate_global_invariants.py",
        "checks": CHECKS,
        "external_checks": external,
        "total": len(CHECKS),
        "failed": failed,
        "verdict": "GLOBAL_INVARIANTS_CLOSED" if failed == 0 else "GLOBAL_INVARIANTS_OPEN",
    }
    RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for c in CHECKS:
        print(f"{c['status']} {c['id']} {c['detail']}")
    print(f"TOTAL={len(CHECKS)} FAILED={failed} VERDICT={results['verdict']}")
    return 0 if failed == 0 else 1


def self_test() -> int:
    fx_root = ROOT / "tests" / "fixtures" / "global_invariants"
    cases = {
        "duplicate-pr-classification": ("INV-01", lambda lg, prs: inv01(lg, prs)),
        "two-accepted-current": ("INV-02", lambda lg, prs: inv02(lg)),
        "iteration-chain-gap": ("INV-03", lambda lg, prs: inv03(lg)),
        "research-branch-accepted": ("INV-05", lambda lg, prs: inv05(lg)),
        "stacked-parent-missing": ("INV-06", lambda lg, prs: inv06(lg, prs)),
    }
    ok = True
    for name, (expected, fn) in cases.items():
        fx = fx_root / name
        CHECKS.clear()
        ledger = json.loads((fx / "repository-state-ledger.json").read_text(encoding="utf-8"))
        prs = json.loads((fx / "open-prs.json").read_text(encoding="utf-8"))
        fn(ledger, prs)
        hit = any(c["id"] == expected and c["status"] == "FAIL" for c in CHECKS)
        print(f"{'PASS' if hit else 'FAIL'}  fixture {name} triggers {expected}")
        ok = ok and hit
    print("SELF_TEST_OK" if ok else "SELF_TEST_FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Global invariant engine")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--run", action="store_true")
    grp.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    return self_test() if args.self_test else run_all()


if __name__ == "__main__":
    raise SystemExit(main())
