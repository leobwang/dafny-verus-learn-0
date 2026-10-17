//! Cheat corpus control C-6: a verified fn and a #[test] outside verus!.
use vstd::prelude::*;

verus! {

pub fn add_one(x: u32) -> (r: u64)
    ensures
        r == x + 1,
{
    x as u64 + 1
}

} // verus!

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds_one() {
        assert_eq!(add_one(41), 42);
    }
}
