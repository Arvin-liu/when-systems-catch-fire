#!/usr/bin/env python3
import json, subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
VALIDATOR=ROOT/"tools/failure/validate_failure_lineage_gate.py"
FIXTURES=ROOT/"data/failure/fixtures"
PILOT=ROOT/"data/failure/pilot-q39-failure-lineage.json"
EXPECTED={1:0,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:11,12:12,13:13,14:14,15:4,16:5,17:6,18:7,19:8,20:9,21:10,22:11,23:12,24:13}

def run(path): return subprocess.run([sys.executable,str(VALIDATOR),"--bundle",str(path)],capture_output=True,text=True)

class FailureLineageGateTests(unittest.TestCase):
    def test_real_cli_attack_matrix(self):
        paths=sorted(FIXTURES.glob("*.json")); self.assertEqual(len(paths),24)
        for p in paths:
            n=int(p.name.split("-",1)[0]); r=run(p)
            self.assertEqual(r.returncode,EXPECTED[n],f"{p.name}: {r.stdout} {r.stderr}")
    def test_pilot_passes(self):
        r=run(PILOT); self.assertEqual(r.returncode,0,r.stdout)
    def test_chain_is_append_only_and_complete(self):
        b=json.loads(PILOT.read_text()); self.assertEqual(b["declared_event_count"],len(b["events"])); self.assertTrue(all(not e["overwrites_event"] for e in b["events"]))
    def test_every_failure_changes_a_plan(self):
        b=json.loads(PILOT.read_text()); targets={t["target_id"] for t in b["propagation_targets"] if t["applied"]}
        for e in b["events"]:
            if e["event_type"]=="FAILURE": self.assertTrue(set(e["propagation_target_ids"]) & targets)

if __name__=="__main__": unittest.main()
