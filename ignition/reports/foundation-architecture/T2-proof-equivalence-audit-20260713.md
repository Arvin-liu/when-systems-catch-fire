# T2 proof-equivalence audit

## Legacy proposition

The source says “任一因子=0→乘积=0” and applies it to the point-fire framework product. It does not declare `Nat`, restrict the product to two factors, or type all factors into one algebraic carrier.

## Artifacts

- Lean proves, for two `Nat` values, `a = 0 ∨ b = 0 → a * b = 0`.
- Z3 proves the corresponding two-factor statement over mathematical integers.

Both artifacts are valid, but their domains differ from one another and both are narrower than the source's domain-unspecified, any-factor framework statement. They are therefore proved weakened lemmas, not an equivalent proof of legacy T2.

## Status

Legacy T2 is `PARTIALLY_FORMALIZED` and remains unproved as stated. The two-factor zero-absorption lemma remains machine checked and separately indexed.
