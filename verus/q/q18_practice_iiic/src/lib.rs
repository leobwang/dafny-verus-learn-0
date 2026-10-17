//! # Q18 — Practice III-C: the Verus half and the capstone crate's verified core (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l7` (`use
//! qg_bignat_l7::*;` brings all seven layers' names, the base API trait `BigNatCore`
//! among them), the vstd prelude and `vstd::arithmetic::{div_mod, mul}`, nothing else: no
//! earlier exercise crate. The layers are frozen and complete; read them, never edit them.
//!
//! How to work this file (the hard practice tier):
//! 1. Predictions first: Q18's predictions are the four build-tool deliveries of
//!    specimens/Q18/; record the first tries with `scripts/firsttry.sh Q18 --check` before
//!    you run anything they are about.
//! 2. H1 ships its statement, its code and a delivered proof (in its doc comment), nothing
//!    else. Proof fns of your own go in its `HELPERS` area, above the item.
//! 3. The capstone (the chapter's H2) builds on this crate: its STATEMENTS, CAPSTONE
//!    HELPERS and ENTRY POINTS sections, below the hole, ship empty. Your statements are
//!    written and committed in research/q18_statements.rs first, proved in src/agent.rs,
//!    and only then copied here (the chapter's ship step).
//! 4. Done = `scripts/vcheck --gate verus/q/q18_practice_iiic` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q18_practice_iiic` reports no finding,
//!    `scripts/vcheck --brittleness verus/q/q18_practice_iiic` ends with `stable`, AND
//!    `scripts/firsttry.sh Q18 --report --strict` exits 0.
//! 5. Stuck for 20 minutes? /tutor Q18.
//!
//! This file ships with exactly 1 hole (H1), counted by `scripts/vcheck` (Verus runs with
//! `--no-cheating`, which turns the hole into one counted diagnostic). Commit every
//! prediction BEFORE you run anything it is about, open later files, or read CI, the
//! registry or the plan: their checks and headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header. src/agent.rs (the
//! capstone's proof work) is never part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l7::*;

verus! {

// =========================================================================================
// Holes
// =========================================================================================

// HELPERS (Q18.H1v): proof fns of your own, here.

// item: Q18.H1v S11
// uses: proof-split
// pair: Q18.H1d
// form: stable
/// **H1.** Seed brittleness. The value modulo `BASE - 1` (that is, 18446744073709551615),
/// computed from the top limb down: each step adds one limb to the running remainder and
/// reduces, because `BASE` leaves remainder 1. A contractor delivered this proof block for
/// the loop body and reported the crate verified:
///
///     proof {
///         let t = seq_to_nat(a@.subrange(i as int + 1, n as int));
///         assert(a@.subrange(i as int, n as int).drop_first()
///             =~= a@.subrange(i as int + 1, n as int));
///         broadcast use lemma_mod_multiples_vanish, lemma_add_mod_noop_right;
///         assert(BASE * t == 18446744073709551615 * t + t);
///         assert(r2 as nat == (x as nat + r as nat) % 18446744073709551615);
///     }
///
/// Paste it in place of the hole, run `scripts/vcheck verus/q/q18_practice_iiic`, then
/// `scripts/vcheck --brittleness verus/q/q18_practice_iiic`; fill the BRITTLENESS table
/// below from what the two runs print. Then repair the proof block: the same code and
/// invariant, a proof that verifies on every seed of the sweep, and no `rlimit`
/// attribute. Which step of the delivered block leaves the solver to choose instances
/// on its own, and how do you state them instead?
pub fn cast_out(a: &BigNat) -> (r: u64)
    requires
        a.wf(),
    ensures
        r as nat == a.to_nat() % 18446744073709551615,
{
    let n = a.limbs.len();
    let mut r: u64 = 0;
    let mut i: usize = n;
    while i > 0
        invariant
            i <= n,
            n == a@.len(),
            r < 18446744073709551615,
            r as nat == seq_to_nat(a@.subrange(i as int, n as int)) % 18446744073709551615,
        decreases i,
    {
        i = i - 1;
        let x = a.limbs[i];
        let s: u128 = x as u128 + r as u128;
        let r2: u64 = (s % 18446744073709551615u128) as u64;
        proof {
            #[verifier::proof_note("Q18.H1v")] assume(false);  // HOLE: replace this line
        }
        r = r2;
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
    }
    r
}
// Hint: the delivered block hands the solver two broadcast lemmas and lets it pick their
//    instances; a stable block names the instances it needs, one fact at a time.

// BRITTLENESS (learner-owned): the delivered block, then yours, from the two runs.
//   run                  delivered: verdict, resource count   yours: verdict, resource count
//   vcheck (no seed)
//   seed 1
//   seed 2
//   seed 3

// =========================================================================================
// The capstone crate (the chapter's H2; ships empty)
// =========================================================================================

// STATEMENTS (the capstone's ship step): your trait from research/q18_statements.rs, an
// extension of `BigNatCore`, and its `impl` for `BigNat` from src/agent.rs, here.

// CAPSTONE HELPERS (the ship step): the proof fns the impl needs, from src/agent.rs, here.

// ENTRY POINTS (the ship step): one verified fn per CLI command (add, sub, mul, div, cmp),
// each a thin call into the base API or your trait, here.

} // verus!
