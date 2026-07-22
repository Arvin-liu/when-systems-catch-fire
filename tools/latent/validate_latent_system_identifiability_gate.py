#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.governance.structured_capability_gate import run
CONFIG=json.loads("{\"task_id\": \"F15-D1-I1\", \"capability\": \"latent_system_identifiability\", \"parent_id\": \"Q41-I1\", \"parent_head\": \"e92e7d3eadbb67da288077052f635e3c052bd3a1\", \"fields\": [\"latent_system_candidate\", \"cross_system_ancestor_graph\", \"missing_system_search_plan\", \"identifiability_gate\", \"observational_signature\", \"equivalent_decompositions\", \"distinguishing_evidence_request\", \"candidate_status\", \"contradictions\", \"unsupported_elements\", \"claim_ceiling\"], \"rules\": [\"residual_not_entity\", \"pattern_not_common_cause\", \"equivalent_decompositions_preserved\", \"distinguishing_evidence_required\", \"non_identifiable_stays_unresolved\", \"contradictions_preserved\", \"unsupported_not_promoted\", \"claim_ceiling_preserved\"], \"schema\": \"schemas/latent/latent_system_identifiability-contract.schema.json\", \"forbidden_claims\": [\"residual is not a latent entity\", \"shared pattern is not a common cause\", \"non-identifiable decomposition remains unresolved\", \"no Q45+ numbering\", \"universal truth\", \"causal proof established\", \"ecosystem deployed\"]}")
if __name__=="__main__": sys.exit(run(CONFIG))
