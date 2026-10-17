//! # Q07 — Internals I: proof engineering, translation, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q07_internals_i/src/lib.rs` (author-only; never
//! learner-visible). Same crate layout (`mod port;`), imports, names, statements, item
//! markers and order as the exercise file. Every hole is filled and every verdict switch is
//! enabled; the verdict answers are in `Solutions/slots/Q07.slots`, their hashes in
//! `expected/Q07.pins`.
//!
//! The crate is silent: `scripts/vcheck --ref` on it prints only the summary line. Every
//! output the module quotes is pinned: the count pins in `expected/Q07.counts`, the
//! statement freeze in `expected/Q07.freeze`, the WRITE-card failure demos by their in-file
//! `// EXPECT` lines, and the RECOGNISE and divergence demos by their sealed sidecars under
//! `expected/specimens/Q07/`.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

mod port;

verus! {

// =========================================================================================
// The prediction block.
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
// CHECK P3v

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
// CHECK P6v

// =========================================================================================
// Test-out (closed book)
// =========================================================================================

// item: Q07.T1v S4
// uses: fuel
// pair: Q07.T1d
/// **T1.** (test-out) The value of a three-limb literal.
///
/// Reference: `seq_to_nat` unfolds once by default; the literal needs one unfolding per
/// limb and one for the empty tail. `reveal_with_fuel(seq_to_nat, 4)` gives the four inside
/// this proof alone, and the solver evaluates `drop_first` of each literal on the way.
pub proof fn lemma_three_limbs(a: u64, b: u64, c: u64)
    ensures
        seq_to_nat(seq![a, b, c]) == a + BASE * (b + BASE * c),
{
    reveal_with_fuel(seq_to_nat, 4);  // did: four unfoldings of seq_to_nat
}

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
/// **H4.** Two limbs, then a tail.
///
/// Reference: the tail of `seq![a, b] + s` is `seq![b] + s`, and its tail is `s`; Verus
/// knows neither until told (`=~=`), and `seq_to_nat` must unfold at both sequences and at
/// the statement's own, so the fuel is three.
pub proof fn lemma_two_limbs_then(a: u64, b: u64, s: Seq<u64>)
    ensures
        seq_to_nat(seq![a, b] + s) == a + BASE * (b + BASE * seq_to_nat(s)),
{
    reveal_with_fuel(seq_to_nat, 3);  // did: three unfoldings of seq_to_nat
    assert((seq![a, b] + s).drop_first() =~= seq![b] + s);
    assert((seq![b] + s).drop_first() =~= s);
}

// item: Q07.H5v S5
// uses: arithmetic-library
// form: no-nl
// cfree: { lemma_weight_succ(n); lemma_weight_zero(); lemma_weight_mono(0, n); assert(v / (BASE * weight(n)) == (v / weight(n)) / BASE) by (nonlinear_arith) requires weight(n) > 0; }
/// **H5.** One more limb dropped is one more division by `BASE`.
///
/// Reference: `weight(n + 1) == BASE * weight(n)` (L3's second equation) and
/// `weight(n) >= weight(0) == 1` (monotonicity and the first equation) set up vstd's
/// `lemma_div_denominator(v, weight(n), BASE)`, which divides by a product in two steps;
/// the commutativity call matches its product to the one in L3's equation.
pub proof fn lemma_div_weight_succ(v: nat, n: nat)
    ensures
        v / weight(n + 1) == (v / weight(n)) / BASE,
{
    lemma_weight_succ(n);
    lemma_weight_zero();
    lemma_weight_mono(0, n);
    lemma_mul_is_commutative(BASE as int, weight(n) as int);
    lemma_div_denominator(v as int, weight(n) as int, BASE as int);
}

// item: Q07.H6v S1
// uses: bit-vector
// form: bv-exec
// triv: { (0u64, 0u64) }
// cfree: { ((p / 0x1_0000_0000_0000_0000u128) as u64, (p % 0x1_0000_0000_0000_0000u128) as u64) }
// cfree: { ((p >> 64u128) as u64, p as u64) }
/// **H6.** Split a double word.
///
/// Reference: the code is a shift and a mask; the proof says, by `bit_vector`, that the
/// shift is the division by 2^64 and the mask the remainder, and the solver's integer
/// arithmetic closes the postcondition from those two facts (the divisions live only in the
/// proof). A truncating cast with no `bit_vector` fact does not verify, and the code may
/// not divide (the form).
pub fn split_word(p: u128) -> (r: (u64, u64))
    ensures
        r.0 as nat * BASE + r.1 as nat == p as nat,
{
    proof {
        assert((p >> 64u128) == p / 0x1_0000_0000_0000_0000u128) by (bit_vector);  // did: the shift as a division
        assert((p & 0xFFFF_FFFF_FFFF_FFFFu128) == p % 0x1_0000_0000_0000_0000u128) by (bit_vector);  // did: the mask as a remainder
    }
    let hi = (p >> 64u128) as u64;
    let lo = (p & 0xFFFF_FFFF_FFFF_FFFFu128) as u64;
    (hi, lo)
}

// =========================================================================================
// The port (src/port.rs: H7, H8, H9) comes after every hole above. The module's divergence
// card, C7, is in the final section of the Dafny file.
// =========================================================================================

} // verus!
