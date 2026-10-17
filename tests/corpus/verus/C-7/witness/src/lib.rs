//! Cheat corpus control C-7, witness: a concrete call the statement admits.
use vstd::prelude::*;

verus! {

pub fn witness() {
    let r = corpus_vc7::mid(1, 4);
}

} // verus!
