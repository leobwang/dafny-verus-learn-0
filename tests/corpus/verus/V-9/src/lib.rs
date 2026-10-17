//! Cheat corpus V-9: #[path] pulls a module from a file the lint never reads.
use vstd::prelude::*;

#[path = "helper_impl.rs"]
mod helper;

verus! {

pub proof fn lemma_level()
    ensures
        helper::level() >= 0,
{
}

} // verus!
