//! # Q01 — Hello, Dafny and Verus: the whole map (Exercises, Verus half)
//!
//! Imports: `vstd::prelude` (the Verus language and its specification types) and the
//! given BigNat layer L1 (`qg_bignat_l1`, frozen: `seq_to_nat`, `seq_wf`, `BigNat`, the
//! worked proof fn). Nothing else, and no earlier exercise file.
//!
//! How to work this file:
//! 1. The prediction block for Q01 is at the top of the Dafny file,
//!    `dafny/Q/Q01_Hello/core/Q01_Hello.dfy`, with P4v and P6v in `specimens/Q01/`:
//!    commit every prediction (`scripts/firsttry.sh Q01 --check`) before you read on.
//! 2. Read the worked examples (W1v, W2v) and the cards; the Rosetta columns below are
//!    the Verus side of the Dafny file's RECOGNISE cards.
//! 3. Replace each hole, then uncomment the checks beneath it.
//! 4. Done = `scripts/vcheck --gate verus/q/q01_hello` prints only the summary line and
//!    exits 0, `scripts/vaudit verus/q/q01_hello` reports no finding, AND
//!    `scripts/firsttry.sh Q01 --report --strict` exits 0.
//! 5. Stuck for 20 minutes? /tutor Q01.
//!
//! This file ships with exactly 3 holes: H1v, H2v, H3v (the Dafny file holds the other
//! 3 of the module's 6). Item kinds: W worked (given, live) · C card · H one-hole item.
//! A hole is a typed placeholder; `scripts/vcheck` counts them (here under
//! `--no-cheating`, so an `assume` or an `external_body` is reported), never grep.
//! Commit every prediction BEFORE you run anything it is about, open later files, or read
//! CI, the registry or the plan: their checks and headers give some predictions away.
//!
//! The agentic exercise (repairer, `src/agent.rs`, with its Dafny half) is described at
//! the bottom of the Dafny file. The closed-book exit is `src/exit.rs` with
//! `dafny/Q/Q01_Hello/exit/Q01_Map.dfy`.
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
/// **H1v.** The larger of two `u64`s: `m` is at least `a` and at least `b`, and it is one
/// of them. Implement it.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn max2(a: u64, b: u64) -> (m: u64)
    ensures
        m >= a && m >= b && (m == a || m == b),
{
    unimplemented!()
}
// Hint(1): one `if`, one branch per argument.
// Hint(2): which comparison decides the branch, and what does each branch return?

// Uncomment as you go:
// fn max2_check() { let m = max2(3, 7); assert(m == 7); }

// item: Q01.H2v S3
// uses: assert, lemma-call
// pair: Q01.H2d
/// **H2v.** Two zero limbs appended at the most significant end do not change the value.
/// The L1 worked proof fn removes one zero; in which form of "append" is it stated?
pub proof fn lemma_append_two_zeros(s: Seq<u64>)
    ensures
        seq_to_nat(s + seq![0u64, 0u64]) == seq_to_nat(s),
{
    #[verifier::proof_note("Q01.H2v")] assume(false);  // HOLE: replace this line
}
// Hint(1): `assert(x =~= y)` states that two sequences are equal element by element;
//    use it to restate `s + seq![0u64, 0u64]` in the worked proof fn's form.
// Hint(2): one zero at a time: which sequence does each call of the worked proof fn need?

// item: Q01.H3v S4
// uses: lemma-call
// pair: Q01.H3d
/// **H3v.** A sequence whose limbs are all zero has value 0. Recursion on what, and
/// why does the shorter sequence still meet the `requires`?
pub proof fn lemma_all_zero(s: Seq<u64>)
    requires
        forall|i: int| 0 <= i < s.len() ==> s[i] == 0,
    ensures
        seq_to_nat(s) == 0,
    decreases s.len(),
{
    #[verifier::proof_note("Q01.H3v")] assume(false);  // HOLE: replace this line
}
// Hint(1): when `s` is not empty, call the proof fn itself on `s.drop_first()`.
// Hint(2): the empty sequence needs no call: what does `seq_to_nat` give for it?

} // verus!
