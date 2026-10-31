# Grounded Ideation Preflight

`research.preflight_grounded_ideation@0.1.0` checks one caller-supplied research-proposal packet for structural traceability before human review. It is an optional offline preflight, not an idea generator or literature-search system.

It checks that the packet distinguishes used sources from attached sources, resolves evidence anchors to used source records, finds each quoted string inside the caller-supplied excerpt, includes both support and contrary anchors for a proposed gap, makes a source-to-target relation mapping explicit, names necessary conditions and boundaries, and supplies a minimum experiment, controls, falsifiers, uncertainties, and an abstention rule. If a temporal cutoff is supplied, used sources with unknown or later dates keep the packet incomplete.

Run it with one UTF-8 JSON object on standard input:

```sh
python3 -B ignition/tools/toolbox_grounded_ideation_preflight.py --stdin < ignition/tests/fixtures/toolbox-grounded-ideation-preflight/valid-input-r0.json
```

The input contract is [grounded-ideation-preflight-r0.schema.json](../../schemas/operations/grounded-ideation-preflight-r0.schema.json). The tool caps input at 256 KiB, sources at 32, evidence anchors at 128, source excerpts at 16 KiB each, and quote strings at 2 KiB. It reads no repository files, writes no files, and makes no network requests. Output omits source excerpts and quotes.

`PREFLIGHT_READY_FOR_HUMAN_REVIEW` means only that the supplied structure and quote-substring checks passed. A matching quote can still be irrelevant, misleading, misattributed, copyrighted, or semantically unsupported. The tool does not authenticate source identity, check citation links, search for prior art, establish novelty, validate a cross-domain mechanism, decide which idea to pursue, perform independent review, run an experiment, or accept a scientific result. It cannot prove that a source date or excerpt is accurate. The report always leaves source authenticity, semantic support, independent review, scientific acceptance, and execution authorization unestablished.

Use only with text that may safely be supplied to a local tool. Do not include secrets, personal data, restricted source text, or content whose use is not permitted. The result is a proposal-structure aid; it does not grant research, publication, or execution authority.

The checked-in input is synthetic and supports only a bounded interface smoke test.

The existing adaptive route planner was replayed against this exact input/output contract. It leaves the optional candidate unselected by default and proposes it only when the caller explicitly allowlists its tool ID. That route plan does not invoke the tool or authorize execution; see [the route profile](../../data/operations/toolbox-grounded-ideation-preflight-route-profile-r0.json) and [the local route evidence](../../data/operations/toolbox-grounded-ideation-preflight-route-evidence-r0.json).
