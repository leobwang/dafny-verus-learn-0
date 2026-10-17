//! # Q15 — exit, Verus half (closed book, timed)
//!
//! Q15's exit is one Dafny item (dafny/Q/Q15_PracticeIIC/exit/Q15_Exit.dfy); this file
//! ships with no block and no hole. It exists because a module's exit files come in
//! pairs. Score the exit with
//!
//!     scripts/firsttry.sh Q15 --exit
//!
//! This file is never `mod`-declared and is in no build.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l6::*;

verus! {

/// Given (not an item): an empty proof, so that the gate has one function to count (its
/// minimum is one verified function).
pub proof fn no_q15_verus_exit_item() {
}

} // verus!
