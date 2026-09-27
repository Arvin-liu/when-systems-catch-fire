# Repair round 3 — unique-writer synthesis and gate result

**Status:** final permitted pre-freeze design round; candidate set passes the four-part A-case gate. This synthesis was written after the A proposal and fresh B/C/D reports were frozen. It does not freeze the experiment or create experimental outputs.

## Gate by family

| Family | G1 | G2 | G3 | G4 | Result |
|---|---|---|---|---|---|
| F01 canopy | Pass on the complete ordered target: E1-bounded view/contact control followed by the M0 soil-moisture confirmation. M0 licenses the latter but not the added control. | Pass at exact-target granularity. Film/sun geometry gives a broad diagnostic cue, but not the 8° away-sun paired protocol or the required M0 sequence. | Pass, bounded to the observed reflective-film/toward-sun/21° context and source-supported 8° comparison. | Pass: the selector/action workflow is absent from M0 and resolves the measurement-control question without replacing M0 confirmation. | Pass |
| F02 turbidity | Pass when the complete method/value is scored: M0's mineral formula reports 214.5 mg/L; the bounded E1 floc-rich interpolation reports 131 mg/L. The bare `REPORT_ESTIMATE` label is shared. | Pass at exact-target granularity. Composition may suggest a matrix-specific method, but A does not provide the E1 points or derive the 131 mg/L result. | Pass for the stated floc-rich composition pattern and 100–300 NTU E1 envelope. M0's ±12 mg/L applies only to its baseline estimate; E1 supplies no uncertainty for 131 mg/L. | Pass: composition is not an M0 input, and the in-envelope E1 relation resolves the method/value ambiguity. | Pass |
| F03 cold chain | Pass: M0 licenses `SCREEN_PASS` for both; the bounded M1 selector routes only the verified group-P pulse to the available `STABILITY_REVIEW` slot. | Pass. The P/S traces are closely matched, with S slightly longer and warmer, so generic intuition does not justify preferring P. | Pass for verified group P and the observed complete high-rate pulse context; no universal pulse cutoff or degradation claim. | Pass: the group/pulse-specific route is absent from M0's applicable rule and resolves the single-slot allocation. The action label exists in M0 but M0 does not select it for these below-8°C means. | Pass |

**FAMILY01=4/4; FAMILY02=4/4; FAMILY03=4/4; FULL_A_CASE_VALIDITY_GATE=3/3**
**M0_ONLY_TWO_WAY_AMBIGUITY_PROVEN=3/3**

## Frozen review findings and required freeze wording

- B found no A case with two materially distinct M0 outputs left compatible. G1 therefore relies on the command's different-action path or, for F02, the full method/value as the scored action. Preserve that distinction in the case schema and outcome key; do not score only a terminal action label.
- C found G3/G4 supported for all three families. For F01, align the final control with E1's paired comparison: acquire two same-canopy away-from-sun scans at 8° off nadir, taking a contact-leaf reference immediately after each. This remains a diagnostic comparison; M0's soil-moisture confirmation remains mandatory regardless of its result.
- For F02, state explicitly that M0's ±12 mg/L uncertainty belongs to the M0 baseline only. Do not attach it to the E1-derived 131 mg/L interpolation.
- D found no exact target/action independently inferable from the A facts. Retain the F01 and F02 distinction between broad generic cues and exact E1-derived target; retain F03's P-versus-S comparison with no assay output in A.
- The A designer's separate proposal omitted the F03 group/high-rate selector from visible facts and therefore is not the candidate carried forward. Its valid F01 protocol detail is incorporated above.

## Boundary at this gate

No scientific freeze, successor conversation, experimental output, provider invocation, or evaluator launch has occurred. Gate completion authorizes only the next steps explicitly listed in the active R0.1 command.
