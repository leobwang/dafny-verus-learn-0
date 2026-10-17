// Lab 2 local task v01-third-limb (Q15, course-authored; QPLAN §25.6).
// Write `third_limb`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `third_limb_witness`. Keep every other line of the file.
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

/// The third-lowest limb of a limb vector, or 0 when it has fewer than three limbs.
pub fn third_limb(a: &Vec<u64>) -> (d: u64)
{
    if a.len() < 3 {
        0
    } else {
        a[2]
    }
}

/// A non-vacuity witness for `third_limb`: one call whose `requires` hold.
fn third_limb_witness() {
}

} // verus!
