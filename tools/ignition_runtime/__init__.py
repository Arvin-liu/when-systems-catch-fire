"""Ignition production runtime (RUN / PROMOTE / EVOLVE).

Draft build only. No external acceptance/merge claims are made here.
Every authoritative state change commits a new immutable generation; a crash
leaves either the prior complete generation or no new generation visible.
"""

from . import errors, generation, store, transaction
from .errors import (
    AuthorizationError,
    EpistemicError,
    IdentityError,
    ManifestError,
    ModeBoundaryError,
    PathEscapeError,
    PointerError,
    SimulatedCrash,
)

__all__ = [
    "errors",
    "generation",
    "store",
    "transaction",
    "AuthorizationError",
    "EpistemicError",
    "IdentityError",
    "ManifestError",
    "ModeBoundaryError",
    "PathEscapeError",
    "PointerError",
    "SimulatedCrash",
]
