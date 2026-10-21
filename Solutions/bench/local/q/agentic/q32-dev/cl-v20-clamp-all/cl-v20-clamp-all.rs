// Topic (e) course-local task cl-v20-clamp-all (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `clamp_all`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn clamp_all(v: &Vec<i64>, lo: i64, hi: i64) -> (r: Vec<i64>)
    requires
        lo <= hi,
    ensures
        r.len() == v.len(),
        forall|j: int| 0 <= j < r.len() ==> lo <= #[trigger] r[j] && r[j] <= hi,
{
    let mut r: Vec<i64> = Vec::new();
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            r.len() == i,
            lo <= hi,
            forall|j: int| 0 <= j < r.len() ==> lo <= #[trigger] r[j] && r[j] <= hi,
        decreases v.len() - i,
    {
        let x = if v[i] < lo { lo } else if v[i] > hi { hi } else { v[i] };
        r.push(x);
        i = i + 1;
    }
    r
}

} // verus!
