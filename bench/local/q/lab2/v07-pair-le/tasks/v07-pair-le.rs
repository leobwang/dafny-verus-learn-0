// Lab 2 local task v07-pair-le (Q15, course-authored; QPLAN §25.6).
// Write `pair_le`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `pair_le_witness`. Keep every other line of the file.
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

/// Whether the two-limb number (a0 low, a1 high) is at most the two-limb number (b0 low, b1 high).
pub fn pair_le(a0: u64, a1: u64, b0: u64, b1: u64) -> (r: bool)
{
    a1 < b1 || (a1 == b1 && a0 <= b0)
}

/// A non-vacuity witness for `pair_le`: one call whose `requires` hold.
fn pair_le_witness() {
}

} // verus!
