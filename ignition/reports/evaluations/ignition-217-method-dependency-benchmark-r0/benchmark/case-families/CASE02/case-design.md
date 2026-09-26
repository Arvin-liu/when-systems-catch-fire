# CASE02 design note — R1

Family: boundary_rejection.

FACTS records mixed regional markers, both controls, an older origin snapshot, and no operation result. SKILL records an operator-selected control but contains no selection rule. METHOD and LINKLESS have byte-identical atom blocks; METHOD has five structured relations and LINKLESS omits only decisive R02.

Before R02, both a purge proposal and a wait-and-probe proposal remain consistent because the record does not say what revision a purge reloads during mixed rollout. R01 and R03–R05 record context, observation fields, coverage, and execution status without deciding the boundary. R02 alone maps the boundary to deferral and the all-region/two-probe reconsideration gate.
