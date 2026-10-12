#!/usr/bin/env python3
"""Run Foundation CI checks sequentially and retain per-command evidence.

Every declared check runs even after an earlier check fails. The aggregate
process exits nonzero if any check fails, so diagnostic continuation never
turns a failed run green. Checks run in one process at a time to keep the
memory-heavy Foundation generators from overlapping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


APP_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = APP_ROOT.parent


@dataclass(frozen=True)
class Check:
    name: str
    argv: tuple[str, ...]
    cwd: str = "."


def foundation_checks(python_executable: str | Path = sys.executable) -> list[Check]:
    py = str(python_executable)

    def check(name: str, *argv: str, cwd: str = ".") -> Check:
        return Check(name=name, argv=(py, *argv), cwd=cwd)

    return [
        Check("lean-foundation", ("lake", "env", "lean", "Foundation.lean"), "formal/lean"),
        check("adjudicate-core", "tools/foundation/adjudicate_core.py", "--check"),
        check("migrate-legacy", "tools/foundation/migrate_legacy.py", "--check"),
        check("validate-foundation", "tools/foundation/validate_foundation.py"),
        check("build-function-asset-census", "tools/foundation/build_function_asset_census.py", "--check"),
        check("adjudicate-function-assets", "tools/foundation/adjudicate_function_assets.py", "--check"),
        check("validate-claim-governance", "tools/foundation/validate_claim_governance.py"),
        check("validate-function-asset-closure", "tools/foundation/validate_function_asset_closure.py"),
        check("function-asset-math-checks", "tools/foundation/run_function_asset_math_checks.py", "--check"),
        check("adjudicate-nonfunction-claims", "tools/foundation/adjudicate_nonfunction_claims.py", "--check"),
        check("validate-nonfunction-claim-closure", "tools/foundation/validate_nonfunction_claim_closure.py"),
        check("build-human-results", "tools/governance/build_human_results.py", "--check"),
        check("run-self-correction", "tools/governance/run_self_correction.py", "--check"),
        check("build-knowledge-experience", "tools/governance/build_knowledge_experience.py", "--check"),
        check("validate-human-visibility", "tools/governance/validate_human_visibility.py"),
        check("validate-knowledge-experience", "tools/governance/validate_knowledge_experience.py"),
        check("validate-fire-seeds", "tools/publication/validate_fire_seeds.py", "--check"),
        check("build-claim-browsers", "tools/governance/build_claim_browsers.py", "--check"),
        check("validate-overall-architecture", "tools/generate_overall_architecture.py", "--check"),
        check("knowledge-experience-determinism", "tools/governance/check_knowledge_experience_determinism.py"),
        check("verify-core-claims", "tools/foundation/verify_core_claims.py", "--check"),
        check("verify-079", "tools/foundation/verify_079.py", "--check"),
        check("validate-080-adjudications", "tools/foundation/validate_080_adjudications.py"),
        check("validate-iteration-sync", "tools/validate_iteration_sync.py"),
        check("validate-phase-d-closeout", "tools/operations/validate_phase_d_closeout.py", "--check"),
        check(
            "compute-q32i-change-propagation",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/121Q32I-request.json",
            "--output", "data/operations/propagation/121Q32I-closure.json",
            "--report", "reports/operations/121Q32I-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/121Q32I-system-map-delta.json",
            "--residue", "data/operations/propagation/121Q32I-residue.json",
            "--era-ref", "0a13c246172c0338bf8dda5dc08db5a574a8b23f",
            "--check",
        ),
        check(
            "compute-method-1-4-continuous-stage-snapshot",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-request.json",
            "--output", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-closure.json",
            "--report", "reports/operations/IGNITION-ITERATION-METHOD-1.4-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-system-map-delta.json",
            "--residue", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726-residue.json",
            "--era-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--head-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--check",
        ),
        check(
            "compute-method-1-4-actor-gate-repair",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-request.json",
            "--output", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-closure.json",
            "--report", "reports/operations/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-system-map-delta.json",
            "--residue", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726-residue.json",
            "--era-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--head-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--check",
        ),
        check(
            "compute-method-1-4-actor-normalized-schema-repair",
            "tools/operations/compute_change_propagation.py",
            "--request", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-request.json",
            "--output", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-closure.json",
            "--report", "reports/operations/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-change-propagation-impact.md",
            "--map-delta", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-system-map-delta.json",
            "--residue", "data/operations/propagation/IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-NORMALIZED-SCHEMA-AND-AUTOMATION-VARIANT-NARROW-REPAIR-R2-20260726-residue.json",
            "--era-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--head-ref", "f59b9f359ea16a346e07e9621049468417b66423",
            "--check",
        ),
        check("validate-phase-e-candidate", "tools/operations/validate_phase_e_candidate.py", "--check"),
        check("validate-system-map", "tools/generate_interactive_system_map.py", "--check"),
        check("validate-homepage-architecture-projection", "tools/validate_homepage_architecture_projection.py", "--check"),
        check("validate-stage-snapshot-actor-contract", "tools/operations/generate_stage_snapshot_actor_contract.py", "--check"),
        check("validate-stage-snapshots", "tools/operations/validate_stage_snapshots.py", "--check"),
        check("stage-snapshot-responsibility-cases", "tools/operations/run_stage_snapshot_responsibility_cases.py"),
        check("validate-human-front-door", "tools/validate_human_front_door.py"),
        check("validate-language-thought", "tools/language_thought/validate_language_thought.py"),
        check("test-language-thought-plane", "-m", "unittest", "tests.test_language_thought_plane"),
        check(
            "validate-epistemic-governance-relationships",
            "tools/validate_epistemic_governance_relationships.py",
            "data/governance/epistemic-governance-relationships.json",
            "--repo-root", ".",
        ),
        check("test-epistemic-governance-relationships", "-m", "unittest", "tests.test_epistemic_governance_relationships", "-v"),
        check("validate-state-changelog", "tools/validate_state_changelog.py"),
        check("test-state-changelog", "-m", "unittest", "tests.test_state_changelog", "-v"),
        check("test-foundation", "-m", "unittest", "tests.foundation.test_foundation"),
        check("test-claim-governance", "-m", "unittest", "tests.foundation.test_claim_governance"),
        check("test-function-asset-closure", "-m", "unittest", "tests.foundation.test_function_asset_closure"),
        check("test-nonfunction-claim-closure", "-m", "unittest", "tests.foundation.test_nonfunction_claim_closure", "-v"),
        check("test-iteration-sync", "-m", "unittest", "tests.test_iteration_sync", "-v"),
        check("test-human-front-door", "-m", "unittest", "tests.test_human_front_door", "-v"),
        check("test-change-propagation", "-m", "unittest", "tests.test_change_propagation", "-v"),
        check("test-human-visibility-self-correction-knowledge-experience", "-m", "unittest",
              "tests.test_human_visibility_gate", "tests.test_self_correction_engine", "tests.test_knowledge_experience", "-v"),
        check("test-stage-snapshot-publication", "-m", "unittest", "tests.test_stage_snapshot_publication", "-v"),
        check("test-era-resolver-and-generated-output-authority", "-m", "unittest",
              "tests.test_era_resolver_generalization", "tests.test_generated_output_authority",
              "tests.test_generated_output_authority_negative", "-v"),
        check("test-phase-e-candidate", "-m", "unittest", "tests.test_phase_e_candidate", "-v"),
        check("test-production-execution-authority", "-m", "unittest", "tests.test_production_execution_authority", "-v"),
        check("test-generator-reconciliation-staleness", "-m", "unittest",
              "tests.foundation.test_generator_reconciliation_staleness", "-v"),
        check("test-propagation-reconciliation", "-m", "unittest", "tests.test_propagation_reconciliation", "-v"),
        check("validate-propagation-reconciliation", "tools/propagation/validate_reconciliation.py", "--check"),
    ]


def default_evidence_dir() -> Path:
    runner_temp = os.environ.get("RUNNER_TEMP")
    if runner_temp:
        return Path(runner_temp) / "foundation-ci-evidence"
    return Path(tempfile.mkdtemp(prefix="foundation-ci-evidence-")) / "results"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _decode(value: bytes | str) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def _tail(value: bytes | str, max_lines: int = 100) -> str:
    lines = _decode(value).splitlines()
    return "\n".join(lines[-max_lines:])


def execute_checks(
    checks: Sequence[Check],
    *,
    repo_root: Path = REPO_ROOT,
    app_root: Path = APP_ROOT,
    evidence_dir: Path,
    env: dict[str, str] | None = None,
) -> dict:
    root = repo_root.resolve()
    app = app_root.resolve()
    output = evidence_dir.expanduser().resolve()
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("Foundation CI evidence directory must be outside the repository")
    output.mkdir(parents=True, exist_ok=False)

    command_env = dict(os.environ if env is None else env)
    python_paths = [str(app), str(app / "tests"), str(app / "tools/foundation")]
    python_paths.extend(item for item in command_env.get("PYTHONPATH", "").split(os.pathsep) if item)
    command_env["PYTHONPATH"] = os.pathsep.join(python_paths)

    ledger_path = output / "command-ledger.jsonl"
    records: list[dict] = []
    failures: list[str] = []
    started_at = datetime.now(timezone.utc).isoformat()
    with ledger_path.open("w", encoding="utf-8") as ledger:
        for number, item in enumerate(checks, 1):
            slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", item.name).strip("-") or f"check-{number}"
            stdout_path = output / f"{number:03d}-{slug}.stdout"
            stderr_path = output / f"{number:03d}-{slug}.stderr"
            command_cwd = app / item.cwd
            wall_start = time.monotonic()
            started = datetime.now(timezone.utc).isoformat()
            try:
                result = subprocess.run(
                    list(item.argv),
                    cwd=command_cwd,
                    env=command_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                stdout = result.stdout or b""
                stderr = result.stderr or b""
                returncode = result.returncode
            except OSError as exc:
                stdout = b""
                stderr = str(exc).encode("utf-8", errors="replace")
                returncode = 127
            duration = round(time.monotonic() - wall_start, 3)
            stdout_path.write_bytes(stdout)
            stderr_path.write_bytes(stderr)
            record = {
                "index": number,
                "name": item.name,
                "argv": list(item.argv),
                "cwd": str(command_cwd),
                "started_at_utc": started,
                "duration_seconds": duration,
                "returncode": returncode,
                "status": "PASS" if returncode == 0 else "FAIL",
                "stdout": {"path": stdout_path.name, "bytes": len(stdout), "sha256": _sha256(stdout)},
                "stderr": {"path": stderr_path.name, "bytes": len(stderr), "sha256": _sha256(stderr)},
            }
            records.append(record)
            ledger.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            ledger.flush()
            print(
                f"FOUNDATION_CHECK {number}/{len(checks)} {item.name} "
                f"status={record['status']} exit={returncode} duration={duration}s "
                f"stdout_sha256={record['stdout']['sha256']} stderr_sha256={record['stderr']['sha256']}",
                flush=True,
            )
            if returncode != 0:
                failures.append(item.name)
                if stdout:
                    print(f"--- {item.name} stdout (tail) ---\n{_tail(stdout)}", flush=True)
                if stderr:
                    print(f"--- {item.name} stderr (tail) ---\n{_tail(stderr)}", flush=True)

    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        head_sha = _decode(head.stdout).strip() if head.returncode == 0 else None
    except OSError:
        head_sha = None
    summary = {
        "schema_version": "foundation-ci-evidence-r1",
        "repository_head": head_sha,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks_total": len(records),
        "checks_passed": sum(row["returncode"] == 0 for row in records),
        "checks_failed": len(failures),
        "failed_checks": failures,
        "status": "PASS" if not failures else "FAIL",
        "command_ledger": ledger_path.name,
        "command_ledger_sha256": _sha256(ledger_path.read_bytes()),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"FOUNDATION_CI_RESULT={summary['status']} checks={summary['checks_passed']}/{summary['checks_total']} "
        f"failed={summary['checks_failed']} evidence_dir={output}",
        flush=True,
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    summary = execute_checks(foundation_checks(), evidence_dir=args.evidence_dir or default_evidence_dir())
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
