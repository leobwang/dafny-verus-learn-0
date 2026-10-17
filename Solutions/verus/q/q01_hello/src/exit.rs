//! # Q01 — the map, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q01_hello/src/exit.rs`: every code block filled,
//! every check live. Verdict answers are in `Solutions/slots/Q01.slots`. Never
//! `mod`-declared; `scripts/vcheck --ref` builds it standalone with the crate's
//! dependencies and prints only its summary line.
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
// Any precondition that keeps 2 * x in u64 and admits 21 passes the check.
// reference-only: the learner writes this fn
pub fn double(x: u64) -> (r: u64)
    requires
        x <= 1000,
    ensures
        r == 2 * x,
{
    x * 2
}
// reference-only: the shipped check, uncommented
fn double_check() { let r = double(21); assert(r == 42); }

// item: Q01.X3v S3
// uses: assert, lemma-call
// need: pub proof fn lemma_append_one_zero(s: Seq<u64>)
// need: seq_to_nat(s + seq![0u64]) == seq_to_nat(s)
// ### X3v · S3 — Prove it.
/// Why this proof: `s + seq![0u64]` is extensionally `s.push(0)` (the `=~=` assert), and
/// the L1 worked proof fn is stated with `push`.
pub proof fn lemma_append_one_zero(s: Seq<u64>)
    ensures
        seq_to_nat(s + seq![0u64]) == seq_to_nat(s),
{
    assert(s + seq![0u64] =~= s.push(0));
    lemma_seq_to_nat_push_zero(s);
}

// item: Q01.X7v S7
// uses: ghost, ensures
// need: spec fn sq(x: int) -> int
// need: fn sq3() -> (r: u64)
// need: let r = sq3(); assert(r == 9);
// need: assert(sq(4) == 16);
// ### X7v · S7 — Write a spec fn `sq` (the square of an int) and an exec fn `sq3` whose
//     postcondition states its result through `sq`; then uncomment the checks.
// reference-only: the learner writes this spec fn
pub open spec fn sq(x: int) -> int {
    x * x
}
// reference-only: the learner writes this exec fn
pub fn sq3() -> (r: u64)
    ensures
        r == sq(3),
{
    9
}
// reference-only: the shipped checks, uncommented
fn sq3_check() { let r = sq3(); assert(r == 9); }
// reference-only: the shipped checks, uncommented
proof fn sq_check() { assert(sq(4) == 16); }

// item: Q01.X13v S13 verdict
// ### X13v · S13 — `fn f(a: u64) -> (r: u64)` should return `a + 1` (for `a < 100`), but
//     its body is `0`. Which postcondition, alone, still lets the wrong body verify?
//     Answer form: one letter.
//     a) ensures r >= 0,
//     b) ensures r > a,
//     c) ensures r == a + 1,
//     d) ensures r >= a,
// CHECK X13v

} // verus!
