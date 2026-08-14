# Core proof and countermodel report

- T2 is retained as a Nat-scoped theorem: `forall a b, a=0 or b=0 -> a*b=0`.
- Machine artifacts: `formal/lean/Foundation.lean`, `formal/z3/T2-zero-factor.smt2`, and `tools/foundation/verify_core_claims.py`.
- T16 is refuted as stated by `f1(x)=exp(x)`, `f2(x)=exp(-2x)`: one increases, one decreases, while their product `exp(-x)` is strictly decreasing.
- D220's displayed implication is invalid without a physical-existence premise; a Boolean countermodel makes all displayed implications true while `Omega=1` remains true.
- T23 remains `UNPROVED_PROPOSITION`: existence of a minimum requires a defined domain plus conditions such as compactness/coercivity and continuity/lower-semicontinuity.
- Proof artifacts: 1 claim with Lean/Z3 realizations. Replayable counterexample/countermodel records: 2.
