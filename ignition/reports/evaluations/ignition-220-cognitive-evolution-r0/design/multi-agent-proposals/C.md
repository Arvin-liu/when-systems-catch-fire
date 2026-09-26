# Agent C — Adversarial controls proposal

**Claim to test:** M1’s revised relation structure improves transfer on held-out cases beyond what a successor can recover from M0, raw failure evidence, or generic reasoning. Improvement must depend on the relevant relation structure.

## Control conditions

Run every held-out case with the same model, task prompt, tools, token budget, and scoring rule. Isolate each run’s context and randomize run order.

1. **M0 alone:** frozen M0; no raw failure records or M1.
2. **M0 + raw failure evidence:** M0 plus the eligible raw records used to develop M1, in unstructured form. Exclude held-out cases, labels, answers, and target-specific feedback.
3. **Generic reasoning:** task prompt and shared instructions only; no M0, raw failure records, or M1.
4. **M1:** M0 plus the revised relation structure. Record the specific relation claims retrieved and used for each answer.

Keep raw source evidence equivalent between conditions 2 and 4, so the comparison tests whether M1’s relation structure adds value beyond the evidence itself.

## Held-out cases for each of the three families

Build matched cases after freezing M1. In every family, include:

- **Novel compositions:** familiar relation types recombined in held-out contexts, so direct recall of a training example is insufficient.
- **Relation-swap pairs:** hold wording, entities, and facts constant while changing one relation that should change the answer. Require the answer to flip accordingly.
- **Relation-ablation or decoy cases:** remove, reverse, or misbind one relation. M1 should lose or change its answer appropriately rather than follow a topical or lexical cue.
- **Negative controls:** cases whose answer does not depend on the revised relation structure. M1 should not show a broad gain on these.

Balance relation variants and answer labels; use neutral or randomized names. Score both answer correctness and whether the cited relation supports the answer.

## Leakage and attribution checks

Before scoring, freeze and hash M1, the held-out suite, prompts, and eligible source records. Have a separate custodian retain held-out labels and answers. For every family:

- Trace every M1 node and edge to an allowed source and creation date; reject held-out or post-freeze material.
- Search M1 and its source records for exact and fuzzy matches to held-out wording, labels, answers, identifiers, and feedback. Inspect semantic retrieval results too; string search alone is insufficient.
- Audit filenames, metadata, indexes, caches, tool outputs, and retrieval logs for answer-bearing cues. Randomize case IDs and strip answer-revealing names.
- Run each condition in a clean context with no cross-run history, shared outputs, or external retrieval.
- Test relation dependence with the paired relation swaps: the answer should change only when the decisive relation changes. A correct answer that persists after the relation is removed or reversed is evidence against the claimed mechanism.

Report per-family results against **each** control, including the relation-swap pairs and negative controls. Do not attribute a gain to M1 if the same answers are obtained from M0, raw evidence, or generic reasoning, or if M1 succeeds without using the decisive relation.
