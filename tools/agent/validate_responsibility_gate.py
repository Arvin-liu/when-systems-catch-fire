#!/usr/bin/env python3
"""Q35 Responsibility-Authority-Action-Trace Gate — fail-closed validator/CLI.

Decides whether a governed action may proceed, and whether a trajectory is intact.
Repository governance only; NEVER adjudicates real-world legal/moral responsibility.

Stable exit codes (machine-readable, never free-text PASS):
  0  GATE_PASS
  2  SCHEMA_ERROR
  3  ACTOR_UNRESOLVABLE
  4  GRANT_UNRESOLVABLE
  5  GRANT_EXPIRED_OR_REVOKED
  6  SCOPE_BREACH                (action outside grant allowed_action_types / resource_scope)
  7  SELF_GRANT                  (grantor == grantee, self-awarded authority)
  8  MODEL_NAME_AS_AUTHORITY     (authority_source is a bare model name, not a resolvable source)
  9  BROKEN_DELEGATION           (delegation forbidden / chain broken)
  10 CLAIM_NOT_COMMITTED         (action relies on a non-committed Q34 claim)
  11 CLAIM_CEILING_BREACH        (action intent exceeds the claim ceiling)
  12 SEPARATION_OF_DUTY_VIOLATION(self propose/authorize/execute/verify where independence required)
  13 STALE_EXACT_HEAD            (action bound to a different/old head)
  14 TRAJECTORY_INTEGRITY_FAIL   (broken hash chain / reorder / delete / backfill / tamper)
  15 Q33_GATE_BYPASS             (Q35 authorizes publishing material the Q33 gate rejects)
  16 SILENT_HISTORY_REWRITE      (rollback/failure/deletion not preserved as a new event)
  17 UNRESOLVED_RESPONSIBILITY_FORCED (many-hands forced into a single fake owner)

Usage:
  python tools/agent/validate_responsibility_gate.py --bundle <bundle.json> \
      [--current-main-head <sha>] [--claims <claims.json>] [--q33-rejects <path>] \
      [--report <out.json>]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent.parent

GATE_PASS = 0
SCHEMA_ERROR = 2
ACTOR_UNRESOLVABLE = 3
GRANT_UNRESOLVABLE = 4
GRANT_EXPIRED_OR_REVOKED = 5
SCOPE_BREACH = 6
SELF_GRANT = 7
MODEL_NAME_AS_AUTHORITY = 8
BROKEN_DELEGATION = 9
CLAIM_NOT_COMMITTED = 10
CLAIM_CEILING_BREACH = 11
SEPARATION_OF_DUTY_VIOLATION = 12
STALE_EXACT_HEAD = 13
TRAJECTORY_INTEGRITY_FAIL = 14
Q33_GATE_BYPASS = 15
SILENT_HISTORY_REWRITE = 16
UNRESOLVED_RESPONSIBILITY_FORCED = 17
UNKNOWN_CLAIM = 18
UNKNOWN_GRANTOR = 19
CLAIM_BINDING_MISMATCH = 20
GRANT_BINDING_MISMATCH = 21
PLACEHOLDER_AUTHORITY = 22
NONCANONICAL_GRANT = 23

EXIT_NAMES = {v: k for k, v in {
    "GATE_PASS": 0, "SCHEMA_ERROR": 2, "ACTOR_UNRESOLVABLE": 3, "GRANT_UNRESOLVABLE": 4,
    "GRANT_EXPIRED_OR_REVOKED": 5, "SCOPE_BREACH": 6, "SELF_GRANT": 7,
    "MODEL_NAME_AS_AUTHORITY": 8, "BROKEN_DELEGATION": 9, "CLAIM_NOT_COMMITTED": 10,
    "CLAIM_CEILING_BREACH": 11, "SEPARATION_OF_DUTY_VIOLATION": 12, "STALE_EXACT_HEAD": 13,
    "TRAJECTORY_INTEGRITY_FAIL": 14, "Q33_GATE_BYPASS": 15, "SILENT_HISTORY_REWRITE": 16,
    "UNRESOLVED_RESPONSIBILITY_FORCED": 17, "UNKNOWN_CLAIM": 18,
    "UNKNOWN_GRANTOR": 19, "CLAIM_BINDING_MISMATCH": 20,
    "GRANT_BINDING_MISMATCH": 21, "PLACEHOLDER_AUTHORITY": 22,
    "NONCANONICAL_GRANT": 23}.items()}

# Bare model-name patterns that are NOT a resolvable authority source
MODEL_NAME_PATTERNS = ("gpt", "claude", "kimi", "hy3", "deepseek", "qwen", "glm", "llama", "grok", "gemini")
REAL_WORLD_TOKENS = ["global", "worldwide", "all jurisdictions", "proven compliant",
                     "legal compliance proven", "real-world truth", "guaranteed legal",
                     "exhaustive", "universal law"]
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDERS = {"", "null", "none", "todo", "tbd", "unknown", "unknown_as_pass",
                "placeholder", "pending", "n/a", "na"}


def _placeholder(value):
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if normalized in PLACEHOLDERS:
        return True
    return bool(SHA256_RE.fullmatch(normalized)) and set(normalized[7:]) == {"0"}


def _repo_relative_path(raw):
    if _placeholder(raw) or not isinstance(raw, str) or "\\" in raw:
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return None
    return path.as_posix() if path.as_posix() == raw else None


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def _read_git_blob(binding):
    commit = binding.get("exact_commit") if isinstance(binding, dict) else None
    path = _repo_relative_path(binding.get("path") if isinstance(binding, dict) else None)
    if not HEX40_RE.fullmatch(str(commit or "")) or path is None:
        return None, None, "invalid exact commit or noncanonical repository path"
    kind = _git("cat-file", "-t", commit)
    if kind.returncode or kind.stdout.strip() != b"commit":
        return None, None, f"exact commit {commit!r} is not a commit"
    entry = _git("ls-tree", "-z", commit, "--", path)
    rows = [row for row in entry.stdout.split(b"\0") if row]
    exact = []
    for row in rows:
        try:
            meta, encoded_path = row.split(b"\t", 1)
            mode, obj_type, blob = meta.decode("ascii").split()
            if encoded_path.decode("utf-8") == path:
                exact.append((mode, obj_type, blob))
        except (ValueError, UnicodeDecodeError):
            continue
    if len(exact) != 1 or exact[0][0] == "120000" or exact[0][1] != "blob":
        return None, None, f"path {path!r} is missing, ambiguous, symlinked, or not a blob"
    content = _git("cat-file", "blob", exact[0][2])
    if content.returncode:
        return None, None, f"blob {exact[0][2]} cannot be read"
    return content.stdout, exact[0][2], None


def _verify_binding(binding):
    if not isinstance(binding, dict):
        return None, "missing canonical Git binding"
    for field in ("path", "exact_commit", "git_blob", "sha256"):
        if _placeholder(binding.get(field)):
            return None, f"binding {field} is null/empty/placeholder"
    content, blob, error = _read_git_blob(binding)
    if error:
        return None, error
    actual_digest = "sha256:" + hashlib.sha256(content).hexdigest()
    if blob != binding.get("git_blob") or actual_digest != binding.get("sha256"):
        return None, "declared blob/digest does not match actual Git bytes"
    return content, None


def _canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(payload, prev):
    return "sha256:" + hashlib.sha256((_canonical(payload) + "|" + prev).encode()).hexdigest()


def _result(code, errors, decision=None):
    return {"gate": "q35_responsibility_gate", "exit_code": code,
            "exit_name": EXIT_NAMES.get(code, "UNKNOWN"), "decision": decision, "errors": errors}


def _index(lst, key):
    return {item.get(key): item for item in lst if isinstance(item, dict) and item.get(key)}


def validate_schema(bundle):
    errors = []
    for field in ("actors", "grants", "actions", "trajectory"):
        if field not in bundle:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors
    if not isinstance(bundle["actors"], list) or not isinstance(bundle["grants"], list) \
       or not isinstance(bundle["actions"], list) or not isinstance(bundle["trajectory"], list):
        errors.append("actors/grants/actions/trajectory must be arrays")
    return errors


def check_actor_resolvable(bundle):
    errors = []
    actors = _index(bundle["actors"], "actor_id")
    for a in bundle["actions"]:
        for role in ("initiator", "authorizer", "executor", "verifier"):
            aid = a.get(role)
            if aid and aid not in actors:
                errors.append(f"action {a.get('action_id')}: {role} '{aid}' not a declared actor")
    return errors


def check_authority_source(bundle):
    errors = []
    for actor in bundle["actors"]:
        src = str(actor.get("authority_source", "")).lower()
        # bare model name (optionally with version) is forbidden as authority source
        stripped = src.split(":")[0]
        if any(stripped == m or stripped.startswith(m + "-") or stripped.startswith(m + "_") for m in MODEL_NAME_PATTERNS):
            errors.append(f"actor {actor.get('actor_id')}: authority_source '{actor.get('authority_source')}' is a bare model name, not a resolvable source")
    return errors


def check_grants(bundle, now):
    errors = []
    grants = _index(bundle["grants"], "grant_id")
    for g in bundle["grants"]:
        gid = g.get("grant_id")
        if g.get("grantor") == g.get("grantee"):
            errors.append(f"grant {gid}: grantor == grantee (self-grant)")
            return _result(SELF_GRANT, errors)
        if g.get("status") in ("revoked", "expired", "suspended") or g.get("revoked"):
            errors.append(f"grant {gid}: revoked/expired/suspended")
            return _result(GRANT_EXPIRED_OR_REVOKED, errors)
        exp = g.get("expires_at")
        if exp and now and exp < now:
            errors.append(f"grant {gid}: expired at {exp} (now {now})")
            return _result(GRANT_EXPIRED_OR_REVOKED, errors)
    return None


def check_action_grants(bundle):
    errors = []
    grants = _index(bundle["grants"], "grant_id")
    for a in bundle["actions"]:
        gid = a.get("grant_id")
        if gid not in grants:
            errors.append(f"action {a.get('action_id')}: grant '{gid}' not resolvable")
    if errors:
        return _result(GRANT_UNRESOLVABLE, errors)
    # scope breach
    for a in bundle["actions"]:
        g = grants.get(a.get("grant_id"), {})
        allowed = g.get("allowed_action_types", [])
        if allowed and a.get("action_type") not in allowed:
            errors.append(f"action {a.get('action_id')}: type '{a.get('action_type')}' not in grant allowed_action_types")
            return _result(SCOPE_BREACH, errors)
    return None


def check_delegation(bundle):
    errors = []
    grants = _index(bundle["grants"], "grant_id")
    actors = _index(bundle["actors"], "actor_id")
    for a in bundle["actions"]:
        g = grants.get(a.get("grant_id"), {})
        grantee = g.get("grantee")
        executor = a.get("executor") or a.get("initiator")
        if executor and grantee and executor != grantee:
            # executor must equal grantee unless delegation allowed AND a valid chain exists
            if g.get("delegation") == "forbidden":
                errors.append(f"action {a.get('action_id')}: executor '{executor}' != grantee '{grantee}' and delegation forbidden")
                return _result(BROKEN_DELEGATION, errors)
    return None


def check_claim_state(bundle, claims_index):
    errors = []
    grants = _index(bundle["grants"], "grant_id")
    for a in bundle["actions"]:
        cref = a.get("claim_ref")
        g = grants.get(a.get("grant_id"), {})
        required = g.get("required_commitment_state", "committed_current")
        # honor an explicit claim_state on the action (fixtures); otherwise resolve
        # from the claims registry; an unknown claim defaults to its declared state.
        if a.get("claim_state") is not None:
            cstate = a.get("claim_state")
        elif claims_index is not None and cref in claims_index:
            cstate = claims_index[cref].get("state")
        else:
            cstate = "committed_current"
        if required in ("committed_current", "any_committed") and cstate != "committed_current":
            errors.append(f"action {a.get('action_id')}: relies on claim '{cref}' in state '{cstate}', not committed_current")
            return _result(CLAIM_NOT_COMMITTED, errors)
    return None


def check_claim_ceiling(bundle):
    errors = []
    for a in bundle["actions"]:
        ceiling = str(a.get("claim_ceiling", "")).lower()
        text = (str(a.get("action_type", "")) + " " + str(a.get("conclusion", ""))).lower()
        ceiling_repo = any(t in ceiling for t in ["repository", "in-repo", "repo", "candidate_only", "within", "does not assert", "not assert", "scope"])
        text_real = any(t in text for t in REAL_WORLD_TOKENS)
        if ceiling_repo and text_real:
            errors.append(f"action {a.get('action_id')}: intent/conclusion exceeds claim ceiling")
            return _result(CLAIM_CEILING_BREACH, errors)
    return None


def check_separation_of_duty(bundle):
    errors = []
    grants = _index(bundle["grants"], "grant_id")
    for a in bundle["actions"]:
        g = grants.get(a.get("grant_id"), {})
        sod = g.get("separation_of_duty", {})
        init, auth, exc, ver = a.get("initiator"), a.get("authorizer"), a.get("executor"), a.get("verifier")
        if sod.get("initiator_not_authorizer") and init and auth and init == auth:
            errors.append(f"action {a.get('action_id')}: initiator == authorizer (separation-of-duty)")
            return _result(SEPARATION_OF_DUTY_VIOLATION, errors)
        if sod.get("authorizer_not_executor") and auth and exc and auth == exc:
            errors.append(f"action {a.get('action_id')}: authorizer == executor (separation-of-duty)")
            return _result(SEPARATION_OF_DUTY_VIOLATION, errors)
        if sod.get("executor_not_verifier") and exc and ver and exc == ver:
            errors.append(f"action {a.get('action_id')}: executor == verifier (separation-of-duty)")
            return _result(SEPARATION_OF_DUTY_VIOLATION, errors)
        # high-risk: require distinct initiator/authorizer/executor/verifier
        if g.get("risk_tier") in ("high", "critical"):
            parties = [x for x in (init, auth, exc, ver) if x]
            if len(parties) != len(set(parties)):
                errors.append(f"action {a.get('action_id')}: high/critical risk action reuses a party across roles")
                return _result(SEPARATION_OF_DUTY_VIOLATION, errors)
    return None


def check_exact_head(bundle, current_main_head):
    errors = []
    if not current_main_head:
        return None
    for a in bundle["actions"]:
        eh = a.get("exact_head")
        if eh and eh != current_main_head:
            errors.append(f"action {a.get('action_id')}: exact_head {eh} != current main head {current_main_head}")
            return _result(STALE_EXACT_HEAD, errors)
    return None


def check_trajectory(bundle):
    errors = []
    traj = sorted(bundle["trajectory"], key=lambda e: e.get("seq", 0))
    if not traj:
        return None
    # seq must be 0..n-1 strictly increasing, chain intact
    for i, ev in enumerate(traj):
        if ev.get("seq") != i:
            errors.append(f"trajectory reorder/backfill: event at index {i} has seq {ev.get('seq')}")
            return _result(TRAJECTORY_INTEGRITY_FAIL, errors)
        expected_prev = "GENESIS" if i == 0 else traj[i-1].get("event_digest")
        if ev.get("prev_digest") != expected_prev:
            errors.append(f"trajectory chain break at seq {i}: prev_digest mismatch")
            return _result(TRAJECTORY_INTEGRITY_FAIL, errors)
        recomputed = _digest(ev.get("payload", {}), ev.get("prev_digest", ""))
        if ev.get("event_digest") != recomputed:
            errors.append(f"trajectory tamper at seq {i}: event_digest does not match payload+prev")
            return _result(TRAJECTORY_INTEGRITY_FAIL, errors)
    return None


def check_q33_bypass(bundle, q33_rejects):
    errors = []
    if not q33_rejects:
        return None
    rejected = set(q33_rejects)
    for a in bundle["actions"]:
        tgt = a.get("target")
        if a.get("action_type") in ("publish", "republish", "release") and tgt in rejected:
            errors.append(f"action {a.get('action_id')}: authorizes publishing '{tgt}' rejected by Q33 publication gate")
            return _result(Q33_GATE_BYPASS, errors)
    return None


def check_silent_rewrite(bundle):
    errors = []
    # a rollback/failure/deletion must appear as a NEW trajectory event, not by removing events
    # heuristic: if any action phase is rollback but there is no rollback trajectory event -> violation
    rb_actions = {a.get("action_id") for a in bundle["actions"] if a.get("phase") == "rollback"}
    rb_events = {e.get("action_id") for e in bundle["trajectory"] if e.get("phase") == "rollback"}
    for aid in rb_actions:
        if aid not in rb_events:
            errors.append(f"rollback action {aid} has no append-only trajectory event (silent rewrite)")
            return _result(SILENT_HISTORY_REWRITE, errors)
    return None


def check_unresolved_forced(bundle):
    errors = []
    for a in bundle["actions"]:
        if a.get("phase") == "unresolved_responsibility":
            # must NOT assert a single owner
            if a.get("governance_owner") and not a.get("many_hands"):
                errors.append(f"action {a.get('action_id')}: unresolved many-hands forced into a single owner")
                return _result(UNRESOLVED_RESPONSIBILITY_FORCED, errors)
    return None


def check_canonical_claims(bundle, claims_index):
    if claims_index is None:
        return _result(UNKNOWN_CLAIM, ["canonical Q34 claim registry is unavailable"])
    for action in bundle["actions"]:
        claim_id = action.get("claim_ref")
        claim = claims_index.get(claim_id)
        if claim is None:
            return _result(UNKNOWN_CLAIM, [f"action {action.get('action_id')}: claim {claim_id!r} is absent from the canonical Q34 registry"])
        content, error = _verify_binding(claim.get("binding"))
        if error:
            return _result(CLAIM_BINDING_MISMATCH, [f"claim {claim_id}: {error}"])
        try:
            artifact = json.loads(content)
        except Exception as exc:  # noqa: BLE001
            return _result(CLAIM_BINDING_MISMATCH, [f"claim {claim_id}: bound bytes are not JSON: {exc}"])
        expected_digest = claim.get("claim_digest")
        expected_head = claim.get("subject_head")
        if artifact.get("claim_id") != claim_id or artifact.get("state") != claim.get("state"):
            return _result(CLAIM_BINDING_MISMATCH, [f"claim {claim_id}: bound artifact identity/state mismatch"])
        if artifact.get("claim_digest") != expected_digest or artifact.get("exact_head_binding", {}).get("head") != expected_head:
            return _result(CLAIM_BINDING_MISMATCH, [f"claim {claim_id}: bound digest/head mismatch"])
        if action.get("claim_digest") != expected_digest or action.get("claim_exact_commit") != claim.get("binding", {}).get("exact_commit"):
            return _result(CLAIM_BINDING_MISMATCH, [f"action {action.get('action_id')}: claim digest/exact commit is absent or mismatched"])
    return None


def _find_grant(artifact, grant_id):
    if isinstance(artifact, dict) and artifact.get("grant_id") == grant_id:
        return artifact
    grants = artifact.get("grants", []) if isinstance(artifact, dict) else []
    return next((item for item in grants if isinstance(item, dict) and item.get("grant_id") == grant_id), None)


def check_canonical_authority(bundle, actor_index, grant_index, now):
    if actor_index is None or grant_index is None:
        return _result(PLACEHOLDER_AUTHORITY, ["canonical actor/grant registry is unavailable"])
    embedded_grants = _index(bundle["grants"], "grant_id")
    for action in bundle["actions"]:
        grant_id = action.get("grant_id")
        embedded = embedded_grants.get(grant_id)
        if embedded is None:
            return _result(NONCANONICAL_GRANT, [f"action {action.get('action_id')}: embedded grant is missing"])
        grantor = embedded.get("grantor")
        if _placeholder(grantor) or grantor not in actor_index:
            return _result(UNKNOWN_GRANTOR, [f"grant {grant_id}: grantor/principal {grantor!r} is not canonical"])
        grantee = embedded.get("grantee")
        if _placeholder(grantee) or grantee not in actor_index:
            return _result(PLACEHOLDER_AUTHORITY, [f"grant {grant_id}: grantee {grantee!r} is not canonical"])
        canonical = grant_index.get(grant_id)
        if canonical is None:
            return _result(NONCANONICAL_GRANT, [f"grant {grant_id!r} is absent from the canonical grant registry"])
        content, error = _verify_binding(canonical.get("binding"))
        if error:
            return _result(GRANT_BINDING_MISMATCH, [f"grant {grant_id}: {error}"])
        try:
            artifact = json.loads(content)
        except Exception as exc:  # noqa: BLE001
            return _result(GRANT_BINDING_MISMATCH, [f"grant {grant_id}: bound bytes are not JSON: {exc}"])
        bound = _find_grant(artifact, grant_id)
        if bound is None:
            return _result(GRANT_BINDING_MISMATCH, [f"grant {grant_id}: bound artifact does not contain this grant"])
        critical = ("grantor", "grantee", "allowed_action_types", "resource_scope",
                    "delegation", "status", "claim_ceiling")
        if any(embedded.get(field) != bound.get(field) for field in critical):
            return _result(GRANT_BINDING_MISMATCH, [f"grant {grant_id}: embedded grant differs from byte-bound canonical grant"])
        for field in ("valid_from", "expires_at", "revoked", "delegation_chain"):
            if field not in bound:
                return _result(GRANT_BINDING_MISMATCH, [f"grant {grant_id}: canonical artifact lacks {field}"])
        if bound.get("revoked") is not False or bound.get("status") != "active":
            return _result(GRANT_EXPIRED_OR_REVOKED, [f"grant {grant_id}: canonical artifact is not active"])
        if now and (now < bound["valid_from"] or now >= bound["expires_at"]):
            return _result(GRANT_EXPIRED_OR_REVOKED, [f"grant {grant_id}: outside canonical validity interval"])
        if bound.get("delegation") == "forbidden" and bound.get("delegation_chain") not in ([], [grantor, grantee]):
            return _result(BROKEN_DELEGATION, [f"grant {grant_id}: forbidden delegation chain is nonempty"])
        if bound.get("resource_scope") == "repository" and _repo_relative_path(action.get("target")) is None:
            return _result(SCOPE_BREACH, [f"action {action.get('action_id')}: target is not canonical repo-relative"])
        binding = canonical.get("binding", {})
        if action.get("grant_digest") != binding.get("sha256") or action.get("grant_exact_commit") != binding.get("exact_commit"):
            return _result(GRANT_BINDING_MISMATCH, [f"action {action.get('action_id')}: grant digest/exact commit is absent or mismatched"])
    return None


def validate(bundle, now=None, claims_index=None, actor_index=None, grant_index=None,
             q33_rejects=None, current_main_head=None):
    errors = validate_schema(bundle)
    if errors:
        return _result(SCHEMA_ERROR, errors)

    r = check_trajectory(bundle)
    if r: return r
    r = check_silent_rewrite(bundle)
    if r: return r

    errs = check_authority_source(bundle)
    if errs: return _result(MODEL_NAME_AS_AUTHORITY, errs)
    errs = check_actor_resolvable(bundle)
    if errs: return _result(ACTOR_UNRESOLVABLE, errs)

    r = check_grants(bundle, now)
    if r: return r
    r = check_action_grants(bundle)
    if r: return r
    r = check_claim_state(bundle, claims_index)
    if r: return r
    r = check_claim_ceiling(bundle)
    if r: return r
    r = check_separation_of_duty(bundle)
    if r: return r
    r = check_delegation(bundle)
    if r: return r
    r = check_exact_head(bundle, current_main_head)
    if r: return r
    r = check_q33_bypass(bundle, q33_rejects)
    if r: return r
    r = check_unresolved_forced(bundle)
    if r: return r

    r = check_canonical_claims(bundle, claims_index)
    if r: return r
    r = check_canonical_authority(bundle, actor_index, grant_index, now)
    if r: return r

    return _result(GATE_PASS, [], decision="AUTHORIZE")


def _load(p):
    try:
        return json.loads(p.read_text()), None
    except Exception as e:  # noqa: BLE001
        return None, f"{p}: {e}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Q35 responsibility-authority-action-trace gate (fail-closed)")
    ap.add_argument("--bundle", required=True, help="path to responsibility bundle JSON")
    ap.add_argument("--claims", help="path to Q34 claims JSON (list with claim_id/state)")
    ap.add_argument("--actors", default=str(ROOT / "data/agent/canonical-actor-registry.json"),
                    help="canonical actor/principal registry")
    ap.add_argument("--grant-registry", default=str(ROOT / "data/agent/canonical-grant-registry.json"),
                    help="canonical byte-bound grant registry")
    ap.add_argument("--q33-rejects", help="path to JSON list of Q33-rejected targets")
    ap.add_argument("--current-main-head", help="current main head SHA")
    ap.add_argument("--now", help="ISO timestamp for expiry evaluation")
    ap.add_argument("--report", help="write JSON report to this path")
    args = ap.parse_args(argv)

    bundle, err = _load(Path(args.bundle))
    if err:
        out = _result(SCHEMA_ERROR, [err])
        return _emit(out, args)

    claims_index = None
    cl, cerr = _load(Path(args.claims)) if args.claims else (None, "canonical claims path missing")
    if not cerr:
        claims_index = _index(cl if isinstance(cl, list) else cl.get("claims", []), "claim_id")

    actor_index = None
    actors, aerr = _load(Path(args.actors))
    if not aerr:
        actor_index = _index(actors.get("actors", []) if isinstance(actors, dict) else [], "actor_id")

    grant_index = None
    grants, gerr = _load(Path(args.grant_registry))
    if not gerr:
        grant_index = _index(grants.get("grants", []) if isinstance(grants, dict) else [], "grant_id")

    q33_rejects = None
    if args.q33_rejects:
        qr, qerr = _load(Path(args.q33_rejects))
        if not qerr:
            q33_rejects = qr if isinstance(qr, list) else qr.get("rejected", [])

    out = validate(bundle, now=args.now, claims_index=claims_index,
                   actor_index=actor_index, grant_index=grant_index,
                   q33_rejects=q33_rejects, current_main_head=args.current_main_head)
    return _emit(out, args)


def _emit(out, args):
    if args.report:
        Path(args.report).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return out["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
