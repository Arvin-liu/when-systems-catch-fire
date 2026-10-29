"""Ignition Generic Kernel R0.

This package owns only domain-neutral identity, permission, state, audit,
checkpoint, handoff and invariant contracts.  It deliberately has no import
path into a particular domain or publication surface.
"""

from .contracts import (
    ALLOWED_PHASES,
    ALLOWED_STOP_STATES,
    AuthorizationDecision,
    AuthorizationRequest,
    AuthorizationStatus,
    CapabilityScope,
    Checkpoint,
    KERNEL_FORBIDDEN_AUTHORITY_UPGRADES,
    KERNEL_NON_ESCALATION,
    Handoff,
    InvariantVerdict,
    MemoryEvent,
    ObjectRef,
    Phase,
    ProvenanceRef,
    ResumeCapsule,
    StateEvent,
    StopState,
    authorize_action,
    assert_no_authority_upgrade,
    canonical_json,
    normalize_relative_paths,
    KernelValidationError,
    sha256_json,
    validate_resume_lineage,
)
from .domain_pack import DomainPackManifest
from .profile import AgentProfile

__all__ = [
    "ALLOWED_PHASES",
    "ALLOWED_STOP_STATES",
    "AuthorizationDecision",
    "AuthorizationRequest",
    "AuthorizationStatus",
    "CapabilityScope",
    "Checkpoint",
    "KERNEL_FORBIDDEN_AUTHORITY_UPGRADES",
    "KERNEL_NON_ESCALATION",
    "DomainPackManifest",
    "Handoff",
    "InvariantVerdict",
    "AgentProfile",
    "MemoryEvent",
    "ObjectRef",
    "Phase",
    "ProvenanceRef",
    "ResumeCapsule",
    "StateEvent",
    "StopState",
    "authorize_action",
    "assert_no_authority_upgrade",
    "canonical_json",
    "normalize_relative_paths",
    "KernelValidationError",
    "sha256_json",
    "validate_resume_lineage",
]
