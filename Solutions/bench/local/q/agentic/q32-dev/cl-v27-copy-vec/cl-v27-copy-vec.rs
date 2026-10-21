// Topic (e) course-local task cl-v27-copy-vec (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `copy_vec`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn copy_vec(v: &Vec<i64>) -> (r: Vec<i64>)
    ensures
        r@ == v@,
{
    let mut r: Vec<i64> = Vec::new();
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            r@ =~= v@.subrange(0, i as int),
        decreases v.len() - i,
    {
        r.push(v[i]);
        i = i + 1;
    }
    assert(v@.subrange(0, v.len() as int) =~= v@);
    r
}

} // verus!
