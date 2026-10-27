#!/usr/bin/env python3
"""Sync 121Q33-request.json coverage with the real Q33 PR diff surface.

Derives the request's `changed_paths` (seed paths) from the actual git diff
`base..HEAD` (base taken from the Q33 iteration manifest), excluding the Q33
generated outputs declared in the same manifest's propagation_closure. This keeps
the request's coverage in lock-step with the real PR surface without hardcoding any
file count, task id, or commit SHA.

The same era/base is resolved generically by tools/operations/era_resolver.py so the
diff-coverage gate, the authority validator, and this sync stay consistent.
"""

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent
MANIFEST = REPO / "data" / "operations" / "iterations" / "121Q33.json"
REQUEST = REPO / "data" / "operations" / "propagation" / "121Q33-request.json"


def _git(args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=str(REPO)
    ).stdout.strip()


def main() -> int:
    if not MANIFEST.exists() or not REQUEST.exists():
        print("ERROR: Q33 manifest or request not found", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pc = manifest.get("propagation_closure", {})
    # Q33 generated outputs are data-driven from the manifest (closure/residue/delta/report).
    generated = {
        pc.get("closure_path"),
        pc.get("residue_path"),
        pc.get("system_map_delta_path"),
        pc.get("impact_report_path"),
    }
    generated.discard(None)

    # Any path already declared as a generated output in the authority (e.g. Q32I-era
    # outputs that were also touched on the Q33 branch) must NOT be double-counted as a
    # seed. Subtract the full set of authority-generated paths from the seed surface.
    authority = json.loads(
        (REPO / "data" / "operations" / "generated-output-authority.json").read_text(encoding="utf-8")
    )
    authority_generated = {item.get("path") for item in authority.get("generated_outputs", [])}
    generated |= authority_generated

    base = (manifest.get("branch_pr", {}).get("base_head")
            or manifest.get("verified_start", {}).get("main_head"))
    if not base:
        print("ERROR: cannot resolve Q33 base commit from manifest", file=sys.stderr)
        return 1

    committed = {p for p in _git(["diff", "--name-only", f"{base}..HEAD"]).splitlines() if p}
    untracked = {p for p in _git(["ls-files", "--others", "--exclude-standard"]).splitlines() if p}
    diff_paths = committed | untracked

    seeds = sorted(diff_paths - generated)
    generated_in_diff = sorted(g for g in generated if g in diff_paths)

    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    request["base_identity"] = base
    # Live candidate: head is externally attested; validator uses base..HEAD (live diff).
    request["head_identity"] = "external_exact_head_attestation"
    request["changed_paths"] = seeds

    REQUEST.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"base:            {base}")
    print(f"diff paths:      {len(diff_paths)}")
    print(f"seed (changed):  {len(seeds)}")
    print(f"generated:       {len(generated_in_diff)}")
    print(f"covered total:   {len(seeds) + len(generated_in_diff)}")
    if len(seeds) + len(generated_in_diff) != len(diff_paths):
        print("WARN: covered total != diff paths", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
