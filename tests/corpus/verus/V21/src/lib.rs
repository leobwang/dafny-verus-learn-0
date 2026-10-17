//! Cheat corpus V21: a global layout directive that is false on the host.
use vstd::prelude::*;

verus! {

global size_of usize == 4;

pub proof fn lemma_word()
    ensures
        usize::MAX == 0xffff_ffff,
{
}

} // verus!
