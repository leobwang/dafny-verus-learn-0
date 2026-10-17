//! # Q09 — Internals III: brittleness, forensics, gate core (Reference Solution)
//!
//! Hole-free reference for `verus/q/q09_internals_iii/src/lib.rs` (author-only; never
//! learner-visible). Same items, names, statements, item markers and order as the exercise
//! file. Every hole is filled; H1's BRITTLENESS table is filled from the module lane's own
//! runs (`Solutions/plans/Q09-code-notes.md` §2). The verdict answers of the module are in
//! `Solutions/slots/Q09.slots`, their hashes in `expected/Q09.pins`.
//!
//! The file is silent: `scripts/vcheck --ref` on its crate prints only the summary line.
//! No proof fn carries a resource attribute (T1 and H1 carry the `stable` form).
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// =========================================================================================
// The prediction block.
// =========================================================================================

// =========================================================================================
// Test-out
// =========================================================================================

// item: Q09.T1v S11
// uses: trigger-rewrite
// pair: Q09.T1d
// form: trigger, stable
// cfree: { lemma_weight_succ(m); lemma_weight_mono(0, m); lemma_weight_zero(); if m + 1 < n { lemma_weight_strict_mono(m + 1, n); lemma_weight_mono(m + 1, n); } }
/// **T1.** (test-out) `weight` grows strictly. Reference: the quantified step
/// `weight(k) < weight(k + 1)` with the trigger on the successor term: no instance creates
/// a new term of that shape, so the step fires only at the terms the proof holds (the
/// recursive call's `weight(m + 1)`). Stable under seeds 1-3; no resource attribute. The
/// `cfree:` line above is a proof with no quantifier at all: it verifies, and the `trigger`
/// form stops it (a presence check; the rubric checks that the step carries the proof).
pub proof fn lemma_weight_strict_mono(m: nat, n: nat)
    requires
        m < n,
    ensures
        weight(m) < weight(n),
    decreases n - m,
{
    assert forall|k: nat| weight(k) < #[trigger] weight(k + 1) by {
        lemma_weight_succ(k);
        lemma_weight_mono(0, k);
        lemma_weight_zero();
    }
    if m + 1 < n {
        lemma_weight_strict_mono(m + 1, n);
    }
}

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q09.W1v S11
// **W1.** Measuring a given proof: layer L4's `lemma_add_lift`. Verus checks the version of
// its Z3, so a Verus proof has one solver; stable means it verifies under seeds 1-3. The
// sweep, then the same sweep with JSON for the counts:
//     scripts/vcheck --brittleness verus/given/qg_bignat_l4
//     scripts/vcheck --brittleness --json verus/given/qg_bignat_l4
// The first prints one verdict per seed and ends with `stable`; the JSON's `spread` gives,
// per proof fn, the smallest and the largest rlimit count of the three runs, and its
// coefficient of variation. The filled BRITTLENESS table of
// `qg_bignat_l4::lemma_add_lift` (captured 2026-10-06 at the pins; your counts are those of
// your runs):
//     seed 1     seed 2     seed 3     rlimit counts
//     verified   verified   verified   252,242..354,101 (CV 14.0%)
// Read it row by row: the verdict is the same under every seed, so the proof is stable,
// while its cost moves by more than a third between seeds. A spread above 20% would be
// flagged, never gated.

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q09/)
// =========================================================================================

// item: Q09.C1v S11 write:proof-split
// C1 — card: splitting a proof into small steps.
// Jurisdiction: `by (nonlinear_arith)` proves its assertion from the facts in its own
// `requires` alone; one step over a whole product either lacks the facts or asks too much
// of the solver. Split it into steps, each one product, each scoped by the facts it needs.
// Success: `lemma_three_limb_product`, two scoped steps. Failure:
// specimens/Q09/card-c1v.rs.specimen (the same goal in one `nonlinear_arith` step with no
// `requires`). Measure both with `scripts/vcheck --json` and compare.
pub proof fn lemma_three_limb_product(x: nat, y: nat, z: nat)
    requires
        x < BASE,
        y < BASE,
        z < BASE,
    ensures
        x * y * z < BASE * BASE * BASE,
{
    // did: the two-limb product, from the two bounds alone
    assert(x * y < BASE * BASE) by (nonlinear_arith)
        requires
            x < BASE,
            y < BASE,
    ;
    // did: the third factor, from the two-limb bound and the third bound alone
    assert(x * y * z < BASE * BASE * BASE) by (nonlinear_arith)
        requires
            x * y < BASE * BASE,
            z < BASE,
    ;
}

// item: Q09.C2v S11 write:trigger-rewrite
// C2 — card: moving a trigger.
// Jurisdiction: a quantified fact is used only at the terms that match its trigger. If each
// instance creates a new term of the trigger's shape, the instances feed themselves, upward,
// and never reach the one the proof needs; moved to a term that no instance creates, the
// trigger matches only the terms the proof already holds. Success:
// `lemma_zeros_nonempty` triggers its step on `zeros(k + 1)`. Failure:
// specimens/Q09/card-c2v.rs.specimen (the same step triggered on `zeros(k)`).
#[verifier::opaque]
pub open spec fn zeros(n: nat) -> Seq<u64>
    decreases n,
{
    if n == 0 {
        Seq::<u64>::empty()
    } else {
        zeros((n - 1) as nat).push(0)
    }
}

pub proof fn lemma_zeros_succ(k: nat)
    ensures
        zeros(k + 1).len() == zeros(k).len() + 1,
{
    reveal(zeros);  // did: one unfolding of `zeros`
}

pub proof fn lemma_zeros_nonempty(m: nat)
    ensures
        zeros(m + 1).len() > 0,
{
    assert forall|k: nat| #[trigger] zeros(k + 1).len() == zeros(k).len() + 1 by {
        lemma_zeros_succ(k);
    }
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q09.H1v S11
// uses: proof-split
// pair: Q09.H1d
// form: nl-steps:2, stable
// cfree: { let p = weight(n); assert(x * y < p * p) by (nonlinear_arith) requires x < p, y < p; }
/// **H1.** Repair pair, Verus: a product of two numbers below `weight(n)` is below
/// `weight(n) * weight(n)`. The quoted attempt's one `nonlinear_arith` step has no
/// `requires`, so it sees none of the bounds and fails under every seed. Reference: two
/// steps, `x * y <= x * p` from `y < p`, then `x * p < p * p` from `x < p`, each scoped by
/// the one fact it needs. Stable under seeds 1-3; no resource attribute. The `cfree:` line
/// above (one step with both bounds) verifies too: the `nl-steps:2` form stops it, a
/// presence check of two scoped steps.
pub proof fn lemma_product_below_square(x: nat, y: nat, n: nat)
    requires
        x < weight(n),
        y < weight(n),
    ensures
        x * y < weight(n) * weight(n),
{
    let p = weight(n);
    // did: the first factor moved up to p, from y < p alone
    assert(x * y <= x * p) by (nonlinear_arith)
        requires
            y < p,
    ;
    // did: the second factor moved up to p, from x < p alone
    assert(x * p < p * p) by (nonlinear_arith)
        requires
            x < p,
    ;
}
/* BRITTLENESS (reviewed, never gated). The quoted attempt as the body, in this crate,
   through scripts/vcheck --brittleness (--json for the counts):
     seed 1     seed 2     seed 3     rlimit counts
     failed     failed     failed     1,210..1,244
   The repair above, the same sweep:
     verified   verified   verified   3,898..3,947
*/

} // verus!
