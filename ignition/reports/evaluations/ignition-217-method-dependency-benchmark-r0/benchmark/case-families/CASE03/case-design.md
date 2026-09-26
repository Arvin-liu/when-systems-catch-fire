# CASE03 design note — R1

Family: failure_interpretation.

FACTS records QUEUED, a lost receipt, no terminal status, an immutable non-duplicating key, and both controls. SKILL records a selected operation without deciding which operation should be used. METHOD and LINKLESS have byte-identical atom blocks; METHOD has five structured relations and LINKLESS omits only decisive R02.

Before R02, query-first and same-key resubmission are both consistent because the request identity is stable but its terminal state is unknown. R01 and R03–R05 preserve request identity, available status fields, and execution status without mapping this failure sequence to a next action. R02 supplies that failure-to-diagnostic mapping and the terminal retry boundary.
