//! # Q04 — Proof craft, loops and libraries, Verus half (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l3` (`use
//! qg_bignat_l3::*;` brings all three layers' names), the vstd prelude and vstd's `calc!`
//! macro, nothing else: no earlier exercise crate. This file, the crate root, imports no
//! `vstd::arithmetic` lemma; the crate's library module, `src/library.rs` (declared below by
//! `mod library;`), does. Work this file before that one. The layers are frozen and
//! complete; read them, never edit them.
//!
//! How to work this file (the moderate tier puts the predictions first):
//! 1. Predictions first: P6 and P7 (the prediction block below; their answers go in
//!    slots/Q04.slots), with every other prediction of the module (the Dafny file's
//!    prediction block, specimens/Q04/, dafny/checks/Q04_checks.dfy); record the first
//!    tries with `scripts/firsttry.sh Q04 --check` before you run anything they are about.
//! 2. Then the test-out, closed book: T1 (below), before any reading, without its hints.
//!    Run `scripts/firsttry.sh Q04 --check` again, which records your first try (it runs
//!    T1's commented checks in a scratch copy, and refuses while a Q04 prediction is
//!    unrecorded), and only then uncomment those checks.
//! 3. Replace each hole, then uncomment the checks beneath it; then src/library.rs.
//! 4. Done = `scripts/vcheck --gate verus/q/q04_proof_craft` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q04_proof_craft` reports no finding, AND
//!    `scripts/firsttry.sh Q04 --report --strict` exits 0. The crate's gate covers this
//!    file and src/library.rs together.
//! 5. Stuck for 20 minutes? /tutor Q04.
//!
//! This file ships with exactly 2 holes: T1 (test-out) and H2, each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one
//! counted diagnostic); src/library.rs ships 4. Commit every prediction BEFORE you run
//! anything it is about, open later files, or read CI, the registry or the plan: their
//! checks and headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header
//! (dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy). Exit (closed book): src/exit.rs here
//! and the Dafny exit file, scored once by `scripts/firsttry.sh Q04 --exit`; src/exit.rs
//! and src/agent.rs are never part of this crate's build.
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
// SLOT: CHECK P6v

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
// SLOT: CHECK P7v

// =========================================================================================
// Test-out (closed book, before any reading, after the prediction block)
// =========================================================================================

// item: Q04.T1v S4
// uses: lemma-recursion, forall
// pair: Q04.T1d
/// **T1.** (test-out) A value of zero means zero limbs: if `seq_to_nat(s) == 0`, every limb
/// of `s` is 0. Prove it by recursion (`decreases s.len()` ships). What does a zero value
/// tell you about `s[0]` and about the rest, and how does a fact about `s.drop_first()`
/// reach index `i` of `s`?
pub proof fn lemma_zero_value_zero_limbs(s: Seq<u64>)
    requires
        seq_to_nat(s) == 0,
    ensures
        forall|i: int| 0 <= i < s.len() ==> s[i] == 0,
    decreases s.len(),
{
    #[verifier::proof_note("Q04.T1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): call the proof fn on `s.drop_first()`, then prove the `forall` with
//    `assert forall … implies … by`.
// Hint(2): limb `i > 0` of `s` is limb `i - 1` of `s.drop_first()`: say so in an `assert`.

proof fn zero_value_zero_limbs_check(s: Seq<u64>)
    requires
        s.len() == 2,
        seq_to_nat(s) == 0,
{
    // Uncomment as you go:
    // lemma_zero_value_zero_limbs(s);
    // assert(s[1] == 0);
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
/// **H2.** A first difference that favours `b` makes `a` smaller: for two limb sequences
/// of one length, if at some index `i` the limb of `a` is below that of `b` and every limb
/// above `i` agrees, then `seq_to_nat(a) < seq_to_nat(b)`. Layer L3's `lemma_lt_at` is
/// this fact for one given index. Method clause: one `assert forall … by`. What must the
/// `by` block know about `i` before it can call the given proof fn?
pub proof fn lemma_first_difference(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == b.len(),
    ensures
        forall|i: int|
            0 <= i < a.len() && #[trigger] a[i] < b[i] && (forall|j: int|
                i < j < a.len() ==> a[j] == b[j]) ==> seq_to_nat(a) < seq_to_nat(b),
{
    #[verifier::proof_note("Q04.H2v")] assume(false);  // HOLE: replace this line
}
// Hint(1): `implies` (where the postcondition has `==>`) puts the hypotheses in front of
//    the `by` block.
// Hint(2): the block is one call of `lemma_lt_at`.

proof fn first_difference_check(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == 2,
        b.len() == 2,
        a[1] < b[1],
{
    // Uncomment as you go:
    // lemma_first_difference(a, b);
    // assert(seq_to_nat(a) < seq_to_nat(b));
}

} // verus!
