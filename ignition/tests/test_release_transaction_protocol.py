from __future__ import annotations

import copy
import unittest

from tools import validate_release_transaction_protocol as protocol


class ReleaseTransactionProtocolTests(unittest.TestCase):
    def test_protocol_is_valid_and_ordered(self) -> None:
        self.assertEqual(protocol.validate(), [])
        document = protocol.load_json(protocol.PROTOCOL_PATH)
        self.assertEqual([row["step_id"] for row in sorted(document["steps"], key=lambda row: row["sequence"])], protocol.EXPECTED_STEPS)

    def test_receipt_witness_cannot_create_formal_commit(self) -> None:
        document = copy.deepcopy(protocol.load_json(protocol.PROTOCOL_PATH))
        next(row for row in document["steps"] if row["step_id"] == "receipt-1111-witness")["creates_formal_commit"] = True
        self.assertTrue(any("must not create a formal commit" in error for error in protocol.validate(document)))

    def test_force_push_is_rejected(self) -> None:
        document = copy.deepcopy(protocol.load_json(protocol.PROTOCOL_PATH))
        document["main_mutation_policy"]["force_push"] = True
        self.assertTrue(protocol.validate(document))

    def test_step_order_mutation_is_rejected(self) -> None:
        document = copy.deepcopy(protocol.load_json(protocol.PROTOCOL_PATH))
        document["steps"][0]["sequence"] = 10
        self.assertTrue(protocol.validate(document))


if __name__ == "__main__":
    unittest.main()
