TASK: Author a deterministic packet builder.

You are a fresh isolated CLI process. You have only the following synthetic-only authoring package in this message. Do not use shell/tools, web, external sources, filesystem reads, or network. Do not infer or invent scientific criteria. Do not mention hidden conditions or map associations. Return only one complete Python source file, in exactly one fenced `python` code block, with no prose outside it. The file must be named `builder.py` by the receiving process.

Implement the exact command-line interface and frozen contract in the allowed package files. Use Python standard library only. Do not import any R1 artifact or use a helper outside the package. The code must be deterministic, fail-closed, avoid logging packet content, and satisfy every synthetic fixture when its placeholders are expanded with the flat `literal_tokens` list from the included deny-token manifest. Do not include test code or third-party dependencies.

Allowed authoring package begins below. Every file is explicitly delimited and byte-hashed; no other input is authorized.

<<<BEGIN_ALLOWED_FILE path="blind-evaluation-schema.json" byte_length="754" sha256="3c6e27ce7b8393314c7b5c76e7a9611d023ddce3ecce69ac626f4b071e019cd4">>>
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "task229-blind-evaluation-r0",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "rows"],
  "properties": {
    "schema_version": {"const": "task229-blind-evaluation-r0"},
    "rows": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["response_id", "case_id", "success", "criterion_reference"],
        "properties": {
          "response_id": {"type": "string", "minLength": 1},
          "case_id": {"enum": ["A", "B", "C"]},
          "success": {"type": "boolean"},
          "criterion_reference": {"type": "string", "minLength": 1}
        }
      }
    }
  }
}

<<<END_ALLOWED_FILE path="blind-evaluation-schema.json">>>

<<<BEGIN_ALLOWED_FILE path="blind-key-schema.json" byte_length="671" sha256="908f5fc868f2a9bf3efc65901ffa1b88b1c3931cf741567cd545213819fdb5c4">>>
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "task229-blind-key-r0",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "items"],
  "properties": {
    "schema_version": {"const": "task229-blind-key-r0"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["response_id", "session_id", "case_id"],
        "properties": {
          "response_id": {"type": "string", "minLength": 1},
          "session_id": {"type": "string", "minLength": 1},
          "case_id": {"enum": ["A", "B", "C"]}
        }
      }
    }
  }
}

<<<END_ALLOWED_FILE path="blind-key-schema.json">>>

<<<BEGIN_ALLOWED_FILE path="checker-spec.md" byte_length="1356" sha256="5b6b3ed45aeb3298f08b9dfa1f3665786bad8c314b3c4b28965bbb3a482cb9d0">>>
# Independent R2 packet-checker contract

Implement the checker independently from the builder; do not import or call builder code. Inputs are the same source response envelope, case ID, response ID, exact case bytes, exact criteria bytes, deny-token manifest, original response schema, and candidate packet.

Independently parse the source, recursively remove its complete `route_trace` objects and only the procedure-defined metadata fields, validate the remaining envelope against the original schema, independently apply exact literal token replacement, and derive the selected response. Compare the candidate response deeply against that independently derived value. This proves that primary action, additional actions, reported values, preserved baseline action IDs, fallback, scope, rationale, and all other nonmetadata fields are unchanged except exact-token redaction. Require exact response ID/case ID; strict UTF-8 round-trip and SHA-256 equality for case/criteria bytes; canonical packet serialization; no `route_trace`; no forbidden metadata fields; and zero exact deny-token matches in the full serialized packet. Do not score, interpret, tune, or use target/condition/outcome information. Fail closed with a concise mechanical diagnostic; do not modify candidate packets. The checker must not import the builder or share its implementation.

<<<END_ALLOWED_FILE path="checker-spec.md">>>

<<<BEGIN_ALLOWED_FILE path="deny-token-manifest.json" byte_length="33893" sha256="57937333000511487958b3e3a428009820d655d8d96afc981113a4b134879cbc">>>
{
  "categories": {
    "artifact_bundle_ids": [
      "057d76eae931881a3209129528fef500aef762854beb6b5288411441bbf55b95",
      "4ee132e8d50e8805c466cb5d681aaa18c34c9f68",
      "699b66b2a67d703d3db62cec0e2ba2b7621ff43c",
      "6e661fde4c3df4ff5382fbd8d1aebc109784df27da03c73f83352a5f36ebb876",
      "961603c2cb8b6cd1aac14ff72ecd946e26828aa5",
      "IGNITION-20260930-229-R1",
      "fcdd4b742ffd0cd7860d2ea583ea39c14ee1aa11fd832c0ab4388a3c5dd97bc0"
    ],
    "condition_names": [
      "M0_ONLY",
      "M0_PLUS_E1",
      "REFERENCE_M1"
    ],
    "design_session_ids": [
      "01-e15692066dfc90306e83372151fc8512",
      "02-a84ab374f5ed0d2a73aac293f4ea1c3b",
      "03-28b15c45689f1c28734faf2458b1adf0",
      "04-14dd9dd2f0941b565d119e80f924d12c",
      "05-52523a1d4c1b32c43e5aa3664e49f84a",
      "06-6c66a1ff607e779c36d3aa14263b7d84",
      "07-7dc11c187444c4693d53c4deb2c6b512",
      "08-fbfbbf5d89215aff7320cccf536f1487",
      "09-0d0186528215b091bf3b222bae8efaa4",
      "10-038df275866cab10ff31c47d72ba4d90",
      "11-4f81a0dfe25c87d425001020e65202ca",
      "12-affb717d00a25db24e300e6ea06fe206",
      "13-1693035e68fa22be10b547271e4a28f2",
      "14-9a508fc197d549e4a9b0799354bd388d",
      "15-b10eff61ecd32a492b683dee9d898539",
      "16-bf5e2d995ca87ed74bf530e13ca99fdd",
      "17-6301b4fae5d0903958a7308be5e8c94c",
      "18-4c102afd6bdc332dee98c1864a553c43"
    ],
    "lineage_ids": [
      "L01",
      "L02",
      "L03",
      "L04",
      "L05",
      "L06"
    ],
    "policy_ids": [
      "POLICY_F01_A",
      "POLICY_F01_B",
      "POLICY_F02_A",
      "POLICY_F02_B",
      "POLICY_F03_A",
      "POLICY_F03_B"
    ],
    "repository_file_path_tokens": [
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/dispatch-receipt.json",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/last-message.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/stderr.txt",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/stdout.jsonl",
      "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/session-run-index.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/README.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/analysis-input-schema.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/blind-evaluation-schema.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/blind-key-schema.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/claim-ceiling.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/condition-manifest.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/evaluator-rubric.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/missingness-retry-rules.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/outcome-rule.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/protocol.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/response-schema.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/run/case-input-values-and-route-expectations.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/sanitization-procedure.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/session-order.json",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/session-prompt-template.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/target-opening-gate.md",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/freeze_manifest.py",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/recompute.py",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/target_opening_gate.py",
      "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/validate_preregistration.py"
    ],
    "runtime_thread_or_session_ids": [
      "01a0f43d-99cc-7412-9310-ed8dd251d4a4",
      "01a0f43e-13d0-7971-8042-d5eb49bd465c",
      "01a0f43e-8e95-7752-ae69-3c1f25fa39b5",
      "01a0f43f-7143-7222-9c26-8b784e955bcb",
      "01a0f43f-fc07-7201-9ec9-70cc872d0ab2",
      "01a0f440-6fa4-72b1-a40d-63d5fdc6eb5e",
      "01a0f440-dd29-7401-98d7-8de530acaae7",
      "01a0f441-d350-78d1-b281-f62ac7983d1d",
      "01a0f442-5e79-7db2-915e-693ddbb0ef58",
      "01a0f442-f53e-79e0-816a-7b99caf89c99",
      "01a0f443-e234-7183-b886-c90da3a85484",
      "01a0f444-6246-7141-98e6-4e364a070568",
      "01a0f444-d3c2-70c0-8306-9aa741d01439",
      "01a0f445-a0f5-7c52-bc70-839e12d09e98",
      "01a0f446-1845-75a0-ade1-ceb57eb2470d",
      "01a0f446-fae3-7a53-95ef-f9260e1536ce",
      "01a0f447-7ad3-7c90-8f3c-d2a90f9a03e1",
      "01a0f448-6415-7dd2-9b57-b83eee6cd269"
    ],
    "source_locator_tokens": [
      "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY01/m0.md",
      "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY01/revision-evidence-e1.md",
      "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY02/m0.md",
      "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY02/revision-evidence-e1.md",
      "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY03/m0.md",
      "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY03/revision-evidence-e1.md",
      "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F01_A.json",
      "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F01_B.json",
      "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F02_A.json",
      "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F02_B.json",
      "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F03_A.json",
      "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F03_B.json"
    ]
  },
  "exclusions": {
    "condition_to_outcome_results_included": false,
    "evaluator_scores_included": false,
    "r1_response_text_included": false,
    "target_case_content_included": false,
    "target_success_failure_labels_included": false
  },
  "experiment_id": "IGNITION-20261001-229-R2",
  "extraction": "mechanical extraction of distinct metadata tokens only; no pairwise condition-lineage mapping emitted",
  "literal_tokens": [
    "01-e15692066dfc90306e83372151fc8512",
    "01a0f43d-99cc-7412-9310-ed8dd251d4a4",
    "01a0f43e-13d0-7971-8042-d5eb49bd465c",
    "01a0f43e-8e95-7752-ae69-3c1f25fa39b5",
    "01a0f43f-7143-7222-9c26-8b784e955bcb",
    "01a0f43f-fc07-7201-9ec9-70cc872d0ab2",
    "01a0f440-6fa4-72b1-a40d-63d5fdc6eb5e",
    "01a0f440-dd29-7401-98d7-8de530acaae7",
    "01a0f441-d350-78d1-b281-f62ac7983d1d",
    "01a0f442-5e79-7db2-915e-693ddbb0ef58",
    "01a0f442-f53e-79e0-816a-7b99caf89c99",
    "01a0f443-e234-7183-b886-c90da3a85484",
    "01a0f444-6246-7141-98e6-4e364a070568",
    "01a0f444-d3c2-70c0-8306-9aa741d01439",
    "01a0f445-a0f5-7c52-bc70-839e12d09e98",
    "01a0f446-1845-75a0-ade1-ceb57eb2470d",
    "01a0f446-fae3-7a53-95ef-f9260e1536ce",
    "01a0f447-7ad3-7c90-8f3c-d2a90f9a03e1",
    "01a0f448-6415-7dd2-9b57-b83eee6cd269",
    "02-a84ab374f5ed0d2a73aac293f4ea1c3b",
    "03-28b15c45689f1c28734faf2458b1adf0",
    "04-14dd9dd2f0941b565d119e80f924d12c",
    "05-52523a1d4c1b32c43e5aa3664e49f84a",
    "057d76eae931881a3209129528fef500aef762854beb6b5288411441bbf55b95",
    "06-6c66a1ff607e779c36d3aa14263b7d84",
    "07-7dc11c187444c4693d53c4deb2c6b512",
    "08-fbfbbf5d89215aff7320cccf536f1487",
    "09-0d0186528215b091bf3b222bae8efaa4",
    "10-038df275866cab10ff31c47d72ba4d90",
    "11-4f81a0dfe25c87d425001020e65202ca",
    "12-affb717d00a25db24e300e6ea06fe206",
    "13-1693035e68fa22be10b547271e4a28f2",
    "14-9a508fc197d549e4a9b0799354bd388d",
    "15-b10eff61ecd32a492b683dee9d898539",
    "16-bf5e2d995ca87ed74bf530e13ca99fdd",
    "17-6301b4fae5d0903958a7308be5e8c94c",
    "18-4c102afd6bdc332dee98c1864a553c43",
    "4ee132e8d50e8805c466cb5d681aaa18c34c9f68",
    "699b66b2a67d703d3db62cec0e2ba2b7621ff43c",
    "6e661fde4c3df4ff5382fbd8d1aebc109784df27da03c73f83352a5f36ebb876",
    "961603c2cb8b6cd1aac14ff72ecd946e26828aa5",
    "IGNITION-20260930-229-R1",
    "L01",
    "L02",
    "L03",
    "L04",
    "L05",
    "L06",
    "M0_ONLY",
    "M0_PLUS_E1",
    "POLICY_F01_A",
    "POLICY_F01_B",
    "POLICY_F02_A",
    "POLICY_F02_B",
    "POLICY_F03_A",
    "POLICY_F03_B",
    "REFERENCE_M1",
    "fcdd4b742ffd0cd7860d2ea583ea39c14ee1aa11fd832c0ab4388a3c5dd97bc0",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/02-a84ab374f5ed0d2a73aac293f4ea1c3b/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/03-28b15c45689f1c28734faf2458b1adf0/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/04-14dd9dd2f0941b565d119e80f924d12c/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/05-52523a1d4c1b32c43e5aa3664e49f84a/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/06-6c66a1ff607e779c36d3aa14263b7d84/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/07-7dc11c187444c4693d53c4deb2c6b512/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/08-fbfbbf5d89215aff7320cccf536f1487/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/09-0d0186528215b091bf3b222bae8efaa4/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/10-038df275866cab10ff31c47d72ba4d90/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/11-4f81a0dfe25c87d425001020e65202ca/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/12-affb717d00a25db24e300e6ea06fe206/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/13-1693035e68fa22be10b547271e4a28f2/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/14-9a508fc197d549e4a9b0799354bd388d/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/15-b10eff61ecd32a492b683dee9d898539/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/16-bf5e2d995ca87ed74bf530e13ca99fdd/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/17-6301b4fae5d0903958a7308be5e8c94c/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/dispatch-receipt.json",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/last-message.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/stderr.txt",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/18-4c102afd6bdc332dee98c1864a553c43/attempt-01/stdout.jsonl",
    "ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/session-run-index.json",
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY01/m0.md",
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY01/revision-evidence-e1.md",
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY02/m0.md",
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY02/revision-evidence-e1.md",
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY03/m0.md",
    "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY03/revision-evidence-e1.md",
    "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F01_A.json",
    "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F01_B.json",
    "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F02_A.json",
    "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F02_B.json",
    "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F03_A.json",
    "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies/POLICY_F03_B.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/README.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/analysis-input-schema.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/blind-evaluation-schema.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/blind-key-schema.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/claim-ceiling.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/condition-manifest.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/evaluator-rubric.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/missingness-retry-rules.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/outcome-rule.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/protocol.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/response-schema.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/run/case-input-values-and-route-expectations.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/sanitization-procedure.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/session-order.json",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/session-prompt-template.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/target-opening-gate.md",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/freeze_manifest.py",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/recompute.py",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/target_opening_gate.py",
    "ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/validate_preregistration.py"
  ],
  "schema_version": "ignition-229-r2-deny-token-manifest-v1",
  "source_basis": {
    "formal_r1_commit": "d7c4715d0cdc23b8d2b0bf4c5285ce0ac6d5041b",
    "original_preregistration_commit": "961603c2cb8b6cd1aac14ff72ecd946e26828aa5",
    "original_preregistration_manifest_sha256": "057d76eae931881a3209129528fef500aef762854beb6b5288411441bbf55b95",
    "r1_session_freeze_manifest_sha256": "fcdd4b742ffd0cd7860d2ea583ea39c14ee1aa11fd832c0ab4388a3c5dd97bc0"
  }
}

<<<END_ALLOWED_FILE path="deny-token-manifest.json">>>

<<<BEGIN_ALLOWED_FILE path="generic-requirements.md" byte_length="2604" sha256="a32c758133a359b4e26f3685257d6f92c6609498949fb6f143fd96c97e7a34c1">>>
# Generic authoring requirements (synthetic-only)

Create exactly one deterministic Python standard-library-only packet builder from this package, then independently create one checker in a separate fresh CLI process from the same package. Return one complete source file per process, clearly fenced and named `builder.py` or `checker.py`. Do not write a score, classify outcomes, call a model, access a network, search for additional materials, or use any R1 implementation.

The builder command-line interface is `builder.py --response PATH --case-id A|B|C --response-id ID --case PATH --criteria PATH --deny-token-manifest PATH --response-schema PATH --output PATH`. It accepts one response envelope, one case ID, one opaque response ID, one exact case file, one exact criteria file, one deny-token manifest, the original response schema, and an output path. It must conform byte-for-byte to `packet-builder-spec.md` and the original `sanitization-procedure.md` and schemas. Parse strict UTF-8 JSON; recursively remove only the whole `route_trace` object and procedure-defined metadata keys (provenance, builder/tool, file-path/source-locator, artifact/session/policy/lineage/bundle/condition variants) before schema validation; then fail on every remaining unknown field. Select the requested A/B/C response. Exact-redact the flat literal token list in response string values, preserve every other scored value, preserve exact case/criteria bytes by strict UTF-8 round-trip and SHA-256, emit deterministic canonical UTF-8 JSON, and fail closed.

The checker command-line interface is `checker.py --response PATH --case-id A|B|C --response-id ID --case PATH --criteria PATH --deny-token-manifest PATH --response-schema PATH --packet PATH`. The checker is separately authored without access to builder source. It must implement the same contract independently, validate source/output pairs, prove scored-field equivalence except exact listed-token redaction, verify byte-bound case/criteria, and prove zero deny-token leakage in the full packet. It must not import builder code.

Use only these package files as authoring inputs. Use Python standard library only; the checker must be a separate implementation and may not import or execute the builder. `synthetic-sanitization-fixtures.json` contains synthetic-only inputs; placeholder token expansion uses only the metadata-only deny-token manifest. No real R1 response, real case, target, policy text, evaluator artifact, condition-to-outcome result, or historical Attempt-1 content may be read or inferred. No new successor session may be launched.

<<<END_ALLOWED_FILE path="generic-requirements.md">>>

<<<BEGIN_ALLOWED_FILE path="packet-builder-spec.md" byte_length="2160" sha256="62f1358dc1e4fe5ca2d154b11bf78f14d68d1f814aa579d72af8993dfdd8b56c">>>
# R2 deterministic packet-builder contract

Input one frozen response envelope, one `case_id` (`A`, `B`, or `C`), one opaque `response_id`, exact matching case bytes, exact frozen scoring-criteria bytes, the frozen deny-token manifest, and the original response schema. Do not read any other data or infer condition/lineage assignment. Never open target criteria while authoring.

Parse strict UTF-8 JSON. Before schema validation, recursively remove the complete `route_trace` object and only the procedure-defined provenance/builder/tool/file-path/source-locator/artifact/session/policy/lineage/bundle/condition metadata fields. Canonicalize metadata keys only by lowercase plus replacing hyphens with underscores; match the predeclared metadata families in the authoring requirements. Validate the resulting envelope against the exact frozen response schema; any remaining unknown key or invalid shape fails closed. Require exactly three distinct case IDs and select exactly one object for the requested case ID. Validate strict UTF-8 round trips for case and criteria bytes.

In every remaining response string leaf, replace every exact literal deny token with `[REDACTED]`; process tokens by descending character length then lexical order. Do not normalize, summarize, reorder, infer, score, or rewrite any response values. Emit exactly one packet as canonical UTF-8 JSON (`ensure_ascii=false`, sorted keys, compact separators, one final LF): `schema_version=task229-r2-blind-packet-v1`, `response_id`, `case_id`, `case_text` (strict UTF-8 decoded original bytes), `case_sha256`, `criteria_text` (strict UTF-8 decoded original bytes), `criteria_sha256`, and `response` (the selected sanitized response). Do not emit source session ID, condition, lineage, policy, raw route trace, or coordinator mapping. Do not log packet content. Fail closed on invalid schema/shape, repeated case IDs, absent requested case, invalid UTF-8, missing inputs, or any deny-token match remaining anywhere in the serialized packet. Identical inputs must produce byte-identical output. The caller supplies all paths and the opaque ID; the builder may not enumerate other files.

<<<END_ALLOWED_FILE path="packet-builder-spec.md">>>

<<<BEGIN_ALLOWED_FILE path="response-schema.json" byte_length="3278" sha256="d0a2de5555d5c176d83acba66494afbf5637dc10aba917a981d3572469a74aa8">>>
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "task229-successor-output-r0",
  "title": "Task229 successor response envelope R0",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "responses"],
  "properties": {
    "schema_version": {"const": "task229-successor-output-r0"},
    "responses": {
      "type": "array",
      "minItems": 3,
      "maxItems": 3,
      "items": {"$ref": "#/$defs/case_response"}
    }
  },
  "$defs": {
    "reported_value": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "value", "unit"],
      "properties": {
        "name": {"type": "string", "minLength": 1},
        "value": {},
        "unit": {"type": ["string", "null"]}
      }
    },
    "route_trace": {
      "type": "object",
      "additionalProperties": false,
      "required": ["policy_id", "route_type", "selected_rule_id", "selected_action_id", "input_ids", "preserved_baseline_action_ids"],
      "properties": {
        "policy_id": {"type": "string", "minLength": 1},
        "route_type": {"enum": ["selector", "fallback", "stop"]},
        "selected_rule_id": {"type": ["string", "null"]},
        "selected_action_id": {"type": ["string", "null"]},
        "input_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": true},
        "preserved_baseline_action_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": true}
      }
    },
    "case_response": {
      "oneOf": [
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["case_id", "primary_action", "additional_actions", "reported_values", "preserved_baseline_action_ids", "fallback", "scope", "rationale"],
          "properties": {
            "case_id": {"enum": ["A", "B", "C"]},
            "primary_action": {"type": "string", "minLength": 1},
            "additional_actions": {"type": "array", "items": {"type": "string"}},
            "reported_values": {"type": "array", "items": {"$ref": "#/$defs/reported_value"}},
            "preserved_baseline_action_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": true},
            "fallback": {"type": ["string", "null"]},
            "scope": {"type": "string"},
            "rationale": {"type": "string"}
          }
        },
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["case_id", "primary_action", "additional_actions", "reported_values", "preserved_baseline_action_ids", "fallback", "scope", "rationale", "route_trace"],
          "properties": {
            "case_id": {"enum": ["A", "B", "C"]},
            "primary_action": {"type": "string", "minLength": 1},
            "additional_actions": {"type": "array", "items": {"type": "string"}},
            "reported_values": {"type": "array", "items": {"$ref": "#/$defs/reported_value"}},
            "preserved_baseline_action_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": true},
            "fallback": {"type": ["string", "null"]},
            "scope": {"type": "string"},
            "rationale": {"type": "string"},
            "route_trace": {"$ref": "#/$defs/route_trace"}
          }
        }
      ]
    }
  }
}

<<<END_ALLOWED_FILE path="response-schema.json">>>

<<<BEGIN_ALLOWED_FILE path="sanitization-procedure.md" byte_length="1815" sha256="7787c29638fb97787a034ad3f3ec3ed92ba83e55168e3d31685a962e1f96688a">>>
# Blind packet sanitization R0

Sanitization runs after all raw session responses are frozen and before either evaluator receives any packet. The sanitizer must not read or use the condition-to-lineage map.

1. Create a distinct opaque response ID for each session-case pair. Keep the response-ID mapping only in the coordinator ledger.
2. Pair each response with only its matching frozen case bytes and the frozen scoring criteria.
3. Remove the complete `route_trace` object, since it is interface evidence and contains policy/rule/action/input identifiers. Remove any provenance, builder, tool, file-path, source-locator, artifact-ID, session-ID, policy-ID, lineage-ID, bundle-ID, and condition-name fields.
4. In remaining text fields, replace exact known identifiers and source-locator tokens with `[REDACTED]`. Do not rewrite, summarize, reorder, or normalize the primary action, additional actions, reported values, preserved baseline action IDs, fallback, scope, or rationale.
5. Mechanically compare the scored fields before and after sanitization. If a primary action, value, preserved baseline action, fallback, scope, or case-relevant rationale changes beyond removal of a listed identifier token, stop packet preparation. Do not rescore or repair the raw output.
6. Scan each completed packet for every condition label, policy ID, lineage ID, session ID, bundle ID, source locator, and repository/file path. Require zero matches before delivery. Store scan counts and hashes.
7. Independently randomize packet order for evaluator A and evaluator B. Evaluators receive no condition map, method material, policy file, raw trace, session order, Task228 audit outcome, or other evaluator sheet.

The raw session response is immutable. Sanitization creates derived packets only; it never edits raw records.

<<<END_ALLOWED_FILE path="sanitization-procedure.md">>>

<<<BEGIN_ALLOWED_FILE path="synthetic-sanitization-fixtures.json" byte_length="15965" sha256="e867a98b68e36195c2a7967ad1d9562934d352ef44f0b96f5a1934e781b06b56">>>
{
  "fixtures": [
    {
      "case_bytes": "synthetic case bytes for case A\n",
      "case_id": "A",
      "criteria_bytes": "synthetic criteria bytes: preserve a fictional baseline action\n",
      "fixture_id": "synthetic-full-token-and-route-removal-v1",
      "response_envelope": {
        "responses": [
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_A L01"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "A",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": "SYNTHETIC_FALLBACK 01-e15692066dfc90306e83372151fc8512",
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_A 01-e15692066dfc90306e83372151fc8512",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_BEGIN __ALL_DENY_TOKENS__ SYNTHETIC_RATIONALE_END",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": "SYNTHETIC_VALUE POLICY_F01_A"
              }
            ],
            "route_trace": {
              "input_ids": [
                "01-e15692066dfc90306e83372151fc8512",
                "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
              ],
              "policy_id": "POLICY_F01_A",
              "preserved_baseline_action_ids": [
                "SYNTHETIC_BASELINE_KEEP"
              ],
              "route_type": "selector",
              "selected_action_id": "SYNTHETIC_ACTION_ID",
              "selected_rule_id": "L01"
            },
            "scope": "SYNTHETIC_SCOPE ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/dispatch-receipt.json",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          },
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_B KEEP"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "B",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": null,
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "SYNTHETIC_BASELINE_2"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_B KEEP",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_B unchanged",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": 12.5
              }
            ],
            "scope": "synthetic-local-scope",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          },
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_C KEEP"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "C",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": null,
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "SYNTHETIC_BASELINE_2"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_C KEEP",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_C unchanged",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": 12.5
              }
            ],
            "route_trace": {
              "input_ids": [
                "01-e15692066dfc90306e83372151fc8512",
                "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
              ],
              "policy_id": "POLICY_F01_A",
              "preserved_baseline_action_ids": [
                "SYNTHETIC_BASELINE_KEEP"
              ],
              "route_type": "selector",
              "selected_action_id": "SYNTHETIC_ACTION_ID",
              "selected_rule_id": "L01"
            },
            "scope": "synthetic-local-scope",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          }
        ],
        "schema_version": "task229-successor-output-r0"
      },
      "response_id": "SYNTHETIC-OPAQUE-RESPONSE-A"
    },
    {
      "case_bytes": "synthetic case bytes for case B\n",
      "case_id": "B",
      "criteria_bytes": "synthetic criteria bytes: fictional case B\n",
      "fixture_id": "synthetic-route-absent-v1",
      "response_envelope": {
        "responses": [
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_A L01"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "A",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": "SYNTHETIC_FALLBACK 01-e15692066dfc90306e83372151fc8512",
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_A 01-e15692066dfc90306e83372151fc8512",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_BEGIN __ALL_DENY_TOKENS__ SYNTHETIC_RATIONALE_END",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": "SYNTHETIC_VALUE POLICY_F01_A"
              }
            ],
            "route_trace": {
              "input_ids": [
                "01-e15692066dfc90306e83372151fc8512",
                "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
              ],
              "policy_id": "POLICY_F01_A",
              "preserved_baseline_action_ids": [
                "SYNTHETIC_BASELINE_KEEP"
              ],
              "route_type": "selector",
              "selected_action_id": "SYNTHETIC_ACTION_ID",
              "selected_rule_id": "L01"
            },
            "scope": "SYNTHETIC_SCOPE ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/dispatch-receipt.json",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          },
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_B KEEP"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "B",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": null,
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "SYNTHETIC_BASELINE_2"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_B KEEP",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_B unchanged",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": 12.5
              }
            ],
            "scope": "synthetic-local-scope",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          },
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_C KEEP"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "C",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": null,
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "SYNTHETIC_BASELINE_2"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_C KEEP",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_C unchanged",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": 12.5
              }
            ],
            "route_trace": {
              "input_ids": [
                "01-e15692066dfc90306e83372151fc8512",
                "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
              ],
              "policy_id": "POLICY_F01_A",
              "preserved_baseline_action_ids": [
                "SYNTHETIC_BASELINE_KEEP"
              ],
              "route_type": "selector",
              "selected_action_id": "SYNTHETIC_ACTION_ID",
              "selected_rule_id": "L01"
            },
            "scope": "synthetic-local-scope",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          }
        ],
        "schema_version": "task229-successor-output-r0"
      },
      "response_id": "SYNTHETIC-OPAQUE-RESPONSE-B"
    },
    {
      "case_bytes": "synthetic case bytes for case C\n",
      "case_id": "C",
      "criteria_bytes": "synthetic criteria bytes: fictional case C\n",
      "fixture_id": "synthetic-route-present-v1",
      "response_envelope": {
        "responses": [
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_A L01"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "A",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": "SYNTHETIC_FALLBACK 01-e15692066dfc90306e83372151fc8512",
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_A 01-e15692066dfc90306e83372151fc8512",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_BEGIN __ALL_DENY_TOKENS__ SYNTHETIC_RATIONALE_END",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": "SYNTHETIC_VALUE POLICY_F01_A"
              }
            ],
            "route_trace": {
              "input_ids": [
                "01-e15692066dfc90306e83372151fc8512",
                "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
              ],
              "policy_id": "POLICY_F01_A",
              "preserved_baseline_action_ids": [
                "SYNTHETIC_BASELINE_KEEP"
              ],
              "route_type": "selector",
              "selected_action_id": "SYNTHETIC_ACTION_ID",
              "selected_rule_id": "L01"
            },
            "scope": "SYNTHETIC_SCOPE ignition/evaluation/ignition-229-r1-cli-transfer-replication-r0/run/sessions/01-e15692066dfc90306e83372151fc8512/attempt-01/dispatch-receipt.json",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          },
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_B KEEP"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "B",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": null,
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "SYNTHETIC_BASELINE_2"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_B KEEP",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_B unchanged",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": 12.5
              }
            ],
            "scope": "synthetic-local-scope",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          },
          {
            "additional_actions": [
              "SYNTHETIC_ADDITIONAL_C KEEP"
            ],
            "artifact_id": "SYNTHETIC_ARTIFACT",
            "builder": "SYNTHETIC_BUILDER",
            "bundle_id": "SYNTHETIC_BUNDLE",
            "case_id": "C",
            "condition_name": "SYNTHETIC_CONDITION",
            "fallback": null,
            "lineage_id": "SYNTHETIC_LINEAGE",
            "policy_id": "SYNTHETIC_POLICY",
            "preserved_baseline_action_ids": [
              "SYNTHETIC_BASELINE_KEEP",
              "SYNTHETIC_BASELINE_2"
            ],
            "primary_action": "SYNTHETIC_PRIMARY_C KEEP",
            "provenance": "SYNTHETIC_PROVENANCE",
            "rationale": "SYNTHETIC_RATIONALE_C unchanged",
            "reported_values": [
              {
                "name": "synthetic_metric",
                "unit": "units",
                "value": 12.5
              }
            ],
            "route_trace": {
              "input_ids": [
                "01-e15692066dfc90306e83372151fc8512",
                "01a0f43d-99cc-7412-9310-ed8dd251d4a4"
              ],
              "policy_id": "POLICY_F01_A",
              "preserved_baseline_action_ids": [
                "SYNTHETIC_BASELINE_KEEP"
              ],
              "route_type": "selector",
              "selected_action_id": "SYNTHETIC_ACTION_ID",
              "selected_rule_id": "L01"
            },
            "scope": "synthetic-local-scope",
            "session_id": "SYNTHETIC_SESSION",
            "source_locator": "__ONE_SOURCE_LOCATOR_TOKEN__",
            "tool": "SYNTHETIC_TOOL"
          }
        ],
        "schema_version": "task229-successor-output-r0"
      },
      "response_id": "SYNTHETIC-OPAQUE-RESPONSE-C"
    }
  ],
  "purpose": "Synthetic-only contract fixtures; no real R1 response/case/target/evaluator data. The gate runner replaces the two explicit placeholders with metadata tokens from deny-token-manifest.json before each invocation.",
  "schema_version": "ignition-229-r2-synthetic-sanitization-fixtures-v1",
  "token_expansion": {
    "all_tokens_joiner": " | ",
    "all_tokens_placeholder": "__ALL_DENY_TOKENS__",
    "must_expand_from": "deny-token-manifest.json#literal_tokens",
    "single_source_locator_placeholder": "__ONE_SOURCE_LOCATOR_TOKEN__"
  }
}

<<<END_ALLOWED_FILE path="synthetic-sanitization-fixtures.json">>>

End of allowed package. Return only builder.py source in one fenced python block.
