//! Cheat corpus V12, witness: a concrete call the statement must admit.
use vstd::prelude::*;

verus! {

pub proof fn witness() {
    corpus_v12::lemma_between(0, 2, 1);
}

} // verus!
