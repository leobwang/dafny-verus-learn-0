// Topic (e) course-local task cl-v15-max-of (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `max_of`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn max_of(v: &Vec<i64>) -> (m: i64)
    requires
        v.len() > 0,
    ensures
        forall|j: int| 0 <= j < v.len() ==> v[j] <= m,
        exists|j: int| 0 <= j < v.len() && v[j] == m,
{
    let mut m = v[0];
    let mut i: usize = 1;
    while i < v.len()
        decreases v.len() - i,
    {
        if v[i] > m {
            m = v[i];
        }
        i = i + 1;
    }
    m
}

} // verus!
