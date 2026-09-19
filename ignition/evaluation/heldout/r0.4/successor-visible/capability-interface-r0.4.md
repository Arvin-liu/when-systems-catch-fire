# Provider-Neutral Capability Interface R0.4

## Input

The caller supplies the exact task contract, method contract, packet manifest, output and ledger schemas, and the two case sources listed in the cognitive allowlist. No model-vendor API, provider-specific message format, hidden evaluator prompt, or operational tool source is part of this interface.

## Capability

For each supplied case, produce a bounded account that separates source observations, interpretations, uncertainties, and missing evidence. The response may leave a question unresolved. The interface does not require a particular conclusion or guarantee that a provider can satisfy every requested operation.

## Output

Return one JSON object conforming to `successor-output-r0.4.schema.json`, with exactly one response for each case ID. The response fields are the model's own synthesis. The schema contains no expected answer, relation label, continuation, score, or evaluation result.

## Operational boundary

Operational tools may be executed only through the paths and actions in the packet manifest. Their source and receipts are not input to this capability interface. The Successor receives finite status values only. The final read-ledger validator runs after the ledger is closed and writes its independent receipt outside the packet; its invocation is not a ledger row. A case-specific value obtained through an operational channel is contamination even though a case-specific value obtained through an authorized cognitive read is normal.
