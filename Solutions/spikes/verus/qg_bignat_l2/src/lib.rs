//! BigNat spike, layer L2 (Q02-Q03 targets): `normalize`, `from_u64`, `add_limb`.
//!
//! Reference material (DV0 spike). Depends only on layer L1.
#![allow(unused_imports)]
use vstd::prelude::*;
pub use qg_bignat_l1::*;

verus! {

/// Limb `j` of `s`, reading past the end as zero.
pub open spec fn limb_at(s: Seq<u64>, j: int) -> nat {
    if 0 <= j < s.len() {
        s[j] as nat
    } else {
        0
    }
}

/// Dropping a most-significant zero limb keeps the value.
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

/// Carry lifting for `add_limb`: per-limb relations `a[j] + c[j] == r[j] + BASE * c[j+1]`
/// add up to the value relation.
pub proof fn lemma_add_limb_lift(a: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] == 0,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + c[j] == #[trigger] r[j] + BASE * c[j + 1],
    ensures
        seq_to_nat(r) == seq_to_nat(a) + c[0],
    decreases r.len(),
{
    if r.len() > 0 {
        let a2 = if a.len() > 0 { a.drop_first() } else { a };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + c2[j] == #[trigger] r2[j]
            + BASE * c2[j + 1] by {
            assert(limb_at(a, j + 1) + c[j + 1] == r[j + 1] + BASE * c[j + 2]);
        }
        lemma_add_limb_lift(a2, r2, c2);
        assert(limb_at(a, 0) + c[0] == r[0] + BASE * c[1]);
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
    }
}

/// Remove most-significant zero limbs.
pub fn normalize(a: &mut BigNat)
    ensures
        final(a).wf(),
        final(a).to_nat() == old(a).to_nat(),
{
    while a.limbs.len() > 0 && a.limbs[a.limbs.len() - 1] == 0
        invariant
            a.to_nat() == old(a).to_nat(),
        decreases a.limbs.len(),
    {
        proof {
            lemma_seq_to_nat_drop_last_zero(a@);
        }
        a.limbs.pop();
    }
}

/// The BigNat for one machine word.
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

/// Add one machine word, propagating the carry.
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
        proof {
            c = c.push(carry as nat);
        }
        i = i + 1;
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

} // verus!
