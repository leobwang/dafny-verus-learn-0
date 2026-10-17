//! # Q06 — The machine and the verifier loop (Reference Solution)
//!
//! Hole-free reference for `verus/q/q06_machine/src/lib.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise file. Every hole is filled and H4's property suite (the `#[cfg(test)]` module
//! after `verus!`) is live. The file is silent: `scripts/vcheck --ref` on the crate prints
//! only the summary line. Every output the module quotes is pinned: the count pins in
//! `expected/Q06.counts`, the statement freeze in `expected/Q06.freeze`, the WRITE-card
//! failure demos by their in-file `// EXPECT` lines, and the divergence demos by their
//! sealed sidecars under `expected/specimens/Q06/`. No fn carries a resource attribute (H3
//! is a budget item).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l3::*;

verus! {

// =========================================================================================
// The prediction block.
// =========================================================================================

// =========================================================================================
// Test-out (closed book)
// =========================================================================================

// item: Q06.T1v S11
// uses: trigger
// pair: Q06.T1d
/// **T1.** (test-out) A fact about every limb, used for limb 1.
///
/// Reference: the hypothesis's trigger is `limb_at(s, k)`, so the solver instantiates it
/// only for a term of that shape. `s[1]` is not one; the assertion names `limb_at(s, 1)`,
/// which fires the hypothesis at `k = 1`, and `limb_at(s, 1)` unfolds to `s[1]` because
/// `1 < s.len()`.
pub proof fn lemma_second_limb(s: Seq<u64>)
    requires
        s.len() > 1,
        forall|k: int| 0 <= k < s.len() ==> #[trigger] limb_at(s, k) < 100,
    ensures
        s[1] < 100,
{
    assert(limb_at(s, 1) < 100);
}

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q06.W1v S11
/// **W1.** An opaque spec fn and a scoped `reveal`. Outside a `reveal`, the verifier knows
/// `twice` by its signature only. `reveal(twice)` inside an `assert … by { … }` unfolds it
/// for that assertion alone: the asserted fact is what the rest of the proof can see,
/// never the definition.
#[verifier::opaque]
pub open spec fn twice(x: nat) -> nat {
    2 * x
}

pub proof fn lemma_twice_even(x: nat)
    ensures
        twice(x) % 2 == 0,
{
    assert(twice(x) == 2 * x) by {
        reveal(twice);
    }
    // Here the equation is known and the body of twice is not: the postcondition follows
    // from the equation.
}

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q06/)
// =========================================================================================

// item: Q06.C1v S11 write:trigger
// C1 — card: triggers (`#[trigger]`).
// Jurisdiction: a quantified fact is used only for the terms that match its trigger, so a
// proof switches it on by mentioning such a term. Success: `lemma_odd_bound` asserts a fact
// about `odd(3)`, which fires the hypothesis at `i = 3`. Failure:
// specimens/Q06/card-c1v.rs.specimen (the same proof fn; no term of the trigger's shape
// appears).
pub open spec fn odd(i: int) -> int {
    2 * i + 1
}

pub proof fn lemma_odd_bound(s: Seq<u64>)
    requires
        s.len() > 3,
        forall|i: int| 0 <= i < s.len() ==> (s[i] as int) < #[trigger] odd(i),
    ensures
        s[3] < 7,
{
    assert((s[3] as int) < odd(3));
}

// item: Q06.C2v S11 write:opaque-reveal
// C2 — card: `#[verifier::opaque]` and a scoped `reveal`.
// Jurisdiction: an opaque spec fn stays folded until a `reveal` unfolds it, inside that
// reveal's scope only, so the solver sees the body exactly where a proof asks for it.
// Success: `lemma_mid_between` reveals `mid` for its whole body. Failure:
// specimens/Q06/card-c2v.rs.specimen (the reveal is confined to an `assert … by` and the
// body is needed after it).
#[verifier::opaque]
pub open spec fn mid(a: nat, b: nat) -> nat {
    (a + b) / 2
}

pub proof fn lemma_mid_between(a: nat, b: nat)
    requires
        a <= b,
    ensures
        a <= mid(a, b) <= b,
{
    reveal(mid);
}

// item: Q06.C3v S11 write:rlimit
// C3 — card: proofs that fit the resource limit.
// Jurisdiction: every crate verifies under one pinned rlimit; a proof that exhausts it
// gets an out-of-resource verdict, which says nothing about whether the goal is true or
// nearly proved. Make the proof fit by changing how it is proved, never by raising the
// limit. Success: `lemma_tri_sixty` hands the arithmetic to Verus's interpreter
// (`by (compute_only)`), which spends no solver budget on it. Failure:
// specimens/Q06/card-c3v.rs.specimen (the same goal, the solver unfolding `tri` with a
// large fuel).
pub open spec fn tri(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        0
    } else {
        n + tri((n - 1) as nat)
    }
}

pub proof fn lemma_tri_sixty()
    ensures
        tri(60) == 1830,
{
    assert(tri(60) == 1830) by (compute_only);  // did: evaluated by the interpreter
}

// item: Q06.C4v S12 write:property-test
// C4 — card: bounded property tests.
// Jurisdiction: before a proof, check a property of a candidate's outputs on chosen
// samples. The checker is a verified exec fn whose postcondition is two-sided (`ok`
// exactly when every output has the property), so no constant body verifies; Rust
// `#[test]`s outside `verus!` (the `card_c4` module at the end of this file) run it on the
// outputs of a correct candidate (it must pass) and of a planted one (it must be
// rejected): `scripts/vcheck --test` on the crate. The verifier checks the checker; the
// test run checks the candidates. Success: `all_below`, `clip`, `clip_planted` and
// `card_c4`. Failure: specimens/Q06/card-c4v.rs.specimen (a one-sided checker, which a
// constant body satisfies).
pub fn all_below(xs: &Vec<u64>, bound: u64) -> (ok: bool)
    ensures
        ok == (forall|k: int| 0 <= k < xs.len() ==> #[trigger] xs@[k] < bound),
{
    let mut ok = true;
    let mut k: usize = 0;
    while k < xs.len()
        invariant
            k <= xs.len(),
            ok == (forall|j: int| 0 <= j < k ==> #[trigger] xs@[j] < bound),
        decreases xs.len() - k,
    {
        ok = ok && xs[k] < bound;
        k = k + 1;
    }
    ok
}

/// A candidate that clips to the limit 1000, and a planted one that lets 1000 itself
/// through.
pub fn clip(x: u64) -> u64 {
    if x < 1000 {
        x
    } else {
        999
    }
}

pub fn clip_planted(x: u64) -> u64 {
    if x <= 1000 {
        x
    } else {
        999
    }
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q06.H1v S11
// uses: trigger
// pair: Q06.H1d
/// **H1.** The first prefix is below one limb's weight.
///
/// Reference: the hypothesis fires only on a `weight(k)` term, and `weight` is opaque.
/// L3's `lemma_weight_zero` and `lemma_weight_succ(0)` give `weight(1) == BASE * 1`; the
/// assertion `weight(1) == BASE` names the term `weight(1)`, which instantiates the
/// hypothesis at `k = 1`.
pub proof fn lemma_first_prefix(s: Seq<u64>)
    requires
        s.len() >= 1,
        forall|k: nat| k <= s.len() ==> seq_to_nat(s.subrange(0, k as int)) < #[trigger] weight(k),
    ensures
        seq_to_nat(s.subrange(0, 1)) < BASE,
{
    lemma_weight_zero();
    lemma_weight_succ(0);
    assert(weight(1) == BASE);
}

/// Given (not an item): two limbs packed into one number. Opaque: its body is hidden from
/// every proof that does not reveal it.
#[verifier::opaque]
pub open spec fn pack(lo: u64, hi: u64) -> nat {
    lo as nat + BASE * hi as nat
}

// item: Q06.H2v S11
// uses: opaque-reveal
// pair: Q06.H2d
/// **H2.** Packing two limbs gives the value of the two-limb sequence.
///
/// Reference: `reveal(pack)` unfolds `pack` for the whole body. `seq_to_nat` unfolds one
/// limb per step; each step needs the tail named as a sequence the solver knows
/// (`drop_first` of `seq![lo, hi]` is `seq![hi]`, of `seq![hi]` the empty sequence), and
/// the two value assertions close the empty and the one-limb case.
pub proof fn lemma_pack_to_nat(lo: u64, hi: u64)
    ensures
        pack(lo, hi) == seq_to_nat(seq![lo, hi]),
{
    reveal(pack);  // did: unfolds pack's body for this proof
    let s = seq![lo, hi];
    assert(s.drop_first() =~= seq![hi]);
    assert(seq![hi].drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(Seq::<u64>::empty()) == 0);
    assert(seq_to_nat(seq![hi]) == hi as nat);
}

// item: Q06.H3v S11
// uses: rlimit
/// **H3.** The value of an append. This attempt does not verify at the pinned rlimit:
///
///     pub proof fn lemma_seq_to_nat_append(a: Seq<u64>, b: Seq<u64>)
///         ensures
///             seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
///         decreases a.len(),
///     {
///         assert forall|k: nat| #[trigger] weight(k) * BASE == weight(k + 1) by {
///             lemma_weight_succ(k);
///         }
///         if a.len() > 0 {
///             lemma_seq_to_nat_append(a.drop_first(), b);
///         } else {
///             lemma_weight_zero();
///         }
///     }
///
/// Reference: drop the quantified step (each instance makes a new `weight` term, which
/// fires it again) and give the recursion's step explicitly: the tail of `a + b` is
/// `a.drop_first() + b` (extensionality), the induction hypothesis on it,
/// `lemma_weight_succ(k)` for the one weight step, and associativity and distributivity to
/// regroup `BASE * (… + weight(k) * …)`. The empty case is `weight(0) == 1` and
/// `a + b =~= b`. No resource attribute.
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

/// Given (not an item): one sample's check, in `u128` arithmetic: `lo` and `hi` split the
/// sum `a + b` into a low limb and a carry.
pub fn split_matches(a: u64, b: u64, lo: u64, hi: u64) -> (r: bool)
    ensures
        r == (lo as nat + hi as nat * BASE == a as nat + b as nat),
{
    lo as u128 + (hi as u128) * 0x1_0000_0000_0000_0000u128 == a as u128 + b as u128
}

// item: Q06.H4v S12
// uses: property-test
// pair: Q06.H4d
/// **H4.** A bounded property check of limb-adder results.
///
/// Reference: one pass over the samples that returns `false` at the first sample whose
/// result does not split its sum (the given `split_matches` checks one sample). The
/// invariant says that every result before `k` splits its sum, so the `false` exit has a
/// witness and the `true` exit has the whole `forall`; the default trivial body `false`
/// fails the `==`. The suite after `verus!` runs it: `add_carry_a` splits every boundary
/// sample, and `add_carry_b` reports a carry whenever the wrapped sum equals `a`, which
/// happens already at `(0, 0)`.
pub fn check_split_results(samples: &Vec<(u64, u64)>, got: &Vec<(u64, u64)>) -> (ok: bool)
    requires
        got.len() == samples.len(),
    ensures
        ok == (forall|k: int| 0 <= k < samples.len() ==>
            (#[trigger] got@[k]).0 as nat + got@[k].1 as nat * BASE == samples@[k].0 as nat
                + samples@[k].1 as nat),
{
    let mut k: usize = 0;
    while k < samples.len()
        invariant
            k <= samples.len(),
            got.len() == samples.len(),
            forall|j: int| 0 <= j < k ==>
                (#[trigger] got@[j]).0 as nat + got@[j].1 as nat * BASE == samples@[j].0 as nat
                    + samples@[j].1 as nat,
        decreases samples.len() - k,
    {
        if !split_matches(samples[k].0, samples[k].1, got[k].0, got[k].1) {
            return false;
        }
        k = k + 1;
    }
    true
}

/// The two candidates the suite runs (given): a correct limb adder and a planted one.
pub fn add_carry_a(a: u64, b: u64) -> (u64, u64) {
    let s = a.wrapping_add(b);
    (s, if s < a { 1 } else { 0 })
}

pub fn add_carry_b(a: u64, b: u64) -> (u64, u64) {
    let s = a.wrapping_add(b);
    (s, if s <= a { 1 } else { 0 })
}

// =========================================================================================
// Final section: divergence card.
// =========================================================================================

// item: Q06.C6dv S10 diverge:q06-c6
// C6 — divergence card. Demos: specimens/Q06/card-c6dv-d.dfy.specimen and
// specimens/Q06/card-c6dv-v.rs.specimen.

} // verus!

// C4's tests (given, live): the outputs of a correct candidate and of a planted one.
#[cfg(test)]
mod card_c4 {
    use super::*;

    fn samples() -> Vec<u64> {
        vec![0, 999, 1000, 1001, u64::MAX]
    }

    #[test]
    fn clip_passes() {
        let got: Vec<u64> = samples().iter().map(|&x| clip(x)).collect();
        assert!(all_below(&got, 1000));
    }

    #[test]
    fn clip_planted_rejected() {
        let got: Vec<u64> = samples().iter().map(|&x| clip_planted(x)).collect();
        assert!(!all_below(&got, 1000));
    }
}

// H4's suite (live in the reference).
#[cfg(test)]
mod props {
    use super::*;

    fn boundary() -> Vec<(u64, u64)> {
        vec![(0, 0), (1, u64::MAX), (u64::MAX, 1), (u64::MAX, u64::MAX), (1u64 << 63, 1u64 << 63)]
    }

    fn run(f: fn(u64, u64) -> (u64, u64)) -> bool {
        let s = boundary();
        let got: Vec<(u64, u64)> = s.iter().map(|&(a, b)| f(a, b)).collect();
        check_split_results(&s, &got)
    }

    #[test]
    fn good_passes() {
        assert!(run(add_carry_a));
    }

    #[test]
    fn planted_rejected() {
        assert!(!run(add_carry_b));
    }
}
