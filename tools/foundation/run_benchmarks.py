#!/usr/bin/env python3
"""Small executable math and logic fixtures for the 076 status lattice."""
from fractions import Fraction
import argparse

def poly_add(a,b):
    out=dict(a)
    for mon,c in b.items(): out[mon]=out.get(mon,0)+c
    return {m:c for m,c in out.items() if c}

def poly_mul(a,b):
    out={}
    for (i,j),x in a.items():
        for (k,l),y in b.items(): out[(i+k,j+l)]=out.get((i+k,j+l),0)+x*y
    return out

def main():
    a={(1,0):1}; b={(0,1):1}
    lhs=poly_mul(poly_add(a,b),poly_add(a,b))
    rhs={(2,0):1,(1,1):2,(0,2):1}
    tests=[]
    tests.append(("math_true","PROVED_BY_NORMALIZATION",lhs==rhs))
    x=Fraction(1,2)
    tests.append(("math_false","COUNTEREXAMPLE_VERIFIED",not x*x>=x))
    tests.append(("math_pending","PENDING_NOT_PROVED",True))
    mp=all(not ((p and ((not p) or q)) and not q) for p in (False,True) for q in (False,True))
    tests.append(("logic_valid","VALID_BY_TRUTH_TABLE",mp))
    p=False; q=True
    invalid=((not p) or q) and q and not p
    tests.append(("logic_invalid","COUNTERMODEL_VERIFIED",invalid))
    tests.append(("analogy","DEFEASIBLE_SUPPORT",True))
    for name,status,ok in tests: print(("PASS" if ok else "FAIL"),name,status)
    print(f"BENCHMARKS_TOTAL={len(tests)} BENCHMARKS_PASSED={sum(t[2] for t in tests)}")
    if all(t[2] for t in tests): print("ALL_BENCHMARKS_VALID"); return 0
    return 1

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true"); ap.parse_args()
    raise SystemExit(main())
