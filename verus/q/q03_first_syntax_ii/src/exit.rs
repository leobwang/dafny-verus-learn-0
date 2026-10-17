//! # Q03 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 3 holes (X1, X2, X3); the Dafny half
//! (dafny/Q/Q03_FirstSyntaxII/exit/Q03_Exit.dfy) ships with 2 holes and one empty block.
//! Score both halves in one sitting with
//!
//!     scripts/firsttry.sh Q03 --exit
//!
//! Threshold: 5 of the 6 exit items. The first full run (every block attempted) is the
//! score; repair every block afterwards, after which the strict gate covers this file
//! too. This file is never `mod`-declared and is in no build: work it with
//! `scripts/vcheck verus/q/q03_first_syntax_ii/src/exit.rs`.
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
/// **X1.** Search `v` for a limb at least `b`: return whether there is one and, as a
/// ghost value, the index of one when there is.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn find_at_least(v: &Vec<u64>, b: u64) -> (r: (bool, Ghost<int>))
    ensures
        r.0 ==> 0 <= r.1@ < v.len() && v@[r.1@] >= b,
        !r.0 ==> forall|j: int| 0 <= j < v.len() ==> v@[j] < b,
{
    unimplemented!()
}

// item: Q03.X2v S13
// uses: witness
// need: pub proof fn lemma_exists_wf_pair()
// need: exists|s: Seq<u64>| seq_wf(s) && s.len() == 2
/// **X2.** Some well-formed limb sequence has exactly two limbs.
pub proof fn lemma_exists_wf_pair()
    ensures
        exists|s: Seq<u64>| seq_wf(s) && s.len() == 2,
{
    #[verifier::proof_note("Q03.X2v")] assume(false);  // HOLE: replace this line
}

// item: Q03.X3v S7
// uses: exec-check, modes
// need: pub fn checked_twice(x: u64) -> (r: Option<u64>)
// need: r.is_some() <==> 2 * x <= u64::MAX
// need: r.is_some() ==> r.unwrap() == twice_spec(x as int)
// pair: Q03.X3d
/// **X3.** Checked doubling: `Some` exactly when `2 * x` fits in a `u64`, holding
/// `twice_spec(x)`.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn checked_twice(x: u64) -> (r: Option<u64>)
    ensures
        r.is_some() <==> 2 * x <= u64::MAX,
        r.is_some() ==> r.unwrap() == twice_spec(x as int),
{
    unimplemented!()
}

} // verus!
