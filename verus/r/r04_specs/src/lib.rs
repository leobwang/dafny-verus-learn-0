/*! R04 — Specs as logic (exercises).
Standalone R, A1 only. Six predictions precede the paper/audit/card material;
T1 is the closed-book first attempt before reading. Six holes in this half,
six in Dafny. Done requires zero-hole gates, clean audits, unchanged statements,
firsttry's strict report and the written/API-agent/bench-card reviews.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
verus! {
pub open spec fn occurs(r: Re, s: Seq<char>) -> bool {
    exists|i: int,j: int| 0 <= i <= j <= s.len() && matches(r,#[trigger] s.subrange(i,j))
}

// item: R04.T1v
// pair: R04.T1d
pub proof fn lemma_some_word_matches()
    ensures exists|s: Seq<char>| matches(Re::Cat(Box::new(Re::Chr('o')),Box::new(Re::Star(Box::new(Re::Chr('k'))))),s),
{ #[verifier::proof_note("R04.T1v")] assume(false); }

// item: R04.W1v
pub proof fn lemma_eps_only_empty()
    ensures forall|s: Seq<char>| matches(Re::Eps,s) ==> s.len() == 0,
{
    assert forall|s: Seq<char>| matches(Re::Eps,s) implies s.len() == 0 by { }
}
// item: R04.W2v
pub proof fn lemma_cat_chr_nonempty(b: Re, s: Seq<char>)
    requires matches(Re::Cat(Box::new(Re::Chr('x')),Box::new(b)),s),
    ensures s.len() >= 1,
{
    let i=choose|i: int| 0 <= i <= s.len() && matches(Re::Chr('x'),#[trigger] s.subrange(0,i))
        && matches(b,s.subrange(i,s.len() as int));
    assert(s.subrange(0,i).len() == 1);
}
// item: R04.C1v write:forall-intro
// The given forall proof introduces an arbitrary s, not a chosen sample.
// item: R04.C2v write:exists-elim
// The given choose retains all the existential witness's bounds and facts.
// item: R04.C4v recognise:assume
// Recognise assume in the sealed audit drill, after recording P5d.

// item: R04.H1v
// pair: R04.H1d
pub proof fn lemma_witness_abb()
    ensures matches(Re::Cat(Box::new(Re::Chr('a')),Box::new(Re::Star(Box::new(Re::Chr('b'))))),seq!['a','b','b']),
{ #[verifier::proof_note("R04.H1v")] assume(false); }

// item: R04.H2v
// uses: forall-intro, exists-elim
// pair: R04.H2d
pub proof fn lemma_witness_not_ba()
    ensures !matches(Re::Cat(Box::new(Re::Chr('a')),Box::new(Re::Star(Box::new(Re::Chr('b'))))),seq!['b','a']),
{ #[verifier::proof_note("R04.H2v")] assume(false); }

// item: R04.H3v
// uses: forall-intro, exists-elim
// pair: R04.H3d
pub proof fn lemma_witness_anchored()
    ensures !matches(Re::Chr('a'),seq!['b','a']) &&
        matches(Re::Cat(Box::new(Re::Star(Box::new(Re::Chr('b')))),Box::new(Re::Chr('a'))),seq!['b','a']),
{ #[verifier::proof_note("R04.H3v")] assume(false); }

// item: R04.H4v
// pair: R04.H4d
/// FROM PROSE: true exactly when some prefix, including the empty prefix,
/// matches r. Supply the definition and enable all three unchanged checks.
pub uninterp spec fn prefix_match(r: Re,s: Seq<char>) -> bool;
// Uncomment as you go:
// proof fn prefix_positive() { let s=seq!['a','b']; assert(s.subrange(0,1) =~= seq!['a']); assert(prefix_match(Re::Chr('a'),s)); }
// proof fn prefix_negative() { let s=seq!['a','b']; assert forall|i: int| 0 <= i <= s.len() implies !matches(Re::Chr('b'),#[trigger] s.subrange(0,i)) by { if i == 0 { assert(s.subrange(0,i) =~= Seq::<char>::empty()); } else if i == 1 { assert(s.subrange(0,i) =~= seq!['a']); } else { assert(s.subrange(0,i) =~= s); } } assert(!prefix_match(Re::Chr('b'),s)); }
// proof fn prefix_empty(s: Seq<char>) { assert(s.subrange(0,0) =~= Seq::<char>::empty()); assert(prefix_match(Re::Eps,s)); }

// item: R04.H5v
// pair: R04.H5d
pub proof fn lemma_mutant_killed()
    ensures exists|r: Re,s: Seq<char>| nullable(r) != occurs(r,s),
{ #[verifier::proof_note("R04.H5v")] assume(false); }
}
