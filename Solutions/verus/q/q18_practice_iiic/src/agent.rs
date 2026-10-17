/* CONTRACT
goal: implement and prove every statement of the STATEMENTS sections of this file and of dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy, following the graded blueprint in paper/Q18_answers.tex (B1), changing no statement
allowed-files:
  - verus/q/q18_practice_iiic/src/agent.rs
  - dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck <the edited file>`; never stack unverified edits
  - `scripts/vcheck --gate verus/q/q18_practice_iiic/src/agent.rs` exits 0 with zero tool-counted holes
  - `scripts/vcheck --gate dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` exits 0 with zero tool-counted holes
  - `scripts/specfreeze --against research/q18_statements.rs verus/q/q18_practice_iiic/src/agent.rs` reports no change
  - `scripts/specfreeze --against research/q18_statements.dfy dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` reports no change
  - `scripts/vaudit verus/q/q18_practice_iiic/src/agent.rs` and `scripts/vaudit dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` report no finding
  - the differential check: `scripts/vcheck --test verus/q/q18_practice_iiic/src/agent.rs` and `scripts/vcheck --test dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` run every test on the same sample rows, and every test passes
  - `git diff` against the committed statements changes only the bodies of the statements and the two HELPERS sections; every WITNESSES and TESTS line is unchanged
  - new helper fns, proof fns, functions and lemmas go only under HELPERS
*/
//! # Q18 The capstone, Verus half: the crate's proof work (Reference Solution)
//!
//! Hole-free reference for `verus/q/q18_practice_iiic/src/agent.rs` (author-only): the
//! proof that the round's contracts are satisfiable as stated. The six sections are empty,
//! as shipped; the closing reference section holds a reference set of statements (the
//! extension trait `BigNatOps` of `BigNatCore`, its spec fns and the round trip), witnesses
//! and tests for them, and the reference delivery: the impl and the helpers a co-developer
//! puts under HELPERS. Committed as stubs (Solutions/plans/Q18-code-notes.md §6: the impl's
//! methods `external_body`, the round trip one labelled assume), the statements leave the
//! file green with 5 holes, the witnesses verifying; the delivery below passes every
//! acceptance line: `vcheck --gate` with 0 holes, `specfreeze --against` the statements with
//! no finding, `vaudit` with no finding, and `vcheck --test` 7/7 on the same sample rows as
//! the Dafny mirror's tests. Stable on seeds 1-3.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l7::*;

verus! {

// item: Q18.A2dv S12

// item: Q18.H2v S12
// uses: trait-spec, witness
// ### STATEMENTS (learner-owned: your extension trait of `BigNatCore`, its spec fns, and
//    its `impl` for `BigNat` as `external_body` stubs). The new operations:
//    - multiplication of two values;
//    - division by one word `w > 0`: the quotient and the remainder;
//    - `to_decimal`: the value as decimal chunks, each below 10^19, least significant
//      chunk first (by repeated division by 10^19);
//    - `from_decimal`: back from such chunks (by Horner steps of `mul_limb` and
//      `add_limb`);
//    and the round trip as a proof fn.

// ### WITNESSES (learner-owned: a fn that calls each operation on concrete arguments and
//    asserts what its statement gives).

// ### REVIEW (the reviewer's, run A1dv: one proof fn per finding).

// ### HELPERS (the co-developer's, run A2dv: helper fns and proof fns).

// ===========================================================================================
// — clearly marked: everything below answers the agentic file —
// ===========================================================================================
// A reference set of statements (H2v) and the reference delivery (A2dv): the extension
// trait `BigNatOps` of `BigNatCore` with its spec fns, the round trip as a proof fn, the
// witnesses, the tests over the sample rows the Dafny mirror's tests use, and the impl with
// its helpers (Solutions/plans/Q18-code-notes.md §6).

/// The decimal chunk base, 10^19 (the largest power of ten below `BASE`).
pub open spec fn dec_base() -> nat {
    10000000000000000000
}

/// The value of decimal chunks, least significant chunk first.
pub open spec fn dec_to_nat(d: Seq<u64>) -> nat
    decreases d.len(),
{
    if d.len() == 0 {
        0
    } else {
        d[0] as nat + dec_base() * dec_to_nat(d.drop_first())
    }
}

/// Every chunk is a decimal digit in base 10^19.
pub open spec fn dec_digits(d: Seq<u64>) -> bool {
    forall|i: int| 0 <= i < d.len() ==> (#[trigger] d[i]) < dec_base()
}

/// Decimal digits with no zero chunk on top (zero is no chunk at all).
pub open spec fn dec_wf(d: Seq<u64>) -> bool {
    dec_digits(d) && (d.len() == 0 || d.last() != 0)
}

/// The capstone's new operations.
pub trait BigNatOps: BigNatCore {
    fn times(&self, other: &Self) -> (r: Self)
        requires
            self.valid(),
            other.valid(),
        ensures
            r.valid(),
            r.value() == self.value() * other.value(),
    ;

    fn div_word(&self, w: u64) -> (r: (Self, u64))
        requires
            self.valid(),
            w > 0,
        ensures
            r.0.valid(),
            r.1 < w,
            self.value() == r.0.value() * w + r.1,
    ;

    fn to_decimal(&self) -> (d: Vec<u64>)
        requires
            self.valid(),
        ensures
            dec_wf(d@),
            dec_to_nat(d@) == self.value(),
    ;

    fn from_decimal(d: &Vec<u64>) -> (r: Self)
        requires
            dec_digits(d@),
        ensures
            r.valid(),
            r.value() == dec_to_nat(d@),
    ;
}

/// The round trip: canonical decimal chunks are fixed by their value, so `to_decimal` gives
/// back the very chunks `from_decimal` read.
pub proof fn lemma_decimal_round_trip(d1: Seq<u64>, d2: Seq<u64>)
    requires
        dec_wf(d1),
        dec_wf(d2),
        dec_to_nat(d1) == dec_to_nat(d2),
    ensures
        d1 == d2,
    decreases d1.len(),
{
    if d1.len() == 0 || d2.len() == 0 {
        lemma_dec_wf_positive(d1);
        lemma_dec_wf_positive(d2);
        assert(d1 =~= d2);
    } else {
        let p = dec_base() as int;
        let t1 = d1.drop_first();
        let t2 = d2.drop_first();
        assert(dec_to_nat(d1) == d1[0] + p * dec_to_nat(t1));
        assert(dec_to_nat(d2) == d2[0] + p * dec_to_nat(t2));
        assert((d1[0] as int) < p);
        assert((d2[0] as int) < p);
        lemma_mul_is_commutative(p, dec_to_nat(t1) as int);
        lemma_mul_is_commutative(p, dec_to_nat(t2) as int);
        lemma_fundamental_div_mod_converse(dec_to_nat(d1) as int, p, dec_to_nat(t1) as int,
            d1[0] as int);
        lemma_fundamental_div_mod_converse(dec_to_nat(d2) as int, p, dec_to_nat(t2) as int,
            d2[0] as int);
        lemma_dec_tail_wf(d1);
        lemma_dec_tail_wf(d2);
        lemma_decimal_round_trip(t1, t2);
        assert(d1 =~= seq![d1[0]] + t1);
        assert(d2 =~= seq![d2[0]] + t2);
    }
}

/// The witnesses: each operation called on concrete arguments.
pub fn capstone_witnesses() {
    let six = BigNat::from_word(6);
    let seven = BigNat::from_word(7);
    let p = six.times(&seven);
    assert(p.value() == 42);
    let (q, r) = BigNat::from_word(43).div_word(6);
    assert(q.value() * 6 + r == 43 && r < 6);
    let d = p.to_decimal();
    assert(dec_to_nat(d@) == 42);
    let back = BigNat::from_decimal(&d);
    assert(back.value() == 42);
}

// ### The reference delivery (A2dv): the impl and its helpers.

impl BigNatOps for BigNat {
    fn times(&self, other: &Self) -> (r: Self) {
        mul_horner(self, other)
    }

    fn div_word(&self, w: u64) -> (r: (Self, u64)) {
        div_limb(self, w)
    }

    fn to_decimal(&self) -> (d: Vec<u64>) {
        to_decimal_impl(self)
    }

    fn from_decimal(d: &Vec<u64>) -> (r: Self) {
        from_decimal_impl(d)
    }
}

/// A canonical non-empty limb sequence has a positive value.
pub proof fn lemma_wf_positive(s: Seq<u64>)
    requires
        seq_wf(s),
        s.len() > 0,
    ensures
        seq_to_nat(s) > 0,
{
    broadcast use group_bignat_bounds;
    lemma_weight_pos((s.len() - 1) as nat);
}

/// A canonical non-empty decimal sequence has a positive value.
pub proof fn lemma_dec_wf_positive(d: Seq<u64>)
    requires
        dec_wf(d),
    ensures
        d.len() > 0 ==> dec_to_nat(d) > 0,
    decreases d.len(),
{
    if d.len() > 1 {
        lemma_dec_tail_wf(d);
        lemma_dec_wf_positive(d.drop_first());
        lemma_mul_strictly_positive(dec_base() as int, dec_to_nat(d.drop_first()) as int);
    } else if d.len() == 1 {
        assert(d.last() == d[0]);
    }
}

/// The tail of canonical decimal chunks is canonical.
pub proof fn lemma_dec_tail_wf(d: Seq<u64>)
    requires
        dec_wf(d),
        d.len() > 0,
    ensures
        dec_wf(d.drop_first()),
{
    let t = d.drop_first();
    assert forall|i: int| 0 <= i < t.len() implies (#[trigger] t[i]) < dec_base() by {
        assert(t[i] == d[i + 1]);
    }
    if t.len() > 0 {
        assert(t.last() == d.last());
    }
}

/// `dec_base()` to the power `k`.
pub open spec fn dec_pow(k: nat) -> nat
    decreases k,
{
    if k == 0 {
        1
    } else {
        dec_base() * dec_pow((k - 1) as nat)
    }
}

/// A chunk pushed on top lands at the place value of the length.
pub proof fn lemma_dec_push(d: Seq<u64>, c: u64)
    ensures
        dec_to_nat(d.push(c)) == dec_to_nat(d) + dec_pow(d.len()) * c,
    decreases d.len(),
{
    if d.len() == 0 {
        assert(d.push(c).drop_first() =~= Seq::<u64>::empty());
        assert(dec_to_nat(Seq::<u64>::empty()) == 0);
        assert(dec_pow(0) == 1);
    } else {
        assert(d.push(c).drop_first() =~= d.drop_first().push(c));
        lemma_dec_push(d.drop_first(), c);
        let t = dec_to_nat(d.drop_first()) as int;
        let w = dec_pow((d.len() - 1) as nat) as int;
        assert(dec_pow(d.len()) == dec_base() * w);
        lemma_mul_is_distributive_add(dec_base() as int, t, w * c);
        lemma_mul_is_associative(dec_base() as int, w, c as int);
    }
}

/// The value of a chunk suffix, one chunk at a time from the top.
pub proof fn lemma_dec_suffix_step(d: Seq<u64>, i: int)
    requires
        0 <= i < d.len(),
    ensures
        dec_to_nat(d.subrange(i, d.len() as int))
            == d[i] + dec_base() * dec_to_nat(d.subrange(i + 1, d.len() as int)),
{
    assert(d.subrange(i, d.len() as int).drop_first() =~= d.subrange(i + 1, d.len() as int));
}

/// Multiply by `BASE`: one zero limb below.
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

/// Full multiplication, Horner from the top limb of `b`.
pub fn mul_horner(a: &BigNat, b: &BigNat) -> (r: BigNat)
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
        acc = big_add(&s, &p);
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

/// The value of a limb suffix, one limb at a time from the top.
pub proof fn lemma_suffix_step(s: Seq<u64>, i: int)
    requires
        0 <= i < s.len(),
    ensures
        seq_to_nat(s.subrange(i, s.len() as int))
            == s[i] + BASE * seq_to_nat(s.subrange(i + 1, s.len() as int)),
{
    assert(s.subrange(i, s.len() as int).drop_first() =~= s.subrange(i + 1, s.len() as int));
}

/// One division step keeps the quotient digit a limb and the remainder below `d`.
pub proof fn lemma_div_step(r: nat, x: nat, d: nat)
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

/// Division by one limb, from the top.
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
            forall|j: int| 0 <= j < k ==> q@[j] == 0,
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
            d > 0,
            seq_to_nat(a@.subrange(i as int, n as int))
                == seq_to_nat(q@.subrange(i as int, n as int)) * d + rem,
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

/// One step of `to_decimal_impl`: the invariant moves one chunk, the value shrinks, and
/// the last step's chunk is not zero.
pub proof fn lemma_to_decimal_step(w: nat, c: nat, qv: nat, xv: nat)
    requires
        xv == qv * dec_base() + c,
        xv > 0,
        c < dec_base(),
    ensures
        w * c + (dec_base() * w) * qv == w * xv,
        qv < xv,
        qv == 0 ==> c > 0,
{
    let p = dec_base() as int;
    let (wi, ci, qi) = (w as int, c as int, qv as int);
    lemma_mul_is_distributive_add(wi, ci, qi * p);
    lemma_mul_is_associative(wi, qi, p);
    lemma_mul_is_commutative(wi * qi, p);
    lemma_mul_is_associative(p, wi, qi);
    lemma_mul_is_commutative(p, wi);
    lemma_mul_is_commutative(qi, p);
    if qv > 0 {
        lemma_mul_increases(p, qv as int);
        assert(qv < xv) by (nonlinear_arith)
            requires
                qv <= p * qv,
                p > 1,
                qv > 0,
                xv == p * qv + c,
        ;
    } else {
        lemma_mul_basics(p);
    }
}

/// Decimal chunks by repeated division by 10^19.
pub fn to_decimal_impl(a: &BigNat) -> (d: Vec<u64>)
    requires
        a.wf(),
    ensures
        dec_wf(d@),
        dec_to_nat(d@) == a.to_nat(),
{
    let mut x = BigNat { limbs: a.limbs.clone() };
    let mut d: Vec<u64> = Vec::new();
    proof {
        assert(x@ =~= a@);
        assert(dec_to_nat(d@) == 0);
        assert(dec_pow(0) == 1);
        lemma_mul_basics(x.to_nat() as int);
    }
    while x.limbs.len() > 0
        invariant
            x.wf(),
            dec_digits(d@),
            x.to_nat() == 0 ==> (d@.len() == 0 || d@.last() != 0),
            dec_to_nat(d@) + dec_pow(d@.len()) * x.to_nat() == a.to_nat(),
        decreases x.to_nat(),
    {
        proof {
            lemma_wf_positive(x@);
        }
        let (q, c) = div_limb(&x, 10000000000000000000u64);
        proof {
            lemma_dec_push(d@, c);
            assert(dec_pow((d@.len() + 1) as nat) == dec_base() * dec_pow(d@.len()));
            lemma_to_decimal_step(dec_pow(d@.len()), c as nat, q.to_nat(), x.to_nat());
        }
        d.push(c);
        x = q;
    }
    proof {
        assert(x.to_nat() == 0) by {
            assert(x@ =~= Seq::<u64>::empty());
        }
        lemma_mul_basics(dec_pow(d@.len()) as int);
    }
    d
}

/// From decimal chunks by Horner steps of `mul_limb` and `add_limb`, from the top chunk.
pub fn from_decimal_impl(d: &Vec<u64>) -> (r: BigNat)
    requires
        dec_digits(d@),
    ensures
        r.wf(),
        r.to_nat() == dec_to_nat(d@),
{
    let n = d.len();
    let mut r = BigNat { limbs: Vec::new() };
    let mut i: usize = n;
    proof {
        assert(d@.subrange(n as int, n as int) =~= Seq::<u64>::empty());
        assert(r@ =~= Seq::<u64>::empty());
    }
    while i > 0
        invariant
            i <= n,
            n == d@.len(),
            r.wf(),
            r.to_nat() == dec_to_nat(d@.subrange(i as int, n as int)),
        decreases i,
    {
        i = i - 1;
        let m = mul_limb(&r, 10000000000000000000u64);
        r = add_limb(&m, d[i]);
        proof {
            lemma_dec_suffix_step(d@, i as int);
            lemma_mul_is_commutative(dec_base() as int,
                dec_to_nat(d@.subrange(i + 1, n as int)) as int);
        }
    }
    proof {
        assert(d@.subrange(0, n as int) =~= d@);
    }
    r
}

} // verus!

// ### TESTS (learner-owned: the differential check's sample rows, as `#[test]` fns over
//    the same rows as the Dafny mirror's tests; tests sit outside `verus!`).

// The reference TESTS: the differential check's sample rows (the Dafny mirror's tests use
// the same rows).
#[cfg(test)]
mod capstone_tests {
    use super::*;

    fn big(v: &[u64]) -> BigNat {
        BigNat { limbs: v.to_vec() }
    }

    #[test]
    fn row1_times_small() {
        assert_eq!(big(&[6]).times(&big(&[7])).limbs, vec![42u64]);
    }

    #[test]
    fn row2_times_top_words() {
        let m = u64::MAX;
        assert_eq!(big(&[m]).times(&big(&[m])).limbs, vec![1u64, 18446744073709551614]);
    }

    #[test]
    fn row3_div_word_small() {
        let (q, r) = big(&[43]).div_word(6);
        assert_eq!((q.limbs, r), (vec![7u64], 1u64));
    }

    #[test]
    fn row4_div_word_by_dec_base() {
        let (q, r) = big(&[0, 1]).div_word(10000000000000000000);
        assert_eq!((q.limbs, r), (vec![1u64], 8446744073709551616u64));
    }

    #[test]
    fn row5_to_decimal_base() {
        assert_eq!(big(&[0, 1]).to_decimal(), vec![8446744073709551616u64, 1]);
    }

    #[test]
    fn row6_from_decimal_base() {
        assert_eq!(BigNat::from_decimal(&vec![8446744073709551616u64, 1]).limbs, vec![0u64, 1]);
    }

    #[test]
    fn row7_to_decimal_zero() {
        assert_eq!(big(&[]).to_decimal(), Vec::<u64>::new());
    }
}

// AUDIT (learner-owned; after the co-developer run)
//   each REVIEW finding: kept, changed a statement (which), or rejected (why):
//   the statement that cost the co-developer most, and why:
//   each helper's statement (does it assume what it should prove?):
