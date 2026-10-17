// Lab 1 local task va5-limb-or-zero (Q12, course-authored; QPLAN §22.6).
// Write the body of `limb_or_zero` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
use vstd::prelude::*;
use core::cmp::Ordering;

verus! {

/// The limb base, 2^64.
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

/// Canonical form: no most significant zero limb.
pub open spec fn seq_wf(s: Seq<u64>) -> bool {
    s.len() == 0 || s.last() != 0
}

/// An arbitrary-precision natural number.
pub struct BigNat {
    pub limbs: Vec<u64>,
}

impl View for BigNat {
    type V = Seq<u64>;

    open spec fn view(&self) -> Seq<u64> {
        self.limbs@
    }
}

impl BigNat {
    pub open spec fn to_nat(&self) -> nat {
        seq_to_nat(self@)
    }

    pub open spec fn wf(&self) -> bool {
        seq_wf(self@)
    }
}

/// The limb at position j, a missing limb read as 0.
pub open spec fn limb_at(s: Seq<u64>, j: int) -> nat {
    if 0 <= j < s.len() {
        s[j] as nat
    } else {
        0
    }
}

/// The limb at a position, or 0 past the end.
pub fn limb_or_zero(a: &BigNat, i: usize) -> (r: u64)
    ensures
        r as nat == limb_at(a@, i as int),
{
    0
}

} // verus!
