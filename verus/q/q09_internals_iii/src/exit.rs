//! # Q09 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 2 holes (X1, X2); the Dafny half
//! (dafny/Q/Q09_InternalsIII/exit/Q09_Exit.dfy) ships with 2 holes. Score both halves in one
//! sitting with
//!
//!     scripts/firsttry.sh Q09 --exit
//!
//! Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language. The first
//! full run (every block attempted) is the score; repair every block afterwards, after
//! which the strict gate covers this file too. Both items count only if they verify under
//! seeds 1-3 (`scripts/vcheck --brittleness` on this file) with no resource attribute; X1
//! counts only in at least two scoped `nonlinear_arith` steps, X2 only with an explicit
//! trigger. This file is never `mod`-declared and is in no build: work it with
//! `scripts/vcheck verus/q/q09_internals_iii/src/exit.rs`.
//!
//! Then fill the EXPLAIN-BACK block at the end of the Dafny exit file.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

/// Given (not an item): the sum of the limbs of a sequence, and how it adds up over a
/// concatenation, for X2.
pub open spec fn limb_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + limb_sum(s.drop_first())
    }
}

pub proof fn lemma_limb_sum_append(s: Seq<u64>, t: Seq<u64>)
    ensures
        limb_sum(s + t) == limb_sum(s) + limb_sum(t),
    decreases s.len(),
{
    if s.len() == 0 {
        assert(s + t =~= t);
    } else {
        assert((s + t).drop_first() =~= s.drop_first() + t);
        lemma_limb_sum_append(s.drop_first(), t);
    }
}

// item: Q09.X1v S11
// uses: proof-split
// need: pub proof fn lemma_product_plus_carry(x: nat, y: nat, z: nat, n: nat)
// need: x * y + z < weight(n) * weight(n)
// pair: Q09.X1d
// form: nl-steps:2, stable
/// **X1.** A product plus a carry stays below the square. Prove it in at least two scoped
/// steps, each one `nonlinear_arith` with its own `requires`, stable on seeds 1-3.
pub proof fn lemma_product_plus_carry(x: nat, y: nat, z: nat, n: nat)
    requires
        x < weight(n),
        y < weight(n),
        z < weight(n),
    ensures
        x * y + z < weight(n) * weight(n),
{
    #[verifier::proof_note("Q09.X1v")] assume(false);  // HOLE: replace this line
}

// item: Q09.X2v S11
// uses: trigger-rewrite
// need: pub proof fn lemma_sum_four(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
// need: limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d)
// need: limb_sum(s + t) == limb_sum(s) + limb_sum(t)
// need: lemma_limb_sum_append(s, t);
// pair: Q09.X2d
// form: trigger, stable
/// **X2.** The limb sum of four concatenated parts. This attempt states the append fact
/// once, for every pair of sequences, and proves it:
///
///     assert forall|s: Seq<u64>, t: Seq<u64>|
///         #![trigger limb_sum(s), limb_sum(t)]
///         limb_sum(s + t) == limb_sum(s) + limb_sum(t) by {
///         lemma_limb_sum_append(s, t);
///     }
///
/// Rewrite the trigger (keep the quantified fact and its proof), stable on seeds 1-3.
pub proof fn lemma_sum_four(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
    ensures
        limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d),
{
    #[verifier::proof_note("Q09.X2v")] assume(false);  // HOLE: replace this line
}

} // verus!
