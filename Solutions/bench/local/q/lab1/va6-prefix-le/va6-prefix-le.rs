// Lab 1 local task va6-prefix-le (Q12, course-authored; QPLAN §22.6).
// Write the body of `lemma_prefix_le` so that `scripts/vcheck --gate` verifies this file. Keep
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

/// A prefix is worth at most the whole sequence.
pub proof fn lemma_prefix_le(s: Seq<u64>, n: nat)
    requires
        n <= s.len(),
    ensures
        seq_to_nat(s.subrange(0, n as int)) <= seq_to_nat(s),
    decreases s.len(),
{
    if n > 0 {
        assert(s.subrange(0, n as int).drop_first() =~= s.drop_first().subrange(0, n - 1));
        lemma_prefix_le(s.drop_first(), (n - 1) as nat);
        let x = seq_to_nat(s.drop_first().subrange(0, n - 1));
        let y = seq_to_nat(s.drop_first());
        assert(BASE * x <= BASE * y) by (nonlinear_arith)
            requires
                x <= y,
        ;
    }
}

} // verus!
