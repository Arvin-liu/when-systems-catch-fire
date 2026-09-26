# Condition packet construction — R1

Each future case contains shared synthetic facts plus exactly one supplemental record. FACTS_ONLY adds a neutral case-log index. SKILL_ONLY adds an operation-recording procedure that does not select among case actions. METHOD adds seven byte-addressable atoms and five source-linked relations; its preregistered decisive relation set carries the case-specific method mapping. LINKLESS uses the byte-identical METHOD atom block and omits exactly that set, retaining all non-decisive relations. CASE01, CASE02, CASE03, CASE05, and CASE06 each cut one relation; CASE04 cuts R01 and R04 because measurement selection and threshold interpretation are both decision-bearing.

Atoms record candidate definitions, observations, provenance, measurement fields, version history, or status without the sealed target disposition. Relation rows use stable `R##` identifiers and structured source/edge/target signatures. Each independent ambiguity proof shows two materially different actions consistent with the facts, atoms, and every retained non-decisive relation before the cut set.

Facts use `F##`, skill steps use `S##`, method atoms use `A##`, and recorded relations use `R##`. Construction notes, proofs, condition labels, and sealed targets are not included in successor-visible payloads.
