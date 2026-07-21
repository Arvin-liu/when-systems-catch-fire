#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run
CONFIG=json.loads("{\"task_id\": \"Q42-I1\", \"capability\": \"counterfactual_unrealized_path\", \"parent_id\": \"D2-I1\", \"parent_head\": \"f638442a2ac28f2e5b4d3911e19c074c2ee003cb\", \"fields\": [\"counterfactuals\", \"alternative_decompositions\", \"unrealized_paths\", \"speculative_narratives\", \"intervention_differences\", \"identifiability_status\", \"observable_portion\", \"unobservable_portion\", \"evidence\", \"claim_ceiling\"], \"rules\": [\"types_separated\", \"identifiability_gate_required\", \"unobservable_not_promoted\", \"evidence_required\", \"intervention_difference_explicit\", \"speculation_labeled\", \"no_if_then_causal_upgrade\", \"claim_ceiling_preserved\"], \"schema\": \"schemas/counterfactual/counterfactual_unrealized_path-contract.schema.json\", \"forbidden_claims\": [\"if-then story is not causal fact\", \"unobservable portion remains unobservable\", \"alternative decomposition is not counterfactual proof\", \"no external intervention\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
if __name__=="__main__": sys.exit(run(CONFIG))
