# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Aggregate validator entry point for R5-A (Commit 1 skeleton).

In Commit 1 validate_all raises NotImplementedError. Commits 2-4 implement the
individual contract validators and Commit 4 wires them into validate_all so the
>=120-check acceptance/attack suite passes.
"""

from __future__ import annotations


def validate_all() -> tuple[bool, list[str]]:
    """Run the full R5-A contract validator set.

    Returns (ok, failures). Implemented in Commit 4.
    """
    raise NotImplementedError("validators.validate_all implemented in Commit 4")
