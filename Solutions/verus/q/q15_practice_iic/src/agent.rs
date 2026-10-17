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
//! # Q15 Pipeline forensic, Verus half — rung 11 (Reference Solution)
//!
//! Hole-free reference for `verus/q/q15_practice_iic/src/agent.rs` (author-only; never
//! learner-visible): the delivery a correct contract run ends with. Same CONTRACT,
//! imports, statements and order; each attempt repaired, ATTRIBUTIONS filled from the
//! captured tool output (Solutions/plans/Q15-code-notes.md §6).
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
    reveal_with_fuel(seq_to_nat, 3);  // did: the value of the literal sequence
    assert(seq![d0, d1].drop_first() =~= seq![d1]);
    assert(seq![d1].drop_first() =~= Seq::<u64>::empty());
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
    assert(s.push(d) =~= s + seq![d]);
    lemma_seq_to_nat_append(s, seq![d]);
    reveal_with_fuel(seq_to_nat, 2);  // did: the value of the one-limb sequence
    assert(seq![d].drop_first() =~= Seq::<u64>::empty());
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
    lemma_weight_pos(n);
}

/// D4. The low limb of a two-limb number, low limb first; its test is
/// `tests::low_of_five_and_nine` below. The attempt delivered:
///
///     {
///         if d0 < d1 { d1 } else { d0 }
///     }
pub fn low_of_two(d0: u64, d1: u64) -> (r: u64)
    ensures
        r == d0 || r == d1,
{
    d0
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
//   D1       | parse   | scripts/vcheck <file>: `mismatched closing delimiter`, stage parse | the first assert's call is never closed
//   D2       | resolve | scripts/vcheck <file>: `cannot find function lemma_seq_to_nat_push`, stage resolve | no layer declares it; the append law of layer L4 and the one-limb value do the work
//   D3       | verify  | scripts/vcheck <file>: `postcondition not satisfied` | weight(0) says nothing about weight(n); layer L5's positivity does
//   D4       | test    | scripts/vcheck --test <file>: `FAILED tests::low_of_five_and_nine` | the ensures admits either limb; the attempt returns the larger, the test asks for the low one

// AUDIT (learner-owned; after the contract run)
//   each row right or wrong, with the command that settles it:
//   did it change a statement, or touch a file outside its allowlist:
//   where its attributions differ from your first pass, and who was right:
