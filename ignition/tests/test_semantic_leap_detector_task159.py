import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/research/semantic-leap-detector-v2-2026-09-07'

class Task159SemanticLeapDetectorTests(unittest.TestCase):
    def test_deterministic_blind_runs_and_migration_controls(self):
        subprocess.run(['python3', str(ROOT/'tools/research/task159_semantic_leap_detector.py')], check=True)
        one=(OUT/'v2-score-run-1.jsonl').read_bytes(); two=(OUT/'v2-score-run-2.jsonl').read_bytes()
        self.assertEqual(one,two)
        scores={r['event_id']:r for r in map(json.loads,one.decode().splitlines())}
        self.assertEqual(scores['N02_INCREMENTAL_REGISTRY']['verdict'],'NON_LEAP')
        self.assertEqual(scores['N03_CANONICAL_PROTOCOL_MIGRATION']['verdict'],'NON_LEAP')
        self.assertEqual(scores['P03_DUAL_CHANNEL_BOOTSTRAP']['verdict'],'LEAP')
