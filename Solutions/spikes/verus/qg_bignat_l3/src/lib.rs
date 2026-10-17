//! BigNat spike, layer L3 (Q04-Q06 targets): `cmp` and a lemma group for `broadcast use`.
//!
//! Reference material (DV0 spike). Depends only on layer L2 (which re-exports L1).
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
pub use qg_bignat_l2::*;

verus! {

/// BASE^n, unfolded one literal multiplication at a time (stays linear).
/// Opaque: with its body visible, `broadcast use group_bignat_bounds` alone closes the empty
/// proof of `to_u64` (DV0 empty-body gate); callers that need the value `reveal(weight)`.
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

/// Weights are monotone in the exponent.
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

/// Upper bound: n limbs hold less than BASE^n.
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

/// Lower bound: a canonical, non-empty sequence is at least BASE^(n-1).
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

/// Same length, equal above index `i`, smaller at `i`: smaller value.
pub proof fn lemma_lt_at(a: Seq<u64>, b: Seq<u64>, i: int)
    requires
        a.len() == b.len(),
        0 <= i < a.len(),
        a[i] < b[i],
        forall|j: int| i < j < a.len() ==> a[j] == b[j],
    ensures
        seq_to_nat(a) < seq_to_nat(b),
    decreases i,
{
    if i == 0 {
        assert(a.drop_first() =~= b.drop_first());
    } else {
        lemma_lt_at(a.drop_first(), b.drop_first(), i - 1);
    }
}

/// Three-way comparison agreeing with the order of the values.
pub fn cmp(a: &BigNat, b: &BigNat) -> (r: Ordering)
    requires
        a.wf(),
        b.wf(),
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    broadcast use group_bignat_bounds;

    let n = a.limbs.len();
    let m = b.limbs.len();
    if n < m {
        return Ordering::Less;
    }
    if n > m {
        return Ordering::Greater;
    }
    let mut i = n;
    while i > 0
        invariant
            i <= n,
            n == a@.len(),
            n == b@.len(),
            forall|j: int| i <= j < n ==> a@[j] == b@[j],
        decreases i,
    {
        i = i - 1;
        if a.limbs[i] < b.limbs[i] {
            proof {
                lemma_lt_at(a@, b@, i as int);
            }
            return Ordering::Less;
        }
        if a.limbs[i] > b.limbs[i] {
            proof {
                lemma_lt_at(b@, a@, i as int);
            }
            return Ordering::Greater;
        }
    }
    proof {
        assert(a@ =~= b@);
    }
    Ordering::Equal
}

} // verus!
