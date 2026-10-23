/*! R05 — No goal state (Exercises).
Standalone R, layer A1 only. Do not import earlier learner proofs or A1b.
Four predictions first: commit P1d/P2v in their specimens and P3dv/P4dv in
slots/R05.slots; record scripts/firsttry.sh R05 --check before enabling them.
This file has four holes. The paired crate has four; variance.py has two.
Each hole has a prompt with a guiding question and two hints below it.
For H4 keep the given branch, choice and measure: add the call and facts.
Done: all native/Python gates, audit, freeze, strict firsttry, variance and
LATENCY logs, written work, OBLIGATION LOG, fourth bench card and viva.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;

verus! {

// ===========================================================================
// Worked examples
// ===========================================================================

// item: R05.W1v
/// Bisection worked once: each assert states one fact, so a failure names
/// the first step the solver could not take.
pub proof fn lemma_slice_bridge(s: Seq<char>, i: int)
    requires
        0 <= i < s.len(),
    ensures
        s.subrange(i, s.len() as int) == seq![s[i]] + s.subrange(i + 1, s.len() as int),
{
    let tail = s.subrange(i, s.len() as int);
    assert(tail.len() > 0);
    assert(tail[0] == s[i]);
    assert(tail.drop_first() =~= s.subrange(i + 1, s.len() as int));
    assert(tail =~= seq![tail[0]] + tail.drop_first());
    assert(s.subrange(i, s.len() as int) == seq![s[i]] + s.subrange(i + 1, s.len() as int));
}

// item: R05.W2v
/// `assert ... by` proves its assertion from a local block whose facts stay
/// local; `#[verifier::spinoff_prover]` gives the function its own prover.
#[verifier::spinoff_prover]
pub proof fn lemma_scoped_arithmetic(n: int)
    requires
        n >= 0,
    ensures
        n + 3 > n,
{
    assert(n + 1 > n) by {
        assert(1 > 0);
    }
    assert(n + 3 > n);
}

// ===========================================================================
// Cards
// ===========================================================================

// item: R05.C1v recognise:assert-by
// An assertion-by block exports its assertion; local facts stay local.
// EXPECT: card-c1v.rs.specimen fails inside its by block.
// item: R05.C3v recognise:spinoff-prover
// #[verifier::spinoff_prover] gives this proof its own prover context.
// EXPECT: card-c3v.rs.specimen names the one false assertion of two.

// ===========================================================================
// Holes
// ===========================================================================

// item: R05.H1v
// pair: R05.H1d
/// **H1.** Concatenation re-associates left to right: a match of
/// `Cat(Cat(a, b), c)` is a match of `Cat(a, Cat(b, c))`. Take the two splits
/// the premise guarantees and build the one the goal needs. Which index splits
/// `s` for the goal's outer `Cat`, and which subranges of which sequences must
/// you prove equal for the inner `Cat(b, c)`?
#[verifier::spinoff_prover]
pub proof fn lemma_cat_assoc_lr(a: Re, b: Re, c: Re, s: Seq<char>)
    requires
        matches(Re::Cat(Box::new(Re::Cat(Box::new(a), Box::new(b))), Box::new(c)), s),
    ensures
        matches(Re::Cat(Box::new(a), Box::new(Re::Cat(Box::new(b), Box::new(c)))), s),
{
    #[verifier::proof_note("R05.H1v")] assume(false);  // HOLE
}
// Hint(1): take the outer split with `choose` (R04 §2.2), then the inner split
//    of its prefix; write the two witnesses down before any assertion.
// Hint(2): every subrange fact relates a subrange of a subrange to a subrange
//    of `s` (the slice chain of §1.2); assert them with `=~=`, one per line.

// item: R05.H2v
// pair: R05.H2d
/// **H2.** The other direction: a match of `Cat(a, Cat(b, c))` is a match of
/// `Cat(Cat(a, b), c)`. Which prefix of `s` does the goal's inner `Cat(a, b)`
/// receive, and which index of `v` corresponds to an index of `s`?
pub proof fn lemma_cat_assoc_rl(a: Re, b: Re, c: Re, s: Seq<char>)
    requires
        matches(Re::Cat(Box::new(a), Box::new(Re::Cat(Box::new(b), Box::new(c)))), s),
    ensures
        matches(Re::Cat(Box::new(Re::Cat(Box::new(a), Box::new(b))), Box::new(c)), s),
{
    #[verifier::proof_note("R05.H2v")] assume(false);  // HOLE
}
// Hint(1): the mirror of H1: outer split first, then the split of its suffix.
// Hint(2): an index `j` of `v` is the index `k + j` of `s`; state each
//    subrange equality that uses this shift.

// item: R05.H3v
// pair: R05.H3d
/// **H3.** One match is a star match, as often as you like: if `a` matches
/// `u`, then `Star(a)` matches `u + u + u`. Each chunk of the star is one copy
/// of `u`. Where does the first chunk end, which sequence is left after it,
/// and which `matches` terms must you mention for each rest?
pub proof fn lemma_star_thrice(a: Re, u: Seq<char>)
    requires
        matches(a, u),
    ensures
        matches(Re::Star(Box::new(a)), u + u + u),
{
    #[verifier::proof_note("R05.H3v")] assume(false);  // HOLE
}
// Hint(1): build the star from the back: the last copy of `u` is a star
//    match (one chunk and the empty rest), then two copies, then three.
// Hint(2): each step splits a sequence at `u.len()`; name its two subranges
//    with `=~=`, and mention the star match of the rest.

// item: R05.H4v
// pair: R05.H4d
/// **H4.** Bisect and repair: two star matches concatenate. The case split
/// and the choice of the first chunk are given and must stay; the induction
/// step and the facts the solver lacks are not. Run the function, read the
/// obligation it names, and add one line at a time where the comments say.
/// Which recursive call gives the rest of `u + v` its star match, and which
/// facts connect `t` to the chunk and to that call's sequence?
#[verifier::spinoff_prover]
pub proof fn lemma_star_concat(a: Re, u: Seq<char>, v: Seq<char>)
    requires
        matches(Re::Star(Box::new(a)), u),
        matches(Re::Star(Box::new(a)), v),
    ensures
        matches(Re::Star(Box::new(a)), u + v),
    decreases u.len(),
{
    #[verifier::proof_note("R05.H4v")] assume(false);
    let st = Re::Star(Box::new(a));
    let t = u + v;
    if u.len() == 0 {
    } else {
        let i = choose|i: int|
            1 <= i <= u.len() && matches(a, #[trigger] u.subrange(0, i)) && matches(
                st,
                u.subrange(i, u.len() as int),
            );
        // Put the recursive call and the facts here (and in the empty case)
        // as bisection directs you.

    }
}
// Hint(1): bisect: add `assert(false);` at a point to learn whether the
//    failure is before or after it, then replace it with the fact you need.
// Hint(2): the first chunk of `t` is the first chunk of `u`, and the rest is
//    `u.subrange(i, u.len() as int) + v`, a shorter case of the function itself
//    (`decreases u.len()`); call it, then state both `=~=` facts about `t`.

} // verus!
