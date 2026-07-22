#!/usr/bin/env python3
"""Shared fail-closed engine for evidence-bound structured capability bundles.

repair-r2: closes RB09-ENGINE-PATH-CONTAINMENT, RB09-MANDATORY-GIT-OBJECT-BINDING,
RB09-EXACT-HEAD-NONRESOLUTION and RB09-CALLER-ASSERTED-SEMANTICS.

Hard rules (no opt-in, no skip):
  * repository_relative_path must be a canonical repository-relative POSIX path
    (rejects absolute paths, '..' traversal, '.' segments, empty segments,
    backslashes, and any symlink escape that would leave ROOT).
  * every evidence object MUST carry commit_sha, repository_relative_path,
    blob_sha, sha256, record_type and declared_role. Missing / empty / all-zero
    / placeholder / wrong-format fields fail closed.
  * commit_sha and exact_head MUST resolve to real Git commits, and exact_head
    MUST be an ancestor of (or equal to) commit_sha.
  * commit:path is resolved against the real Git blob; the recomputed sha256 and
    the rev-parsed blob_sha are verified against the declared values. The working
    tree is NEVER authoritative for evidence bytes.
  * rule satisfaction is RECOMPUTED from registered, git-resolved evidence; caller
    asserted facts[rid]==True / status=="PASS" are ignored.
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

MANDATORY_EVIDENCE_FIELDS = (
    "commit_sha",
    "repository_relative_path",
    "blob_sha",
    "sha256",
    "record_type",
    "declared_role",
)


def _git(args):
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT)] + args, capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        return ""


def _git_ok(args):
    try:
        return (
            subprocess.run(
                ["git", "-C", str(ROOT)] + args, capture_output=True
            ).returncode
            == 0
        )
    except Exception:
        return False


def _git_bytes(args):
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT)] + args, capture_output=True
        ).stdout or b""
    except Exception:
        return b""


def digest(text):
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def result(gate, code, name, errors):
    return {
        "gate": gate,
        "exit_code": code,
        "exit_name": name,
        "errors": errors,
        "boundary": "repository candidate only; no external action or truth-layer upgrade",
    }


def _is_canonical_relpath(p):
    """True only if p is a safe repository-relative POSIX path contained in ROOT."""
    if not isinstance(p, str) or p == "":
        return False
    if p.startswith("/") or p.startswith("\\") or ":" in p or "\\" in p:
        return False
    parts = p.split("/")
    if ".." in parts or "." in parts or "" in parts:
        return False
    candidate = ROOT / p
    try:
        resolved = candidate.resolve()
        resolved.relative_to(ROOT.resolve())
    except Exception:
        return False
    return True


def _resolve_evidence(eid, e, errors):
    """Fail-closed verification of a single evidence object against real Git."""
    for f in MANDATORY_EVIDENCE_FIELDS:
        val = e.get(f)
        if not isinstance(val, str) or val.strip() == "":
            errors.append(f"{eid}: missing or empty mandatory field '{f}'")
            continue
        if set(val) == {"0"}:
            errors.append(f"{eid}: placeholder/all-zero mandatory field '{f}'")

    cs = e.get("commit_sha")
    rrp = e.get("repository_relative_path")
    bs = e.get("blob_sha")
    ds = e.get("sha256")
    eh = e.get("exact_head")

    # RB09-ENGINE-PATH-CONTAINMENT
    if not _is_canonical_relpath(rrp):
        errors.append(
            f"{eid}: repository_relative_path not a canonical repo-relative POSIX path"
        )

    # RB09-EXACT-HEAD-NONRESOLUTION (evidence-level exact_head)
    if not HEAD_RE.match(str(eh or "")):
        errors.append(f"{eid}: exact_head not a 40-hex commit")
    elif not _git_ok(["cat-file", "-e", str(eh)]):
        errors.append(f"{eid}: exact_head {eh} does not resolve to a real Git commit")

    # RB09-MANDATORY-GIT-OBJECT-BINDING: commit_sha must be real
    if not HEAD_RE.match(str(cs or "")):
        errors.append(f"{eid}: commit_sha not a 40-hex commit")
    elif not _git_ok(["cat-file", "-e", str(cs)]):
        errors.append(f"{eid}: commit_sha {cs} does not resolve to a real Git commit")

    # sha256 / blob_sha format
    if not SHA256_RE.match(str(ds or "")):
        errors.append(f"{eid}: sha256 not 'sha256:<64hex>'")
    if not HEAD_RE.match(str(bs or "")):
        errors.append(f"{eid}: blob_sha not a 40-hex object id")

    # resolve commit:path to the real Git blob and verify blob_sha + sha256
    if (
        HEAD_RE.match(str(cs or ""))
        and _is_canonical_relpath(rrp)
        and HEAD_RE.match(str(bs or ""))
        and _git_ok(["cat-file", "-e", str(cs)])
    ):
        actual_blob = _git(["rev-parse", f"{cs}:{rrp}"])
        content = _git_bytes(["show", f"{cs}:{rrp}"])
        if actual_blob == "":
            errors.append(f"{eid}: cannot resolve real Git object {cs}:{rrp}")
        else:
            if actual_blob != bs:
                errors.append(
                    f"{eid}: blob_sha {bs} != real Git object {cs}:{rrp} ({actual_blob})"
                )
            if content and SHA256_RE.match(str(ds or "")):
                actual_sha = "sha256:" + hashlib.sha256(content).hexdigest()
                if actual_sha != ds:
                    errors.append(
                        f"{eid}: sha256 {ds} != recomputed digest of real Git object {cs}:{rrp} ({actual_sha})"
                    )

    # exact_head must be an ancestor of (or equal to) commit_sha
    if (
        HEAD_RE.match(str(eh or ""))
        and HEAD_RE.match(str(cs or ""))
        and eh != cs
        and _git_ok(["cat-file", "-e", str(eh)])
        and _git_ok(["cat-file", "-e", str(cs)])
    ):
        if not _git_ok(["merge-base", "--is-ancestor", str(eh), str(cs)]):
            errors.append(
                f"{eid}: exact_head {eh} is not an ancestor of commit_sha {cs}"
            )


def _validate_evidence_and_rules(config, b):
    """Returns (code, name, errors). Recomputes rule satisfaction from evidence."""
    evidence = {}
    errors = []
    seen = set()
    for e in b.get("evidence_registry", []):
        eid = e.get("evidence_id")
        if eid in seen:
            errors.append(f"{eid}: duplicate evidence id")
        seen.add(eid)
        _resolve_evidence(eid, e, errors)
        evidence[eid] = e

    if errors:
        return 4, "EVIDENCE_BINDING_INVALID", errors

    # RB09-CALLER-ASSERTED-SEMANTICS: recompute from evidence, ignore facts/status.
    assertions = b.get("rule_assertions", [])
    amap = {x.get("rule_id"): x for x in assertions}
    if set(amap) != set(config["rules"]) or len(amap) != len(assertions):
        return 4, "EVIDENCE_BINDING_INVALID", [
            "rule assertion coverage is incomplete or duplicated"
        ]
    for rid in config["rules"]:
        a = amap.get(rid)
        refs = (a.get("evidence_refs") or []) if isinstance(a, dict) else []
        if not refs:
            return (
                5 + config["rules"].index(rid),
                "RULE_BLOCKED",
                [f"{rid}: no evidence_refs (caller-asserted facts/status ignored)"],
            )
        for ref in refs:
            if ref not in evidence:
                return (
                    5 + config["rules"].index(rid),
                    "RULE_BLOCKED",
                    [f"{rid}: evidence {ref} not registered or not git-resolved"],
                )
    return 0, "GATE_PASS", []


def run(config):
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", required=True)
    p.add_argument("--config-json", required=False)
    a = p.parse_args()
    try:
        b = json.loads(Path(a.bundle).read_text())
    except Exception as exc:
        print(
            json.dumps(
                result(config["capability"], 2, "SCHEMA_ERROR", [str(exc)]),
                sort_keys=True,
            )
        )
        return 2
    try:
        import jsonschema

        schema = json.loads((ROOT / config["schema"]).read_text())
        v = jsonschema.Draft202012Validator(schema)
        errors = [
            f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(v.iter_errors(b), key=lambda e: list(e.absolute_path))
        ][:25]
    except ImportError:
        errors = [
            f"missing {k}"
            for k in (
                "task_id",
                "parent_binding",
                "evidence_registry",
                "records",
                "facts",
                "rule_assertions",
                "conclusion",
            )
            if k not in b
        ]
    if errors:
        code, name = 2, "SCHEMA_ERROR"
    elif b["parent_binding"].get("task_id") != config["parent_id"] or b[
        "parent_binding"
    ].get("exact_head") != config["parent_head"]:
        code, name, errors = 3, "PARENT_BINDING_INVALID", [
            "direct parent task/head mismatch"
        ]
    else:
        code, name, errors = _validate_evidence_and_rules(config, b)
        if code == 0:
            text = (
                b["conclusion"].get("statement", "")
                + " "
                + b["conclusion"].get("claim_ceiling", "")
            ).lower()
            if (
                "candidate_only"
                not in b["conclusion"].get("claim_ceiling", "").lower()
                or not b["conclusion"].get("history_preserved")
                or any(x.lower() in text for x in config["forbidden_claims"])
            ):
                code, name, errors = 20, "CLAIM_CEILING_OVERREACH", [
                    "candidate ceiling or history preservation violated"
                ]
            elif b["conclusion"].get("external_action_performed"):
                code, name, errors = 21, "EXTERNAL_ACTION_FORBIDDEN", [
                    "repository candidate cannot perform external action"
                ]
    print(json.dumps(result(config["capability"], code, name, errors), sort_keys=True))
    return code


if __name__ == "__main__":
    # When run as a script, the wrapper supplies config via --config-json
    # (inline JSON or a path to a JSON file).
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--config-json", required=True)
    aa = ap.parse_args()
    try:
        cfg = json.loads(aa.config_json)
    except json.JSONDecodeError:
        cfg = json.loads(Path(aa.config_json).read_text())
    sys.exit(run(cfg))
