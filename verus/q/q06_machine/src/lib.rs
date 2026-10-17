//! # Q06 — The machine and the verifier loop (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l3` (`use
//! qg_bignat_l3::*;` brings all three layers' names), the vstd prelude and vstd's
//! multiplication lemmas (`vstd::arithmetic::mul`), nothing else: no earlier exercise crate.
//! The layers are frozen and complete; read them, never edit them.
//!
//! How to work this file:
//! 1. Predictions first: every prediction of the module (the Dafny file's prediction
//!    block, specimens/Q06/P3d and P4v, and the Python file's prediction block); record the
//!    first tries with `scripts/firsttry.sh Q06 --check` before you run anything they are
//!    about. This file's prediction block only points to them.
//! 2. Test-out next, closed book: T1 (below) before any reading, without its hints.
//!    `scripts/firsttry.sh Q06 --check` records its first try, and refuses to while any
//!    prediction of the module is unrecorded. If both files' T1 pass on that first try,
//!    you may skip the chapter section on triggers.
//! 3. Replace each hole, then uncomment the checks beneath it (H4's property suite, after
//!    the end of `verus!`, included).
//! 4. Done = `scripts/vcheck --gate verus/q/q06_machine` prints only the summary line and
//!    exits 0, `scripts/vaudit verus/q/q06_machine` reports no finding,
//!    `scripts/vcheck --test verus/q/q06_machine` passes every test, AND
//!    `scripts/firsttry.sh Q06 --report --strict` exits 0. H3 counts only with no resource
//!    attribute anywhere in this file.
//! 5. Stuck for 20 minutes? /tutor Q06.
//!
//! This file ships with exactly 5 holes: T1 (test-out) and H1–H4, each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one
//! counted diagnostic). Commit every prediction BEFORE you run anything it is about, open
//! later files, or read CI, the registry or the plan: their checks and headers give some
//! predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header
//! (dafny/Q/Q06_Machine/std/Q06_Machine.dfy). Exit (closed book): src/exit.rs here and the
//! Dafny exit file, scored once by `scripts/firsttry.sh Q06 --exit`; src/exit.rs is never
//! part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l3::*;

verus! {

// =========================================================================================
// The prediction block. Commit every prediction of this module before you read past this
// block (the test-out T1 included), and record the first tries:
//     scripts/firsttry.sh Q06 --check
// This file holds none: the Dafny file's prediction block holds the cross-language ones
// (P1, P2, P5, P6, P8), specimens/Q06/ holds P3 and P4, and the Python file
// harness/q/fvh_q/q06_stats.py holds P7 and P9.
// =========================================================================================

// =========================================================================================
// Test-out (closed book: after every prediction of this module is recorded, before any
// reading; `scripts/firsttry.sh Q06 --check` refuses T1's first try until then)
// =========================================================================================

// item: Q06.T1v S11
// uses: trigger
// pair: Q06.T1d
/// **T1.** (test-out) A fact about every limb, used for limb 1. The quantified hypothesis
/// carries an explicit trigger. Which term must the proof mention before the solver uses
/// the hypothesis for limb 1?
pub proof fn lemma_second_limb(s: Seq<u64>)
    requires
        s.len() > 1,
        forall|k: int| 0 <= k < s.len() ==> #[trigger] limb_at(s, k) < 100,
    ensures
        s[1] < 100,
{
    #[verifier::proof_note("Q06.T1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): the trigger is the shape of term that switches the hypothesis on.
// Hint(2): one `assert` about limb 1, written in the trigger's own terms.

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
/// **H1.** The first prefix is below one limb's weight. The hypothesis bounds every prefix
/// by a weight, its trigger is `weight(k)`, and `weight` (layer L3) is opaque. Which term
/// must appear before the solver uses the hypothesis for the prefix of length 1, and which
/// L3 facts say what that term equals?
pub proof fn lemma_first_prefix(s: Seq<u64>)
    requires
        s.len() >= 1,
        forall|k: nat| k <= s.len() ==> seq_to_nat(s.subrange(0, k as int)) < #[trigger] weight(k),
    ensures
        seq_to_nat(s.subrange(0, 1)) < BASE,
{
    #[verifier::proof_note("Q06.H1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): L3 gives `weight`'s two defining equations as proof fns.
// Hint(2): call them for the step you need, then `assert` the value of that weight.

/// Given (not an item): two limbs packed into one number. Opaque: its body is hidden from
/// every proof that does not reveal it.
#[verifier::opaque]
pub open spec fn pack(lo: u64, hi: u64) -> nat {
    lo as nat + BASE * hi as nat
}

// item: Q06.H2v S11
// uses: opaque-reveal
// pair: Q06.H2d
/// **H2.** Packing two limbs gives the value of the two-limb sequence. `pack` is opaque.
/// Where must its body be visible, and what must the solver be told about the tails of
/// `seq![lo, hi]` before `seq_to_nat` unfolds twice?
pub proof fn lemma_pack_to_nat(lo: u64, hi: u64)
    ensures
        pack(lo, hi) == seq_to_nat(seq![lo, hi]),
{
    #[verifier::proof_note("Q06.H2v")] assume(false);  // HOLE: replace this line
}
// Hint(1): reveal `pack` in the scope that needs its body.
// Hint(2): state each `drop_first` as a sequence you name (`=~=`), then the value of the
//    empty and of the one-limb sequence.

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
/// Write a proof that verifies at the pinned limit, with no resource attribute. What does
/// each instance of the quantified step hand back to the solver?
pub proof fn lemma_seq_to_nat_append(a: Seq<u64>, b: Seq<u64>)
    ensures
        seq_to_nat(a + b) == seq_to_nat(a) + weight(a.len()) * seq_to_nat(b),
    decreases a.len(),
{
    #[verifier::proof_note("Q06.H3v")] assume(false);  // HOLE: replace this line
}
// Hint(1): keep the recursion, drop the quantified step, and give the one weight step the
//    recursion needs; the tail of `a + b` must be named as `a.drop_first() + b`.
// Hint(2): vstd's multiplication lemmas (`vstd::arithmetic::mul`, imported) regroup
//    `BASE * (x + weight(k) * y)`.

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
/// **H4.** A bounded property check of limb-adder results: `check_split_results` is true
/// exactly when every result `got[k]` splits the sum of `samples[k]` into a low limb and a
/// carry. Its postcondition is two-sided, so no constant body verifies. Then uncomment the
/// suite after the end of `verus!`: the correct candidate `add_carry_a` must pass and the
/// planted `add_carry_b` must be rejected under `scripts/vcheck --test
/// verus/q/q06_machine`. Which invariant carries "every result so far splits its sum" to
/// the end of the loop?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn check_split_results(samples: &Vec<(u64, u64)>, got: &Vec<(u64, u64)>) -> (ok: bool)
    requires
        got.len() == samples.len(),
    ensures
        ok == (forall|k: int| 0 <= k < samples.len() ==>
            (#[trigger] got@[k]).0 as nat + got@[k].1 as nat * BASE == samples@[k].0 as nat
                + samples@[k].1 as nat),
{
    unimplemented!()
}
// Hint(1): one loop over the samples that stops at the first result that does not split
//    its sum; `split_matches` checks one sample.
// Hint(2): besides the per-sample clause, the invariant restates the two lengths.

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
// Final section: divergence card. Record every prediction of this module
// (scripts/firsttry.sh Q06 --check) before you read on or open its demos.
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

// H4's suite: uncomment it once `check_split_results` is written.
// Uncomment as you go:
// #[cfg(test)]
// mod props {
//     use super::*;
//
//     fn boundary() -> Vec<(u64, u64)> {
//         vec![(0, 0), (1, u64::MAX), (u64::MAX, 1), (u64::MAX, u64::MAX), (1u64 << 63, 1u64 << 63)]
//     }
//
//     fn run(f: fn(u64, u64) -> (u64, u64)) -> bool {
//         let s = boundary();
//         let got: Vec<(u64, u64)> = s.iter().map(|&(a, b)| f(a, b)).collect();
//         check_split_results(&s, &got)
//     }
//
//     #[test]
//     fn good_passes() {
//         assert!(run(add_carry_a));
//     }
//
//     #[test]
//     fn planted_rejected() {
//         assert!(!run(add_carry_b));
//     }
// }
