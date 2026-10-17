// Lab 2 local task v02-top-two-equal (Q15, course-authored; QPLAN §25.6).
// Write `top_two_equal`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `top_two_equal_witness`. Keep every other line of the file.
use vstd::prelude::*;

verus! {

pub spec const BASE: nat = 0x1_0000_0000_0000_0000;

/// The value of a limb sequence, least significant limb first.
pub open spec fn seq_to_nat(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + BASE * seq_to_nat(s.drop_first())
    }
}

/// Whether a limb vector has at least two limbs and its two top limbs are equal.
pub fn top_two_equal(a: &Vec<u64>) -> (b: bool)
{
    a.len() >= 2 && a[a.len() - 1] == a[a.len() - 2]
}

/// A non-vacuity witness for `top_two_equal`: one call whose `requires` hold.
fn top_two_equal_witness() {
}

} // verus!
