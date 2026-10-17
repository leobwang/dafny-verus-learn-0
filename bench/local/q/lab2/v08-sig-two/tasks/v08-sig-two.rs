// Lab 2 local task v08-sig-two (Q15, course-authored; QPLAN §25.6).
// Write `sig_two`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `sig_two_witness`. Keep every other line of the file.
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

/// How many limbs the two-limb number (x0 low, x1 high) needs: 2 when its high limb is non-zero, else 1 when its low limb is, else 0.
pub fn sig_two(x0: u64, x1: u64) -> (n: usize)
{
    if x1 != 0 {
        2
    } else if x0 != 0 {
        1
    } else {
        0
    }
}

/// A non-vacuity witness for `sig_two`: one call whose `requires` hold.
fn sig_two_witness() {
}

} // verus!
