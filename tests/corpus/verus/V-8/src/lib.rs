//! Cheat corpus V-8: external_trait_specification gives a std trait unchecked method specs.
use vstd::prelude::*;

verus! {

#[verifier::external_trait_specification]
pub trait ExFromStr: Sized {
    type ExternalTraitSpecificationFor: core::str::FromStr;

    type Err;

    fn from_str(s: &str) -> Result<Self, Self::Err>;
}

pub fn one() -> (r: u64)
    ensures
        r == 1,
{
    1
}

} // verus!
