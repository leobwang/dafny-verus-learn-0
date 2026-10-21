// Topic (e) course-local task cl-v22-reverse-copy (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `reverse_copy`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn reverse_copy(v: &Vec<i64>) -> (r: Vec<i64>)
    ensures
        r.len() == v.len(),
        forall|j: int| 0 <= j < v.len() ==> r[j] == v[v.len() - 1 - j],
{
    let mut r: Vec<i64> = Vec::new();
    let mut i: usize = v.len();
    while i > 0
        decreases i,
    {
        i = i - 1;
        r.push(v[i]);
    }
    r
}

} // verus!
