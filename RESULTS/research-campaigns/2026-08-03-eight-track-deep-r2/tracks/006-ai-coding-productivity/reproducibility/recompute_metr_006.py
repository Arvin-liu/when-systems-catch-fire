#!/usr/bin/env python3
"""Recompute the METR 2025 early-2025 AI developer result and bounded checks.

This script intentionally keeps the published primary specification separate from
descriptive and sensitivity analyses.  It consumes the public, anonymized CSV
from the METR reproduction repository and writes deterministic JSON/CSV outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm


REQUIRED_COLUMNS = {
    "dev_id",
    "issue_id",
    "predicted_time_no_ai",
    "predicted_time_ai_allowed",
    "prior_task_exposure_1_to_5",
    "external_resource_needs_1_to_3",
    "ai_treatment",
    "initial_implementation_time",
    "post_review_implementation_time",
}


def round_value(value: object, digits: int = 6) -> object:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return round(float(value), digits)
    return value


def impute_post_review(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    means = {
        str(treatment): float(
            df.loc[
                (df["ai_treatment"] == treatment)
                & df["post_review_implementation_time"].notna(),
                "post_review_implementation_time",
            ].mean()
        )
        for treatment in (0, 1)
    }
    out = df.copy()
    out["post_review_observed"] = out["post_review_implementation_time"].notna()
    out["post_review_imputed"] = out["post_review_implementation_time"].fillna(
        out["ai_treatment"].map({int(k): v for k, v in means.items()})
    )
    out["total_implementation_time"] = (
        out["initial_implementation_time"] + out["post_review_imputed"]
    )
    return out, means


def transformed_effect(beta: float, standard_error: float) -> dict[str, float]:
    z = norm.ppf(0.975)
    lower = beta - z * standard_error
    upper = beta + z * standard_error
    return {
        "estimate_time_change": round_value(np.exp(beta) - 1),
        "ci95_lower": round_value(np.exp(lower) - 1),
        "ci95_upper": round_value(np.exp(upper) - 1),
        "beta_log_time": round_value(beta),
        "se_beta": round_value(standard_error),
    }


def fit_treatment_model(
    df: pd.DataFrame,
    outcome: str,
    covariance: str = "nonrobust",
    groups: pd.Series | None = None,
) -> dict[str, object]:
    work = df.copy()
    work["log_outcome"] = np.log(work[outcome])
    work["log_predicted_time_no_ai"] = np.log(work["predicted_time_no_ai"])
    model = smf.ols(
        "log_outcome ~ ai_treatment + log_predicted_time_no_ai",
        data=work,
        missing="drop",
    )
    if covariance == "cluster":
        result = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    else:
        result = model.fit(cov_type=covariance)
    beta = float(result.params["ai_treatment"])
    se = float(result.bse["ai_treatment"])
    effect = transformed_effect(beta, se)
    effect.update(
        {
            "outcome": outcome,
            "covariance": covariance,
            "n": int(result.nobs),
            "r_squared": round_value(result.rsquared),
        }
    )
    return effect


def core_results(df: pd.DataFrame) -> list[dict[str, object]]:
    results = []
    for covariance in ("nonrobust", "HC3", "cluster"):
        results.append(
            fit_treatment_model(
                df,
                "total_implementation_time",
                covariance=covariance,
                groups=df["dev_id"],
            )
        )
    return results


def subgroup_results(df: pd.DataFrame) -> list[dict[str, object]]:
    """Use the paper's preregistered-style cutoffs and its interaction form."""
    results: list[dict[str, object]] = []
    subgroup_specs = {
        "prior_task_exposure_high": (
            df["prior_task_exposure_1_to_5"].notna(),
            df["prior_task_exposure_1_to_5"] > 3,
        ),
        "external_resource_needs_low": (
            df["external_resource_needs_1_to_3"].notna(),
            df["external_resource_needs_1_to_3"] <= 2,
        ),
    }
    for name, (available, indicator) in subgroup_specs.items():
        work = df.loc[available].copy()
        work["subgroup"] = indicator.loc[work.index].astype(int)
        work["log_total"] = np.log(work["total_implementation_time"])
        work["log_predicted_time_no_ai"] = np.log(work["predicted_time_no_ai"])
        model = smf.ols(
            "log_total ~ ai_treatment * subgroup + log_predicted_time_no_ai",
            data=work,
            missing="drop",
        ).fit()
        for level, label in ((0, "reference"), (1, "target")):
            beta = float(model.params["ai_treatment"])
            se = float(model.bse["ai_treatment"])
            if level == 1:
                contrast = model.t_test([0, 1, 0, 1, 0])
                beta = float(np.asarray(contrast.effect).squeeze())
                se = float(np.asarray(contrast.sd).squeeze())
            record = transformed_effect(beta, se)
            record.update(
                {
                    "subgroup": name,
                    "level": label,
                    "level_value": level,
                    "n": int(model.nobs),
                    "n_level": int((work["subgroup"] == level).sum()),
                    "interaction_beta": round_value(
                        model.params.get("ai_treatment:subgroup")
                    ),
                    "interaction_p_value": round_value(
                        model.pvalues.get("ai_treatment:subgroup")
                    ),
                }
            )
            results.append(record)
    return results


def sensitivity_results(df: pd.DataFrame) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []

    for covariance in ("nonrobust", "HC3", "cluster"):
        results.append(
            {
                **fit_treatment_model(
                    df,
                    "initial_implementation_time",
                    covariance=covariance,
                    groups=df["dev_id"],
                ),
                "sensitivity": "initial_only_outcome",
            }
        )

    observed = df.loc[df["post_review_implementation_time"].notna()].copy()
    for covariance in ("nonrobust", "HC3", "cluster"):
        results.append(
            {
                **fit_treatment_model(
                    observed,
                    "total_implementation_time",
                    covariance=covariance,
                    groups=observed["dev_id"],
                ),
                "sensitivity": "complete_post_review_cases",
            }
        )

    valid_external = df.loc[
        df["external_resource_needs_1_to_3"].isna()
        | df["external_resource_needs_1_to_3"].isin([1, 2, 3])
    ].copy()
    results.append(
        {
            **fit_treatment_model(
                valid_external,
                "total_implementation_time",
                covariance="nonrobust",
                groups=valid_external["dev_id"],
            ),
            "sensitivity": "exclude_external_resource_out_of_range_row",
        }
    )

    for label, imputation in (
        (
            "extreme_ai_allowed_one_hour_control_zero",
            {0: 0.0, 1: 60.0},
        ),
        (
            "extreme_ai_allowed_zero_control_one_hour",
            {0: 60.0, 1: 0.0},
        ),
    ):
        extreme = df.copy()
        missing = extreme["post_review_implementation_time"].isna()
        extreme.loc[missing, "post_review_imputed"] = extreme.loc[
            missing, "ai_treatment"
        ].map(imputation)
        extreme["total_implementation_time"] = (
            extreme["initial_implementation_time"] + extreme["post_review_imputed"]
        )
        results.append(
            {
                **fit_treatment_model(
                    extreme,
                    "total_implementation_time",
                    covariance="nonrobust",
                    groups=extreme["dev_id"],
                ),
                "sensitivity": label,
            }
        )

    work = df.copy()
    work["log_total"] = np.log(work["total_implementation_time"])
    work["log_predicted_time_no_ai"] = np.log(work["predicted_time_no_ai"])
    model = smf.ols(
        "log_total ~ ai_treatment + log_predicted_time_no_ai + C(dev_id)",
        data=work,
        missing="drop",
    ).fit(cov_type="cluster", cov_kwds={"groups": work["dev_id"]})
    results.append(
        {
            **transformed_effect(
                float(model.params["ai_treatment"]),
                float(model.bse["ai_treatment"]),
            ),
            "outcome": "total_implementation_time",
            "covariance": "cluster",
            "n": int(model.nobs),
            "r_squared": round_value(model.rsquared),
            "sensitivity": "developer_fixed_effects",
        }
    )

    for outcome, label in (
        ("total_implementation_time", "ratio_of_means_imputed_total"),
        ("initial_implementation_time", "ratio_of_means_initial_only"),
    ):
        means = df.groupby("ai_treatment")[outcome].mean()
        results.append(
            {
                "sensitivity": label,
                "outcome": outcome,
                "estimate_time_change": round_value(means[1] / means[0] - 1),
                "control_mean": round_value(means[0]),
                "ai_allowed_mean": round_value(means[1]),
            }
        )
    return results


def group_descriptives(df: pd.DataFrame) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for treatment, group in df.groupby("ai_treatment", sort=True):
        for outcome in (
            "initial_implementation_time",
            "post_review_implementation_time",
            "total_implementation_time",
        ):
            values = group[outcome]
            records.append(
                {
                    "ai_treatment": int(treatment),
                    "outcome": outcome,
                    "n": int(values.notna().sum()),
                    "mean": round_value(values.mean()),
                    "median": round_value(values.median()),
                    "std": round_value(values.std()),
                    "min": round_value(values.min()),
                    "max": round_value(values.max()),
                }
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    raw = pd.read_csv(args.input)
    missing_columns = sorted(REQUIRED_COLUMNS - set(raw.columns))
    if missing_columns:
        raise ValueError(f"missing required columns: {missing_columns}")

    df, imputation_means = impute_post_review(raw)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    profile = {
        "rows": int(len(df)),
        "unique_developers": int(df["dev_id"].nunique()),
        "unique_issues": int(df["issue_id"].nunique()),
        "treatment_counts": {
            str(int(k)): int(v) for k, v in df["ai_treatment"].value_counts().sort_index().items()
        },
        "missing_counts": {
            str(k): int(v) for k, v in raw.isna().sum().items() if int(v) > 0
        },
        "post_review_imputation_means": imputation_means,
        "post_review_missing_by_treatment": {
            str(int(k)): int(v)
            for k, v in (
                raw.loc[raw["post_review_implementation_time"].isna()]
                .groupby("ai_treatment")
                .size()
                .items()
            )
        },
        "developer_treatment_cell_counts": [
            {
                "dev_id": int(dev_id),
                "ai_disallowed": int(cells.get(0.0, 0)),
                "ai_allowed": int(cells.get(1.0, 0)),
            }
            for dev_id, cells in df.groupby("dev_id")["ai_treatment"].value_counts().unstack(fill_value=0).iterrows()
        ],
    }

    (args.output_dir / "data_profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n"
    )
    (args.output_dir / "group_descriptives.csv").write_text(
        pd.DataFrame(group_descriptives(df)).to_csv(index=False)
    )
    (args.output_dir / "core_results.json").write_text(
        json.dumps(core_results(df), ensure_ascii=False, indent=2) + "\n"
    )
    (args.output_dir / "subgroup_results.json").write_text(
        json.dumps(subgroup_results(df), ensure_ascii=False, indent=2) + "\n"
    )
    (args.output_dir / "sensitivity_results.json").write_text(
        json.dumps(sensitivity_results(df), ensure_ascii=False, indent=2) + "\n"
    )

    official_like = core_results(df)[0]
    print(
        "official_like="
        + json.dumps(
            {
                key: official_like[key]
                for key in (
                    "estimate_time_change",
                    "ci95_lower",
                    "ci95_upper",
                    "n",
                )
            },
            sort_keys=True,
        )
    )
    print("wrote", args.output_dir)


if __name__ == "__main__":
    main()
