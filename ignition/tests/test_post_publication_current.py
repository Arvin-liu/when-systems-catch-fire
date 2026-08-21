from __future__ import annotations

import unittest

from tools import validate_post_publication_current as checker


class PostPublicationCurrentTests(unittest.TestCase):
    def test_pre_publication_readiness(self) -> None:
        result = checker.run_checks(post_publication=False)
        self.assertEqual(result["result"], "PASS", result["errors"])
        self.assertEqual(result["mode"], "PRE_PUBLICATION")


if __name__ == "__main__":
    unittest.main()
