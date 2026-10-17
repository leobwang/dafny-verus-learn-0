//! # Q13 — exit, Verus half (closed book, timed)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 1 hole (X1, 20 minutes); the Dafny exit file
//! (dafny/Q/Q13_PracticeIIA/exit/Q13_Exit.dfy) ships with none. Score it with
//!
//!     scripts/firsttry.sh Q13 --exit
//!
//! Threshold: the 1 exit item must pass. The first full run (the block attempted) is the
//! score; repair the block afterwards, after which the strict gate covers this file too.
//! This file is never `mod`-declared and is in no build: work it with `scripts/vcheck
//! verus/q/q13_practice_iia/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

verus! {

// item: Q13.X1v S4
// need: pub proof fn lemma_value_below_top(s: Seq<u64>)
// need: seq_to_nat(s) < (s.last() + 1) * weight((s.len() - 1) as nat)
// form: no-nl
/// **X1.** A sequence's value is below its top limb plus one, times the place value of the
/// top limb. Prove it: no skeleton, and no `nonlinear_arith`.
pub proof fn lemma_value_below_top(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) < (s.last() + 1) * weight((s.len() - 1) as nat),
{
    #[verifier::proof_note("Q13.X1v")] assume(false);  // HOLE: replace this line
}

} // verus!
