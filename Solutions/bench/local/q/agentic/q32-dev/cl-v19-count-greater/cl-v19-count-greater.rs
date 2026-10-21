// Topic (e) course-local task cl-v19-count-greater (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `count_greater`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn count_greater(v: &Vec<i64>, t: i64) -> (c: usize)
    ensures
        c <= v.len(),
{
    let mut c: usize = 0;
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            c <= i,
        decreases v.len() - i,
    {
        if v[i] > t {
            c = c + 1;
        }
        i = i + 1;
    }
    c
}

} // verus!
