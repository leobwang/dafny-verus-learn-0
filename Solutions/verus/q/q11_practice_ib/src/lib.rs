//! # Q11 — Practice I-B (Reference Solution)
//!
//! Hole-free reference for `verus/q/q11_practice_ib/src/lib.rs` (author-only; never
//! learner-visible). Same crate root, imports, names, statements, item markers and order
//! as the exercise file; every hole is filled and every check is live. The exec items
//! declare their `// triv:` bodies for the empty-body gate's TRIV mode. Silent under
//! `scripts/vcheck --ref` on the crate.
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
    /// **H3v.** Add one word to the total and count the step; refuse, changing nothing,
    /// when the step count is full.
    ///
    /// Reference: test the count first and return `Err` before any write; otherwise L3's
    /// `add_limb` gives a canonical total with the new value, and the count goes up by one.
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
        if self.steps == u64::MAX {
            return Err(AccError::Overflow);
        }
        self.total = add_limb(&self.total, x);
        self.steps = self.steps + 1;
        Ok(())
    }
    // triv: { Ok(()) }

    // item: Q11.H4v S6
    // uses: mut-ref, result, old
    /// **H4v.** Take the total out when it is at least `limit`, resetting the accumulator;
    /// refuse, changing nothing, when it is smaller.
    ///
    /// Reference: compare with L4's `cmp` and `match` on its `Ordering` (an `==` on
    /// `Ordering` tells the verifier nothing); on `Less` return `Err` before any write.
    /// Otherwise swap an empty `BigNat` in for the total (`core::mem::swap` has a
    /// specification at the pin; `mem::replace` has none), zero the count, and assert that
    /// the empty limb sequence has the value 0.
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
        match cmp(&self.total, limit) {
            Ordering::Less => {
                return Err(AccError::TooSmall);
            },
            _ => {},
        }
        let mut out = BigNat { limbs: Vec::new() };
        core::mem::swap(&mut out, &mut self.total);
        self.steps = 0;
        proof {
            assert(seq_to_nat(self.total@) == 0);
        }
        Ok(out)
    }
    // triv: { Err(AccError::TooSmall) }
}

fn acc_check(a: &mut Acc, limit: &BigNat)
    requires
        old(a).total.wf(),
        old(a).steps == 3,
        limit.wf(),
{
    // reference-only: live in the twin, commented in the learner crate
    let r = a.add_word(5);
    assert(r is Ok && a.steps == 4 && a.total.wf());
    let t = a.take_if_at_least(limit);
    match t {
        Ok(v) => {
            assert(v.to_nat() >= limit.to_nat() && a.total.to_nat() == 0 && a.steps == 0);
        },
        Err(_) => {
            assert(a.steps == 4);
        },
    }
}

// =========================================================================================
// Modes: exec code, ghost facts
// =========================================================================================

// item: Q11.H6v S7
// uses: modes, ghost, assert
/// **H6v.** The value of a number of at most two limbs, as one `u128`.
///
/// Reference: one exec branch per length. In each, a proof block shows the verifier the
/// value of the limb sequence: the tail of a one-limb sequence (and the tail's tail of a
/// two-limb one) is empty, with the value 0, so `seq_to_nat` unfolds to the limbs. The
/// exec arithmetic is in `u128`, where the two-limb sum cannot overflow.
pub fn value_two(a: &BigNat) -> (r: u128)
    requires
        a.wf(),
        a@.len() <= 2,
    ensures
        r as nat == a.to_nat(),
{
    if a.limbs.len() == 0 {
        0
    } else if a.limbs.len() == 1 {
        proof {
            assert(a@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(a@.drop_first()) == 0);
        }
        a.limbs[0] as u128
    } else {
        proof {
            let t = a@.drop_first();
            assert(t.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(t.drop_first()) == 0);
            assert(seq_to_nat(t) == t[0] as nat);
        }
        a.limbs[0] as u128 + (a.limbs[1] as u128) * 0x1_0000_0000_0000_0000u128
    }
}
// triv: { 0 }

fn value_two_check(a: &BigNat)
    requires
        a.wf(),
        a@.len() <= 2,
        a.to_nat() > 5,
{
    // reference-only: live in the twin, commented in the learner crate
    let r = value_two(a);
    assert(r > 5);
}

} // verus!
