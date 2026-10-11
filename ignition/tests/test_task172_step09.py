import json
import unittest
from pathlib import Path

from tools.research.validate_task172_step09 import validate


ROOT = Path(__file__).resolve().parents[1]


class Task172Step09Test(unittest.TestCase):
    def test_incremental_field_corpus_is_valid(self):
        validate(ROOT)

    def test_global_physical_records_are_deduplicated(self):
        corpus = ROOT / "data/external-research/unesco-general-knowledge-r1/step09-corpus"
        path = corpus / "physical-records.jsonl"
        rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        ids = [json.loads(line)["physical_record_id"] for line in rows]
        manifest = json.loads((corpus / "corpus-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), manifest["physical_record_count"])
        self.assertGreaterEqual(len(ids), 48)


if __name__ == "__main__":
    unittest.main()
