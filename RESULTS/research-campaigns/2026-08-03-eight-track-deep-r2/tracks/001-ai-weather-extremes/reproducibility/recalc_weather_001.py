"""Reproduce the coarse public-data audit for R2 track 001.

This intentionally does not claim to reproduce Zhang et al.'s 0.25-degree
headline table. It loads the official WeatherBench2 64x32 Zarr data, builds
strict 1979-2017 per-grid/per-month maxima, counts 2020 exceedances, and
scores the available HRES/Pangu 2-m-temperature forecasts on those events.
Requires xarray, zarr, fsspec/gcsfs, dask, numpy, and public internet access.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import xarray as xr


BASE = "https://storage.googleapis.com/weatherbench2/datasets/"
ERA5 = BASE + "era5/1959-2022-6h-64x32_equiangular_conservative.zarr"
HRES = BASE + "hres/2016-2022-0012-64x32_equiangular_conservative.zarr"
PANGU = BASE + "pangu/2018-2022_0012_64x32_equiangular_conservative.zarr"


def train_thresholds(era5: xr.Dataset) -> np.ndarray:
    threshold = np.full((12, era5.sizes["longitude"], era5.sizes["latitude"]), -np.inf, dtype=np.float32)
    for year in range(1979, 2018):
        block = era5["2m_temperature"].sel(time=slice(f"{year}-01-01", f"{year}-12-31T23:59:59")).load()
        month = block.time.dt.month.values
        for number in range(1, 13):
            threshold[number - 1] = np.maximum(threshold[number - 1], block.values[month == number].max(axis=0))
    return threshold


def score_model(ds: xr.Dataset, truth: xr.DataArray, thresholds: np.ndarray, mask: np.ndarray, name: str) -> list[dict]:
    truth_values = truth.values
    truth_index = {stamp: index for index, stamp in enumerate(truth.time.values)}
    rows = []
    for lead in (24, 48, 120):
        times = ds.time.values
        index = np.where(
            (times >= np.datetime64("2020-01-01T00:00:00"))
            & (times <= np.datetime64("2020-12-31T23:59:59") - np.timedelta64(lead, "h"))
        )[0]
        valid = times[index] + np.timedelta64(lead, "h")
        keep = np.array([stamp in truth_index for stamp in valid])
        index, valid = index[keep], valid[keep]
        lead_index = int(np.where(ds.prediction_timedelta.values == lead)[0][0])
        forecast = ds["2m_temperature"].isel(time=index, prediction_timedelta=lead_index).load().values
        observed = truth_values[np.array([truth_index[stamp] for stamp in valid])]
        month = np.array([int(str(stamp)[5:7]) for stamp in valid])
        event = (observed > np.stack([thresholds[number - 1] for number in month])) & mask[None, :, :]
        error = forecast - observed
        event_error = error[event]
        rows.append({
            "model": name,
            "lead_hours": lead,
            "n_valid_times": int(len(valid)),
            "record_count": int(event.sum()),
            "overall_rmse_K": float(np.sqrt(np.mean(error**2))),
            "record_rmse_K": float(np.sqrt(np.mean(event_error**2))),
            "record_bias_K": float(np.mean(event_error)),
        })
    return rows


def main() -> None:
    era5 = xr.open_zarr(ERA5, consolidated=True, chunks={})
    hres = xr.open_zarr(HRES, consolidated=True, chunks={})
    pangu = xr.open_zarr(PANGU, consolidated=True, chunks={})
    thresholds = train_thresholds(era5)
    land = era5["land_sea_mask"].load().values > 0.5
    mask = land & (era5.latitude.values[None, :] > -60)
    truth = era5["2m_temperature"].sel(time=slice("2020-01-01", "2020-12-31T23:59:59")).load()
    rows = score_model(hres, truth, thresholds, mask, "HRES") + score_model(pangu, truth, thresholds, mask, "Pangu")
    output = {
        "definition": "strict per-grid/per-calendar-month 1979-2017 maximum; 2020 valid-time exceedance",
        "grid": "WeatherBench2 64x32; land_sea_mask>0.5; latitude>-60",
        "warning": "coarse public-data audit, not Zhang et al. 0.25-degree headline replication",
        "results": rows,
    }
    destination = Path(__file__).parent / "output/coarse_forecast_recalc.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
