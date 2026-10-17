//! # Q12 — Lab 1: the hand part, Verus (Exercises)
//!
//! The module `lab1_hand` of the crate `q12_practice_ic` (declared in src/lib.rs). Imports:
//! the given spine (`use qg_bignat_l5::*;`), the vstd prelude and `core::cmp::Ordering`,
//! nothing else.
//!
//! The hand part of Lab 1 (QPLAN §22.5): the four items below and their Dafny partners in
//! dafny/Q/Q12_PracticeIC/std/Q12_Lab1Hand.dfy, done closed book (keep the chapter, the
//! other exercise files, search tools and /tutor closed; the given spine may be open), 12
//! minutes each, BEFORE any Lab 1 run. Some of them are also tasks the agents get in the
//! lab's local stratum, so your own hit rate can stand beside each arm's on the same tasks.
//! Time each item from its first edit; when its 12 minutes are up, write its row in the
//! HAND block at the end of the Dafny hand file (verified within the time, yes or no, and
//! the minutes it took), then finish it untimed. The lab's acceptance needs at least 3 of
//! the 4 within time in each language.
//!
//! Done = `scripts/vcheck --gate verus/q/q12_practice_ic` prints only the summary line and
//! exits 0 and `scripts/vaudit verus/q/q12_practice_ic` reports no finding (the crate's
//! gate covers this file and src/lib.rs together).
//!
//! This file ships with exactly 4 holes: H4, H5, H6 and H7, each counted by
//! `scripts/vcheck`.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l5::*;

verus! {

// item: Q12.H4v S12
// uses: lemma-recursion, forall
// pair: Q12.H4d
/// **H4.** The value is monotone in each limb: a limb sequence that is limb by limb at most
/// another of the same length has at most its value.
pub proof fn lemma_seq_to_nat_mono(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == b.len(),
        forall|i: int| 0 <= i < b.len() ==> a[i] <= b[i],
    ensures
        seq_to_nat(a) <= seq_to_nat(b),
    decreases a.len(),
{
    #[verifier::proof_note("Q12.H4v")] assume(false);  // HOLE: replace this line
}

// item: Q12.H5v S12
// uses: exec-check, lemma-call
/// **H5.** Is a canonical number zero? Decide it from the limbs, and prove the answer.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn is_zero(a: &BigNat) -> (r: bool)
    requires
        a.wf(),
    ensures
        r == (a.to_nat() == 0),
{
    unimplemented!()
}

// item: Q12.H6v S12
// uses: exec-check
/// **H6.** Are two canonical numbers equal in value?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn eq_big(a: &BigNat, b: &BigNat) -> (r: bool)
    requires
        a.wf(),
        b.wf(),
    ensures
        r == (a.to_nat() == b.to_nat()),
{
    unimplemented!()
}

// item: Q12.H7v S12
// uses: lemma-call
/// **H7.** A number of limbs that bounds the value. No precondition: any limb sequence.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn size_bound(a: &BigNat) -> (r: usize)
    ensures
        a.to_nat() < weight(r as nat),
{
    unimplemented!()
}

} // verus!
