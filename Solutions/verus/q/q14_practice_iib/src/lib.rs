//! # Q14 — Practice II-B: the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q14_practice_iib/src/lib.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise crate; every hole is filled and every check is live. Each item uses at most
//! the one helper the tier allows, in its `HELPERS` area; each exec method declares its
//! trivial body in a `// triv:` line (`// triv: <method>: { … }` for the trait impl).
//!
//! Silent under `scripts/vcheck --ref` on the crate (with src/perm.rs).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

mod perm;

verus! {

// =========================================================================================
// A trait with a ghost view
// =========================================================================================

/// Given (not an item): an accumulator seen through its ghost total.
pub trait Accum: Sized {
    spec fn total(&self) -> nat;

    fn add_word(&mut self, x: u64)
        requires
            old(self).total() + x < BASE * BASE,
        ensures
            final(self).total() == old(self).total() + x,
    ;

    fn read(&self) -> (r: BigNat)
        ensures
            r.wf(),
            r.to_nat() == self.total(),
    ;

    fn from_big(a: &BigNat) -> (r: Option<Self>)
        requires
            a.wf(),
        ensures
            r is Some <==> a.to_nat() < BASE * BASE,
            r is Some ==> r->0.total() == a.to_nat(),
    ;
}

/// Given (not an item): a generic client, which sees an accumulator only through `total`.
pub fn add_both<A: Accum>(acc: &mut A, x: u64, y: u64)
    requires
        old(acc).total() + x + y < BASE * BASE,
    ensures
        final(acc).total() == old(acc).total() + x + y,
{
    acc.add_word(x);
    acc.add_word(y);
}

/// Given (not an item): a two-limb accumulator.
pub struct PairAcc {
    pub lo: u64,
    pub hi: u64,
}

// item: Q14.H2v S6
// uses: trait-spec
// triv: add_word: { }
// triv: read: { BigNat { limbs: Vec::new() } }
// triv: from_big: { None }
/// **H2.** Reference: `add_word` carries into `hi` when `lo + x` overflows (the
/// precondition keeps `hi + 1` in range); `read` builds no, one or two limbs and unfolds
/// `seq_to_nat` as far as they go; `from_big` takes zero, one or two limbs the same way
/// and refuses three or more by L3's lower bound with `weight(2) == BASE * BASE`.
impl Accum for PairAcc {
    open spec fn total(&self) -> nat {
        self.lo as nat + BASE * self.hi as nat
    }

    fn add_word(&mut self, x: u64) {
        if self.lo <= u64::MAX - x {
            self.lo = self.lo + x;
        } else {
            self.lo = self.lo - (u64::MAX - x) - 1;
            self.hi = self.hi + 1;
        }
    }

    fn read(&self) -> (r: BigNat) {
        let mut v: Vec<u64> = Vec::new();
        if self.hi != 0 {
            v.push(self.lo);
            v.push(self.hi);
            proof {
                assert(v@.drop_first() =~= seq![self.hi]);
                assert(v@.drop_first().drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(v@.drop_first().drop_first()) == 0);
                assert(seq_to_nat(v@.drop_first()) == self.hi as nat);
            }
        } else if self.lo != 0 {
            v.push(self.lo);
            proof {
                assert(v@.drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(v@.drop_first()) == 0);
            }
        }
        proof {
            assert(seq_to_nat(Seq::<u64>::empty()) == 0);
        }
        BigNat { limbs: v }
    }

    fn from_big(a: &BigNat) -> (r: Option<Self>) {
        let n = a.limbs.len();
        if n == 0 {
            Some(PairAcc { lo: 0, hi: 0 })
        } else if n == 1 {
            proof {
                assert(a@.drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(a@.drop_first()) == 0);
            }
            Some(PairAcc { lo: a.limbs[0], hi: 0 })
        } else if n == 2 {
            proof {
                let t = a@.drop_first();
                assert(t.drop_first() =~= Seq::<u64>::empty());
                assert(seq_to_nat(t.drop_first()) == 0);
                assert(seq_to_nat(t) == t[0] as nat);
            }
            Some(PairAcc { lo: a.limbs[0], hi: a.limbs[1] })
        } else {
            proof {
                lemma_seq_to_nat_lower(a@);
                lemma_weight_mono(2, (n - 1) as nat);
                lemma_weight_zero();
                lemma_weight_succ(0);
                lemma_weight_succ(1);
            }
            None
        }
    }
}

fn pair_acc_check() {
    let mut acc = PairAcc { lo: u64::MAX, hi: 0 };
    add_both(&mut acc, 1, 2);
    let r = acc.read();
    assert(r.to_nat() == u64::MAX as nat + 3);
    let b = BigNat { limbs: Vec::new() };
    let z = PairAcc::from_big(&b);
    assert(z is Some);
}

// =========================================================================================
// Erasure
// =========================================================================================

/// Given (not an item): the sum of the limbs, defined from the top limb.
pub open spec fn limb_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { limb_sum(s.drop_last()) + s.last() as nat }
}

// HELPERS (Q14.H3v): at most one proof fn of your own, here.
/// The top-defined sum read from the bottom.
pub proof fn lemma_limb_sum_cons(t: Seq<u64>)  // reference-only: the learner's helper
    requires
        t.len() > 0,
    ensures
        limb_sum(t) == t[0] as nat + limb_sum(t.drop_first()),
    decreases t.len(),
{
    if t.len() > 1 {
        lemma_limb_sum_cons(t.drop_last());
        assert(t.drop_last().drop_first() =~= t.drop_first().drop_last());
        assert(t.drop_first().last() == t.last());
    } else {
        assert(limb_sum(t.drop_last()) == 0);
        assert(limb_sum(t.drop_first()) == 0);
    }
}

// item: Q14.H3v S7
// uses: ghost, invariant, lemma-recursion
// pair: Q14.H3d
// form: loop-dir:i:down
// triv: { 0 }
// cfree: {
// cfree:     let mut s: u128 = 0;
// cfree:     let mut i: usize = 0;
// cfree:     while i < v.len()
// cfree:         invariant
// cfree:             i <= v.len(),
// cfree:             s == limb_sum(v@.subrange(0, i as int)),
// cfree:             s <= i * bound,
// cfree:             forall|k: int| 0 <= k < v.len() ==> v@[k] <= bound,
// cfree:             v.len() * bound <= u128::MAX,
// cfree:         decreases v.len() - i,
// cfree:     {
// cfree:         proof {
// cfree:             lemma_mul_is_distributive_add_other_way(bound as int, i as int, 1);
// cfree:             lemma_mul_inequality((i + 1) as int, v.len() as int, bound as int);
// cfree:             assert(v@.subrange(0, i + 1).drop_last() =~= v@.subrange(0, i as int));
// cfree:         }
// cfree:         s = s + v[i] as u128;
// cfree:         i = i + 1;
// cfree:     }
// cfree:     proof { assert(v@.subrange(0, v.len() as int) =~= v@); }
// cfree:     s
// cfree: }
// cfree: {
// cfree:     let mut s: u128 = 0;
// cfree:     let mut i: usize = v.len();
// cfree:     while i > 0
// cfree:         invariant
// cfree:             i <= v.len(),
// cfree:             s == limb_sum(v@.subrange(0, v.len() - i)),
// cfree:             s <= (v.len() - i) * bound,
// cfree:             forall|k: int| 0 <= k < v.len() ==> v@[k] <= bound,
// cfree:             v.len() * bound <= u128::MAX,
// cfree:         decreases i,
// cfree:     {
// cfree:         let j: usize = v.len() - i;
// cfree:         proof {
// cfree:             lemma_mul_is_distributive_add_other_way(bound as int, j as int, 1);
// cfree:             lemma_mul_inequality((j + 1) as int, v.len() as int, bound as int);
// cfree:             assert(v@.subrange(0, j + 1).drop_last() =~= v@.subrange(0, j as int));
// cfree:         }
// cfree:         s = s + v[j] as u128;
// cfree:         i = i - 1;
// cfree:     }
// cfree:     proof { assert(v@.subrange(0, v.len() as int) =~= v@); }
// cfree:     s
// cfree: }
/// **H3.** Reference: a loop from the top limb down keeps the suffix's sum and the bound
/// `s <= (len - i) * bound`, which the ghost `bound` gives and the overflow check needs
/// (`lemma_mul_inequality`, distributivity); the helper turns the top-defined `limb_sum`
/// of a suffix into its low limb plus the rest. The first `cfree:` answer is the loop the other
/// way, from the low limb up: the top-defined `limb_sum` then extends by one `drop_last`
/// per step and no lemma is needed. It verifies, so the block's `loop-dir:i:down` form is
/// what kills it; the second is the same loop with `i` stepping down and the limb read at
/// `v.len() - i` (DV5c fix round), which the form's index rule kills
/// (Solutions/plans/Q14-code-notes.md).
pub fn sum_limbs(v: &Vec<u64>, Ghost(bound): Ghost<nat>) -> (r: u128)
    requires
        forall|i: int| 0 <= i < v.len() ==> v@[i] <= bound,
        v.len() * bound <= u128::MAX,
    ensures
        r == limb_sum(v@),
{
    let mut s: u128 = 0;
    let mut i: usize = v.len();
    while i > 0
        invariant
            i <= v.len(),
            s == limb_sum(v@.subrange(i as int, v.len() as int)),
            s <= (v.len() - i) * bound,
            forall|k: int| 0 <= k < v.len() ==> v@[k] <= bound,
            v.len() * bound <= u128::MAX,
        decreases i,
    {
        i = i - 1;
        proof {
            let t = v@.subrange(i as int, v.len() as int);
            lemma_limb_sum_cons(t);
            assert(t.drop_first() =~= v@.subrange(i + 1, v.len() as int));
            assert(v@[i as int] <= bound);
            lemma_mul_is_distributive_add_other_way(bound as int, (v.len() - i - 1) as int, 1);
            lemma_mul_inequality((v.len() - i) as int, v.len() as int, bound as int);
            assert(s + v@[i as int] <= v.len() * bound);
        }
        s = s + v[i] as u128;
    }
    proof {
        assert(v@.subrange(0, v.len() as int) =~= v@);
    }
    s
}

fn sum_limbs_check() {
    let mut v: Vec<u64> = Vec::new();
    v.push(7);
    v.push(u64::MAX);
    let r = sum_limbs(&v, Ghost(u64::MAX as nat));
    proof {
        assert(v@.drop_last() =~= seq![7u64]);
        assert(v@.drop_last().drop_last() =~= Seq::<u64>::empty());
        assert(limb_sum(Seq::<u64>::empty()) == 0);
        assert(limb_sum(v@.drop_last()) == 7);
    }
    assert(r == 7 + u64::MAX as u128);
}

} // verus!
