// Topic (e) course-local task cl-v24-sorted-check (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `sorted_check`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn sorted_check(v: &Vec<i64>) -> (b: bool)
    ensures
        b == (forall|k: int| 0 <= k && k + 1 < v.len() ==> #[trigger] v[k] <= v[k + 1]),
{
    let mut b = true;
    let mut i: usize = 0;
    while i < v.len()
        decreases v.len() - i,
    {
        if i + 1 < v.len() && v[i] > v[i + 1] {
            b = false;
        }
        i = i + 1;
    }
    b
}

} // verus!
