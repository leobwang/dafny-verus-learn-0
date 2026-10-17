//! # Q07 — Internals I: proof engineering, translation, Verus half (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l4` (`use
//! qg_bignat_l4::*;` brings all four layers' names), the vstd prelude and vstd's
//! multiplication and division lemmas (`vstd::arithmetic::mul`, `vstd::arithmetic::div_mod`),
//! nothing else: no earlier exercise crate. This file is the crate root; it declares the
//! crate's port module, src/port.rs (`mod port;` below), which holds H7, H8 and H9. The
//! layers are frozen and complete; read them, never edit them.
//!
//! How to work this file:
//! 1. Predictions first: P3 and P6 (the prediction block below; their answers go in
//!    slots/Q07.slots), with every other prediction of the module (the Dafny file's
//!    prediction block); record the first tries with `scripts/firsttry.sh Q07 --check`
//!    before you run anything they are about.
//! 2. Test-out next, closed book: T1 (below) before any reading, without its hints.
//!    `scripts/firsttry.sh Q07 --check` records its first try, and refuses to while any
//!    prediction of the module is unrecorded. If both files' T1 pass on that first try, you
//!    may skip the chapter section on unfolding and fuel.
//! 3. Replace each hole here; then src/port.rs.
//! 4. Done = `scripts/vcheck --gate verus/q/q07_internals_i` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q07_internals_i` reports no finding,
//!    `scripts/vcheck --test verus/q/q07_internals_i` passes every test (H7's suite), AND
//!    `scripts/firsttry.sh Q07 --report --strict` exits 0. The crate's gate covers this file
//!    and src/port.rs together. H5 counts only with no `nonlinear_arith` in its proof, and
//!    H6 only with no `*`, `/` or `%` in its code (each block's `form:` line).
//! 5. Stuck for 20 minutes? /tutor Q07.
//!
//! This file ships with exactly 4 holes: T1 (test-out), H4, H5 and H6, each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one
//! counted diagnostic); src/port.rs ships 3. Commit every prediction BEFORE you run anything
//! it is about, open later files, or read CI, the registry or the plan: their checks and
//! headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header
//! (dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy). Exit (closed book): src/exit.rs here
//! and the Dafny exit file, scored once by `scripts/firsttry.sh Q07 --exit`; src/exit.rs
//! and src/agent.rs are never part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

mod port;

verus! {

// =========================================================================================
// The prediction block. Commit every prediction of this module before you read past this
// block (the test-out T1 included), and record the first tries:
//     scripts/firsttry.sh Q07 --check
// The verdict answers go in slots/Q07.slots. The Dafny file's prediction block holds the
// cross-language predictions (P1, P2, P5) and P4 and P7.
// =========================================================================================

// item: Q07.P3v S1 verdict
// **P3.** Choosing a prover for a machine-word fact. Four crates of their own, each checked
// with `scripts/vcheck`. Each holds `use vstd::prelude::*;` and, inside `verus! { }`, this
// one proof fn:
/*
    proof fn split(p: u128)
        ensures
            (p >> 64u128) == p / 0x1_0000_0000_0000_0000u128,
    {
        <body>
    }

  where <body> is
    [a] assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (nonlinear_arith);
    [b] assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (bit_vector);
    [c] assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (compute);
    [d] nothing: the body is empty
*/
// Which of the four crates verify?
// Answer form: the labels that verify, in label order, separated by single spaces, or
// `none`.
// SLOT: CHECK P3v

// item: Q07.P6v S2 verdict
// **P6.** A spec fn that recommends. In a crate of its own, with `use vstd::prelude::*;`:
/*
    pub open spec fn top(s: Seq<u64>) -> u64
        recommends
            s.len() > 0,
    {
        s[s.len() - 1]
    }

    proof fn r1(s: Seq<u64>)
        ensures
            top(s) == s[s.len() - 1],
    {
    }
*/
// `r1` has no `requires`. What does `scripts/vcheck` say about the crate?
// Answer form: `V:<v>`, v one of `ok` (verifies), `fail` (a verification error), `timeout`
// (out of resource or time), `err:<stage>` (refused before verification; the stage as
// `scripts/vcheck` prints it: `parse` or `resolve`).
// SLOT: CHECK P6v

// =========================================================================================
// Test-out (closed book: after every prediction of this module is recorded, before any
// reading; `scripts/firsttry.sh Q07 --check` refuses T1's first try until then)
// =========================================================================================

// item: Q07.T1v S4
// uses: fuel
// pair: Q07.T1d
/// **T1.** (test-out) The value of a three-limb literal: `seq_to_nat` peels one limb at a
/// time, least significant first. What must the solver know about the literal's tails
/// before the three limbs add up?
pub proof fn lemma_three_limbs(a: u64, b: u64, c: u64)
    ensures
        seq_to_nat(seq![a, b, c]) == a + BASE * (b + BASE * c),
{
    #[verifier::proof_note("Q07.T1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): Verus unfolds a recursive spec fn once by default, and this literal needs one
//    unfolding per limb.
// Hint(2): state each `drop_first` yourself (`=~=`) with the values of the shorter
//    sequences, or raise `seq_to_nat`'s fuel for this proof alone.

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q07.W1v S1
/// **W1.** Bit-vector reasoning. `assert(…) by (bit_vector)` hands one assertion to the
/// solver's bit-vector theory, where `&`, `>>` and `%` by a power of two are facts about
/// the same bits. Every term must be a fixed-width integer (a `u8` … `u128`, a cast of one,
/// or a constant): `lemma_mask_is_rem` states a mask as a remainder on a `u32`. Where it
/// stops: a `nat` or `int` variable is no fixed-width integer, so an assertion about one
/// is refused before anything is verified; such a fact is stated about a word, and the
/// solver then uses it as an ordinary integer fact.
pub proof fn lemma_mask_is_rem(x: u32)
    ensures
        x & 0xFFFF == x % 0x10000,
{
    assert(x & 0xFFFF == x % 0x10000) by (bit_vector);  // did: the mask as a remainder
}

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q07/)
// =========================================================================================

// item: Q07.C1v S4 write:fuel
// C1 — card: unfolding and fuel (`reveal_with_fuel`).
// Jurisdiction: Verus unfolds a recursive spec fn once by default. A proof unfolds it by
// hand (name a `drop_first` as a sequence with `=~=`, and state the values of the shorter
// sequences: each assertion about `seq_to_nat` of a new term unfolds it once more) or
// raises its fuel for one proof with `reveal_with_fuel(f, k)`.
// Success: `lemma_two_limbs_by_hand` and `lemma_two_limbs_by_fuel`. Failure:
// specimens/Q07/card-c1v.rs.specimen (the same statement, an empty body).
pub proof fn lemma_two_limbs_by_hand(a: u64, b: u64)
    ensures
        seq_to_nat(seq![a, b]) == a + BASE * b,
{
    assert(seq![a, b].drop_first() =~= seq![b]);
    assert(seq_to_nat(seq![b].drop_first()) == 0);
    assert(seq_to_nat(seq![b]) == b);
}

pub proof fn lemma_two_limbs_by_fuel(a: u64, b: u64)
    ensures
        seq_to_nat(seq![a, b]) == a + BASE * b,
{
    reveal_with_fuel(seq_to_nat, 3);  // did: three unfoldings of seq_to_nat
}

// item: Q07.C2v S5 write:arithmetic-library
// C2 — card: the arithmetic library (`vstd::arithmetic::mul`, `vstd::arithmetic::div_mod`).
// Jurisdiction: Verus leaves a product of two variables to the solver's linear arithmetic
// unless a proof names a library lemma (or asks for `nonlinear_arith`). Call the proof fn
// with arguments that meet its `requires`; the library states its lemmas over `int`, so
// `nat` and word arguments are cast. Success: `lemma_limb_product_at_most`, one call of
// `lemma_mul_upper_bound`. Failure: specimens/Q07/card-c2v.rs.specimen (no call).
pub proof fn lemma_limb_product_at_most(x: u64, y: u64)
    ensures
        (x as nat) * (y as nat) <= (BASE - 1) * (BASE - 1),
{
    lemma_mul_upper_bound(x as int, (BASE - 1) as int, y as int, (BASE - 1) as int);
}

// item: Q07.C3v S1 write:bit-vector
// C3 — card: machine words by `bit_vector`, and the bridge to `nat`.
// Jurisdiction: a fact about the bits of a word (a mask, a shift) is a `by (bit_vector)`
// assertion about the word; once it holds, the solver uses it about the word's value, so a
// cast carries it over to `nat`. Success: `lemma_low_byte_value`. Failure:
// specimens/Q07/card-c3v.rs.specimen (the same assertion handed to another prover).
pub proof fn lemma_low_byte_value(x: u64)
    ensures
        (x & 0xFF) as nat == x as nat % 256,
{
    assert(x & 0xFF == x % 256) by (bit_vector);  // did: the low byte as a remainder
}

// =========================================================================================
// RECOGNISE card
// =========================================================================================

// item: Q07.C6v S2 recognise:recommends
// C6 — card: `recommends` (recognise).
// `recommends` on a spec fn states the domain it is meant for, without restricting it: a
// spec fn is total, and outside that domain its value is unspecified. Verus checks a
// recommendation in a few places only (a `spec(checked)` fn's body, and as a note beside a
// failed proof), never as a proof obligation of a caller. You will read it in vstd and in
// other code. Demo: specimens/Q07/card-c6v.rs.specimen (run it with `scripts/vcheck
// --json`: the notes are in its `diagnostics`).

// =========================================================================================
// Holes
// =========================================================================================

// item: Q07.H4v S4
// uses: fuel
/// **H4.** Two limbs, then a tail: the value of `seq![a, b] + s` is `a`, plus `BASE` times
/// `b`, plus `BASE * BASE` times the value of `s`. What are the tails of `seq![a, b] + s`,
/// and how often must `seq_to_nat` unfold?
pub proof fn lemma_two_limbs_then(a: u64, b: u64, s: Seq<u64>)
    ensures
        seq_to_nat(seq![a, b] + s) == a + BASE * (b + BASE * seq_to_nat(s)),
{
    #[verifier::proof_note("Q07.H4v")] assume(false);  // HOLE: replace this line
}
// Hint(1): name each tail with `=~=`: the solver does not know `drop_first` of a
//    concatenation until it is told.
// Hint(2): `seq_to_nat` must unfold at every sequence on the way down; C1 shows how to
//    raise its fuel.

// item: Q07.H5v S5
// uses: arithmetic-library
// form: no-nl
/// **H5.** One more limb dropped is one more division by `BASE`: `v / weight(n + 1)` is
/// `(v / weight(n)) / BASE`. `weight` (layer L3) is opaque. Prove it with vstd's arithmetic
/// lemmas and the layers' weight lemmas, with no `nonlinear_arith` (the form). Which
/// product is `weight(n + 1)`, and what does a division by a product equal?
pub proof fn lemma_div_weight_succ(v: nat, n: nat)
    ensures
        v / weight(n + 1) == (v / weight(n)) / BASE,
{
    #[verifier::proof_note("Q07.H5v")] assume(false);  // HOLE: replace this line
}
// Hint(1): L3 gives `weight`'s two defining equations and its monotonicity; a divisor must
//    be positive before vstd will divide by it.
// Hint(2): `vstd::arithmetic::div_mod` (imported) divides by a product in two steps; match
//    the order of the product in its `ensures` to the one in L3's equation.

// item: Q07.H6v S1
// uses: bit-vector
// form: bv-exec
/// **H6.** Split a double word into its high and its low limb, by a shift and a mask, with
/// no `*`, `/` or `%` in the code (the form). Which facts relate the shift and the mask to
/// the value the postcondition speaks of?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn split_word(p: u128) -> (r: (u64, u64))
    ensures
        r.0 as nat * BASE + r.1 as nat == p as nat,
{
    unimplemented!()
}
// Hint(1): `>>` and `&` are bit operations: say what each equals in a `by (bit_vector)`
//    assertion inside `proof { }` (W1, C3).
// Hint(2): a division may appear in the proof, never in the code.

// =========================================================================================
// The port (src/port.rs: H7, H8, H9) comes after every hole above. The module's divergence
// card, C7, is in the final section of the Dafny file.
// =========================================================================================

} // verus!
