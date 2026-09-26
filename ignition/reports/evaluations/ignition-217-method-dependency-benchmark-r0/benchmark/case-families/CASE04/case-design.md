# CASE04 design note — R1

Family: missing_discriminating_measurement.

FACTS records two plausible explanations and several available measurements/interventions without a post-refill result. SKILL records the location/time chosen by an operator but contains no measurement-selection rule. METHOD and LINKLESS have byte-identical atom blocks; METHOD has five structured relations and LINKLESS omits the complete decision-bearing set R01 and R04.

Before those relations, feed adjustment and canopy-humidity investigation are both consistent with the record. R02, R03, and R05 preserve temporal limits, equipment availability, and missing-result status without selecting a discriminator or interpreting a threshold. R01 selects the timed root-zone measurement; R04 supplies its numeric interpretation and the boundary against changing feed from current observations.
