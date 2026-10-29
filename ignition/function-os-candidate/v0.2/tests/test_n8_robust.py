"""121Q6 Step 014: N8 ComposerRouter robust tests."""
import unittest

from function_os.n8_composer_router import N8ComposerRouter

ART_A = {"function_id": "FN-20260715-0001", "artifact_id": "ART-FN-20260715-0001-1",
         "payload": {"function_id": "FN-20260715-0001", "entrypoint": "add"}}
# candidate keyed only by payload.function_id (no top-level function_id)
ART_B_PAYLOAD_ONLY = {"artifact_id": "ART-FN-20260715-0002-1",
                      "payload": {"function_id": "FN-20260715-0002", "entrypoint": "sub"}}


class TestN8Positive(unittest.TestCase):
    def setUp(self):
        self.r = N8ComposerRouter()

    def test_plan_ok(self):
        task = {"task_id": "T1", "required_functions": [{"function_id": "FN-20260715-0001"}]}
        plan = self.r.plan(task, [ART_A])
        self.assertEqual(plan['status'], 'OK')
        self.assertEqual(plan['steps'][0]['status'], 'PLANNED')
        self.assertEqual(plan['steps'][0]['artifact_id'], 'ART-FN-20260715-0001-1')

    def test_candidate_keyed_by_payload_function_id(self):
        # regression: candidate without top-level function_id must still resolve via payload
        task = {"task_id": "T2", "required_functions": [{"function_id": "FN-20260715-0002"}]}
        plan = self.r.plan(task, [ART_B_PAYLOAD_ONLY])
        self.assertEqual(plan['status'], 'OK')
        self.assertEqual(plan['steps'][0]['function_id'], 'FN-20260715-0002')

    def test_inputs_from_and_on_failure_propagated(self):
        task = {"task_id": "T3", "required_functions": [
            {"function_id": "FN-20260715-0001", "inputs_from": "prev_output", "on_failure": "CONTINUE"}]}
        plan = self.r.plan(task, [ART_A])
        step = plan['steps'][0]
        self.assertEqual(step['inputs_from'], 'prev_output')
        self.assertEqual(step['on_failure'], 'CONTINUE')

    def test_compose_sequential(self):
        p1 = self.r.plan({"task_id": "T1", "required_functions": [{"function_id": "FN-20260715-0001"}]}, [ART_A])
        p2 = self.r.plan({"task_id": "T2", "required_functions": [{"function_id": "FN-20260715-0002"}]}, [ART_B_PAYLOAD_ONLY])
        comp = self.r.compose_sequential([p1, p2])
        self.assertEqual(comp['plan_count'], 2)
        self.assertEqual(len(comp['steps']), 2)

    def test_capabilities_excludes_weight_space(self):
        caps = self.r.capabilities
        self.assertIn("weight-space algebra", caps['excluded'])
        self.assertFalse(caps['deferred_composition'])


class TestN8Negative(unittest.TestCase):
    def setUp(self):
        self.r = N8ComposerRouter()

    def test_function_not_found_skipped(self):
        task = {"task_id": "T4", "required_functions": [{"function_id": "FN-19990101-9999"}]}
        plan = self.r.plan(task, [ART_A])
        self.assertEqual(plan['status'], 'PARTIAL')
        self.assertEqual(plan['steps'][0]['status'], 'SKIPPED')
        self.assertTrue(any(e['issue'] == 'FUNCTION_NOT_FOUND' for e in plan['errors']))

    def test_empty_candidates(self):
        task = {"task_id": "T5", "required_functions": [{"function_id": "FN-20260715-0001"}]}
        plan = self.r.plan(task, [])
        self.assertEqual(plan['status'], 'PARTIAL')
        self.assertEqual(len(plan['errors']), 1)

    def test_compose_sequential_with_errors(self):
        p_ok = self.r.plan({"task_id": "T1", "required_functions": [{"function_id": "FN-20260715-0001"}]}, [ART_A])
        p_bad = self.r.plan({"task_id": "T6", "required_functions": [{"function_id": "FN-19990101-9999"}]}, [ART_A])
        comp = self.r.compose_sequential([p_ok, p_bad])
        self.assertEqual(comp['status'], 'PARTIAL')
        self.assertEqual(len(comp['errors']), 1)


if __name__ == '__main__':
    unittest.main()
