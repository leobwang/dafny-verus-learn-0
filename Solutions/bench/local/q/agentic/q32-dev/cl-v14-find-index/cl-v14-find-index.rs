// Topic (e) course-local task cl-v14-find-index (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `find_index`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn find_index(v: &Vec<i64>, x: i64) -> (k: usize)
    ensures
        k <= v.len(),
        k < v.len() ==> v[k as int] == x,
        forall|j: int| 0 <= j < k ==> v[j] != x,
{
    let mut k: usize = 0;
    while k < v.len() && v[k] != x
        invariant
            k <= v.len(),
            forall|j: int| 0 <= j < k ==> v[j] != x,
        decreases v.len() - k,
    {
        k = k + 1;
    }
    k
}

} // verus!
