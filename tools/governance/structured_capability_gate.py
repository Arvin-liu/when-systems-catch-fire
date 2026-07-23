#!/usr/bin/env python3
"""Shared fail-closed engine for evidence-bound structured capability bundles.

repair-r2: closes RB09-ENGINE-PATH-CONTAINMENT, RB09-MANDATORY-GIT-OBJECT-BINDING,
RB09-EXACT-HEAD-NONRESOLUTION.
repair-r3: ACTUALLY closes RB09-CALLER-ASSERTED-SEMANTICS by delegating rule
semantics to a per-capability evaluator (CONFIG["evaluator"]); rule predicates are
recomputed from record values + authoritative evidence bytes, never from caller
asserted facts[rid]/rule_assertions[rid].status.

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
  * rule satisfaction is RECOMPUTED from registered, git-resolved evidence by a
    per-capability evaluator (CONFIG["evaluator"]); caller asserted
    facts[rid]==True / status=="PASS" are IGNORED (RB09-CALLER-ASSERTED-SEMANTICS).
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


# ---------------------------------------------------------------------------
# Semantic evaluator layer (repair-r3: RB09-CALLER-ASSERTED-SEMANTICS).
#
# RuleResult  = {"rule_id", "verdict": "PASS"|"FAIL", "used_evidence": list[str], "detail": str}
# EvalReport  = {"capability", "results": dict[rule_id, RuleResult]}  (keyed exactly by config["rules"])
#
# The engine never trusts caller-asserted facts[rid] / rule_assertions[rid].status;
# it delegates rule semantics to a per-capability evaluator callable carried in
# CONFIG["evaluator"] (req-7), with an optional registry fallback.
# ---------------------------------------------------------------------------
_EVALUATOR_REGISTRY = {}


def register_evaluator(capability, fn):
    """Register a task-specific evaluator callable for a capability (defense-in-depth).

    ``run()`` prefers ``CONFIG["evaluator"]`` and falls back to this registry.
    """
    _EVALUATOR_REGISTRY[capability] = fn


def _evaluator_layer(config, b, evidence):
    """Req-7 (missing evaluator) / Req-4 (exact-once coverage) / Req-5 (per-rule fail).

    Returns ``None`` when every rule recomputes PASS, else ``(code, name, errors)``.
    """
    cap = config["capability"]
    evaluator = config.get("evaluator") or _EVALUATOR_REGISTRY.get(cap)
    # Req-7: a consumer that imports run without a task-specific evaluator fails closed.
    if not callable(evaluator):
        return 1, "MISSING_EVALUATOR", [
            "consumer imported run without a task-specific evaluator"
        ]
    try:
        report = evaluator(b, config, evidence)
    except Exception as exc:  # recomputation must never raise into a silent pass
        return 6, "EVALUATOR_COVERAGE_INVALID", [
            f"evaluator raised: {type(exc).__name__}: {exc}"
        ]
    results = (report or {}).get("results", {})

    # Req-4: exact-once coverage.
    expected = set(config["rules"])
    got = set(results)
    if got != expected or len(results) != len(expected):
        missing = sorted(expected - got)
        unknown = sorted(got - expected)
        return 6, "EVALUATOR_COVERAGE_INVALID", [
            f"rule set mismatch: missing={missing}, unknown={unknown}"
        ]
    for rid, rr in results.items():
        if not isinstance(rr, dict):
            return 6, "EVALUATOR_COVERAGE_INVALID", [f"{rid}: RuleResult is not a mapping"]
        if rr.get("verdict") not in ("PASS", "FAIL"):
            return 6, "EVALUATOR_COVERAGE_INVALID", [
                f"{rid}: verdict {rr.get('verdict')!r} not in {{PASS, FAIL}}"
            ]
        if not rr.get("used_evidence"):
            return 6, "EVALUATOR_COVERAGE_INVALID", [
                f"{rid}: used_evidence is empty (no evidence actually relied upon)"
            ]

    # Req-5: first failing rule in config order fails closed.
    # 30+index (NOT 10+index) to avoid colliding with claim_ceiling=20 /
    # external_action=21 for 11/12-rule capabilities.
    for index, rid in enumerate(config["rules"]):
        rr = results[rid]
        if rr.get("verdict") == "FAIL":
            return 30 + index, "EVALUATOR_RULE_FAILED", [
                str(rr.get("detail", "")) or f"{rid} recomputation failed"
            ]
    return None


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
    """Fail-closed verification of a single evidence object against real Git.

    Returns a ResolvedEvidence dict carrying the authoritative ``bytes`` (and a
    typed ``decoded``) of ``git show {commit_sha}:{repository_relative_path}``.
    All mandatory-field / path-containment / exact-head / sha256 / blob_sha
    checks from the r2 control set are preserved unchanged.
    """
    re = {
        "evidence_id": eid,
        "declared_role": e.get("declared_role"),
        "record_type": e.get("record_type"),
        "rights_status": e.get("rights_status"),
        "repository_relative_path": e.get("repository_relative_path"),
        "commit_sha": e.get("commit_sha"),
        "blob_sha": e.get("blob_sha"),
        "sha256": e.get("sha256"),
        "exact_head": e.get("exact_head"),
        "bytes": b"",
        "decoded": None,
    }
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
            re["bytes"] = content
            rt = str(e.get("record_type") or "")
            if rt and ("JSON" in rt.upper() or rt.endswith("_JSON") or rt == "JSON"):
                try:
                    re["decoded"] = json.loads(content.decode("utf-8", "replace"))
                except Exception:
                    re["decoded"] = content.decode("utf-8", "replace")
            else:
                re["decoded"] = content.decode("utf-8", "replace")
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
    return re


def _validate_evidence_and_rules(config, b):
    """Returns (code, name, errors, evidence). Recomputes rule satisfaction from evidence.

    ``evidence`` is ``dict[evidence_id, ResolvedEvidence]`` carrying authoritative
    bytes / decoded content for the evaluator layer.
    """
    evidence = {}
    errors = []
    seen = set()
    for e in b.get("evidence_registry", []):
        eid = e.get("evidence_id")
        if eid in seen:
            errors.append(f"{eid}: duplicate evidence id")
        seen.add(eid)
        re = _resolve_evidence(eid, e, errors)
        evidence[eid] = re

    if errors:
        return 4, "EVIDENCE_BINDING_INVALID", errors, evidence

    # RB09-CALLER-ASSERTED-SEMANTICS: recompute from evidence, ignore facts/status.
    assertions = b.get("rule_assertions", [])
    amap = {x.get("rule_id"): x for x in assertions}
    if set(amap) != set(config["rules"]) or len(amap) != len(assertions):
        return 4, "EVIDENCE_BINDING_INVALID", [
            "rule assertion coverage is incomplete or duplicated"
        ], evidence
    for rid in config["rules"]:
        a = amap.get(rid)
        refs = (a.get("evidence_refs") or []) if isinstance(a, dict) else []
        if not refs:
            return (
                5 + config["rules"].index(rid),
                "RULE_BLOCKED",
                [f"{rid}: no evidence_refs (caller-asserted facts/status ignored)"],
                evidence,
            )
        for ref in refs:
            if ref not in evidence:
                return (
                    5 + config["rules"].index(rid),
                    "RULE_BLOCKED",
                    [f"{rid}: evidence {ref} not registered or not git-resolved"],
                    evidence,
                )
    return 0, "GATE_PASS", [], evidence


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
        code, name, errors, evidence = _validate_evidence_and_rules(config, b)
        if code == 0:
            # [NEW evaluator layer] recompute every rule from evidence; caller
            # facts/status are declarations only and are ignored. Inserted AFTER
            # evidence verification and BEFORE the claim-ceiling check.
            el = _evaluator_layer(config, b, evidence)
            if el is not None:
                code, name, errors = el
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
