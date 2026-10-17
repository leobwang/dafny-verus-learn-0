//! BigNat spike, layer L4 (Q07-Q09 targets): `add` with proof, `mul_limb`, `trait NatLike`;
//! plus full `mul` (Horner from the top), which the design's fallback would have dropped.
//!
//! Reference material (DV0 spike). Depends only on layer L3 (which re-exports L1-L2).
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l3::*;

verus! {

/// Carry lifting for `add`: per-limb relations `a[j] + b[j] + c[j] == r[j] + BASE * c[j+1]`
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

/// Sum of two BigNats.
pub fn add(a: &BigNat, b: &BigNat) -> (r: BigNat)
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

/// Product of a BigNat and one machine word.
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

/// Multiply by BASE: prepend one zero limb (zero stays the empty sequence).
pub fn shift_limb(a: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == BASE * a.to_nat(),
{
    let n = a.limbs.len();
    let mut v: Vec<u64> = Vec::new();
    if n == 0 {
        return BigNat { limbs: v };
    }
    v.push(0);
    let mut i: usize = 0;
    while i < n
        invariant
            n == a@.len(),
            i <= n,
            v@ =~= seq![0u64] + a@.subrange(0, i as int),
        decreases n - i,
    {
        v.push(a.limbs[i]);
        i = i + 1;
        proof {
            assert(v@ =~= seq![0u64] + a@.subrange(0, i as int));
        }
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
        assert(v@.drop_first() =~= a@);
    }
    BigNat { limbs: v }
}

/// Product of two BigNats, Horner-style from the most significant limb of `b`.
pub fn mul(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * b.to_nat(),
{
    let m = b.limbs.len();
    let mut acc = BigNat { limbs: Vec::new() };
    let mut i: usize = m;
    proof {
        assert(seq_to_nat(b@.subrange(m as int, m as int)) == 0);
        lemma_mul_basics(a.to_nat() as int);
    }
    while i > 0
        invariant
            i <= m,
            m == b@.len(),
            a.wf(),
            acc.wf(),
            acc.to_nat() == a.to_nat() * seq_to_nat(b@.subrange(i as int, m as int)),
        decreases i,
    {
        i = i - 1;
        let s = shift_limb(&acc);
        let p = mul_limb(a, b.limbs[i]);
        acc = add(&s, &p);
        proof {
            let t = b@.subrange(i as int, m as int);
            assert(t.drop_first() =~= b@.subrange(i + 1, m as int));
            let av = a.to_nat() as int;
            let t1 = seq_to_nat(t.drop_first()) as int;
            let h = b@[i as int] as int;
            assert(seq_to_nat(t) == h + BASE * t1);
            lemma_mul_is_distributive_add(av, h, BASE * t1);
            lemma_mul_is_associative(av, BASE as int, t1);
            lemma_mul_is_associative(BASE as int, av, t1);
        }
    }
    proof {
        assert(b@.subrange(0, m as int) =~= b@);
    }
    acc
}

/// The interface a natural-number implementation offers.
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

    fn times(&self, other: &Self) -> (r: Self)
        requires
            self.valid(),
            other.valid(),
        ensures
            r.valid(),
            r.value() == self.value() * other.value(),
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
        add(self, other)
    }

    fn times_word(&self, x: u64) -> (r: Self) {
        mul_limb(self, x)
    }

    fn times(&self, other: &Self) -> (r: Self) {
        mul(self, other)
    }

    fn compare(&self, other: &Self) -> (r: Ordering) {
        cmp(self, other)
    }
}

/// A generic client: 2 * v + 1, through the trait only.
pub fn double_plus_one<T: NatLike>(v: &T) -> (r: T)
    requires
        v.valid(),
    ensures
        r.valid(),
        r.value() == 2 * v.value() + 1,
{
    let one = T::from_word(1);
    let d = v.plus(v);
    d.plus(&one)
}

} // verus!
