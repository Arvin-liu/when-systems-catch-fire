# Soft Context Exposure Contract R0

This contract describes one optional, provider-neutral handoff: an external executor may read a bounded Structural Governance Surface before acting. The handoff is advisory context, not a new instruction hierarchy and not an authority channel.

## What crosses the boundary

The observable capsule may carry a surface identifier, a transition-relation identifier, a claim ceiling, a Current-state label, unknowns/open obligations, source pointers and an advisory experiment-arm label. It may carry receipt metadata about what was exposed and what was validated.

It does not carry hidden reasoning, a full prompt or token stream, vendor session state, secrets, channel/device state, an approval decision, an Owner decision, a truth decision or an unvalidated external effect.

## What does not change

Capability, permission, authorization, truth status, M/E, claim ceiling, Owner status and epistemic acceptance all have an explicit delta of `NONE`. The effective permission remains the strict intersection of the task, profile, pack, executor and approval scopes. A soft surface cannot widen it.

The exposure is request-local and has no durable authority. It cannot authorize browser, network, messaging, device, remote Git or other external side effects. A downstream executor may ignore it, reject it, or report that it could not consume it.

## OS/Federation ownership

Ignition OS remains the owner of goals, contracts, approvals, canonical state, validation and receipts. An external Agent remains responsible for its own model loop and tool wiring. An adapter translates only observable boundaries and must not copy a vendor runtime or import private session state. This is consistent with the [External Agent Federation R1 boundary](external-agent-federation-r1.md).

## Human reading and failure handling

The [ESI human surface](esi-human-surface-r0.md) is the readable explanation. If a proposed adapter maps soft context to permission, truth, Owner acceptance, epistemic acceptance, safety release or an external effect, the mapping is rejected as `REJECT_SOFT_AUTHORITY_ESCALATION`. If the exposure cannot be sanitized into the declared capsule, it is skipped and recorded as unavailable; it is not silently widened.

Machine contract: [soft-context-exposure-contract-r0.json](../../data/agent-federation/soft-context-exposure-contract-r0.json). The underlying non-authority invariant remains the hard negative contract.
