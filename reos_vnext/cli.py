"""Small command line surface for operating one R1 case document."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .kernel import (
    add_obligation,
    load_case,
    new_case,
    parse_json,
    prepare_handoff,
    record_artifact,
    record_claim_candidate,
    record_evidence_request,
    record_review,
    request_review,
    save_case,
    serialize_case,
    status_snapshot,
)
from .validation import ContractError, canonical_json, validate_case


def _json_file(path: str) -> Any:
    return parse_json(Path(path).read_text(encoding="utf-8"))


def _write_output(path: str, value: Any) -> None:
    Path(path).write_text(canonical_json(value) + "\n", encoding="utf-8")


def _case_mutation(args: argparse.Namespace, mutator: Any) -> int:
    document = load_case(args.case)
    updated = mutator(document, _json_file(args.record))
    save_case(args.case, updated)
    print(canonical_json(status_snapshot(updated)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m reos_vnext")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create one validated case document")
    init.add_argument("--case-id", required=True)
    init.add_argument("--mode", default="REOS_LIGHT")
    init.add_argument("--activation-reason", required=True)
    init.add_argument("--observed-need", action="append", default=[])
    init.add_argument("--simpler-baseline", required=True)
    init.add_argument("--unnecessary-module", action="append", default=[])
    init.add_argument("--preregistration-ref", required=True, help="external preregistration reference; full text stays outside the case")
    init.add_argument("--preregistration-digest", required=True, help="sha256 of the external preregistration")
    init.add_argument("--frozen-validation-summary", required=True, help="JSON file containing only the compact frozen validation summary")
    init.add_argument("--budget-json", default=None)
    init.add_argument("--stop-condition", action="append", default=[])
    init.add_argument("--owner-boundary", default="GPT_OWNER_REVIEW_ONLY")
    init.add_argument("--output", required=True)

    for name, help_text in (("validate", "validate a case"), ("status", "show deterministic case status")):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("case")

    for name, help_text in (
        ("add-obligation", "append an obligation"),
        ("record-artifact", "append a thin artifact reference"),
        ("record-evidence-request", "append an evidence retrieval request"),
        ("record-claim", "append a noncanonical claim annotation"),
        ("request-review", "append a named review request"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("case")
        command.add_argument("--record", required=True, help="JSON record file")

    review = sub.add_parser("record-review", help="record a review decision and optional repair obligations")
    review.add_argument("case")
    review.add_argument("--record", required=True, help="JSON object with decision and optional repair_obligations")

    handoff = sub.add_parser("handoff", help="emit a deterministic typed handoff projection")
    handoff.add_argument("case")
    handoff.add_argument("--bundle-id", required=True)
    handoff.add_argument("--bundle-type", required=True)
    handoff.add_argument("--receiving-authority", required=True)
    handoff.add_argument("--object-ref", action="append", default=[])
    handoff.add_argument("--allowed-claim", action="append", default=[])
    handoff.add_argument("--noncanonical-status", required=True)
    handoff.add_argument("--scope", required=True)
    handoff.add_argument("--prohibited-inference", action="append", default=[])
    handoff.add_argument("--residual", action="append", default=[])
    handoff.add_argument("--no-independent-review", action="store_true")
    handoff.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            budget = _json_file(args.budget_json) if args.budget_json else {"max_minutes": 0, "method": "operator-accounted"}
            document = new_case(
                case_id=args.case_id,
                mode=args.mode,
                activation_reason=args.activation_reason,
                observed_need=args.observed_need,
                simpler_baseline=args.simpler_baseline,
                unnecessary_modules=args.unnecessary_module,
                preregistration_ref=args.preregistration_ref,
                preregistration_digest=args.preregistration_digest,
                frozen_validation_summary=_json_file(args.frozen_validation_summary),
                budget_contract=budget,
                stop_conditions=args.stop_condition,
                owner_boundary=args.owner_boundary,
            )
            save_case(args.output, document)
            print(canonical_json(status_snapshot(document)))
            return 0
        if args.command == "validate":
            document = load_case(args.case)
            validate_case(document)
            print(canonical_json({"valid": True, "case_id": document["case"]["case_id"]}))
            return 0
        if args.command == "status":
            print(canonical_json(status_snapshot(load_case(args.case))))
            return 0
        if args.command == "add-obligation":
            return _case_mutation(args, add_obligation)
        if args.command == "record-artifact":
            return _case_mutation(args, record_artifact)
        if args.command == "record-evidence-request":
            return _case_mutation(args, record_evidence_request)
        if args.command == "record-claim":
            return _case_mutation(args, record_claim_candidate)
        if args.command == "request-review":
            return _case_mutation(args, request_review)
        if args.command == "record-review":
            document = load_case(args.case)
            payload = _json_file(args.record)
            decision = payload.get("decision", payload)
            repairs = payload.get("repair_obligations", [])
            updated = record_review(document, decision, repairs)
            save_case(args.case, updated)
            print(canonical_json(status_snapshot(updated)))
            return 0
        if args.command == "handoff":
            bundle = prepare_handoff(
                load_case(args.case),
                bundle_id=args.bundle_id,
                bundle_type=args.bundle_type,
                receiving_authority=args.receiving_authority,
                object_refs=args.object_ref,
                allowed_claims=args.allowed_claim,
                noncanonical_status=args.noncanonical_status,
                scope=args.scope,
                prohibited_inference=args.prohibited_inference,
                residuals=args.residual,
                independent_review_required=not args.no_independent_review,
            )
            if args.output:
                _write_output(args.output, bundle)
            print(canonical_json(bundle))
            return 0
        raise AssertionError(f"unhandled command: {args.command}")
    except ContractError as exc:
        print(canonical_json({"valid": False, "errors": [issue.as_dict() for issue in exc.issues]}), file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(canonical_json({"valid": False, "error": str(exc)}), file=sys.stderr)
        return 2
