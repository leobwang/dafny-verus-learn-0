//! Cheat corpus V-9: the module behind the #[path] attribute.
use vstd::prelude::*;

verus! {

pub open spec fn level() -> nat {
    arbitrary()
}

} // verus!
