# Early-ignition historical replay — Task163

This is the Stage A historical qualification record for the research-only R1 operator.

## Isolation

The frozen universe has 18 real events: P01–P04, N01–N12, and B01–B02. Each packet is identified to the blind operator only by an anonymous packet ID and sequence. Its material is built from the repository snapshot at the pre-event cutoff, plus a bounded pre-cutoff history window. Post-event diffs, event subjects, labels, answer descriptions, and later canonical terminology are absent from the packet.

The separate `historical-answer-key.jsonl` contains the event mapping and capability requirements. It is not an operator input. `historical-blind-run-1.jsonl` and `historical-blind-run-2.jsonl` were byte-identical. The answer key was read only during the unblind evaluation step.

## Qualification outcome

The operator generated a few ordinary structural cues, but it did not produce a basis mutation that survived replay of prior material. Consequently:

- P01, P02, P03, and P04: no capability-equivalent mutation was established;
- N02 and N03: no mutation signal, so both remained stable non-leap controls in this run;
- strong-negative false positives: `0`;
- Stage A: `FAIL`.

The result is limited by the pre-event-only packet boundary and by deterministic open structural extraction. It is not an independent semantic adjudication of any historical commit. The failed qualification gate prevents the operator from judging external longform material.

## Machine records

- `historical-event-universe.jsonl`
- `historical-temporal-packets.jsonl`
- `historical-stage-a-split.json`
- `historical-blind-run-1.jsonl`
- `historical-blind-run-2.jsonl`
- `historical-unblind-evaluation.jsonl`
- `historical-qualification-verdict.json`
- `mutation-proposals.jsonl`
- `mutation-replay-results.jsonl`
- `representation-generations.jsonl`
