"""EVOLVE mode: engineering work ONLY.

EVOLVE produces an ``evolve`` generation after explicit user authorization
(``--authorize evolve:<token>``) AND a referenced approved engineering signal
id. It MUST NOT be invoked by RUN or by the review pathway. It never
auto-applies formal knowledge and never auto-triggers the review pathway.
"""

from __future__ import annotations

from .errors import AuthorizationError
from .generation import Generation, load_generation
from .hashutil import sha256_text
from .providers.base import MaterialProvider
from .store import StoreLayout
from .transaction import publish_generation


def evolve(store: StoreLayout, provider: MaterialProvider, *, authorized_by: str,
          approved_signal_id: str, crash_after: str = "none") -> str:
    if not authorized_by:
        raise AuthorizationError("engineering work requires explicit --authorize evolve:<token>")
    if not approved_signal_id:
        raise AuthorizationError("engineering work requires an approved signal id")
    gen_dir = store.resolve_current_gen()
    if gen_dir is None:
        raise AuthorizationError("no committed generation to extend (run first)")
    parent = load_generation(gen_dir)
    current_gen_id = gen_dir.name

    signals = parent.get("signals", [])
    approved = [s for s in signals if s.get("signal_id") == approved_signal_id]
    if not approved or approved[0].get("status") not in ("OPEN", "APPROVED"):
        raise AuthorizationError(
            f"approved signal not found in ledger: {approved_signal_id}"
        )

    # Engineering work: derive a new signal from the approved one. Deterministic
    # (semantic_id from approved_signal_id) so a repeat is a byte-stable no-op.
    new_sid = "sid_" + sha256_text("evolve:" + approved_signal_id)[:32]
    new_signal = {
        "signal_id": "sig_" + new_sid,
        "material_id": approved[0].get("material_id", ""),
        "semantic_id": new_sid,
        "description": f"engineering work derived from {approved_signal_id}",
        "source_sha256": approved[0].get("source_sha256", ""),
        "created_gen": current_gen_id,
        "approved": True,
        "status": "CONSUMED",
    }
    new_signals = list(signals) + [new_signal]

    gen = Generation(
        op_type="evolve",
        operation_id="",
        parent_generation=current_gen_id,
        store_identity=parent["store_identity"],
        materials=parent.get("materials", {}),
        results=parent.get("results", []),
        candidates=parent.get("candidates", []),
        unknowns=parent.get("unknowns", []),
        signals=new_signals,
        provider_identity=parent["manifest"].get("provider_identity", "fixture://deterministic"),
        timestamps={"observed_at": None, "published_at": None},
    )
    return publish_generation(store, gen, crash_after=crash_after, authorized_by=authorized_by)
