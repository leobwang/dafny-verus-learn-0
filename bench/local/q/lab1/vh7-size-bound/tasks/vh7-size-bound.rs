// Lab 1 local task vh7-size-bound (Q12, course-authored; QPLAN §22.6).
// Write the body of `size_bound` so that `scripts/vcheck --gate` verifies this file. Keep
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

/// `BASE` to the power `n`.
#[verifier::opaque]
pub open spec fn weight(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else {
        BASE * weight((n - 1) as nat)
    }
}

pub proof fn lemma_weight_zero()
    ensures
        weight(0) == 1,
{
    reveal(weight);
}

pub proof fn lemma_weight_succ(n: nat)
    ensures
        weight(n + 1) == BASE * weight(n),
{
    reveal(weight);
}

pub broadcast proof fn lemma_weight_mono(m: nat, n: nat)
    requires
        m <= n,
    ensures
        #[trigger] weight(m) <= #[trigger] weight(n),
    decreases n,
{
    reveal(weight);
    if m < n {
        lemma_weight_mono(m, (n - 1) as nat);
    }
}

pub broadcast proof fn lemma_seq_to_nat_upper(s: Seq<u64>)
    ensures
        #[trigger] seq_to_nat(s) < weight(s.len()),
    decreases s.len(),
{
    reveal(weight);
    if s.len() > 0 {
        lemma_seq_to_nat_upper(s.drop_first());
    }
}

pub broadcast proof fn lemma_seq_to_nat_lower(s: Seq<u64>)
    requires
        seq_wf(s),
        s.len() > 0,
    ensures
        weight((s.len() - 1) as nat) <= #[trigger] seq_to_nat(s),
    decreases s.len(),
{
    reveal(weight);
    if s.len() > 1 {
        assert(s.drop_first().last() == s.last());
        lemma_seq_to_nat_lower(s.drop_first());
    }
}

pub broadcast group group_bignat_bounds {
    lemma_weight_mono,
    lemma_seq_to_nat_upper,
    lemma_seq_to_nat_lower,
}

/// A number of limbs that bounds the value.
pub fn size_bound(a: &BigNat) -> (r: usize)
    ensures
        a.to_nat() < weight(r as nat),
{
    0
}

} // verus!
