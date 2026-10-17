//! # Q02 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q02_first_syntax_i/src/exit.rs` (author-only): every
//! block written out and every `need:` line met. Never `mod`-declared, as in the learner
//! crate. Silent under `scripts/vcheck --ref`. The evidence is in
//! Solutions/plans/Q02-author-notes.md.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// item: Q02.X1v S4
// uses: invariant, decreases, quantified-ensures
// need: pub fn all_nonzero(v: &Vec<u64>) -> (b: bool)
// need: b == (forall|i: int| 0 <= i < v.len() ==> v@[i] != 0)
/// **X1v.** Whether every limb of `v` is non-zero.
/// (Reference) A scan whose invariant says every limb before `i` is non-zero; the early
/// `return false` is justified by the limb at `i`, the final `true` by the invariant at
/// `i == v.len()`.
pub fn all_nonzero(v: &Vec<u64>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < v.len() ==> v@[i] != 0),
{
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            forall|j: int| 0 <= j < i ==> v@[j] != 0,
        decreases v.len() - i,
    {
        if v[i] == 0 {
            return false;
        }
        i = i + 1;
    }
    true
}

// item: Q02.X2v S6
// need: pub fn bump_low(a: &mut BigNat)
// need: final(a)@ == old(a)@.update(0, (old(a)@[0] + 1) as u64)
/// **X2v.** Add one to the least significant limb of `a`, in place.
/// (Reference) Read the limb, then write it back through the `&mut` with `set`; the
/// `requires` rules out the overflow of `x + 1`.
pub fn bump_low(a: &mut BigNat)
    requires
        old(a)@.len() > 0,
        old(a)@[0] < u64::MAX,
    ensures
        final(a)@ == old(a)@.update(0, (old(a)@[0] + 1) as u64),
{
    let x = a.limbs[0];
    a.limbs.set(0, x + 1);
}

// item: Q02.X3v S3
// uses: assert-by
// need: pub proof fn lemma_two_limbs(a: u64, b: u64)
// need: seq_to_nat(seq![a, b]) == a + BASE * b
/// **X3v.** The value of two limbs.
/// (Reference) `seq_to_nat` unfolds once on `seq![a, b]`; the tail's value is `b`, which
/// takes its own steps: the tail is `seq![b]`, whose tail is empty, whose value is 0.
pub proof fn lemma_two_limbs(a: u64, b: u64)
    ensures
        seq_to_nat(seq![a, b]) == a + BASE * b,
{
    let s = seq![a, b];
    assert(seq_to_nat(s.drop_first()) == b as nat) by {
        assert(s.drop_first() =~= seq![b]);
        assert(seq![b].drop_first() =~= Seq::<u64>::empty());
        assert(seq_to_nat(Seq::<u64>::empty()) == 0);
    }
}

} // verus!
