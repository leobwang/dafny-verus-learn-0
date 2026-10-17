/* CONTRACT
goal: for each of the four DELIVERIES, fill its row of the ATTRIBUTIONS block (the stage at which its quoted attempt stops, the instrument whose output shows it, the root cause), then repair the attempt into a verified proof or implementation without changing its statement
allowed-files:
  - verus/q/q15_practice_iic/src/agent.rs
acceptance:
  - re-verify after every edit with `scripts/vcheck verus/q/q15_practice_iic/src/agent.rs`; never stack unverified edits
  - `scripts/vcheck --gate verus/q/q15_practice_iic/src/agent.rs` exits 0, with zero tool-counted holes
  - `scripts/specfreeze --against research/q15_forensic.rs verus/q/q15_practice_iic/src/agent.rs` reports no change
  - `scripts/vaudit verus/q/q15_practice_iic/src/agent.rs` reports no finding
  - `scripts/vcheck --test verus/q/q15_practice_iic/src/agent.rs` runs the test and it passes
  - every row of ATTRIBUTIONS is filled: stage, instrument and root cause, each from a tool's output you ran
*/
//! # Q15 Pipeline forensic, Verus half — rung 11 (`/contract Q15`)
//!
//! What this file ships: four DELIVERIES about the BigNat spine (layers L1-L6), each a
//! statement whose body is one labelled `assume(false)` or an external body (a hole) and,
//! in its doc comment, the attempt a contractor delivered for it. Each attempt stops at a
//! different stage of the pipeline, and none of them is in the file: as shipped it is
//! green with holes, `scripts/vcheck` reports it verified with exactly 4 tool-counted holes
//! and no error. An empty ATTRIBUTIONS block and the AUDIT block are at the end. Check
//! command:
//!
//!     scripts/vcheck verus/q/q15_practice_iic/src/agent.rs
//!
//! The file is never `mod`-declared: no build of the crate reaches it; `scripts/vcheck`
//! verifies it on its own with the crate's dependencies. Its statements, as shipped, are
//! also in research/q15_forensic.rs (the freeze reference).
//!
//! Learner follow-up (after the contractor delivers; THIS is the exercise, with the Dafny
//! half's): in a FRESH session, run /contract Q15 on this file; then grade its
//! ATTRIBUTIONS against the tools' output and your own first pass, and fill AUDIT.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l6::*;

verus! {

// item: Q15.A1v S10

// ### DELIVERIES (four; repair each attempt, statement unchanged)

/// D1. The value of a two-limb sequence. The attempt delivered:
///
///     {
///         reveal_with_fuel(seq_to_nat, 3);
///         assert(seq![d0, d1].drop_first() =~= seq![d1];
///         assert(seq![d1].drop_first() =~= Seq::<u64>::empty());
///     }
pub proof fn lemma_pair_value(d0: u64, d1: u64)
    ensures
        seq_to_nat(seq![d0, d1]) == d0 + BASE * d1,
{
    #[verifier::proof_note("Q15.A1v")] assume(false);  // HOLE: replace this line
}

/// D2. A limb pushed on top lands at the place value of the length. The attempt
/// delivered:
///
///     {
///         lemma_seq_to_nat_push(s, d);
///     }
pub proof fn lemma_push_value(s: Seq<u64>, d: u64)
    ensures
        seq_to_nat(s.push(d)) == seq_to_nat(s) + weight(s.len()) * d,
{
    #[verifier::proof_note("Q15.A1v")] assume(false);  // HOLE: replace this line
}

/// D3. Every place value is at least one. The attempt delivered:
///
///     {
///         lemma_weight_zero();
///     }
pub proof fn lemma_weight_at_least_one(n: nat)
    ensures
        1 <= weight(n),
{
    #[verifier::proof_note("Q15.A1v")] assume(false);  // HOLE: replace this line
}

/// D4. The low limb of a two-limb number, low limb first; its test is
/// `tests::low_of_five_and_nine` below. The attempt delivered:
///
///     {
///         if d0 < d1 { d1 } else { d0 }
///     }
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn low_of_two(d0: u64, d1: u64) -> (r: u64)
    ensures
        r == d0 || r == d1,
{
    unimplemented!()
}

} // verus!

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn low_of_five_and_nine() {
        assert_eq!(low_of_two(5, 9), 5);
    }
}

// ATTRIBUTIONS (the contractor's; one row per delivery)
//   delivery | stage | instrument (the command whose output shows it) | root cause
//   D1       |       |                                                 |
//   D2       |       |                                                 |
//   D3       |       |                                                 |
//   D4       |       |                                                 |

// AUDIT (learner-owned; after the contract run)
//   each row right or wrong, with the command that settles it:
//   did it change a statement, or touch a file outside its allowlist:
//   where its attributions differ from your first pass, and who was right:
