#!/usr/bin/env python3
"""Recompute bounded GONGGA annual totals from published monthly posterior files.

Daily coverage is derived from each NetCDF ``history`` attribute's
``HEMCO_diagnostics.YYYYMMDD0000.nc`` inputs. The primary annual estimate
weights monthly means only by days represented in that history. A separate
full-month sensitivity reports the effect of imputing missing month-days at
the observed monthly mean. This is an analysis artifact, not a toolbox tool.

Requires netCDF4 1.7.2 and NumPy 2.0.2. Fetch the three input files from their
recorded Figshare URLs, then pass their directory with --data-dir.
"""

import argparse
import calendar
import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
from netCDF4 import Dataset


EXPECTED = {
    2019: (
        "2019_GONGGA-CH4_Flux_CAMS_TRO.nc",
        4601366,
        "3f88d98c231a9deae00fc4042bcd6613",
        "5184942a22ff5d04c0b625740e2ee7b0aa7e8c8e70f1e16fe58abe0a854883e8",
    ),
    2023: (
        "2023_GONGGA-CH4_Flux_CAMS_TRO.nc",
        4601366,
        "b54c2122d5f56f08da82b9ed55b75fde",
        "3882cec6b0e737e7e4680a37633401971f15265ac1a70ffcb48934c7d3f79cb3",
    ),
    2024: (
        "2024_GONGGA-CH4_Flux_CAMS_TRO.nc",
        4595180,
        "2f0f439d9b010a96a7d015c4ebcf30cf",
        "49a8c80a070e9fe89d9d8f3e1383f62a8874621c4e582dcede74060df3e64601",
    ),
}
SECTORS = [
    "EmisCH4_OtherNat",
    "EmisCH4_Wetlands",
    "EmisCH4_BB",
    "EmisCH4_AW",
    "EmisCH4_FF",
]
HISTORY_DAILY_FILE = re.compile(r"HEMCO_diagnostics\.(\d{8})0000\.nc")
SECONDS_PER_DAY = 86400.0
KG_PER_TG = 1e9


def source_dates_from_history(history, year):
    dates = [
        datetime.strptime(value, "%Y%m%d").date()
        for value in HISTORY_DAILY_FILE.findall(history)
    ]
    if not dates:
        raise SystemExit(f"no daily HEMCO diagnostics found in {year} history")
    if len(set(dates)) != len(dates):
        raise SystemExit(f"duplicate daily HEMCO diagnostic date in {year} history")
    if any(value.year != year for value in dates):
        raise SystemExit(f"daily HEMCO diagnostic year mismatch in {year} history")
    dates.sort()
    if dates[0] != date(year, 1, 1):
        raise SystemExit(f"{year} history does not begin on January 1")
    expected_contiguous = [dates[0] + timedelta(days=i) for i in range(len(dates))]
    if dates != expected_contiguous:
        raise SystemExit(f"{year} history contains an internal daily coverage gap")
    return dates


def daily_counts_by_month(source_dates):
    return [sum(value.month == month for value in source_dates) for month in range(1, 13)]


def integrate_sectors(flux_by_sector, area, day_weights):
    seconds = np.asarray(day_weights, dtype=np.float64) * SECONDS_PER_DAY
    sector_totals = {}
    max_method_delta = 0.0
    for key, flux in flux_by_sector.items():
        monthly_spatial = np.array(
            [np.sum(flux[i] * area, dtype=np.float64) for i in range(12)],
            dtype=np.float64,
        )
        total = float(np.sum(monthly_spatial * seconds, dtype=np.float64) / KG_PER_TG)
        vector = float(
            np.sum(flux * area[None, :, :] * seconds[:, None, None], dtype=np.float64)
            / KG_PER_TG
        )
        delta = abs(total - vector)
        if delta > 1e-10:
            raise SystemExit(f"vector cross-check mismatch: {key}; delta={delta}")
        max_method_delta = max(max_method_delta, delta)
        sector_totals[key] = total
    return {
        "sectors_Tg_CH4": sector_totals,
        "five_positive_source_sectors_Tg_CH4": float(sum(sector_totals.values())),
        "monthly_spatial_vs_vectorized_max_abs_delta_Tg": max_method_delta,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    root = Path(parser.parse_args().data_dir)
    results = []
    flux_by_year = {}
    area_by_year = {}
    dates_by_year = {}

    for year, (name, expected_size, wanted_md5, wanted_sha256) in EXPECTED.items():
        path = root / name
        raw = path.read_bytes()
        got_md5 = hashlib.md5(raw).hexdigest()
        got_sha256 = hashlib.sha256(raw).hexdigest()
        if len(raw) != expected_size or got_md5 != wanted_md5 or got_sha256 != wanted_sha256:
            raise SystemExit(f"input integrity mismatch: {name}")

        with Dataset(path) as dataset:
            if len(dataset.dimensions.get("time", ())) != 12:
                raise SystemExit(f"expected 12 monthly records: {name}")
            area = np.asarray(dataset["AREA"][:], dtype=np.float64)
            area_by_year[year] = area
            source_dates = source_dates_from_history(
                str(getattr(dataset, "history", "")), year
            )
            actual_days = daily_counts_by_month(source_dates)
            calendar_days = [calendar.monthrange(year, month)[1] for month in range(1, 13)]
            if any(actual > expected for actual, expected in zip(actual_days, calendar_days)):
                raise SystemExit(f"daily source-file count exceeds calendar days: {year}")
            if sum(actual_days) != len(source_dates):
                raise SystemExit(f"monthly source-file counts do not sum to daily count: {year}")
            flux_by_year[year] = {}
            for key in SECTORS:
                flux = np.asarray(dataset[key][:], dtype=np.float64)
                if flux.shape[0] != 12 or flux.shape[1:] != area.shape:
                    raise SystemExit(f"unexpected monthly flux shape: {year}/{key}")
                flux_by_year[year][key] = flux

        dates_by_year[year] = source_dates
        available_date_set = set(source_dates)
        missing_dates = [
            (date(year, 1, 1) + timedelta(days=offset)).isoformat()
            for offset in range((date(year, 12, 31) - date(year, 1, 1)).days + 1)
            if date(year, 1, 1) + timedelta(days=offset) not in available_date_set
        ]
        actual = integrate_sectors(flux_by_year[year], area, actual_days)
        full_month = integrate_sectors(flux_by_year[year], area, calendar_days)
        results.append(
            {
                "year": year,
                "file": name,
                "bytes": len(raw),
                "md5": got_md5,
                "sha256": got_sha256,
                "monthly_record_count": 12,
                "daily_coverage": {
                    "daily_source_file_count": len(source_dates),
                    "first_daily_source_date": source_dates[0].isoformat(),
                    "last_daily_source_date": source_dates[-1].isoformat(),
                    "monthly_daily_source_file_counts": {
                        f"{month:02d}": count for month, count in enumerate(actual_days, 1)
                    },
                    "expected_calendar_days": sum(calendar_days),
                    "missing_calendar_dates": missing_dates,
                },
                "available_coverage_estimate": {
                    "weighting": "monthly posterior mean weighted only by daily source files listed in NetCDF history",
                    "coverage_days": len(source_dates),
                    **actual,
                },
                "full_month_imputation_sensitivity": {
                    "weighting": "Gregorian month lengths; any missing day is imputed at that month's observed posterior mean",
                    "imputed_days": sum(calendar_days) - len(source_dates),
                    **full_month,
                },
            }
        )

    proxy_results = {}
    for year in (2023, 2024):
        coverage = dates_by_year[year]
        if coverage[-1] < date(year, 12, 29):
            raise SystemExit(f"{year} does not cover the matched calendar-date proxy")
        proxy_days = [
            calendar.monthrange(year, month)[1] if month < 12 else 29
            for month in range(1, 13)
        ]
        proxy = integrate_sectors(
            flux_by_year[year], area_by_year[year], proxy_days
        )
        proxy_results[str(year)] = {
            "calendar_window": f"January 1 through December 29, {year}",
            "proxy_days": sum(proxy_days),
            "monthly_mean_proxy_uses_observed_monthly_means": True,
            **proxy,
        }

    rate_2023 = (
        proxy_results["2023"]["five_positive_source_sectors_Tg_CH4"]
        / proxy_results["2023"]["proxy_days"]
    )
    rate_2024 = (
        proxy_results["2024"]["five_positive_source_sectors_Tg_CH4"]
        / proxy_results["2024"]["proxy_days"]
    )
    proxy_results["2024_vs_2023_daily_rate_difference_percent"] = (
        (rate_2024 / rate_2023) - 1.0
    ) * 100.0

    print(
        json.dumps(
            {
                "method": "Monthly posterior flux (kg/m2/s) times grid-cell area (m2), weighted by daily source-file coverage, converted to Tg CH4; Gregorian full-month weighting is reported only as imputation sensitivity.",
                "daily_coverage_source": "HEMCO_diagnostics.YYYYMMDD0000.nc filenames in each NetCDF history attribute",
                "sectors": SECTORS,
                "results": results,
                "matched_calendar_date_monthly_mean_proxy": {
                    "cutoff_month_day": "12-29",
                    "interpretation": "matched-date proxy using monthly means, not daily-resolved totals; December 2023 uses its 31-day monthly mean to proxy 29 calendar days",
                    "comparisons": proxy_results,
                    "daily_rate_Tg_CH4_per_day": {
                        "2023": rate_2023,
                        "2024": rate_2024,
                    },
                },
            },
            sort_keys=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
