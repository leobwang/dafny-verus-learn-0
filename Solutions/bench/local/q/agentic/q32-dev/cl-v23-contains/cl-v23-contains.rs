// Topic (e) course-local task cl-v23-contains (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `contains_value`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn contains_value(v: &Vec<i64>, x: i64) -> (b: bool)
    ensures
        b == (exists|j: int| 0 <= j < v.len() && v[j] == x),
{
    let mut b = false;
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            b == (exists|j: int| 0 <= j < i && v[j] == x),
        decreases v.len() - i,
    {
        if v[i] == x {
            b = true;
        }
        i = i + 1;
    }
    b
}

} // verus!
