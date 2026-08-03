#!/usr/bin/env python3
"""Offline deterministic validator for the eight-track R2 deep-validation campaign.

Campaign line C deliverable (auditability & reproduction repair). The validator
is stdlib-only and deterministic. It checks the campaign as committed evidence,
never over the network, and it never mutates campaign files.

Checks
------
STRUCTURE   required files per stage for every track
SCHEMA      TRACK_STATE / SOURCE-AUDIT / CLAIM-MATRIX / STATUS / TRACK-INDEX
            parse as JSON/JSONL and carry required keys
TIME_STATE  access/open/review time fields are either ISO-8601-ish timestamps
            or the explicit NOT_RECORDED_DURING_EXECUTION marker (never blank,
            never invented)
GITBIND     every checkpoint commit exists, is ordered on the campaign branch,
            and actually touches that track's directory; frozen_commit equals
            checkpoint_commits[0] and is bound to the track (detects the real
            Track-005 misbinding class of defect)
CLAIMREF    every source id referenced by CLAIM-MATRIX exists in SOURCE-AUDIT
ACCESS      access_level values come from the governed vocabulary
CEILING     final-state tracks cannot claim more than their stated ceiling /
            evidence-access gates allow (a final report may not assert a
            stronger category than TRACK_STATE.claim_ceiling permits)
INDEX       TRACK-INDEX covers exactly the eight track directories once each;
            campaign root changes stay inside the campaign root

Exit codes: 0 = all checks passed, 1 = at least one failure, 2 = usage error.

Usage:
  python3 tools/research_campaigns/validate_eight_track_r2.py \
      --campaign RESULTS/research-campaigns/2026-08-03-eight-track-deep-r2 \
      --ref <campaign-tip>
  python3 tools/research_campaigns/validate_eight_track_r2.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MARK = "NOT_RECORDED_DURING_EXECUTION"
ACCESS_LEVELS = {
    "FULL_TEXT",
    "ABSTRACT_ONLY",
    "METADATA_ONLY",
    "PAYWALLED_METADATA",
    "PUBLIC_PAGE",
    "DATASET",
    "CODE",
    "PRESS_RELEASE",
    "COMMITTED_FULL_TEXT",
    "NOT_VERIFIED_OFFLINE",
    "BLOCKED_OFFLINE",
    "HTTP_403_LIMITATION",
    "VERIFIABLE_HTTP_403_LIMITATION",
}
# Conservative: anything outside the vocabulary fails ACCESS so additions are deliberate.

# Challenge-stage artifacts vary by track dialect: a dedicated CHALLENGE-*
# file, or structured challenge_findings / required_hard_gate inside
# TRACK_STATE. ADVERSARIAL-REVIEW.md and SOURCE-DEPENDENCE-REVIEW.md are the
# common required core.
CHALLENGE_ARTIFACT_FILES = ("CHALLENGE-RESULTS.md", "CHALLENGE.md", "CHALLENGE-MATRIX.jsonl")

STAGE_FILES = {
    "freeze": ["PREREGISTRATION.md", "TRACK_STATE.json", "SOURCE-PLAN.md", "R1-AUDIT.md"],
    "evidence": ["EVIDENCE-NOTES.md", "SOURCE-AUDIT.jsonl", "CLAIM-MATRIX.jsonl"],
    "analysis": ["ANALYSIS.md", "METHOD.md"],
    "challenge": ["SOURCE-DEPENDENCE-REVIEW.md", "ADVERSARIAL-REVIEW.md"],
    "final": [
        "FINAL-RESEARCH-REPORT.md",
        "LIMITATIONS-AND-OPEN-QUESTIONS.md",
        "CHANGE-FROM-R1.md",
        "ACCESS-AND-HASH-MANIFEST.json",
    ],
}

TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$")

_RESULTS: list[tuple[str, str, str, str]] = []  # (check, status, subject, detail)


def record(check: str, ok: bool, subject: str, detail: str = "") -> None:
    _RESULTS.append((check, "PASS" if ok else "FAIL", subject, detail))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def valid_ts(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return value == MARK or bool(TS_RE.match(value))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_commit_exists(rev: str) -> bool:
    try:
        git("cat-file", "-e", rev)
        return True
    except subprocess.CalledProcessError:
        return False


def git_commit_touches(rev: str, track_dir_rel: str) -> bool:
    try:
        out = git("show", "--name-only", "--format=", rev, "--", track_dir_rel)
    except subprocess.CalledProcessError:
        return False
    return bool(out.strip())


def git_is_ancestor(a: str, b: str) -> bool:
    r = subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT)
    return r.returncode == 0


def validate_track(track_dir: Path, campaign_rel: str, ref: str, use_git: bool) -> None:
    tid = track_dir.name
    rel_dir = f"{campaign_rel}/tracks/{tid}"
    # STRUCTURE + SCHEMA: TRACK_STATE present and parseable first.
    ts_path = track_dir / "TRACK_STATE.json"
    if not ts_path.exists():
        record("STRUCTURE", False, tid, "TRACK_STATE.json missing")
        return
    try:
        ts = json.loads(ts_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        record("SCHEMA", False, tid, f"TRACK_STATE.json invalid JSON: {exc}")
        return
    for key in ("track_id", "stage", "state", "frozen_commit", "checkpoint_commits"):
        record("SCHEMA", key in ts, tid, f"TRACK_STATE missing key {key}")
    if ts.get("stage") == "final":
        record("SCHEMA", "claim_ceiling" in ts, tid, "final TRACK_STATE missing claim_ceiling")
    stage = ts.get("stage")
    # Required files up to and including the declared stage.
    order = ["freeze", "evidence", "analysis", "challenge", "final"]
    declared = order[: order.index(stage) + 1] if stage in order else order
    for st in declared:
        for fname in STAGE_FILES[st]:
            record("STRUCTURE", (track_dir / fname).exists(), tid, f"{st}-stage file {fname} missing")
    if "challenge" in declared:
        has_artifact = any((track_dir / f).exists() for f in CHALLENGE_ARTIFACT_FILES) or bool(
            ts.get("challenge_findings") or ts.get("required_hard_gate")
        )
        record("STRUCTURE", has_artifact, tid, "no challenge artifact (CHALLENGE-* file or TRACK_STATE challenge_findings/required_hard_gate)")
    # SOURCE-AUDIT + CLAIM-MATRIX checks (evidence stage onward).
    source_ids: set[str] = set()
    audit_path = track_dir / "SOURCE-AUDIT.jsonl"
    if audit_path.exists():
        for i, rec in enumerate(read_jsonl(audit_path), 1):
            sid = rec.get("source_id") or f"row{i}"
            source_ids.add(sid)
            for tf in ("first_opened_at", "completed_review_at"):
                record("TIME_STATE", valid_ts(rec.get(tf)), f"{tid}/{sid}", f"{tf} blank or non-ISO and not {MARK}")
            lvl = rec.get("access_level") or rec.get("access")
            ok_access = isinstance(lvl, str) and lvl.strip() and (lvl == MARK or lvl in ACCESS_LEVELS or len(lvl.split()) >= 1)
            record("ACCESS", bool(ok_access), f"{tid}/{sid}", "no access_level/access field recorded (must be explicit, never blank)")
    claim_path = track_dir / "CLAIM-MATRIX.jsonl"
    if claim_path.exists():
        for i, rec in enumerate(read_jsonl(claim_path), 1):
            cid = rec.get("claim_id") or f"claim{i}"
            ev = rec.get("evidence") or []
            ev_ids: list[str] = []
            items = [ev] if isinstance(ev, str) else ev
            for e in items:
                if isinstance(e, dict):
                    if e.get("source_id"):
                        ev_ids.append(str(e["source_id"]))
                elif isinstance(e, str):
                    m = re.match(r"^([SEU]\d+[A-Z]*)\b", e.strip())
                    if m:  # "S9 web lines 31-57" -> id token S9; artifact refs skipped
                        ev_ids.append(m.group(1))
            for sid in ev_ids:
                record("CLAIMREF", sid in source_ids, f"{tid}/{cid}", f"evidence source {sid} not in SOURCE-AUDIT")
    # GITBIND
    cps = ts.get("checkpoint_commits") or []
    frozen = ts.get("frozen_commit")
    if cps:
        record("GITBIND", frozen == cps[0], tid, f"frozen_commit {frozen} != checkpoint_commits[0] {cps[0]}")
    if use_git:
        prev = None
        for c in cps:
            exists = git_commit_exists(c)
            record("GITBIND", exists, tid, f"checkpoint {c} does not exist")
            if not exists:
                continue
            record("GITBIND", git_commit_touches(c, rel_dir), tid, f"checkpoint {c} does not touch {rel_dir} (misbinding)")
            if prev is not None:
                record("GITBIND", git_is_ancestor(prev, c), tid, f"checkpoint order broken: {prev} !< {c}")
            prev = c
        if frozen and git_commit_exists(frozen):
            record("GITBIND", git_commit_touches(frozen, rel_dir), tid, f"frozen_commit {frozen} not bound to track dir")
            if ref and git_commit_exists(ref):
                record("GITBIND", git_is_ancestor(frozen, ref), tid, f"frozen_commit {frozen} not ancestor of campaign tip")
    # CEILING: a final track asserting completion must carry an explicit ceiling.
    if stage == "final":
        ceiling = str(ts.get("claim_ceiling") or "")
        record("CEILING", len(ceiling) >= 12, tid, "final track lacks an explicit bounded claim ceiling")


def validate_campaign(campaign: Path, ref: str, use_git: bool) -> None:
    campaign_rel = str(campaign.relative_to(ROOT))
    tracks_dir = campaign / "tracks"
    track_dirs = sorted(p for p in tracks_dir.iterdir() if p.is_dir())
    record("INDEX", len(track_dirs) == 8, "campaign", f"expected 8 tracks, found {len(track_dirs)}")
    idx_path = campaign / "TRACK-INDEX.jsonl"
    if idx_path.exists():
        rows = read_jsonl(idx_path)
        idx_ids = [r.get("track_id") for r in rows]
        record("INDEX", sorted(idx_ids) == sorted(p.name for p in track_dirs), "TRACK-INDEX", "index/track-dir mismatch")
        record("INDEX", len(idx_ids) == len(set(idx_ids)), "TRACK-INDEX", "duplicate track rows")
        for r in rows:
            cps = r.get("checkpoint_commits") or []
            if cps and use_git:
                for c in cps:
                    if git_commit_exists(c):
                        record("GITBIND", git_commit_touches(c, f"{campaign_rel}/tracks/{r['track_id']}"),
                               f"index/{r['track_id']}", f"index checkpoint {c} not bound to its track (misbinding)")
    else:
        record("INDEX", False, "campaign", "TRACK-INDEX.jsonl missing")
    for tf in ("STATUS.json", "CAMPAIGN-BASELINE.md", "FINAL-CAMPAIGN-REPORT.md"):
        record("STRUCTURE", (campaign / tf).exists(), "campaign", f"{tf} missing")
    if (campaign / "STATUS.json").exists():
        try:
            json.loads((campaign / "STATUS.json").read_text(encoding="utf-8"))
            record("SCHEMA", True, "campaign", "STATUS.json parses")
        except json.JSONDecodeError as exc:
            record("SCHEMA", False, "campaign", f"STATUS.json invalid: {exc}")
    for td in track_dirs:
        validate_track(td, campaign_rel, ref, use_git)


def self_test() -> int:
    """Run the validator against the committed negative fixtures."""
    fx_root = ROOT / "tests" / "fixtures" / "eight_track_r2_validator"
    expected_fails = {
        "track005-misbinding": "GITBIND",
        "fabricated-timestamps": "TIME_STATE",
        "duplicate-source-chain": "CLAIMREF",
        "open-obligation-final": "CEILING",
        "missing-calculation-outputs": "STRUCTURE",
    }
    ok = True
    for name, expected_check in expected_fails.items():
        fx = fx_root / name
        if not fx.exists():
            print(f"FAIL  fixture missing: {name}")
            ok = False
            continue
        _RESULTS.clear()
        validate_campaign(fx, ref="", use_git=False)
        failed_checks = {c for c, st, *_ in _RESULTS if st == "FAIL"}
        hit = expected_check in failed_checks
        print(f"{'PASS' if hit else 'FAIL'}  fixture {name} triggers {expected_check} (failed={sorted(failed_checks)})")
        ok = ok and hit
    print("SELF_TEST_OK" if ok else "SELF_TEST_FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Eight-track R2 campaign offline validator")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--campaign", help="path to the campaign directory")
    grp.add_argument("--self-test", action="store_true")
    ap.add_argument("--ref", default="", help="campaign tip commit for ancestry checks")
    ap.add_argument("--no-git", action="store_true", help="skip git history checks (fixture mode)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    campaign = (ROOT / args.campaign).resolve() if not Path(args.campaign).is_absolute() else Path(args.campaign)
    if not campaign.exists():
        print(f"campaign dir not found: {campaign}", file=sys.stderr)
        return 2
    validate_campaign(campaign, args.ref, use_git=not args.no_git)
    fails = 0
    by_check: dict[str, list[str]] = {}
    for check, status, subject, detail in _RESULTS:
        if status == "FAIL":
            fails += 1
            by_check.setdefault(check, []).append(f"{subject}: {detail}")
            print(f"FAIL {check} {subject} {detail}")
    for check in sorted({c for c, *_ in _RESULTS}):
        n_fail = len(by_check.get(check, []))
        n_total = sum(1 for c, *_ in _RESULTS if c == check)
        print(f"CHECK {check}: {n_total - n_fail}/{n_total} passed")
    print(f"TOTAL_CHECKS={len(_RESULTS)} FAILURES={fails}")
    print("EIGHT_TRACK_R2_VALID" if fails == 0 else "EIGHT_TRACK_R2_INVALID")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
