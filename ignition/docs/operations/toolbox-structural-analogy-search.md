# Structural Analogy Search

**Tool ID:** reasoning.search_structural_analogies
**Version:** 0.1.0
**Availability:** optional experimental tool, default off
**Entrypoint:** python3.10+ -B ignition/tools/toolbox_structural_analogy_search.py --stdin

## Purpose

Compare one small caller-supplied relation graph with one to eight candidate graphs in other domains. The tool enumerates injective node mappings that preserve exact controlled role classes, applies the caller's one-to-one relation-type map, and ranks candidates by exact directed relation matches and then fewer extra mapped relations.

The input contains identifiers, role classes, directed relation triples, and an explicit relation map. It contains no free-text labels, embeddings, internet lookup, ontology, or authority metadata. The algorithm therefore measures only the structure encoded in that input.

## Suitable tasks

- Find bounded candidate structures when a task already has a typed source graph, typed target graphs, and an explicit relation-type correspondence.
- Generate a short list of transfer hypotheses for later target-domain validation.
- Check whether direction and role constraints preserve a proposed structural analogy.

## Do not use it for

- Discovering or validating facts about a target domain, proving semantic equivalence, or transferring authority or evidence.
- Ranking free-text ideas, inferring relation mappings, generating target candidates, or deciding that a proposed solution is safe or effective.
- Any task needing more than eight nodes per graph, more than eight candidates, more than 24 edges per graph, or more than 200,000 possible node mappings.
- A task where role classes or relation mappings are unknown or disputed; supply a human-reviewed mapping first or use a different method.

## Input and output

Read one UTF-8 JSON request from stdin. The input and output schemas are in the operations schema directory. The request is limited to 256 KiB. Node and relation identifiers are unique within their graph; every edge endpoint must exist; source relation types must be covered exactly by a one-to-one relation map.

Output includes candidate ranks, coverage counts, precision among mapped target relations, the best node maps, extra and unmapped relations, and transfer hypotheses marked REQUIRES_TARGET_DOMAIN_VALIDATION. Tied mappings are counted and at most eight are detailed. Ratios preserve the actual numerator and denominator. A missing role-compatible mapping reports zero coverage over the source's actual edge count and null mapped-target precision; unclassified target edges are reported separately.

## Permissions, cost, and dependencies

Read-only local computation. It reads only stdin, writes one bounded JSON result to stdout, and writes diagnostics to stderr. It has no network, secret, billing, repository-write, or external-action access. Python 3.10+ standard library only. The search uses bounded enumeration; latency and memory cost are unknown beyond the declared graph and mapping limits.

## Evidence and comparison

The focused fixture searches for a structure corresponding to a repository component-admission workflow. It contains an exact role- and direction-preserving pipeline-validation analog, a graph with an additional mapped relation, and a reversed-edge negative control. These are tool-behavior examples and do not establish a real-world analogy.

The existing object-collision operation checks identity collisions against registered current objects, and the grounded-ideation preflight validates a caller-provided sourced proposal and relation map. Neither enumerates role-compatible mappings across caller-supplied target graphs. Those tools keep their distinct use cases. The comparison remains limited to their declared interfaces; this candidate is specialized, and no replacement or retirement is established.

## Route, failure, and rollback

The candidate is not selected by default. The route planner may propose it only after the caller explicitly includes its tool ID and the task profile requires the declared graph inputs and outputs. A route proposal never invokes the tool or grants execution authority.

Malformed JSON, duplicate keys, unexpected fields, duplicate identifiers/triples, missing relation mappings, non-injective mappings, unknown edge endpoints, and requests exceeding the mapping budget fail closed. Use a manual typed relation-graph review or a caller's existing analysis process as fallback; retain the original graphs and do not treat no match as evidence that no analogy exists.

Rollback removes this candidate card, implementation, schemas, fixture, tests, documentation, and candidate-specific evidence from the isolated branch, then rebuilds the toolbox identity-card and human-directory projections. Preserve the implementation and comparison commit history plus the Workbench blueprint reference for historical reproduction.
