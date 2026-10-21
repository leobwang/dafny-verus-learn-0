// Topic (e) course-local task cl-v25-sum-bytes (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `sum_bytes`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn sum_bytes(v: &Vec<u8>) -> (s: u64)
    requires
        v.len() <= 1000,
    ensures
        s <= 255 * v.len(),
{
    let mut s: u64 = 0;
    let mut i: usize = 0;
    while i < v.len()
        decreases v.len() - i,
    {
        s = s + v[i] as u64;
        i = i + 1;
    }
    s
}

} // verus!
