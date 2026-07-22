#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run
CONFIG=json.loads("{\"task_id\": \"Q41-I1\", \"capability\": \"world_feedback_anomaly\", \"parent_id\": \"SCIENTIFIC-METACOGNITION-I1\", \"parent_head\": \"25f937ea8d53b4b14f31fc9c8779995f3c516bac\", \"fields\": [\"world_feedback_anomaly\", \"recurrence_window\", \"residual_failure_aggregation\", \"expected_observed_divergence\", \"model_repair_budget\", \"governance_decision\", \"escalation_authority\", \"stop_rollback\", \"q39_update\", \"metacognition_update\", \"claim_ceiling\"], \"rules\": [\"anomaly_not_hidden_system\", \"recurrence_required\", \"threshold_declared\", \"single_deviation_no_rebuild\", \"repair_budget_bounded\", \"authority_required\", \"stop_rollback_present\", \"failure_sampling_balanced\", \"q39_updated\", \"metacognition_updated\"], \"schema\": \"schemas/anomaly/world_feedback_anomaly-contract.schema.json\", \"forbidden_claims\": [\"single residual is not a hidden system\", \"anomaly is not causal proof\", \"no threshold-free escalation\", \"no selective failure sampling\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
if __name__=="__main__": sys.exit(run(CONFIG))
