// Topic (e) course-local task cl-v18-index-of-min (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `index_of_min`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn index_of_min(v: &Vec<i64>) -> (k: usize)
    requires
        v.len() > 0,
    ensures
        k < v.len(),
        forall|j: int| 0 <= j < v.len() ==> v[k as int] <= v[j],
{
    let mut k: usize = 0;
    let mut i: usize = 1;
    while i < v.len()
        invariant
            1 <= i <= v.len(),
            k < i,
            forall|j: int| 0 <= j < i ==> v[k as int] <= v[j],
        decreases v.len() - i,
    {
        if v[i] < v[k] {
            k = i;
        }
        i = i + 1;
    }
    k
}

} // verus!
