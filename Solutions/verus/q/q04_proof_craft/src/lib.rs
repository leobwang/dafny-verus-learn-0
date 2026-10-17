//! # Q04 — Proof craft, loops and libraries, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q04_proof_craft/src/lib.rs` (author-only; never
//! learner-visible). Same crate layout, imports, names, statements, item markers and order
//! as the exercise file. Every hole is filled, every check is live, and the verdict
//! switches are enabled; the verdict answers are in `Solutions/slots/Q04.slots`, their
//! hashes in `expected/Q04.pins`. The crate's library module is `src/library.rs`.
//!
//! The file is silent: `scripts/vcheck --ref` on the crate prints only the summary line.
//! Every output the module quotes is pinned (`expected/Q04.counts`, `expected/Q04.freeze`,
//! the card demos' `// EXPECT` lines and sidecars).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::calc;
use qg_bignat_l3::*;

mod library;

verus! {

// =========================================================================================
// The prediction block. Commit every prediction of this module before you read past this
// block, and record the first tries:
//     scripts/firsttry.sh Q04 --check
// The verdict answers go in slots/Q04.slots. The Dafny file's prediction block holds the
// cross-language predictions (P1, P3, P8); specimens/Q04/ holds P4, P5 and P9;
// dafny/checks/Q04_checks.dfy holds P2.
// Verdict vocabulary for `V:<v>` answers: `ok` (verifies), `fail` (a verification error),
// `timeout` (out of resource or time), `err:<stage>` (refused before verification;
// <stage> as scripts/vcheck prints it: `parse` or `resolve`).
// =========================================================================================

// item: Q04.P6v S3 verdict
// **P6.** Choosing a prover. Three crates of their own, each checked with
// `scripts/vcheck`. Each holds `use vstd::prelude::*;` and, inside `verus! { }`, this one
// proof fn, its body one assertion of its postcondition closed by a different prover:
/*
    pub proof fn lemma_limb_product_bound(x: u64, y: u64, c: u64)
        ensures
            (x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat,
    {
        assert((x as nat) * (y as nat) + (c as nat) <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFnat)
            by (<prover>);
    }

  where <prover> is
    [a] nonlinear_arith
    [b] bit_vector
    [c] compute
*/
// Which of the three crates verify?
// Answer form: the labels that verify, in label order, separated by single spaces, or
// `none`.
// CHECK P6v

// item: Q04.P7v S5 verdict
// **P7.** A library group in a proof that needs none. In a file of its own, with
// `use vstd::prelude::*;` and `use qg_bignat_l3::*;`, this proof fn verifies as written
// (its body is empty):
/*
    pub proof fn at_least_low_limb(s: Seq<u64>)
        requires
            s.len() > 0,
        ensures
            seq_to_nat(s) >= s[0],
    {
    }
*/
// Now add, as the body's only line,
//     broadcast use vstd::arithmetic::mul::group_mul_properties;
// and check the file with `scripts/vcheck --module Q04 <file>`. What does it report?
// Answer form: `V:<v>` with the verdict vocabulary above.
// CHECK P7v

// =========================================================================================
// Test-out (closed book, before any reading, after the prediction block)
// =========================================================================================

// item: Q04.T1v S4
// uses: lemma-recursion, forall
// pair: Q04.T1d
/// **T1.** (test-out) A value of zero means zero limbs.
///
/// Reference: recursion on `s.drop_first()`. `seq_to_nat(s) == 0` forces `s[0] == 0` and
/// a zero value for the rest, so the call applies; the `assert forall … by` covers index 0
/// directly and every other index through `s[i] == s.drop_first()[i - 1]`.
pub proof fn lemma_zero_value_zero_limbs(s: Seq<u64>)
    requires
        seq_to_nat(s) == 0,
    ensures
        forall|i: int| 0 <= i < s.len() ==> s[i] == 0,
    decreases s.len(),
{
    if s.len() > 0 {
        lemma_zero_value_zero_limbs(s.drop_first());
        assert forall|i: int| 0 <= i < s.len() implies s[i] == 0 by {
            if i > 0 {
                assert(s[i] == s.drop_first()[i - 1]);
            }
        }
    }
}

proof fn zero_value_zero_limbs_check(s: Seq<u64>)
    requires
        s.len() == 2,
        seq_to_nat(s) == 0,
{
    lemma_zero_value_zero_limbs(s);
    assert(s[1] == 0);
    assert(s[0] == 0);
}

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q04.W1v S3
/// **W1.** The chain of the Dafny file's W1, in `calc!`: the relation comes first, then
/// each line, and the braces after a line hold the hint for the step to the next line.
/// L3's equation for `weight` is `weight(n + 1) == BASE * weight(n)`; the chain turns the
/// product around.
pub proof fn lemma_weight_succ_comm(n: nat)
    ensures
        weight(n + 1) == weight(n) * BASE,
{
    calc! {
        (==)
        weight(n + 1); { lemma_weight_succ(n); }
        BASE * weight(n);
        (==) {}
        weight(n) * BASE;
    }
}

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q04/)
// =========================================================================================

// item: Q04.C1v S3 write:calc
// C1 — card: `calc!` chains.
// Jurisdiction: an equality (or `<=`, `<`) that takes several small steps; the relation
// comes first, and the braces after a line prove the step to the next line. Success:
// `lemma_seq_to_nat_two_steps` unfolds `seq_to_nat` twice. Failure:
// specimens/Q04/card-c1v.rs.specimen (a chain with one false step).
pub proof fn lemma_seq_to_nat_two_steps(s: Seq<u64>)
    requires
        s.len() >= 2,
    ensures
        seq_to_nat(s) == s[0] as nat + BASE * (s[1] as nat + BASE * seq_to_nat(
            s.drop_first().drop_first(),
        )),
{
    calc! {
        (==)
        seq_to_nat(s); {}
        s[0] as nat + BASE * seq_to_nat(s.drop_first()); { assert(s.drop_first()[0] == s[1]); }
        s[0] as nat + BASE * (s[1] as nat + BASE * seq_to_nat(s.drop_first().drop_first()));
    }
}

// item: Q04.C2v S2 write:forall
// C2 — card: `assert forall … implies … by`.
// Jurisdiction: a quantified goal whose instances each need a step of their own; the
// assertion names the bound variable, `implies` puts the range in front of the `by`
// block, and the block proves one instance. Success: `lemma_push_zero_each` calls L1's
// worked proof fn once per sequence. Failure: specimens/Q04/card-c2v.rs.specimen (the same,
// with an empty `by` block).
pub proof fn lemma_push_zero_each(ss: Seq<Seq<u64>>)
    ensures
        forall|j: int| 0 <= j < ss.len() ==> seq_to_nat(#[trigger] ss[j].push(0)) == seq_to_nat(ss[j]),
{
    assert forall|j: int| 0 <= j < ss.len() implies seq_to_nat(#[trigger] ss[j].push(0))
        == seq_to_nat(ss[j]) by {
        lemma_seq_to_nat_push_zero(ss[j]);
    }
}

// item: Q04.C3v S4 write:lemma-recursion
// C3 — card: a proof fn that calls itself (induction by hand).
// Jurisdiction: a fact about a recursive definition, proved by calling the same proof fn on
// a smaller argument; its `decreases` says why the calls end. Success: `lemma_weight_above`
// (`weight` is L3's power of `BASE`, reached through its two equations). Failure:
// specimens/Q04/card-c3v.rs.specimen (the same proof fn without its call).
pub proof fn lemma_weight_above(n: nat)
    ensures
        n < weight(n),
    decreases n,
{
    if n == 0 {
        lemma_weight_zero();
    } else {
        lemma_weight_above((n - 1) as nat);
        lemma_weight_succ((n - 1) as nat);
    }
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q04.H2v S2
// uses: forall
/// **H2.** A first difference that favours `b` makes `a` smaller.
///
/// Reference: one `assert forall … implies … by` over the index `i`; with the range and the
/// two hypotheses in front of the `by` block, each instance is L3's `lemma_lt_at(a, b, i)`.
pub proof fn lemma_first_difference(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == b.len(),
    ensures
        forall|i: int|
            0 <= i < a.len() && #[trigger] a[i] < b[i] && (forall|j: int|
                i < j < a.len() ==> a[j] == b[j]) ==> seq_to_nat(a) < seq_to_nat(b),
{
    assert forall|i: int|
        0 <= i < a.len() && #[trigger] a[i] < b[i] && (forall|j: int|
            i < j < a.len() ==> a[j] == b[j]) implies seq_to_nat(a) < seq_to_nat(b) by {
        lemma_lt_at(a, b, i);
    }
}

proof fn first_difference_check(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == 2,
        b.len() == 2,
        a[1] < b[1],
{
    lemma_first_difference(a, b);
    assert(seq_to_nat(a) < seq_to_nat(b));
}

} // verus!
