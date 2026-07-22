#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run
CONFIG=json.loads("{\"task_id\": \"Q44-I1\", \"capability\": \"coaching_commitment_subcapability\", \"parent_id\": \"Q43-I1\", \"parent_head\": \"e5181c83efba68f847b55e13c7b5a1ee1fd6888e\", \"fields\": [\"user_declared_goal\", \"informed_commitment\", \"plan_checkpoints\", \"deviations\", \"support_options\", \"revise_pause_stop\", \"non_manipulation_constraint\", \"multi_perspective_narrative\", \"autonomy_consent\", \"outcome_process_separation\", \"escalation\", \"claim_ceiling\"], \"rules\": [\"goal_user_declared\", \"commitment_informed\", \"consent_reversible\", \"no_goal_substitution\", \"no_shame_pressure\", \"multiple_narratives_preserved\", \"process_outcome_separate\", \"support_not_control\", \"escalation_boundary_enforced\"], \"schema\": \"schemas/coaching/coaching_commitment_subcapability-contract.schema.json\", \"forbidden_claims\": [\"no manipulative persuasion\", \"no hidden goal substitution\", \"no shame-driven compliance\", \"outcome does not prove intervention legitimacy\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
if __name__=="__main__": sys.exit(run(CONFIG))
