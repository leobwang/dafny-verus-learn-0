/*! R05 — No goal state (Reference Solution).
Standalone R, layer A1 only. Do not import earlier learner proofs or A1b.
Four predictions first: commit P1d/P2v in their specimens and P3dv/P4dv in
slots/R05.slots; record scripts/firsttry.sh R05 --check before enabling them.
This file has four holes. The paired crate has four; variance.py has two.
Each hole has a prompt with a guiding question and two hints below it.
For H4 keep the given branch, choice, recursive call and measure: add facts.
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

// item: R05.C1v write:assert-by
// An assertion-by block exports its assertion; local facts stay local.
// EXPECT: card-c1v.rs.specimen fails inside its by block.
// item: R05.C3v write:spinoff-prover
// #[verifier::spinoff_prover] gives this proof its own prover context.
// EXPECT: card-c3v.rs.specimen names the one false assertion of two.

// ===========================================================================
// Holes
// ===========================================================================

// item: R05.H1v
// pair: R05.H1d
// uses: assert-by, spinoff-prover
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
    // @hole-begin R05.H1v
    let ab = Re::Cat(Box::new(a), Box::new(b));
    let bc = Re::Cat(Box::new(b), Box::new(c));
    let i = choose|i: int|
        0 <= i <= s.len() && matches(ab, #[trigger] s.subrange(0, i)) && matches(
            c,
            s.subrange(i, s.len() as int),
        );
    let u = s.subrange(0, i);
    let k = choose|k: int|
        0 <= k <= u.len() && matches(a, #[trigger] u.subrange(0, k)) && matches(
            b,
            u.subrange(k, u.len() as int),
        );
    let v = s.subrange(k, s.len() as int);
    assert(u.subrange(0, k) =~= s.subrange(0, k)) by {
    }
    assert(u.subrange(k, u.len() as int) =~= v.subrange(0, i - k));
    assert(v.subrange(i - k, v.len() as int) =~= s.subrange(i, s.len() as int));
    assert(matches(bc, v));
    // @hole-end R05.H1v
}
// Hint(1): take the outer split with `choose` (R04 §2.2), then the inner split
//    of its prefix; write the two witnesses down before any assertion.
// Hint(2): every subrange fact relates a subrange of a subrange to a subrange
//    of `s` (the slice chain of §1.2); assert them with `=~=`, one per line.

// item: R05.H2v
// pair: R05.H2d
// uses: assert-by
/// **H2.** The other direction: a match of `Cat(a, Cat(b, c))` is a match of
/// `Cat(Cat(a, b), c)`. Which prefix of `s` does the goal's inner `Cat(a, b)`
/// receive, and which index of `v` corresponds to an index of `s`?
pub proof fn lemma_cat_assoc_rl(a: Re, b: Re, c: Re, s: Seq<char>)
    requires
        matches(Re::Cat(Box::new(a), Box::new(Re::Cat(Box::new(b), Box::new(c)))), s),
    ensures
        matches(Re::Cat(Box::new(Re::Cat(Box::new(a), Box::new(b))), Box::new(c)), s),
{
    // @hole-begin R05.H2v
    let ab = Re::Cat(Box::new(a), Box::new(b));
    let bc = Re::Cat(Box::new(b), Box::new(c));
    let k = choose|k: int|
        0 <= k <= s.len() && matches(a, #[trigger] s.subrange(0, k)) && matches(
            bc,
            s.subrange(k, s.len() as int),
        );
    let v = s.subrange(k, s.len() as int);
    let j = choose|j: int|
        0 <= j <= v.len() && matches(b, #[trigger] v.subrange(0, j)) && matches(
            c,
            v.subrange(j, v.len() as int),
        );
    let u = s.subrange(0, k + j);
    assert(u.subrange(0, k) =~= s.subrange(0, k)) by {
    }
    assert(u.subrange(k, u.len() as int) =~= v.subrange(0, j));
    assert(v.subrange(j, v.len() as int) =~= s.subrange(k + j, s.len() as int));
    assert(matches(ab, u));
    // @hole-end R05.H2v
}
// Hint(1): the mirror of H1: outer split first, then the split of its suffix.
// Hint(2): an index `j` of `v` is the index `k + j` of `s`; state each
//    subrange equality that uses this shift.

// item: R05.H3v
// pair: R05.H3d
/// **H3.** One match is a star match: if `a` matches `u`, `Star(a)` does. How
/// many chunks does the star take, and which `matches` term must you mention
/// for the empty rest?
pub proof fn lemma_star_one(a: Re, u: Seq<char>)
    requires
        matches(a, u),
    ensures
        matches(Re::Star(Box::new(a)), u),
{
    // @hole-begin R05.H3v
    if u.len() > 0 {
        assert(u.subrange(0, u.len() as int) =~= u);
        assert(u.subrange(u.len() as int, u.len() as int) =~= Seq::<char>::empty());
        assert(matches(Re::Star(Box::new(a)), Seq::<char>::empty()));
    }
    // @hole-end R05.H3v
}
// Hint(1): the empty sequence is a star match by definition; only a non-empty
//    `u` needs a witness.
// Hint(2): the whole of `u` is the first chunk; name the split at `u.len()`
//    by its two subranges, and mention the star match of the empty rest.

// item: R05.H4v
// pair: R05.H4d
// uses: assert-by, spinoff-prover
/// **H4.** Bisect and repair: two star matches concatenate. The case split,
/// the choice of the first chunk and the recursive call are given and must
/// stay; the facts the solver lacks are not. Run the function, read the
/// obligation it names, and add one fact at a time where the comments say.
/// Which facts connect `u + v` to the chunk and to the recursive call's
/// sequence?
#[verifier::spinoff_prover]
pub proof fn lemma_star_concat(a: Re, u: Seq<char>, v: Seq<char>)
    requires
        matches(Re::Star(Box::new(a)), u),
        matches(Re::Star(Box::new(a)), v),
    ensures
        matches(Re::Star(Box::new(a)), u + v),
    decreases u.len(),
{
    // @hole-begin R05.H4v
    assert(u.len() == 0 ==> u + v == v) by {
        assert(u.len() == 0 ==> u =~= Seq::<char>::empty());
    }
    // @hole-end R05.H4v
    let st = Re::Star(Box::new(a));
    let t = u + v;
    if u.len() == 0 {
    } else {
        let i = choose|i: int|
            1 <= i <= u.len() && matches(a, #[trigger] u.subrange(0, i)) && matches(
                st,
                u.subrange(i, u.len() as int),
            );
        lemma_star_concat(a, u.subrange(i, u.len() as int), v);
        // Put facts here (and in the empty case) as bisection directs you.
        // @hole-begin R05.H4v
        assert(t.subrange(0, i) =~= u.subrange(0, i)) by {
        }
        assert(t.subrange(i, t.len() as int) =~= u.subrange(i, u.len() as int) + v);
        // @hole-end R05.H4v
    }
}
// Hint(1): bisect: add `assert(false);` at a point to learn whether the
//    failure is before or after it, then replace it with the fact you need.
// Hint(2): the first chunk of `u + v` is the first chunk of `u`, and the rest
//    is the recursive call's sequence; both are `=~=` facts about `t`.

} // verus!
