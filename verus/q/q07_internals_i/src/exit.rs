//! # Q07 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) and the pinned vstd source may
//! be open: X2 asks for library lemmas by name.
//!
//! This file ships with exactly 2 holes (X1, X2); the Dafny half
//! (dafny/Q/Q07_InternalsI/exit/Q07_Exit.dfy) ships with 2 holes. Score both halves in one
//! sitting with
//!
//!     scripts/firsttry.sh Q07 --exit
//!
//! Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language. The first
//! full run (every block attempted) is the score; repair every block afterwards, after
//! which the strict gate covers this file too. X1 counts only with no `*`, `/` or `%` in
//! its code, and X2 only with no `nonlinear_arith` (each block's `form:` line). Then fill
//! the EXPLAIN-BACK block at the end of the Dafny exit file, on one of these two items.
//! This file is never `mod`-declared and is in no build: work it with `scripts/vcheck
//! verus/q/q07_internals_i/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// item: Q07.X1v S1
// uses: bit-vector
// need: pub fn join_word(hi: u64, lo: u64) -> (r: u128)
// need: r as nat == hi as nat * BASE + lo as nat
// form: bv-exec
/// **X1.** Join two words into a double word: the high word shifted by 64 bits, and the
/// low word. Implement it with a shift and an `or`, with no `*`, `/` or `%` in the code
/// (the form).
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn join_word(hi: u64, lo: u64) -> (r: u128)
    ensures
        r as nat == hi as nat * BASE + lo as nat,
{
    unimplemented!()
}

// item: Q07.X2v S5
// uses: arithmetic-library
// need: pub proof fn lemma_weight_quotient(k: nat, n: nat)
// need: k <= n
// need: weight(n) / weight(k) == weight((n - k) as nat)
// form: no-nl
/// **X2.** A quotient of weights is a weight. Prove it with `vstd::arithmetic` lemmas and
/// the layers' weight lemmas (L3 and L4), with no `nonlinear_arith` (the form).
pub proof fn lemma_weight_quotient(k: nat, n: nat)
    requires
        k <= n,
    ensures
        weight(n) / weight(k) == weight((n - k) as nat),
{
    #[verifier::proof_note("Q07.X2v")] assume(false);  // HOLE: replace this line
}

} // verus!
