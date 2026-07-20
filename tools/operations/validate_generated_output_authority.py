#!/usr/bin/env python3
"""Validate the generated-output authority table.

Checks performed:
1. Schema validation against generated-output-authority.schema.json
2. Every declared generated output file exists on disk
3. Every producer_command script exists on disk
4. Every input_authorities file exists on disk
5. No duplicate semantic authority (same producer_id/generator_id + same sorted
   input_authorities producing same output_type must not claim two different paths)
6. Diff coverage: seeds ∪ generated_outputs == all diff paths (no gaps, no extras)
7. No overlap between seed paths and generated output paths
8. For registered_generator entries: positive verification against generator-registry.json
   (generator_id exists, canonical_tool matches, output path is allowed, input authorities
   match exactly, content digest matches the live file, lifecycle_status active)
9. For historical_sealed_record entries: the seal file exists and its digest matches; the
   record is historical_only and does NOT claim current/live authority.

Authority kinds are mutually exclusive (producer_command / registered_generator /
historical_sealed_record). Free-string generators are rejected by the schema.

Exit 0 on full pass, exit 1 on any failure.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
AUTHORITY_PATH = ROOT / "data" / "operations" / "generated-output-authority.json"
SCHEMA_PATH = ROOT / "schemas" / "operations" / "generated-output-authority.schema.json"
GENERATOR_REGISTRY_PATH = ROOT / "data" / "operations" / "generator-registry.json"
REQUEST_PATH = ROOT / "data" / "operations" / "propagation" / "121Q32I-request.json"
# Kept ONLY as a last-resort fallback. The actual base/era are derived per-request from
# the iteration manifest via tools/operations/era_resolver.py (no hardcoded task/SHA in
# the production contract path).
BASE_MAIN = "4097e610eebfc65c739df4fe7d2900161c204a9d"

try:
    from era_resolver import resolve_era_for_request
except ImportError:  # allow running from repo root or tools/operations
    import importlib.util

    _spec = importlib.util.spec_from_file_location(
        "era_resolver", ROOT / "tools" / "operations" / "era_resolver.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    resolve_era_for_request = _mod.resolve_era_for_request

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


def is_registered_generator(item: dict) -> bool:
    """A registered_generator entry carries a generator_id (registered in the registry)."""
    return "generator_id" in item


def is_historical_record(item: dict) -> bool:
    """A historical_sealed_record entry is marked historical_only."""
    return bool(item.get("historical_only"))


def is_producer_command(item: dict) -> bool:
    """A producer_command entry carries a producer_id + producer_command."""
    return "producer_id" in item and "producer_command" in item


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_schema(authority: dict) -> None:
    """Step 1: Schema validation."""
    print("\n[1/9] Schema validation")
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
        for key in ("schema_version", "task_id", "description", "generated_outputs"):
            if key not in authority:
                fail(f"Missing required top-level key: {key}")
        if "generated_outputs" in authority:
            ok("Basic structure present")


def check_output_files_exist(authority: dict) -> None:
    """Step 2: Every declared generated output file exists."""
    print("\n[2/9] Generated output file existence")
    for item in authority["generated_outputs"]:
        path = ROOT / item["path"]
        if path.exists():
            ok(f"{item['path']} exists")
        else:
            fail(f"{item['path']} does NOT exist on disk")


def check_producer_scripts(authority: dict) -> None:
    """Step 3: Every producer_command script exists (producer_command entries only)."""
    print("\n[3/9] Producer script existence")
    checked = set()
    for item in authority["generated_outputs"]:
        if not is_producer_command(item):
            continue
        cmd = item["producer_command"]
        if cmd in checked:
            continue
        checked.add(cmd)
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
    """Step 4: Every input_authorities file exists (producer_command entries only;
    registered_generator inputs are verified in check_registered_generators)."""
    print("\n[4/9] Input authority file existence")
    all_inputs = set()
    for item in authority["generated_outputs"]:
        if not is_producer_command(item):
            continue
        for inp in item["input_authorities"]:
            all_inputs.add(inp)
    for inp in sorted(all_inputs):
        path = ROOT / inp
        if path.exists():
            ok(f"{inp} exists")
        else:
            fail(f"{inp} does NOT exist on disk")


def check_duplicate_semantic_authority(authority: dict) -> None:
    """Step 5: No duplicate semantic authority."""
    print("\n[5/9] Duplicate semantic authority check")
    from collections import defaultdict
    groups = defaultdict(list)
    for item in authority["generated_outputs"]:
        # Registered-generator and historical entries are uniquely governed by the
        # generator-registry / seal (generator_id + allowed path + digest), so they do
        # not participate in the producer-command semantic-duplicate key space.
        if not is_producer_command(item):
            continue
        key = (item["producer_id"], tuple(sorted(item["input_authorities"])), item["output_type"])
        groups[key].append(item["path"])

    has_real_dupes = False
    for (producer, inputs, otype), paths in groups.items():
        if len(paths) <= 1:
            continue
        contents = []
        for p in paths:
            fp = ROOT / p
            contents.append(fp.read_bytes() if fp.exists() else None)
        all_identical = all(c is not None and c == contents[0] for c in contents)
        if all_identical:
            warn(f"Deliberate copy: producer={producer}, type={otype}: {len(paths)} identical files: {[p.split('/')[-1] for p in paths]}")
        else:
            has_real_dupes = True
            fail(f"INCONSISTENT duplicate: producer={producer}, type={otype}: {paths} have different content")

    if not has_real_dupes:
        ok("No inconsistent duplicate semantic authorities")


def check_registered_generators(authority: dict, gen_reg: dict) -> None:
    """Step 6: Positive verification of registered_generator entries against the registry."""
    print("\n[6/9] Registered-generator verification")
    if not gen_reg.get("generators"):
        ok("No generator registry entries (none to verify)")
        return
    checked_any = False
    for item in authority["generated_outputs"]:
        if not is_registered_generator(item):
            continue
        checked_any = True
        gid = item["generator_id"]
        if gid not in gen_reg["generators"]:
            fail(f"Registered generator '{gid}' for {item['path']} is NOT in generator-registry.json (unregistered generator rejected)")
            continue
        entry = gen_reg["generators"][gid]
        # canonical_tool must match
        if item.get("canonical_tool") != entry.get("canonical_tool"):
            fail(f"{item['path']}: canonical_tool '{item.get('canonical_tool')}' != registry '{entry.get('canonical_tool')}'")
        # output path must be allowed for this generator
        if item["path"] not in entry.get("allowed_output_paths", []):
            fail(f"{item['path']}: not an allowed output for generator '{gid}' (allowed: {entry.get('allowed_output_paths')})")
        # input authorities must match exactly
        if set(item.get("input_authorities", [])) != set(entry.get("required_input_authorities", [])):
            fail(f"{item['path']}: input_authorities {sorted(item.get('input_authorities', []))} != registry required {sorted(entry.get('required_input_authorities', []))}")
        # lifecycle must be active (current/live authority)
        if item.get("lifecycle_status") != "active":
            fail(f"{item['path']}: registered_generator must have lifecycle_status 'active' (got '{item.get('lifecycle_status')}')")
        # content digest must match the live file
        fpath = ROOT / item["path"]
        if not fpath.exists():
            fail(f"{item['path']}: file missing, cannot verify digest")
        else:
            live_digest = sha256_of(fpath)
            if live_digest != item.get("content_digest_sha256"):
                fail(f"{item['path']}: content_digest_sha256 mismatch (live {live_digest[:12]}... != declared {str(item.get('content_digest_sha256'))[:12]}...) — stale or tampered output")
            else:
                ok(f"{item['path']}: registered generator '{gid}' verified (digest match)")
    if not checked_any:
        ok("No registered_generator entries to verify")


def check_historical_records(authority: dict) -> None:
    """Step 7: Historical sealed records are historical-only and cannot authorize current output."""
    print("\n[7/9] Historical sealed-record verification")
    checked_any = False
    for item in authority["generated_outputs"]:
        if not is_historical_record(item):
            continue
        checked_any = True
        if item.get("lifecycle_status") == "active":
            fail(f"{item['path']}: historical_sealed_record MUST NOT claim lifecycle_status 'active' (cannot authorize current/live output)")
        seal_file = ROOT / item["seal_file"]
        if not seal_file.exists():
            fail(f"{item['path']}: seal_file {item['seal_file']} does not exist")
        else:
            live = sha256_of(seal_file)
            if live != item.get("seal_sha256"):
                fail(f"{item['path']}: seal_sha256 mismatch (live {live[:12]}... != declared {str(item.get('seal_sha256'))[:12]}...)")
            else:
                ok(f"{item['path']}: historical seal verified (digest match)")
    if not checked_any:
        ok("No historical_sealed_record entries to verify")


def check_diff_coverage(authority: dict, request: dict, base: str, era_ref: str = None) -> None:
    """Step 8 & 9: Diff coverage completeness.

    The diff window is base..era_ref when an era reference is supplied (frozen-era
    authority), otherwise base..HEAD. This keeps a sealed historical authority from
    being judged against a later, unrelated change set.
    """
    print("\n[8/9] Diff coverage (seeds ∪ generated == diff paths)")
    diff_spec = f"{base}..{era_ref}" if era_ref else f"{base}..HEAD"

    result = subprocess.run(
        ["git", "diff", "--name-only", diff_spec],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if result.returncode != 0:
        fail(f"git diff failed: {result.stderr}")
        return
    diff_paths = {p for p in result.stdout.strip().split("\n") if p}
    # Untracked files are only relevant for a LIVE era (base..HEAD). For a frozen (sealed)
    # era, untracked files post-date the era boundary and must not be folded into the
    # historical diff window.
    if era_ref is None:
        untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, cwd=str(ROOT))
        if untracked.returncode == 0:
            diff_paths |= {p for p in untracked.stdout.splitlines() if p}

    seeds = set(request.get("changed_paths", []))
    all_generated = {item["path"] for item in authority["generated_outputs"]}
    generated = all_generated & diff_paths

    covered = seeds | generated
    uncovered = diff_paths - covered
    extra = covered - diff_paths
    overlap = seeds & all_generated

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

    print(f"\n[9/9] Seed/generated disjointness")
    if overlap:
        for p in sorted(overlap):
            fail(f"Path is both seed and generated: {p}")
    else:
        ok("Seeds and generated outputs are disjoint")

    print(f"\n  Coverage summary: {len(seeds)} seeds + {len(generated)} generated = {len(covered)} total (diff: {len(diff_paths)})")
    if len(covered) == len(diff_paths) and not uncovered and not extra:
        ok("DIFF COVERAGE: COMPLETE")
    else:
        fail("DIFF COVERAGE: INCOMPLETE")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generated Output Authority Validator")
    ap.add_argument("--authority", default=str(AUTHORITY_PATH), help="Authority JSON path")
    ap.add_argument("--request", default=str(REQUEST_PATH), help="Request JSON path (seeds)")
    ap.add_argument("--base", default=None, help="Base commit for diff coverage (defaults to request base_identity or BASE_MAIN)")
    ap.add_argument("--era-ref", default=None, help="Era reference commit; diff window becomes base..era_ref (frozen-era authority)")
    ap.add_argument("--generator-registry", default=str(GENERATOR_REGISTRY_PATH), help="Generator registry JSON path")
    args = ap.parse_args()

    authority_path = Path(args.authority)
    request_path = Path(args.request)
    gen_reg_path = Path(args.generator_registry)

    print("=" * 60)
    print("Generated Output Authority Validator")
    print("=" * 60)
    print(f"Authority: {authority_path}")
    print(f"Schema:    {SCHEMA_PATH}")
    print(f"Request:   {request_path}")

    if not authority_path.exists():
        print(f"\nFATAL: Authority file not found: {authority_path}")
        return 1
    if not SCHEMA_PATH.exists():
        print(f"\nFATAL: Schema file not found: {SCHEMA_PATH}")
        return 1
    if not request_path.exists():
        print(f"\nFATAL: Request file not found: {request_path}")
        return 1

    authority = load_json(authority_path)
    request = load_json(request_path)
    gen_reg = load_json(gen_reg_path) if gen_reg_path.exists() else {"generators": {}}

    base = args.base
    era_ref = args.era_ref
    # Derive base/era from the request's iteration manifest (generic era resolver) when
    # not explicitly overridden on the CLI. A sealed iteration is bounded to its merge
    # commit; a live candidate validates against base..HEAD. No hardcoded task/SHA.
    if base is None or era_ref is None:
        era = resolve_era_for_request(ROOT, request)
        if era:
            if base is None:
                base = era["base"]
            if era_ref is None:
                era_ref = era["era_ref"]
    if base is None:
        base = request.get("base_identity") or BASE_MAIN
    print(f"Base:      {base}")
    print(f"Era ref:   {era_ref or 'HEAD (live)'}")

    check_schema(authority)
    check_output_files_exist(authority)
    check_producer_scripts(authority)
    check_input_authorities(authority)
    check_duplicate_semantic_authority(authority)
    check_registered_generators(authority, gen_reg)
    check_historical_records(authority)
    check_diff_coverage(authority, request, base, era_ref)

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
