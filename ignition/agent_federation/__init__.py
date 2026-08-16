"""External Agent Federation R1: vendor-neutral OS/executor contracts."""

from .contracts import (
    ApprovalPolicy,
    ArtifactRef,
    BudgetContract,
    ExecutorDescriptor,
    ExecutorHealth,
    ExternalSessionRef,
    FederatedExecutor,
    FederatedHandoffBundle,
    FederatedProgressEvent,
    FederatedResultReceipt,
    FederatedTaskEnvelope,
    FederationContractError,
    HandoffEligibility,
    HandoffPolicy,
    OutputContract,
    UnsupportedExecutorOperation,
    ValidationContract,
    canonical_digest,
)
from .router import (
    CandidateEvaluation,
    ExecutorRoutingProfile,
    FederationRouter,
    RoutingDecision,
    RoutingError,
    RoutingPolicy,
    RoutingRequest,
    load_routing_policy,
)

__all__ = [
    "ApprovalPolicy", "ArtifactRef", "BudgetContract", "ExecutorDescriptor", "ExecutorHealth",
    "ExternalSessionRef", "FederatedExecutor", "FederatedHandoffBundle", "FederatedProgressEvent",
    "FederatedResultReceipt", "FederatedTaskEnvelope", "FederationContractError", "HandoffEligibility",
    "HandoffPolicy", "OutputContract", "UnsupportedExecutorOperation", "ValidationContract", "canonical_digest",
    "CandidateEvaluation", "ExecutorRoutingProfile", "FederationRouter", "RoutingDecision", "RoutingError",
    "RoutingPolicy", "RoutingRequest", "load_routing_policy",
]
