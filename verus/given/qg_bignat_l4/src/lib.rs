//! # qg_bignat_l4 — the BigNat spine, layer L4 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q07–Q18. From Q07 on, a module's crate depends on this layer beside L1,
//! L2 and L3. A file imports it with `use qg_bignat_l4::*;`, which also brings the L1–L3
//! names (re-exported below); the crate still lists the lower layers as dependencies.
//!
//! Do not open this file before you start Q07: it holds finished versions of code and
//! proofs that Q04 and Q06 pose as holes, so reading it earlier spoils them.
//!
//! What it holds: the verified comparison `cmp` and the proof fns `lemma_weight_add` and
//! `lemma_seq_to_nat_append`; addition (`big_add`, with its carry lemma `lemma_add_lift`);
//! multiplication by one machine word (`mul_limb`, with `lemma_mul_limb_lift`); and the
//! trait `NatLike`, the interface a natural-number implementation offers, with its
//! implementation for `BigNat`.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l3::*;

verus! {

// ---------------------------------------------------------------------------
// Verified code and proofs about the L1–L3 definitions
// ---------------------------------------------------------------------------

/// The weight of a sum of positions is the product of the weights.
pub proof fn lemma_weight_add(m: nat, n: nat)
    ensures
        weight(m + n) == weight(m) * weight(n),
    decreases m,
{
    if m == 0 {
        lemma_weight_zero();
        lemma_mul_basics(weight(n) as int);
    } else {
        let k = (m - 1) as nat;
        lemma_weight_add(k, n);
        lemma_weight_succ(k);
        lemma_weight_succ(k + n);
        lemma_mul_is_associative(BASE as int, weight(k) as int, weight(n) as int);
    }
}

/// The value of a concatenation.
pub proof fn lemma_seq_to_nat_append(a: Seq<u64>, b: Seq<u64>)
    ensures
        seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    if a.len() > 0 {
        let k = (a.len() - 1) as nat;
        assert((a + b).drop_first() =~= a.drop_first() + b);
        lemma_seq_to_nat_append(a.drop_first(), b);
        lemma_weight_succ(k);
        lemma_mul_is_associative(BASE as int, weight(k) as int, seq_to_nat(b) as int);
        lemma_mul_is_distributive_add(
            BASE as int,
            seq_to_nat(a.drop_first()) as int,
            (weight(k) * seq_to_nat(b)) as int,
        );
    } else {
        lemma_weight_zero();
        assert(a + b =~= b);
    }
}

/// Three-way comparison of two canonical `BigNat`s by value.
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
    while i > 0 && a.limbs[i - 1] == b.limbs[i - 1]
        invariant
            i <= n,
            n == a@.len(),
            n == b@.len(),
            forall|j: int| i <= j < n ==> a@[j] == b@[j],
        decreases i,
    {
        i = i - 1;
    }
    if i == 0 {
        proof {
            assert(a@ =~= b@);
        }
        Ordering::Equal
    } else if a.limbs[i - 1] < b.limbs[i - 1] {
        proof {
            lemma_lt_at(a@, b@, (i - 1) as int);
        }
        Ordering::Less
    } else {
        proof {
            lemma_lt_at(b@, a@, (i - 1) as int);
        }
        Ordering::Greater
    }
}

// ---------------------------------------------------------------------------
// Addition
// ---------------------------------------------------------------------------

/// Carry lifting for `big_add`: per-limb relations `a[j] + b[j] + c[j] == r[j] + BASE * c[j+1]`
/// add up to the value relation.
pub proof fn lemma_add_lift(a: Seq<u64>, b: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() <= r.len(),
        b.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] == 0,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + limb_at(b, j) + c[j] == #[trigger] r[j] + BASE
                * c[j + 1],
    ensures
        seq_to_nat(r) == seq_to_nat(a) + seq_to_nat(b) + c[0],
    decreases r.len(),
{
    if r.len() > 0 {
        let a2 = if a.len() > 0 { a.drop_first() } else { a };
        let b2 = if b.len() > 0 { b.drop_first() } else { b };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + limb_at(b2, j) + c2[j]
            == #[trigger] r2[j] + BASE * c2[j + 1] by {
            assert(limb_at(a, j + 1) + limb_at(b, j + 1) + c[j + 1] == r[j + 1] + BASE * c[j + 2]);
        }
        lemma_add_lift(a2, b2, r2, c2);
        assert(limb_at(a, 0) + limb_at(b, 0) + c[0] == r[0] + BASE * c[1]);
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

/// The sum of two canonical `BigNat`s.
pub fn big_add(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + b.to_nat(),
{
    let n = a.limbs.len();
    let m = b.limbs.len();
    let len = if n >= m { n } else { m };
    let mut res: Vec<u64> = Vec::new();
    let mut carry: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < len
        invariant
            n == a@.len(),
            m == b@.len(),
            len == if n >= m { n } else { m },
            i <= len,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == carry,
            carry <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + limb_at(b@, j) + c[j] == #[trigger] res@[j] + BASE
                    * c[j + 1],
        decreases len - i,
    {
        let x: u64 = if i < n { a.limbs[i] } else { 0 };
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        let s: u128 = x as u128 + y as u128 + carry as u128;
        let d: u64 = (s % 0x1_0000_0000_0000_0000u128) as u64;
        carry = (s / 0x1_0000_0000_0000_0000u128) as u64;
        res.push(d);
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
        lemma_add_lift(a@, b@, res@, c);
    }
    BigNat { limbs: res }
}

// ---------------------------------------------------------------------------
// Multiplication by one machine word
// ---------------------------------------------------------------------------

/// Carry lifting for `mul_limb`: per-limb relations `a[j] * x + c[j] == r[j] + BASE * c[j+1]`
/// add up to the value relation.
pub proof fn lemma_mul_limb_lift(a: Seq<u64>, x: nat, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] == 0,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) * x + c[j] == #[trigger] r[j] + BASE * c[j + 1],
    ensures
        seq_to_nat(r) == seq_to_nat(a) * x + c[0],
    decreases r.len(),
{
    if r.len() > 0 {
        let a2 = if a.len() > 0 { a.drop_first() } else { a };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) * x + c2[j]
            == #[trigger] r2[j] + BASE * c2[j + 1] by {
            assert(limb_at(a, j + 1) * x + c[j + 1] == r[j + 1] + BASE * c[j + 2]);
        }
        lemma_mul_limb_lift(a2, x, r2, c2);
        assert(limb_at(a, 0) * x + c[0] == r[0] + BASE * c[1]);
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
        let h = limb_at(a, 0);
        let t = seq_to_nat(a2);
        let v = seq_to_nat(a);
        assert(v == h + BASE * t);
        lemma_mul_is_distributive_add_other_way(x as int, h as int, (BASE * t) as int);
        lemma_mul_is_associative(BASE as int, t as int, x as int);
    } else {
        let v = seq_to_nat(a);
        assert(v == 0);
        lemma_mul_basics(x as int);
    }
}

/// The product of a canonical `BigNat` and one machine word.
pub fn mul_limb(a: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * x,
{
    let n = a.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    if x == 0 {
        proof {
            lemma_mul_basics(a.to_nat() as int);
        }
        return BigNat { limbs: res };
    }
    let mut carry: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < n
        invariant
            n == a@.len(),
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == carry,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) * x + c[j] == #[trigger] res@[j] + BASE * c[j + 1],
        decreases n - i,
    {
        let li = a.limbs[i];
        proof {
            lemma_mul_upper_bound(li as int, 0xFFFF_FFFF_FFFF_FFFF, x as int, 0xFFFF_FFFF_FFFF_FFFF);
        }
        let p: u128 = li as u128 * x as u128 + carry as u128;
        let d: u64 = (p % 0x1_0000_0000_0000_0000u128) as u64;
        carry = (p / 0x1_0000_0000_0000_0000u128) as u64;
        res.push(d);
        proof {
            c = c.push(carry as nat);
        }
        i = i + 1;
    }
    if carry != 0 {
        res.push(carry);
        proof {
            c = c.push(0);
            lemma_mul_basics(x as int);
        }
    } else if n > 0 {
        proof {
            let top = a@[n - 1];
            lemma_mul_increases(top as int, x as int);
            assert(limb_at(a@, n - 1) * x + c[n - 1] == res@[n - 1] + BASE * c[n as int]);
        }
    }
    proof {
        lemma_mul_limb_lift(a@, x as nat, res@, c);
    }
    BigNat { limbs: res }
}

// ---------------------------------------------------------------------------
// The interface a natural-number implementation offers
// ---------------------------------------------------------------------------

/// The operations every natural-number implementation provides, with their specifications.
pub trait NatLike: Sized {
    spec fn valid(&self) -> bool;

    spec fn value(&self) -> nat;

    fn zero() -> (r: Self)
        ensures
            r.valid(),
            r.value() == 0,
    ;

    fn from_word(x: u64) -> (r: Self)
        ensures
            r.valid(),
            r.value() == x,
    ;

    fn plus(&self, other: &Self) -> (r: Self)
        requires
            self.valid(),
            other.valid(),
        ensures
            r.valid(),
            r.value() == self.value() + other.value(),
    ;

    fn times_word(&self, x: u64) -> (r: Self)
        requires
            self.valid(),
        ensures
            r.valid(),
            r.value() == self.value() * x,
    ;

    fn compare(&self, other: &Self) -> (r: Ordering)
        requires
            self.valid(),
            other.valid(),
        ensures
            (r == Ordering::Less) == (self.value() < other.value()),
            (r == Ordering::Equal) == (self.value() == other.value()),
            (r == Ordering::Greater) == (self.value() > other.value()),
    ;
}

impl NatLike for BigNat {
    open spec fn valid(&self) -> bool {
        self.wf()
    }

    open spec fn value(&self) -> nat {
        self.to_nat()
    }

    fn zero() -> (r: Self) {
        BigNat { limbs: Vec::new() }
    }

    fn from_word(x: u64) -> (r: Self) {
        from_u64(x)
    }

    fn plus(&self, other: &Self) -> (r: Self) {
        big_add(self, other)
    }

    fn times_word(&self, x: u64) -> (r: Self) {
        mul_limb(self, x)
    }

    fn compare(&self, other: &Self) -> (r: Ordering) {
        cmp(self, other)
    }
}

} // verus!
