/*! R06 — Induction and loops (Exercises).
Standalone R, A1/A1b only. The given Deriv and deriv_exec are complete;
no A2 or earlier learner proof is imported. Five holes in each hand file
(T1 and H1-H4); two code test-outs, six predictions and four unseen exits.
T1 is closed book before the worked examples. Record all prediction/test-out
first tries with scripts/firsttry.sh R06 --check before enabling switches.
H1 needs your measure. H2 retains its loop, decreasing measure and proof call;
supply invariants and connecting facts. H4 opens only its requires clause:
repair with the weakest hypothesis, not an arbitrary sufficient restriction.
Done: complete zero-hole native gates, audit, freeze, strict report, checkpoint,
written work, decomposer review, fifth bench card, viva and calibration.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::calc;
use rg_re_a1::*;
use rg_re_a1b::*;
verus! {
// GIVEN: specification and proved executable derivative.
pub open spec fn deriv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv(*a, c)), Box::new(deriv(*b, c))),
        Re::Cat(a, b) => if nullable(*a) {
            Re::Alt(Box::new(Re::Cat(Box::new(deriv(*a, c)), b)), Box::new(deriv(*b, c)))
        } else {
            Re::Cat(Box::new(deriv(*a, c)), b)
        },
        Re::Star(a) => Re::Cat(Box::new(deriv(*a, c)), Box::new(Re::Star(a))),
    }
}
pub fn deriv_exec(r: &Re, c: char) -> (out: Re)
    ensures
        out == deriv(*r, c),
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == *d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv_exec(a, c)), Box::new(deriv_exec(b, c))),
        Re::Cat(a, b) => if is_nullable(a) {
            Re::Alt(
                Box::new(Re::Cat(Box::new(deriv_exec(a, c)), Box::new(copy_re(b)))),
                Box::new(deriv_exec(b, c)),
            )
        } else {
            Re::Cat(Box::new(deriv_exec(a, c)), Box::new(copy_re(b)))
        },
        Re::Star(a) => Re::Cat(Box::new(deriv_exec(a, c)), Box::new(Re::Star(Box::new(copy_re(a))))),
    }
}

// item: R06.T1v
// pair: R06.T1d
// uses: invariant
// Closed book before reading; implement with a while loop.
#[verifier::external_body]
pub fn all_nullable(rs: &Vec<Re>) -> (b: bool)
    ensures b == (forall|i:int| 0 <= i < rs.len() ==> nullable(#[trigger] rs@[i])),
{ unimplemented!() }

// item: R06.W1v
pub proof fn lemma_deriv_base(r: Re,c: char,s: Seq<char>)
    requires r is Empty || r is Eps || r is Chr,
    ensures matches(deriv(r,c),s) <==> matches(r,seq![c]+s),
{
    match r {
        Re::Chr(d) => { assert((seq![c]+s)[0] == c); },
        _ => { },
    }
}
// item: R06.W2v
pub fn all_same(s: &Vec<char>,c: char) -> (b: bool)
    ensures b == (forall|j:int| 0 <= j < s.len() ==> #[trigger] s@[j] == c),
{
    let mut b=true;let mut i:usize=0;
    while i < s.len()
        invariant i <= s.len(),b == (forall|j:int| 0 <= j < i ==> #[trigger] s@[j] == c),
        decreases s.len()-i,
    { b = b && s[i] == c; i=i+1; }
    b
}
// item: R06.C1v write:calc
// calc! states its relation and each justified intermediate expression.
// item: R06.C2v write:invariant
// The invariant relates the visited prefix to the accumulator.
// item: R06.C3v write:lemma-decreases
// A recursive proof fn gives a well-founded decreasing measure.

// item: R06.H1v
// pair: R06.H1d
// uses: lemma-decreases, calc
// The measure is yours; prove every constructor.
pub proof fn lemma_deriv_correct(r: Re,c: char,s: Seq<char>)
    ensures matches(deriv(r,c),s) <==> matches(r,seq![c]+s),
{ #[verifier::proof_note("R06.H1v")] assume(false); }

// item: R06.H2v
// pair: R06.H2d
// uses: invariant
pub fn deriv_match(r: &Re,s: &Vec<char>) -> (b: bool)
    ensures b == matches(*r,s@),
{
    proof { #[verifier::proof_note("R06.H2v")] assume(false); }
    let mut cur=copy_re(r);let mut i:usize=0;
    while i < s.len()

        decreases s.len()-i,
    {
        proof {
            lemma_deriv_correct(cur,s@[i as int],s@.subrange(i+1,s@.len() as int));

        }
        cur=deriv_exec(&cur,s[i]);
        i=i+1;
    }

    is_nullable(&cur)
}

// item: R06.H3v
// pair: R06.H3d
pub proof fn lemma_star_unfold_refuted()
    ensures exists|a:Re,s:Seq<char>| matches(Re::Star(Box::new(a)),s) && !matches(Re::Cat(Box::new(a),Box::new(Re::Star(Box::new(a)))),s),
{ #[verifier::proof_note("R06.H3v")] assume(false); }

// item: R06.H4v
// pair: R06.H4d
// uses: calc
// REPAIR: add the weakest sufficient requires; retain the exact postcondition.
pub proof fn lemma_star_unfold(a: Re,s: Seq<char>)
    ensures matches(Re::Star(Box::new(a)),s) <==> matches(Re::Cat(Box::new(a),Box::new(Re::Star(Box::new(a)))),s),
{ #[verifier::proof_note("R06.H4v")] assume(false); }
} // verus!
