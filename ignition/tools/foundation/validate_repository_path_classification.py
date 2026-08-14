#!/usr/bin/env python3
"""Universal repository-path-accounting preflight (Task 107, Layer A).

Source of truth
----------------
A deterministic *rule engine* classifies every Git-tracked path into exactly one
governed category.  The committed manifest under
``data/foundation/repository-path-classification/classification-manifest.jsonl``
is a *generated snapshot* of that engine output.  In ``--check`` mode the engine is
re-run on the live Git tree and compared against the committed manifest.

Why an engine (not a hand-maintained list)
--------------------------------------------
* Every Git-tracked path is forced through the engine, so a newly added,
  deleted, or renamed path is caught automatically -- no silent exclusion of a
  handful of paths (contract §3.1) and no drifting hand-written parallel list
  (contract §4 Layer B).
* The ``AUTHORITATIVE_CLAIM_INPUT`` category is restricted to an explicit
  allowlist (the two CJK master tables).  Editorial / test / generated /
  candidate / evidence paths can *never* be classified authoritative, which is
  the anti-backflow guarantee (contract §3.1 / §3.2).

This tool is stdlib-first and fast: it does NOT re-run the heavy Foundation
generation chain.  It only enumerates ``git ls-files`` and applies prefix rules.

Exit codes: 0 = all checks passed, 1 = at least one check failed, 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
MANIFEST_DIR = ROOT / "data/foundation/repository-path-classification"
MANIFEST = MANIFEST_DIR / "classification-manifest.jsonl"
SCHEMA = ROOT / "data/foundation/schemas/repository-path-classification.schema.json"

# Authoritative claim / function discovery inputs.
# Restricted allowlist: the ONLY paths that may feed Foundation assertion or
# function discovery.  Everything else is non-authoritative by construction.
AUTHORITATIVE_PREFIXES: tuple[str, ...] = ("统一函数总表/", "统一案例总表/")

# Fallthrough category.  Must be zero after classification.
UNRESOLVED = "UNRESOLVED"

# Ordered rule list: (category, (prefix, ...)).  First match wins.
# Order matters: the operations exception must precede the broad ``data/`` rule.
RULES: list[tuple[str, tuple[str, ...]]] = [
    # 1. Authoritative assertion / function discovery inputs (restricted allowlist).
    ("AUTHORITATIVE_CLAIM_INPUT", AUTHORITATIVE_PREFIXES),
    # 2. Operations / receipt / history records.
    ("RECEIPT_HISTORY_OPERATIONS", ("data/operations/", "data/ops/")),
    # 3. Tools, scripts, workflows.
    ("TOOL_OR_WORKFLOW", ("tools/", "scripts/", ".github/", "reos_vnext/")),
    # 4. Schemas.
    ("SCHEMA", ("schemas/",)),
    # 5. Test fixtures.
    ("TEST_FIXTURE", ("tests/",)),
    # 6. Generated projections / outputs / reports.
    ("GENERATED_PROJECTION", ("outputs/", "reports/")),
    # 7. Evidence / benchmark results.
    ("EVIDENCE_OR_BENCHMARK", ("evidence-program/", "case_failures/")),
    # 8. Candidate (non-authoritative) claims -- must NOT be authoritative.
    ("CANDIDATE_NONAUTHORITATIVE_RECORD", ("function-os-candidate/",)),
    # 9. Reference surfaces / knowledge / templates / views / inputs / canonical / formal.
    # PUBLICATIONS/ is a maintained human-reading/reference surface; it is not
    # an authoritative claim input and must not flow back into Foundation discovery.
    ("REFERENCE_OR_KNOWLEDGE", ("KNOWLEDGE/", "PUBLICATIONS/", "templates/", "views/", "inputs/", "canonical/", "formal/")),
    # 10. Editorial articles / analyses / stories / results / licenses / agent-results.
    ("EDITORIAL_ARTICLE", ("docs/", "analysis/", "新故事/", "RESULTS/", "LICENSES/", "agent-results/")),
    # 11. All remaining data/ machine records.  Must come after the operations exception.
    ("GOVERNED_MACHINE_RECORD", ("data/",)),
    # 12. Root-level governance / meta docs (paths with no "/") are handled in classify().
]

# Categories that must never feed Foundation assertion discovery.
NON_AUTHORITATIVE_CATEGORIES = {
    "GOVERNED_MACHINE_RECORD",
    "GENERATED_PROJECTION",
    "EVIDENCE_OR_BENCHMARK",
    "EDITORIAL_ARTICLE",
    "TEST_FIXTURE",
    "SCHEMA",
    "TOOL_OR_WORKFLOW",
    "RECEIPT_HISTORY_OPERATIONS",
    "CANDIDATE_NONAUTHORITATIVE_RECORD",
    "REFERENCE_OR_KNOWLEDGE",
    "REPOSITORY_GOVERNANCE_DOC",
}

ALL_CATEGORIES = {"AUTHORITATIVE_CLAIM_INPUT"} | NON_AUTHORITATIVE_CATEGORIES | {UNRESOLVED}


def tracked_paths() -> list[str]:
    """Return every Git-tracked (and untracked-but-not-ignored) path, sorted."""
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=REPO_ROOT,
    )
    return sorted(p.decode("utf-8") for p in raw.split(b"\0") if p)


def logical_path(path: str) -> str:
    """Map repository-relative paths into the app-root classification namespace."""
    return path[len("ignition/"):] if path.startswith("ignition/") else path


def classify(path: str) -> tuple[str, str]:
    """Return ``(category, matched_rule_name)`` for a single path.

    The engine is pure and deterministic: only the path string is examined.
    """
    logical = logical_path(path)
    if "/" not in logical:
        return ("REPOSITORY_GOVERNANCE_DOC", "REPOSITORY_GOVERNANCE_DOC")
    for category, prefixes in RULES:
        for prefix in prefixes:
            if logical.startswith(prefix):
                return (category, category)
    return (UNRESOLVED, UNRESOLVED)


def live_classification() -> dict[str, tuple[str, str]]:
    """Run the engine over the live Git tree."""
    out: dict[str, tuple[str, str]] = {}
    for path in tracked_paths():
        out[path] = classify(path)
    return out


def read_manifest() -> dict[str, tuple[str, str]]:
    """Load the committed manifest into ``{path: (category, rule)}``."""
    result: dict[str, tuple[str, str]] = {}
    if not MANIFEST.is_file():
        return result
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        result[row["path"]] = (row["category"], row.get("matched_rule", row["category"]))
    return result


def generate() -> int:
    """Write the manifest from the live engine output.  Idempotent / deterministic.

    The manifest file itself lives under data/foundation/ and is a governed machine
    record; it is explicitly included so the snapshot accounts for its own path
    (otherwise --check would see the live tree out of sync with the snapshot).
    """
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    paths = tracked_paths()
    manifest_rel = str(MANIFEST.relative_to(REPO_ROOT))
    if manifest_rel not in paths:
        paths = paths + [manifest_rel]
    paths = sorted(set(paths))
    live = {p: classify(p) for p in paths}
    lines = []
    for path in paths:
        category, rule = live[path]
        lines.append(json.dumps(
            {"path": path, "category": category, "matched_rule": rule},
            ensure_ascii=False, sort_keys=True,
        ))
    MANIFEST.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    unresolved = sum(1 for _, (c, _) in live.items() if c == UNRESOLVED)
    print(f"GENERATED manifest={MANIFEST} paths={len(live)} unresolved={unresolved}")
    return 0 if unresolved == 0 else 1


def load_schema() -> dict | None:
    if not SCHEMA.is_file():
        return None
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _schema_valid_row(row: dict, schema: dict | None) -> tuple[bool, str]:
    """Lightweight stdlib schema/semantic validation (no jsonschema dependency)."""
    if not isinstance(row, dict):
        return False, "row is not an object"
    if "path" not in row or not isinstance(row["path"], str) or not row["path"]:
        return False, "missing/empty 'path'"
    if "category" not in row or row["category"] not in ALL_CATEGORIES:
        return False, f"missing/invalid 'category': {row.get('category')!r}"
    if "matched_rule" not in row or not isinstance(row["matched_rule"], str):
        return False, "missing 'matched_rule'"
    if schema:
        # If the committed schema declares an enum for category, honour it.
        cat_schema = schema.get("properties", {}).get("category", {})
        enum = cat_schema.get("enum")
        if enum and row["category"] not in enum:
            return False, f"category {row['category']!r} not in schema enum"
    return True, ""


def check(live: dict[str, tuple[str, str]] | None = None,
          manifest: dict[str, tuple[str, str]] | None = None) -> int:
    """Re-run the engine on the live tree and compare against the committed manifest.

    ``live`` / ``manifest`` may be injected for testing; when omitted they are read
    from the live Git tree and the committed manifest file respectively.

    Fail-closed: any of the following is a non-zero exit.
      * an UNRESOLVED (unclassified) path exists;
      * a path is duplicated in the manifest (file-level);
      * the live path set != the manifest path set (new / removed / renamed path);
      * a path's category changed vs the manifest;
      * the anti-backflow invariant is violated (authoritative path not in allowlist,
        either live or in the committed manifest);
      * a manifest row fails schema/semantic validation.
    """
    checks: list[tuple[str, bool, str]] = []
    if live is None:
        live = live_classification()
    if manifest is None:
        manifest = read_manifest()
        manifest_raw_lines = None
        if MANIFEST.is_file():
            manifest_raw_lines = [l for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        manifest_raw_lines = None
    schema = load_schema()

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    live_paths = sorted(live)
    manifest_paths = sorted(manifest)

    # C1: every tracked path classified (no UNRESOLVED).
    unresolved = [p for p, (c, _) in live.items() if c == UNRESOLVED]
    chk("classification:no-unresolved", not unresolved,
        f"count={len(unresolved)}" + ("" if not unresolved else f" example={unresolved[0]}"))

    # C2: manifest has no duplicate paths (file-level detection).
    if manifest_raw_lines is not None:
        dup = [p for p, n in Counter(json.loads(l)["path"] for l in manifest_raw_lines).items() if n > 1]
    else:
        dup = []
    chk("classification:no-duplicate", not dup, f"count={len(dup)}")

    # C3: manifest path set == live Git tree (no stale, no missing).
    live_set, manifest_set = set(live_paths), set(manifest_paths)
    missing = sorted(live_set - manifest_set)   # tracked but not in manifest
    stale = sorted(manifest_set - live_set)      # in manifest but no longer tracked
    chk("manifest:all-tracked-accounted", not missing,
        f"missing={len(missing)}" + ("" if not missing else f" example={missing[0]}"))
    chk("manifest:no-stale-path", not stale,
        f"stale={len(stale)}" + ("" if not stale else f" example={stale[0]}"))

    # C4: category agreement for every shared path.
    changed = sorted(
        p for p in (live_set & manifest_set)
        if live[p][0] != manifest[p][0]
    )
    chk("manifest:category-stable", not changed,
        f"changed={len(changed)}" + ("" if not changed else f" example={changed[0]}"))

    # C5: anti-backflow invariant -- authoritative only from the allowlist (live).
    backflow = [
        p for p, (c, _) in live.items()
        if c == "AUTHORITATIVE_CLAIM_INPUT" and not logical_path(p).startswith(AUTHORITATIVE_PREFIXES)
    ]
    chk("anti-backflow:authoritative-only-from-allowlist", not backflow,
        f"violations={len(backflow)}" + ("" if not backflow else f" example={backflow[0]}"))
    # Defensive: none of the non-authoritative categories may sit under the allowlist.
    mislabeled = [
        p for p, (c, _) in live.items()
        if c in NON_AUTHORITATIVE_CATEGORIES and logical_path(p).startswith(AUTHORITATIVE_PREFIXES)
    ]
    chk("anti-backflow:allowlist-not-mislabeled", not mislabeled,
        f"count={len(mislabeled)}")

    # C5b: anti-backflow invariant -- the committed manifest must not claim
    # authoritative for any path outside the allowlist (e.g. editorial mislabeled).
    manifest_backflow = [
        p for p, (c, _) in manifest.items()
        if c == "AUTHORITATIVE_CLAIM_INPUT" and not logical_path(p).startswith(AUTHORITATIVE_PREFIXES)
    ]
    chk("anti-backflow:manifest-authoritative-allowlist", not manifest_backflow,
        f"violations={len(manifest_backflow)}" + ("" if not manifest_backflow else f" example={manifest_backflow[0]}"))

    # C6: schema / semantic validation of every manifest row.
    if manifest_raw_lines is not None:
        bad = 0
        first_bad = ""
        for line in manifest_raw_lines:
            ok, why = _schema_valid_row(json.loads(line), schema)
            if not ok:
                bad += 1
                if not first_bad:
                    first_bad = why
        chk("schema:manifest-rows-valid", bad == 0, f"invalid={bad}" + ("" if not bad else f" {first_bad}"))
    elif manifest:
        bad = 0
        first_bad = ""
        for p, (c, r) in manifest.items():
            ok, why = _schema_valid_row({"path": p, "category": c, "matched_rule": r}, schema)
            if not ok:
                bad += 1
                if not first_bad:
                    first_bad = why
        chk("schema:manifest-rows-valid", bad == 0, f"invalid={bad}" + ("" if not bad else f" {first_bad}"))

    # Summary of category distribution (human-readable CI log).
    dist = Counter(c for _, (c, _) in live.items())
    print("category_distribution:")
    for cat in sorted(dist):
        print(f"  {cat}={dist[cat]}")
    print(f"tracked={len(live_paths)} manifest={len(manifest_paths)}")

    for name, ok, detail in checks:
        print(("PASS" if ok else "FAIL") + " " + name + (" " + detail if detail else ""))
    passed = sum(ok for _, ok, _ in checks)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={passed} CHECKS_FAILED={len(checks) - passed}")
    if passed == len(checks):
        print("REPOSITORY_PATH_CLASSIFICATION_VALID")
        return 0
    return 1


def self_test() -> int:
    """Internal sanity checks for the engine itself (determinism, coverage)."""
    a = live_classification()
    b = live_classification()
    assert a == b, "engine not deterministic"
    assert all(c != UNRESOLVED for _, (c, _) in a.items()), "engine left unresolved paths"
    print("SELF_TEST_OK paths=%d" % len(a))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Universal repository-path-accounting preflight (Layer A).")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--generate", action="store_true", help="write the manifest from the live engine")
    grp.add_argument("--check", action="store_true", help="re-run engine and compare to committed manifest")
    grp.add_argument("--self-test", action="store_true", help="internal engine sanity checks")
    args = ap.parse_args()
    if args.generate:
        return generate()
    if args.check:
        return check()
    if args.self_test:
        return self_test()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
