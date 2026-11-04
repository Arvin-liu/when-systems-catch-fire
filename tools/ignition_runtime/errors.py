"""Exception taxonomy for the Ignition production runtime.

All failures are fail-closed: the runtime raises a specific exception rather
than silently degrading. Tests assert these exceptions to prove the
old-or-new-only and fail-closed guarantees.
"""

from __future__ import annotations


class IgnitionError(Exception):
    """Base class for all Ignition runtime errors."""


class SimulatedCrash(IgnitionError):
    """Raised deliberately by the crash harness to test old-or-new-only."""


class PointerError(IgnitionError):
    """Raised when the CURRENT strict pointer is missing/corrupt/escaped."""


class ManifestError(IgnitionError):
    """Raised when a closed-manifest check fails (closure / digests / parent)."""


class GenerationIntegrityError(ManifestError):
    """Raised when a generation directory name or manifest ``generation_id`` does
    not match the content-derived generation id recomputed on load.

    This is a fail-closed *content-addressing / crash-consistency* check. It does
    NOT resist an attacker holding full local store write permission (who can
    rewrite data, manifest, and directory name consistently). Cross-trust-boundary
    authenticity is borne by external Git commit, remote refetch, and evidence
    anchors.
    """


class EpistemicError(IgnitionError):
    """Raised when the epistemic contract is violated (fail closed)."""


class IdentityError(IgnitionError):
    """Raised on non-self-referential identity / publication-identity violation."""


class ModeBoundaryError(IgnitionError):
    """Raised when a mode attempts to cross its hard boundary (RUN/PROMOTE/EVOLVE)."""


class AuthorizationError(IgnitionError):
    """Raised when an operation lacks explicit user authorization."""


class PathEscapeError(IgnitionError):
    """Raised when a path attempts to escape its authorized root."""
