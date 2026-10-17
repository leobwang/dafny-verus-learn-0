// Lab 2 local task v09-add-carry-in (Q15, course-authored; QPLAN §25.6).
// Write `add_carry_in`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `add_carry_in_witness`. Keep every other line of the file.
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

/// The sum of two limbs and an incoming carry of 0 or 1, as a low limb and an outgoing carry: the low limb plus BASE times the carry is the sum, and the carry is 0 or 1.
pub fn add_carry_in(x: u64, y: u64, c: u64) -> (r: (u64, u64))
{
    let s = x as u128 + y as u128 + c as u128;
    if s < 0x1_0000_0000_0000_0000u128 {
        (s as u64, 0)
    } else {
        ((s - 0x1_0000_0000_0000_0000u128) as u64, 1)
    }
}

/// A non-vacuity witness for `add_carry_in`: one call whose `requires` hold.
fn add_carry_in_witness() {
}

} // verus!
