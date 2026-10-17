//! Test fixture (tests/wrappers): no learner lint finding; strings and
//! comments that merely name banned constructs are not code.
use vstd::prelude::*;
#[cfg(verus_only)]
use vstd::seq::*;
#[cfg_attr(verus_only, verifier::loop_isolation(false))]
pub mod helpers;

// vstd::pervasive::assume, arbitrary(), #[verifier::external] in a comment
verus! {

/* a block comment: #[verifier::exec_allows_no_decreases_clause] */
pub fn names() -> (r: &'static str)
    ensures
        true,
{
    "pervasive::assume arbitrary() include!"
}

pub fn ch() -> (r: char)
    ensures
        r == 'a',
{
    'a'
}

} // verus!

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn t() {
        assert_eq!(ch(), 'a');
    }
}
