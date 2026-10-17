// Lab 2 local task v06-min-limb (Q15, course-authored; QPLAN §25.6).
// Write `min_limb`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `min_limb_witness`. Keep every other line of the file.
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

/// The smaller of two limbs (either one when they are equal).
pub fn min_limb(x: u64, y: u64) -> (r: u64)
{
    if x < y {
        x
    } else {
        y
    }
}

/// A non-vacuity witness for `min_limb`: one call whose `requires` hold.
fn min_limb_witness() {
}

} // verus!
