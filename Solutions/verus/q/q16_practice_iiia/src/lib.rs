//! # Q16 — Practice III-A: the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q16_practice_iiia/src/lib.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise file. Every hole is filled, every check is live and the speed test is
//! uncommented. The lemmas the learner invents (the blueprint's) are in the file's
//! `HELPERS` area, each marked reference-only.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l7::*;

verus! {

// =========================================================================================
// HELPERS: the lemmas of your blueprint, here (statements and proofs).
// =========================================================================================

/// The value of a suffix, one limb at a time from the top.
pub proof fn lemma_suffix_step(s: Seq<u64>, i: int)  // reference-only: the learner's H2 lemma
    requires
        0 <= i < s.len(),
    ensures
        seq_to_nat(s.subrange(i, s.len() as int)) == s[i] + BASE * seq_to_nat(
            s.subrange(i + 1, s.len() as int),
        ),
{
    assert(s.subrange(i, s.len() as int).drop_first() =~= s.subrange(i + 1, s.len() as int));
}

/// One division step keeps the quotient digit a limb and the remainder below d.
pub proof fn lemma_div_step(r: nat, x: nat, d: nat)  // reference-only: the learner's H2 lemma
    requires
        0 < d < BASE,
        r < d,
        x < BASE,
    ensures
        (r * BASE + x) / d < BASE,
        (r * BASE + x) % d < d,
        r * BASE + x == ((r * BASE + x) / d) * d + (r * BASE + x) % d,
{
    let t = (r * BASE + x) as int;
    lemma_fundamental_div_mod(t, d as int);
    lemma_mul_is_commutative(d as int, t / (d as int));
    lemma_mod_pos_bound(t, d as int);
    assert(t < d * BASE) by (nonlinear_arith)
        requires
            r < d,
            x < BASE,
            t == r * BASE + x,
    ;
    lemma_multiply_divide_lt(t, d as int, BASE as int);
}

/// The value of a sequence with one more limb on top.
pub proof fn lemma_push_value(s: Seq<u64>, x: u64)  // reference-only: the learner's H3 lemma
    ensures
        seq_to_nat(s.push(x)) == seq_to_nat(s) + weight(s.len()) * x,
{
    lemma_seq_to_nat_append(s, seq![x]);
    assert(s + seq![x] =~= s.push(x));
    assert(seq![x].drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(Seq::<u64>::empty()) == 0);
}

/// Writing limb x at position p moves the value by the two limbs' place values.
pub proof fn lemma_set_limb(s: Seq<u64>, p: int, x: u64)  // reference-only: the learner's H3 lemma
    requires
        0 <= p < s.len(),
    ensures
        seq_to_nat(s.update(p, x)) + weight(p as nat) * s[p] == seq_to_nat(s) + weight(p as nat)
            * x,
    decreases p,
{
    if p == 0 {
        assert(s.update(0, x).drop_first() =~= s.drop_first());
        lemma_weight_zero();
        lemma_mul_basics(s[0] as int);
        lemma_mul_basics(x as int);
    } else {
        let t = s.drop_first();
        assert(s.update(p, x).drop_first() =~= t.update(p - 1, x));
        lemma_set_limb(t, p - 1, x);
        lemma_weight_succ((p - 1) as nat);
        let w = weight((p - 1) as nat) as int;
        lemma_mul_is_associative(BASE as int, w, s[p] as int);
        lemma_mul_is_associative(BASE as int, w, x as int);
        lemma_mul_is_distributive_add(BASE as int, seq_to_nat(t.update(p - 1, x)) as int, w
            * s[p]);
        lemma_mul_is_distributive_add(BASE as int, seq_to_nat(t) as int, w * x);
    }
}

// =========================================================================================
// H2: division by one limb
// =========================================================================================

// item: Q16.H2v S4
// uses: invariant, ghost, library-call, nonlinear-arith
// form: loop-dir:i:down
// triv: { (BigNat { limbs: Vec::new() }, 0) }
// cfree: { let mut q = BigNat { limbs: Vec::new() }; let dd = from_u64(d); let mut r = big_add(a, &q);
// cfree:   let mut ge = match cmp(&r, &dd) { Ordering::Less => false, _ => true };
// cfree:   proof { lemma_mul_basics(d as int); }
// cfree:   while ge
// cfree:     invariant a.wf(), r.wf(), q.wf(), dd.wf(), dd.to_nat() == d, d > 0, a.to_nat() == q.to_nat() * d + r.to_nat(), ge == (r.to_nat() >= d)
// cfree:     decreases r.to_nat()
// cfree:   { let ghost q0 = q.to_nat(); r = big_sub(&r, &dd); q = add_limb(&q, 1);
// cfree:     proof { lemma_mul_is_distributive_add_other_way(d as int, q0 as int, 1); }
// cfree:     ge = match cmp(&r, &dd) { Ordering::Less => false, _ => true }; }
// cfree:   let w = to_u64(&r); (q, w.unwrap()) }
// cfree: { let mut q = BigNat { limbs: Vec::new() }; let dd = from_u64(d); let mut r = big_add(a, &q);
// cfree:   let mut ge = match cmp(&r, &dd) { Ordering::Less => false, _ => true };
// cfree:   proof { lemma_mul_basics(d as int); }
// cfree:   while ge
// cfree:     invariant a.wf(), r.wf(), q.wf(), dd.wf(), dd.to_nat() == d, d > 0, a.to_nat() == q.to_nat() * d + r.to_nat(), ge == (r.to_nat() >= d)
// cfree:     decreases r.to_nat()
// cfree:   { let ghost q0 = q.to_nat(); r = big_sub(&r, &dd); q = add_limb(&q, 1);
// cfree:     proof { lemma_mul_is_distributive_add_other_way(d as int, q0 as int, 1); }
// cfree:     ge = match cmp(&r, &dd) { Ordering::Less => false, _ => true }; }
// cfree:   let mut i: usize = 1; while i > 0 decreases i { i = i - 1; } let w = to_u64(&r); (q, w.unwrap()) }
/// **H2.** Division of a BigNat by one machine word, from the top limb down: a counter
/// `i` that steps down over the limbs, one quotient limb per step, and a remainder below
/// `d` carried down. The loop invariant and the lemmas under it are yours (the blueprint's,
/// B1). Layer L6's `normalize` is available for the quotient. Which equation between
/// values holds at every step?
pub fn div_limb(a: &BigNat, d: u64) -> (res: (BigNat, u64))
    requires
        a.wf(),
        d > 0,
    ensures
        res.0.wf(),
        res.1 < d,
        a.to_nat() == res.0.to_nat() * d + res.1,
{
    let n = a.limbs.len();
    let mut q: Vec<u64> = Vec::new();
    let mut k: usize = 0;
    while k < n
        invariant
            k <= n,
            q@.len() == k,
        decreases n - k,
    {
        q.push(0);
        k = k + 1;
    }
    let mut rem: u64 = 0;
    let mut i: usize = n;
    proof {
        assert(a@.subrange(n as int, n as int) =~= Seq::<u64>::empty());
        assert(q@.subrange(n as int, n as int) =~= Seq::<u64>::empty());
        assert(seq_to_nat(Seq::<u64>::empty()) == 0);
        lemma_mul_basics(d as int);
    }
    while i > 0
        invariant
            i <= n,
            n == a@.len(),
            q@.len() == n,
            rem < d,
            seq_to_nat(a@.subrange(i as int, n as int)) == seq_to_nat(q@.subrange(i as int, n as int))
                * d + rem,
        decreases i,
    {
        i = i - 1;
        let x = a.limbs[i];
        proof {
            lemma_div_step(rem as nat, x as nat, d as nat);
        }
        let t: u128 = (rem as u128) * 0x1_0000_0000_0000_0000u128 + x as u128;
        let qd: u64 = (t / d as u128) as u64;
        let r2: u64 = (t % d as u128) as u64;
        let ghost oldq = q@;
        q.set(i, qd);
        proof {
            lemma_suffix_step(a@, i as int);
            lemma_suffix_step(q@, i as int);
            assert(q@.subrange(i + 1, n as int) =~= oldq.subrange(i + 1, n as int));
            let qs = seq_to_nat(q@.subrange(i + 1, n as int)) as int;
            let av = seq_to_nat(a@.subrange(i + 1, n as int)) as int;
            assert(av == qs * d + rem);
            lemma_mul_is_distributive_add_other_way(d as int, qd as int, BASE * qs);
            lemma_mul_is_associative(BASE as int, qs, d as int);
            lemma_mul_is_distributive_add(BASE as int, qs * d, rem as int);
        }
        rem = r2;
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
        assert(q@.subrange(0, n as int) =~= q@);
    }
    let mut qb = BigNat { limbs: q };
    normalize(&mut qb);
    (qb, rem)
}

fn div_limb_check(a: &BigNat, d: u64)
    requires
        a.wf(),
        d > 0,
{
    let (q, r) = div_limb(a, d);
    assert(q.to_nat() * d + r == a.to_nat());
}

// =========================================================================================
// H3, the Verus half (the Dafny half is MulLoop, in the Dafny file)
// =========================================================================================

// item: Q16.H3v S1
// uses: invariant, lemma-call, property-test
// pair: Q16.H3d
// form: no-call:big_add, no-call:plus, no-adder
// triv: { BigNat { limbs: Vec::new() } }
// cfree: { let m = b.limbs.len(); let mut acc = BigNat { limbs: Vec::new() }; let mut i: usize = m;
// cfree:   proof { assert(b@.subrange(m as int, m as int) =~= Seq::<u64>::empty()); lemma_mul_basics(a.to_nat() as int); }
// cfree:   while i > 0
// cfree:     invariant i <= m, m == b@.len(), a.wf(), b.wf(), acc.wf(), acc.to_nat() == a.to_nat() * seq_to_nat(b@.subrange(i as int, m as int))
// cfree:     decreases i
// cfree:   { i = i - 1; let ghost g = acc.to_nat() as int;
// cfree:     let s0 = mul_limb(&acc, 0x1_0000_0000); let s = mul_limb(&s0, 0x1_0000_0000); let p = mul_limb(a, b.limbs[i]); acc = big_add(&s, &p);
// cfree:     proof { let t = b@.subrange(i as int, m as int); assert(t.drop_first() =~= b@.subrange(i + 1, m as int));
// cfree:       let av = a.to_nat() as int; let t1 = seq_to_nat(t.drop_first()) as int; let h = b@[i as int] as int;
// cfree:       assert(seq_to_nat(t) == h + BASE * t1); lemma_mul_is_associative(g, 0x1_0000_0000, 0x1_0000_0000);
// cfree:       assert(acc.to_nat() == av * (h + BASE * t1)) by (nonlinear_arith) requires acc.to_nat() == g * BASE + av * h, g == av * t1; } }
// cfree:   proof { assert(b@.subrange(0, m as int) =~= b@); } acc }
// cfree-decl: pub fn my_add(a: &BigNat, b: &BigNat) -> (r: BigNat)
// cfree-decl:     requires
// cfree-decl:         a.wf(),
// cfree-decl:         b.wf(),
// cfree-decl:     ensures
// cfree-decl:         r.wf(),
// cfree-decl:         r.to_nat() == a.to_nat() + b.to_nat(),
// cfree-decl: {
// cfree-decl:     let n = a.limbs.len();
// cfree-decl:     let m = b.limbs.len();
// cfree-decl:     let len = if n >= m { n } else { m };
// cfree-decl:     let mut res: Vec<u64> = Vec::new();
// cfree-decl:     let mut carry: u64 = 0;
// cfree-decl:     let mut i: usize = 0;
// cfree-decl:     let ghost mut c: Seq<nat> = seq![0nat];
// cfree-decl:     while i < len
// cfree-decl:         invariant
// cfree-decl:             n == a@.len(),
// cfree-decl:             m == b@.len(),
// cfree-decl:             len == if n >= m { n } else { m },
// cfree-decl:             i <= len,
// cfree-decl:             res@.len() == i,
// cfree-decl:             c.len() == i + 1,
// cfree-decl:             c[0] == 0,
// cfree-decl:             c[i as int] == carry,
// cfree-decl:             carry <= 1,
// cfree-decl:             forall|j: int|
// cfree-decl:                 0 <= j < i ==> limb_at(a@, j) + limb_at(b@, j) + c[j] == #[trigger] res@[j] + BASE
// cfree-decl:                     * c[j + 1],
// cfree-decl:         decreases len - i,
// cfree-decl:     {
// cfree-decl:         let x: u64 = if i < n { a.limbs[i] } else { 0 };
// cfree-decl:         let y: u64 = if i < m { b.limbs[i] } else { 0 };
// cfree-decl:         let s: u128 = x as u128 + y as u128 + carry as u128;
// cfree-decl:         let d: u64 = (s % 0x1_0000_0000_0000_0000u128) as u64;
// cfree-decl:         carry = (s / 0x1_0000_0000_0000_0000u128) as u64;
// cfree-decl:         res.push(d);
// cfree-decl:         proof {
// cfree-decl:             c = c.push(carry as nat);
// cfree-decl:         }
// cfree-decl:         i = i + 1;
// cfree-decl:     }
// cfree-decl:     if carry != 0 {
// cfree-decl:         res.push(carry);
// cfree-decl:         proof {
// cfree-decl:             c = c.push(0);
// cfree-decl:         }
// cfree-decl:     }
// cfree-decl:     proof {
// cfree-decl:         lemma_add_lift(a@, b@, res@, c);
// cfree-decl:     }
// cfree-decl:     BigNat { limbs: res }
// cfree-decl: }
// cfree: { let m = b.limbs.len(); let mut acc = BigNat { limbs: Vec::new() }; let mut i: usize = m;
// cfree:   proof { assert(b@.subrange(m as int, m as int) =~= Seq::<u64>::empty()); lemma_mul_basics(a.to_nat() as int); }
// cfree:   while i > 0
// cfree:     invariant i <= m, m == b@.len(), a.wf(), b.wf(), acc.wf(), acc.to_nat() == a.to_nat() * seq_to_nat(b@.subrange(i as int, m as int))
// cfree:     decreases i
// cfree:   { i = i - 1; let ghost g = acc.to_nat() as int;
// cfree:     let s0 = mul_limb(&acc, 0x1_0000_0000); let s = mul_limb(&s0, 0x1_0000_0000); let p = mul_limb(a, b.limbs[i]); acc = my_add(&s, &p);
// cfree:     proof { let t = b@.subrange(i as int, m as int); assert(t.drop_first() =~= b@.subrange(i + 1, m as int));
// cfree:       let av = a.to_nat() as int; let t1 = seq_to_nat(t.drop_first()) as int; let h = b@[i as int] as int;
// cfree:       assert(seq_to_nat(t) == h + BASE * t1); lemma_mul_is_associative(g, 0x1_0000_0000, 0x1_0000_0000);
// cfree:       assert(acc.to_nat() == av * (h + BASE * t1)) by (nonlinear_arith) requires acc.to_nat() == g * BASE + av * h, g == av * t1; } }
// cfree:   proof { assert(b@.subrange(0, m as int) =~= b@); } acc }
/// **H3 (the Verus half).** Full multiplication, schoolbook and in place: one result
/// vector, and one pass per limb of `b` that adds that limb's row of products into the
/// vector at the limb's offset, with its own carry. No whole-number addition per row:
/// layer L4's `big_add` and `NatLike::plus` are not called here or in a helper this item
/// calls. Then uncomment the speed test after `verus!` and run it with
/// `scripts/vcheck --test verus/q/q16_practice_iiia`: it multiplies two four-limb
/// factors, which a method that adds `a` to itself `b` times cannot finish. What does each
/// loop's invariant say about the value of the vector so far?
pub fn mul(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * b.to_nat(),
{
    let n = a.limbs.len();
    let m = b.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut k: usize = 0;
    while k < n
        invariant
            k <= n,
            res@.len() == k,
            seq_to_nat(res@) == 0,
        decreases n - k,
    {
        proof {
            lemma_seq_to_nat_push_zero(res@);
        }
        res.push(0);
        k = k + 1;
    }
    let mut j: usize = 0;
    proof {
        assert(b@.subrange(0, 0) =~= Seq::<u64>::empty());
        lemma_mul_basics(a.to_nat() as int);
    }
    while j < m
        invariant
            j <= m,
            n == a@.len(),
            m == b@.len(),
            res@.len() == n + j,
            seq_to_nat(res@) == a.to_nat() * seq_to_nat(b@.subrange(0, j as int)),
        decreases m - j,
    {
        let bj = b.limbs[j];
        let top = res.len();
        let ghost v0 = seq_to_nat(res@);
        let mut carry: u64 = 0;
        let mut i: usize = 0;
        proof {
            assert(a@.subrange(0, 0) =~= Seq::<u64>::empty());
            lemma_mul_basics(bj as int);
            lemma_mul_basics(weight(j as nat) as int);
        }
        while i < n
            invariant
                i <= n,
                j < m,
                n == a@.len(),
                top == n + j,
                res@.len() == top,
                seq_to_nat(res@) + weight((j + i) as nat) * carry == v0 + weight(j as nat) * (
                seq_to_nat(a@.subrange(0, i as int)) * bj),
            decreases n - i,
        {
            let ai = a.limbs[i];
            let cur = res[j + i];
            proof {
                lemma_mul_upper_bound(ai as int, 0xFFFF_FFFF_FFFF_FFFF, bj as int, 0xFFFF_FFFF_FFFF_FFFF);
            }
            let p: u128 = ai as u128 * bj as u128 + cur as u128 + carry as u128;
            let dgt: u64 = (p % 0x1_0000_0000_0000_0000u128) as u64;
            let ghost s0 = res@;
            let ghost c0 = carry;
            res.set(j + i, dgt);
            carry = (p / 0x1_0000_0000_0000_0000u128) as u64;
            proof {
                lemma_set_limb(s0, (j + i) as int, dgt);
                assert(a@.subrange(0, i + 1) =~= a@.subrange(0, i as int).push(ai));
                lemma_push_value(a@.subrange(0, i as int), ai);
                lemma_weight_succ((j + i) as nat);
                lemma_weight_add(j as nat, i as nat);
                let w = weight((j + i) as nat);
                let wj = weight(j as nat);
                let wi = weight(i as nat);
                let pa = seq_to_nat(a@.subrange(0, i as int));
                lemma_mul_is_associative(BASE as int, w as int, carry as int);
                lemma_mul_is_associative(w as int, BASE as int, carry as int);
                lemma_mul_is_commutative(w as int, BASE as int);
                lemma_mul_is_distributive_add(w as int, dgt as int, BASE * carry);
                lemma_mul_is_distributive_add(w as int, ai * bj, cur + c0);
                lemma_mul_is_distributive_add(w as int, cur as int, c0 as int);
                lemma_mul_is_distributive_add_other_way(bj as int, pa as int, wi * ai);
                lemma_mul_is_distributive_add(wj as int, pa * bj, (wi * ai) * bj);
                lemma_mul_is_associative(wj as int, wi as int, ai * bj);
                lemma_mul_is_associative(wi as int, ai as int, bj as int);
            }
            i = i + 1;
        }
        proof {
            assert(a@.subrange(0, n as int) =~= a@);
            lemma_push_value(res@, carry);
            assert(b@.subrange(0, j + 1) =~= b@.subrange(0, j as int).push(bj));
            lemma_push_value(b@.subrange(0, j as int), bj);
            let wj = weight(j as nat);
            let av = a.to_nat();
            let bs = seq_to_nat(b@.subrange(0, j as int));
            assert(v0 + wj * (av * bj) == av * (bs + wj * bj)) by (nonlinear_arith)  // did: distributivity of the row
                requires
                    v0 == av * bs,
            ;
        }
        res.push(carry);
        j = j + 1;
    }
    proof {
        assert(b@.subrange(0, m as int) =~= b@);
    }
    let mut r = BigNat { limbs: res };
    normalize(&mut r);
    r
}
fn mul_check(a: &BigNat, b: &BigNat)
    requires
        a.wf(),
        b.wf(),
{
    let r = mul(a, b);
    assert(r.to_nat() == a.to_nat() * b.to_nat());
}

} // verus!

// H3's speed test: uncomment it once `mul` is proved, then run
// `scripts/vcheck --test verus/q/q16_practice_iiia`.
#[cfg(test)]
mod speed {
    use super::*;

    #[test]
    fn four_limb_factors() {
        let a = BigNat { limbs: vec![u64::MAX, u64::MAX, u64::MAX, u64::MAX] };
        let r = mul(&a, &a);
        assert_eq!(
            r.limbs,
            vec![1, 0, 0, 0, u64::MAX - 1, u64::MAX, u64::MAX, u64::MAX]
        );
    }

    #[test]
    fn four_limb_factors_mixed() {
        let a = BigNat {
            limbs: vec![0x0123456789abcdef, 0xfedcba9876543210, 0x0f1e2d3c4b5a6978, 0x8796a5b4c3d2e1f0],
        };
        let b = BigNat {
            limbs: vec![0xdeadbeefcafebabe, 0x1, 0xffffffff00000000, 0x7fffffffffffffff],
        };
        let r = mul(&a, &b);
        assert_eq!(
            r.limbs,
            vec![
                0x7eb689f4ea447d62, 0xa4bc5861c31b35ec, 0xb734532f456bc3bf, 0x6cc47c15ced65da2,
                0xb2be889116e9e9fa, 0xbb9b7b5c2c0bebcc, 0x078f169d9e168f07, 0x43cb52da61e970f8,
            ]
        );
    }
}
