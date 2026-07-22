#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run
CONFIG=json.loads("{\"task_id\": \"D2-I1\", \"capability\": \"multi_history_world_projection\", \"parent_id\": \"F15-D1-I1\", \"parent_head\": \"f0f7d7ff9dda620d59ad1dd1b504bcd503fe5c09\", \"fields\": [\"world_candidates\", \"divergence_point\", \"shared_evidence\", \"branch_specific_assumptions\", \"indistinguishable_set\", \"falsifiers\", \"justified_weights\", \"unresolved_paths\", \"narrative_ceiling\", \"claim_ceiling\"], \"rules\": [\"every_world_evidence_bound\", \"no_forced_unique_story\", \"indistinguishable_not_ranked_fact\", \"weights_need_justification\", \"possibility_not_probability\", \"falsifier_required\", \"unresolved_paths_preserved\", \"narrative_ceiling_preserved\"], \"schema\": \"schemas/multihistory/multi_history_world_projection-contract.schema.json\", \"forbidden_claims\": [\"generated possibility is not real probability\", \"indistinguishable paths are not ranked facts\", \"no evidence-free story\", \"no forced unique narrative\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
if __name__=="__main__": sys.exit(run(CONFIG))
