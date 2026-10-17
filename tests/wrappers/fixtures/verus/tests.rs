//! Test fixture (tests/wrappers): libtest checks outside verus! (Δ42).
use vstd::prelude::*;

verus! {

pub fn add1(x: u64) -> (r: u64)
    requires
        x < 100,
    ensures
        r == x + 1,
{
    x + 1
}

#[verifier::external_body]
pub fn stub(x: u64) -> (r: u64)
    ensures
        r == x,
{
    unimplemented!()
}

} // verus!

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn add1_three() {
        assert_eq!(add1(3), 4);
    }

    #[test]
    fn add1_wrong() {
        assert_eq!(add1(3), 5);
    }

    #[test]
    fn stub_panics() {
        assert_eq!(stub(3), 3);
    }

    #[test]
    #[ignore]
    fn add1_ignored() {
        assert_eq!(add1(1), 2);
    }
}
