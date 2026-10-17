//! # Q02 — exit, Verus half (closed book)
//!
//! Closed during the exit: the chapter, the exercise files (src/lib.rs of this crate,
//! dafny/Q/Q02_FirstSyntaxI/core, the specimens), later modules' files, search tools and
//! /tutor. Open, at most: the given spine (verus/given/, dafny/given/Q/).
//!
//! This file ships with exactly 3 holes (X1v, X2v, X3v). Its Dafny half,
//! dafny/Q/Q02_FirstSyntaxI/exit/Q02_Exit.dfy, ships with 1 hole and two empty blocks. This
//! file is never `mod`-declared: no build of the crate reaches it, and `scripts/vcheck`
//! verifies it on its own with the crate's dependencies.
//!
//! Score: `scripts/firsttry.sh Q02 --exit` judges every block of both files, each on its
//! own, and records the first run on which every block holds an attempt (a guess counts; a
//! hole does not). The threshold is 5 of the 6 blocks. That first run is the score; repair
//! every block afterwards, and from then on the strict gate covers this file too. A block
//! passes when it is attempted and has no error, no hole, no commented check, and every
//! `need:` line of its marker in its code.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// item: Q02.X1v S4
// uses: invariant, decreases, quantified-ensures
// need: pub fn all_nonzero(v: &Vec<u64>) -> (b: bool)
// need: b == (forall|i: int| 0 <= i < v.len() ==> v@[i] != 0)
/// **X1v.** Whether every limb of `v` is non-zero. Implement it with a loop.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn all_nonzero(v: &Vec<u64>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < v.len() ==> v@[i] != 0),
{
    unimplemented!()
}

// item: Q02.X2v S6
// need: pub fn bump_low(a: &mut BigNat)
// need: final(a)@ == old(a)@.update(0, (old(a)@[0] + 1) as u64)
/// **X2v.** Add one to the least significant limb of `a`, in place.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn bump_low(a: &mut BigNat)
    requires
        old(a)@.len() > 0,
        old(a)@[0] < u64::MAX,
    ensures
        final(a)@ == old(a)@.update(0, (old(a)@[0] + 1) as u64),
{
    unimplemented!()
}

// item: Q02.X3v S3
// uses: assert-by
// need: pub proof fn lemma_two_limbs(a: u64, b: u64)
// need: seq_to_nat(seq![a, b]) == a + BASE * b
/// **X3v.** The value of two limbs. Prove it with `assert … by` steps.
pub proof fn lemma_two_limbs(a: u64, b: u64)
    ensures
        seq_to_nat(seq![a, b]) == a + BASE * b,
{
    #[verifier::proof_note("Q02.X3v")] assume(false);  // HOLE: replace this line
}

} // verus!
