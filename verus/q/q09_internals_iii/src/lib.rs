//! # Q09 — Internals III: brittleness, forensics, gate core (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`-`qg_bignat_l4` (`use
//! qg_bignat_l4::*;` brings all four layers' names) and the vstd prelude, nothing else: no
//! earlier exercise crate. The layers are frozen and complete; read them, never edit them.
//!
//! How to work this file:
//! 1. Predictions first: every prediction of the module (the Dafny file's prediction block,
//!    the Python file's, and the forensic deliveries of specimens/Q09/); record the first
//!    tries with `scripts/firsttry.sh Q09 --check` before you run anything they are about.
//!    This file's prediction block only points to them.
//! 2. Test-out next, closed book: T1 (below) before any reading, without its hints.
//!    `scripts/firsttry.sh Q09 --check` records its first try, and refuses to while any
//!    prediction of the module is unrecorded. If both files' T1 pass on that first try, you
//!    may skip the chapter section on matching loops.
//! 3. Then H1, the repair pair's Verus half: fill its BRITTLENESS table from your own runs
//!    before you write the proof.
//! 4. Done = `scripts/vcheck --gate verus/q/q09_internals_iii` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q09_internals_iii` reports no finding,
//!    `scripts/vcheck --brittleness verus/q/q09_internals_iii` ends with `stable`, AND
//!    `scripts/firsttry.sh Q09 --report --strict` exits 0. T1 and H1 count only with no
//!    resource attribute in their blocks.
//! 5. Stuck for 20 minutes? /tutor Q09.
//!
//! This file ships with exactly 2 holes: T1 (test-out) and H1, each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one counted
//! diagnostic). Commit every prediction BEFORE you run anything it is about, open later
//! files, or read CI, the registry or the plan: their checks and headers give some
//! predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header
//! (dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy). Exit (closed book): src/exit.rs here
//! and the Dafny exit file, scored once by `scripts/firsttry.sh Q09 --exit`; src/exit.rs and
//! src/agent.rs are never part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// =========================================================================================
// The prediction block. Commit every prediction of this module before you read past this
// block (the test-out T1 included), and record the first tries:
//     scripts/firsttry.sh Q09 --check
// This file holds none: the Dafny file's prediction block holds the cross-language ones
// (P1, P2, P3), the Python file harness/q/fvh_q/gate/core.py holds P4 and P5, and
// specimens/Q09/ holds the forensic deliveries P6-P15.
// =========================================================================================

// =========================================================================================
// Test-out (closed book: after every prediction of this module is recorded, before any
// reading; `scripts/firsttry.sh Q09 --check` refuses T1's first try until then)
// =========================================================================================

// item: Q09.T1v S11
// uses: trigger-rewrite
// pair: Q09.T1d
// form: trigger, stable
/// **T1.** (test-out) `weight` (layer L3) grows strictly. Prove it with a quantified step
/// whose trigger you choose and write explicitly (an `assert forall` with `#[trigger]`); the
/// proof must be stable under `scripts/vcheck --brittleness` and carry no resource
/// attribute.
pub proof fn lemma_weight_strict_mono(m: nat, n: nat)
    requires
        m < n,
    ensures
        weight(m) < weight(n),
    decreases n - m,
{
    #[verifier::proof_note("Q09.T1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): recurse from m + 1 to n; the quantified step covers the first comparison.
// Hint(2): L3 gives `weight`'s defining equations and its monotonicity as proof fns; an
//    instance of the step mentions two weights, and a trigger on one of them makes the step
//    fire again on its own output.

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
/// **H1.** Repair pair, Verus: a product of two numbers below `weight(n)` is below
/// `weight(n) * weight(n)`. This attempt closes the goal in one step:
///
///     let p = weight(n);
///     assert(x * y < p * p) by (nonlinear_arith);
///
/// First fill the BRITTLENESS table below from your runs of the attempt (put it in as the
/// body, then `scripts/vcheck --brittleness --json verus/q/q09_internals_iii`), whatever they
/// show. Then write a proof in at least two `nonlinear_arith` steps, each scoped by its own
/// `requires` and small, that verifies under every seed, with no resource attribute.
pub proof fn lemma_product_below_square(x: nat, y: nat, n: nat)
    requires
        x < weight(n),
        y < weight(n),
    ensures
        x * y < weight(n) * weight(n),
{
    #[verifier::proof_note("Q09.H1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): what can a `nonlinear_arith` step see besides its own `requires`?
// Hint(2): move one factor up to `p` at a time.
/* BRITTLENESS (learner-owned; reviewed, never gated). The attempt as the body, in this
   crate, through scripts/vcheck --brittleness (the verdicts from its first line, the counts
   from --json's `spread`):
     seed 1     seed 2     seed 3     rlimit counts

   Your proof, the same sweep:

*/

} // verus!
