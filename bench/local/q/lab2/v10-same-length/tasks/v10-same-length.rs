// Lab 2 local task v10-same-length (Q15, course-authored; QPLAN §25.6).
// Write `same_length`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `same_length_witness`. Keep every other line of the file.
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

/// Whether two limb vectors have the same number of limbs.
pub fn same_length(a: &Vec<u64>, b: &Vec<u64>) -> (r: bool)
{
    a.len() == b.len()
}

/// A non-vacuity witness for `same_length`: one call whose `requires` hold.
fn same_length_witness() {
}

} // verus!
