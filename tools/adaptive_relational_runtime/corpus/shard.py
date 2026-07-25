# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Deterministic shard planning for the R3 corpus run (IGNITION §10).

Shard membership is derived purely from frozen object identity, so that
reordering the input, re-running, or resuming from a checkpoint always yields the
identical plan. The plan digest is content-addressed over the full membership.
"""
from __future__ import annotations

from typing import Any

from . import schemas
from .identity import compute_identity


def build_shard_plan(
    identities: list[schemas.CorpusObjectIdentity],
    shard_count: int,
    frozen_corpus_ref: str,
) -> schemas.ShardPlan:
    """Assign object keys to shards deterministically by sorted identity hash.

    Determinism: sort keys by their ``path_digest`` (lexicographic), then assign
    round-robin. Reordering the input list does not change membership because we
    sort first. ``shard_count`` is fixed for the run.
    """
    if shard_count < 1:
        raise ValueError("shard_count must be >= 1")
    keys = sorted(r.path_digest for r in identities)
    shards: list[list[str]] = [[] for _ in range(shard_count)]
    for i, key in enumerate(keys):
        shards[i % shard_count].append(key)
    members = [
        schemas.ShardMember(shard_id=f"shard-{idx:03d}", object_keys=sk).to_dict()
        for idx, sk in enumerate(shards)
    ]
    plan = schemas.ShardPlan(
        shard_count=shard_count,
        method="deterministic_by_identity_hash",
        frozen_corpus_ref=frozen_corpus_ref,
        object_count=len(keys),
        plan_digest="",
        shards=members,
    )
    plan.plan_digest = shard_plan_digest(plan)
    return plan


def shard_plan_digest(plan: schemas.ShardPlan) -> str:
    """Content-addressed digest over the full shard membership (order-independent)."""
    membership = {
        m["shard_id"]: sorted(m["object_keys"]) for m in plan.shards
    }
    ordered = {k: membership[k] for k in sorted(membership)}
    payload = schemas.canonical_json(
        {
            "shard_count": plan.shard_count,
            "method": plan.method,
            "frozen_corpus_ref": plan.frozen_corpus_ref,
            "object_count": plan.object_count,
            "membership": ordered,
        }
    )
    return schemas.digest_of(payload)


def is_key_in_namespace(plan: schemas.ShardPlan, shard_id: str, key: str) -> bool:
    for m in plan.shards:
        if m["shard_id"] == shard_id:
            return key in m["object_keys"]
    return False
