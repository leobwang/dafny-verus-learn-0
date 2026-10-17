//! # Q13 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q13_practice_iia/src/exit.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and `need:` lines as
//! the exit file; the block is proved. Silent under `scripts/vcheck --ref`.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

verus! {

// item: Q13.X1v S4
// need: pub proof fn lemma_value_below_top(s: Seq<u64>)
// need: seq_to_nat(s) < (s.last() + 1) * weight((s.len() - 1) as nat)
// form: no-nl
// cfree: { let p = s.drop_last(); let w = weight((s.len() - 1) as nat) as int; assert(s =~= p + seq![s.last()]); lemma_seq_to_nat_append(p, seq![s.last()]); assert(seq![s.last()].drop_first() =~= Seq::<u64>::empty()); assert(seq_to_nat(seq![s.last()].drop_first()) == 0); lemma_seq_to_nat_upper(p); assert(seq_to_nat(s) < (s.last() + 1) * w) by (nonlinear_arith) requires seq_to_nat(s) == seq_to_nat(p) + w * s.last(), seq_to_nat(p) < w; }
/// **X1.** A sequence's value is below its top limb plus one, times the place value of the
/// top limb. Prove it: no skeleton, and no `nonlinear_arith`.
pub proof fn lemma_value_below_top(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) < (s.last() + 1) * weight((s.len() - 1) as nat),
{
    let p = s.drop_last();
    let w = weight((s.len() - 1) as nat) as int;
    assert(s =~= p + seq![s.last()]);
    lemma_seq_to_nat_append(p, seq![s.last()]);
    assert(seq![s.last()].drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(seq![s.last()].drop_first()) == 0);
    lemma_seq_to_nat_upper(p);
    lemma_mul_is_distributive_add_other_way(w, s.last() as int, 1);
    lemma_mul_is_commutative(w, s.last() as int);
}

} // verus!
