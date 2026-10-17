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
//! # Q02 Implementer, Verus half — implementer vs checks (`/contract Q02`)
//!
//! What this file ships: three definitions over limb sequences, each stated by a prose
//! contract (its doc comment) and a partial formal one (its bound lemma), each an
//! uninterpreted spec fn whose body is to be written, one bound-lemma hole per definition,
//! and a live suite of six checks, two per definition. It is RED by design: the three
//! `uninterp` definitions and the three bound lemmas are 6 tool-counted holes, and no check
//! can hold over an uninterpreted definition. As shipped, the command below reports 6 holes
//! and 1 error, at the first shipped check. Check command:
//!
//!     scripts/vcheck verus/q/q02_first_syntax_i/src/agent.rs
//!
//! One failing check at a time (a limit of the pinned Verus, not of this file). The checks
//! are `by (compute_only)` asserts, which Verus evaluates for the whole file before its SMT
//! verification starts, and the run stops at the first check that does not evaluate to
//! true. So a run reports one failing check, the first in file order, and a check further
//! down shows its result only once every check above it holds. The fast channel cannot
//! isolate a check either: while any check fails, `scripts/vcheck --symbol <fn> …` reports
//! that same first failing check and prints `symbol <fn>: failed`, whichever fn it names,
//! one whose own checks hold included. Read the error's line, not the symbol line, and keep
//! this in mind when you tally the transcript (step 3).
//!
//! The file is never `mod`-declared: no build of the crate reaches it; `scripts/vcheck`
//! verifies it on its own with the crate's dependencies.
//!
//! Learner follow-up (after the contractor delivers; THIS is the exercise):
//! 1. Before the run: read the three contracts and run the command above; read every message.
//! 2. In a FRESH session, run /contract Q02 on this file.
//! 3. Tally the transcript: only the fast channel per edit? exactly one full gate, last?
//!    touched a statement or a check? reached for an escape hatch? Fill the LATENCY LOG
//!    below from the transcript's timings.
//! 4. Check the artifact yourself: the gate output, `git diff` scope, `scripts/vaudit`.
//! 5. Write ADVERSARIAL CHECKS (the block at the end): inputs the shipped suite never
//!    tried, judged against the prose contracts. The doc contracts say more than the bound
//!    lemmas and the checks do.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// item: Q02.A1v S3

// ### The definitions. Their domain is every `Seq<u64>`.

/// The number of zero limbs of `s`: how many positions `i` have `s[i] == 0`.
pub uninterp spec fn count_zero_limbs(s: Seq<u64>) -> nat
    decreases s.len();

/// The index of the most significant non-zero limb of `s`: the largest `i` with
/// `s[i] != 0`, or `-1` when there is none (`s` empty, or every limb zero).
pub uninterp spec fn top_index(s: Seq<u64>) -> int
    decreases s.len();

/// The sum of the limbs of `s`, `s[0] + s[1] + … + s[s.len() - 1]` as natural numbers (not
/// the value `seq_to_nat(s)`); 0 for the empty sequence.
pub uninterp spec fn sum_limbs(s: Seq<u64>) -> nat
    decreases s.len();

// ### The bound lemmas: the partial formal contracts, one per definition.

pub proof fn lemma_count_zero_limbs_bound(s: Seq<u64>)
    ensures
        count_zero_limbs(s) <= s.len(),
    decreases s.len(),
{
    #[verifier::proof_note("Q02.A1v")] assume(false);  // HOLE: replace this line
}

pub proof fn lemma_top_index_bound(s: Seq<u64>)
    ensures
        -1 <= top_index(s) < s.len(),
    decreases s.len(),
{
    #[verifier::proof_note("Q02.A1v")] assume(false);  // HOLE: replace this line
}

pub proof fn lemma_sum_limbs_empty(s: Seq<u64>)
    ensures
        s.len() == 0 ==> sum_limbs(s) == 0,
    decreases s.len(),
{
    #[verifier::proof_note("Q02.A1v")] assume(false);  // HOLE: replace this line
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

} // verus!

// LATENCY LOG (learner-owned; from the contract transcript)
//   fast-channel runs: count, typical wall time:
//   the one full gate run: wall time:
//   what the fast channel did not tell the contractor:
