//! # Q10 — exit, Verus half (closed book, timed)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 1 hole (X1, 10 minutes); the Dafny half
//! (dafny/Q/Q10_PracticeIA/exit/Q10_Exit.dfy) ships with 1 hole (X1, 10 minutes). Score
//! both halves in one sitting with
//!
//!     scripts/firsttry.sh Q10 --exit
//!
//! Threshold: 1 of the 2 exit items. The first full run (both blocks attempted) is the
//! score; repair both blocks afterwards, after which the strict gate covers this file too.
//! This file is never `mod`-declared and is in no build: work it with `scripts/vcheck
//! verus/q/q10_practice_ia/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l5::*;

verus! {

// item: Q10.X1v S1
// uses: exec-check
// need: pub fn halve_words(lo: u64, hi: u64) -> (r: (u64, u64))
// need: r.0 as nat + r.1 as nat * BASE == (lo as nat + hi as nat * BASE) / 2
/// **X1.** Halve a two-word number: `lo` is its low word and `hi` its high word, and the
/// result is the two words of half its value (rounded down), low word first. Implement it
/// so that no operation in the code can overflow.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn halve_words(lo: u64, hi: u64) -> (r: (u64, u64))
    ensures
        r.0 as nat + r.1 as nat * BASE == (lo as nat + hi as nat * BASE) / 2,
{
    unimplemented!()
}

} // verus!
