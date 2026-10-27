from __future__ import annotations

import json
from pathlib import Path

from .calculations import is_normalized_kernel, observation_intervention_distinct


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "data" / "architecture" / "probabilistic-system-dynamics" / "examples"


def load_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_example_paths() -> list[Path]:
    return sorted(EXAMPLE_DIR.glob("*.json"))


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    rid = record.get("psd_id", "<missing>")
    for key in ("system_context", "state_space", "transition_law", "probability_semantics", "intervention_distribution", "unmapped_residue"):
        if not record.get(key):
            errors.append(f"{rid}: missing {key}")

    ctx = record.get("system_context", {})
    for field in ("boundary_rule", "environment", "open_closed_hybrid", "observer_frame", "purpose_of_model"):
        if field not in ctx:
            errors.append(f"{rid}: missing system_context.{field}")

    state = record.get("state_space", {})
    if "observed_variables" not in state or "latent_variables" not in state:
        errors.append(f"{rid}: observed/latent variables not separated")

    law = record.get("transition_law", {})
    assumptions = law.get("assumptions", {})
    for assumption in ("markov", "stationary", "ergodic", "linear", "gaussian", "closed_system"):
        if assumption not in assumptions:
            errors.append(f"{rid}: missing assumption {assumption}")
    if law.get("transition_kernel") and not is_normalized_kernel(law["transition_kernel"]):
        errors.append(f"{rid}: transition kernel not normalized")
    record_text = json.dumps(record, ensure_ascii=False).lower()
    if law.get("law_type") == "deterministic" and "physical randomness" in record_text and "not physical randomness" not in record_text:
        errors.append(f"{rid}: deterministic relation forced into pseudo-randomness")

    for item in record.get("probability_semantics", []):
        prob = item.get("probability", {})
        for field in ("value", "event_or_variable", "conditions", "time_scope", "system_boundary", "source", "estimation_method", "sample_or_model", "uncertainty", "claim_ceiling"):
            if field not in prob:
                errors.append(f"{rid}: probability missing {field}")
        if "value" in prob and not 0 <= prob["value"] <= 1:
            errors.append(f"{rid}: probability out of range")
        ceiling = prob.get("claim_ceiling", "").lower()
        if item.get("semantic_type") == "posterior" and "physical randomness" in ceiling and "not physical randomness" not in ceiling:
            errors.append(f"{rid}: posterior treated as physical randomness")
        if item.get("not_intervention_unless_declared") is not True:
            errors.append(f"{rid}: probability may be mistaken for intervention")

    if not observation_intervention_distinct(record):
        errors.append(f"{rid}: observation/intervention distributions not separated")

    entropy_text = record_text
    if "shannon entropy equals thermodynamic entropy" in entropy_text or "信息熵等于热力学熵" in entropy_text:
        errors.append(f"{rid}: entropy conflation")
    if "high probability proves" in entropy_text or "高概率证明" in entropy_text:
        errors.append(f"{rid}: high probability causal proof overclaim")
    if ("macro always" in entropy_text and "does not claim macro always" not in entropy_text) or "宏观永远" in entropy_text:
        errors.append(f"{rid}: coarse graining overclaim")
    if not record.get("unmapped_residue"):
        errors.append(f"{rid}: missing residue")

    coarse = record.get("coarse_graining_emergence", {})
    if not coarse.get("micro_macro_map") or not coarse.get("information_loss") or not coarse.get("control_case"):
        errors.append(f"{rid}: coarse graining lacks map/loss/control")

    return errors


def validate_all(paths: list[Path] | None = None) -> dict:
    selected = paths or iter_example_paths()
    failures = {}
    for path in selected:
        errors = validate_record(load_record(path))
        if errors:
            failures[str(path)] = errors
    return {"checked": len(selected), "failures": failures, "status": "PASS" if not failures else "FAIL"}


def main() -> int:
    result = validate_all()
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
