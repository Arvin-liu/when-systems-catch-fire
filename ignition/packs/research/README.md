# Research Domain Pack — REOS LIGHT

This is the bounded REOS LIGHT research pack entrypoint. It routes declared
research validation and obligation coordination only; it does not grant truth,
Owner, executor, network, or generic permission authority.

Within Agent Platform R2 it is a Pack-aware proposal/validation surface, not a
second Kernel or a long-running scheduler. Its obligation DAG, evidence-request
and review projections stay bounded by the REOS LIGHT contract; a completed
workflow cannot create truth, Owner acceptance or `EPISTEMICALLY_ACCEPTED`.

The runtime may route a declared REOS capability, but the Pack cannot import an
unlisted module, select an executor, widen a Profile, or mutate the Knowledge
 registry. See [`manifest.json`](./manifest.json) and the
[REOS LIGHT boundary](../../docs/architecture/reos-vnext-light.md).

External Agent Federation is a separate OS/executor contract. This Pack may
produce a bounded research proposal, but it cannot select an adapter, absorb an
external session into memory, or treat executor output as evidence without the
declared validation and provenance gates.
