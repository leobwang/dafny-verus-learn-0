// Lab 2 local task v04-add-carry (Q15, course-authored; QPLAN §25.6).
// Write `add_carry`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `add_carry_witness`. Keep every other line of the file.
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

/// The sum of two limbs as a low limb and a carry: the low limb plus BASE times the carry is the sum, and the carry is 0 or 1.
pub fn add_carry(x: u64, y: u64) -> (r: (u64, u64))
{
    if x <= u64::MAX - y {
        (x + y, 0)
    } else {
        (x - (u64::MAX - y) - 1, 1)
    }
}

/// A non-vacuity witness for `add_carry`: one call whose `requires` hold.
fn add_carry_witness() {
}

} // verus!
