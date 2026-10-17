/*! R05 — No goal state (Exercises).
Standalone R, layer A1 only. Do not import earlier learner proofs or A1b.
Four predictions first: commit P1d/P2v in their specimens and P3dv/P4dv in
slots/R05.slots; record scripts/firsttry.sh R05 --check before enabling them.
This file has four holes. The paired crate has four; variance.py has two.
For H4 keep the given branch, choice, recursive call and measure: add facts.
Done: all native/Python gates, audit, freeze, strict firsttry, variance and
LATENCY logs, written work, OBLIGATION LOG, fourth bench card and viva.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
verus! {
// item: R05.W1v
pub proof fn lemma_slice_bridge(s: Seq<char>, i: int)
    requires 0 <= i < s.len(),
    ensures s.subrange(i,s.len() as int) == seq![s[i]] + s.subrange(i+1,s.len() as int),
{
    let tail = s.subrange(i,s.len() as int);
    assert(tail.len() > 0);
    assert(tail[0] == s[i]);
    assert(tail.drop_first() =~= s.subrange(i+1,s.len() as int));
    assert(tail =~= seq![tail[0]] + tail.drop_first());
    assert(s.subrange(i,s.len() as int) == seq![s[i]] + s.subrange(i+1,s.len() as int));
}
// item: R05.W2v
#[verifier::spinoff_prover]
pub proof fn lemma_scoped_arithmetic(n: int)
    requires n >= 0,
    ensures n+3 > n,
{
    assert(n+1 > n) by { assert(1 > 0); }
    assert(n+3 > n);
}
// item: R05.C1v write:assert-by
// An assertion-by block exports its assertion; local facts stay local.
// item: R05.C3v write:spinoff-prover
// #[verifier::spinoff_prover] gives this proof its own prover context.

// item: R05.H1v
// pair: R05.H1d
// uses: assert-by, spinoff-prover
#[verifier::spinoff_prover]
pub proof fn lemma_cat_assoc_lr(a: Re, b: Re, c: Re, s: Seq<char>)
    requires matches(Re::Cat(Box::new(Re::Cat(Box::new(a),Box::new(b))),Box::new(c)),s),
    ensures matches(Re::Cat(Box::new(a),Box::new(Re::Cat(Box::new(b),Box::new(c)))),s),
{ #[verifier::proof_note("R05.H1v")] assume(false);
}

// item: R05.H2v
// pair: R05.H2d
// uses: assert-by
pub proof fn lemma_cat_assoc_rl(a: Re, b: Re, c: Re, s: Seq<char>)
    requires matches(Re::Cat(Box::new(a),Box::new(Re::Cat(Box::new(b),Box::new(c)))),s),
    ensures matches(Re::Cat(Box::new(Re::Cat(Box::new(a),Box::new(b))),Box::new(c)),s),
{ #[verifier::proof_note("R05.H2v")] assume(false);
}

// item: R05.H3v
// pair: R05.H3d
pub proof fn lemma_star_one(a: Re, u: Seq<char>)
    requires matches(a,u),
    ensures matches(Re::Star(Box::new(a)),u),
{ #[verifier::proof_note("R05.H3v")] assume(false);
}

// item: R05.H4v
// pair: R05.H4d
// uses: assert-by, spinoff-prover
#[verifier::spinoff_prover]
pub proof fn lemma_star_concat(a: Re, u: Seq<char>, v: Seq<char>)
    requires matches(Re::Star(Box::new(a)),u), matches(Re::Star(Box::new(a)),v),
    ensures matches(Re::Star(Box::new(a)),u+v),
    decreases u.len(),
{
    #[verifier::proof_note("R05.H4v")] assume(false);
    let st = Re::Star(Box::new(a));
    let t = u+v;
    if u.len() == 0 {
    } else {
        let i = choose|i: int| 1 <= i <= u.len()
            && matches(a,#[trigger] u.subrange(0,i))
            && matches(st,u.subrange(i,u.len() as int));
        lemma_star_concat(a,u.subrange(i,u.len() as int),v);
        // Put facts here (and in the empty case) as bisection directs you.

    }
}
} // verus!
