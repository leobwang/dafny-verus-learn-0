//! # Q15 — Practice II-C: the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q15_practice_iic/src/lib.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise crate; every hole is filled and every check is live. Each item uses at most
//! the one helper the tier allows; H2's refutation sits under REFUTATIONS. The `cfree:`
//! lines are the construct-free answers the author measured.
//!
//! Silent under `scripts/vcheck --ref` on the crate.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

mod lab2_specs;

verus! {

// =========================================================================================
// Holes
// =========================================================================================

// HELPERS (Q15.H1v): at most one proof fn of your own, here.

// item: Q15.H1v S11
// uses: trigger-rewrite
// pair: Q15.H1d
// form: trigger, stable
// cfree: { lemma_weight_succ(n); lemma_weight_succ(n + 1); lemma_weight_succ(n + 2); }
/// **H1.** Stability. Three places up the place values. This attempt gives the proof one
/// quantified step, whose trigger is the plain place-value term:
///
///     {
///         assert forall|k: nat| weight(k + 1) == BASE * #[trigger] weight(k) by {
///             lemma_weight_succ(k);
///         }
///     }
///
/// Paste it as the body and run `scripts/vcheck --brittleness verus/q/q15_practice_iic`;
/// write in the BRITTLENESS table below what the sweep prints. Then prove the lemma with a
/// quantified step whose trigger no instance of the step creates. The proof must be stable
/// under the same sweep and carry no resource attribute. Which terms must the proof hold
/// for your trigger to fire?
pub proof fn lemma_weight_three_up(n: nat)
    ensures
        weight(n + 3) == BASE * (BASE * (BASE * weight(n))),
{
    assert forall|k: nat| #[trigger] weight(k + 1) == BASE * weight(k) by {
        lemma_weight_succ(k);
    }
    assert(weight(n + 1) == BASE * weight(n));
    assert(weight((n + 1) + 1) == BASE * weight(n + 1));
    assert(weight(((n + 1) + 1) + 1) == BASE * weight((n + 1) + 1));
}

// BRITTLENESS (learner-owned): the attempt, then your proof, from the sweep.
//   seed   attempt: verdict, rlimit count   yours: verdict, rlimit count
//   1
//   2
//   3

// HELPERS (Q15.H2v): at most one proof fn of your own, here.

// item: Q15.H2v S12
// uses: witness
// pair: Q15.H2d
/// **H2.** Refute, repair, prove. The lemma below ships false. First, under
/// REFUTATIONS, write a proof fn `lemma_push_lt_refuted()` (no parameters) whose `ensures`
/// says, on concrete sequences and a limb you choose, that `lemma_push_lt`'s `requires`
/// holds and its `ensures` does not; prove it. Then repair `lemma_push_lt` with the
/// smallest change that makes it true: add `requires` clauses only (its shipped clause
/// stays as it is), so that the given client `push_check` verifies with its use-site check
/// uncommented. Then prove it. Which length does the claim silently assume?
pub proof fn lemma_push_lt(a: Seq<u64>, b: Seq<u64>, x: u64)
    requires
        seq_to_nat(a) < seq_to_nat(b),
        a.len() <= b.len(),
    ensures
        seq_to_nat(a.push(x)) < seq_to_nat(b.push(x)),
{
    broadcast use group_bignat_bounds;  // did: the layers' bounds, for weight's monotonicity
    assert(a.push(x) =~= a + seq![x]);
    assert(b.push(x) =~= b + seq![x]);
    lemma_seq_to_nat_append(a, seq![x]);
    lemma_seq_to_nat_append(b, seq![x]);
    reveal_with_fuel(seq_to_nat, 2);  // did: the value of the one-limb sequence
    lemma_mul_inequality(weight(a.len()) as int, weight(b.len()) as int, x as int);
}

// REFUTATIONS (Q15.H2v): your `lemma_push_lt_refuted`, here.

/// The counterexample: [5, 0] is below [6]; with the limb 1 pushed on each, it is above.
pub proof fn lemma_push_lt_refuted()  // reference-only: the refutation the item asks for
    ensures
        seq_to_nat(seq![5u64, 0u64]) < seq_to_nat(seq![6u64]),
        seq_to_nat(seq![6u64].push(1u64)) < seq_to_nat(seq![5u64, 0u64].push(1u64)),
{
    reveal_with_fuel(seq_to_nat, 4);  // did: the values of the literal sequences
}

pub proof fn push_check(a: Seq<u64>, b: Seq<u64>)
    requires
        seq_to_nat(a) < seq_to_nat(b),
        a.len() <= b.len(),
{
    lemma_push_lt(a, b, 7);
    assert(seq_to_nat(a.push(7)) < seq_to_nat(b.push(7)));
    lemma_push_lt_refuted();
}

} // verus!
