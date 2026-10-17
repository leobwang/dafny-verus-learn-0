//! Q04 — synthetic test fixture (tests/course_map). Not course content.
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

// item: Q04.P2dv S2 verdict
// SLOT: CHECK P2dv

// item: Q04.H1v S3
// uses: calc
// pair: Q04.H1d
pub proof fn h1(x: nat)
    ensures x + 0 == x,
{
    #[verifier::proof_note("Q04.H1v")] assume(false);
}

// item: Q04.H2v S4
// uses: lemma-call
pub proof fn h2()
    ensures true,
{
    #[verifier::proof_note("Q04.H2v")] assume(false);
}

} // verus!
