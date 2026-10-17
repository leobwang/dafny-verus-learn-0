//! # Q03 — First syntax II: modes, logic, tooling, trust (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1` and `qg_bignat_l2` (`use
//! qg_bignat_l2::*;` brings both layers' names) and the vstd prelude, nothing else: no
//! earlier exercise crate. The layers are frozen and complete; read them, never edit them.
//!
//! How to work this file:
//! 1. Test-out first, closed book: T1 (below) before any reading, without its hints. Then
//!    run `scripts/firsttry.sh Q03 --check`, which records your first try (it runs T1's
//!    commented checks in a scratch copy), and only then uncomment those checks. If both
//!    files' T1 pass on that first try, you may skip the chapter section on ghost variables.
//! 2. Predictions next: P4 (the prediction block below; its answer goes in
//!    slots/Q03.slots), with every other prediction of the module (the Dafny file's
//!    prediction block, specimens/Q03/, dafny/checks/Q03_checks.dfy); record the first
//!    tries with `scripts/firsttry.sh Q03 --check` before you run anything they are about.
//! 3. Replace each hole, then uncomment the checks beneath it.
//! 4. Done = `scripts/vcheck --gate verus/q/q03_first_syntax_ii` prints only the summary
//!    line and exits 0, `scripts/vaudit verus/q/q03_first_syntax_ii` reports no finding,
//!    AND `scripts/firsttry.sh Q03 --report --strict` exits 0.
//! 5. Stuck for 20 minutes? /tutor Q03.
//!
//! This file ships with exactly 5 holes: T1 (test-out) and H1–H4, each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one
//! counted diagnostic). Commit every prediction BEFORE you run anything it is about, open
//! later files, or read CI, the registry or the plan: their checks and headers give some
//! predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header
//! (dafny/Q/Q03_FirstSyntaxII/core/Q03_FirstSyntaxII.dfy). Exit (closed book): src/exit.rs
//! here and the Dafny exit file, scored once by `scripts/firsttry.sh Q03 --exit`; src/exit.rs
//! is never part of this crate's build.
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// =========================================================================================
// Test-out (closed book, before any reading)
// =========================================================================================

// item: Q03.T1v S7
// uses: ghost
// pair: Q03.T1d
/// **T1.** (test-out) The largest limb of a non-empty vector.
/// Method clause: keep the index of the current maximum in a `let ghost` variable.
/// Which index proves the `exists` postcondition, and where may you assign to it?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn max_limb(v: &Vec<u64>) -> (m: u64)
    requires
        v.len() > 0,
    ensures
        forall|i: int| 0 <= i < v.len() ==> v@[i] <= m,
        exists|i: int| 0 <= i < v.len() && v@[i] == m,
{
    unimplemented!()
}
// Hint(1): a loop over the indices from 1, with one invariant per postcondition (the
//    first over the prefix read so far).
// Hint(2): the ghost index `w` satisfies `0 <= w < v.len()` and `v@[w] == m`.

fn max_limb_check() {
    // Uncomment as you go:
    // let mut v: Vec<u64> = Vec::new();
    // v.push(7);
    // let m = max_limb(&v);
    // assert(m == 7);
}

// =========================================================================================
// The prediction block. Commit every prediction of this module before you read past this
// block, and record the first tries:
//     scripts/firsttry.sh Q03 --check
// The verdict answer goes in slots/Q03.slots. The Dafny file's prediction block holds the
// cross-language predictions (P1, P2, P5–P8); specimens/Q03/ holds P3, P10 and P11–P14.
// =========================================================================================

// item: Q03.P4v S7 verdict
// **P4.** Modes. Four separate crates. Each holds these two declarations:
/*
    fn triple(x: u64) -> (r: u64)
        requires
            x < 1000,
        ensures
            r == 3 * x,
    {
        x * 3
    }

    proof fn lemma_pos(x: int)
        requires
            x > 0,
        ensures
            2 * x > x,
    {
    }

  and one more function, which makes one call:

    [a] a proof fn calls the exec fn:
            proof fn call_a() {
                let y = triple(3);
            }
    [b] a spec fn calls the exec fn:
            spec fn call_b() -> u64 {
                triple(3)
            }
    [c] an exec fn calls the proof fn on `x as int`, outside any proof block:
            fn call_c(x: u64) {
                if x > 0 {
                    lemma_pos(x as int);
                }
            }
    [d] the same call inside a `proof { }` block:
            fn call_d(x: u64) {
                if x > 0 {
                    proof {
                        lemma_pos(x as int);
                    }
                }
            }
*/
// Which of the four crates does `scripts/vcheck` accept (verified)?
// Answer form: the accepted labels in label order, separated by single spaces, or `none`.
// SLOT: CHECK P4v

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q03.W1v S7
/// **W1.** The mode triangle. A spec fn says what a value is, a proof fn proves a fact
/// about it, and an exec fn is specified through the spec fn and calls the proof fn
/// inside a `proof { }` block (ghost code inside exec code).
pub open spec fn succ_spec(x: int) -> int {
    x + 1
}

pub proof fn lemma_succ_gt(x: int)
    ensures
        succ_spec(x) > x,
{
}

pub fn succ(x: u64) -> (r: u64)
    requires
        x < u64::MAX,
    ensures
        r == succ_spec(x as int),
        r > x,
{
    proof {
        lemma_succ_gt(x as int);  // the fact `succ_spec(x as int) > x` is now known
    }
    x + 1
}

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q03/)
// =========================================================================================

// item: Q03.C1v S7 write:ghost
// C1 — card: ghost variables (`let ghost`, `Ghost<T>`).
// Jurisdiction: values the proof needs and the program never uses; they are checked,
// then erased. Success: `count_zero_limbs` keeps the limbs it has read in a ghost
// sequence, updated only inside `proof { }`. Failure: specimens/Q03/card-c1v.rs.specimen
// (a ghost value used by exec code).
pub open spec fn zero_count(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        zero_count(s.drop_last()) + if s.last() == 0 {
            1nat
        } else {
            0nat
        }
    }
}

pub fn count_zero_limbs(v: &Vec<u64>) -> (n: usize)
    ensures
        n == zero_count(v@),
{
    let mut n: usize = 0;
    let mut i: usize = 0;
    let ghost mut seen: Seq<u64> = Seq::empty();
    while i < v.len()
        invariant
            i <= v.len(),
            n <= i,
            seen == v@.subrange(0, i as int),
            n == zero_count(seen),
        decreases v.len() - i,
    {
        proof {
            assert(seen.push(v@[i as int]).drop_last() =~= seen);
            assert(seen.push(v@[i as int]) =~= v@.subrange(0, i as int + 1));
            seen = seen.push(v@[i as int]);
        }
        if v[i] == 0 {
            n = n + 1;
        }
        i = i + 1;
    }
    proof {
        assert(seen =~= v@);
    }
    n
}

// item: Q03.C2v S7 write:exec-check
// C2 — card: a runtime check that hands the verifier a fact.
// Jurisdiction: a precondition the caller cannot promise; test it in code and return the
// answer in an `Option`. Success: `safe_div`. Failure: specimens/Q03/card-c2v.rs.specimen
// (the unchecked division).
pub fn safe_div(a: u64, b: u64) -> (r: Option<u64>)
    ensures
        r.is_some() <==> b != 0,
        r.is_some() ==> r.unwrap() == a / b,
{
    if b != 0 {
        Some(a / b)
    } else {
        None
    }
}

// item: Q03.C3v S13 write:witness
// C3 — card: witnesses.
// Jurisdiction: an `exists` goal is proved by naming a term that works. Success:
// `lemma_exists_square_four` names 2. Failure: specimens/Q03/card-c3v.rs.specimen (the
// same proof fn, empty body).
pub open spec fn square(i: nat) -> nat {
    i * i
}

pub proof fn lemma_exists_square_four()
    ensures
        exists|i: nat| square(i) == 4,
{
    assert(square(2) == 4);
}

// item: Q03.C5v S7 write:modes
// C5 — card: spec, proof and exec modes.
// Jurisdiction: spec fns define (no code is run), proof fns prove (erased), exec fns run;
// ghost code reaches exec code only through `proof { }` blocks and ghost variables.
// Success: `half_spec`, `lemma_half_le` and `half`. Failure:
// specimens/Q03/card-c5v.rs.specimen (an exec variable assigned inside `proof { }`).
pub open spec fn half_spec(x: int) -> int {
    x / 2
}

pub proof fn lemma_half_le(x: int)
    requires
        x >= 0,
    ensures
        half_spec(x) <= x,
{
}

pub fn half(x: u64) -> (r: u64)
    ensures
        r == half_spec(x as int),
        r <= x,
{
    proof {
        lemma_half_le(x as int);
    }
    x / 2
}

// Rosetta card Q03.C9dv (quantifier triggers), Verus column. The card's marker and its
// Dafny column are in dafny/Q/Q03_FirstSyntaxII/core/Q03_FirstSyntaxII.dfy.
pub proof fn trigger_rosetta(s: Seq<u64>, k: int)
    requires
        forall|i: int| 0 <= i < s.len() ==> #[trigger] s[i] < 100,
        0 <= k < s.len(),
    ensures
        s[k] < 100,
{
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q03.H1v S7
// uses: invariant, ghost, modes
// pair: Q03.H1d
/// **H1.** Add one machine word to a BigNat, propagating the carry. The code, the ghost
/// carry sequence `c` and its updates, the `decreases`, the first invariant and the final
/// call of the given `lemma_add_limb_lift` (layer L2) are given: write the rest of the
/// loop invariant. What must hold of `c`, `res` and `carry` after `i` limbs, so that the
/// lift lemma's preconditions hold after the loop?
pub fn add_limb(a: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + x,
{
    let n = a.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut carry: u64 = x;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![x as nat];
    #[verifier::proof_note("Q03.H1v")] assume(false);  // HOLE: delete this line; write the rest of the invariant below
    while i < n
        invariant
            n == a@.len(),
        decreases n - i,
    {
        let li = a.limbs[i];
        if li <= u64::MAX - carry {
            res.push(li + carry);
            carry = 0;
        } else {
            res.push(li - (u64::MAX - carry) - 1);
            carry = 1;
        }
        i = i + 1;
        proof {
            c = c.push(carry as nat);
        }
    }
    if carry != 0 {
        res.push(carry);
        proof {
            c = c.push(0);
        }
    }
    let out = BigNat { limbs: res };
    proof {
        lemma_add_limb_lift(a@, out@, c);
    }
    out
}
// Hint(1): read the lift lemma's `requires`: each one must follow from the invariant and
//    the loop exit (and the code after the loop).
// Hint(2): besides the per-limb relation, the invariant needs bounds and lengths for
//    `i`, `res@` and `c`, the link between `c` and `carry`, and a bound on `carry`.

fn add_limb_check() {
    // Uncomment as you go:
    // let a = BigNat { limbs: Vec::new() };
    // let r = add_limb(&a, 5);
    // assert(r.to_nat() == 5);
}

// item: Q03.H2v S7
// uses: modes, assert
// pair: Q03.H2d
/// **H2.** The BigNat of one machine word: canonical limbs whose value is `x`. Which
/// limb sequence is it for `x == 0`, and which otherwise? What does the verifier need to
/// be told before `seq_to_nat` of a one-limb sequence is known?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn from_u64(x: u64) -> (r: BigNat)
    ensures
        r.wf(),
        r.to_nat() == x,
{
    unimplemented!()
}
// Hint(1): a `Vec` you push to at most once, then `BigNat { limbs: v }`.
// Hint(2): the value of a one-limb sequence unfolds once, to its limb plus `BASE` times
//    the value of an empty tail; L1's worked proof fn shows how to state such steps.

fn from_u64_check() {
    // Uncomment as you go:
    // let r = from_u64(5);
    // assert(r.to_nat() == 5);
}

// item: Q03.H3v S13
// uses: witness, assert
// pair: Q03.H3d
/// **H3.** Some canonical limb sequence has the value 5. Which sequence is the witness,
/// and what must the solver know about it before it can use it for the `exists`?
pub proof fn lemma_exists_canonical_five()
    ensures
        exists|s: Seq<u64>| seq_wf(s) && seq_to_nat(s) == 5,
{
    #[verifier::proof_note("Q03.H3v")] assume(false);  // HOLE: replace this line
}
// Hint(1): name the witness in a `let`, then `assert` both conjuncts for it.
// Hint(2): its value needs the same unfolding steps as H2.

// item: Q03.H4v S7
// uses: exec-check, modes
// pair: Q03.H4d
/// **H4.** A checked conversion from `u128` to a limb: `Some` exactly when `x` fits in a
/// limb, holding the same value. `BASE` is a spec const: what does the exec code test
/// instead?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn try_limb(x: u128) -> (r: Option<u64>)
    ensures
        r.is_some() <==> x < BASE,
        r.is_some() ==> r.unwrap() == x,
{
    unimplemented!()
}
// Hint: one `if` on a `u128` literal, and a cast.

fn try_limb_check() {
    // Uncomment as you go:
    // let r = try_limb(5);
    // assert(r.is_some() && r.unwrap() == 5);
}

} // verus!
