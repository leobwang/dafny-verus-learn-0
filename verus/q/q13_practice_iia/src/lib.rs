//! # Q13 — Practice II-A: the Verus half (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l6` (`use
//! qg_bignat_l6::*;` brings all six layers' names), the vstd prelude and
//! `vstd::arithmetic::mul`, nothing else: no earlier exercise crate. The layers are frozen
//! and complete; read them, never edit them.
//!
//! How to work this file (the intermediate practice tier):
//! 1. Predictions first: the module's prediction is in the Dafny file's prediction block
//!    (dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy; its answer goes in
//!    slots/Q13.slots); record the first try with `scripts/firsttry.sh Q13 --check`
//!    before you run anything it is about.
//! 2. Each item ships its statement and nothing else: no skeleton. Each item allows at
//!    most one lemma of your own, in its `HELPERS` area above the item. H3 is a prose
//!    item: its statement is yours too.
//! 3. Done = `scripts/vcheck --gate verus/q/q13_practice_iia` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q13_practice_iia` reports no finding, AND
//!    `scripts/firsttry.sh Q13 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q13.
//!
//! This file ships with exactly 3 holes (H1, H3 and H4), each counted by `scripts/vcheck`
//! (Verus runs with `--no-cheating`, which turns each hole into one counted diagnostic).
//! Commit every prediction BEFORE you run anything it is about, open later files, or read
//! CI, the registry or the plan: their checks and headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header. Exit (closed book,
//! timed): src/exit.rs, scored once by `scripts/firsttry.sh Q13 --exit`; src/exit.rs is
//! never part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

verus! {

// =========================================================================================
// Holes
// =========================================================================================

// HELPERS (Q13.H1v): at most one proof fn of your own, here.

// item: Q13.H1v S1
// uses: invariant, ghost, lemma-recursion
/// **H1.** Subtraction with a borrow chain: one pass over the limbs from the low limb,
/// each step subtracting the next limb of `b` (0 past its end) and the borrow, borrowing
/// from the next limb when that goes below zero. No skeleton; layer L6's `normalize` is
/// available for the result. What ghost record of the borrows lets one lemma tie the
/// limbs you wrote to the two values?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() - b.to_nat(),
{
    unimplemented!()
}
// Hint: a canonical `b` no larger than `a` has no more limbs than `a`: the layers'
//    bounds say why.

fn sub_check(a: &BigNat, b: &BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
{
    // Uncomment as you go:
    // let r = sub(a, b);
    // assert(r.to_nat() + b.to_nat() == a.to_nat());
}

// HELPERS (Q13.H3v): at most one proof fn of your own, here.

// item: Q13.H3v S2
// uses: lemma-recursion, forall
// prose: lemma_lt_at_any
/// **H3.** Prose item. *Read a missing limb as zero. If two limb sequences — not
/// necessarily canonical, possibly of different lengths — agree at every position above
/// some index, and at that index the first one's limb is the smaller, then the first one's
/// value is the smaller.*
///
/// State it as `pub proof fn lemma_lt_at_any(a: Seq<u64>, b: Seq<u64>, i: int)`, above
/// the client `prose_use_site`, and prove it (layer L3's `limb_at` reads a missing limb as
/// zero). Then uncomment the use-site check, write one non-vacuity witness in
/// `prose_witness` (a call whose `requires` hold), and delete the client's assume.
pub proof fn prose_use_site(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == 3,
        b.len() == 2,
        a[1] < b[1],
        a[2] == 0,
{
    #[verifier::proof_note("Q13.H3v")] assume(false);  // HOLE: delete once lemma_lt_at_any is stated and proved
    // Uncomment as you go:
    // lemma_lt_at_any(a, b, 1);
    // assert(seq_to_nat(a) < seq_to_nat(b));
}

/// Your non-vacuity witness for `lemma_lt_at_any`: one call whose `requires` hold.
pub proof fn prose_witness() {
}

// HELPERS (Q13.H4v): at most one proof fn of your own, here.

// item: Q13.H4v S5
// uses: library-call
// pair: Q13.H4d
// form: no-nl
/// **H4.** The value of `n` equal non-zero limbs, by `vstd::arithmetic::mul` (imported):
/// with no `nonlinear_arith`, every product step is a named lemma. Which steps need one?
pub proof fn lemma_repeat_value(d: u64, n: nat)
    requires
        0 < d,
    ensures
        seq_to_nat(Seq::new(n, |i: int| d)) * (BASE - 1) == d * (weight(n) - 1),
    decreases n,
{
    #[verifier::proof_note("Q13.H4v")] assume(false);  // HOLE: replace this line
}
// Hint: layer L3's `weight` is opaque; its two equations are lemmas.

} // verus!
