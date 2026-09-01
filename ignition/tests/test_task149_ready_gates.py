import unittest

from tools.validate_task149_ready_gates import generated_front_door_change_only, validate


class Task149ReadyGateTests(unittest.TestCase):
    def test_all_additional_ready_gates_pass(self):
        self.assertEqual(validate(), [])

    def test_only_generated_current_snapshot_block_may_refresh(self):
        before = "intro\n<!-- CURRENT-SNAPSHOT:BEGIN profile=human schema=current-snapshot-r1 -->\nold\n<!-- CURRENT-SNAPSHOT:END -->\n"
        after = "intro\n<!-- CURRENT-SNAPSHOT:BEGIN profile=human schema=current-snapshot-r1 -->\nnew\n<!-- CURRENT-SNAPSHOT:END -->\n"
        self.assertTrue(generated_front_door_change_only(before, after))
        self.assertFalse(generated_front_door_change_only("changed\n" + before, after))


if __name__ == "__main__":
    unittest.main()
