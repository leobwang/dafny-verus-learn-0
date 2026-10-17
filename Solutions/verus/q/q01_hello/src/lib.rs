//! # Q01 — Hello, Dafny and Verus: the whole map (Reference Solution, Verus half)
//!
//! Hole-free reference for `verus/q/q01_hello/src/lib.rs`. Same item markers,
//! declarations and order as the learner crate; every hole is filled and every check is
//! live. The prediction block (the seven `dv` verdict items) is in the Dafny twin,
//! `Solutions/dafny/Q/Q01_Hello/core/Q01_Hello.dfy`; P4v and P6v are specimens.
//!
//! Every output the course quotes for this crate is pinned (`expected/Q01.counts`, the
//! WRITE-card demos' EXPECT lines, the false-friends sidecars). The crate is silent:
//! `scripts/vcheck --ref` on it prints only the summary line.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l1::*;

verus! {

// =====================================================================================
// Worked examples
// =====================================================================================

// item: Q01.W1v S3
/// **W1v.** The L1 worked proof fn, proved again with an `assert` after each step that
/// states what the verifier knows at that point.
pub proof fn lemma_push_zero_stepwise(s: Seq<u64>)
    ensures
        seq_to_nat(s.push(0)) == seq_to_nat(s),
    decreases s.len(),
{
    if s.len() == 0 {
        assert(s.push(0).drop_first() =~= Seq::<u64>::empty());
        assert(seq_to_nat(Seq::<u64>::empty()) == 0);
    } else {
        // Dropping the low limb of `s.push(0)` leaves the rest of `s`, then the zero.
        assert(s.push(0).drop_first() =~= s.drop_first().push(0));
        // The same fact for the shorter sequence (the recursive call).
        lemma_push_zero_stepwise(s.drop_first());
        assert(seq_to_nat(s.drop_first().push(0)) == seq_to_nat(s.drop_first()));
        // The definition of seq_to_nat, read on `s.push(0)` and on `s`: both sides agree.
        assert(seq_to_nat(s.push(0)) == s[0] as nat + BASE * seq_to_nat(s.drop_first()));
        assert(seq_to_nat(s) == s[0] as nat + BASE * seq_to_nat(s.drop_first()));
    }
}

// item: Q01.W2v S1
/// **W2v.** A first verified exec fn: the low limb of a BigNat with at least one limb,
/// stated over its spec view `a@`.
pub fn low_limb(a: &BigNat) -> (d: u64)
    requires
        a@.len() > 0,
    ensures
        d == a@[0],
{
    a.limbs[0]
}

// =====================================================================================
// WRITE cards: one success here, one pinned failure in specimens/Q01/card-*.specimen
// =====================================================================================

// item: Q01.C1v S2 write:ensures
// ### C1v — card: `ensures` (WRITE)
// Jurisdiction: what a fn promises its callers about its result; the body must establish
// it. Success: `inc` below. Failure: specimens/Q01/card-c1v.rs.specimen (its EXPECT line
// pins the message).
pub fn inc(x: u64) -> (y: u64)
    requires
        x < 100,
    ensures
        y == x + 1,
{
    x + 1
}

// item: Q01.C2v S3 write:assert
// ### C2v — card: `assert` (WRITE)
// Jurisdiction: a fact the verifier must prove at this point; afterwards it is known.
// Success: `assert_step` below. Failure: specimens/Q01/card-c2v.rs.specimen.
pub fn assert_step(x: u64)
    requires
        x < 100,
{
    let y = x + 2;
    assert(y > x);
}

// item: Q01.C3v S3 write:lemma-call
// ### C3v — card: calling a proof fn (WRITE)
// Jurisdiction: a call proves the proof fn's `requires` at the call site and then knows
// its `ensures` there. Success: `wf_push_call` below. Failure:
// specimens/Q01/card-c3v.rs.specimen.
/// The card proof fn (given): pushing a nonzero limb gives a canonical sequence.
pub proof fn lemma_wf_push(s: Seq<u64>, d: u64)
    requires
        d != 0,
    ensures
        seq_wf(s.push(d)),
{
}

pub proof fn wf_push_call(s: Seq<u64>) {
    lemma_wf_push(s, 7);
    assert(seq_wf(s.push(7)));
}

} // verus!

// =====================================================================================
// Rosetta columns: the Verus side of the RECOGNISE cards C5dv–C10dv (the cards and their
// Dafny columns are in dafny/Q/Q01_Hello/core/Q01_Hello.dfy)
// =====================================================================================
verus! {

// C5dv `requires`
pub fn get_limb(v: &Vec<u64>, i: usize) -> (d: u64)
    requires
        i < v.len(),
    ensures
        d == v@[i as int],
{
    v[i]
}

// C6dv `decreases`
pub open spec fn reverse_limbs(s: Seq<u64>) -> Seq<u64>
    decreases s.len(),
{
    if s.len() == 0 {
        Seq::empty()
    } else {
        reverse_limbs(s.drop_first()).push(s[0])
    }
}

// C7dv loop `invariant`
pub fn count_to(n: u64) -> (i: u64)
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i < n
        invariant
            i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

// C8dv `forall` in a specification
pub open spec fn all_below(s: Seq<u64>, b: u64) -> bool {
    forall|i: int| 0 <= i < s.len() ==> s[i] < b
}

// C9dv ghost code
pub fn ghost_demo(x: u64) -> (y: u64)
    requires
        x < 100,
    ensures
        y == x + 1,
{
    let ghost before = x;
    let y = x + 1;
    assert(y == before + 1);
    y
}

// C10dv a specification function
pub open spec fn is_zero_limb(d: u64) -> bool {
    d == 0
}

} // verus!

// =====================================================================================
// Holes
// =====================================================================================
verus! {

// item: Q01.H1v S2
// uses: ensures
// pair: Q01.H1d
/// **H1v.** Why this body: each branch returns one of the arguments (the third conjunct),
/// and the guard makes it the larger one (the first two). No arithmetic, so no overflow
/// obligation arises.
pub fn max2(a: u64, b: u64) -> (m: u64)
    ensures
        m >= a && m >= b && (m == a || m == b),
{
    if a >= b {
        a
    } else {
        b
    }
}

// reference-only: live in the twin, commented in the learner crate
fn max2_check() {
    let m = max2(3, 7);
    assert(m == 7);
}

// reference-only: an extra edge check (equal arguments)
fn max2_equal_check() {
    let m = max2(4, 4);
    assert(m == 4);
}

// item: Q01.H2v S3
// uses: assert, lemma-call
// pair: Q01.H2d
/// **H2v.** Why this proof: `s + seq![0u64, 0u64]` is extensionally `s.push(0).push(0)`
/// (the `=~=` assert states it, so the verifier can use the worked lemma's `push` form),
/// and the worked lemma applied twice, first to `s.push(0)`, then to `s`, removes the two
/// zeros one at a time.
pub proof fn lemma_append_two_zeros(s: Seq<u64>)
    ensures
        seq_to_nat(s + seq![0u64, 0u64]) == seq_to_nat(s),
{
    assert(s + seq![0u64, 0u64] =~= s.push(0).push(0));
    lemma_seq_to_nat_push_zero(s.push(0));
    lemma_seq_to_nat_push_zero(s);
}

// item: Q01.H3v S4
// uses: lemma-call
// pair: Q01.H3d
/// **H3v.** Why this proof: a recursive call on `s.drop_first()`, whose limbs are also
/// all zero; the value of `s` is `s[0] + BASE * seq_to_nat(s.drop_first())`, and both
/// terms are 0.
pub proof fn lemma_all_zero(s: Seq<u64>)
    requires
        forall|i: int| 0 <= i < s.len() ==> s[i] == 0,
    ensures
        seq_to_nat(s) == 0,
    decreases s.len(),
{
    if s.len() > 0 {
        lemma_all_zero(s.drop_first());
    }
}

} // verus!
