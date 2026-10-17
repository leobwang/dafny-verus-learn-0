//! # Q12 — Lab 1: the hand part, Verus (Reference Solution)
//!
//! Hole-free reference for `verus/q/q12_practice_ic/src/lab1_hand.rs` (author-only; never
//! learner-visible). Same module, imports, names, statements, item markers and order as
//! the exercise file; every hole is filled. The exec items declare their `// triv:` bodies
//! for the empty-body gate's TRIV mode, and the `cfree:` lines are their exec code without
//! the proof, which must fail.
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
    if a.len() > 0 {
        assert forall|i: int| 0 <= i < a.drop_first().len() implies a.drop_first()[i] <= b.drop_first()[i] by {
            assert(a[i + 1] <= b[i + 1]);
        }
        lemma_seq_to_nat_mono(a.drop_first(), b.drop_first());
    }
}

// item: Q12.H5v S12
// uses: exec-check, lemma-call
// cfree: { a.limbs.len() == 0 }
/// **H5.** Is a canonical number zero? Decide it from the limbs, and prove the answer.
pub fn is_zero(a: &BigNat) -> (r: bool)
    requires
        a.wf(),
    ensures
        r == (a.to_nat() == 0),
{
    if a.limbs.len() == 0 {
        true
    } else {
        proof {
            lemma_seq_to_nat_lower(a@);
            lemma_weight_zero();
            lemma_weight_mono(0, (a@.len() - 1) as nat);
        }
        false
    }
}
// triv: { false }

// item: Q12.H6v S12
// uses: exec-check
/// **H6.** Are two canonical numbers equal in value?
pub fn eq_big(a: &BigNat, b: &BigNat) -> (r: bool)
    requires
        a.wf(),
        b.wf(),
    ensures
        r == (a.to_nat() == b.to_nat()),
{
    match cmp(a, b) {
        Ordering::Equal => true,
        _ => false,
    }
}
// triv: { false }

// item: Q12.H7v S12
// uses: lemma-call
// cfree: { a.limbs.len() }
/// **H7.** A number of limbs that bounds the value. No precondition: any limb sequence.
pub fn size_bound(a: &BigNat) -> (r: usize)
    ensures
        a.to_nat() < weight(r as nat),
{
    proof {
        lemma_seq_to_nat_upper(a@);
    }
    a.limbs.len()
}
// triv: { 0 }

} // verus!
