//! # Q04 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q04_proof_craft/src/exit.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the exit
//! file; every hole is filled. Silent under `scripts/vcheck --ref`.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::calc;
use qg_bignat_l3::*;

verus! {

// item: Q04.X1v S5
// uses: calc, nonlinear-arith
// need: pub proof fn lemma_limb_square(x: u64)
// need: (x as nat) * (x as nat) < weight(2)
/// **X1.** The square of a limb fits in two limbs.
///
/// Reference: the weight equations give `weight(1) == BASE` and
/// `weight(2) == BASE * weight(1)`; the chain's first step, `x * x < BASE * BASE`, is a
/// nonlinear assertion with `x < BASE` in its `requires`, and two equalities fold
/// `BASE * BASE` into `weight(2)`.
pub proof fn lemma_limb_square(x: u64)
    ensures
        (x as nat) * (x as nat) < weight(2),
{
    lemma_weight_zero();
    lemma_weight_succ(0);
    lemma_weight_succ(1);
    calc! {
        (<)
        (x as nat) * (x as nat); {
            // did: the square of a limb is below BASE * BASE
            assert((x as nat) * (x as nat) < BASE * BASE) by (nonlinear_arith)
                requires
                    (x as nat) < BASE,
            ;
        }
        BASE * BASE;
        (==) {}
        BASE * weight(1);
        (==) {}
        weight(2);
    }
}

// item: Q04.X2v S5
// uses: broadcast-use
// need: pub fn fits_one_limb(a: &BigNat) -> (r: bool)
// need: r == (a.to_nat() < BASE)
/// **X2.** Does a BigNat fit in one limb?
///
/// Reference: for canonical limbs, the value is below `BASE` exactly when there is at most
/// one limb. L3's bounds group gives both directions: at most one limb means a value below
/// `weight(1) == BASE`; two or more limbs mean a value at least `weight(1)`. The weight
/// equations pin `weight(1)`.
pub fn fits_one_limb(a: &BigNat) -> (r: bool)
    requires
        a.wf(),
    ensures
        r == (a.to_nat() < BASE),
{
    broadcast use group_bignat_bounds;  // did: the value bounds of one limb and of two or more

    proof {
        lemma_weight_zero();
        lemma_weight_succ(0);
    }
    a.limbs.len() <= 1
}
// triv: { false }

} // verus!
