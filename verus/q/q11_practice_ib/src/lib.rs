//! # Q11 — Practice I-B (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l5` (`use
//! qg_bignat_l5::*;` brings all five layers' names), the vstd prelude and
//! `core::cmp::Ordering`, nothing else: no earlier exercise crate. The layers are frozen
//! and complete; read them, never edit them. The crate's second file is src/perm.rs (the
//! module `perm`, declared below), which also uses vstd's permissioned cells.
//!
//! How to work this file (the order is the module's; the Dafny file's header,
//! dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy, gives it in full):
//! 1. Predictions first: Q11's two predictions are in the Dafny file's prediction block;
//!    commit both, and record the first tries with `scripts/firsttry.sh Q11 --check`,
//!    before you run anything they are about.
//! 2. Replace each hole (H3, H4, then H6), then uncomment the check beneath it; H10 is in
//!    src/perm.rs. Read the hint only when stuck.
//! 3. Done = `scripts/vcheck --gate verus/q/q11_practice_ib` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q11_practice_ib` reports no finding, AND
//!    `scripts/firsttry.sh Q11 --report --strict` exits 0. The crate's gate covers this
//!    file and src/perm.rs together; `scripts/specfreeze --check Q11` reports no change.
//! 4. Stuck for 20 minutes? /tutor Q11.
//!
//! This file ships with exactly 3 holes: H3, H4 and H6, each counted by `scripts/vcheck`
//! (Verus runs with `--no-cheating`, which turns each hole into one counted diagnostic);
//! src/perm.rs ships 1. Item kinds and the slot protocol are in the Dafny file's header.
//! Exit (closed book): src/exit.rs here and the Dafny exit file, scored once by
//! `scripts/firsttry.sh Q11 --exit`; src/exit.rs is never part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l5::*;

mod perm;

verus! {

// =========================================================================================
// A `&mut self` API that returns a `Result`
// =========================================================================================

// Given (not items): the error type and an accumulator of words.
pub enum AccError {
    Overflow,
    TooSmall,
}

pub struct Acc {
    pub total: BigNat,
    pub steps: u64,
}

impl Acc {
    // item: Q11.H3v S6
    // uses: mut-ref, result, old
    /// **H3v.** Add one word to the total and count the step; refuse with `Err`, changing
    /// nothing, when the step count is already `u64::MAX`. The whole contract ships: write
    /// the body. Which call of the layers adds a word to a `BigNat`, and where must the
    /// refusal happen for the `Err` clause to hold?
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn add_word(&mut self, x: u64) -> (r: Result<(), AccError>)
        requires
            old(self).total.wf(),
        ensures
            final(self).total.wf(),
            r is Ok <==> old(self).steps < u64::MAX,
            r is Ok ==> final(self).total.to_nat() == old(self).total.to_nat() + x
                && final(self).steps == old(self).steps + 1,
            r is Err ==> final(self).total@ == old(self).total@ && final(self).steps
                == old(self).steps,
    {
        unimplemented!()
    }
    // Hint: an early `return` leaves the rest of the body unrun.

    // item: Q11.H4v S6
    // uses: mut-ref, result, old
    /// **H4v.** Take the total out when it is at least `limit` (`Ok` with the old total),
    /// resetting the accumulator to zero total and zero steps; refuse with `Err`, changing
    /// nothing, when the total is smaller. The contract ships; L4's `cmp` is available. How
    /// do you move a `BigNat` out of `*self` and leave a valid one behind?
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn take_if_at_least(&mut self, limit: &BigNat) -> (r: Result<BigNat, AccError>)
        requires
            old(self).total.wf(),
            limit.wf(),
        ensures
            final(self).total.wf(),
            r is Ok <==> old(self).total.to_nat() >= limit.to_nat(),
            r is Ok ==> r->Ok_0.wf() && r->Ok_0.to_nat() == old(self).total.to_nat()
                && final(self).total.to_nat() == 0 && final(self).steps == 0,
            r is Err ==> final(self).total@ == old(self).total@ && final(self).steps
                == old(self).steps,
    {
        unimplemented!()
    }
    // Hint: what does the verifier learn from `r == Ordering::Less`, and what from a
    //    `match` on `r`?
}

fn acc_check(a: &mut Acc, limit: &BigNat)
    requires
        old(a).total.wf(),
        old(a).steps == 3,
        limit.wf(),
{
    // Uncomment as you go:
    // let r = a.add_word(5);
    // assert(r is Ok && a.steps == 4 && a.total.wf());
    // let t = a.take_if_at_least(limit);
    // match t {
    //     Ok(v) => {
    //         assert(v.to_nat() >= limit.to_nat() && a.total.to_nat() == 0 && a.steps == 0);
    //     },
    //     Err(_) => {
    //         assert(a.steps == 4);
    //     },
    // }
}

// =========================================================================================
// Modes: exec code, ghost facts
// =========================================================================================

// item: Q11.H6v S7
// uses: modes, ghost, assert
/// **H6v.** The value of a number of at most two limbs, as one `u128`. The exec code
/// computes in `u128`; the verifier must also see why that value is `a.to_nat()`. What does
/// `seq_to_nat` (layer L1) unfold to on a sequence of one or two limbs, and what must a
/// proof block state for it to finish?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn value_two(a: &BigNat) -> (r: u128)
    requires
        a.wf(),
        a@.len() <= 2,
    ensures
        r as nat == a.to_nat(),
{
    unimplemented!()
}
// Hint: the unfolding stops only at the empty sequence: what does the verifier need to
//    know about the tail of a one-limb sequence?

fn value_two_check(a: &BigNat)
    requires
        a.wf(),
        a@.len() <= 2,
        a.to_nat() > 5,
{
    // Uncomment as you go:
    // let r = value_two(a);
    // assert(r > 5);
}

} // verus!
