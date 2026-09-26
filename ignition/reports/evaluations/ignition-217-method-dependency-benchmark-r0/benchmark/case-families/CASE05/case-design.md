# CASE05 design note — R1

Family: revision_scope.

FACTS records V0, V1, a prior cross-access event whose raw record omits grouping key and procedure version, a present two-class request, and no execution. SKILL records a grouping key supplied by the operator without choosing it. METHOD and LINKLESS have byte-identical atom blocks; METHOD has five relations and LINKLESS omits only decisive R01.

Before R01, both request-level V0 grouping and signatory-class V1 grouping are consistent: the prior event does not identify which grouping mechanism produced it. R02–R05 preserve version chronology, current-shape/verification fields, and execution status without assigning the revision's scope. R01 links the counterexample to the limited V1 scope for mixed-signatory records while retaining V0 for single-class records.
