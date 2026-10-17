//! # Q01 — the map, Verus half (closed-book exit)
//!
//! Closed book: the chapter, the exercise files, later modules' files, search tools and
//! /tutor stay closed while you work here. Only the given spine (dafny/given/,
//! verus/given/) may be open. Answer every block of this file and of
//! `dafny/Q/Q01_Hello/exit/Q01_Map.dfy` in one sitting.
//!
//! This file ships with exactly 1 hole (X3v) and 4 blocks: three code items (X1v, X3v,
//! X7v) and one verdict (X13v; answer it in `slots/Q01.slots`, then turn its
//! `// SLOT: CHECK` line into `// CHECK`). It is never `mod`-declared: `scripts/vcheck`
//! builds it standalone with the crate's dependencies, and it is in no build.
//!
//! Score: `scripts/firsttry.sh Q01 --exit`, threshold 10 of 13 over both exit files. The
//! first run on which every block holds an attempt is the score; repair every block
//! afterwards, and from then on `scripts/firsttry.sh Q01 --report --strict` covers this
//! file too. Prompt-as-heading blocks: write at most three lines of code under the
//! heading, then uncomment the shipped checks; a block passes only with its checks
//! uncommented and green.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l1::*;

verus! {

// item: Q01.X1v S1
// uses: ensures, requires
// need: fn double(x: u64) -> (r: u64)
// need: let r = double(21); assert(r == 42);
// ### X1v · S1 — Write `double`: a precondition that rules out overflow, a postcondition,
//     the body; then uncomment the check.
// Uncomment as you go:
// fn double_check() { let r = double(21); assert(r == 42); }

// item: Q01.X3v S3
// uses: assert, lemma-call
// need: pub proof fn lemma_append_one_zero(s: Seq<u64>)
// need: seq_to_nat(s + seq![0u64]) == seq_to_nat(s)
// ### X3v · S3 — One zero limb appended with `+` does not change the value. Prove it.
pub proof fn lemma_append_one_zero(s: Seq<u64>)
    ensures
        seq_to_nat(s + seq![0u64]) == seq_to_nat(s),
{
    #[verifier::proof_note("Q01.X3v")] assume(false);  // HOLE: replace this line
}

// item: Q01.X7v S7
// uses: ghost, ensures
// need: spec fn sq(x: int) -> int
// need: fn sq3() -> (r: u64)
// need: let r = sq3(); assert(r == 9);
// need: assert(sq(4) == 16);
// ### X7v · S7 — Write a spec fn `sq` (the square of an int) and an exec fn `sq3` whose
//     postcondition states its result through `sq`; then uncomment the checks.
// Uncomment as you go:
// fn sq3_check() { let r = sq3(); assert(r == 9); }
// proof fn sq_check() { assert(sq(4) == 16); }

// item: Q01.X13v S13 verdict
// ### X13v · S13 — `fn f(a: u64) -> (r: u64)` should return `a + 1` (for `a < 100`), but
//     its body is `0`. Which postcondition, alone, still lets the wrong body verify?
//     Answer form: one letter.
//     a) ensures r >= 0,
//     b) ensures r > a,
//     c) ensures r == a + 1,
//     d) ensures r >= a,
// SLOT: CHECK X13v

} // verus!
