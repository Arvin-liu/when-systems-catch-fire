#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run
CONFIG=json.loads("{\"task_id\": \"Q43-I1\", \"capability\": \"graded_intervention_escalation\", \"parent_id\": \"Q42-I1\", \"parent_head\": \"98998bb1e3db67230954c1436d8effbcb87027af\", \"fields\": [\"action_risk_class\", \"reversibility\", \"evidence_grade\", \"authority\", \"expertise_requirement\", \"automatic_repository_local_action\", \"user_confirmation_required\", \"expert_escalation\", \"institutional_approval\", \"prohibited_action\", \"request_only_external_action\", \"stop_rollback_result_return\", \"claim_ceiling\"], \"rules\": [\"risk_class_required\", \"reversibility_required\", \"evidence_grade_required\", \"authority_required\", \"expertise_boundary_enforced\", \"automatic_only_repository_local\", \"confirmation_for_external\", \"high_risk_request_only\", \"prohibited_never_executed\", \"stop_rollback_return_present\"], \"schema\": \"schemas/escalation/graded_intervention_escalation-contract.schema.json\", \"forbidden_claims\": [\"no legal action\", \"no medical action\", \"no financial action\", \"no safety-critical external action\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
if __name__=="__main__": sys.exit(run(CONFIG))
