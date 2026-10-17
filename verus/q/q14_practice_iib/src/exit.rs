//! # Q14 — exit, Verus half (closed book, timed)
//!
//! Q14's exit is one Dafny item (dafny/Q/Q14_PracticeIIB/exit/Q14_Exit.dfy); this file
//! ships with no block and no hole. It exists because a module's exit files come in pairs.
//! Score the exit with
//!
//!     scripts/firsttry.sh Q14 --exit
//!
//! This file is never `mod`-declared and is in no build.
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {

/// Given (not an item): an empty proof, so that the gate has one function to count (its
/// minimum is one verified function).
pub proof fn no_verus_exit_item() {
}

} // verus!
