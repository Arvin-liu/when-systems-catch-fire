# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus-scale runtime: a generic layer over Adaptive Relational Runtime R2.

This subpackage implements the first complete corpus-scale pressure test of ARR
(IGNITION R3 WAIC CORPUS SCALE RUN R1). It is a *layer*, not a second ARR and not
a second production executor. It may call existing ARR objectization / routing /
receipt interfaces (``tools.adaptive_relational_runtime.canonical``,
``adapter_protocol``, ``production_receipt_adapter``) but it MUST NOT call
PROMOTE or EVOLVE and MUST NOT perform any external real-world action.

Public-repository boundary (IGNITION §12): this code, its schemas, synthetic
fixtures and tests contain NO private corpus content. The generic runner reads a
corpus root supplied at runtime and emits typed references (hashes + types) only.
Per-note detail is produced only into a designated private evidence workspace.

The runtime modules (identity, shard, inventory, semantic, checkpoint, runner,
aggregate) are added in the subsequent R3 commits; this package re-exports them
as they land.
"""
from __future__ import annotations

from . import schemas

__all__ = ["schemas"]
