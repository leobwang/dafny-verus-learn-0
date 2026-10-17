//! BigNat spike, extras beyond L1-L4: candidates for later BigNat holes.
//!   Q10 `u64` round trip (`to_u64`, `round_trip`), Q13 `sub` with borrow,
//!   Q07 bit-vector digit split (`lemma_digit_split`, `split_u128`),
//!   Q16 hard-tier candidate `cmp_any` (comparison of non-canonical limb vectors).
//!
//! Reference material (DV0 spike). Depends only on layer L4 (which re-exports L1-L3).
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
pub use qg_bignat_l4::*;

verus! {

/// The value as one machine word, when it fits.
pub fn to_u64(a: &BigNat) -> (r: Option<u64>)
    requires
        a.wf(),
    ensures
        match r {
            Some(x) => x as nat == a.to_nat(),
            None => a.to_nat() >= BASE,
        },
{
    let n = a.limbs.len();
    if n == 0 {
        return Some(0);
    }
    if n == 1 {
        proof {
            assert(a@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(a@.drop_first()) == 0);
        }
        return Some(a.limbs[0]);
    }
    proof {
        lemma_seq_to_nat_lower(a@);
        lemma_weight_mono(1, (n - 1) as nat);
        reveal(weight);
        assert(weight(1) == BASE * weight(0));
    }
    None
}

/// Round trip: a word survives `from_u64` then `to_u64`.
pub fn round_trip(x: u64) -> (r: Option<u64>)
    ensures
        r == Some(x),
{
    let b = from_u64(x);
    to_u64(&b)
}

/// Borrow lifting for `sub`: per-limb relations `a[j] + BASE * c[j+1] == r[j] + b[j] + c[j]`
/// add up to the value relation (the top borrow counts `weight(n)`).
pub proof fn lemma_sub_lift(a: Seq<u64>, b: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() == r.len(),
        b.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] <= 1,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + BASE * c[j + 1] == #[trigger] r[j] + limb_at(b, j)
                + c[j],
    ensures
        seq_to_nat(a) + (if c[r.len() as int] == 0 { 0 } else { weight(r.len()) }) == seq_to_nat(r)
            + seq_to_nat(b) + c[0],
    decreases r.len(),
{
    reveal(weight);
    if r.len() > 0 {
        let a2 = a.drop_first();
        let b2 = if b.len() > 0 { b.drop_first() } else { b };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + BASE * c2[j + 1]
            == #[trigger] r2[j] + limb_at(b2, j) + c2[j] by {
            assert(limb_at(a, j + 1) + BASE * c[j + 2] == r[j + 1] + limb_at(b, j + 1) + c[j + 1]);
        }
        lemma_sub_lift(a2, b2, r2, c2);
        assert(limb_at(a, 0) + BASE * c[1] == r[0] + limb_at(b, 0) + c[0]);
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

/// Difference of two BigNats, `a >= b`, with a borrow chain.
pub fn sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() - b.to_nat(),
{
    broadcast use group_bignat_bounds;

    let n = a.limbs.len();
    let m = b.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut borrow: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < n
        invariant
            n == a@.len(),
            m == b@.len(),
            m <= n,
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == borrow,
            borrow <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + BASE * c[j + 1] == #[trigger] res@[j] + limb_at(b@, j)
                    + c[j],
        decreases n - i,
    {
        let x: u64 = a.limbs[i];
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        let d: u64;
        if x >= y && x - y >= borrow {
            d = x - y - borrow;
            borrow = 0;
        } else {
            d = ((x as u128 + 0x1_0000_0000_0000_0000u128) - y as u128 - borrow as u128) as u64;
            borrow = 1;
        }
        res.push(d);
        proof {
            c = c.push(borrow as nat);
        }
        i = i + 1;
    }
    proof {
        lemma_sub_lift(a@, b@, res@, c);
    }
    let mut r = BigNat { limbs: res };
    normalize(&mut r);
    r
}

/// Carry-overflow bound for one limb step of `mul_limb` (a nonlinear-arith site).
pub proof fn lemma_limb_product_bound(x: u64, y: u64, c: u64)
    ensures
        (x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFu128 as nat,
{
    assert((x as nat) * (y as nat) <= 0xFFFF_FFFF_FFFF_FFFFnat * 0xFFFF_FFFF_FFFF_FFFFnat) by (nonlinear_arith)
        requires
            x <= 0xFFFF_FFFF_FFFF_FFFFu64,
            y <= 0xFFFF_FFFF_FFFF_FFFFu64,
    ;
}

/// Bit-vector facts for the u128 digit split (shift and mask).
pub proof fn lemma_digit_split(p: u128)
    ensures
        (p >> 64u128) == p / 0x1_0000_0000_0000_0000u128,
        (p & 0xFFFF_FFFF_FFFF_FFFFu128) == p % 0x1_0000_0000_0000_0000u128,
{
    assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (bit_vector);
    assert((p & 0xFFFF_FFFF_FFFF_FFFFu128) == p % 0x1_0000_0000_0000_0000u128) by (bit_vector);
}

/// Split a double word into (high, low) limbs with shift and mask.
pub fn split_u128(p: u128) -> (r: (u64, u64))
    ensures
        r.0 as nat * BASE + r.1 as nat == p as nat,
{
    proof {
        lemma_digit_split(p);
    }
    let hi = (p >> 64u128) as u64;
    let lo = (p & 0xFFFF_FFFF_FFFF_FFFFu128) as u64;
    (hi, lo)
}

/// The limbs above the lowest one (the empty sequence stays empty).
pub open spec fn tail(s: Seq<u64>) -> Seq<u64> {
    if s.len() > 0 {
        s.drop_first()
    } else {
        s
    }
}

/// Limb-wise equal (zero padded) sequences have equal values.
pub proof fn lemma_eq_any(a: Seq<u64>, b: Seq<u64>)
    requires
        forall|j: int| 0 <= j ==> #[trigger] limb_at(a, j) == limb_at(b, j),
    ensures
        seq_to_nat(a) == seq_to_nat(b),
    decreases a.len() + b.len(),
{
    if a.len() > 0 || b.len() > 0 {
        assert forall|j: int| 0 <= j implies #[trigger] limb_at(tail(a), j) == limb_at(tail(b), j) by {
            assert(limb_at(a, j + 1) == limb_at(b, j + 1));
        }
        lemma_eq_any(tail(a), tail(b));
        assert(limb_at(a, 0) == limb_at(b, 0));
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

/// Zero-padded limbs equal above `i` and smaller at `i`: smaller value (any lengths).
pub proof fn lemma_lt_at_any(a: Seq<u64>, b: Seq<u64>, i: int)
    requires
        0 <= i,
        limb_at(a, i) < limb_at(b, i),
        forall|j: int| i < j ==> #[trigger] limb_at(a, j) == limb_at(b, j),
    ensures
        seq_to_nat(a) < seq_to_nat(b),
    decreases i,
{
    assert forall|j: int| i - 1 < j implies #[trigger] limb_at(tail(a), j) == limb_at(tail(b), j)
        by {
        assert(limb_at(a, j + 1) == limb_at(b, j + 1));
    }
    if i == 0 {
        lemma_eq_any(tail(a), tail(b));
    } else {
        lemma_lt_at_any(tail(a), tail(b), i - 1);
    }
    if a.len() == 0 {
        assert(seq_to_nat(a) == 0);
    }
}

/// Three-way comparison of limb vectors that need not be canonical (zero top limbs allowed).
pub fn cmp_any(a: &BigNat, b: &BigNat) -> (r: Ordering)
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    let n = a.limbs.len();
    let m = b.limbs.len();
    let mut i = if n >= m { n } else { m };
    while i > 0
        invariant
            n == a@.len(),
            m == b@.len(),
            forall|j: int| i <= j ==> #[trigger] limb_at(a@, j) == limb_at(b@, j),
        decreases i,
    {
        i = i - 1;
        let x: u64 = if i < n { a.limbs[i] } else { 0 };
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        if x < y {
            proof {
                lemma_lt_at_any(a@, b@, i as int);
            }
            return Ordering::Less;
        }
        if x > y {
            proof {
                lemma_lt_at_any(b@, a@, i as int);
            }
            return Ordering::Greater;
        }
    }
    proof {
        lemma_eq_any(a@, b@);
    }
    Ordering::Equal
}

} // verus!
