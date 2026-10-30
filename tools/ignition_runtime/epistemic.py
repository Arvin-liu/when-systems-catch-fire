"""Epistemic contract (design D): source/result binding, claim ceiling,
candidate lifecycle, UNKNOWN non-emptiness, idempotency. All failures are
fail-closed via EpistemicError.
"""

from __future__ import annotations

from .errors import EpistemicError
from .hashutil import sha256_text

ALLOWED_CEILINGS = frozenset({"PRIMARY_VERIFIED", "SECONDARY", "UNKNOWN"})
ALLOWED_TIERS = frozenset(
    {"PRIMARY_REPORT", "SECONDARY_ACADEMIC_INTERPRETATION", "MEDIA_SYNTHESIS"}
)

# Claims beyond the ceiling (SOTA / originality / root cure) are downgraded to
# UNKNOWN unless primary-verified.
_BEYOND_CEILING_HINTS = (
    "sota",
    "state-of-the-art",
    "originality",
    "root cure",
    "根治",
    "最优",
    "最佳",
    "首创",
    "world's first",
)


def tier_to_ceiling(tier: str) -> str:
    return {
        "PRIMARY_REPORT": "PRIMARY_VERIFIED",
        "SECONDARY_ACADEMIC_INTERPRETATION": "SECONDARY",
        "MEDIA_SYNTHESIS": "UNKNOWN",
    }[tier]


def semantic_id_of(source_sha256: str, claim_text: str) -> str:
    normalized = " ".join(claim_text.strip().split())
    return "sid_" + sha256_text(source_sha256 + "|" + normalized)[:32]


def _normalize_claim(text: str) -> str:
    """HEURISTIC normalization for the beyond-ceiling guard (NOT a semantic
    classifier). Unicode NFKC, lowercase, then drop all non-alphanumeric
    characters (whitespace + punctuation separators). This neutralizes trivial
    spacing/punctuation obfuscations (e.g. ``new best`` -> ``newbest``) but does
    NOT defeat character-set substitution (leetspeak, synonyms). Over-claims from
    SECONDARY sources are still downgraded to UNKNOWN by the caller's tier check.
    """
    import unicodedata

    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    return "".join(c.lower() for c in text if c.isalnum())


def is_beyond_ceiling(claim_text: str) -> bool:
    norm = _normalize_claim(claim_text)
    return any(_normalize_claim(hint) in norm for hint in _BEYOND_CEILING_HINTS)


def source_bind(material_id: str, source_bytes: bytes, *, tier: str, provider_id: str,
                provider_mode: str, observed_at=None, published_at=None, event_at=None,
                contract_version: str = "1.0.0", runtime_version: str = "1.0.0",
                extra: dict | None = None) -> dict:
    if tier not in ALLOWED_TIERS:
        raise EpistemicError(f"unsupported source_tier: {tier}")
    source_sha256 = sha256_text(source_bytes.decode("utf-8", "replace") if isinstance(source_bytes, bytes) else str(source_bytes))
    rec = {
        "material_id": material_id,
        "source_sha256": source_sha256,
        "source_tier": tier,
        "observed_at": observed_at,
        "published_at": published_at,
        "event_at": event_at,
        "valid_from": None,
        "valid_to": None,
        "provider_id": provider_id,
        "provider_mode": provider_mode,
        "result_digest": None,
        "schema_version": "ignition_runtime/1.0.0",
        "runtime_version": runtime_version,
        "contract_version": contract_version,
        "unknown_nonempty": True,
        "claim_ceiling": tier_to_ceiling(tier),
        "inference_claims": [],
        "source_claims": [],
        "stale": False,
    }
    if extra:
        rec.update(extra)
    return rec


def merge_candidates(prev_candidates: list, new_seeds: list, present_material_ids: set, gen_id: str) -> list:
    """Apply the candidate lifecycle (ACTIVE / ARCHIVED / REPLACED).

    - identical semantic_id already ACTIVE -> kept ACTIVE (idempotent, no new entity)
    - identical semantic_id ARCHIVED -> reactivated ACTIVE exactly once
    - absent ACTIVE candidate whose material is still present -> REPLACED (source changed)
    - absent ACTIVE candidate whose material was removed -> ARCHIVED (tombstone)
    """
    prev_active = {c["semantic_id"]: c for c in prev_candidates if c["status"] == "ACTIVE"}
    prev_archived = {c["semantic_id"]: c for c in prev_candidates if c["status"] == "ARCHIVED"}
    new_sids = {s["semantic_id"] for s in new_seeds}
    out: list = []

    for s in new_seeds:
        sid = s["semantic_id"]
        if sid in prev_active:
            c = dict(prev_active[sid])
            c["status"] = "ACTIVE"
        elif sid in prev_archived:
            c = dict(prev_archived[sid])
            c["status"] = "ACTIVE"
            c["archived_at"] = None
            c["archived_gen"] = None
        else:
            c = {
                "candidate_id": s.get("candidate_id") or ("cand_" + sid),
                "material_id": s.get("material_id", ""),
                "semantic_id": sid,
                "claim_text": s["claim_text"],
                "source_sha256": s["source_sha256"],
                "source_tier": s["source_tier"],
                "claim_ceiling": s["claim_ceiling"],
                "status": "ACTIVE",
                "inference_claims": list(s.get("inference_claims", [])),
                "source_claims": list(s.get("source_claims", [])),
                "first_seen_gen": gen_id,
                "archived_at": None,
                "archived_gen": None,
            }
        out.append(c)

    for c in prev_candidates:
        sid = c["semantic_id"]
        if sid in new_sids:
            continue
        if c["status"] == "ACTIVE":
            carried = dict(c)
            if c.get("material_id") in present_material_ids:
                carried["status"] = "REPLACED"
            else:
                carried["status"] = "ARCHIVED"
            carried["archived_at"] = None
            carried["archived_gen"] = gen_id
            out.append(carried)
        else:
            out.append(dict(c))
    return out


def validate_epistemic_contract(materials: dict, candidates: list, unknowns: list,
                                signals: list, op_type: str, provider_identity: str) -> None:
    # UNKNOWN must be non-empty and every entry must have a non-empty question.
    if len(unknowns) == 0:
        raise EpistemicError("UNKNOWN ledger is empty (fail closed)")
    for u in unknowns:
        if not u.get("question") or not str(u["question"]).strip():
            raise EpistemicError("UNKNOWN entry has empty question (fail closed)")
        if u.get("scope") is None or not str(u["scope"]).strip():
            raise EpistemicError("UNKNOWN entry has empty scope (fail closed)")

    # Candidate claim ceilings must be bounded.
    for c in candidates:
        if c.get("claim_ceiling") not in ALLOWED_CEILINGS:
            raise EpistemicError(f"arbitrary claim ceiling: {c.get('claim_ceiling')}")
        if c.get("source_tier") not in ALLOWED_TIERS:
            raise EpistemicError(f"unsupported candidate source_tier: {c.get('source_tier')}")

    # No duplicate active semantic ids.
    active_sids = [c["semantic_id"] for c in candidates if c.get("status") == "ACTIVE"]
    if len(active_sids) != len(set(active_sids)):
        raise EpistemicError("duplicate active semantic_id detected (fail closed)")

    # Source/result binding: every ACTIVE candidate must bind to a known
    # material source. Non-active candidates (REPLACED / ARCHIVED) are historical
    # tombstones whose original source binding is intentionally stale after a
    # source change or material removal and must NOT fail the contract.
    material_shas = {m["source_sha256"] for m in materials.values()}
    for c in candidates:
        if c.get("status") != "ACTIVE":
            continue
        if c.get("source_sha256") not in material_shas:
            raise EpistemicError(
                f"candidate {c.get('candidate_id')} binds to unknown source (tamper)"
            )

    # Material tiers must be supported; provider identity must be coherent.
    provider_ids = {m.get("provider_id") for m in materials.values()}
    if None in provider_ids or not provider_ids:
        raise EpistemicError("material missing provider_id (binding tamper)")
    if op_type == "run" and provider_identity:
        # provider_identity must be among the material providers (no silent swap).
        # Incoherence fails closed for ALL schemes (upload://, fixture://, and any
        # other): if the identity is neither present in provider_ids nor prefix-
        # coherent with any material provider, reject. Provider identity/tier are
        # self-asserted; this check enforces internal coherence only, not provenance
        # authenticity (which requires out-of-band trust / evidence anchors).
        if provider_identity not in provider_ids and not any(
            provider_identity.startswith(pid.split("://")[0]) for pid in provider_ids
        ):
            raise EpistemicError("provider identity mismatch (binding tamper)")
