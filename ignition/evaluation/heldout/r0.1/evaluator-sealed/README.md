# Evaluator-only preregistration instructions

This directory intentionally contains no case-specific answer, gold IR, gold
relations, transition, human confirmation, or expected continuation. It is
excluded from the successor allowlist.

Before opening Task182 outputs, the independent Task183 evaluator must create
and hash its own source-grounded anchor inventory and scoring notes for both
cases, using only the raw packet and provenance. Record the sealed reference
commit/ref and hash before any successor narrative is inspected. Then evaluate
the frozen criteria in `../evaluation-criteria-r0.1.json`. A missing ordering
proof, post-output rubric change, or shared conversation history is a protocol
deviation and must be disclosed. This is procedural isolation, not
cryptographic secrecy.
