#!/usr/bin/env python3
"""Recalculate the public-output interval slice used by stage 4.

The comparison follows the stage-4 operation at lines 355-371: the 14-row
provided output is column-averaged for each simulation, then the HWS=1 output
is compared with HWS=0.  This is an output-level audit, not the full EU
mortality analysis; the script therefore labels the result as a 14-row public
output mean rather than a population-weighted EU total.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile


def q7(values: list[float], probability: float) -> float:
    """R's default type-7 sample quantile for finite values."""
    values = sorted(values)
    h = (len(values) - 1) * probability
    lower = math.floor(h)
    upper = math.ceil(h)
    if lower == upper:
        return values[lower]
    return values[lower] + (h - lower) * (values[upper] - values[lower])


def load_simulations(zf: zipfile.ZipFile, name: str) -> list[list[float]]:
    raw = zf.read(f"MCC-HEWS-main/data/{name}").decode("utf-8")
    rows = list(csv.reader(io.StringIO(raw)))
    if len(rows) != 15 or len(rows[0]) != 1002:
        raise ValueError(f"unexpected {name} shape: {len(rows)} x {len(rows[0])}")
    return [[float(value) for value in row[:1000]] for row in rows[1:]]


def mean_by_simulation(rows: list[list[float]]) -> list[float]:
    return [sum(row[index] for row in rows) / len(rows) for index in range(1000)]


def summarize(values: list[float]) -> dict[str, float | list[float]]:
    reported = [q7(values[:100], 0.025), q7(values[:100], 0.975)]
    complete = [q7(values, 0.025), q7(values, 0.975)]
    return {
        "mean_all_1000": sum(values) / len(values),
        "ci_reported_1_to_100": reported,
        "ci_all_1_to_1000": complete,
        "width_reported_1_to_100": reported[1] - reported[0],
        "width_all_1_to_1000": complete[1] - complete[0],
        "width_delta_all_minus_reported": (complete[1] - complete[0]) - (reported[1] - reported[0]),
    }


def audit(package: str) -> dict:
    package_bytes = open(package, "rb").read()
    with zipfile.ZipFile(io.BytesIO(package_bytes)) as zf:
        an_hws1 = mean_by_simulation(load_simulations(zf, "ansimlist_1_hws1.csv"))
        an_hws0 = mean_by_simulation(load_simulations(zf, "ansimlist_1_hws0.csv"))
        af_hws1 = mean_by_simulation(load_simulations(zf, "afsimlist_1_hws1.csv"))
        af_hws0 = mean_by_simulation(load_simulations(zf, "afsimlist_1_hws0.csv"))

    an_difference = [x - y for x, y in zip(an_hws1, an_hws0)]
    af_difference = [x - y for x, y in zip(af_hws1, af_hws0)]
    af_ratio = [(x - y) / y * 100 for x, y in zip(af_hws1, af_hws0)]

    return {
        "package_sha256": hashlib.sha256(package_bytes).hexdigest(),
        "comparison": "ansimlist_1_hws1 minus ansimlist_1_hws0 and afsimlist_1_hws1 minus afsimlist_1_hws0",
        "stage4_locator": "04.stage4_final_analysis_and_reporting.R:355-371",
        "rows_in_public_output_mean": 14,
        "simulations_available": 1000,
        "reported_simulation_slice": "1:100",
        "metrics": {
            "AN_difference": summarize(an_difference),
            "AF_difference_percentage_points": summarize(af_difference),
            "AF_ratio_percent": summarize(af_ratio),
        },
        "interpretation": {
            "point_estimate_change": "none from changing quantile slice; point means use the same provided output",
            "interval_change": "all-1000 intervals are wider for AN and AF difference, but slightly narrower for AF ratio; all preserve the same direction",
            "not_claimed": [
                "full rerun of stage 1 mortality-temperature models",
                "population-weighted EU total",
                "proof that the Urban headline 25.2% CI changes by the same amount",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    args = parser.parse_args()
    print(json.dumps(audit(args.package), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
