from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / 'tools/operations'))
import plan_ignition_operation_run as planner  # noqa: E402

TOOL_ID = 'maintenance.audit_execution_state_lineage'
PROFILE_PATH = IGNITION_ROOT / 'data/operations/toolbox-execution-state-lineage-route-profile-r0.json'
EVIDENCE_PATH = IGNITION_ROOT / 'data/operations/toolbox-execution-state-lineage-route-evidence-r0.json'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ExecutionStateLineageRoutingTests(unittest.TestCase):
    def test_default_off_and_explicit_allowlist_only_proposes_read_only_tool(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding='utf-8'))
        default = planner.plan_tool_route(profile)
        explicit = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])

        self.assertEqual(default['decision'], 'INCOMPLETE')
        self.assertEqual(default['selected_tools'], [])
        self.assertEqual(explicit['decision'], 'COMPLETE')
        self.assertEqual([row['tool_id'] for row in explicit['selected_tools']], [TOOL_ID])
        self.assertFalse(explicit['execution_authorized'])
        self.assertFalse(explicit['selected_tools'][0]['permissions']['network'])
        self.assertEqual(explicit['selected_tools'][0]['permissions']['write_paths'], [])
        self.assertFalse(explicit['selected_tools'][0]['permissions']['external_actions'])

        trials = {row['scenario']: row for row in evidence['route_trials']}
        self.assertEqual(trials['default_off']['decision'], default['decision'])
        self.assertEqual(trials['explicit_allowlist']['decision'], explicit['decision'])
        self.assertEqual(trials['explicit_allowlist']['selected_tool_ids'], [TOOL_ID])
        self.assertFalse(trials['explicit_allowlist']['candidate_invoked'])
        self.assertFalse(trials['explicit_allowlist']['execution_authorized'])
        self.assertEqual(evidence['task_profile_sha256'], sha256(PROFILE_PATH.read_bytes()))
        self.assertEqual(evidence['candidate_catalog_git_blob_sha1'], planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()))
        self.assertEqual(evidence['planner_source_sha256'], sha256(Path(planner.__file__).read_bytes()))
        self.assertTrue(evidence['catalog_replay']['all_expected_decisions_reproduced'])


if __name__ == '__main__':
    unittest.main()
