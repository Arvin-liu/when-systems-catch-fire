#!/usr/bin/env python3
"""Recompute the crude SELECT in-trial event proportions, ARR and approximate NNT.

The published SELECT analysis is time-to-first-event with censoring and
competing-risk cumulative incidence. This script intentionally computes only
the transparent count/denominator approximation and labels the time-window
limitation in its output.
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext

getcontext().prec = 28


def result(label: str, treatment_events: int, treatment_n: int, control_events: int, control_n: int) -> dict:
    treatment_risk = Decimal(treatment_events) / Decimal(treatment_n)
    control_risk = Decimal(control_events) / Decimal(control_n)
    arr = control_risk - treatment_risk
    return {
        "endpoint": label,
        "treatment": {"events": treatment_events, "n": treatment_n, "crude_event_proportion": float(treatment_risk)},
        "control": {"events": control_events, "n": control_n, "crude_event_proportion": float(control_risk)},
        "absolute_risk_difference_control_minus_treatment": float(arr),
        "approximate_nnt": float(Decimal(1) / arr) if arr > 0 else None,
    }


output = {
    "source": "SELECT published counts; no individual-level data",
    "time_window": "in-trial observation period from randomization to each participant's final in-trial observation",
    "interpretation": "crude count/denominator approximation; not a fixed-time Aalen-Johansen NNT, not a 5-year or lifetime NNT",
    "primary_mace": result("first three-point MACE", 569, 8803, 701, 8801),
    "reported_rounded_risk_difference_percentage_points": 1.5,
}

print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
