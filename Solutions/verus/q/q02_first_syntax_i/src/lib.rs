//! # Q02 — First syntax I (Reference Solution)
//!
//! Hole-free reference for `verus/q/q02_first_syntax_i/src/lib.rs` (author-only; never
//! learner-visible). Same items in the same order, same statements; the hole bodies are
//! complete and the test-out block and its check are written out.
//!
//! Every output the course quotes about this crate is pinned: the unit's count pin
//! (expected/Q02.counts) and the card demo pins (in-file EXPECT lines and the
//! expected/specimens/Q02/ sidecars). The crate is silent: `scripts/vcheck --ref` on it
//! prints only its summary line.
//!
//! Imports: the given layer crates qg_bignat_l1 and qg_bignat_l2 (re-supply: no exercise
//! crate is imported). Q02's verdict items live in the Dafny file's prediction block.
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
// (Reference) The measure `k - s.len()` shrinks by one per call; the guard stops the
// recursion before it goes below zero. Verus needs the measure stated.
// reference-only: the learner writes this spec fn (a prompt-as-heading block)
pub open spec fn pad_zeros(s: Seq<u64>, k: nat) -> Seq<u64>
    decreases k - s.len(),
{
    if s.len() >= k {
        s
    } else {
        pad_zeros(s.push(0u64), k)
    }
}

// reference-only: the learner uncomments this check
proof fn pad_zeros_check() {
    // did: evaluates pad_zeros on the literal
    assert(pad_zeros(seq![7u64], 3) =~= seq![7u64, 0u64, 0u64]) by (compute_only);
}

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
/// (Reference) `s` is `s.drop_last()` with one zero pushed. L1's worked proof fn gives the
/// value of that push, proved inside one `assert … by`; the extensional equality
/// `s.drop_last().push(0) =~= s` then lets the verifier rewrite that fact into the goal.
/// Without `=~=` the solver never connects the two sequences.
pub proof fn lemma_seq_to_nat_drop_last_zero(s: Seq<u64>)
    requires
        s.len() > 0,
        s.last() == 0,
    ensures
        seq_to_nat(s.drop_last()) == seq_to_nat(s),
{
    assert(seq_to_nat(s.drop_last().push(0)) == seq_to_nat(s.drop_last())) by {
        lemma_seq_to_nat_push_zero(s.drop_last());
    }
    assert(s.drop_last().push(0) =~= s);
}

// item: Q02.H2v S4
// uses: invariant
// pair: Q02.H2d
/// **H2v.** Strip the most significant zero limbs in place, keeping the value.
/// (Reference) One invariant clause: the value is the value at the call. The proof call in
/// the body (H1v) keeps it across each `pop`, and at exit the guard is false, which is
/// `wf()`. Verus checks the loop body from the invariant alone, so without that clause
/// nothing ties `a` inside the loop to `old(a)`.
pub fn normalize(a: &mut BigNat)
    ensures
        final(a).wf(),
        final(a).to_nat() == old(a).to_nat(),
{
    while a.limbs.len() > 0 && a.limbs[a.limbs.len() - 1] == 0
        invariant
            // @hole-begin Q02.H2v
            a.to_nat() == old(a).to_nat(),
            // @hole-end Q02.H2v
        decreases a.limbs.len(),
    {
        proof {
            lemma_seq_to_nat_drop_last_zero(a@);
        }
        a.limbs.pop();
    }
}

// item: Q02.H5v S2
// uses: quantified-ensures, invariant, decreases
// pair: Q02.H5d
/// **H5v.** `n` zero limbs.
/// (Reference) A counter `k` with the vector's length tied to it; the invariant carries
/// both halves of the postcondition for the part built so far, and `n - k` shrinks.
// The empty-body gate's trivial body in TRIV mode (firsttry --empty-body; it must fail):
// triv: { Vec::new() }
pub fn zeros(n: usize) -> (v: Vec<u64>)
    ensures
        v@.len() == n,
        forall|i: int| 0 <= i < n ==> v@[i] == 0,
{
    let mut v: Vec<u64> = Vec::new();
    let mut k: usize = 0;
    while k < n
        invariant
            k <= n,
            v@.len() == k,
            forall|i: int| 0 <= i < k ==> v@[i] == 0,
        decreases n - k,
    {
        v.push(0);
        k = k + 1;
    }
    v
}

// item: Q02.H6v S6
// uses: quantified-ensures, invariant, decreases
// pair: Q02.H6d
/// **H6v.** Clear every limb of `v` from position `k` on, in place.
/// (Reference) The invariant describes the whole vector at every pass (old values below
/// `k` and from `j` on, zeros in between) and keeps its length, which `set` preserves.
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
    let mut j = k;
    while j < v.len()
        invariant
            k <= j,
            v@.len() == old(v)@.len(),
            forall|i: int|
                0 <= i < v@.len() ==> v@[i] == (if i < k || i >= j {
                    old(v)@[i]
                } else {
                    0u64
                }),
        decreases v@.len() - j,
    {
        v.set(j, 0);
        j = j + 1;
    }
}

// item: Q02.H7v S4
// uses: lemma-call, assert
/// **H7v.** A non-empty canonical limb sequence has a positive value.
/// (Reference) By recursion on the length. One limb: that limb is the top one, so it is not
/// zero. More limbs: the tail is canonical too (its last limb is `s`'s), so its value is
/// positive by the recursive call, and `BASE` times it already is.
pub proof fn lemma_wf_value_pos(s: Seq<u64>)
    requires
        seq_wf(s),
        s.len() > 0,
    ensures
        seq_to_nat(s) > 0,
    decreases s.len(),
{
    if s.len() > 1 {
        assert(s.drop_first().last() == s.last());
        lemma_wf_value_pos(s.drop_first());
    } else {
        assert(seq_to_nat(s.drop_first()) == 0);
    }
}

// item: Q02.H8v S5
// uses: lemma-call, assert
/// **H8v.** Any number of zero limbs on top keeps the value.
/// (Reference) The given fact to reuse is L1's worked proof fn (one zero pushed). By
/// recursion on `k`: `k` zeros are `k - 1` zeros with one more pushed, which `=~=` states.
pub proof fn lemma_push_zeros(s: Seq<u64>, k: nat)
    ensures
        seq_to_nat(s + Seq::new(k, |i: int| 0u64)) == seq_to_nat(s),
    decreases k,
{
    if k == 0 {
        assert(s + Seq::new(k, |i: int| 0u64) =~= s);
    } else {
        let z = Seq::new((k - 1) as nat, |i: int| 0u64);
        lemma_push_zeros(s, (k - 1) as nat);
        assert(s + Seq::new(k, |i: int| 0u64) =~= (s + z).push(0));
        lemma_seq_to_nat_push_zero(s + z);
    }
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

// =============================================================================
// — clearly marked: everything below answers the agentic file —
// =============================================================================
// The reference delivery of verus/q/q02_first_syntax_i/src/agent.rs is that file's own twin,
// Solutions/verus/q/q02_first_syntax_i/src/agent.rs: its definitions and bound proofs, the
// shipped suite verbatim, the adversarial checks and the author's note on the planted soft
// spots, in a closing section under this same heading.
