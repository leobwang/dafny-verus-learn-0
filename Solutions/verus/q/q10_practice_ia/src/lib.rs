//! # Q10 — Practice I-A: the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q10_practice_ia/src/lib.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise crate; every hole is filled, every given client verifies with no assume and
//! every check is live. The twin of the H4v annotation hole marks the learner's lines with
//! `@hole-begin` / `@hole-end`, and the exec items declare their trivial bodies in
//! `// triv:` lines.
//!
//! Silent under `scripts/vcheck --ref` on the crate.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l5::*;

verus! {

// =========================================================================================
// Holes
// =========================================================================================

// item: Q10.H1v S1
// uses: exec-check, lemma-call
// pair: Q10.H1d
// triv: { None }
/// **H1.** A canonical BigNat as one word.
///
/// Reference: no limb is 0 (the empty view's value); one limb is its own value once the
/// verifier sees that the view's tail is empty and has value 0; two or more limbs put the
/// value at or above `weight(n - 1)` (L3's lower bound), which is at least `weight(1)`
/// (monotonicity) `== BASE * weight(0) == BASE` (the two equations).
pub fn to_u64(a: &BigNat) -> (r: Option<u64>)
    requires
        a.wf(),
    ensures
        r is Some <==> a.to_nat() < BASE,
        r is Some ==> r->0 as nat == a.to_nat(),
{
    let n = a.limbs.len();
    if n == 0 {
        Some(0)
    } else if n == 1 {
        proof {
            assert(a@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(a@.drop_first()) == 0);
        }
        Some(a.limbs[0])
    } else {
        proof {
            lemma_seq_to_nat_lower(a@);
            lemma_weight_mono(1, (n - 1) as nat);
            lemma_weight_zero();
            lemma_weight_succ(0);
        }
        None
    }
}

/// The given client: a word's BigNat converts back to the word.
pub fn round_trip(x: u64) -> (r: Option<u64>)
    ensures
        r == Some(x),
{
    let b = from_u64(x);
    to_u64(&b)
}

// item: Q10.H2v S2
// uses: ensures
/// **H2.** Specify the top limb.
///
/// Reference `ensures`: `r == 0 <==> a@.len() == 0` (a canonical BigNat's top limb is not
/// zero). The client needs the direction from `r == 0` to the empty view, whose value is
/// 0; the reverse direction keeps the statement exact.
pub fn high_limb(a: &BigNat) -> (r: u64)
    requires
        a.wf(),
    ensures
        r == 0 <==> a@.len() == 0,
{
    if a.limbs.len() == 0 {
        0
    } else {
        a.limbs[a.limbs.len() - 1]
    }
}

/// The given client: with `high_limb` specified, it verifies with no assume.
pub fn high_client(a: &BigNat)
    requires
        a.wf(),
{
    let h = high_limb(a);
    if h == 0 {
        assert(a.to_nat() == 0);
    }
}

// item: Q10.H3v S3
// uses: assert, lemma-call
// pair: Q10.H3d
/// **H3.** The top limb's place value: an assertion repair.
///
/// Reference: the quoted attempt plus one extensional equality, `s` as its prefix followed
/// by its last limb, which lets the append lemma's statement speak about `s` itself.
pub proof fn lemma_top_limb(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) == seq_to_nat(s.drop_last()) + weight((s.len() - 1) as nat) * s.last(),
{
    lemma_seq_to_nat_append(s.drop_last(), seq![s.last()]);
    assert(seq![s.last()].drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(seq![s.last()].drop_first()) == 0);
    assert(s =~= s.drop_last() + seq![s.last()]);
}

// item: Q10.H4v S4
// uses: invariant
// pair: Q10.H4d
/// **H4.** The forward-scan normalize: the loop invariant.
///
/// Reference: the bounds `n <= i <= v@.len()`, the limb below `n` (when there is one) is
/// not zero, and every limb from `n` up to `i` is zero.
pub fn norm_len(v: &Vec<u64>) -> (n: usize)
    ensures
        n <= v@.len(),
        n == 0 || v@[n - 1] != 0,
        forall|j: int| n <= j < v@.len() ==> v@[j] == 0,
{
    let mut n: usize = 0;
    let mut i: usize = 0;
    while i < v.len()
        invariant
            // @hole-begin Q10.H4v
            n <= i <= v@.len(),
            n == 0 || v@[n - 1] != 0,
            forall|j: int| n <= j < i ==> v@[j] == 0,
            // @hole-end Q10.H4v
        decreases v@.len() - i,
    {
        if v[i] != 0 {
            n = i + 1;
        }
        i = i + 1;
    }
    n
}

fn norm_len_check() {
    let mut v: Vec<u64> = Vec::new();
    v.push(3);
    v.push(0);
    assert(v@[0] == 3 && v@[1] == 0);
    let n = norm_len(&v);
    assert(n == 1);
}

// item: Q10.H5v S5
// uses: library-call
// pair: Q10.H5d
/// **H5.** Search, then name: a remainder of a remainder.
///
/// Reference: `vstd::arithmetic::div_mod::lemma_mod_mod(x, weight(n), BASE)` (`x % (a * b)
/// % a == x % a` for positive `a`, `b`), after L5's positivity and L3's second equation;
/// the commutativity assertion matches the lemma's `weight(n) * BASE` to the equation's
/// `BASE * weight(n)`.
pub proof fn lemma_mod_weight_succ(x: nat, n: nat)
    ensures
        x % weight(n + 1) % weight(n) == x % weight(n),
{
    lemma_weight_pos(n);
    lemma_weight_succ(n);
    vstd::arithmetic::div_mod::lemma_mod_mod(x as int, weight(n) as int, BASE as int);
    assert(weight(n) * BASE == BASE * weight(n));
}

// =========================================================================================
// The ring buffer
// =========================================================================================

// item: Q10.W1v S1
/// **W1.** A ring buffer of words. `buf` is the storage, `head` the position of the first
/// element and `len` the number of elements; the elements wrap around the end of `buf`.
/// `inv` keeps `head` and `len` inside the storage, `slot(i)` is the storage position of
/// element `i` (the wrap is a comparison, not a remainder), and the view `self@` is the
/// sequence of the `len` elements in order. `new` is given and verified.
pub struct Ring {
    pub buf: Vec<u64>,
    pub head: usize,
    pub len: usize,
}

impl Ring {
    pub open spec fn inv(&self) -> bool {
        self.buf@.len() > 0 && self.head < self.buf@.len() && self.len <= self.buf@.len()
    }

    pub open spec fn slot(&self, i: int) -> int {
        if self.head + i < self.buf@.len() {
            self.head + i
        } else {
            self.head + i - self.buf@.len()
        }
    }

    pub open spec fn view(&self) -> Seq<u64> {
        Seq::new(self.len as nat, |i: int| self.buf@[self.slot(i)])
    }

    pub fn new(cap: usize) -> (r: Ring)
        requires
            cap > 0,
        ensures
            r.inv(),
            r.buf@.len() == cap,
            r.len == 0,
            r@ == Seq::<u64>::empty(),
    {
        let mut buf: Vec<u64> = Vec::new();
        let mut k: usize = 0;
        while k < cap
            invariant
                k <= cap,
                buf@.len() == k,
            decreases cap - k,
        {
            buf.push(0);
            k = k + 1;
        }
        let r = Ring { buf, head: 0, len: 0 };
        proof {
            assert(r@ =~= Seq::<u64>::empty());
        }
        r
    }

    // item: Q10.H6v S1
    // uses: exec-check
    /// **H6.** Read element `i`.
    ///
    /// Reference: compare `head` with `buf.len() - i` (no overflow: `i < len <= buf.len()`)
    /// and index either `head + i` or `i - (buf.len() - head)`; each index is the spec's
    /// `slot(i)`, so the view's element is the value read.
    pub fn get(&self, i: usize) -> (r: u64)
        requires
            self.inv(),
            i < self.len,
        ensures
            r == self@[i as int],
    {
        if self.head < self.buf.len() - i {
            self.buf[self.head + i]
        } else {
            self.buf[i - (self.buf.len() - self.head)]
        }
    }

    // item: Q10.H7v S1
    // uses: mut-ref, assert
    /// **H7.** Append one element.
    ///
    /// Reference: the free position is `slot(len)`, computed by a comparison as in `get`;
    /// write it with `set`, grow `len`, and say extensionally that the new view is the old
    /// one with `x` pushed (every old element's slot is untouched: its position differs
    /// from the written one).
    pub fn push_back(&mut self, x: u64)
        requires
            old(self).inv(),
            old(self).len < old(self).buf@.len(),
        ensures
            final(self).inv(),
            final(self)@ == old(self)@.push(x),
    {
        let cap = self.buf.len();
        let idx = if self.head < cap - self.len {
            self.head + self.len
        } else {
            self.len - (cap - self.head)
        };
        let ghost before = self@;
        self.buf.set(idx, x);
        self.len = self.len + 1;
        proof {
            assert(self@ =~= before.push(x));
        }
    }
}

/// A check of the ring buffer's operations.
fn ring_check() {
    let mut q = Ring::new(3);
    q.push_back(7);
    assert(q@.len() == 1);
    let a = q.get(0);
    assert(a == 7);
}

} // verus!
