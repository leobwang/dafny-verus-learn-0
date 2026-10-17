//! # Q16 — Practice III-A: the Verus half (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l7` (`use
//! qg_bignat_l7::*;` brings all seven layers' names, the base API of layer L7 among
//! them), the vstd prelude, `vstd::arithmetic::mul` and `vstd::arithmetic::div_mod`,
//! nothing else: no earlier exercise crate. The layers are frozen and complete; read them,
//! never edit them.
//!
//! How to work this file (the hard practice tier; the Dafny file's header,
//! dafny/Q/Q16_PracticeIIIA/std/Q16_PracticeIIIA.dfy, gives it in full):
//! 1. The blueprint first: problem B1 of paper/Q16_problems.tex, graded by
//!    `/grade-paper Q16` before you write any proof here.
//! 2. Each problem ships its statement and nothing else: the invariants, the lemmas you
//!    invent (two to four per problem) and their order are yours. The lemmas go in the
//!    `HELPERS` area below, statement and proof.
//! 3. Done = `scripts/vcheck --gate verus/q/q16_practice_iiia` prints only the summary
//!    line and exits 0, `scripts/vaudit verus/q/q16_practice_iiia` reports no finding, AND
//!    `scripts/firsttry.sh Q16 --report --strict` exits 0 (it also runs H3's speed test);
//!    then `/review-code Q16` and `/grade-paper Q16 --post`.
//! 4. Stuck for 20 minutes? /tutor Q16.
//!
//! This file ships with exactly 2 holes (H2 and H3's Verus half), each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one
//! counted diagnostic). No prediction and no exit file.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l7::*;

verus! {

// =========================================================================================
// HELPERS: the lemmas of your blueprint, here (statements and proofs).
// =========================================================================================

// =========================================================================================
// H2: division by one limb
// =========================================================================================

// item: Q16.H2v S4
// uses: invariant, ghost, library-call, nonlinear-arith
// form: loop-dir:i:down
/// **H2.** Division of a BigNat by one machine word, from the top limb down: a counter
/// `i` that steps down over the limbs, one quotient limb per step, and a remainder below
/// `d` carried down. The loop invariant and the lemmas under it are yours (the blueprint's,
/// B1). Layer L6's `normalize` is available for the quotient. Which equation between
/// values holds at every step?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn div_limb(a: &BigNat, d: u64) -> (res: (BigNat, u64))
    requires
        a.wf(),
        d > 0,
    ensures
        res.0.wf(),
        res.1 < d,
        a.to_nat() == res.0.to_nat() * d + res.1,
{
    unimplemented!()
}

fn div_limb_check(a: &BigNat, d: u64)
    requires
        a.wf(),
        d > 0,
{
    // Uncomment as you go:
    // let (q, r) = div_limb(a, d);
    // assert(q.to_nat() * d + r == a.to_nat());
}

// =========================================================================================
// H3, the Verus half (the Dafny half is MulLoop, in the Dafny file)
// =========================================================================================

// item: Q16.H3v S1
// uses: invariant, lemma-call, property-test
// pair: Q16.H3d
// form: no-call:big_add, no-call:plus, no-adder
/// **H3 (the Verus half).** Full multiplication, schoolbook and in place: one result
/// vector, and one pass per limb of `b` that adds that limb's row of products into the
/// vector at the limb's offset, with its own carry. No whole-number addition per row:
/// layer L4's `big_add` and `NatLike::plus` are not called here or in a helper this item
/// calls. Then uncomment the speed test after `verus!` and run it with
/// `scripts/vcheck --test verus/q/q16_practice_iiia`: it multiplies two four-limb
/// factors, which a method that adds `a` to itself `b` times cannot finish. What does each
/// loop's invariant say about the value of the vector so far?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn mul(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * b.to_nat(),
{
    unimplemented!()
}

fn mul_check(a: &BigNat, b: &BigNat)
    requires
        a.wf(),
        b.wf(),
{
    // Uncomment as you go:
    // let r = mul(a, b);
    // assert(r.to_nat() == a.to_nat() * b.to_nat());
}

} // verus!

// H3's speed test: uncomment it once `mul` is proved, then run
// `scripts/vcheck --test verus/q/q16_practice_iiia`.
// Uncomment as you go:
// #[cfg(test)]
// mod speed {
//     use super::*;
//
//     #[test]
//     fn four_limb_factors() {
//         let a = BigNat { limbs: vec![u64::MAX, u64::MAX, u64::MAX, u64::MAX] };
//         let r = mul(&a, &a);
//         assert_eq!(
//             r.limbs,
//             vec![1, 0, 0, 0, u64::MAX - 1, u64::MAX, u64::MAX, u64::MAX]
//         );
//     }
//
//     #[test]
//     fn four_limb_factors_mixed() {
//         let a = BigNat {
//             limbs: vec![0x0123456789abcdef, 0xfedcba9876543210, 0x0f1e2d3c4b5a6978, 0x8796a5b4c3d2e1f0],
//         };
//         let b = BigNat {
//             limbs: vec![0xdeadbeefcafebabe, 0x1, 0xffffffff00000000, 0x7fffffffffffffff],
//         };
//         let r = mul(&a, &b);
//         assert_eq!(
//             r.limbs,
//             vec![
//                 0x7eb689f4ea447d62, 0xa4bc5861c31b35ec, 0xb734532f456bc3bf, 0x6cc47c15ced65da2,
//                 0xb2be889116e9e9fa, 0xbb9b7b5c2c0bebcc, 0x078f169d9e168f07, 0x43cb52da61e970f8,
//             ]
//         );
//     }
// }
