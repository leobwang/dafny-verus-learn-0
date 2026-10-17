//! Cheat corpus V12b, witness: a concrete call the statement must admit.
use vstd::prelude::*;

verus! {

pub fn witness() {
    let r = corpus_v12b::window_len(1, 4);
}

} // verus!
