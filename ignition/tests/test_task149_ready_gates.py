import unittest

from tools.validate_task149_ready_gates import validate


class Task149ReadyGateTests(unittest.TestCase):
    def test_all_additional_ready_gates_pass(self):
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
