/* CONTRACT
goal: give count_zero_limbs, top_index and sum_limbs bodies that meet their doc contracts, and prove their three bound lemmas, so that every shipped check in this file verifies
allowed-files:
  - verus/q/q02_first_syntax_i/src/agent.rs
acceptance:
  - per edit, feedback only from the fast channel `scripts/vcheck --symbol <fn> verus/q/q02_first_syntax_i/src/agent.rs`, run on the fn just edited and on the checks and bound lemma that use it; never stack unverified edits
  - exactly one full `scripts/vcheck --gate verus/q/q02_first_syntax_i/src/agent.rs` run, as the last verifier command: exit 0, only the summary line printed
  - zero tool-counted holes in the allowed file
  - `git diff` shows only the bodies of the three definitions and of the three bound lemmas: each `pub uninterp spec fn … decreases s.len();` becomes `pub open spec fn … decreases s.len(), { … }`, each bound lemma's hole line is replaced by its proof, and no other line changes (no signature, `ensures`, doc comment or check, no declaration added or removed)
  - `scripts/vaudit --compare expected/q02_first_syntax_i_agent.audit verus/q/q02_first_syntax_i/src/agent.rs` reports no difference (an empty report: no finding)
*/
//! # Q02 Implementer, Verus half — implementer vs checks (Reference Solution)
//!
//! Hole-free reference for `verus/q/q02_first_syntax_i/src/agent.rs` (author-only): the
//! proof that the contract is satisfiable as stated. The three definitions meet their prose
//! contracts, the bound lemmas are proved, the six shipped checks (verbatim) verify, and
//! the closing reference section holds the adversarial checks and the author's note on the
//! planted soft spots. Never `mod`-declared, as in the learner crate. Silent under
//! `scripts/vcheck --ref`; `scripts/vaudit --ref` reports no finding, which
//! expected/q02_first_syntax_i_agent.audit pins (an empty report).
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// item: Q02.A1v S3

// ### The definitions. Their domain is every `Seq<u64>`.

/// The number of zero limbs of `s`: how many positions `i` have `s[i] == 0`.
pub open spec fn count_zero_limbs(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        (if s[0] == 0 { 1nat } else { 0nat }) + count_zero_limbs(s.drop_first())
    }
}

/// The index of the most significant non-zero limb of `s`: the largest `i` with
/// `s[i] != 0`, or `-1` when there is none (`s` empty, or every limb zero).
pub open spec fn top_index(s: Seq<u64>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        -1
    } else if s.last() != 0 {
        s.len() - 1
    } else {
        top_index(s.drop_last())
    }
}

/// The sum of the limbs of `s`, `s[0] + s[1] + … + s[s.len() - 1]` as natural numbers (not
/// the value `seq_to_nat(s)`); 0 for the empty sequence.
pub open spec fn sum_limbs(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + sum_limbs(s.drop_first())
    }
}

// ### The bound lemmas: the partial formal contracts, one per definition.

pub proof fn lemma_count_zero_limbs_bound(s: Seq<u64>)
    ensures
        count_zero_limbs(s) <= s.len(),
    decreases s.len(),
{
    if s.len() > 0 {
        lemma_count_zero_limbs_bound(s.drop_first());
    }
}

pub proof fn lemma_top_index_bound(s: Seq<u64>)
    ensures
        -1 <= top_index(s) < s.len(),
    decreases s.len(),
{
    if s.len() > 0 && s.last() == 0 {
        lemma_top_index_bound(s.drop_last());
    }
}

pub proof fn lemma_sum_limbs_empty(s: Seq<u64>)
    ensures
        s.len() == 0 ==> sum_limbs(s) == 0,
    decreases s.len(),
{
}

// ### The shipped checks (do not edit)

proof fn check_count_zero_limbs_1() {
    assert(count_zero_limbs(seq![0u64, 5u64, 0u64]) == 2) by (compute_only);
}

proof fn check_count_zero_limbs_2() {
    assert(count_zero_limbs(seq![7u64]) == 0) by (compute_only);
}

proof fn check_top_index_1() {
    assert(top_index(seq![1u64, 0u64]) == 0) by (compute_only);
}

proof fn check_top_index_2() {
    assert(top_index(seq![0u64, 7u64]) == 1) by (compute_only);
}

proof fn check_sum_limbs_1() {
    assert(sum_limbs(seq![2u64, 3u64]) == 5) by (compute_only);
}

proof fn check_sum_limbs_2() {
    assert(sum_limbs(seq![4u64]) == 4) by (compute_only);
}

// ### ADVERSARIAL CHECKS (learner-owned; after the contract run). Write each as a proof fn
//    like the shipped ones, below this line.

// =============================================================================
// — clearly marked: everything below answers the agentic file —
// =============================================================================
// The reference delivery is the three bodies above (recursion on the length) and the three
// bound proofs (the same recursion; the empty case unfolds the definition once). The
// adversarial checks below hold for it; each one fails a planted soft spot, a wrong body
// that passes all six shipped checks and its bound lemma:
//
//   count_zero_limbs  soft spot: count the zero limbs at even positions only (every zero
//                     of every shipped check sits at an even position).
//                     Caught by adv_count_zero_limbs_odd_position.
//   top_index         soft spot: scan down from the top and stop at index 0, returning 0
//                     for an all-zero sequence (0 satisfies the bound when s is not
//                     empty). Caught by adv_top_index_all_zero; adv_top_index_empty pins
//                     the empty case the contract names.
//   sum_limbs         soft spot: sum the first two limbs only (no shipped check has more).
//                     Caught by adv_sum_limbs_three.
//
// Unlike the Dafny half (whose limbs are any nat, so `% BASE` is a soft spot there), a
// u64 limb is always below BASE: the Verus soft spots are positional instead.

proof fn adv_count_zero_limbs_odd_position() {
    assert(count_zero_limbs(seq![5u64, 0u64]) == 1) by (compute_only);
}

proof fn adv_top_index_all_zero() {
    assert(top_index(seq![0u64, 0u64]) == -1) by (compute_only);
}

proof fn adv_top_index_empty() {
    assert(top_index(Seq::<u64>::empty()) == -1) by (compute_only);
}

proof fn adv_sum_limbs_three() {
    assert(sum_limbs(seq![1u64, 2u64, 3u64]) == 6) by (compute_only);
}

} // verus!

// LATENCY LOG (learner-owned; from the contract transcript)
//   fast-channel runs: count, typical wall time:
//   the one full gate run: wall time:
//   what the fast channel did not tell the contractor:
