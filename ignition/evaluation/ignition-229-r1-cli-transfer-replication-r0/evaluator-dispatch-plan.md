# Evaluator dispatch plan

This plan implements only the frozen Task229 evaluator procedure. It adds no scoring criteria.

1. Wait until all 18 successor sessions have terminal records. Validate the exact session-to-prompt mapping, prompt hashes, fresh PID/thread identities, response schema, no historical Attempt-1 response use, and fixed reference-route traces using the copied `source-prereg/tools/recompute.py` logic and fixed input map.
2. Freeze raw successor response bytes and hashes before opening any target scoring criteria. Record the coordinator's historical target exposure; do not pass that history to evaluators.
3. Only after the dataset freeze, bind the exact Task225 target cases/criteria and Task227 transfer-evaluator criteria through their frozen historical hashes. Do not reconstruct missing materials.
4. Freeze a deterministic packet builder that implements only the copied sanitization procedure. Require zero leakage under the original scan rules.
5. Generate two independent packet orders with new seeds recorded before evaluator launch. Freeze exact evaluator prompts, schemas, and hashes.
6. Dispatch evaluator A and B through the same unchanged H1 dispatcher to distinct fresh ephemeral CLI processes, requesting `gpt-6-astra` / `medium`, with no tools or external sources. Do not reconcile outputs and do not launch a third evaluator.
7. Run the original copied recomputation twice from immutable inputs and require byte-identical aggregates. Report interface execution, reference target compatibility, and incremental policy effect separately.

No target criteria or evaluator source content is read before the 18-response dataset freeze.
