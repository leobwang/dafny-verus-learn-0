//! # Q12 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 1 hole (X1); the Dafny half
//! (dafny/Q/Q12_PracticeIC/exit/Q12_Exit.dfy) ships with 1 hole. Score both halves in one
//! sitting with
//!
//!     scripts/firsttry.sh Q12 --exit
//!
//! Threshold: at least 1 of the 2 exit items. The first full run (every block attempted)
//! is the score; repair every block afterwards, after which the strict gate covers this
//! file too. This file is never `mod`-declared and is in no build: work it with
//! `scripts/vcheck verus/q/q12_practice_ic/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l5::*;

verus! {

// item: Q12.X1v S11
// need: pub proof fn lemma_weight_two()
// need: weight(2) == BASE * BASE
/// **X1.** The weight of two limbs. Layer L3's `weight` is `BASE` to the power `n`.
/// Prove the instance below.
pub proof fn lemma_weight_two()
    ensures
        weight(2) == BASE * BASE,
{
    #[verifier::proof_note("Q12.X1v")] assume(false);  // HOLE: replace this line
}

} // verus!
