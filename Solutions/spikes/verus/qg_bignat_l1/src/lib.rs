//! BigNat spike, layer L1 (Q01): representation, view, abstraction, well-formedness.
//!
//! Reference material (DV0 spike). Limbs are little-endian `u64`s; the value is read
//! Horner-style over the literal base 2^64, so multiplying by `BASE` stays linear.
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {

/// The limb base, 2^64, written as a literal.
pub spec const BASE: nat = 0x1_0000_0000_0000_0000;

/// Value of a little-endian limb sequence: `s[0] + BASE * value(s[1..])`.
pub open spec fn seq_to_nat(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + BASE * seq_to_nat(s.drop_first())
    }
}

/// Canonical form: no most-significant zero limb; zero is the empty sequence.
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
    /// The abstract value.
    pub open spec fn to_nat(&self) -> nat {
        seq_to_nat(self@)
    }

    /// Well-formed: canonical limbs.
    pub open spec fn wf(&self) -> bool {
        seq_wf(self@)
    }
}

/// Worked proof fn: a zero limb pushed at the most-significant end does not change the value.
pub proof fn lemma_seq_to_nat_push_zero(s: Seq<u64>)
    ensures
        seq_to_nat(s.push(0)) == seq_to_nat(s),
    decreases s.len(),
{
    if s.len() == 0 {
        assert(s.push(0).drop_first() =~= Seq::<u64>::empty());
        assert(seq_to_nat(Seq::<u64>::empty()) == 0);
    } else {
        assert(s.push(0).drop_first() =~= s.drop_first().push(0));
        lemma_seq_to_nat_push_zero(s.drop_first());
    }
}

} // verus!
