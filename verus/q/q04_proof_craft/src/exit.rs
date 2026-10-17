//! # Q04 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) and the pinned vstd's own
//! source may be open.
//!
//! This file ships with exactly 2 holes (X1, X2); the Dafny half
//! (dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy) ships with 2 holes. Score both halves in
//! one sitting with
//!
//!     scripts/firsttry.sh Q04 --exit
//!
//! Threshold: 3 of the 4 exit items, at least 1 in each language. The first full run
//! (every block attempted) is the score; repair every block afterwards, after which the
//! strict gate covers this file too. This file is never `mod`-declared and is in no build:
//! work it with `scripts/vcheck verus/q/q04_proof_craft/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::calc;
use qg_bignat_l3::*;

verus! {

// item: Q04.X1v S5
// uses: calc, nonlinear-arith
// need: pub proof fn lemma_limb_square(x: u64)
// need: (x as nat) * (x as nat) < weight(2)
/// **X1.** The square of a limb fits in two limbs. Prove it with a `calc!` chain, one of
/// whose steps is closed by `nonlinear_arith`.
pub proof fn lemma_limb_square(x: u64)
    ensures
        (x as nat) * (x as nat) < weight(2),
{
    #[verifier::proof_note("Q04.X1v")] assume(false);  // HOLE: replace this line
}

// item: Q04.X2v S5
// uses: broadcast-use
// need: pub fn fits_one_limb(a: &BigNat) -> (r: bool)
// need: r == (a.to_nat() < BASE)
/// **X2.** Does a BigNat fit in one limb? Implement it with no loop.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn fits_one_limb(a: &BigNat) -> (r: bool)
    requires
        a.wf(),
    ensures
        r == (a.to_nat() < BASE),
{
    unimplemented!()
}

} // verus!
