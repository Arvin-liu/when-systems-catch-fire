"""Round 6 — bounded sleep-timing pilot (TASK.md Round 6).

The deep-research capability's adapters are OFFLINE-SAFE by design (Rounds 1-3)
and no live public-web tool is wired into the runtime in this sandbox, so the
precondition "required tool access is available" (TASK.md Round 6) is NOT met.
The pilot therefore must NOT attempt unattended public-web work; instead it
drives the frozen question through the real Round 2 SerialQueue + Round 3
EpisodeController + Round 4 SufficiencyEvaluator interfaces, preserves a full
machine trace, and terminates honestly as BLOCKED_WITH_EVIDENCE with the exact
evidence. This test guards that contract and the assembled-pipeline stability.

Run:  python3 tests/test_deep_research_round6.py
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "tools") not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT / "tools"))

import tempfile  # noqa: E402

from deep_research import run_round6_pilot as P  # noqa: E402


class Round6PilotTests(unittest.TestCase):
    def test_pilot_runs_through_real_interfaces_and_blocks_offline(self):
        with tempfile.TemporaryDirectory() as td:
            report = P.run_pilot(Path(td))

            # --- honest terminal outcome ---------------------------------
            self.assertEqual(report["pilot_outcome"], "BLOCKED_WITH_EVIDENCE",
                             "offline sandbox must end as BLOCKED_WITH_EVIDENCE")
            self.assertEqual(report["episode_terminal_state"], "BLOCKED")

            # --- full machine trace preserved ----------------------------
            ep_path = Path(report["machine_trace_refs"]["episode"])
            q_path = Path(report["machine_trace_refs"]["queue"])
            self.assertTrue(ep_path.exists(), "episode machine trace missing")
            self.assertTrue(q_path.exists(), "queue machine trace missing")

            ep = json.loads(ep_path.read_text(encoding="utf-8"))
            self.assertEqual(ep["state"], "BLOCKED")
            self.assertTrue(ep.get("blockers"), "blocker must be recorded on episode")
            self.assertGreaterEqual(len(ep.get("observations", [])), 1)
            self.assertGreaterEqual(len(ep.get("source_identities", [])), 1)
            # the opened source is NONE access (offline fail-closed) -> blocker
            none = [s for s in ep["source_identities"]
                     if s.get("access_level") == "NONE"]
            self.assertTrue(none, "expected a NONE-access source (offline)")

            # --- exact evidence documented (not a vague stop) ------------
            ev = "\n".join(report["evidence"])
            self.assertIn("OFFLINE-SAFE", ev)
            self.assertIn("no live public-web tool", ev)
            self.assertIn("required tool access", ev)

            # --- the in-episode evaluator corroborates the blocker -------
            self.assertEqual(report["in_episode_decision"], "BLOCKED_WITH_EVIDENCE")

            # --- resume path for Round 7 / Codex is specified -----------
            self.assertTrue(report["resume_commands_for_round7_codex"])

    def test_frozen_question_is_exact_taskmd_text(self):
        self.assertIn("7-8 hours of sleep", P.FROZEN_QUESTION)
        self.assertIn("delayed circadian phase", P.FROZEN_QUESTION)
        self.assertIn("separately from sleep duration", P.FROZEN_QUESTION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
