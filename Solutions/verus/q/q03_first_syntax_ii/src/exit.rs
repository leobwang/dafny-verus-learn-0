//! # Q03 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q03_first_syntax_ii/src/exit.rs` (author-only):
//! every block answered and every `need:` fragment present in its code. Never
//! `mod`-declared; `scripts/vcheck --ref` builds it alone with the crate's dependencies.
//! Silent: the reference gate prints only its summary line.
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

/// Given (not an item): the specification of doubling, for X3.
pub open spec fn twice_spec(x: int) -> int {
    2 * x
}

// item: Q03.X1v S7
// uses: ghost
// need: pub fn find_at_least(v: &Vec<u64>, b: u64) -> (r: (bool, Ghost<int>))
// need: r.0 ==> 0 <= r.1@ < v.len() && v@[r.1@] >= b
// need: !r.0 ==> forall|j: int| 0 <= j < v.len() ==> v@[j] < b
// pair: Q03.X1d
/// **X1.** Search for a limb at least `b`. Reference: a linear search whose invariant
/// says every limb read so far is below `b`; on a hit, `Ghost(i as int)` carries the index
/// as the witness of the first postcondition (a ghost value inside an exec tuple).
pub fn find_at_least(v: &Vec<u64>, b: u64) -> (r: (bool, Ghost<int>))
    ensures
        r.0 ==> 0 <= r.1@ < v.len() && v@[r.1@] >= b,
        !r.0 ==> forall|j: int| 0 <= j < v.len() ==> v@[j] < b,
{
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            forall|j: int| 0 <= j < i ==> v@[j] < b,
        decreases v.len() - i,
    {
        if v[i] >= b {
            return (true, Ghost(i as int));
        }
        i = i + 1;
    }
    (false, Ghost(0))
}
// triv: { (false, Ghost(0)) }

// item: Q03.X2v S13
// uses: witness
// need: pub proof fn lemma_exists_wf_pair()
// need: exists|s: Seq<u64>| seq_wf(s) && s.len() == 2
/// **X2.** Some well-formed limb sequence has two limbs. Reference: the witness
/// `seq![0u64, 1u64]` (its top limb is 1, so it is canonical), named in an `assert` that
/// states both conjuncts.
pub proof fn lemma_exists_wf_pair()
    ensures
        exists|s: Seq<u64>| seq_wf(s) && s.len() == 2,
{
    assert(seq_wf(seq![0u64, 1u64]) && seq![0u64, 1u64].len() == 2);
}

// item: Q03.X3v S7
// uses: exec-check, modes
// need: pub fn checked_twice(x: u64) -> (r: Option<u64>)
// need: r.is_some() <==> 2 * x <= u64::MAX
// need: r.is_some() ==> r.unwrap() == twice_spec(x as int)
// pair: Q03.X3d
/// **X3.** Checked doubling. Reference: the runtime test `x <= u64::MAX / 2` is
/// equivalent to the spec's `2 * x <= u64::MAX` and keeps `x * 2` from overflowing.
pub fn checked_twice(x: u64) -> (r: Option<u64>)
    ensures
        r.is_some() <==> 2 * x <= u64::MAX,
        r.is_some() ==> r.unwrap() == twice_spec(x as int),
{
    if x <= u64::MAX / 2 {
        Some(x * 2)
    } else {
        None
    }
}
// triv: { None }

} // verus!
