//! # qg_bignat_l1 — the BigNat spine, layer L1 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q01–Q18. Q01's crate depends on this layer alone; from Q02 on, a
//! module's crate depends on it beside the later layers of its chain. A file imports it
//! with `use qg_bignat_l1::*;` (a later layer crate re-exports it, so
//! `use qg_bignat_l2::*;` brings these names too).
//!
//! What it holds: the limb representation (little-endian `u64` limbs, least significant
//! first), the base `BASE`, the value `seq_to_nat`, the canonical-form predicate
//! `seq_wf`, the exec type `BigNat` with its spec view, `to_nat` and `wf`, and one
//! worked proof fn. Layer L2 (`qg_bignat_l2`) adds a spec helper and a lifting lemma.
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {

/// The limb base, 2^64, written as a literal.
pub spec const BASE: nat = 0x1_0000_0000_0000_0000;

/// The value of a limb sequence, least significant limb first:
/// `s[0] + BASE * (the value of the remaining limbs)`.
pub open spec fn seq_to_nat(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + BASE * seq_to_nat(s.drop_first())
    }
}

/// Canonical form: no most significant zero limb; zero is the empty sequence.
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
    /// The value.
    pub open spec fn to_nat(&self) -> nat {
        seq_to_nat(self@)
    }

    /// Well-formed: canonical limbs.
    pub open spec fn wf(&self) -> bool {
        seq_wf(self@)
    }
}

/// The worked proof fn: a zero limb pushed at the most significant end does not change
/// the value.
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
