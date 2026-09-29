#!/usr/bin/env python3
"""Bind the immutable Task227 Owner Packet and exact frozen formal sources."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TASK227 = ROOT / "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
TASK228 = ROOT / "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0"
PACKET = Path("/tmp/ignition-227-component-isolation-r0/FINAL-OWNER-PACKET")
REFS = PACKET / "reference-m1"
SOURCES = {
    "Task227 protocol": TASK227 / "design/protocol.md",
    "policy schema": TASK227 / "reference/policy-schema.json",
    "official validator": TASK227 / "tools/validate_policy.py",
    "reviewer criteria": TASK227 / "reference/reviewer-criteria.md",
    "validity criteria": TASK227 / "reference/validity-criteria.md",
    "builder prompt": TASK227 / "reference/builder-prompt.md",
    "revision prompt": TASK227 / "revision/prompt.md",
    "revision evaluator criteria": TASK227 / "revision/evaluator/criteria.md",
}
FAMILIES = ["FAMILY01", "FAMILY01", "FAMILY02", "FAMILY02", "FAMILY03", "FAMILY03"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest_path = PACKET / "SHA256SUMS"
listed = {}
for line in manifest_path.read_text(encoding="utf-8").splitlines():
    if line.strip():
        sha, rel = line.split("  ", 1)
        listed[rel] = sha
actual = {
    p.relative_to(PACKET).as_posix()
    for p in PACKET.rglob("*")
    if p.is_file() and p.name != "SHA256SUMS"
}
assert len(listed) == 100 and actual == set(listed), "packet inventory differs from 100-entry manifest"
for rel, expected in listed.items():
    assert digest(PACKET / rel) == expected, f"packet checksum mismatch: {rel}"

freeze = json.loads((TASK227 / "freeze/freeze-manifest.json").read_text(encoding="utf-8"))
freeze_rows = freeze["frozen_files"]
frozen_bad = [
    item["path"] for item in freeze_rows
    if not (ROOT / item["path"]).is_file()
    or digest(ROOT / item["path"]) != item["sha256"]
]
external_rows = freeze["external_m0_e1_inputs"]
external_bad = [
    item["path"] for item in external_rows
    if not (ROOT / item["path"]).is_file()
    or digest(ROOT / item["path"]) != item["sha256"]
]
assert not frozen_bad and not external_bad, "Task227 frozen contract/source checksum mismatch"

review_a = json.loads((REFS / "policy-reviewer-A.json").read_text(encoding="utf-8"))
review_b = json.loads((REFS / "policy-reviewer-B.json").read_text(encoding="utf-8"))
lock = json.loads((REFS / "reference-policy-validity-lock.json").read_text(encoding="utf-8"))
a = {r["ref"]: r["USABLE"] for r in review_a["results"]}
b = {r["ref"]: r["USABLE"] for r in review_b["policies"]}
locked = {r["ref"]: r["usable"] for r in lock["results"]}
assert review_a["reviewed_policy_count"] == 6 and review_b["fixed_denominator"] == 6
assert sum(a[r] and b[r] and locked[r] for r in locked) == 3
assert lock["usable_count"] == 3
lock_sidecar = (REFS / "reference-policy-validity-lock.sha256").read_text(encoding="utf-8").split()
assert lock_sidecar[0] == digest(REFS / "reference-policy-validity-lock.json")
assert set(a) == set(b) == set(locked)
assert all(locked[ref] == (a[ref] and b[ref]) for ref in locked)

with (REFS / "post-review-official-validator-audit.csv").open(newline="", encoding="utf-8") as f:
    audits = list(csv.DictReader(f))
assert len(audits) == 6
assert all(row["validator_status"] == "TASK227_POLICY_INVALID" for row in audits)
assert all(row["review_scores_modified"] == "false" for row in audits)

policy_rows = []
for i, row in enumerate(audits, 1):
    path = REFS / f"REF-0{i}.json"
    sha = digest(path)
    assert row["policy_sha256"] == sha
    policy_rows.append((path.name, sha, FAMILIES[i - 1], row["validator_exit_code"], row["detail"]))

review_rows = [
    ("policy-reviewer-A.json", digest(REFS / "policy-reviewer-A.json")),
    ("policy-reviewer-B.json", digest(REFS / "policy-reviewer-B.json")),
]
lock_rows = [
    ("reference-policy-validity-lock.json", digest(REFS / "reference-policy-validity-lock.json")),
    ("reference-policy-validity-lock.sha256", digest(REFS / "reference-policy-validity-lock.sha256")),
]
audit_sha = digest(REFS / "post-review-official-validator-audit.csv")

lines = [
    "# Task228 Task227 evidence-binding receipt",
    "",
    "- Owner Packet path: `/tmp/ignition-227-component-isolation-r0/FINAL-OWNER-PACKET/`",
    f"- Packet manifest: `SHA256SUMS`; SHA256=`{digest(manifest_path)}`",
    f"- Inventory: {len(listed)} manifest-listed files; every entry verified; no unlisted or missing files (excluding the manifest file itself).",
    f"- Task227 PR: #237; OPEN + DRAFT + UNMERGED; head `7d979b1aa523030b16f773a973477cbfca1e4513`.",
    "- Current exact-head CI: 4/4 success: foundation-validation run 36420663470; repository-path-accounting-preflight run 36420663792; architecture-pages run 36420663646; q33-governance-validation run 36420663752.",
    f"- Task227 freeze manifest: `{(TASK227 / 'freeze/freeze-manifest.json').relative_to(ROOT)}`; SHA256=`{digest(TASK227 / 'freeze/freeze-manifest.json')}`.",
    f"- Frozen files verified: {len(freeze_rows)}/{len(freeze_rows)}; M0/E1 source inputs verified: {len(external_rows)}/{len(external_rows)}.",
    "- The reference-policy validity-lock sidecar verifies the lock JSON.",
    "- Locked human review: 3/6 usable (REF-01, REF-04, REF-05); both raw reviewer sheets and the non-reconciled lock agree.",
    "- Official validator audit: 0/6 pass; all six audit rows say TASK227_POLICY_INVALID and review_scores_modified=false.",
    "",
    "## Immutable reference policies",
    "",
    "| File | SHA256 | Family | Official exit | Frozen audit first failure |",
    "|---|---|---|---:|---|",
]
for name, sha, family, exit_code, detail in policy_rows:
    lines.append(f"| `{name}` | `{sha}` | {family} | {exit_code} | {detail} |")
lines += ["", "## Locked reviewer and validator records", "",
          "| File | SHA256 |", "|---|---|"]
for name, sha in review_rows + lock_rows:
    lines.append(f"| `{name}` | `{sha}` |")
lines.append(f"| `post-review-official-validator-audit.csv` | `{audit_sha}` |")
lines += ["", "## Exact Task227 contract source paths and hashes", "",
          "| Source | Path | SHA256 |", "|---|---|---|"]
for label, path in SOURCES.items():
    lines.append(f"| {label} | `{path.relative_to(ROOT)}` | `{digest(path)}` |")
lines += [
    "",
    "No Task227 policy, reviewer sheet, lock, aggregate, result, target, or validator source was modified. The Task228 diagnostic read only the six raw reference policies, the frozen schema/validator, and frozen family M0/E1 inputs; it did not read A/B/C target files.",
    "",
]
(TASK228 / "evidence-binding-receipt.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({
    "manifest_entries": len(listed), "manifest_sha256": digest(manifest_path),
    "frozen_files_verified": len(freeze_rows), "external_m0_e1_verified": len(external_rows),
    "human_usable": sum(locked.values()), "official_validator_pass": sum(
        row["validator_status"] == "TASK227_POLICY_VALID" for row in audits),
    "policy_hashes": len(policy_rows), "output": str(TASK228 / "evidence-binding-receipt.md"),
}, ensure_ascii=False))
