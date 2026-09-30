You are an independent blind evaluator. Use only the frozen scoring text and the 54 packets below. Do not use tools, browse, inspect files, or consult external sources. Do not infer or name a condition, policy, lineage, session, bundle, or sibling relationship. Do not compare packets or reconcile scores. Score only the case named by each packet. The full original three-case response was mechanically checked against the frozen response schema; if response_schema_valid is false, mark success false. A valid packet contains one sanitized case object, with the complete route_trace removed. Use the exact case facts and corresponding frozen target. Apply the full operational action and required reported values, not only the action label. Preserve applicable baseline routes; use the frozen fallback for unresolved or out-of-scope facts; do not impute missing information. A critical error overrides a correct terminal label. Do not invent values or actions. Return exactly one JSON object, no markdown fences, with one row for every packet and no extra fields. Missing or invalid rows remain false.

## Frozen Task225 transfer scoring criteria (verbatim relevant sections)

## Transfer case outcomes

For every transfer trial, independently score visible cases A/B/C against the sealed target for that family. Compare the complete operational action and any required reported value, not only an action label. For A, use the whole selector/applicability/action path. For B, check preservation. For C, check the unresolved/fallback path. Record true/false and a concise evidence citation; no partial credit is used for a case outcome.
## Critical errors

Record a critical error if an output claims unsupported stress/irrigation, confirmed degradation, universal thresholds/formulas, or a disposition outside the sealed evidence envelope, or replaces a required preserved M0 rule. A critical error is not overridden by a correct terminal label.

## Frozen Task227 transfer scoring criteria (verbatim)

# Blind Component-A transfer evaluator criteria

Each evaluator independently scores the same 18 randomized opaque response packets. Use only the visible case bytes, corresponding frozen target, this scoring guide, and sanitized response. Do not access M0/E1/reference-policy materials, condition labels, input manifests, condition map, lineage groupings, sibling responses, Task226 outcomes, or the other evaluator's sheet.

For each response:
- Mark valid_response false if the supplied JSON was missing, unparsable, or failed the frozen response schema. Invalid responses receive false for A, B, and C.
- Independently mark A, B, and C target success based on the full frozen target details, not shared terminal action names.
- Record the concrete missing or contradictory requirement for each false score.
- Record a critical error only for unsupported global claims, retiring a required M0 baseline, imputing an unresolved required input, or contradicting an explicit case fact. Critical-error flags are descriptive and do not change the preregistered Component-A thresholds.
- Do not infer a condition, assign an ID to a condition, compare responses across trials, or reconcile with another evaluator.

The A target requires the full family-specific method/value/action. For FAMILY01 it includes both same-canopy away-sun 8-degree scans, immediate contact-leaf check after each, followed by mandatory M0 soil-moisture confirmation regardless. For FAMILY02 it includes 131 mg/L from the bounded in-envelope floc-rich relation; M0's ±12 mg/L uncertainty does not attach to that estimate. For FAMILY03 it selects verified group P for the one review slot while retaining M0 SCREEN_PASS for both and making no degradation or universal-threshold claim. B preserves its applicable M0 route. C routes unresolved or out-of-scope inputs to the frozen safe fallback and does not impute.

Return a complete 18-row JSON sheet with locked=true and raw per-case scores. Do not score dispositions, component thresholds, or aggregate outcomes.

## Required case-level output schema

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "task229-blind-evaluation-r0",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "rows"
  ],
  "properties": {
    "schema_version": {
      "const": "task229-blind-evaluation-r0"
    },
    "rows": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "response_id",
          "case_id",
          "success",
          "criterion_reference"
        ],
        "properties": {
          "response_id": {
            "type": "string",
            "minLength": 1
          },
          "case_id": {
            "enum": [
              "A",
              "B",
              "C"
            ]
          },
          "success": {
            "type": "boolean"
          },
          "criterion_reference": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  }
}

## Randomized blind packets

{
  "packets": [
    {
      "response_id": "ed6ad4e253c734fb143adb9f5f8cfc19",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 C — successor-visible case facts\n\nBlank, cell, and turbidity duplicate checks pass at 155 NTU. Composition aliquots are not reproducible and do not stably match either the measured mineral-dominant or floc-rich patterns. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 221.25,
        "target_action": "RECONCILE_COMPOSITION_OR_OBTAIN_GRAVIMETRY",
        "reason": "Composition aliquots do not reproducibly match an observed E1 composition tuple; no floc-rich point estimate is licensed."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "RECONCILE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F02A_MEASUREMENT_VALID": true,
              "F02A_COMPOSITION_PATTERN": "Nonreproducible composition; no stable match to either measured pattern",
              "turbidity_NTU": 155,
              "blank_cell_turbidity_duplicate_checks": "pass",
              "composition_aliquots_reproducible": false
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Zero selector matches: composition does not reproducibly match the observed organic-floc category.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "Preserved. Turbidity passes the supplied quality and range checks, but composition uncertainty prevents treating the calculation as a supported mass estimate for this sample.",
            "unit": null
          },
          {
            "name": "M0_estimate_for_comparison",
            "value": 221.25,
            "unit": "mg/L"
          },
          {
            "name": "independent_gravimetric_result",
            "value": null,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "RECONCILE: retain supplied values and M0 calculation, document unstable composition, and request independent composition and gravimetric review.",
        "scope": "No supported composition-specific point mapping or ±12 mg/L uncertainty claim. M0 remains available without extending its validated matrix.",
        "rationale": "Unstable composition does not match the selector and does not invalidate the passing turbidity checks. The measurement-invalid stop is not triggered. The arithmetic M0 result is 1.35 × 155 + 12 = 221.25 mg/L, retained only for comparison pending independent review."
      }
    },
    {
      "response_id": "090765660837af9ee8f7ec7b45d907ff",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 C — successor-visible case facts\n\nPartially covered reflective surface with measured reflectance range 0.18–0.69 and bearing varying between scans; valid D readings are 2.2/1.4 °C. Calibration and sensor-quality checks pass.\n",
      "frozen_target_case": {
        "m0_action": "REPEAT_THERMAL_SCAN",
        "target_action": "REPEAT_THERMAL_SCAN",
        "reason": "The pair straddles the 2.0 degree trigger and bearing varies; the stable reflective-context rule does not apply. Reacquire under stable coverage/view."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "REPEAT_THERMAL_SCAN"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F01A_MEASUREMENT_VALID": true,
              "F01A_SURFACE_PATTERN": "partially covered reflective surface",
              "F01A_BEARING_RELATION": "varying between scans",
              "reflectance_range": [
                0.18,
                0.69
              ],
              "paired_D_C": [
                2.2,
                1.4
              ],
              "calibration_and_sensor_quality": "pass"
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Zero selector matches: partial reflective coverage and varying bearing do not establish the specified silver-film and toward-sun pattern.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "REPEAT_THERMAL_SCAN: the valid pair straddles 2.0 °C. Its difference is 0.8 °C, not greater than 0.8 °C.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": "RECONCILE; preserve the M0 repeat-scan pathway and request independent review if the measurement context remains unresolved.",
        "scope": "Outside the selector's licensed pattern. No reflectance cutoff or corrected thermal threshold is established for partial coverage or varying bearing.",
        "rationale": "The supplied valid readings do not trigger the invalid-measurement stop. Neither the surface nor bearing matches the selector. M0 requires REPEAT_THERMAL_SCAN because 2.2/1.4 °C straddles its threshold; check setup and establish a consistent measurement context."
      }
    },
    {
      "response_id": "e7f2c787481b17f738353faf4760dde4",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 B — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger and aligned high-rate trace; all shipment and segment means are below 8.0 °C; no above-12 °C pulse is present; calibration, clock, and custody checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action": "SCREEN_PASS",
        "reason": "No above-12 degree C pulse is present; preserve M0."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "formulation_group",
            "value": "P",
            "unit": null
          },
          {
            "name": "above_12_C_pulse_present",
            "value": false,
            "unit": null
          },
          {
            "name": "all_segment_and_shipment_means_below_8_C",
            "value": true,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "M0 temperature screening only; no unconditional product-safety guarantee.",
        "rationale": "Required logger checks pass and all means are below the stated cutoff. The complete trace supplies no above-12 °C pulse concern, and [REDACTED] preserves a stable continuous-profile group-P example. The supplied evidence does not justify rejecting all group-P lots."
      }
    },
    {
      "response_id": "f5ec14cc2237c660bc4e47328a02240f",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 A — successor-visible case facts\n\nTwo independently registry-verified lots are available for one stability-review slot: one is formulation group P and one is group S. Both have complete calibrated 15-minute logger records and valid clock/custody checks; every segment and shipment mean is below 8.0 °C. Both have complete aligned high-rate traces. The group-P trace has a 9-minute excursion peaking at 13.7 °C; the group-S trace has a 10-minute excursion peaking at 14.0 °C. No assay or disposition result is provided. Select one lot for the available review slot.\n",
      "frozen_target_case": {
        "m0_actions": {
          "group_p": "SCREEN_PASS",
          "group_s": "SCREEN_PASS"
        },
        "target_action": {
          "group_p": "STABILITY_REVIEW",
          "group_s": "SCREEN_PASS"
        },
        "selected_for_single_review_slot": "group_p",
        "operational_policy": {
          "selector_inputs": [
            "independently registry-verified group P",
            "complete aligned high-rate trace",
            "pulse duration within 9–13 minutes",
            "pulse peak within 13.7–14.4 degrees C",
            "valid M0 means below 8.0 degrees C"
          ],
          "applicability_rule": "For a complete high-rate pulse within the observed group-P E1 context only, select group P for stability review even when M0's 15-minute means pass. The matched group-S pulsed control does not authorize a universal pulse rule.",
          "action_mapping": "Retain the M0 mean-only SCREEN_PASS as the baseline result and add STABILITY_REVIEW for the verified group-P lot. This is an independent review disposition, not a confirmed degradation or safety finding.",
          "preserved_rule_ids": [
            "M0_F03_LOGGER_CALIBRATION_CLOCK_CUSTODY",
            "M0_F03_MEAN_ONLY_SCREEN_PASS"
          ],
          "unresolved_or_fallback_rule": "If the required high-rate trace is incomplete or pulse duration cannot be determined, select RECONCILE_LOGGER; if unresolved, select UNSCORABLE. For a complete group-P trace without the observed pulse context, retain the M0 pass path.",
          "stop_conditions": [
            "No universal temperature or pulse-duration cutoff",
            "No automatic degradation claim",
            "No generalization from group P to group S or other formulations",
            "No replacement of M0 mean-only baseline"
          ],
          "scope_ceiling": "Verified group-P formulation, complete calibrated high-rate pulse context in the observed 9–13 minute / 13.7–14.4 degree C envelope, and stability-review triage only."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "STABILITY_REVIEW",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "selected_formulation_group",
            "value": "P",
            "unit": null
          },
          {
            "name": "selected_lot_excursion_duration",
            "value": 9,
            "unit": "min"
          },
          {
            "name": "selected_lot_peak_temperature",
            "value": 13.7,
            "unit": "°C"
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "Prioritize the group-P lot for the single review slot; no degradation or unconditional safety determination for either lot.",
        "rationale": "M0 would screen both lots pass. However, [REDACTED] through [REDACTED] show repeated below-reference activity in group P with short pulses, including the same duration and peak as the supplied group-P excursion in [REDACTED]. [REDACTED] shows retained activity above reference in group S with a similar pulse. This supports prioritizing group P without establishing a universal pulse threshold."
      }
    },
    {
      "response_id": "ea7002732b73f2629cd308902938bcde",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 A — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 150 NTU. Reproducible composition is 21% mineral grains and 46% organic flocs; the remainder is mixed fines. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 214.5,
        "m0_uncertainty_mg_l": 12,
        "target_action": "REPORT_ESTIMATE",
        "target_value_mg_l": 131,
        "operational_policy": {
          "selector_inputs": [
            "QC-passing composition matching the observed floc-rich pattern",
            "blank-corrected turbidity from 100 through 300 NTU"
          ],
          "applicability_rule": "Use only for reproducible QC-passing composition matching one of the observed E1 floc-rich tuples: (21% mineral, 46% organic flocs), (18%, 49%), or (24%, 42%), and turbidity within the observed 100–300 NTU span. Do not treat the independent minimum/maximum values as permission for unobserved composition pairs.",
          "action_mapping": "Use the E1 floc-rich empirical relation at 100/200/300 NTU (91/171/251 mg/L) and linearly interpolate only within that turbidity span. At 150 NTU the estimate is 131 mg/L. E1 provides no uncertainty band for this estimate; do not transfer M0's ±12 mg/L band.",
          "preserved_rule_ids": [
            "M0_F02_QC_AND_DUPLICATE_CHECKS",
            "M0_F02_MINERAL_DOMINANT_REPORT_ESTIMATE"
          ],
          "unresolved_or_fallback_rule": "Outside an exact observed floc-rich composition tuple, outside 100–300 NTU, or when composition/QC is unresolved, request or reconcile composition and/or obtain gravimetry; do not apply the floc-rich point relation.",
          "stop_conditions": [
            "No universal mineral/floc cutoff",
            "No composition-pair interpolation beyond the observed tuples",
            "No turbidity extrapolation beyond 100–300 NTU",
            "No ±12 mg/L uncertainty claim for the E1 estimate"
          ],
          "scope_ceiling": "Exact observed floc-rich composition tuples and 100–300 NTU; no universal formula or inference beyond the synthetic E1 evidence."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "RECONCILE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F02B_MEASUREMENT_VALID": true,
              "F02B_COMPOSITION_REPRODUCIBLE": true,
              "F02B_GRAVIMETRIC_REPLICATES_AGREE": null,
              "turbidity_NTU": 150,
              "mineral_grains_percent": 21,
              "organic_flocs_percent": 46,
              "remainder": "mixed fines",
              "gravimetric_reference": null
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Composition is reproducible, so the selector does not match; gravimetric replicate agreement is also unavailable.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "Preserved. The in-range M0 calculation is 214.5 mg/L, but its original ±12 mg/L uncertainty band is not validated for this composition.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "Record supplied values and request independent review of calibration applicability.",
        "scope": "No composition-specific point mapping or universal composition threshold is supplied.",
        "rationale": "Valid turbidity measurements do not establish calibration accuracy for this composition. Missing gravimetric evidence cannot be treated as replicate disagreement."
      }
    },
    {
      "response_id": "1939722f962245855d583cf5b1c556a6",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 B — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 250 NTU. Reproducible composition is 84% mineral grains and 3% organic flocs, matching the measured mineral-dominant pattern. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 349.5,
        "target_action": "REPORT_ESTIMATE",
        "target_method": "M0 mineral-dominant formula; preserve baseline scope"
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "M0 TSS estimate",
            "value": 349.5,
            "unit": "mg/L"
          },
          {
            "name": "Original mineral-matrix calibration uncertainty band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "M0 mineral-dominant calibration scope, 0–500 NTU; uncertainty band is ±12 mg/L for the original calibration matrix.",
        "rationale": "Checks pass, turbidity is in range, and composition matches the mineral-dominant pattern supported by [REDACTED] through [REDACTED]. Applying M0 gives 1.35 × 250 + 12 = 349.5 mg/L. No gravimetric reference confirms this individual estimate."
      }
    },
    {
      "response_id": "7b2083c3753f556945c2071650a6a3b1",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 A — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 150 NTU. Reproducible composition is 21% mineral grains and 46% organic flocs; the remainder is mixed fines. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 214.5,
        "m0_uncertainty_mg_l": 12,
        "target_action": "REPORT_ESTIMATE",
        "target_value_mg_l": 131,
        "operational_policy": {
          "selector_inputs": [
            "QC-passing composition matching the observed floc-rich pattern",
            "blank-corrected turbidity from 100 through 300 NTU"
          ],
          "applicability_rule": "Use only for reproducible QC-passing composition matching one of the observed E1 floc-rich tuples: (21% mineral, 46% organic flocs), (18%, 49%), or (24%, 42%), and turbidity within the observed 100–300 NTU span. Do not treat the independent minimum/maximum values as permission for unobserved composition pairs.",
          "action_mapping": "Use the E1 floc-rich empirical relation at 100/200/300 NTU (91/171/251 mg/L) and linearly interpolate only within that turbidity span. At 150 NTU the estimate is 131 mg/L. E1 provides no uncertainty band for this estimate; do not transfer M0's ±12 mg/L band.",
          "preserved_rule_ids": [
            "M0_F02_QC_AND_DUPLICATE_CHECKS",
            "M0_F02_MINERAL_DOMINANT_REPORT_ESTIMATE"
          ],
          "unresolved_or_fallback_rule": "Outside an exact observed floc-rich composition tuple, outside 100–300 NTU, or when composition/QC is unresolved, request or reconcile composition and/or obtain gravimetry; do not apply the floc-rich point relation.",
          "stop_conditions": [
            "No universal mineral/floc cutoff",
            "No composition-pair interpolation beyond the observed tuples",
            "No turbidity extrapolation beyond 100–300 NTU",
            "No ±12 mg/L uncertainty claim for the E1 estimate"
          ],
          "scope_ceiling": "Exact observed floc-rich composition tuples and 100–300 NTU; no universal formula or inference beyond the synthetic E1 evidence."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [
          "Obtain independent gravimetric confirmation."
        ],
        "reported_values": [
          {
            "name": "Provisional floc-rich TSS estimate",
            "value": 131,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "Use independent constant-weight gravimetry if a confirmed concentration is required.",
        "scope": "Provisional interpolation within the observed floc-rich pattern and 100–300 NTU interval; no validated uncertainty band.",
        "rationale": "The reproducible composition matches [REDACTED]. [REDACTED] through [REDACTED] support the provisional local relationship TSS = 0.80 × T + 11, yielding 131 mg/L at 150 NTU. This is an inferred interpolation, not a supplied or validated revised calibration. M0's universal composition premise is contradicted by these observations, and its ±12 mg/L band cannot be transferred to this estimate."
      }
    },
    {
      "response_id": "290e8c13e7a84834b34a7bdc85d6451a",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 B — successor-visible case facts\n\nCalibrated setup; ordinary mineral-soil surface with reflectance 0.15; toward-sun bearing at 21° off nadir; valid stable paired D readings 2.5/2.4 °C. Required M0 inputs are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action": "SOIL_MOISTURE_CONFIRMATION",
        "reason": "The reflective-film selector is absent; preserve the M0 path."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F01B_MEASUREMENT_VALID": true,
              "F01B_SURFACE_COVERAGE_COMPLETE": null,
              "F01B_PAIRED_READING_PATTERN": "stable",
              "surface": "ordinary mineral soil",
              "reflectance": 0.15,
              "bearing": "toward sun",
              "off_nadir_degrees": 21,
              "paired_D_C": [
                2.5,
                2.4
              ]
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Surface-coverage completeness is not explicitly supplied; stable readings do not match the variable_observed selector condition.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "SOIL_MOISTURE_CONFIRMATION: valid paired readings differ by 0.1 °C and both meet the 2.0 °C threshold.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": "Record supplied values and unmatched routing; retain M0 soil-moisture confirmation and request independent review when needed.",
        "scope": "The ordinary-surface M0 pathway remains available. Thermal evidence does not authorize irrigation.",
        "rationale": "The bounded selector does not match. Both valid stable D readings trigger confirmation under M0."
      }
    },
    {
      "response_id": "0352d9ccd7da33ac1b627946cfcbad1e",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 A — successor-visible case facts\n\nTwo independently registry-verified lots are available for one stability-review slot: one is formulation group P and one is group S. Both have complete calibrated 15-minute logger records and valid clock/custody checks; every segment and shipment mean is below 8.0 °C. Both have complete aligned high-rate traces. The group-P trace has a 9-minute excursion peaking at 13.7 °C; the group-S trace has a 10-minute excursion peaking at 14.0 °C. No assay or disposition result is provided. Select one lot for the available review slot.\n",
      "frozen_target_case": {
        "m0_actions": {
          "group_p": "SCREEN_PASS",
          "group_s": "SCREEN_PASS"
        },
        "target_action": {
          "group_p": "STABILITY_REVIEW",
          "group_s": "SCREEN_PASS"
        },
        "selected_for_single_review_slot": "group_p",
        "operational_policy": {
          "selector_inputs": [
            "independently registry-verified group P",
            "complete aligned high-rate trace",
            "pulse duration within 9–13 minutes",
            "pulse peak within 13.7–14.4 degrees C",
            "valid M0 means below 8.0 degrees C"
          ],
          "applicability_rule": "For a complete high-rate pulse within the observed group-P E1 context only, select group P for stability review even when M0's 15-minute means pass. The matched group-S pulsed control does not authorize a universal pulse rule.",
          "action_mapping": "Retain the M0 mean-only SCREEN_PASS as the baseline result and add STABILITY_REVIEW for the verified group-P lot. This is an independent review disposition, not a confirmed degradation or safety finding.",
          "preserved_rule_ids": [
            "M0_F03_LOGGER_CALIBRATION_CLOCK_CUSTODY",
            "M0_F03_MEAN_ONLY_SCREEN_PASS"
          ],
          "unresolved_or_fallback_rule": "If the required high-rate trace is incomplete or pulse duration cannot be determined, select RECONCILE_LOGGER; if unresolved, select UNSCORABLE. For a complete group-P trace without the observed pulse context, retain the M0 pass path.",
          "stop_conditions": [
            "No universal temperature or pulse-duration cutoff",
            "No automatic degradation claim",
            "No generalization from group P to group S or other formulations",
            "No replacement of M0 mean-only baseline"
          ],
          "scope_ceiling": "Verified group-P formulation, complete calibrated high-rate pulse context in the observed 9–13 minute / 13.7–14.4 degree C envelope, and stability-review triage only."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "STABILITY_REVIEW"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F03B_MEASUREMENT_VALID": true,
              "F03B_HIGH_RATE_TRACE_COMPLETE": true,
              "F03B_ASSAY_REPLICATES_RECONCILE": null,
              "both_lots_means_below_8_C": true,
              "group_P_excursion": {
                "duration_minutes": 9,
                "peak_C": 13.7
              },
              "group_S_excursion": {
                "duration_minutes": 10,
                "peak_C": 14.0
              }
            },
            "unit": null
          },
          {
            "name": "selected_review_lot",
            "value": "P",
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Complete high-rate traces exclude the selector pattern; assay reconciliation inputs are unavailable.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "SCREEN_PASS for both lots under the baseline mean criterion.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "Record supplied inputs and preserve M0 screening; allocate the independent review slot to group P.",
        "scope": "Review prioritization only; no pulse threshold or confirmed degradation conclusion.",
        "rationale": "The policy requires fallback. Within its independent-review provision, prioritize P because the supplied evidence records reduced activity in observed pulsed P lots while the observed pulsed S lot retained activity. This supports a bounded review priority, not a predicted assay result."
      }
    },
    {
      "response_id": "eb7b7437c2ec816b6eb266b5ae4f78a3",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 A — successor-visible case facts\n\nCalibrated radiometric camera and matched shielded air sensor; same marked canopy; valid stable paired D readings 2.7/2.6 °C. Ground cover is reflective silver film with measured reflectance 0.72; the camera bearing is toward the sun at 21° off nadir. Required M0 calibration, time, mask, geometry, and sensor-quality fields are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action_sequence": [
          "REFLECTION_CONTROL_SCAN_OR_CONTACT_CHECK",
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "operational_policy": {
          "selector_inputs": [
            "reflective silver film at measured reflectance 0.72",
            "toward-sun view at 21 degrees off nadir",
            "same marked canopy and calibrated camera",
            "stable high D pair"
          ],
          "applicability_rule": "For this observed stable reflective-film/toward-sun/21-degree context only, do not treat stable high D as sufficient to rely on the ordinary M0 thermal-trigger path until the measurement-control discriminator is resolved.",
          "action_mapping": "Acquire two same-canopy scans with the view changed away from the sun to 8 degrees off nadir; take a contact-leaf reference immediately after each scan and record the paired comparisons. Then retain the M0 soil-moisture confirmation regardless of the comparison. Do not infer stress or irrigation.",
          "preserved_rule_ids": [
            "M0_F01_CALIBRATION_QC",
            "M0_F01_STABLE_HIGH_D_SOIL_MOISTURE_CONFIRMATION"
          ],
          "unresolved_or_fallback_rule": "If coverage, bearing, or the required control measurements are invalid or incomplete, reacquire under stable coverage/view and retain the M0 confirmation path; do not infer stress or irrigation.",
          "stop_conditions": [
            "No universal reflectance cutoff",
            "No universal view-angle cutoff",
            "No changed D threshold",
            "No stress or irrigation disposition from thermal evidence alone"
          ],
          "scope_ceiling": "The measured reflective-silver-film/toward-sun/21-degree case context and the E1-observed away-sun 8-degree comparison; no population or universal physical claim."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "D_scan_1",
            "value": 2.7,
            "unit": "°C"
          },
          {
            "name": "D_scan_2",
            "value": 2.6,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.72,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Independent soil-moisture triage only; no irrigation authorization or established plant stress.",
        "rationale": "Both valid D readings exceed M0's 2.0 °C criterion and differ by only 0.1 °C. The surface and bearing match the measurement context implicated by [REDACTED] and [REDACTED], so a thermal false positive is plausible. Those observations do not supply a revised routing rule or establish this case's VWC. Preserve M0's confirmation action and assess the independent soil measurement."
      }
    },
    {
      "response_id": "1592265ddc29b2d8a29922c6c12774e9",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 B — successor-visible case facts\n\nCalibrated setup; ordinary mineral-soil surface with reflectance 0.15; toward-sun bearing at 21° off nadir; valid stable paired D readings 2.5/2.4 °C. Required M0 inputs are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action": "SOIL_MOISTURE_CONFIRMATION",
        "reason": "The reflective-film selector is absent; preserve the M0 path."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "D_scan_1",
            "value": 2.5,
            "unit": "°C"
          },
          {
            "name": "D_scan_2",
            "value": 2.4,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.15,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Ordinary mineral-soil thermal triage; independent VWC and plant-water evidence govern subsequent review.",
        "rationale": "Both valid D readings exceed 2.0 °C and differ by only 0.1 °C, selecting confirmation under M0. [REDACTED] supports retaining this ordinary-surface pathway, but its VWC and plant-water observations cannot be assigned to this case."
      }
    },
    {
      "response_id": "253085a12529d9d443b906df00b8e627",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 B — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 250 NTU. Reproducible composition is 84% mineral grains and 3% organic flocs, matching the measured mineral-dominant pattern. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 349.5,
        "target_action": "REPORT_ESTIMATE",
        "target_method": "M0 mineral-dominant formula; preserve baseline scope"
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "Turbidity",
            "value": 250,
            "unit": "NTU"
          },
          {
            "name": "M0 estimated TSS",
            "value": 349.5,
            "unit": "mg/L"
          },
          {
            "name": "Original-matrix calibration uncertainty band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "CE-F02-M0-R0 mineral-dominant calibration; validated turbidity range 0–500 NTU; uncertainty ±12 mg/L.",
        "rationale": "Checks pass and composition matches the measured mineral-dominant pattern supported by [REDACTED] through [REDACTED]. Applying 1.35 × 250 + 12 gives 349.5 mg/L. No independent reference establishes this case's actual residual."
      }
    },
    {
      "response_id": "ed45b9abf8cec51da2140d865bd9a111",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 B — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 250 NTU. Reproducible composition is 84% mineral grains and 3% organic flocs, matching the measured mineral-dominant pattern. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 349.5,
        "target_action": "REPORT_ESTIMATE",
        "target_method": "M0 mineral-dominant formula; preserve baseline scope"
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "REPORT_ESTIMATE"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F02B_MEASUREMENT_VALID": true,
              "F02B_COMPOSITION_REPRODUCIBLE": true,
              "F02B_GRAVIMETRIC_REPLICATES_AGREE": null,
              "turbidity_NTU": 250,
              "mineral_grains_percent": 84,
              "organic_flocs_percent": 3,
              "matches_measured_mineral_dominant_pattern": true,
              "gravimetric_reference": null
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Reproducible composition does not match the selector; gravimetric replicate agreement is unavailable.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "Preserved and applicable to the supplied mineral-dominant pattern. REPORT_ESTIMATE uses CE-F02-M0-R0 within its 0–500 NTU range.",
            "unit": null
          },
          {
            "name": "M0_estimated_TSS",
            "value": 349.5,
            "unit": "mg/L"
          },
          {
            "name": "original_matrix_calibration_uncertainty_plus_minus",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "Record supplied values and preserve the applicable M0 reporting pathway.",
        "scope": "Original mineral-dominant calibration scope; the estimate lacks a sample-specific gravimetric verification.",
        "rationale": "The policy selector does not match. The preserved baseline yields 1.35 × 250 + 12 = 349.5 mg/L for the stated matching mineral-dominant pattern."
      }
    },
    {
      "response_id": "8c4a59173a5ca7b87843d0c792e85636",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 C — successor-visible case facts\n\nPartially covered reflective surface with measured reflectance range 0.18–0.69 and bearing varying between scans; valid D readings are 2.2/1.4 °C. Calibration and sensor-quality checks pass.\n",
      "frozen_target_case": {
        "m0_action": "REPEAT_THERMAL_SCAN",
        "target_action": "REPEAT_THERMAL_SCAN",
        "reason": "The pair straddles the 2.0 degree trigger and bearing varies; the stable reflective-context rule does not apply. Reacquire under stable coverage/view."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "F01B_REACQUIRE_CONTEXT",
        "additional_actions": [
          "REPEAT_THERMAL_SCAN"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F01B_MEASUREMENT_VALID": true,
              "F01B_SURFACE_COVERAGE_COMPLETE": false,
              "F01B_PAIRED_READING_PATTERN": "variable_observed"
            },
            "unit": null
          },
          {
            "name": "F01B_COVERAGE_AND_VARIATION",
            "value": {
              "surface_coverage": "partial reflective coverage",
              "reflectance_range": [
                0.18,
                0.69
              ],
              "scan_bearing": "varies between scans",
              "paired_D_C": [
                2.2,
                1.4
              ],
              "mask_status": "not separately supplied",
              "contact_reference_variation": "not supplied",
              "calibration_and_sensor_quality": "pass"
            },
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "REPEAT_THERMAL_SCAN: the pair straddles 2.0 °C; its 0.8 °C difference does not exceed the disagreement limit.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Reacquire complete surface and paired-reading context for this incomplete-coverage, variable-reading pattern. No new numeric threshold or causal conclusion is established.",
        "rationale": "Valid measurements, partial coverage, and the observed variable pair match F01B_INCOMPLETE_VARIABLE_CONTEXT, whose action_ref is F01B_REACQUIRE_CONTEXT."
      }
    },
    {
      "response_id": "a4344a7bf34c022c1b4e817bc558d4bf",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 C — successor-visible case facts\n\nBlank, cell, and turbidity duplicate checks pass at 155 NTU. Composition aliquots are not reproducible and do not stably match either the measured mineral-dominant or floc-rich patterns. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 221.25,
        "target_action": "RECONCILE_COMPOSITION_OR_OBTAIN_GRAVIMETRY",
        "reason": "Composition aliquots do not reproducibly match an observed E1 composition tuple; no floc-rich point estimate is licensed."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "estimated_TSS",
            "value": 221.25,
            "unit": "mg/L"
          },
          {
            "name": "original_calibration_matrix_uncertainty_band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "CE-F02-M0-R0; validated turbidity range 0–500 NTU. The ±12 mg/L band applies to the original mineral-dominant calibration matrix; this sample's matrix applicability is unresolved.",
        "rationale": "Blank, cell, and turbidity duplicate checks pass at 155 NTU, so M0 reports 1.35 × 155 + 12 = 221.25 mg/L. Unstable composition aliquots do not trigger M0's turbidity replicate rule because composition is not an M0 input. No gravimetric reference establishes the estimate's error."
      }
    },
    {
      "response_id": "a96cbb608c620826524821f844a3280b",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 A — successor-visible case facts\n\nCalibrated radiometric camera and matched shielded air sensor; same marked canopy; valid stable paired D readings 2.7/2.6 °C. Ground cover is reflective silver film with measured reflectance 0.72; the camera bearing is toward the sun at 21° off nadir. Required M0 calibration, time, mask, geometry, and sensor-quality fields are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action_sequence": [
          "REFLECTION_CONTROL_SCAN_OR_CONTACT_CHECK",
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "operational_policy": {
          "selector_inputs": [
            "reflective silver film at measured reflectance 0.72",
            "toward-sun view at 21 degrees off nadir",
            "same marked canopy and calibrated camera",
            "stable high D pair"
          ],
          "applicability_rule": "For this observed stable reflective-film/toward-sun/21-degree context only, do not treat stable high D as sufficient to rely on the ordinary M0 thermal-trigger path until the measurement-control discriminator is resolved.",
          "action_mapping": "Acquire two same-canopy scans with the view changed away from the sun to 8 degrees off nadir; take a contact-leaf reference immediately after each scan and record the paired comparisons. Then retain the M0 soil-moisture confirmation regardless of the comparison. Do not infer stress or irrigation.",
          "preserved_rule_ids": [
            "M0_F01_CALIBRATION_QC",
            "M0_F01_STABLE_HIGH_D_SOIL_MOISTURE_CONFIRMATION"
          ],
          "unresolved_or_fallback_rule": "If coverage, bearing, or the required control measurements are invalid or incomplete, reacquire under stable coverage/view and retain the M0 confirmation path; do not infer stress or irrigation.",
          "stop_conditions": [
            "No universal reflectance cutoff",
            "No universal view-angle cutoff",
            "No changed D threshold",
            "No stress or irrigation disposition from thermal evidence alone"
          ],
          "scope_ceiling": "The measured reflective-silver-film/toward-sun/21-degree case context and the E1-observed away-sun 8-degree comparison; no population or universal physical claim."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [
          "REPEAT_THERMAL_SCAN"
        ],
        "reported_values": [
          {
            "name": "D_scan_1",
            "value": 2.7,
            "unit": "°C"
          },
          {
            "name": "D_scan_2",
            "value": 2.6,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.72,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Independent soil-moisture triage only; possible reflected-radiance contamination requires investigation.",
        "rationale": "Both valid D readings exceed M0's 2.0 °C threshold, selecting confirmation. The surface and bearing match the measurement context implicated by [REDACTED] through [REDACTED], so additionally repeat the scan with a bearing comparison and contact-leaf check. Those observations do not establish this case's VWC or justify a replacement threshold. Do not infer irrigation or plant stress from D alone."
      }
    },
    {
      "response_id": "97686007dab6abacc8db1267f71ee2cc",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 A — successor-visible case facts\n\nCalibrated radiometric camera and matched shielded air sensor; same marked canopy; valid stable paired D readings 2.7/2.6 °C. Ground cover is reflective silver film with measured reflectance 0.72; the camera bearing is toward the sun at 21° off nadir. Required M0 calibration, time, mask, geometry, and sensor-quality fields are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action_sequence": [
          "REFLECTION_CONTROL_SCAN_OR_CONTACT_CHECK",
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "operational_policy": {
          "selector_inputs": [
            "reflective silver film at measured reflectance 0.72",
            "toward-sun view at 21 degrees off nadir",
            "same marked canopy and calibrated camera",
            "stable high D pair"
          ],
          "applicability_rule": "For this observed stable reflective-film/toward-sun/21-degree context only, do not treat stable high D as sufficient to rely on the ordinary M0 thermal-trigger path until the measurement-control discriminator is resolved.",
          "action_mapping": "Acquire two same-canopy scans with the view changed away from the sun to 8 degrees off nadir; take a contact-leaf reference immediately after each scan and record the paired comparisons. Then retain the M0 soil-moisture confirmation regardless of the comparison. Do not infer stress or irrigation.",
          "preserved_rule_ids": [
            "M0_F01_CALIBRATION_QC",
            "M0_F01_STABLE_HIGH_D_SOIL_MOISTURE_CONFIRMATION"
          ],
          "unresolved_or_fallback_rule": "If coverage, bearing, or the required control measurements are invalid or incomplete, reacquire under stable coverage/view and retain the M0 confirmation path; do not infer stress or irrigation.",
          "stop_conditions": [
            "No universal reflectance cutoff",
            "No universal view-angle cutoff",
            "No changed D threshold",
            "No stress or irrigation disposition from thermal evidence alone"
          ],
          "scope_ceiling": "The measured reflective-silver-film/toward-sun/21-degree case context and the E1-observed away-sun 8-degree comparison; no population or universal physical claim."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "F01A_ROUTE_CONTACT_CONTEXT",
        "additional_actions": [
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "reported_values": [
          {
            "name": "F01A_OBSERVED_CONTEXT",
            "value": {
              "surface": "reflective silver film",
              "reflectance": 0.72,
              "bearing": "toward sun, 21 degrees off nadir",
              "paired_D_C": [
                2.7,
                2.6
              ],
              "contact_check": "not supplied; obtain independent contact check",
              "VWC": "not supplied; obtain independent VWC measurement"
            },
            "unit": null
          },
          {
            "name": "supplied_inputs",
            "value": {
              "F01A_MEASUREMENT_VALID": true,
              "F01A_SURFACE_PATTERN": "reflective_silver_film_observed",
              "F01A_BEARING_RELATION": "toward_sun_observed"
            },
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Independent contact and VWC review for the specified silver-film and toward-sun context. No thermal correction, universal reflectance cutoff, or irrigation authorization.",
        "rationale": "F01A_OBSERVED_REFLECTIVE_CONTEXT matches all three inputs and references F01A_ROUTE_CONTACT_CONTEXT. The preserved M0 pathway also selects SOIL_MOISTURE_CONFIRMATION because both D values exceed 2.0 °C and differ by only 0.1 °C."
      }
    },
    {
      "response_id": "95f31fd99160ddd5e87d88d4643154ec",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 C — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger means are below 8.0 °C. The high-rate trace has a custody gap across handoff, so pulse duration cannot be determined. Calibration and 15-minute logger checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action_sequence": [
          "RECONCILE_LOGGER",
          "UNSCORABLE_IF_TRACE_REMAINS_UNRESOLVED"
        ],
        "reason": "M0 means do not reveal a missing high-rate trace; the revision requires the trace for pulse evaluation."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "high_rate_pulse_duration",
            "value": null,
            "unit": "minutes"
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "M0 screening using the complete validated 15-minute logger; high-rate pulse exposure remains unresolved.",
        "rationale": "The required 15-minute logger checks pass and its means are below 8.0 °C. The custody gap affects the supplementary high-rate trace, which M0 does not require or use to determine pulse duration. It does not establish a failure of the required logger's custody checks."
      }
    },
    {
      "response_id": "4eedc1a6c2fb44daa4c7d1ed5390a186",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 C — successor-visible case facts\n\nBlank, cell, and turbidity duplicate checks pass at 155 NTU. Composition aliquots are not reproducible and do not stably match either the measured mineral-dominant or floc-rich patterns. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 221.25,
        "target_action": "RECONCILE_COMPOSITION_OR_OBTAIN_GRAVIMETRY",
        "reason": "Composition aliquots do not reproducibly match an observed E1 composition tuple; no floc-rich point estimate is licensed."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "estimated_TSS",
            "value": 221.25,
            "unit": "mg/L"
          },
          {
            "name": "original_calibration_matrix_uncertainty_band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "CE-F02-M0-R0; validated turbidity range 0–500 NTU. Applicability of the original mineral-dominant matrix's ±12 mg/L band is unresolved because composition is not reproducible.",
        "rationale": "Blank, cell, and turbidity duplicate checks pass at 155 NTU. M0 calculates 1.35 × 155 + 12 = 221.25 mg/L. Unstable composition aliquots do not trigger M0's turbidity replicate rule, and M0 supplies no composition-based stop. Without a gravimetric reference, sample-specific error cannot be established."
      }
    },
    {
      "response_id": "665bf7adadf7582c273e6a5b792ec906",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 B — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger and aligned high-rate trace; all shipment and segment means are below 8.0 °C; no above-12 °C pulse is present; calibration, clock, and custody checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action": "SCREEN_PASS",
        "reason": "No above-12 degree C pulse is present; preserve M0."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "all_segment_and_shipment_means_below_8_C",
            "value": true,
            "unit": null
          },
          {
            "name": "above_12_C_pulse_present",
            "value": false,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "M0 temperature screening only.",
        "rationale": "Required inputs and logger checks pass, and all means are below 8.0 °C. The high-rate observation does not introduce an additional M0 criterion. This is a triage pass, not an unconditional product-safety guarantee."
      }
    },
    {
      "response_id": "0c88ca7d192717bfd65253da46bed7ae",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 C — successor-visible case facts\n\nBlank, cell, and turbidity duplicate checks pass at 155 NTU. Composition aliquots are not reproducible and do not stably match either the measured mineral-dominant or floc-rich patterns. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 221.25,
        "target_action": "RECONCILE_COMPOSITION_OR_OBTAIN_GRAVIMETRY",
        "reason": "Composition aliquots do not reproducibly match an observed E1 composition tuple; no floc-rich point estimate is licensed."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "Withhold a supported concentration estimate",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "Turbidity",
            "value": 155,
            "unit": "NTU"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "Representative sampling and independent constant-weight gravimetry would be needed to resolve concentration and aliquot variability.",
        "scope": "Valid in-range turbidity with nonreproducible composition.",
        "rationale": "The composition does not support a stable calibration assignment. [REDACTED] demonstrates that stable turbidity can coexist with composition and gravimetric variability. No supplied rule resolves this mixture; passing turbidity checks neither establishes a concentration mapping nor triggers INVALID_MEASUREMENT."
      }
    },
    {
      "response_id": "0f2a73fd4a5b2245522091cec6626b3c",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 C — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger means are below 8.0 °C. The high-rate trace has a custody gap across handoff, so pulse duration cannot be determined. Calibration and 15-minute logger checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action_sequence": [
          "RECONCILE_LOGGER",
          "UNSCORABLE_IF_TRACE_REMAINS_UNRESOLVED"
        ],
        "reason": "M0 means do not reveal a missing high-rate trace; the revision requires the trace for pulse evaluation."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "RECONCILE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F03B_MEASUREMENT_VALID": true,
              "F03B_HIGH_RATE_TRACE_COMPLETE": false,
              "F03B_ASSAY_REPLICATES_RECONCILE": null,
              "formulation_group": "P",
              "all_means_below_8_C": true,
              "high_rate_trace_custody_gap": true,
              "pulse_duration": null
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Assay replicate reconciliation is unavailable; a trace gap alone does not satisfy the selector.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "The supplied passing 15-minute logger checks and means satisfy the baseline SCREEN_PASS criterion; the separate high-rate custody gap remains unresolved.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "Record the handoff custody gap and unavailable assay information; reconcile the high-rate record and seek independent review as needed.",
        "scope": "Record reconciliation only; neither a pulse nor degradation is established.",
        "rationale": "Baseline measurement checks pass, while high-rate completeness is false. Missing assay evidence cannot be treated as non-reconciling replicates, so the selector is not established and fallback applies."
      }
    },
    {
      "response_id": "40e5ca91f0222d6451a61d9ced0606d8",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 A — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 150 NTU. Reproducible composition is 21% mineral grains and 46% organic flocs; the remainder is mixed fines. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 214.5,
        "m0_uncertainty_mg_l": 12,
        "target_action": "REPORT_ESTIMATE",
        "target_value_mg_l": 131,
        "operational_policy": {
          "selector_inputs": [
            "QC-passing composition matching the observed floc-rich pattern",
            "blank-corrected turbidity from 100 through 300 NTU"
          ],
          "applicability_rule": "Use only for reproducible QC-passing composition matching one of the observed E1 floc-rich tuples: (21% mineral, 46% organic flocs), (18%, 49%), or (24%, 42%), and turbidity within the observed 100–300 NTU span. Do not treat the independent minimum/maximum values as permission for unobserved composition pairs.",
          "action_mapping": "Use the E1 floc-rich empirical relation at 100/200/300 NTU (91/171/251 mg/L) and linearly interpolate only within that turbidity span. At 150 NTU the estimate is 131 mg/L. E1 provides no uncertainty band for this estimate; do not transfer M0's ±12 mg/L band.",
          "preserved_rule_ids": [
            "M0_F02_QC_AND_DUPLICATE_CHECKS",
            "M0_F02_MINERAL_DOMINANT_REPORT_ESTIMATE"
          ],
          "unresolved_or_fallback_rule": "Outside an exact observed floc-rich composition tuple, outside 100–300 NTU, or when composition/QC is unresolved, request or reconcile composition and/or obtain gravimetry; do not apply the floc-rich point relation.",
          "stop_conditions": [
            "No universal mineral/floc cutoff",
            "No composition-pair interpolation beyond the observed tuples",
            "No turbidity extrapolation beyond 100–300 NTU",
            "No ±12 mg/L uncertainty claim for the E1 estimate"
          ],
          "scope_ceiling": "Exact observed floc-rich composition tuples and 100–300 NTU; no universal formula or inference beyond the synthetic E1 evidence."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "F02A_GRAVIMETRIC_REVIEW",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "F02A_MEASUREMENT_VALID",
            "value": true,
            "unit": null
          },
          {
            "name": "F02A_COMPOSITION_PATTERN",
            "value": "observed_organic_floc_cases",
            "unit": null
          },
          {
            "name": "turbidity",
            "value": 150,
            "unit": "NTU"
          },
          {
            "name": "composition_assay",
            "value": {
              "mineral_grains_percent": 21,
              "organic_flocs_percent": 46,
              "remainder": "mixed fines",
              "reproducible": true
            },
            "unit": null
          },
          {
            "name": "turbidity_duplicates",
            "value": "Checks pass; individual readings not supplied.",
            "unit": null
          },
          {
            "name": "M0_estimate_for_comparison",
            "value": 214.5,
            "unit": "mg/L"
          },
          {
            "name": "independent_gravimetric_result",
            "value": null,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "Independent gravimetric review of the represented organic-floc pattern. The M0 uncertainty band is not established for this composition.",
        "rationale": "Valid measurement and reproducible 21% mineral grains / 46% organic flocs match F02A_OBSERVED_ORGANIC_FLOC_PATTERN, whose action reference is F02A_GRAVIMETRIC_REVIEW. Record the M0 calculation as a comparison and obtain independent gravimetry; no replacement formula or composition cutoff is established."
      }
    },
    {
      "response_id": "067eaaaecb7b056f5bced12b16d23e37",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 B — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger and aligned high-rate trace; all shipment and segment means are below 8.0 °C; no above-12 °C pulse is present; calibration, clock, and custody checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action": "SCREEN_PASS",
        "reason": "No above-12 degree C pulse is present; preserve M0."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "SCREEN_PASS"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F03A_MEASUREMENT_VALID": true,
              "F03A_FORMULATION_GROUP": "P",
              "F03A_PULSE_PATTERN": "No above-12 °C pulse present",
              "records": "Complete calibrated 15-minute logger and aligned high-rate trace; calibration, clock, and custody checks pass",
              "means": "All segment and shipment means below 8.0 °C"
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Zero matching selector rules: the observed group-P pulse pattern is absent.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "SCREEN_PASS under the complete, valid baseline record and mean criterion.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "RECONCILE: record the supplied inputs and zero-match reason while preserving the M0 SCREEN_PASS pathway.",
        "scope": "Baseline temperature screening only; no unconditional product-safety guarantee.",
        "rationale": "Valid measurements avoid the stop condition, but group P alone does not satisfy the selector. The fallback applies, and the supplied baseline checks support SCREEN_PASS."
      }
    },
    {
      "response_id": "487044e41eee0495ddf4ca6f7d1189d1",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 B — successor-visible case facts\n\nCalibrated setup; ordinary mineral-soil surface with reflectance 0.15; toward-sun bearing at 21° off nadir; valid stable paired D readings 2.5/2.4 °C. Required M0 inputs are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action": "SOIL_MOISTURE_CONFIRMATION",
        "reason": "The reflective-film selector is absent; preserve the M0 path."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "paired_D",
            "value": [
              2.5,
              2.4
            ],
            "unit": "°C"
          },
          {
            "name": "absolute_pair_difference",
            "value": 0.1,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.15,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Thermal triage for independent root-zone VWC confirmation only; no irrigation authorization or established plant stress.",
        "rationale": "Required inputs are valid, the pair differs by less than 0.8 °C, and both D values are at least 2.0 °C. Ordinary mineral soil is a listed calibration surface. Send a technician to measure VWC at the fixed root-zone probe."
      }
    },
    {
      "response_id": "c3fda147bc9cfafbb9c488f2161d3b9d",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 C — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger means are below 8.0 °C. The high-rate trace has a custody gap across handoff, so pulse duration cannot be determined. Calibration and 15-minute logger checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action_sequence": [
          "RECONCILE_LOGGER",
          "UNSCORABLE_IF_TRACE_REMAINS_UNRESOLVED"
        ],
        "reason": "M0 means do not reveal a missing high-rate trace; the revision requires the trace for pulse evaluation."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "REACQUIRE",
        "additional_actions": [
          "RECONCILE_LOGGER"
        ],
        "reported_values": [
          {
            "name": "F03A_MEASUREMENT_VALID",
            "value": false,
            "unit": null
          },
          {
            "name": "F03A_FORMULATION_GROUP",
            "value": "P",
            "unit": null
          },
          {
            "name": "F03A_PULSE_PATTERN",
            "value": null,
            "unit": null
          },
          {
            "name": "measurement_quality",
            "value": "High-rate trace custody gap across handoff prevents determining pulse duration; calibration and 15-minute logger checks pass.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "The supplied 15-minute record meets the baseline mean criterion. It does not resolve the high-rate custody gap or establish a pulse-pattern classification.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "Stop the candidate pulse route pending restoration of trace custody and required measurement inputs; neither pulse absence nor degradation is established.",
        "rationale": "The high-rate custody failure makes the candidate measurement-quality input false, triggering [REDACTED]_INVALID_MEASUREMENT_STOP. Passing 15-minute checks cannot repair that gap."
      }
    },
    {
      "response_id": "d707e6a551c9ca590cfad7ed33fd99a3",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 B — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 250 NTU. Reproducible composition is 84% mineral grains and 3% organic flocs, matching the measured mineral-dominant pattern. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 349.5,
        "target_action": "REPORT_ESTIMATE",
        "target_method": "M0 mineral-dominant formula; preserve baseline scope"
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F02A_MEASUREMENT_VALID": true,
              "F02A_COMPOSITION_PATTERN": "Reproducible measured mineral-dominant pattern",
              "turbidity_NTU": 250,
              "mineral_grains_percent": 84,
              "organic_flocs_percent": 3,
              "blank_cell_duplicate_custody_checks": "pass"
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Zero selector matches: the mineral-dominant pattern is outside the organic-floc selector.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "Applicable: valid in-range measurement matching the original mineral-dominant matrix; REPORT_ESTIMATE.",
            "unit": null
          },
          {
            "name": "M0_estimated_TSS",
            "value": 349.5,
            "unit": "mg/L"
          },
          {
            "name": "original_matrix_calibration_uncertainty",
            "value": 12,
            "unit": "mg/L"
          },
          {
            "name": "source_method",
            "value": "CE-F02-M0-R0",
            "unit": null
          },
          {
            "name": "validated_turbidity_range",
            "value": [
              0,
              500
            ],
            "unit": "NTU"
          },
          {
            "name": "independent_gravimetric_result",
            "value": null,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "RECONCILE: record supplied inputs and zero-match reason; retain and apply the M0 pathway.",
        "scope": "Report 349.5 mg/L with the original mineral-matrix calibration band of ±12 mg/L. No case-specific gravimetric verification is available.",
        "rationale": "The organic-floc selector does not match. The preserved M0 pathway applies to the supplied mineral-dominant pattern and yields 1.35 × 250 + 12 = 349.5 mg/L."
      }
    },
    {
      "response_id": "0162f719db4d608eec7b4aa7fd51af98",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 C — successor-visible case facts\n\nPartially covered reflective surface with measured reflectance range 0.18–0.69 and bearing varying between scans; valid D readings are 2.2/1.4 °C. Calibration and sensor-quality checks pass.\n",
      "frozen_target_case": {
        "m0_action": "REPEAT_THERMAL_SCAN",
        "target_action": "REPEAT_THERMAL_SCAN",
        "reason": "The pair straddles the 2.0 degree trigger and bearing varies; the stable reflective-context rule does not apply. Reacquire under stable coverage/view."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "REPEAT_THERMAL_SCAN",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "paired_D",
            "value": [
              2.2,
              1.4
            ],
            "unit": "°C"
          },
          {
            "name": "absolute_pair_difference",
            "value": 0.8,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance_range",
            "value": [
              0.18,
              0.69
            ],
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Repeat thermal acquisition under M0; independent site review remains available and thermal readings alone do not authorize irrigation.",
        "rationale": "The supplied valid D readings straddle 2.0 °C, which requires a repeat scan after checking setup. The difference equals 0.8 °C and does not exceed the disagreement limit. M0 supplies no reflectance or bearing-variation threshold that changes this action."
      }
    },
    {
      "response_id": "45388d3a60a387a9890bf55317ab3464",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 B — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 250 NTU. Reproducible composition is 84% mineral grains and 3% organic flocs, matching the measured mineral-dominant pattern. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 349.5,
        "target_action": "REPORT_ESTIMATE",
        "target_method": "M0 mineral-dominant formula; preserve baseline scope"
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "estimated_TSS",
            "value": 349.5,
            "unit": "mg/L"
          },
          {
            "name": "original_calibration_matrix_uncertainty_band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "CE-F02-M0-R0; validated turbidity range 0–500 NTU and original mineral-dominant calibration matrix, with a recorded ±12 mg/L calibration uncertainty band.",
        "rationale": "Measurement checks pass and 250 NTU is in range. M0 calculates 1.35 × 250 + 12 = 349.5 mg/L. The supplied composition matches the mineral-dominant pattern. Without a gravimetric reference, sample-specific error cannot be established."
      }
    },
    {
      "response_id": "d50f4b37accdd3510e293c823fb2e28e",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 A — successor-visible case facts\n\nTwo independently registry-verified lots are available for one stability-review slot: one is formulation group P and one is group S. Both have complete calibrated 15-minute logger records and valid clock/custody checks; every segment and shipment mean is below 8.0 °C. Both have complete aligned high-rate traces. The group-P trace has a 9-minute excursion peaking at 13.7 °C; the group-S trace has a 10-minute excursion peaking at 14.0 °C. No assay or disposition result is provided. Select one lot for the available review slot.\n",
      "frozen_target_case": {
        "m0_actions": {
          "group_p": "SCREEN_PASS",
          "group_s": "SCREEN_PASS"
        },
        "target_action": {
          "group_p": "STABILITY_REVIEW",
          "group_s": "SCREEN_PASS"
        },
        "selected_for_single_review_slot": "group_p",
        "operational_policy": {
          "selector_inputs": [
            "independently registry-verified group P",
            "complete aligned high-rate trace",
            "pulse duration within 9–13 minutes",
            "pulse peak within 13.7–14.4 degrees C",
            "valid M0 means below 8.0 degrees C"
          ],
          "applicability_rule": "For a complete high-rate pulse within the observed group-P E1 context only, select group P for stability review even when M0's 15-minute means pass. The matched group-S pulsed control does not authorize a universal pulse rule.",
          "action_mapping": "Retain the M0 mean-only SCREEN_PASS as the baseline result and add STABILITY_REVIEW for the verified group-P lot. This is an independent review disposition, not a confirmed degradation or safety finding.",
          "preserved_rule_ids": [
            "M0_F03_LOGGER_CALIBRATION_CLOCK_CUSTODY",
            "M0_F03_MEAN_ONLY_SCREEN_PASS"
          ],
          "unresolved_or_fallback_rule": "If the required high-rate trace is incomplete or pulse duration cannot be determined, select RECONCILE_LOGGER; if unresolved, select UNSCORABLE. For a complete group-P trace without the observed pulse context, retain the M0 pass path.",
          "stop_conditions": [
            "No universal temperature or pulse-duration cutoff",
            "No automatic degradation claim",
            "No generalization from group P to group S or other formulations",
            "No replacement of M0 mean-only baseline"
          ],
          "scope_ceiling": "Verified group-P formulation, complete calibrated high-rate pulse context in the observed 9–13 minute / 13.7–14.4 degree C envelope, and stability-review triage only."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "STABILITY_REVIEW",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "selected_formulation_group",
            "value": "P",
            "unit": null
          },
          {
            "name": "selected_lot_excursion_duration",
            "value": 9,
            "unit": "min"
          },
          {
            "name": "selected_lot_peak_temperature",
            "value": 13.7,
            "unit": "°C"
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "Allocate the single review slot to group P; no degradation or release determination.",
        "rationale": "Both lots meet M0's mean criterion. [REDACTED] through [REDACTED] support prioritizing the group-P excursion for independent review, whereas [REDACTED] records retained activity above the assay reference for a similar group-S excursion. This supports review priority without establishing a universal pulse threshold or guaranteeing the group-S lot's stability."
      }
    },
    {
      "response_id": "7e113bd5591cb7b5630cf8a45b70bc57",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 A — successor-visible case facts\n\nCalibrated radiometric camera and matched shielded air sensor; same marked canopy; valid stable paired D readings 2.7/2.6 °C. Ground cover is reflective silver film with measured reflectance 0.72; the camera bearing is toward the sun at 21° off nadir. Required M0 calibration, time, mask, geometry, and sensor-quality fields are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action_sequence": [
          "REFLECTION_CONTROL_SCAN_OR_CONTACT_CHECK",
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "operational_policy": {
          "selector_inputs": [
            "reflective silver film at measured reflectance 0.72",
            "toward-sun view at 21 degrees off nadir",
            "same marked canopy and calibrated camera",
            "stable high D pair"
          ],
          "applicability_rule": "For this observed stable reflective-film/toward-sun/21-degree context only, do not treat stable high D as sufficient to rely on the ordinary M0 thermal-trigger path until the measurement-control discriminator is resolved.",
          "action_mapping": "Acquire two same-canopy scans with the view changed away from the sun to 8 degrees off nadir; take a contact-leaf reference immediately after each scan and record the paired comparisons. Then retain the M0 soil-moisture confirmation regardless of the comparison. Do not infer stress or irrigation.",
          "preserved_rule_ids": [
            "M0_F01_CALIBRATION_QC",
            "M0_F01_STABLE_HIGH_D_SOIL_MOISTURE_CONFIRMATION"
          ],
          "unresolved_or_fallback_rule": "If coverage, bearing, or the required control measurements are invalid or incomplete, reacquire under stable coverage/view and retain the M0 confirmation path; do not infer stress or irrigation.",
          "stop_conditions": [
            "No universal reflectance cutoff",
            "No universal view-angle cutoff",
            "No changed D threshold",
            "No stress or irrigation disposition from thermal evidence alone"
          ],
          "scope_ceiling": "The measured reflective-silver-film/toward-sun/21-degree case context and the E1-observed away-sun 8-degree comparison; no population or universal physical claim."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "paired_D",
            "value": [
              2.7,
              2.6
            ],
            "unit": "°C"
          },
          {
            "name": "absolute_pair_difference",
            "value": 0.1,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.72,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Thermal triage for independent root-zone VWC confirmation only; no stress determination or irrigation authorization.",
        "rationale": "Required inputs are valid, the pair difference is within 0.8 °C, and both D values are at least 2.0 °C. M0 therefore selects confirmation. Reflective silver film raises an unresolved concern about M0's ground-radiance premise, but M0 supplies no reflectance threshold or alternative surface-based action."
      }
    },
    {
      "response_id": "184fe890beaadaadb3da0a17b2665095",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 C — successor-visible case facts\n\nPartially covered reflective surface with measured reflectance range 0.18–0.69 and bearing varying between scans; valid D readings are 2.2/1.4 °C. Calibration and sensor-quality checks pass.\n",
      "frozen_target_case": {
        "m0_action": "REPEAT_THERMAL_SCAN",
        "target_action": "REPEAT_THERMAL_SCAN",
        "reason": "The pair straddles the 2.0 degree trigger and bearing varies; the stable reflective-context rule does not apply. Reacquire under stable coverage/view."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "REPEAT_THERMAL_SCAN",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "D_scan_1",
            "value": 2.2,
            "unit": "°C"
          },
          {
            "name": "D_scan_2",
            "value": 1.4,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance_range",
            "value": [
              0.18,
              0.69
            ],
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": "INPUT_INVALID if required setup or mask fields are absent or fail verification.",
        "scope": "Reacquire a comparable paired thermal measurement after checking setup, geometry, and canopy mask.",
        "rationale": "The supplied valid D readings straddle 2.0 °C, which independently requires a repeat under M0. Their difference is exactly 0.8 °C, not greater than the disagreement limit. Partial reflective coverage and varying bearing do not establish a stable measurement context or justify a new reflectance threshold."
      }
    },
    {
      "response_id": "09def73f971481ddc5a0375a5f74553e",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 C — successor-visible case facts\n\nPartially covered reflective surface with measured reflectance range 0.18–0.69 and bearing varying between scans; valid D readings are 2.2/1.4 °C. Calibration and sensor-quality checks pass.\n",
      "frozen_target_case": {
        "m0_action": "REPEAT_THERMAL_SCAN",
        "target_action": "REPEAT_THERMAL_SCAN",
        "reason": "The pair straddles the 2.0 degree trigger and bearing varies; the stable reflective-context rule does not apply. Reacquire under stable coverage/view."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "REPEAT_THERMAL_SCAN",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "paired_D",
            "value": [
              2.2,
              1.4
            ],
            "unit": "°C"
          },
          {
            "name": "absolute_pair_difference",
            "value": 0.8,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance_range",
            "value": [
              0.18,
              0.69
            ],
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Repeat thermal acquisition under M0; independent site review remains available regardless of thermal output.",
        "rationale": "The supplied valid D pair straddles 2.0 °C, which requires a repeat scan after checking setup. Its difference equals 0.8 °C and does not exceed the disagreement limit. M0 provides no separate routing threshold for reflectance variation or bearing variation."
      }
    },
    {
      "response_id": "5bddfdaead8c3f22f78e7f6ad63db6cc",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 C — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger means are below 8.0 °C. The high-rate trace has a custody gap across handoff, so pulse duration cannot be determined. Calibration and 15-minute logger checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action_sequence": [
          "RECONCILE_LOGGER",
          "UNSCORABLE_IF_TRACE_REMAINS_UNRESOLVED"
        ],
        "reason": "M0 means do not reveal a missing high-rate trace; the revision requires the trace for pulse evaluation."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "RECONCILE_LOGGER",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "formulation_group",
            "value": "P",
            "unit": null
          },
          {
            "name": "pulse_duration",
            "value": null,
            "unit": "min"
          },
          {
            "name": "high_rate_trace_custody_gap",
            "value": true,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "UNSCORABLE if the required high-rate custody and exposure record cannot be recovered.",
        "scope": "Reconcile the high-rate trace custody gap before resolving the group-P exposure assessment.",
        "rationale": "The complete 15-minute means meet M0's pass criterion, but cannot resolve short excursions during the custody gap. [REDACTED] demonstrates that an incomplete high-rate trace leaves pulse occurrence unresolved. Recover the missing provenance and exposure record rather than infer either absence of a pulse or degradation."
      }
    },
    {
      "response_id": "d8f5bcba5fd9f5d0f7673f4327074fac",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 B — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger and aligned high-rate trace; all shipment and segment means are below 8.0 °C; no above-12 °C pulse is present; calibration, clock, and custody checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action": "SCREEN_PASS",
        "reason": "No above-12 degree C pulse is present; preserve M0."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "formulation_group",
            "value": "P",
            "unit": null
          },
          {
            "name": "above_12_C_pulse_present",
            "value": false,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "M0 temperature-screen triage only; no unconditional product-safety guarantee.",
        "rationale": "All required M0 checks pass and all means are below 8.0 °C. The complete high-rate trace provides no observed above-12 °C pulse. [REDACTED] supports retaining mean-based screening for the observed continuous-profile group-P scope; formulation identity alone does not justify review."
      }
    },
    {
      "response_id": "4841a7f71282475e8b801fbc88c1c513",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 A — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 150 NTU. Reproducible composition is 21% mineral grains and 46% organic flocs; the remainder is mixed fines. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 214.5,
        "m0_uncertainty_mg_l": 12,
        "target_action": "REPORT_ESTIMATE",
        "target_value_mg_l": 131,
        "operational_policy": {
          "selector_inputs": [
            "QC-passing composition matching the observed floc-rich pattern",
            "blank-corrected turbidity from 100 through 300 NTU"
          ],
          "applicability_rule": "Use only for reproducible QC-passing composition matching one of the observed E1 floc-rich tuples: (21% mineral, 46% organic flocs), (18%, 49%), or (24%, 42%), and turbidity within the observed 100–300 NTU span. Do not treat the independent minimum/maximum values as permission for unobserved composition pairs.",
          "action_mapping": "Use the E1 floc-rich empirical relation at 100/200/300 NTU (91/171/251 mg/L) and linearly interpolate only within that turbidity span. At 150 NTU the estimate is 131 mg/L. E1 provides no uncertainty band for this estimate; do not transfer M0's ±12 mg/L band.",
          "preserved_rule_ids": [
            "M0_F02_QC_AND_DUPLICATE_CHECKS",
            "M0_F02_MINERAL_DOMINANT_REPORT_ESTIMATE"
          ],
          "unresolved_or_fallback_rule": "Outside an exact observed floc-rich composition tuple, outside 100–300 NTU, or when composition/QC is unresolved, request or reconcile composition and/or obtain gravimetry; do not apply the floc-rich point relation.",
          "stop_conditions": [
            "No universal mineral/floc cutoff",
            "No composition-pair interpolation beyond the observed tuples",
            "No turbidity extrapolation beyond 100–300 NTU",
            "No ±12 mg/L uncertainty claim for the E1 estimate"
          ],
          "scope_ceiling": "Exact observed floc-rich composition tuples and 100–300 NTU; no universal formula or inference beyond the synthetic E1 evidence."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "Withhold a supported concentration estimate",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "Turbidity",
            "value": 150,
            "unit": "NTU"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "Independent constant-weight gravimetry would be needed to establish concentration.",
        "scope": "Reproducible floc-rich composition; valid in-range turbidity.",
        "rationale": "Composition matches [REDACTED]. [REDACTED] through [REDACTED] show substantial M0 calibration error despite stable measurements. No validated replacement mapping or uncertainty band is supplied. Measurement validity alone does not support applying M0 to this composition."
      }
    },
    {
      "response_id": "60226d7822dad84894917a73610be61c",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 B — successor-visible case facts\n\nCalibrated setup; ordinary mineral-soil surface with reflectance 0.15; toward-sun bearing at 21° off nadir; valid stable paired D readings 2.5/2.4 °C. Required M0 inputs are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action": "SOIL_MOISTURE_CONFIRMATION",
        "reason": "The reflective-film selector is absent; preserve the M0 path."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "D_scan_1",
            "value": 2.5,
            "unit": "°C"
          },
          {
            "name": "D_scan_2",
            "value": 2.4,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.15,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "M0 triage on ordinary mineral soil; irrigation remains subject to independent site evidence.",
        "rationale": "Both valid, stable D readings exceed 2.0 °C. M0 selects a fixed root-zone VWC measurement. [REDACTED] supports retaining this ordinary-surface pathway, but its VWC and plant-water observations cannot be transferred to this case."
      }
    },
    {
      "response_id": "d275b181f68cc808cdbeb0076fb01a30",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 A — successor-visible case facts\n\nTwo independently registry-verified lots are available for one stability-review slot: one is formulation group P and one is group S. Both have complete calibrated 15-minute logger records and valid clock/custody checks; every segment and shipment mean is below 8.0 °C. Both have complete aligned high-rate traces. The group-P trace has a 9-minute excursion peaking at 13.7 °C; the group-S trace has a 10-minute excursion peaking at 14.0 °C. No assay or disposition result is provided. Select one lot for the available review slot.\n",
      "frozen_target_case": {
        "m0_actions": {
          "group_p": "SCREEN_PASS",
          "group_s": "SCREEN_PASS"
        },
        "target_action": {
          "group_p": "STABILITY_REVIEW",
          "group_s": "SCREEN_PASS"
        },
        "selected_for_single_review_slot": "group_p",
        "operational_policy": {
          "selector_inputs": [
            "independently registry-verified group P",
            "complete aligned high-rate trace",
            "pulse duration within 9–13 minutes",
            "pulse peak within 13.7–14.4 degrees C",
            "valid M0 means below 8.0 degrees C"
          ],
          "applicability_rule": "For a complete high-rate pulse within the observed group-P E1 context only, select group P for stability review even when M0's 15-minute means pass. The matched group-S pulsed control does not authorize a universal pulse rule.",
          "action_mapping": "Retain the M0 mean-only SCREEN_PASS as the baseline result and add STABILITY_REVIEW for the verified group-P lot. This is an independent review disposition, not a confirmed degradation or safety finding.",
          "preserved_rule_ids": [
            "M0_F03_LOGGER_CALIBRATION_CLOCK_CUSTODY",
            "M0_F03_MEAN_ONLY_SCREEN_PASS"
          ],
          "unresolved_or_fallback_rule": "If the required high-rate trace is incomplete or pulse duration cannot be determined, select RECONCILE_LOGGER; if unresolved, select UNSCORABLE. For a complete group-P trace without the observed pulse context, retain the M0 pass path.",
          "stop_conditions": [
            "No universal temperature or pulse-duration cutoff",
            "No automatic degradation claim",
            "No generalization from group P to group S or other formulations",
            "No replacement of M0 mean-only baseline"
          ],
          "scope_ceiling": "Verified group-P formulation, complete calibrated high-rate pulse context in the observed 9–13 minute / 13.7–14.4 degree C envelope, and stability-review triage only."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "F03A_PRODUCT_STABILITY_REVIEW",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "selected_formulation_group",
            "value": "P",
            "unit": null
          },
          {
            "name": "F03A_MEASUREMENT_VALID",
            "value": true,
            "unit": null
          },
          {
            "name": "F03A_FORMULATION_GROUP",
            "value": "P",
            "unit": null
          },
          {
            "name": "F03A_PULSE_PATTERN",
            "value": "observed_group_p_pulse_cases",
            "unit": null
          },
          {
            "name": "F03A_TRACE_AND_ASSAY",
            "value": {
              "formulation_identity": "Independently verified group P",
              "high_rate_trace": "Complete and aligned; 9-minute excursion peaking at 13.7 °C, matching the supplied [REDACTED] pattern",
              "15_minute_record": "Complete and calibrated; clock and custody valid; all segment and shipment means below 8.0 °C",
              "duplicate_activity_assay": "Not supplied"
            },
            "unit": null
          },
          {
            "name": "alternative_lot",
            "value": {
              "formulation_group": "S",
              "pulse_duration_minutes": 10,
              "peak_temperature_celsius": 14.0,
              "selector_match": false
            },
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "Both lots meet SCREEN_PASS under the baseline mean criterion.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "Allocate the review slot to group P for product-specific stability review; no degradation finding or universal pulse threshold.",
        "rationale": "The valid group-P trace matches the supplied observed pulse pattern and satisfies F03A_OBSERVED_GROUP_P_PULSE_PATTERN, whose action reference is F03A_PRODUCT_STABILITY_REVIEW. Group S does not satisfy the formulation condition."
      }
    },
    {
      "response_id": "ac0b8326006b50904975a173d22dbabc",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 B — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger and aligned high-rate trace; all shipment and segment means are below 8.0 °C; no above-12 °C pulse is present; calibration, clock, and custody checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action": "SCREEN_PASS",
        "reason": "No above-12 degree C pulse is present; preserve M0."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "SCREEN_PASS"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F03B_MEASUREMENT_VALID": true,
              "F03B_HIGH_RATE_TRACE_COMPLETE": true,
              "F03B_ASSAY_REPLICATES_RECONCILE": null,
              "formulation_group": "P",
              "all_means_below_8_C": true,
              "above_12_C_pulse_present": false
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Complete high-rate trace excludes the selector pattern; assay reconciliation input is unavailable.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "SCREEN_PASS: required baseline checks pass and all means are below 8.0 C.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "Record the unmatched inputs and preserve the M0 SCREEN_PASS pathway.",
        "scope": "Baseline temperature screening only; no unconditional product-safety guarantee.",
        "rationale": "The selector does not match. The baseline independently permits SCREEN_PASS; absence of an above-12 C pulse is not used as a new safety threshold."
      }
    },
    {
      "response_id": "4731de10ad04e2167ee08b6be0d1f758",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 C — successor-visible case facts\n\nBlank, cell, and turbidity duplicate checks pass at 155 NTU. Composition aliquots are not reproducible and do not stably match either the measured mineral-dominant or floc-rich patterns. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 221.25,
        "target_action": "RECONCILE_COMPOSITION_OR_OBTAIN_GRAVIMETRY",
        "reason": "Composition aliquots do not reproducibly match an observed E1 composition tuple; no floc-rich point estimate is licensed."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "RECONCILE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F02B_MEASUREMENT_VALID": true,
              "F02B_COMPOSITION_REPRODUCIBLE": false,
              "F02B_GRAVIMETRIC_REPLICATES_AGREE": null,
              "turbidity_NTU": 155,
              "composition": "Aliquots are not reproducible and do not stably match either supplied composition pattern.",
              "gravimetric_reference": null
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Gravimetric replicate agreement is missing; the selector requires an explicit false value, which cannot be inferred.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "Preserved. The in-range baseline calculation is 221.25 mg/L, but no reproducible composition basis establishes its applicability or the original uncertainty band.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "Record supplied values and request independent review of unresolved composition and gravimetric evidence.",
        "scope": "No licensed selector action or validated composition-specific point estimate is established.",
        "rationale": "Non-reproducible composition alone does not satisfy F02B_UNREPRODUCIBLE_COMPOSITION_AND_MASS. Passing turbidity checks neither supplies missing gravimetric evidence nor establishes mass agreement."
      }
    },
    {
      "response_id": "d6ac97c5f39ba14c31bf58102d036feb",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 B — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 250 NTU. Reproducible composition is 84% mineral grains and 3% organic flocs, matching the measured mineral-dominant pattern. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 349.5,
        "target_action": "REPORT_ESTIMATE",
        "target_method": "M0 mineral-dominant formula; preserve baseline scope"
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "estimated_TSS",
            "value": 349.5,
            "unit": "mg/L"
          },
          {
            "name": "original_calibration_matrix_uncertainty_band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "CE-F02-M0-R0; validated turbidity range 0–500 NTU and original mineral-dominant calibration matrix, with a recorded uncertainty band of ±12 mg/L.",
        "rationale": "Measurement checks pass and 250 NTU is in range, so M0 reports 1.35 × 250 + 12 = 349.5 mg/L. The supplied composition matches the mineral-dominant pattern. Without a gravimetric reference, the individual estimate's error remains unverified."
      }
    },
    {
      "response_id": "547987a6028360e90d56a44a42833f13",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 B — successor-visible case facts\n\nCalibrated setup; ordinary mineral-soil surface with reflectance 0.15; toward-sun bearing at 21° off nadir; valid stable paired D readings 2.5/2.4 °C. Required M0 inputs are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action": "SOIL_MOISTURE_CONFIRMATION",
        "reason": "The reflective-film selector is absent; preserve the M0 path."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "paired_D",
            "value": [
              2.5,
              2.4
            ],
            "unit": "°C"
          },
          {
            "name": "absolute_pair_difference",
            "value": 0.1,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.15,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Thermal triage for independent root-zone VWC confirmation only; no stress determination or irrigation authorization.",
        "rationale": "Required inputs are valid, the pair difference is within 0.8 °C, and both D values are at least 2.0 °C. Ordinary mineral soil is represented in M0's calibration basis. Measure VWC at the fixed root-zone probe."
      }
    },
    {
      "response_id": "fb8087c5a4c955e22bb192b0ce54c42a",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 A — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 150 NTU. Reproducible composition is 21% mineral grains and 46% organic flocs; the remainder is mixed fines. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 214.5,
        "m0_uncertainty_mg_l": 12,
        "target_action": "REPORT_ESTIMATE",
        "target_value_mg_l": 131,
        "operational_policy": {
          "selector_inputs": [
            "QC-passing composition matching the observed floc-rich pattern",
            "blank-corrected turbidity from 100 through 300 NTU"
          ],
          "applicability_rule": "Use only for reproducible QC-passing composition matching one of the observed E1 floc-rich tuples: (21% mineral, 46% organic flocs), (18%, 49%), or (24%, 42%), and turbidity within the observed 100–300 NTU span. Do not treat the independent minimum/maximum values as permission for unobserved composition pairs.",
          "action_mapping": "Use the E1 floc-rich empirical relation at 100/200/300 NTU (91/171/251 mg/L) and linearly interpolate only within that turbidity span. At 150 NTU the estimate is 131 mg/L. E1 provides no uncertainty band for this estimate; do not transfer M0's ±12 mg/L band.",
          "preserved_rule_ids": [
            "M0_F02_QC_AND_DUPLICATE_CHECKS",
            "M0_F02_MINERAL_DOMINANT_REPORT_ESTIMATE"
          ],
          "unresolved_or_fallback_rule": "Outside an exact observed floc-rich composition tuple, outside 100–300 NTU, or when composition/QC is unresolved, request or reconcile composition and/or obtain gravimetry; do not apply the floc-rich point relation.",
          "stop_conditions": [
            "No universal mineral/floc cutoff",
            "No composition-pair interpolation beyond the observed tuples",
            "No turbidity extrapolation beyond 100–300 NTU",
            "No ±12 mg/L uncertainty claim for the E1 estimate"
          ],
          "scope_ceiling": "Exact observed floc-rich composition tuples and 100–300 NTU; no universal formula or inference beyond the synthetic E1 evidence."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "estimated_TSS",
            "value": 214.5,
            "unit": "mg/L"
          },
          {
            "name": "original_calibration_matrix_uncertainty_band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "CE-F02-M0-R0; validated turbidity range 0–500 NTU. The ±12 mg/L band applies to the original mineral-dominant calibration matrix; its applicability to this composition is unvalidated.",
        "rationale": "Measurement checks pass and 150 NTU is in range, so M0 reports 1.35 × 150 + 12 = 214.5 mg/L. Composition is not an M0 routing input. Without a gravimetric reference, this estimate's error cannot be determined."
      }
    },
    {
      "response_id": "2f099c2ced27269747479274181d4899",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 B — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger and aligned high-rate trace; all shipment and segment means are below 8.0 °C; no above-12 °C pulse is present; calibration, clock, and custody checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action": "SCREEN_PASS",
        "reason": "No above-12 degree C pulse is present; preserve M0."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "M0 temperature triage, not an unconditional product-safety guarantee.",
        "rationale": "Required logger records and provenance checks pass, and every segment and shipment mean is below 8.0 °C. The absence of an above-12 °C pulse is not an M0 selection criterion."
      }
    },
    {
      "response_id": "49ac78902b3e4e36a367eb97b9676bb0",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 A — successor-visible case facts\n\nCalibrated radiometric camera and matched shielded air sensor; same marked canopy; valid stable paired D readings 2.7/2.6 °C. Ground cover is reflective silver film with measured reflectance 0.72; the camera bearing is toward the sun at 21° off nadir. Required M0 calibration, time, mask, geometry, and sensor-quality fields are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action_sequence": [
          "REFLECTION_CONTROL_SCAN_OR_CONTACT_CHECK",
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "operational_policy": {
          "selector_inputs": [
            "reflective silver film at measured reflectance 0.72",
            "toward-sun view at 21 degrees off nadir",
            "same marked canopy and calibrated camera",
            "stable high D pair"
          ],
          "applicability_rule": "For this observed stable reflective-film/toward-sun/21-degree context only, do not treat stable high D as sufficient to rely on the ordinary M0 thermal-trigger path until the measurement-control discriminator is resolved.",
          "action_mapping": "Acquire two same-canopy scans with the view changed away from the sun to 8 degrees off nadir; take a contact-leaf reference immediately after each scan and record the paired comparisons. Then retain the M0 soil-moisture confirmation regardless of the comparison. Do not infer stress or irrigation.",
          "preserved_rule_ids": [
            "M0_F01_CALIBRATION_QC",
            "M0_F01_STABLE_HIGH_D_SOIL_MOISTURE_CONFIRMATION"
          ],
          "unresolved_or_fallback_rule": "If coverage, bearing, or the required control measurements are invalid or incomplete, reacquire under stable coverage/view and retain the M0 confirmation path; do not infer stress or irrigation.",
          "stop_conditions": [
            "No universal reflectance cutoff",
            "No universal view-angle cutoff",
            "No changed D threshold",
            "No stress or irrigation disposition from thermal evidence alone"
          ],
          "scope_ceiling": "The measured reflective-silver-film/toward-sun/21-degree case context and the E1-observed away-sun 8-degree comparison; no population or universal physical claim."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "SOIL_MOISTURE_CONFIRMATION",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "paired_D",
            "value": [
              2.7,
              2.6
            ],
            "unit": "°C"
          },
          {
            "name": "absolute_pair_difference",
            "value": 0.1,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance",
            "value": 0.72,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": null,
        "scope": "Thermal triage for independent root-zone VWC confirmation only; no irrigation authorization or established plant stress.",
        "rationale": "Required inputs are valid, the pair differs by less than 0.8 °C, and both D values are at least 2.0 °C. M0 therefore selects confirmation. Its procedure has no reflectance-based exception; reflective silver film is outside the listed calibration surfaces, so this routing does not establish validity on that surface."
      }
    },
    {
      "response_id": "45603ae3954ea181d60aabc083bbb387",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 A — successor-visible case facts\n\nTwo independently registry-verified lots are available for one stability-review slot: one is formulation group P and one is group S. Both have complete calibrated 15-minute logger records and valid clock/custody checks; every segment and shipment mean is below 8.0 °C. Both have complete aligned high-rate traces. The group-P trace has a 9-minute excursion peaking at 13.7 °C; the group-S trace has a 10-minute excursion peaking at 14.0 °C. No assay or disposition result is provided. Select one lot for the available review slot.\n",
      "frozen_target_case": {
        "m0_actions": {
          "group_p": "SCREEN_PASS",
          "group_s": "SCREEN_PASS"
        },
        "target_action": {
          "group_p": "STABILITY_REVIEW",
          "group_s": "SCREEN_PASS"
        },
        "selected_for_single_review_slot": "group_p",
        "operational_policy": {
          "selector_inputs": [
            "independently registry-verified group P",
            "complete aligned high-rate trace",
            "pulse duration within 9–13 minutes",
            "pulse peak within 13.7–14.4 degrees C",
            "valid M0 means below 8.0 degrees C"
          ],
          "applicability_rule": "For a complete high-rate pulse within the observed group-P E1 context only, select group P for stability review even when M0's 15-minute means pass. The matched group-S pulsed control does not authorize a universal pulse rule.",
          "action_mapping": "Retain the M0 mean-only SCREEN_PASS as the baseline result and add STABILITY_REVIEW for the verified group-P lot. This is an independent review disposition, not a confirmed degradation or safety finding.",
          "preserved_rule_ids": [
            "M0_F03_LOGGER_CALIBRATION_CLOCK_CUSTODY",
            "M0_F03_MEAN_ONLY_SCREEN_PASS"
          ],
          "unresolved_or_fallback_rule": "If the required high-rate trace is incomplete or pulse duration cannot be determined, select RECONCILE_LOGGER; if unresolved, select UNSCORABLE. For a complete group-P trace without the observed pulse context, retain the M0 pass path.",
          "stop_conditions": [
            "No universal temperature or pulse-duration cutoff",
            "No automatic degradation claim",
            "No generalization from group P to group S or other formulations",
            "No replacement of M0 mean-only baseline"
          ],
          "scope_ceiling": "Verified group-P formulation, complete calibrated high-rate pulse context in the observed 9–13 minute / 13.7–14.4 degree C envelope, and stability-review triage only."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "P_excursion_duration",
            "value": 9,
            "unit": "minutes"
          },
          {
            "name": "P_peak_temperature",
            "value": 13.7,
            "unit": "°C"
          },
          {
            "name": "S_excursion_duration",
            "value": 10,
            "unit": "minutes"
          },
          {
            "name": "S_peak_temperature",
            "value": 14.0,
            "unit": "°C"
          },
          {
            "name": "selected_review_lot",
            "value": null,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "M0 supplies no criterion for allocating the single review slot between these lots.",
        "scope": "Both lots pass the M0 interval-mean screen; review-slot allocation is undetermined.",
        "rationale": "Both lots satisfy the required logger checks and mean criterion. M0 contains no formulation-specific priority, peak-temperature threshold, pulse-duration rule, or tie-breaker. Selecting either lot for preferential review would require an unsupported rule. Neither pass establishes stability under the observed excursions."
      }
    },
    {
      "response_id": "17e2ad30821a9745ba312520408b6f55",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 A — successor-visible case facts\n\nBlank, cell, duplicate, and custody checks pass. Turbidity is 150 NTU. Reproducible composition is 21% mineral grains and 46% organic flocs; the remainder is mixed fines. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 214.5,
        "m0_uncertainty_mg_l": 12,
        "target_action": "REPORT_ESTIMATE",
        "target_value_mg_l": 131,
        "operational_policy": {
          "selector_inputs": [
            "QC-passing composition matching the observed floc-rich pattern",
            "blank-corrected turbidity from 100 through 300 NTU"
          ],
          "applicability_rule": "Use only for reproducible QC-passing composition matching one of the observed E1 floc-rich tuples: (21% mineral, 46% organic flocs), (18%, 49%), or (24%, 42%), and turbidity within the observed 100–300 NTU span. Do not treat the independent minimum/maximum values as permission for unobserved composition pairs.",
          "action_mapping": "Use the E1 floc-rich empirical relation at 100/200/300 NTU (91/171/251 mg/L) and linearly interpolate only within that turbidity span. At 150 NTU the estimate is 131 mg/L. E1 provides no uncertainty band for this estimate; do not transfer M0's ±12 mg/L band.",
          "preserved_rule_ids": [
            "M0_F02_QC_AND_DUPLICATE_CHECKS",
            "M0_F02_MINERAL_DOMINANT_REPORT_ESTIMATE"
          ],
          "unresolved_or_fallback_rule": "Outside an exact observed floc-rich composition tuple, outside 100–300 NTU, or when composition/QC is unresolved, request or reconcile composition and/or obtain gravimetry; do not apply the floc-rich point relation.",
          "stop_conditions": [
            "No universal mineral/floc cutoff",
            "No composition-pair interpolation beyond the observed tuples",
            "No turbidity extrapolation beyond 100–300 NTU",
            "No ±12 mg/L uncertainty claim for the E1 estimate"
          ],
          "scope_ceiling": "Exact observed floc-rich composition tuples and 100–300 NTU; no universal formula or inference beyond the synthetic E1 evidence."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "REPORT_ESTIMATE",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "estimated_TSS",
            "value": 214.5,
            "unit": "mg/L"
          },
          {
            "name": "original_calibration_matrix_uncertainty_band",
            "value": 12,
            "unit": "mg/L"
          }
        ],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": null,
        "scope": "CE-F02-M0-R0; validated turbidity range 0–500 NTU. The ±12 mg/L band applies to the original mineral-dominant calibration matrix; its applicability to this composition is unvalidated.",
        "rationale": "Measurement checks pass and 150 NTU is in range. M0 calculates 1.35 × 150 + 12 = 214.5 mg/L. Composition is not an M0 input and supplies no alternate action. Without a gravimetric reference, sample-specific error cannot be established."
      }
    },
    {
      "response_id": "918159b9ca9deeeceb4cd1fc6f498364",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 A — successor-visible case facts\n\nTwo independently registry-verified lots are available for one stability-review slot: one is formulation group P and one is group S. Both have complete calibrated 15-minute logger records and valid clock/custody checks; every segment and shipment mean is below 8.0 °C. Both have complete aligned high-rate traces. The group-P trace has a 9-minute excursion peaking at 13.7 °C; the group-S trace has a 10-minute excursion peaking at 14.0 °C. No assay or disposition result is provided. Select one lot for the available review slot.\n",
      "frozen_target_case": {
        "m0_actions": {
          "group_p": "SCREEN_PASS",
          "group_s": "SCREEN_PASS"
        },
        "target_action": {
          "group_p": "STABILITY_REVIEW",
          "group_s": "SCREEN_PASS"
        },
        "selected_for_single_review_slot": "group_p",
        "operational_policy": {
          "selector_inputs": [
            "independently registry-verified group P",
            "complete aligned high-rate trace",
            "pulse duration within 9–13 minutes",
            "pulse peak within 13.7–14.4 degrees C",
            "valid M0 means below 8.0 degrees C"
          ],
          "applicability_rule": "For a complete high-rate pulse within the observed group-P E1 context only, select group P for stability review even when M0's 15-minute means pass. The matched group-S pulsed control does not authorize a universal pulse rule.",
          "action_mapping": "Retain the M0 mean-only SCREEN_PASS as the baseline result and add STABILITY_REVIEW for the verified group-P lot. This is an independent review disposition, not a confirmed degradation or safety finding.",
          "preserved_rule_ids": [
            "M0_F03_LOGGER_CALIBRATION_CLOCK_CUSTODY",
            "M0_F03_MEAN_ONLY_SCREEN_PASS"
          ],
          "unresolved_or_fallback_rule": "If the required high-rate trace is incomplete or pulse duration cannot be determined, select RECONCILE_LOGGER; if unresolved, select UNSCORABLE. For a complete group-P trace without the observed pulse context, retain the M0 pass path.",
          "stop_conditions": [
            "No universal temperature or pulse-duration cutoff",
            "No automatic degradation claim",
            "No generalization from group P to group S or other formulations",
            "No replacement of M0 mean-only baseline"
          ],
          "scope_ceiling": "Verified group-P formulation, complete calibrated high-rate pulse context in the observed 9–13 minute / 13.7–14.4 degree C envelope, and stability-review triage only."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "group_P_screen",
            "value": "SCREEN_PASS",
            "unit": null
          },
          {
            "name": "group_S_screen",
            "value": "SCREEN_PASS",
            "unit": null
          },
          {
            "name": "selected_review_lot",
            "value": null,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "The supplied method provides no basis to select one lot for the review slot.",
        "scope": "M0 interval-mean screening of both lots; review priority is undetermined.",
        "rationale": "Both lots satisfy M0's required checks and mean criterion. M0 contains no formulation-specific ranking, peak-temperature rule, pulse-duration rule, or tie-breaker. Selecting one preferentially would require an unsupported rule."
      }
    },
    {
      "response_id": "d94379c9c0ad79c4c04809f485f674aa",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY02 C — successor-visible case facts\n\nBlank, cell, and turbidity duplicate checks pass at 155 NTU. Composition aliquots are not reproducible and do not stably match either the measured mineral-dominant or floc-rich patterns. No gravimetric reference is provided.\n",
      "frozen_target_case": {
        "m0_action": "REPORT_ESTIMATE",
        "m0_value_mg_l": 221.25,
        "target_action": "RECONCILE_COMPOSITION_OR_OBTAIN_GRAVIMETRY",
        "reason": "Composition aliquots do not reproducibly match an observed E1 composition tuple; no floc-rich point estimate is licensed."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "Withhold a TSS point estimate.",
        "additional_actions": [
          "Obtain independent constant-weight gravimetry across representative aliquots."
        ],
        "reported_values": [],
        "preserved_baseline_action_ids": [
          "REPORT_ESTIMATE",
          "REPEAT_SAMPLE",
          "FLAG_OUT_OF_RANGE",
          "INVALID_MEASUREMENT"
        ],
        "fallback": "Report aliquot-specific gravimetric results and their spread; reassess composition reproducibility before selecting a calibration.",
        "scope": "Composition-variable sample without a supported reproducible turbidity-to-mass mapping.",
        "rationale": "Stable turbidity does not resolve aliquot-dependent composition. [REDACTED] demonstrates differing gravimetric outcomes despite stable turbidity. Neither observed composition pattern can be selected, and no mixture threshold is supplied. Passing instrument checks does not justify INVALID_MEASUREMENT, while an in-range reading does not justify FLAG_OUT_OF_RANGE."
      }
    },
    {
      "response_id": "71a32465bdf48ba211a105beb0577832",
      "case_id": "A",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 A — successor-visible case facts\n\nCalibrated radiometric camera and matched shielded air sensor; same marked canopy; valid stable paired D readings 2.7/2.6 °C. Ground cover is reflective silver film with measured reflectance 0.72; the camera bearing is toward the sun at 21° off nadir. Required M0 calibration, time, mask, geometry, and sensor-quality fields are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action_sequence": [
          "REFLECTION_CONTROL_SCAN_OR_CONTACT_CHECK",
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "operational_policy": {
          "selector_inputs": [
            "reflective silver film at measured reflectance 0.72",
            "toward-sun view at 21 degrees off nadir",
            "same marked canopy and calibrated camera",
            "stable high D pair"
          ],
          "applicability_rule": "For this observed stable reflective-film/toward-sun/21-degree context only, do not treat stable high D as sufficient to rely on the ordinary M0 thermal-trigger path until the measurement-control discriminator is resolved.",
          "action_mapping": "Acquire two same-canopy scans with the view changed away from the sun to 8 degrees off nadir; take a contact-leaf reference immediately after each scan and record the paired comparisons. Then retain the M0 soil-moisture confirmation regardless of the comparison. Do not infer stress or irrigation.",
          "preserved_rule_ids": [
            "M0_F01_CALIBRATION_QC",
            "M0_F01_STABLE_HIGH_D_SOIL_MOISTURE_CONFIRMATION"
          ],
          "unresolved_or_fallback_rule": "If coverage, bearing, or the required control measurements are invalid or incomplete, reacquire under stable coverage/view and retain the M0 confirmation path; do not infer stress or irrigation.",
          "stop_conditions": [
            "No universal reflectance cutoff",
            "No universal view-angle cutoff",
            "No changed D threshold",
            "No stress or irrigation disposition from thermal evidence alone"
          ],
          "scope_ceiling": "The measured reflective-silver-film/toward-sun/21-degree case context and the E1-observed away-sun 8-degree comparison; no population or universal physical claim."
        }
      },
      "sanitized_response": {
        "case_id": "A",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F01B_MEASUREMENT_VALID": true,
              "F01B_SURFACE_COVERAGE_COMPLETE": null,
              "F01B_PAIRED_READING_PATTERN": "stable",
              "surface": "reflective silver film",
              "reflectance": 0.72,
              "bearing": "toward sun",
              "off_nadir_degrees": 21,
              "paired_D_C": [
                2.7,
                2.6
              ]
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Surface-coverage completeness is not explicitly supplied; stable readings do not match the variable_observed selector condition.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "SOIL_MOISTURE_CONFIRMATION: valid paired readings differ by 0.1 °C and both meet the 2.0 °C threshold.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": "Record supplied values and unmatched routing; retain M0 soil-moisture confirmation and request independent review when needed.",
        "scope": "No reflective-surface cutoff or thermal correction is supplied. Thermal evidence does not authorize irrigation.",
        "rationale": "The bounded selector does not match. The preserved M0 pathway prioritizes an independent VWC measurement."
      }
    },
    {
      "response_id": "6e69a1be475d1b83f13aed29159ebbfe",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 C — successor-visible case facts\n\nPartially covered reflective surface with measured reflectance range 0.18–0.69 and bearing varying between scans; valid D readings are 2.2/1.4 °C. Calibration and sensor-quality checks pass.\n",
      "frozen_target_case": {
        "m0_action": "REPEAT_THERMAL_SCAN",
        "target_action": "REPEAT_THERMAL_SCAN",
        "reason": "The pair straddles the 2.0 degree trigger and bearing varies; the stable reflective-context rule does not apply. Reacquire under stable coverage/view."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "REPEAT_THERMAL_SCAN",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "D_scan_1",
            "value": 2.2,
            "unit": "°C"
          },
          {
            "name": "D_scan_2",
            "value": 1.4,
            "unit": "°C"
          },
          {
            "name": "paired_D_difference",
            "value": 0.8,
            "unit": "°C"
          },
          {
            "name": "surface_reflectance_range",
            "value": [
              0.18,
              0.69
            ],
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": "INPUT_INVALID if required setup or mask checks fail or required fields are absent.",
        "scope": "Unresolved paired thermal signal with varying bearing and partial reflective coverage.",
        "rationale": "The readings straddle 2.0 °C, requiring a repeat under M0. Their difference equals, rather than exceeds, 0.8 °C. Verify required setup fields and repeat with consistent geometry and a checked mask. The mixed surface context does not support a reflectance cutoff, corrected threshold, or dry-soil conclusion."
      }
    },
    {
      "response_id": "31dfdf63e6a2aac464a57fd89e23b47f",
      "case_id": "B",
      "response_schema_valid": true,
      "case_facts": "# FAMILY01 B — successor-visible case facts\n\nCalibrated setup; ordinary mineral-soil surface with reflectance 0.15; toward-sun bearing at 21° off nadir; valid stable paired D readings 2.5/2.4 °C. Required M0 inputs are valid.\n",
      "frozen_target_case": {
        "m0_action": "SOIL_MOISTURE_CONFIRMATION",
        "target_action": "SOIL_MOISTURE_CONFIRMATION",
        "reason": "The reflective-film selector is absent; preserve the M0 path."
      },
      "sanitized_response": {
        "case_id": "B",
        "primary_action": "RECONCILE",
        "additional_actions": [
          "SOIL_MOISTURE_CONFIRMATION"
        ],
        "reported_values": [
          {
            "name": "supplied_inputs",
            "value": {
              "F01A_MEASUREMENT_VALID": true,
              "F01A_SURFACE_PATTERN": "ordinary mineral soil",
              "F01A_BEARING_RELATION": "toward_sun_observed",
              "reflectance": 0.15,
              "off_nadir_degrees": 21,
              "paired_D_C": [
                2.5,
                2.4
              ]
            },
            "unit": null
          },
          {
            "name": "fallback_reason",
            "value": "Zero selector matches: ordinary mineral soil does not match the specified reflective silver-film pattern.",
            "unit": null
          },
          {
            "name": "M0_pathway_status",
            "value": "SOIL_MOISTURE_CONFIRMATION: valid stable pair, both D values at least 2.0 °C.",
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "ROUTINE_MONITORING",
          "SOIL_MOISTURE_CONFIRMATION",
          "REPEAT_THERMAL_SCAN",
          "INPUT_INVALID"
        ],
        "fallback": "RECONCILE; preserve and execute the M0 soil-moisture confirmation pathway.",
        "scope": "Outside the selector's licensed surface pattern; the unchanged M0 threshold applies. Thermal evidence alone does not authorize irrigation.",
        "rationale": "The surface input excludes the selector. The preserved M0 pathway selects SOIL_MOISTURE_CONFIRMATION because D is 2.5/2.4 °C with a 0.1 °C difference. Independent VWC evidence remains necessary."
      }
    },
    {
      "response_id": "36d3f0fd52b57ed9b0231f7b412c5b60",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 C — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger means are below 8.0 °C. The high-rate trace has a custody gap across handoff, so pulse duration cannot be determined. Calibration and 15-minute logger checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action_sequence": [
          "RECONCILE_LOGGER",
          "UNSCORABLE_IF_TRACE_REMAINS_UNRESOLVED"
        ],
        "reason": "M0 means do not reveal a missing high-rate trace; the revision requires the trace for pulse evaluation."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "RECONCILE_LOGGER",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "formulation_group",
            "value": "P",
            "unit": null
          },
          {
            "name": "pulse_duration",
            "value": null,
            "unit": "min"
          },
          {
            "name": "high_rate_trace_custody_gap",
            "value": true,
            "unit": null
          },
          {
            "name": "all_segment_and_shipment_means_below_8_C",
            "value": true,
            "unit": null
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": "UNSCORABLE if the trace and custody information needed to resolve exposure remains unavailable.",
        "scope": "Recover high-rate trace custody and handoff exposure before resolving the screening decision.",
        "rationale": "The interval means satisfy M0, but the custody gap prevents determining whether the group-P exposure resembles the observed pulse counterexamples. [REDACTED] supports preserving that uncertainty. Neither a pulse nor degradation can be inferred from the gap, and the low means cannot resolve it."
      }
    },
    {
      "response_id": "287867329023b38127ce0bf0b3fde1ff",
      "case_id": "C",
      "response_schema_valid": true,
      "case_facts": "# FAMILY03 C — successor-visible case facts\n\nVerified formulation group P; complete calibrated 15-minute logger means are below 8.0 °C. The high-rate trace has a custody gap across handoff, so pulse duration cannot be determined. Calibration and 15-minute logger checks pass.\n",
      "frozen_target_case": {
        "m0_action": "SCREEN_PASS",
        "target_action_sequence": [
          "RECONCILE_LOGGER",
          "UNSCORABLE_IF_TRACE_REMAINS_UNRESOLVED"
        ],
        "reason": "M0 means do not reveal a missing high-rate trace; the revision requires the trace for pulse evaluation."
      },
      "sanitized_response": {
        "case_id": "C",
        "primary_action": "SCREEN_PASS",
        "additional_actions": [],
        "reported_values": [
          {
            "name": "all_required_logger_means_below_8_C",
            "value": true,
            "unit": null
          },
          {
            "name": "high_rate_trace_custody_gap",
            "value": true,
            "unit": null
          },
          {
            "name": "pulse_duration",
            "value": null,
            "unit": "minutes"
          }
        ],
        "preserved_baseline_action_ids": [
          "SCREEN_PASS",
          "STABILITY_REVIEW",
          "RECONCILE_LOGGER",
          "UNSCORABLE"
        ],
        "fallback": null,
        "scope": "M0 interval-mean screening only; pulse duration remains unknown.",
        "rationale": "The required 15-minute logger record is complete, its checks pass, and its means are below 8.0 °C. The custody gap affects the supplemental high-rate trace, which M0 does not require. It prevents a pulse-duration conclusion but does not invalidate the supplied M0 inputs or establish product safety."
      }
    }
  ]
}
