//! Test fixture (tests/wrappers): the invented bottom layer.
use vstd::prelude::*;

verus! {

pub open spec fn twice(x: nat) -> nat {
    x + x
}

pub broadcast proof fn lemma_twice(x: nat)
    ensures
        #[trigger] twice(x) == 2 * x,
{
}

pub broadcast group group_tla {
    lemma_twice,
}

} // verus!
