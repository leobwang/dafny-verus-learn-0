/*! R10 flagship: human statement design, then contractor proof bodies.
Before actor work, write original-domain contracts for all three constructors,
record nonvacuous input/output examples, and snapshot those statements.
The provided output type promises normal shape. Design and justify the
additional language promise yourself. The actor may edit only bodies and
reference-only helpers in its delivery; it must preserve your snapshot.
*/
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a4::*;

verus! {

// Your statements: add requires and ensures clauses to each constructor below,
// and snapshot the file under research/R10/ before any contractor edit. The
// contractor may add private proof helpers here and write the bodies.

// item: R10.A1v
#[verifier::external_body]
fn build_alt_r10(a: NormRe, b: NormRe) -> (out: NormRe)
{
    unimplemented!()
}

#[verifier::external_body]
fn build_cat_r10(a: NormRe, b: NormRe) -> (out: NormRe)
{
    unimplemented!()
}

#[verifier::external_body]
fn build_star_r10(a: NormRe) -> (out: NormRe)
{
    unimplemented!()
}

} // verus!
