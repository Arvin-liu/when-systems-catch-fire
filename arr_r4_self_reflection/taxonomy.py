"""R4 self-reflection taxonomy: closed enumerations for axes, dispositions,
limitation classes and architecture-candidate evaluation.

These enumerations are the contract surface for every R4 audit module. They are
deliberately data-free: no 836 note ids, no private titles, no R3 result values
are embedded here. All inputs arrive at runtime through the sealed ingestor.
"""

# --- Four-axis status vocabularies (R4 task §5) ---

PIPELINE_AXIS = (
    "PIPELINE_COMPLETE",
    "PIPELINE_PARTIAL",
    "PIPELINE_FAILED",
    "PIPELINE_QUARANTINED",
)

SEMANTIC_AXIS = (
    "SEMANTIC_REPRESENTATION_SUFFICIENT",
    "SEMANTIC_REPRESENTATION_LIMITED",
    "SEMANTIC_NOT_ATTEMPTED",
    "SEMANTIC_UNKNOWN",
)

EVIDENCE_AXIS = (
    "INDEPENDENTLY_SUPPORTED",
    "SOURCE_DEPENDENT",
    "AUTHOR_OR_SPEAKER_REPORT",
    "TRANSCRIPT_OR_INTERPRETER_INFERENCE",
    "EVIDENCE_UNKNOWN",
)

GOVERNANCE_AXIS = (
    "BOUNDARY_HELD",
    "CONSENT_OR_RIGHTS_LIMITED",
    "ACTION_PROHIBITED",
    "GOVERNANCE_REVIEW_REQUIRED",
    "GOVERNANCE_UNKNOWN",
)

AXIS_NAMES = ("pipeline", "semantic", "evidence", "governance")

# Individual status constants (used by derivers to avoid stringly-typed literals).
PIPELINE_COMPLETE = "PIPELINE_COMPLETE"
PIPELINE_PARTIAL = "PIPELINE_PARTIAL"
PIPELINE_FAILED = "PIPELINE_FAILED"
PIPELINE_QUARANTINED = "PIPELINE_QUARANTINED"

SEMANTIC_REPRESENTATION_SUFFICIENT = "SEMANTIC_REPRESENTATION_SUFFICIENT"
SEMANTIC_REPRESENTATION_LIMITED = "SEMANTIC_REPRESENTATION_LIMITED"
SEMANTIC_NOT_ATTEMPTED = "SEMANTIC_NOT_ATTEMPTED"
SEMANTIC_UNKNOWN = "SEMANTIC_UNKNOWN"

INDEPENDENTLY_SUPPORTED = "INDEPENDENTLY_SUPPORTED"
SOURCE_DEPENDENT = "SOURCE_DEPENDENT"
AUTHOR_OR_SPEAKER_REPORT = "AUTHOR_OR_SPEAKER_REPORT"
TRANSCRIPT_OR_INTERPRETER_INFERENCE = "TRANSCRIPT_OR_INTERPRETER_INFERENCE"
EVIDENCE_UNKNOWN = "EVIDENCE_UNKNOWN"

BOUNDARY_HELD = "BOUNDARY_HELD"
CONSENT_OR_RIGHTS_LIMITED = "CONSENT_OR_RIGHTS_LIMITED"
ACTION_PROHIBITED = "ACTION_PROHIBITED"
GOVERNANCE_REVIEW_REQUIRED = "GOVERNANCE_REVIEW_REQUIRED"
GOVERNANCE_UNKNOWN = "GOVERNANCE_UNKNOWN"

# --- Metric-contradiction dispositions (R4 task §4) ---

METRIC_DISPOSITIONS = (
    "DEFINITION_CORRECT_VALUE_MISREAD",
    "AGGREGATION_DEFECT",
    "REPORTING_DEFECT",
    "TEST_OR_FIXTURE_DEFECT",
    "TRUE_ZERO_OR_TRUE_VALUE",
    "INSUFFICIENT_EVIDENCE",
    "UNKNOWN",
)

# --- Failure / limitation taxonomy (R4 task §6) ---

LIMITATION_CLASSES = (
    "MATERIAL_OR_SOURCE_LIMITATION",
    "RIGHTS_OR_ACCESS_LIMITATION",
    "EXTRACTION_LIMITATION",
    "REPRESENTATION_LIMITATION",
    "TEMPORAL_LIMITATION",
    "SOURCE_DEPENDENCY_LIMITATION",
    "FALSE_CONSENSUS_RISK",
    "ROUTING_LIMITATION",
    "MECHANISM_LIMITATION",
    "RUNTIME_DEFECT",
    "METRIC_OR_OBSERVABILITY_DEFECT",
    "TEST_OR_CI_DEBT",
    "GOVERNANCE_CONSTRAINT",
    "ARCHITECTURE_CANDIDATE",
    "UNKNOWN",
)

# --- Architecture-candidate gate (R4 task §7) ---

DEFAULT_ARCH_DISPOSITION = "NO_EVOLVE"
ARCH_CANDIDATE_DISPOSITION = "ARCHITECTURE_CANDIDATE"

# The eight mandatory conditions for ARCHITECTURE_CANDIDATE. If any is False,
# the disposition MUST be NO_EVOLVE. The gate is mutation-tested: removing or
# falsifying any condition must make a candidate fail.
ARCH_GATE_CONDITIONS = (
    "reproducible_from_sealed_evidence",
    "cross_source_or_class_breadth",
    "not_explained_by_lower_level",
    "measurable_loss_or_misclassification",
    "primitives_cannot_represent",
    "lower_cost_adapter_insufficient",
    "explicit_non_goals_risk_rollback",
    "independent_audit_agrees",
)

# --- Claim classes observed in R3 (not an R4 verdict; input vocabulary) ---

R3_CLAIM_CLASSES = (
    "AUTHOR_OBSERVATION",
    "SECONDARY_ARCHIVE_CLAIM",
    "TRANSCRIPT_INFERENCE",
)

R3_NOTE_TYPES = ("link", "plain_text", "local_audio", "recorder_audio")
