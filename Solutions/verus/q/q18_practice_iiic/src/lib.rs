//! # Q18 — Practice III-C: the Verus half and the capstone crate's verified core (Reference Solution)
//!
//! Hole-free reference for `verus/q/q18_practice_iiic/src/lib.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise crate; the hole is filled with a repair that names each instance it needs and
//! is stable on seeds 1-3. The `cfree:` line is the delivered block the item quotes, laid
//! into the whole body (it fails at the pin or the `stable` form); the `triv:` line is the
//! exec item's trivial body. The capstone sections stay empty here: their reference is the
//! agent twin's (Solutions/verus/q/q18_practice_iiic/src/agent.rs).
//!
//! Silent under `scripts/vcheck --ref` on the crate.
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
// cfree: { let n = a.limbs.len(); let mut r: u64 = 0; let mut i: usize = n; while i > 0 invariant i <= n, n == a@.len(), r < 18446744073709551615, r as nat == seq_to_nat(a@.subrange(i as int, n as int)) % 18446744073709551615, decreases i, { i = i - 1; let x = a.limbs[i]; let s: u128 = x as u128 + r as u128; let r2: u64 = (s % 18446744073709551615u128) as u64; proof { let t = seq_to_nat(a@.subrange(i as int + 1, n as int)); assert(a@.subrange(i as int, n as int).drop_first() =~= a@.subrange(i as int + 1, n as int)); broadcast use lemma_mod_multiples_vanish, lemma_add_mod_noop_right; assert(BASE * t == 18446744073709551615 * t + t); assert(r2 as nat == (x as nat + r as nat) % 18446744073709551615); } r = r2; } proof { assert(a@.subrange(0, n as int) =~= a@); } r }
// triv: { 0 }
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
            let t = seq_to_nat(a@.subrange(i as int + 1, n as int));
            let m: int = 18446744073709551615;
            assert(a@.subrange(i as int, n as int).drop_first()
                =~= a@.subrange(i as int + 1, n as int));
            assert(seq_to_nat(a@.subrange(i as int, n as int)) == x as nat + BASE * t);
            assert(BASE * t == m * t + t);
            lemma_mod_multiples_vanish(t as int, x + t, m);
            assert((x + BASE * t) % m == (x + t) % m);
            lemma_add_mod_noop_right(x as int, t as int, m);
            assert((x + t) % m == (x + r) % m);
            assert(r2 == (x + r) % m);
        }
        r = r2;
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
    }
    r
}

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
