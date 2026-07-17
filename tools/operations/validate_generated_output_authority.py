#!/usr/bin/env python3
"""Validate the generated-output authority table.

Checks performed:
1. Schema validation against generated-output-authority.schema.json
2. Every declared generated output file exists on disk
3. Every producer_command script exists on disk
4. Every input_authorities file exists on disk
5. No duplicate semantic authority (same producer_id + same sorted input_authorities
   producing same output_type must not claim two different paths unless justified
   as a deliberate copy)
6. Diff coverage: seeds ∪ generated_outputs == all diff paths (no gaps, no extras)
7. No overlap between seed paths and generated output paths
8. For byte_level_recompute propagation outputs, run --check to verify freshness

Exit 0 on full pass, exit 1 on any failure.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
AUTHORITY_PATH = ROOT / "data" / "operations" / "generated-output-authority.json"
SCHEMA_PATH = ROOT / "schemas" / "operations" / "generated-output-authority.schema.json"
REQUEST_PATH = ROOT / "data" / "operations" / "propagation" / "121Q32-request.json"
BASE_MAIN = "d1bedb074af8dad8202b4324f3f5bbbb6b308b51"

failures = []
warnings = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"  FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"  OK:   {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"  WARN: {msg}")


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_schema() -> dict:
    """Step 1: Schema validation."""
    print("\n[1/8] Schema validation")
    authority = load_json(AUTHORITY_PATH)
    schema = load_json(SCHEMA_PATH)

    try:
        from jsonschema import Draft202012Validator
        errors = sorted(
            Draft202012Validator(schema).iter_errors(authority),
            key=lambda e: list(e.path),
        )
        if errors:
            for err in errors:
                fail(f"Schema error: {'/'.join(str(p) for p in err.path)}: {err.message}")
        else:
            ok("Authority passes JSON Schema validation")
    except ImportError:
        warn("jsonschema not installed; skipping formal schema validation")
        # Basic structural check
        for key in ("schema_version", "task_id", "description", "generated_outputs"):
            if key not in authority:
                fail(f"Missing required top-level key: {key}")
        if "generated_outputs" in authority:
            ok("Basic structure present")

    return authority


def check_output_files_exist(authority: dict) -> None:
    """Step 2: Every declared generated output file exists."""
    print("\n[2/8] Generated output file existence")
    for item in authority["generated_outputs"]:
        path = ROOT / item["path"]
        if path.exists():
            ok(f"{item['path']} exists")
        else:
            fail(f"{item['path']} does NOT exist on disk")


def check_producer_scripts(authority: dict) -> None:
    """Step 3: Every producer_command script exists."""
    print("\n[3/8] Producer script existence")
    checked = set()
    for item in authority["generated_outputs"]:
        cmd = item["producer_command"]
        if cmd in checked:
            continue
        checked.add(cmd)
        # Extract the script path from the command (e.g. "python tools/foo.py" -> "tools/foo.py")
        parts = cmd.split()
        script_path = None
        for part in parts:
            if part.endswith(".py") or part.endswith(".sh"):
                script_path = part
                break
        if script_path is None:
            fail(f"Cannot extract script path from command: {cmd}")
            continue
        full_path = ROOT / script_path
        if full_path.exists():
            ok(f"{script_path} exists")
        else:
            fail(f"{script_path} does NOT exist (from command: {cmd})")


def check_input_authorities(authority: dict) -> None:
    """Step 4: Every input_authorities file exists."""
    print("\n[4/8] Input authority file existence")
    all_inputs = set()
    for item in authority["generated_outputs"]:
        for inp in item["input_authorities"]:
            all_inputs.add(inp)
    for inp in sorted(all_inputs):
        path = ROOT / inp
        if path.exists():
            ok(f"{inp} exists")
        else:
            fail(f"{inp} does NOT exist on disk")


def check_duplicate_semantic_authority(authority: dict) -> None:
    """Step 5: No duplicate semantic authority.
    
    Two entries with the same producer_id AND same sorted input_authorities
    AND same output_type that point to different paths are potential duplicates.
    If the files are byte-identical, it's a deliberate copy (WARN).
    If the files differ, it's a genuine inconsistency (FAIL).
    """
    print("\n[5/8] Duplicate semantic authority check")
    from collections import defaultdict
    groups = defaultdict(list)
    for item in authority["generated_outputs"]:
        key = (item["producer_id"], tuple(sorted(item["input_authorities"])), item["output_type"])
        groups[key].append(item["path"])

    has_real_dupes = False
    for (producer, inputs, otype), paths in groups.items():
        if len(paths) <= 1:
            continue
        # Check if all files are byte-identical
        contents = []
        for p in paths:
            fp = ROOT / p
            if fp.exists():
                contents.append(fp.read_bytes())
            else:
                contents.append(None)
        
        all_identical = all(c is not None and c == contents[0] for c in contents)
        if all_identical:
            warn(f"Deliberate copy: producer={producer}, type={otype}: {len(paths)} identical files: {[p.split('/')[-1] for p in paths]}")
        else:
            has_real_dupes = True
            fail(f"INCONSISTENT duplicate: producer={producer}, type={otype}: {paths} have different content")
    
    if not has_real_dupes:
        ok("No inconsistent duplicate semantic authorities")


def check_diff_coverage(authority: dict) -> None:
    """Step 6 & 7: Diff coverage completeness."""
    print("\n[6/8] Diff coverage (seeds ∪ generated == diff paths)")
    
    # Get diff paths
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{BASE_MAIN}...HEAD"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if result.returncode != 0:
        fail(f"git diff failed: {result.stderr}")
        return
    diff_paths = set(result.stdout.strip().split("\n"))

    # Get seeds
    request = load_json(REQUEST_PATH)
    seeds = set(request["changed_paths"])

    # Get generated outputs
    generated = {item["path"] for item in authority["generated_outputs"]}

    # Check coverage
    covered = seeds | generated
    uncovered = diff_paths - covered
    extra = covered - diff_paths
    overlap = seeds & generated

    print(f"  Diff paths: {len(diff_paths)}")
    print(f"  Seeds: {len(seeds)}")
    print(f"  Generated: {len(generated)}")
    print(f"  Covered: {len(covered)}")

    if uncovered:
        for p in sorted(uncovered):
            fail(f"Uncovered diff path (not in seeds or generated): {p}")
    else:
        ok("All diff paths covered (0 uncovered)")

    if extra:
        for p in sorted(extra):
            fail(f"Declared but not in diff: {p}")
    else:
        ok("No extra declarations (0 outside diff)")

    print(f"\n[7/8] Seed/generated disjointness")
    if overlap:
        for p in sorted(overlap):
            fail(f"Path is both seed and generated: {p}")
    else:
        ok("Seeds and generated outputs are disjoint")

    # Summary
    print(f"\n  Coverage summary: {len(seeds)} seeds + {len(generated)} generated = {len(covered)} total (diff: {len(diff_paths)})")
    if len(covered) == len(diff_paths) and not uncovered and not extra:
        ok("DIFF COVERAGE: COMPLETE")
    else:
        fail("DIFF COVERAGE: INCOMPLETE")


def check_propagation_freshness(authority: dict) -> None:
    """Step 8: For propagation outputs with byte_level_recompute, run --check."""
    print("\n[8/8] Propagation freshness (--check)")
    
    propagation_items = [
        item for item in authority["generated_outputs"]
        if item["producer_id"] == "compute_change_propagation"
        and item["freshness_mode"] == "byte_level_recompute"
    ]
    
    if not propagation_items:
        ok("No propagation outputs to freshness-check")
        return

    # Run compute_change_propagation.py --check
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "operations" / "compute_change_propagation.py"),
        "--request", str(REQUEST_PATH),
        "--output", str(ROOT / "data/operations/propagation/121Q32-closure.json"),
        "--report", str(ROOT / "data/operations/propagation/121Q32-impact-report.md"),
        "--map-delta", str(ROOT / "data/operations/propagation/121Q32-system-map-delta.json"),
        "--residue", str(ROOT / "data/operations/propagation/121Q32-residue.json"),
        "--check",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    
    if result.returncode == 0:
        try:
            check_output = json.loads(result.stdout.strip().split("\n")[-1])
            if check_output.get("status") == "PASS":
                ok(f"Propagation --check PASS (hash: {check_output.get('closure_hash', '?')[:16]}...)")
            else:
                fail(f"Propagation --check status: {check_output.get('status', 'unknown')}")
        except (json.JSONDecodeError, IndexError):
            ok("Propagation --check exited 0")
    else:
        fail(f"Propagation --check FAILED (rc={result.returncode}): {result.stderr[:200]}")


def main() -> int:
    print("=" * 60)
    print("Generated Output Authority Validator")
    print("=" * 60)
    print(f"Authority: {AUTHORITY_PATH}")
    print(f"Schema:    {SCHEMA_PATH}")
    print(f"Request:   {REQUEST_PATH}")
    print(f"Base main: {BASE_MAIN}")

    if not AUTHORITY_PATH.exists():
        print(f"\nFATAL: Authority file not found: {AUTHORITY_PATH}")
        return 1
    if not SCHEMA_PATH.exists():
        print(f"\nFATAL: Schema file not found: {SCHEMA_PATH}")
        return 1
    if not REQUEST_PATH.exists():
        print(f"\nFATAL: Request file not found: {REQUEST_PATH}")
        return 1

    authority = check_schema()
    check_output_files_exist(authority)
    check_producer_scripts(authority)
    check_input_authorities(authority)
    check_duplicate_semantic_authority(authority)
    check_diff_coverage(authority)
    check_propagation_freshness(authority)

    print("\n" + "=" * 60)
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failures, {len(warnings)} warnings)")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print(f"RESULT: PASS (0 failures, {len(warnings)} warnings)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
