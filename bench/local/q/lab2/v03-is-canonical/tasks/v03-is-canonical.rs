// Lab 2 local task v03-is-canonical (Q15, course-authored; QPLAN §25.6).
// Write `is_canonical`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `is_canonical_witness`. Keep every other line of the file.
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

/// Whether a limb vector is canonical: empty, or with a non-zero top limb.
pub fn is_canonical(a: &Vec<u64>) -> (b: bool)
{
    a.len() == 0 || a[a.len() - 1] != 0
}

/// A non-vacuity witness for `is_canonical`: one call whose `requires` hold.
fn is_canonical_witness() {
}

} // verus!
