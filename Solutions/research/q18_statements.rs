// Reference Solution (author-only): research/q18_statements.rs as a learner commits it at H2's step 2 (Q18.H2v):
// the Verus agent file with the reference trait, spec fns, witnesses and test rows, every operation a stub. The
// statement route of `firsttry.sh Q18 --empty-body` checks the reference delivery against it (the user's decision D9).
/* CONTRACT
goal: implement and prove every statement of the STATEMENTS sections of this file and of dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy, following the graded blueprint in paper/Q18_answers.tex (B1), changing no statement
allowed-files:
  - verus/q/q18_practice_iiic/src/agent.rs
  - dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck <the edited file>`; never stack unverified edits
  - `scripts/vcheck --gate verus/q/q18_practice_iiic/src/agent.rs` exits 0 with zero tool-counted holes
  - `scripts/vcheck --gate dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` exits 0 with zero tool-counted holes
  - `scripts/specfreeze --against research/q18_statements.rs verus/q/q18_practice_iiic/src/agent.rs` reports no change
  - `scripts/specfreeze --against research/q18_statements.dfy dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` reports no change
  - `scripts/vaudit verus/q/q18_practice_iiic/src/agent.rs` and `scripts/vaudit dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` report no finding
  - the differential check: `scripts/vcheck --test verus/q/q18_practice_iiic/src/agent.rs` and `scripts/vcheck --test dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` run every test on the same sample rows, and every test passes
  - `git diff` against the committed statements changes only the bodies of the statements and the two HELPERS sections; every WITNESSES and TESTS line is unchanged
  - new helper fns, proof fns, functions and lemmas go only under HELPERS
*/
//! # Q18 The capstone, Verus half: the crate's proof work — rungs 14a and 14b (`/contract Q18`)
//!
//! What this file ships: the given layers L1–L7 (the base API `BigNatCore` among them)
//! and vstd's multiplication and division lemmas imported, and six empty sections:
//! STATEMENTS, WITNESSES, TESTS, REVIEW, HELPERS and, at the end, AUDIT. It is green with
//! no hole: `scripts/vcheck` reports it verified, with 0 tool-counted holes and no error.
//! Check command:
//!
//!     scripts/vcheck verus/q/q18_practice_iiic/src/agent.rs
//!
//! The file is never `mod`-declared: no build of the crate reaches it; `scripts/vcheck`
//! verifies it on its own with the crate's dependencies. The capstone round's steps are
//! in the Dafny mirror's header (dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy):
//! the statement-only review runs from that file's CONTRACT, the co-developer from THIS
//! file's CONTRACT (name this file when `/contract Q18` asks which run it is).
//!
//! Your statements here (H2v): in STATEMENTS, an extension trait of L7's `BigNatCore`
//! (`pub trait <YourName>: BigNatCore { … }`) with each new operation as a trait method
//! with its `requires` and `ensures`, any spec fns your statements name, and `impl
//! <YourName> for BigNat` with every method marked `#[verifier::external_body]` over the
//! body `unimplemented!()` (a stub: the co-developer writes the bodies); the round trip as
//! a proof fn whose body is one labelled `assume(false)`. In WITNESSES, a fn that calls
//! each operation on concrete arguments; in TESTS, `#[test]` fns over the same sample rows
//! as the Dafny mirror's tests. Then copy this file to research/q18_statements.rs and
//! commit (the Dafny header's step 2).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l7::*;

verus! {

// item: Q18.A2dv S12

// item: Q18.H2v S12
// uses: trait-spec, witness
// ### STATEMENTS (learner-owned: your extension trait of `BigNatCore`, its spec fns, and
//    its `impl` for `BigNat` as `external_body` stubs). The new operations:
//    - multiplication of two values;
//    - division by one word `w > 0`: the quotient and the remainder;
//    - `to_decimal`: the value as decimal chunks, each below 10^19, least significant
//      chunk first (by repeated division by 10^19);
//    - `from_decimal`: back from such chunks (by Horner steps of `mul_limb` and
//      `add_limb`);
//    and the round trip as a proof fn.

// ### WITNESSES (learner-owned: a fn that calls each operation on concrete arguments and
//    asserts what its statement gives).

// ### REVIEW (the reviewer's, run A1dv: one proof fn per finding).

// ### HELPERS (the co-developer's, run A2dv: helper fns and proof fns).

// ===========================================================================================
// — clearly marked: everything below answers the agentic file —
// ===========================================================================================
// A reference set of statements (H2v) and the reference delivery (A2dv): the extension
// trait `BigNatOps` of `BigNatCore` with its spec fns, the round trip as a proof fn, the
// witnesses, the tests over the sample rows the Dafny mirror's tests use, and the impl with
// its helpers (Solutions/plans/Q18-code-notes.md §6).

/// The decimal chunk base, 10^19 (the largest power of ten below `BASE`).
pub open spec fn dec_base() -> nat {
    10000000000000000000
}

/// The value of decimal chunks, least significant chunk first.
pub open spec fn dec_to_nat(d: Seq<u64>) -> nat
    decreases d.len(),
{
    if d.len() == 0 {
        0
    } else {
        d[0] as nat + dec_base() * dec_to_nat(d.drop_first())
    }
}

/// Every chunk is a decimal digit in base 10^19.
pub open spec fn dec_digits(d: Seq<u64>) -> bool {
    forall|i: int| 0 <= i < d.len() ==> (#[trigger] d[i]) < dec_base()
}

/// Decimal digits with no zero chunk on top (zero is no chunk at all).
pub open spec fn dec_wf(d: Seq<u64>) -> bool {
    dec_digits(d) && (d.len() == 0 || d.last() != 0)
}

/// The capstone's new operations.
pub trait BigNatOps: BigNatCore {
    fn times(&self, other: &Self) -> (r: Self)
        requires
            self.valid(),
            other.valid(),
        ensures
            r.valid(),
            r.value() == self.value() * other.value(),
    ;

    fn div_word(&self, w: u64) -> (r: (Self, u64))
        requires
            self.valid(),
            w > 0,
        ensures
            r.0.valid(),
            r.1 < w,
            self.value() == r.0.value() * w + r.1,
    ;

    fn to_decimal(&self) -> (d: Vec<u64>)
        requires
            self.valid(),
        ensures
            dec_wf(d@),
            dec_to_nat(d@) == self.value(),
    ;

    fn from_decimal(d: &Vec<u64>) -> (r: Self)
        requires
            dec_digits(d@),
        ensures
            r.valid(),
            r.value() == dec_to_nat(d@),
    ;
}

/// The round trip: canonical decimal chunks are fixed by their value, so `to_decimal` gives
/// back the very chunks `from_decimal` read.
pub proof fn lemma_decimal_round_trip(d1: Seq<u64>, d2: Seq<u64>)
    requires
        dec_wf(d1),
        dec_wf(d2),
        dec_to_nat(d1) == dec_to_nat(d2),
    ensures
        d1 == d2,
    decreases d1.len(),
{
    #[verifier::proof_note("Q18.H2v")] assume(false);
}

/// The witnesses: each operation called on concrete arguments.
pub fn capstone_witnesses() {
    let six = BigNat::from_word(6);
    let seven = BigNat::from_word(7);
    let p = six.times(&seven);
    assert(p.value() == 42);
    let (q, r) = BigNat::from_word(43).div_word(6);
    assert(q.value() * 6 + r == 43 && r < 6);
    let d = p.to_decimal();
    assert(dec_to_nat(d@) == 42);
    let back = BigNat::from_decimal(&d);
    assert(back.value() == 42);
}

// ### The reference delivery (A2dv): the impl and its helpers.

impl BigNatOps for BigNat {
    #[verifier::external_body]
    fn times(&self, other: &Self) -> (r: Self) {
        unimplemented!()
    }

    #[verifier::external_body]
    fn div_word(&self, w: u64) -> (r: (Self, u64)) {
        unimplemented!()
    }

    #[verifier::external_body]
    fn to_decimal(&self) -> (d: Vec<u64>) {
        unimplemented!()
    }

    #[verifier::external_body]
    fn from_decimal(d: &Vec<u64>) -> (r: Self) {
        unimplemented!()
    }
}

} // verus!

// ### TESTS (learner-owned: the differential check's sample rows, as `#[test]` fns over
//    the same rows as the Dafny mirror's tests; tests sit outside `verus!`).

// The reference TESTS: the differential check's sample rows (the Dafny mirror's tests use
// the same rows).
#[cfg(test)]
mod capstone_tests {
    use super::*;

    fn big(v: &[u64]) -> BigNat {
        BigNat { limbs: v.to_vec() }
    }

    #[test]
    fn row1_times_small() {
        assert_eq!(big(&[6]).times(&big(&[7])).limbs, vec![42u64]);
    }

    #[test]
    fn row2_times_top_words() {
        let m = u64::MAX;
        assert_eq!(big(&[m]).times(&big(&[m])).limbs, vec![1u64, 18446744073709551614]);
    }

    #[test]
    fn row3_div_word_small() {
        let (q, r) = big(&[43]).div_word(6);
        assert_eq!((q.limbs, r), (vec![7u64], 1u64));
    }

    #[test]
    fn row4_div_word_by_dec_base() {
        let (q, r) = big(&[0, 1]).div_word(10000000000000000000);
        assert_eq!((q.limbs, r), (vec![1u64], 8446744073709551616u64));
    }

    #[test]
    fn row5_to_decimal_base() {
        assert_eq!(big(&[0, 1]).to_decimal(), vec![8446744073709551616u64, 1]);
    }

    #[test]
    fn row6_from_decimal_base() {
        assert_eq!(BigNat::from_decimal(&vec![8446744073709551616u64, 1]).limbs, vec![0u64, 1]);
    }

    #[test]
    fn row7_to_decimal_zero() {
        assert_eq!(big(&[]).to_decimal(), Vec::<u64>::new());
    }
}

// AUDIT (learner-owned; after the co-developer run)
//   each REVIEW finding: kept, changed a statement (which), or rejected (why):
//   the statement that cost the co-developer most, and why:
//   each helper's statement (does it assume what it should prove?):
