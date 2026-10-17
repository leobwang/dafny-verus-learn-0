//! Test fixture (tests/wrappers): a proved lemma beside a test whose literal is out of
//! range, a deny-by-default rustc lint that only the compiled test build reaches.
use vstd::prelude::*;

verus! {

pub proof fn sum_thirteen()
{
    assert(6 + 7 == 13);
}

} // verus!

#[cfg(test)]
mod tests {
    #[test]
    fn literal_out_of_range() {
        let x: u8 = 300;
        assert_eq!(x, 44);
    }
}
