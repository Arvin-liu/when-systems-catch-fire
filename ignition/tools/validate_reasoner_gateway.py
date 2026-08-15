"""Offline validator for the provider-neutral Reasoner Gateway R1."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.transport import (
    AdversarialGatewayAdapter,
    GatewayError,
    GatewayRequest,
    ReasonerGateway,
    ScriptedGatewayAdapter,
)


def main() -> int:
    request = GatewayRequest(
        phase="FRAME", run_id="run-gateway-validator", goal_summary="bounded frame",
        environment_summary="offline workspace", capability_catalog=("read.files",),
        context_capsule=("bounded context capsule",), available_packs=("maintenance.repository",),
    )
    response = ReasonerGateway(ScriptedGatewayAdapter(())).request(request)
    assert response.request_digest == request.request_digest
    for mode in ("permission_expansion", "forged_completion", "malformed_json", "oversized_output", "crash"):
        try:
            ReasonerGateway(AdversarialGatewayAdapter(mode)).request(request)
        except GatewayError:
            continue
        raise AssertionError(f"adversarial Gateway mode was not rejected: {mode}")
    print("REASONER_GATEWAY_R1_VALIDATOR=PASS")
    print("SCHEMA_NEGOTIATION=reasoner-gateway-r1")
    print("REQUEST_DIGEST=DETERMINISTIC")
    print("ADVERSARIAL_BOUNDARY=FAIL_CLOSED")
    print("EXECUTION_AUTHORITY=NONE_REASONER_PROPOSALS_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
