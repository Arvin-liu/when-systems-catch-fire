; T2, scoped to mathematical integers: if either factor is zero, the product is zero.
(set-logic QF_NIA)
(declare-const a Int)
(declare-const b Int)
(assert (or (= a 0) (= b 0)))
(assert (not (= (* a b) 0)))
(check-sat)
; Expected: unsat
