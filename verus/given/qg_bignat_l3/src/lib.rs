//! # qg_bignat_l3 — the BigNat spine, layer L3 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q04–Q18. From Q04 on, a module's crate depends on this layer beside L1
//! and L2. A file imports it with `use qg_bignat_l3::*;`, which also brings the L1 and
//! L2 names (re-exported below); the crate still lists `qg_bignat_l1` and
//! `qg_bignat_l2` as dependencies.
//!
//! Do not open this file before you start Q04: it holds finished versions of code and
//! proofs that Q02 and Q03 pose as holes, so reading it earlier spoils them.
//!
//! What it holds: the proof fn `lemma_seq_to_nat_drop_last_zero` and the exec fns
//! `from_u64` and `add_limb`, all verified; the power `weight` with its two defining
//! equations as lemmas (`lemma_weight_zero`, `lemma_weight_succ`); three bound lemmas
//! collected in the group `group_bignat_bounds`; and `lemma_lt_at`.
#![allow(unused_imports)]
use vstd::prelude::*;
pub use qg_bignat_l2::*;

verus! {

// ---------------------------------------------------------------------------
// Verified code and proofs about the L1 and L2 definitions
// ---------------------------------------------------------------------------

/// Dropping one most significant zero limb keeps the value.
pub proof fn lemma_seq_to_nat_drop_last_zero(s: Seq<u64>)
    requires
        s.len() > 0,
        s.last() == 0,
    ensures
        seq_to_nat(s.drop_last()) == seq_to_nat(s),
{
    assert(s.drop_last().push(0) =~= s);
    lemma_seq_to_nat_push_zero(s.drop_last());
}

/// The canonical `BigNat` of one `u64`.
pub fn from_u64(x: u64) -> (r: BigNat)
    ensures
        r.wf(),
        r.to_nat() == x,
{
    let mut v: Vec<u64> = Vec::new();
    if x != 0 {
        v.push(x);
        proof {
            assert(v@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(v@.drop_first()) == 0);
        }
    }
    BigNat { limbs: v }
}

/// Add one limb `x` to a canonical `BigNat`, propagating the carry.
pub fn add_limb(a: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + x,
{
    let n = a.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut carry: u64 = x;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![x as nat];
    while i < n
        invariant
            n == a@.len(),
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == x,
            c[i as int] == carry,
            i > 0 ==> carry <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + c[j] == #[trigger] res@[j] + BASE * c[j + 1],
        decreases n - i,
    {
        let li = a.limbs[i];
        if li <= u64::MAX - carry {
            res.push(li + carry);
            carry = 0;
        } else {
            res.push(li - (u64::MAX - carry) - 1);
            carry = 1;
        }
        i = i + 1;
        proof {
            c = c.push(carry as nat);
        }
    }
    if carry != 0 {
        res.push(carry);
        proof {
            c = c.push(0);
        }
    }
    proof {
        lemma_add_limb_lift(a@, res@, c);
    }
    BigNat { limbs: res }
}

// ---------------------------------------------------------------------------
// The power `weight` and its bounds
// ---------------------------------------------------------------------------

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

/// The first defining equation of `weight`.
pub proof fn lemma_weight_zero()
    ensures
        weight(0) == 1,
{
    reveal(weight);
}

/// The second defining equation of `weight`.
pub proof fn lemma_weight_succ(n: nat)
    ensures
        weight(n + 1) == BASE * weight(n),
{
    reveal(weight);
}

/// `weight` is monotone.
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

/// The value of `s` is below `weight(s.len())`.
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

/// The value of a canonical non-empty `s` is at least `weight(s.len() - 1)`.
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

/// The three bound lemmas above, as one group.
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

} // verus!
