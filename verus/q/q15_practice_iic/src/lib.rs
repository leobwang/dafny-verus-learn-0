//! # Q15 — Practice II-C: the Verus half (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l6` (`use
//! qg_bignat_l6::*;` brings all six layers' names), the vstd prelude and
//! `vstd::arithmetic::mul`, nothing else: no earlier exercise crate. The layers are frozen
//! and complete; read them, never edit them.
//!
//! How to work this file (the intermediate practice tier):
//! 1. Predictions first: the module's predictions are in the Dafny file's prediction block
//!    (dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy) and the forensic specimens
//!    (specimens/Q15/); record the first tries with `scripts/firsttry.sh Q15 --check`
//!    before you run anything they are about.
//! 2. Each item ships its statement and nothing else: no skeleton. Each item allows at
//!    most one lemma of your own, in its `HELPERS` area above the item.
//! 3. Done = `scripts/vcheck --gate verus/q/q15_practice_iic` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q15_practice_iic` reports no finding,
//!    `scripts/vcheck --brittleness verus/q/q15_practice_iic` ends with `stable`, AND
//!    `scripts/firsttry.sh Q15 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q15.
//!
//! This file ships with exactly 2 holes (H1 and H2), each counted by `scripts/vcheck`
//! (Verus runs with `--no-cheating`, which turns each hole into one counted diagnostic);
//! src/lab2_specs.rs ships 3 more (Lab 2's prose specifications). Commit every prediction
//! BEFORE you run anything it is about, open later files, or read CI, the registry or the
//! plan: their checks and headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header. The exit is the Dafny
//! exit file's one item; src/exit.rs ships no block. src/agent.rs (rung 11) and src/exit.rs
//! are never part of this crate's build.
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
    #[verifier::proof_note("Q15.H1v")] assume(false);  // HOLE: replace this line
}
// Hint: layer L3's `weight` is opaque, so every step is an instance of the quantified
//    fact; a trigger matches terms by their shape, and `n + 3` has its own shape.

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
    ensures
        seq_to_nat(a.push(x)) < seq_to_nat(b.push(x)),
{
    #[verifier::proof_note("Q15.H2v")] assume(false);  // HOLE: repair the requires, then prove
}
// Hint: a pushed limb lands at the place value of the sequence's length.

// REFUTATIONS (Q15.H2v): your `lemma_push_lt_refuted`, here.

pub proof fn push_check(a: Seq<u64>, b: Seq<u64>)
    requires
        seq_to_nat(a) < seq_to_nat(b),
        a.len() <= b.len(),
{
    // Uncomment as you go:
    // lemma_push_lt(a, b, 7);
    // assert(seq_to_nat(a.push(7)) < seq_to_nat(b.push(7)));
    // lemma_push_lt_refuted();
}

} // verus!
