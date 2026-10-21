// Topic (e) course-local task cl-v17-fill-zero (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `fill_zero`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn fill_zero(n: usize) -> (v: Vec<u8>)
    ensures
        v.len() == n,
        forall|j: int| 0 <= j < n ==> v[j] == 0,
{
    let mut v: Vec<u8> = Vec::new();
    let mut i: usize = 0;
    while i < n
        invariant
            i <= n,
            v.len() == i,
            forall|j: int| 0 <= j < i ==> v[j] == 0,
        decreases n - i,
    {
        v.push(0);
        i = i + 1;
    }
    v
}

} // verus!
