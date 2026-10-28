namespace IgnitionFoundation

namespace IgnitionFoundation

theorem T2_mul_zero_factor (a b : Nat) (h : a = 0 ∨ b = 0) : a * b = 0 := by
  cases h with
  | inl ha => simp [ha]
  | inr hb => simp [hb]

end IgnitionFoundation
