# Condition packet construction

Each future case consists of the shared synthetic case facts (`case-families/CASE##/facts.md`) plus exactly one condition-specific supplemental record. FACTS_ONLY adds no procedure or method-use trace. SKILL_ONLY adds a reusable operational procedure with stable `S##` locators and no method-selection rationale. METHOD adds the full linked trace: candidate/criterion, boundary, expected observation, application or test, failure interpretation, and disposition. LINKLESS_METHOD_CONTROL preserves the same METHOD atoms and all non-cut relations; it removes one predeclared target-licensing relation per case.

Source locators are stable within a case: facts use `F##`, skill steps use `S##`, method atoms use `A##`, and recorded method relations use `R##`. Control-equivalence notes inventory the atoms and relation cut. These construction notes and condition labels are not included in successor-visible packet payloads.
