// Topic (e) course-local task cl-v16-all-pos (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `all_positive`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn all_positive(v: &Vec<i64>) -> (b: bool)
    ensures
        b == (forall|j: int| 0 <= j < v.len() ==> v[j] > 0),
{
    let mut b = true;
    let mut i: usize = 0;
    while i < v.len()
        decreases v.len() - i,
    {
        if v[i] <= 0 {
            b = false;
        }
        i = i + 1;
    }
    b
}

} // verus!
