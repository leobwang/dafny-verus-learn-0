// Lab 1 local task vh4-seq-to-nat-mono (Q12, course-authored; QPLAN §22.6).
// Write the body of `lemma_seq_to_nat_mono` so that `scripts/vcheck --gate` verifies this file. Keep
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

/// The value is monotone in each limb.
pub proof fn lemma_seq_to_nat_mono(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == b.len(),
        forall|i: int| 0 <= i < a.len() ==> a[i] <= b[i],
    ensures
        seq_to_nat(a) <= seq_to_nat(b),
    decreases a.len(),
{
    if a.len() > 0 {
        assert forall|i: int| 0 <= i < a.drop_first().len() implies a.drop_first()[i] <= b.drop_first()[i] by {
            assert(a[i + 1] <= b[i + 1]);
        }
        lemma_seq_to_nat_mono(a.drop_first(), b.drop_first());
    }
}

} // verus!
