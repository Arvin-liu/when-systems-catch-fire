"""PROMOTE mode: reviewable promotion packages ONLY.

PROMOTE produces a ``promote_request`` or ``promote_approval`` generation after
explicit user authorization (``--authorize promote:<token>``). It MUST NOT call
the engineering-pathway mode; that is a separate, gated mode. Promotion never
auto-applies formal knowledge (candidates stay candidates).
"""

from __future__ import annotations

from .errors import AuthorizationError
from .generation import Generation, load_generation
from .hashutil import sha256_text
from .providers.base import MaterialProvider
from .store import StoreLayout
from .transaction import publish_generation


def _provider_identity_of(parent: dict) -> str:
    return parent["manifest"].get("provider_identity", "fixture://deterministic")


def _trace_source_run_gen(store: "StoreLayout", gen_dir: "Path | None") -> str | None:
    """Walk the parent chain from ``gen_dir`` to the nearest ``run`` generation.

    This yields a STABLE logical input for a promotion request: whether CURRENT
    is the run itself or an already-published promote_request, the linked source
    run is the same, so a duplicate request collapses to the same generation id.
    """
    cur = gen_dir
    while cur is not None:
        try:
            g = load_generation(cur)
        except Exception:
            return None
        if g["manifest"]["op_type"] == "run":
            return cur.name
        parent_ref = g["manifest"].get("parent_generation")
        cur = store.generations_dir / parent_ref if parent_ref else None
    return None


def promote_request(store: StoreLayout, provider: MaterialProvider, *, authorized_by: str,
                    candidate_refs: list[str] | None = None, crash_after: str = "none") -> str:
    if not authorized_by:
        raise AuthorizationError("promotion requires explicit --authorize promote:<token>")
    gen_dir = store.resolve_current_gen()
    if gen_dir is None:
        raise AuthorizationError("no committed generation to promote (run first)")
    parent = load_generation(gen_dir)
    current_gen_id = gen_dir.name
    source_run_gen = _trace_source_run_gen(store, gen_dir)
    if candidate_refs is None:
        candidate_refs = [
            c["candidate_id"]
            for c in parent.get("candidates", [])
            if c.get("status") == "ACTIVE"
        ]
    request_id = "promo_" + sha256_text("request" + (source_run_gen or "") + authorized_by)[:32]
    promotion = {
        "request_id": request_id,
        "request_type": "promote_request",
        "candidate_refs": sorted(candidate_refs),
        "package": {
            "package_id": "pkg_" + request_id,
            "candidate_refs": sorted(candidate_refs),
            "justification": "reviewable promotion package; no formal knowledge applied",
            "constraint_no_formal_promotion": True,
            "promotes_to_formal": False,
        },
        "authorized_by": authorized_by,
        "source_run_gen": source_run_gen,
        "links_request_gen": None,
        "status": "OPEN",
    }
    gen = Generation(
        op_type="promote_request",
        operation_id="",
        parent_generation=current_gen_id,
        store_identity=parent["store_identity"],
        materials=parent.get("materials", {}),
        results=parent.get("results", []),
        candidates=parent.get("candidates", []),
        unknowns=parent.get("unknowns", []),
        signals=parent.get("signals", []),
        promotion=promotion,
        provider_identity=_provider_identity_of(parent),
        timestamps={"observed_at": None, "published_at": None},
    )
    return publish_generation(store, gen, crash_after=crash_after, authorized_by=authorized_by)


def promote_approval(store: StoreLayout, provider: MaterialProvider, *, authorized_by: str,
                     request_gen_id: str, crash_after: str = "none") -> str:
    if not authorized_by:
        raise AuthorizationError("promotion approval requires explicit --authorize promote:<token>")
    req_dir = store.generations_dir / request_gen_id
    if not req_dir.is_dir():
        raise AuthorizationError(f"promotion request generation not found: {request_gen_id}")
    req = load_generation(req_dir)
    req_promotion = req.get("promotion", {})
    if req_promotion.get("request_type") != "promote_request":
        raise AuthorizationError("linked generation is not a promote_request")
    gen_dir = store.resolve_current_gen()
    current_gen_id = gen_dir.name if gen_dir is not None else request_gen_id
    approval_id = "promo_" + sha256_text("approval" + request_gen_id + authorized_by)[:32]
    promotion = {
        "request_id": approval_id,
        "request_type": "promote_approval",
        "candidate_refs": sorted(req_promotion.get("candidate_refs", [])),
        "package": req_promotion.get("package", {}),
        "authorized_by": authorized_by,
        "source_run_gen": req_promotion.get("source_run_gen"),
        "links_request_gen": request_gen_id,
        "status": "APPROVED",
    }
    parent = req
    gen = Generation(
        op_type="promote_approval",
        operation_id="",
        parent_generation=current_gen_id,
        store_identity=parent["store_identity"],
        materials=parent.get("materials", {}),
        results=parent.get("results", []),
        candidates=parent.get("candidates", []),
        unknowns=parent.get("unknowns", []),
        signals=parent.get("signals", []),
        promotion=promotion,
        provider_identity=_provider_identity_of(parent),
        timestamps={"observed_at": None, "published_at": None},
    )
    return publish_generation(store, gen, crash_after=crash_after, authorized_by=authorized_by)
