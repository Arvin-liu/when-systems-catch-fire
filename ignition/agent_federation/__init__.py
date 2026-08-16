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

__all__ = [
    "ApprovalPolicy", "ArtifactRef", "BudgetContract", "ExecutorDescriptor", "ExecutorHealth",
    "ExternalSessionRef", "FederatedExecutor", "FederatedHandoffBundle", "FederatedProgressEvent",
    "FederatedResultReceipt", "FederatedTaskEnvelope", "FederationContractError", "HandoffEligibility",
    "HandoffPolicy", "OutputContract", "UnsupportedExecutorOperation", "ValidationContract", "canonical_digest",
]
