#!/usr/bin/env python3
"""Deterministic static audit of the public MCC-HEWS package.

This deliberately does not claim to rerun the study.  The public archive lacks
the raw mortality object used by stage 1, and the audit host may not have R.
The script only inspects the supplied zip, R source, and precomputed CSVs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import PurePosixPath


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_member(zf: zipfile.ZipFile, suffix: str) -> tuple[str, str]:
    names = [n for n in zf.namelist() if n.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"expected one member ending {suffix!r}, got {names}")
    raw = zf.read(names[0])
    return names[0], raw.decode("utf-8")


def csv_bytes(zf: zipfile.ZipFile, suffix: str) -> tuple[str, bytes]:
    names = [n for n in zf.namelist() if n.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"expected one member ending {suffix!r}, got {names}")
    return names[0], zf.read(names[0])


def line_for(text: str, needle: str) -> int | None:
    for number, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return number
    return None


def audit(package: str) -> dict:
    with zipfile.ZipFile(package) as zf:
        stage1_name, stage1 = text_member(zf, "01.stage1_erf_coefficient_preparation.R")
        stage2_name, stage2 = text_member(zf, "02.stage2_meta_regression.R")
        stage3_name, stage3 = text_member(zf, "03.stage3_attributable_mortality_calculation.R")
        stage4_name, stage4 = text_member(zf, "04.stage4_final_analysis_and_reporting.R")

        tmean_name, tmean_raw = csv_bytes(zf, "data/tmeanperpar.csv")
        tmean_rows = list(csv.DictReader(io.StringIO(tmean_raw.decode("utf-8"))))
        city_periods = Counter(row.get("period") for row in tmean_rows)
        hws = Counter(row.get("hws") for row in tmean_rows)
        hwc = Counter(row.get("hwc") for row in tmean_rows)
        cities = sorted({row.get("cityname") for row in tmean_rows})

        output_shapes = {}
        for name in sorted(
            n for n in zf.namelist()
            if PurePosixPath(n).name.startswith(("ansimlist_", "afsimlist_"))
            and n.endswith(".csv")
        ):
            rows = list(csv.reader(io.StringIO(zf.read(name).decode("utf-8"))))
            output_shapes[PurePosixPath(name).name] = {
                "data_rows": max(len(rows) - 1, 0),
                "columns_first_row": len(rows[0]) if rows else 0,
                "simulation_columns_if_1002": 1000 if rows and len(rows[0]) == 1002 else None,
            }

        return {
            "package_sha256": sha256_bytes(open(package, "rb").read()),
            "members": {
                "stage1": stage1_name,
                "stage2": stage2_name,
                "stage3": stage3_name,
                "stage4": stage4_name,
                "tmeanperpar": tmean_name,
            },
            "missing_raw_input_marker": {
                "stage1_reads_MCCdata_20230830_RData": "MCCdata_20230830.RData" in stage1,
                "stage1_marker_line": line_for(stage1, "MCCdata_20230830.RData"),
            },
            "stage3_simulation": {
                "nsim_1000_present": bool(re.search(r"nsim\s*<-\s*1000", stage3)),
                "nsim_line": line_for(stage3, "nsim <- 1000"),
                "seed_12345_present": "set.seed(12345)" in stage3,
                "simulation_loop_marker_line": line_for(stage3, "for (i in 1:nsim)"),
            },
            "stage4_interval_selection": {
                "exact_1_colon_100_count": len(re.findall(r"(?<![0-9])1:100(?![0-9])", stage4)),
                "first_exact_1_colon_100_line": line_for(stage4, "1:100"),
                "has_1000_marker": "1:1000" in stage4,
            },
            "commented_sensitivity_models": {
                "mod4_comment_present": bool(re.search(r"^\s*#\s*mod4\b", stage2, re.MULTILINE)),
                "mod5_comment_present": bool(re.search(r"^\s*#\s*mod5\b", stage2, re.MULTILINE)),
                "mod4_first_comment_line": line_for(stage2, "# mod4"),
                "mod5_first_comment_line": line_for(stage2, "# mod5"),
            },
            "tmeanperpar": {
                "records": len(tmean_rows),
                "unique_cities": len(cities),
                "city_period_counts": dict(sorted(city_periods.items())),
                "hws_counts": dict(sorted(hws.items(), key=lambda item: str(item[0]))),
                "hwc_counts": dict(sorted(hwc.items(), key=lambda item: str(item[0]))),
            },
            "provided_output_shapes": output_shapes,
            "interpretation": "static and precomputed-output audit only; not a full numerical rerun",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    args = parser.parse_args()
    print(json.dumps(audit(args.package), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
