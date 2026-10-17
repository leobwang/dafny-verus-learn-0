//! # Q02 — First syntax I (Exercises)
//!
//! Imports: the given layer crates qg_bignat_l1 and qg_bignat_l2 (verus/given/), which
//! this crate's Cargo.toml lists; `use qg_bignat_l2::*;` brings both layers' names. No
//! earlier exercise crate is imported.
//!
//! How to work this file:
//! 1. Test-out first, closed book, before you read the chapter: T1v below (and T1d in
//!    dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy). Write each, then record its
//!    first try with `scripts/firsttry.sh Q02 --check` BEFORE you uncomment its check.
//! 2. Predictions next: Q02's prediction block is in the Dafny file, its Verus specimens
//!    are specimens/Q02/P2v.rs.specimen and P6v.rs.specimen. Record every prediction with
//!    `scripts/firsttry.sh Q02 --check` before you run anything it is about.
//! 3. Then read the chapter (docs/Q02_FirstSyntaxI.md), the worked example W1v and the
//!    cards. A card's failure demo is a specimen: open it only after step 2.
//! 4. Replace each hole; its statement is its check. The test-out block T1v ships a
//!    commented check: uncomment it once its first try is recorded (step 1). Read Hint(1)
//!    only when stuck, Hint(2) only when still stuck.
//! 5. Done = `scripts/vcheck --gate verus/q/q02_first_syntax_i` prints only the summary
//!    line and exits 0, `scripts/vaudit verus/q/q02_first_syntax_i` reports no finding,
//!    AND `scripts/firsttry.sh Q02 --report --strict` exits 0.
//! 6. Stuck for 20 minutes? /tutor Q02.
//!
//! This file ships with exactly 6 holes: H1v, H2v, H5v, H6v, H7v and H8v (the tool counts
//! them: `scripts/vcheck verus/q/q02_first_syntax_i` lists one per item). Module Q02 ships
//! 12 holes (6 here, 6 in the Dafny file), 2 test-out items, 10 predictions and 6 exit
//! items (the exit files: src/exit.rs here, never built with this crate).
//! Commit every prediction BEFORE you run anything it is about, open later files, or read
//! CI, the registry or the plan: their checks and headers give some predictions away.
//!
//! Item kinds: T test-out · P prediction · W worked example · C card (write, recognise,
//! diverge) · H hole · X exit item · A agent run. A hole is
//! `#[verifier::proof_note("<item>")] assume(false);` in a proof fn, or an
//! `#[verifier::external_body]` line over an `unimplemented!()` body in an exec fn.
//!
//! The agentic exercise (implementer vs checks, src/agent.rs, never built with this crate)
//! is described at the bottom of the Dafny file.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// =============================================================================
// Test-out (closed book, before the chapter)
// =============================================================================

// item: Q02.T1v S4
// uses: decreases
// pair: Q02.T1d
// ### T1v · S4 — Write `pub open spec fn pad_zeros(s: Seq<u64>, k: nat) -> Seq<u64>`, which
//    pushes zero limbs onto `s` until its length is at least `k`, by recursion. Closed book:
//    no chapter, no hints, no tutor. Then run `scripts/firsttry.sh Q02 --check`: it records
//    your first try (it runs the check below in a scratch copy). Only then uncomment the
//    check.

// Uncomment as you go:
// proof fn pad_zeros_check() {
//     // did: evaluates pad_zeros on the literal
//     assert(pad_zeros(seq![7u64], 3) =~= seq![7u64, 0u64, 0u64]) by (compute_only);
// }

// Q02's verdict predictions are in the Dafny file's prediction block
// (dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy); the Verus obligation specimens are
// specimens/Q02/P2v.rs.specimen and P6v.rs.specimen.

// =============================================================================
// Worked example
// =============================================================================

// item: Q02.W1v S4
/// **W1v (worked).** The index of the first zero limb of `v`, or `v.len()` when there is
/// none. A loop with its invariant and its `decreases`; the `assert`s after the loop state
/// what the verifier knows there: the invariant, and the guard false.
pub fn first_zero(v: &Vec<u64>) -> (i: usize)
    ensures
        i <= v.len(),
        forall|j: int| 0 <= j < i ==> v@[j] != 0,
        i < v.len() ==> v@[i as int] == 0,
{
    let mut i: usize = 0;
    while i < v.len() && v[i] != 0
        invariant
            i <= v.len(),
            forall|j: int| 0 <= j < i ==> v@[j] != 0,
        decreases v.len() - i,
    {
        i = i + 1;
    }
    // At loop exit: the invariant holds, and the guard is false.
    assert(i <= v.len() && forall|j: int| 0 <= j < i ==> v@[j] != 0);
    assert(!(i < v.len() && v@[i as int] != 0));
    i
}

// =============================================================================
// WRITE cards. Each failure demo is a specimen under specimens/Q02/: open it only after
// your predictions are committed.
// =============================================================================

// item: Q02.C1v S3 write:assert-by
// ### C1v — card: `assert … by`
//    Jurisdiction: a fact that needs its own proof steps (here one proof-fn call), written
//    next to the fact it proves. Success: card_assert_by below. Failure:
//    specimens/Q02/card-c1v.rs.specimen.
pub proof fn card_assert_by(a: BigNat)
    ensures
        seq_to_nat(a@.push(0)) == a.to_nat(),
{
    assert(seq_to_nat(a@.push(0)) == seq_to_nat(a@)) by {
        lemma_seq_to_nat_push_zero(a@);
    }
}

// item: Q02.C2v S4 write:invariant
// ### C2v — card: loop invariants
//    Jurisdiction: what a loop keeps true from one pass to the next, written in an
//    `invariant` clause between the guard and the body; it must hold before the first pass
//    and after every pass. Success: card_invariant below. Failure:
//    specimens/Q02/card-c2v.rs.specimen.
pub fn card_invariant(v: &Vec<u64>) -> (n: usize)
    ensures
        n == v.len(),
{
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
        decreases v.len() - i,
    {
        i = i + 1;
    }
    i
}

// item: Q02.C3v S4 write:decreases
// ### C3v — card: termination measures (`decreases`)
//    Jurisdiction: why a recursion or a loop stops: a measure that every recursive call (or
//    every pass) makes smaller and that cannot fall below zero. Success: card_evens below
//    (the limbs at even positions). Failure: specimens/Q02/card-c3v.rs.specimen.
pub open spec fn card_evens(s: Seq<u64>) -> Seq<u64>
    decreases s.len(),
{
    if s.len() < 2 {
        s
    } else {
        seq![s[0]] + card_evens(s.subrange(2, s.len() as int))
    }
}

// item: Q02.C4v S2 write:quantified-ensures
// ### C4v — card: a `forall` postcondition
//    Jurisdiction: a property of every element of a result, stated once for all indices.
//    Success: card_indices below (the vector 0, 1, …, n - 1). Failure:
//    specimens/Q02/card-c4v.rs.specimen.
pub fn card_indices(n: u64) -> (v: Vec<u64>)
    ensures
        v@.len() == n,
        forall|i: int| 0 <= i < n ==> v@[i] as int == i,
{
    let mut v: Vec<u64> = Vec::new();
    let mut k: u64 = 0;
    while k < n
        invariant
            k <= n,
            v@.len() == k,
            forall|i: int| 0 <= i < k ==> v@[i] as int == i,
        decreases n - k,
    {
        v.push(k);
        k = k + 1;
    }
    v
}

// Card Q02.C8dv (recognise:old), the Verus column (the card is in the Dafny file): the value
// of a `&mut` parameter at the call is `old(v)`, at the return `final(v)`.
pub fn card_old(v: &mut Vec<u64>)
    ensures
        final(v)@ == old(v)@.push(7u64),
{
    v.push(7);
}

// Card Q02.C9dv (recognise:exists), the Verus column (the card is in the Dafny file): the
// witness is a term the verifier sees, here an index named and asserted.
pub proof fn card_exists(s: Seq<u64>)
    requires
        s.len() > 0,
        s.last() != 0,
    ensures
        exists|i: int| 0 <= i < s.len() && s[i] != 0,
{
    let w = s.len() - 1;
    assert(0 <= w < s.len() && s[w] != 0);
}

// =============================================================================
// Holes
// =============================================================================

// item: Q02.H1v S3
// uses: assert-by, lemma-call
// pair: Q02.H1d
/// **H1v.** Dropping a most significant zero limb keeps the value.
/// Method clause: the proof uses one `assert … by`. Which given proof fn talks about a zero
/// limb pushed on top, and how is `s` such a sequence?
pub proof fn lemma_seq_to_nat_drop_last_zero(s: Seq<u64>)
    requires
        s.len() > 0,
        s.last() == 0,
    ensures
        seq_to_nat(s.drop_last()) == seq_to_nat(s),
{
    #[verifier::proof_note("Q02.H1v")] assume(false);  // HOLE: replace this line
    // Hint(1): `s` is `s.drop_last()` with one limb pushed.
    // Hint(2): the solver compares two sequences element by element only when asked to:
    //    which `=~=` does it need?
}

// item: Q02.H2v S4
// uses: invariant
// pair: Q02.H2d
/// **H2v.** Strip the most significant zero limbs in place, keeping the value.
/// The loop, its `decreases` and the proof call in its body are given (the call is H1v's
/// statement). Write the loop invariant. What must every pass keep about `a`'s value?
pub fn normalize(a: &mut BigNat)
    ensures
        final(a).wf(),
        final(a).to_nat() == old(a).to_nat(),
{
    #[verifier::proof_note("Q02.H2v")] assume(false);  // HOLE: delete this line, then write the loop invariant
    while a.limbs.len() > 0 && a.limbs[a.limbs.len() - 1] == 0
        decreases a.limbs.len(),
    {
        proof {
            lemma_seq_to_nat_drop_last_zero(a@);
        }
        a.limbs.pop();
    }
    // Hint(1): an `invariant` clause goes between the guard and `decreases`.
    // Hint(2): inside a loop body Verus knows only the invariant and the guard. What must
    //    it know about `a`'s value for the postcondition to follow at exit?
}

// item: Q02.H5v S2
// uses: quantified-ensures, invariant, decreases
// pair: Q02.H5d
/// **H5v.** `n` zero limbs.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn zeros(n: usize) -> (v: Vec<u64>)
    ensures
        v@.len() == n,
        forall|i: int| 0 <= i < n ==> v@[i] == 0,
{
    unimplemented!()
    // Hint(1): start from `Vec::new()` and push one limb per pass of a `while` loop.
    // Hint(2): keep a counter; the invariant ties the vector's length to it and states
    //    the postcondition for the part built so far.
}

// item: Q02.H6v S6
// uses: quantified-ensures, invariant, decreases
// pair: Q02.H6d
/// **H6v.** Clear every limb of `v` from position `k` on, in place.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn clear_from(v: &mut Vec<u64>, k: usize)
    ensures
        final(v)@.len() == old(v)@.len(),
        forall|i: int|
            0 <= i < old(v)@.len() ==> final(v)@[i] == (if i < k {
                old(v)@[i]
            } else {
                0u64
            }),
{
    unimplemented!()
    // Hint(1): `v.set(j, 0)` writes one limb; start `j` at `k`.
    // Hint(2): the invariant describes the whole vector at every pass, and its length.
}

// item: Q02.H7v S4
// uses: lemma-call, assert
/// **H7v.** A non-empty canonical limb sequence has a positive value. Which limb is
/// non-zero, and how does the value of `s` depend on the value of `s.drop_first()`?
pub proof fn lemma_wf_value_pos(s: Seq<u64>)
    requires
        seq_wf(s),
        s.len() > 0,
    ensures
        seq_to_nat(s) > 0,
    decreases s.len(),
{
    #[verifier::proof_note("Q02.H7v")] assume(false);  // HOLE: replace this line
    // Hint(1): split on `s.len() > 1`.
    // Hint(2): with more than one limb, is `s.drop_first()` canonical, and what would the
    //    verifier need to be told to see it?
}

// item: Q02.H8v S5
// uses: lemma-call, assert
/// **H8v.** Any number of zero limbs on top keeps the value. Find the given fact you need
/// in L1–L2 (verus/given/) and reuse it.
pub proof fn lemma_push_zeros(s: Seq<u64>, k: nat)
    ensures
        seq_to_nat(s + Seq::new(k, |i: int| 0u64)) == seq_to_nat(s),
    decreases k,
{
    #[verifier::proof_note("Q02.H8v")] assume(false);  // HOLE: replace this line
    // Hint(1): recursion on `k`; `k` zeros are `k - 1` zeros with one more pushed.
    // Hint(2): state that sequence equality with `=~=`, then use the given proof fn about
    //    one pushed zero.
}

// =============================================================================
// Final section: divergence card. Record every Q02 prediction before you read on.
// =============================================================================

// item: Q02.C6v S6 diverge:q02-c6
// ### C6v — divergence card: writing through a parameter, Dafny frames vs Verus references
//    The same intent, a write the signature does not permit, in each language. Demos:
//    specimens/Q02/card-c6v-d.dfy.specimen and specimens/Q02/card-c6v-v.rs.specimen; run
//    each with `scripts/vcheck` and compare. The chapter explains the difference.

} // verus!
