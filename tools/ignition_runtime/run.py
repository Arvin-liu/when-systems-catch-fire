"""RUN mode: ingest, source-bind, decompose, collide, falsify, classify.

RUN commits a new immutable generation of type ``run``. It MUST NOT import or
invoke the review pathway or the engineering-pathway modes; those are separate
modes gated in ``cli``. This module contains no reference to those other modes.
"""

from __future__ import annotations

from pathlib import Path

from .epistemic import (
    is_beyond_ceiling,
    merge_candidates,
    semantic_id_of,
    source_bind,
    tier_to_ceiling,
    validate_epistemic_contract,
)
from .errors import EpistemicError
from .generation import Generation, load_generation
from .hashutil import sha256_text
from .providers.base import MaterialProvider
from .store import StoreLayout
from .transaction import publish_generation


def _result_for(material: dict) -> dict:
    summary = canonical_result_summary(material)
    return {
        "result_id": "res_" + material["source_sha256"][:16],
        "source_sha256": material["source_sha256"],
        "result_digest": sha256_text(summary),
        "schema_version": "ignition_runtime/1.0.0",
        "contract_version": material["contract_version"],
    }


def canonical_result_summary(material: dict) -> str:
    return sha256_text(
        material["material_id"] + "|" + material["source_sha256"]
    )


def _build_from_material(material_rec, material: dict, gen_id: str):
    """Return (candidate_seeds, unknown_records, signal_records) for one material."""
    source_sha = material["source_sha256"]
    tier = material["source_tier"]
    ceiling = material["claim_ceiling"]

    candidate_seeds: list[dict] = []
    unknown_records: list[dict] = []

    for seed in material_rec.candidate_seeds:
        sid = semantic_id_of(source_sha, seed["claim_text"])
        beyond = is_beyond_ceiling(seed["claim_text"]) or any(
            is_beyond_ceiling(c) for c in seed.get("inference_claims", [])
        )
        if beyond and tier != "PRIMARY_REPORT":
            # Downgrade beyond-ceiling claim to UNKNOWN (never auto-applies review).
            unknown_records.append(
                {
                    "unknown_id": "unk_" + sid,
                    "material_id": material_rec.material_id,
                    "semantic_id": sid,
                    "question": f"Beyond-ceiling claim unverified: {seed['claim_text']}",
                    "scope": material_rec.material_id + " beyond-ceiling",
                    "created_gen": gen_id,
                    "resolved": False,
                }
            )
            continue
        candidate_seeds.append(
            {
                "candidate_id": "cand_" + sid,
                "material_id": material_rec.material_id,
                "semantic_id": sid,
                "claim_text": seed["claim_text"],
                "source_sha256": source_sha,
                "source_tier": tier,
                "claim_ceiling": ceiling,
                "inference_claims": list(seed.get("inference_claims", [])),
                "source_claims": list(seed.get("source_claims", [])),
            }
        )

    for seed in material_rec.unknown_seeds:
        sid = semantic_id_of(source_sha, seed["question"])
        unknown_records.append(
            {
                "unknown_id": "unk_" + sid,
                "material_id": material_rec.material_id,
                "semantic_id": sid,
                "question": seed["question"],
                "scope": seed.get("scope", material_rec.material_id),
                "created_gen": gen_id,
                "resolved": False,
            }
        )

    signal_records: list[dict] = []
    for seed in material_rec.signal_seeds:
        sid = semantic_id_of(source_sha, seed["description"])
        signal_records.append(
            {
                "signal_id": "sig_" + sid,
                "material_id": material_rec.material_id,
                "semantic_id": sid,
                "description": seed["description"],
                "source_sha256": source_sha,
                "created_gen": gen_id,
                "approved": False,
                "status": "OPEN",
            }
        )

    return candidate_seeds, unknown_records, signal_records


def run(store: StoreLayout, provider: MaterialProvider, *, authorized_by: str = "",
       crash_after: str = "none", refs: list[str] | None = None) -> str:
    gen_dir = store.resolve_current_gen()
    if gen_dir is None:
        store.bootstrap()
        gen_dir = store.resolve_current_gen()
    assert gen_dir is not None

    parent = load_generation(gen_dir)
    parent_gen_id = parent["manifest"]["parent_generation"]
    # parent_gen_id is None only for bootstrap; for the run the parent is the
    # resolved (current) generation id.
    current_gen_id = gen_dir.name
    store_identity = parent["store_identity"]
    prev_candidates = parent.get("candidates", [])

    gen_id_for_seeds = current_gen_id  # seeds reference the parent (before swap)
    ingested: dict[str, dict] = {}
    results: list[dict] = []
    all_candidate_seeds: list[dict] = []
    all_unknowns: list[dict] = []
    all_signals: list[dict] = []

    recs = provider.list_materials(refs)
    for rec in recs:
        material = source_bind(
            rec.material_id,
            rec.source_bytes,
            tier=rec.source_tier,
            provider_id=rec.provider_id,
            provider_mode=rec.provider_mode,
            observed_at=rec.observed_at,
            published_at=rec.published_at,
            event_at=rec.event_at,
            extra=rec.extra or None,
        )
        ingested[rec.material_id] = material
        c_seeds, u_recs, s_recs = _build_from_material(rec, material, gen_id_for_seeds)
        all_candidate_seeds.extend(c_seeds)
        all_unknowns.extend(u_recs)
        all_signals.extend(s_recs)

    # A generation must be self-contained: include source materials referenced by
    # carried-forward candidates (parent materials), so bindings stay valid.
    parent_materials = parent.get("materials", {})
    materials = {**parent_materials, **ingested}
    results = [_result_for(m) for m in materials.values()]

    present_material_ids = set(ingested.keys())
    candidates = merge_candidates(
        prev_candidates, all_candidate_seeds, present_material_ids, current_gen_id
    )

    validate_epistemic_contract(
        materials, candidates, all_unknowns, all_signals, "run", provider.provider_identity()
    )

    gen = Generation(
        op_type="run",
        operation_id="",  # filled by publish
        parent_generation=current_gen_id,
        store_identity=store_identity,
        materials=materials,
        results=results,
        candidates=candidates,
        unknowns=all_unknowns,
        signals=all_signals,
        provider_identity=provider.provider_identity(),
        timestamps={"observed_at": None, "published_at": None},
    )
    return publish_generation(store, gen, crash_after=crash_after, authorized_by=authorized_by)
