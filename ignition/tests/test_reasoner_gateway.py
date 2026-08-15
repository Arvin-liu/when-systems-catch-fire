from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest

from agent_runtime.actions import ApprovalClass
from agent_runtime.r1_runtime import AgentRuntimeR1
from agent_runtime.transport import (
    AdversarialGatewayAdapter,
    GatewayError,
    GatewayRequest,
    GATEWAY_SCHEMA_VERSION,
    ReasonerGateway,
    ScriptedGatewayAdapter,
    SubprocessReasonerAdapter,
)
from tests.test_supervisor import packet
from tests.test_agent_runtime_r1 import spec as r1_spec


class ReasonerGatewayTests(unittest.TestCase):
    def request(self, run_id: str = "run-gateway") -> GatewayRequest:
        return GatewayRequest(
            phase="PLAN", run_id=run_id, goal_summary="make one bounded proposal",
            environment_summary="offline local workspace", capability_catalog=("write.files",),
            context_capsule=("bounded context capsule",), available_packs=("maintenance.repository",),
        )

    def test_scripted_gateway_is_digest_bound_and_read_only(self) -> None:
        p = packet("run-gateway", "action-gateway", "gateway.txt")
        gateway = ReasonerGateway(ScriptedGatewayAdapter((p,)))
        request = self.request()
        response = gateway.request(request)
        self.assertEqual(response.schema_version, GATEWAY_SCHEMA_VERSION)
        self.assertEqual(response.request_digest, request.request_digest)
        self.assertEqual(response.packets[0].action_id, "action-gateway")
        self.assertNotIn("execute", response.to_dict())
        self.assertNotIn("permission", response.to_dict())

    def test_schema_context_digest_and_authority_attacks_fail_closed(self) -> None:
        with self.assertRaises(GatewayError):
            GatewayRequest(
                phase="PLAN", run_id="run-gateway", goal_summary="bounded", environment_summary="offline",
                capability_catalog=("write.files",), context_capsule=("private model reasoning",),
            )
        with self.assertRaises(GatewayError):
            ReasonerGateway(AdversarialGatewayAdapter("permission_expansion")).request(self.request())
        with self.assertRaises(GatewayError):
            ReasonerGateway(AdversarialGatewayAdapter("forged_completion")).request(self.request())
        with self.assertRaises(GatewayError):
            ReasonerGateway(AdversarialGatewayAdapter("malformed_json")).request(self.request())

    def test_subprocess_reference_adapter_covers_timeout_crash_malformed_and_oversized(self) -> None:
        script = (
            "print(__import__('json').dumps((lambda r:{'schema_version':r['schema_version'],"
            "'request_digest':r['request_digest'],'phase':r['phase'],'status':'STOP',"
            "'frame_summary':None,'packets':[],'block_summary':'bounded stop',"
            "'requested_capabilities':[],'requested_packs':[],'authority_claims':[],'terminal_claim':None,"
            "'telemetry':{'adapter':'test'}})(__import__('json').loads(__import__('sys').stdin.readline()))))"
        )
        response = ReasonerGateway(SubprocessReasonerAdapter((sys.executable, "-c", script))).request(self.request())
        self.assertEqual(response.status, "STOP")
        with self.assertRaisesRegex(GatewayError, "MALFORMED_OUTPUT"):
            ReasonerGateway(SubprocessReasonerAdapter((sys.executable, "-c", "print('not-json')"))).request(self.request())
        with self.assertRaisesRegex(GatewayError, "OVERSIZED_OUTPUT"):
            ReasonerGateway(SubprocessReasonerAdapter((sys.executable, "-c", "print('x' * 1000)"), max_output_bytes=20)).request(self.request())
        with self.assertRaisesRegex(GatewayError, "CRASH"):
            ReasonerGateway(SubprocessReasonerAdapter((sys.executable, "-c", "raise SystemExit(7)"))).request(self.request())
        with self.assertRaisesRegex(GatewayError, "TIMEOUT"):
            ReasonerGateway(SubprocessReasonerAdapter((sys.executable, "-c", "__import__('time').sleep(1)"), timeout_seconds=0.02)).request(self.request())

    def test_gateway_scripted_adapter_drives_existing_r1_without_execution_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gateway-r1-") as temp:
            root = Path(temp)
            p = packet("run-gateway-r1", "action-gateway-r1", "gateway-r1.txt")
            run_spec = r1_spec(root, (p,))
            run_spec = replace(run_spec, reasoner={"type": "gateway-scripted", "available_packs": ["maintenance.repository"]})
            state = AgentRuntimeR1(root / "run").start(run_spec)
            self.assertEqual(state["terminal"]["state"], "COMPLETED_VALIDATED")
            self.assertEqual((root / "gateway-r1.txt").read_text(encoding="utf-8"), "content-action-gateway-r1\n")
            self.assertNotIn("SUCCESS", json.dumps(state))


if __name__ == "__main__":
    unittest.main()
