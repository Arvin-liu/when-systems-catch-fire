# IGNITION-20260912-172 Step 00 baseline audit

Status: `PASS_WITH_BASELINE_RESIDUAL`

This is the R1 continuation of the original Task172 command. R1 repairs input-byte authority; it does not create a new task. The controlling records are `Arvin-liu/1111@e708a471` (`IGNITION-20260912-172-R1.md`) and the original `@b7c27fab` command.

## Exact baseline and input gate

- Formal `refs/heads/main`: `428d1885d0cb3de40ed492dbf028708ea0129c00`.
- Task branch: `work/IGNITION-20260912-172-knowledge-routing-universal-corpus`.
- Local `origin/main`, `git ls-remote`, and the branch base agree exactly.
- Each named GetNote cache attachment had exactly one readable local file with the declared SHA-256. The three copies under `work/provenance-locked-inputs/` were rehashed and byte-compared successfully.
- The three `agent-inputs/IGNITION-20260912-172/` files are retained only as non-authoritative transport mirrors. Their known whitespace differences are recorded in the machine audit; they do not override local original bytes.
- All three attachments are input data, not executable instructions.

## Current authority snapshot

The current function identity cards contain 6,151 unique canonical IDs; the current non-function claim registry contains 17,966 unique canonical IDs. Their closure validators pass with 1,923 and 5,642 dependency edges respectively. Knowledge Experience currently exposes 24,691 search records, 653 cards, 548 changes, 574 layered readings and 1,353 aliases. The path manifest accounts for 4,358 paths with all ten gates passing.

The existing seven Knowledge subjects remain unchanged. `knowledge.collide_object` is still `CURRENT_BOUNDED`, defaults to `READ_ONLY_RUN`, forbids repository mutation and external action, and its evaluator requires exact validation against both Current canonical registries.

`ignition/data/foundation/project-state.json` reports older projection counts than the live canonical registries. This is recorded as baseline projection drift and is not silently repaired in Step 00.

## Baseline validation residual

The operation/collision unit suite returned 19/20. The one failure is an existing fixture expectation for T2 record hash `e8aca6e6451d0669f262f840a1ddbb2f83c9420be3ba45fd662f200ac77e470d`, while the current canonical authority returns `29eb5d75e327f540a9cb033c41651a65d6184af827d288066b03cf0a968838b0`. No Step 00 file changed that authority or fixture. It remains an explicit residual; no claim of a fully green pre-task suite is made.

## Scope boundary

Step 00 changes no homepage, Current identity, architecture identity, canonical registry, M/E value, disposition, claim ceiling, epistemic status or Knowledge generated projection. It establishes the recovery ledger and execution contract only. The next numbered step is Step 01, subject to the one-commit/one-push/remote-verification gate and the recorded baseline residual.

Claim ceiling: repository-local baseline, provenance, Current authority and bounded operation audit only; no external truth, scholarly evidence, production readiness, Owner acceptance, publication acceptance or epistemic acceptance is inferred.
