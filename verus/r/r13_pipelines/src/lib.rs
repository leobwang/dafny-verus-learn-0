//! # R13 — Pipelines and trust (Exercises)
//!
//! Imports: the given regex spine `rg_re_a1`, `rg_re_a1b`, `rg_re_a2`; nothing else: no
//! earlier exercise file.
//!
//! Each item below comes with a fake delivery, shown and run in the chapter (§8): a
//! version of the same task that some instrument reports as fine while it is not. Run
//! its instruments and attribute it in `research/r13_forensics.md` first, then replace
//! the hole with the honest proof; the statement stays as shipped.
//!
//! Done = `scripts/vcheck --gate verus/r/r13_pipelines` prints only the summary line and
//! exits 0, `scripts/vaudit verus/r/r13_pipelines` reports no finding,
//! `scripts/specfreeze --check R13` reports none, AND
//! `scripts/firsttry.sh R13 --report --strict` exits 0.
//!
//! This file ships with exactly 4 holes: T1 (closed-book test-out) and H1–H3.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a2::char_class::CharClass;

verus! {

/// Given: the derivative by every character of `u`, in order.
pub open spec fn derivs(r: Re, u: Seq<char>) -> Re
    decreases u.len(),
{
    if u.len() == 0 {
        r
    } else {
        derivs(deriv(r, u[0]), u.drop_first())
    }
}

// item: R13.T1v
// pair: R13.T1d
/// **T1.** (closed book) An executable matcher with the regex semantics as its contract.
/// `matches` is a spec fn: what may an exec fn call instead, and which layer supplies an
/// executable matcher with this postcondition?
pub fn accepts_r13(r: &Re, s: &Vec<char>) -> (b: bool)
    ensures
        b == matches(*r, s@),
{
    proof {
        #[verifier::proof_note("R13.T1v")] assume(false);  // HOLE: replace this block
    }
    false
}
// Hint(1): the chapter's fake delivery for T1 (§8) shows the call that is refused,
//          and the stage that refuses it.
// Hint(2): A2 re-supplies the derivative matcher.

// item: R13.H1v
// pair: R13.H1d
/// **H1.** Taking derivatives by `u + v` is taking them by `u`, then by `v`. The fake
/// delivery trusts an `external_body` proof fn. What are the first character and the
/// rest of `u + v` when `u` is not empty, and which call is the induction hypothesis?
pub proof fn lemma_derivs_cat_r13(r: Re, u: Seq<char>, v: Seq<char>)
    ensures
        derivs(r, u + v) == derivs(derivs(r, u), v),
    decreases u.len(),
{
    #[verifier::proof_note("R13.H1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): induction on `u.len()`; the base case needs `u + v =~= v`.
// Hint(2): assert `(u + v)[0] == u[0]` and `(u + v).drop_first() =~= u.drop_first() + v`,
//          then call the lemma on `deriv(r, u[0])`.

// item: R13.H2v
// pair: R13.H2d
/// **H2.** Every character of `s` lies in the class `cc`: a verified loop over A2's class
/// API, where the fake delivery trusts an `external_body` helper. What does the loop know
/// about the prefix it has read, and what ends it early?
pub fn class_covers_r13(cc: &CharClass, s: &Vec<char>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < s@.len() ==> cc@.contains(#[trigger] s@[i])),
{
    proof {
        #[verifier::proof_note("R13.H2v")] assume(false);  // HOLE: replace this block
    }
    false
}
// Hint(1): a `while` loop with an invariant over the indices below `k`.
// Hint(2): `cc.class_member(c)` promises `cc@.contains(c)`.

// item: R13.H3v
// pair: R13.H3d
/// **H3.** A word matches exactly when its derivatives end in a nullable regex. The fake
/// delivery proves it only for the empty word. Which A1b fact is the base case, and which
/// A2 fact moves one character from the word into the regex?
pub proof fn lemma_nullable_derivs_r13(r: Re, u: Seq<char>)
    ensures
        nullable(derivs(r, u)) == matches(r, u),
    decreases u.len(),
{
    #[verifier::proof_note("R13.H3v")] assume(false);  // HOLE: replace this line
}
// Hint(1): induction on `u.len()`; the base case is `lemma_nullable_correct`.
// Hint(2): `lemma_deriv_correct(r, u[0], u.drop_first())`, and
//          `seq![u[0]] + u.drop_first() =~= u`.

} // verus!
