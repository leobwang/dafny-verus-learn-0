/*! R04 — Specs as logic (Reference Solution).
Standalone R, A1 only. Six predictions precede the paper/audit/card material;
T1 is the closed-book first attempt before reading. Six holes in this half,
six in Dafny. Each hole H1-H5 has a prompt with a guiding question and two
hints below it. Done requires zero-hole gates, clean audits, unchanged
statements, firsttry's strict report and the written/agent/bench-card reviews.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;

verus! {

// Given: some substring s[i..j] of s, the empty ones included, matches r.
pub open spec fn occurs(r: Re, s: Seq<char>) -> bool {
    exists|i: int, j: int| 0 <= i <= j <= s.len() && matches(r, #[trigger] s.subrange(i, j))
}

// item: R04.T1v
// pair: R04.T1d
/// Closed book, before reading: give a witness and prove the claim.
pub proof fn lemma_some_word_matches()
    ensures
        exists|s: Seq<char>| matches(Re::Cat(Box::new(Re::Chr('o')), Box::new(Re::Star(Box::new(Re::Chr('k'))))), s),
{
    // @hole-begin R04.T1v
    let s = seq!['o'];
    let a = Re::Chr('o');
    let b = Re::Star(Box::new(Re::Chr('k')));
    assert(s.subrange(0, 1) =~= seq!['o']);
    assert(s.subrange(1, 1) =~= Seq::<char>::empty());
    assert(matches(a, s.subrange(0, 1)));
    assert(matches(b, s.subrange(1, 1)));
    assert(matches(Re::Cat(Box::new(a), Box::new(b)), s));
    // @hole-end R04.T1v
}

// ===========================================================================
// Worked examples
// ===========================================================================

// item: R04.W1v
/// Introduce a universal claim: `assert forall ... implies ... by` fixes an
/// arbitrary s, with the antecedent in scope, and proves the conclusion.
pub proof fn lemma_eps_only_empty()
    ensures
        forall|s: Seq<char>| matches(Re::Eps, s) ==> s.len() == 0,
{
    assert forall|s: Seq<char>| matches(Re::Eps, s) implies s.len() == 0 by {
    }
}

// item: R04.W2v
/// Eliminate an existential: `choose` takes a split the premise guarantees,
/// with every conjunct of its definition, and reasons about it.
pub proof fn lemma_cat_chr_nonempty(b: Re, s: Seq<char>)
    requires
        matches(Re::Cat(Box::new(Re::Chr('x')), Box::new(b)), s),
    ensures
        s.len() >= 1,
{
    let i = choose|i: int|
        0 <= i <= s.len() && matches(Re::Chr('x'), #[trigger] s.subrange(0, i)) && matches(
            b,
            s.subrange(i, s.len() as int),
        );
    assert(s.subrange(0, i).len() == 1);
}

// ===========================================================================
// Cards
// ===========================================================================

// item: R04.C1v write:forall-intro
// The given forall proof introduces an arbitrary s, not a chosen sample.
// EXPECT: card-c1v.rs.specimen fails: its claim does not hold for every s.
// item: R04.C2v write:exists-elim
// The given choose retains all the existential witness's bounds and facts.
// EXPECT: card-c2v.rs.specimen fails: no premise guarantees its witness.
// item: R04.C4v recognise:assume
// Recognise assume in the sealed audit drill, after recording P5d.

// ===========================================================================
// Holes
// ===========================================================================

// item: R04.H1v
// pair: R04.H1d
/// **H1.** A positive witness: prove that `Cat(Chr('a'), Star(Chr('b')))`
/// matches the whole string "abb". Which split of "abb" does the `Cat` need,
/// how many chunks does the `Star` take from the rest, and which `matches`
/// terms must you mention for Verus to unfold them?
pub proof fn lemma_witness_abb()
    ensures
        matches(Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Chr('b'))))), seq!['a', 'b', 'b']),
{
    // @hole-begin R04.H1v
    let a = Re::Chr('a');
    let b = Re::Chr('b');
    let star = Re::Star(Box::new(b));
    let u = seq!['b'];
    let t = seq!['b', 'b'];
    let s = seq!['a', 'b', 'b'];
    assert(u.subrange(0, 1) =~= seq!['b']);
    assert(u.subrange(1, 1) =~= Seq::<char>::empty());
    assert(matches(b, u.subrange(0, 1)));
    assert(matches(star, u.subrange(1, 1)));
    assert(matches(star, u));
    assert(t.subrange(0, 1) =~= seq!['b']);
    assert(t.subrange(1, 2) =~= u);
    assert(matches(Re::Chr('b'), t.subrange(0, 1)));
    assert(matches(star, t.subrange(1, t.len() as int)));
    assert(matches(star, t));
    assert(s.subrange(0, 1) =~= seq!['a']);
    assert(s.subrange(1, 3) =~= t);
    assert(matches(a, s.subrange(0, 1)));
    assert(matches(star, s.subrange(1, 3)));
    // @hole-end R04.H1v
}
// Hint(1): a Star match on a non-empty string is one non-empty chunk and a
//    Star match of the rest; build it from the shortest rest upwards.
// Hint(2): Verus unfolds a `matches` term only where it is mentioned: assert
//    each side's match at each split, the way chapter §2.3's witness does.

// item: R04.H2v
// uses: forall-intro, exists-elim
// pair: R04.H2d
/// **H2.** A negative claim about every match: no string that
/// `Cat(Chr('x'), Cat(Chr('y'), Star(Chr('z'))))` matches has 'x' in second
/// place. Prove it for an arbitrary match with `assert forall ... implies ...
/// by` (W1), and use the match through the splits it guarantees (W2). Which
/// two splits does a match supply, and what does each `Chr` side force?
pub proof fn lemma_no_x_in_second_place()
    ensures
        forall|s: Seq<char>| matches(Re::Cat(Box::new(Re::Chr('x')), Box::new(Re::Cat(Box::new(Re::Chr('y')), Box::new(Re::Star(Box::new(Re::Chr('z'))))))), s) ==> s.len() >= 2 && s[1] != 'x',
{
    // @hole-begin R04.H2v
    let r = Re::Cat(Box::new(Re::Chr('x')), Box::new(Re::Cat(Box::new(Re::Chr('y')), Box::new(Re::Star(Box::new(Re::Chr('z')))))));
    let yz = Re::Cat(Box::new(Re::Chr('y')), Box::new(Re::Star(Box::new(Re::Chr('z')))));
    assert forall|s: Seq<char>| matches(r, s) implies s.len() >= 2 && s[1] != 'x' by {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(Re::Chr('x'), #[trigger] s.subrange(0, i)) && matches(
                yz,
                s.subrange(i, s.len() as int),
            );
        let t = s.subrange(i, s.len() as int);
        let j = choose|j: int|
            0 <= j <= t.len() && matches(Re::Chr('y'), #[trigger] t.subrange(0, j)) && matches(
                Re::Star(Box::new(Re::Chr('z'))),
                t.subrange(j, t.len() as int),
            );
        assert(s.subrange(0, i).len() == 1);
        assert(i == 1);
        assert(t.subrange(0, j).len() == 1);
        assert(j == 1);
        assert(t.subrange(0, j)[0] == 'y');
        assert(t[0] == t.subrange(0, j)[0]);
        assert(s[1] == t[0]);
    }
    // @hole-end R04.H2v
}
// Hint(1): `assert forall|s: Seq<char>| <the match> implies <the claim> by
//    { ... }` fixes one arbitrary match; the rest is about that `s`.
// Hint(2): take the outer split with `choose`, then the split of its suffix;
//    each `Chr` side pins one character.

// item: R04.H3v
// uses: forall-intro, exists-elim
// pair: R04.H3d
/// **H3.** Anchoring: a whole-string match of `Cat(Cat(Chr('a'),
/// Star(Chr('b'))), Chr('c'))` begins with 'a' and ends with 'c'; an
/// occurrence would pin neither end. Prove it for every matching string, from
/// the splits a match guarantees (W2). Which split pins the last character,
/// and which pins the first?
pub proof fn lemma_witness_anchored()
    ensures
        forall|s: Seq<char>| matches(Re::Cat(Box::new(Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Chr('b')))))), Box::new(Re::Chr('c'))), s) ==> s.len() >= 2 && s[0] == 'a' && s[s.len() - 1] == 'c',
{
    // @hole-begin R04.H3v
    let r = Re::Cat(Box::new(Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Chr('b')))))), Box::new(Re::Chr('c')));
    let ab = Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Chr('b')))));
    assert forall|s: Seq<char>| matches(r, s) implies s.len() >= 2 && s[0] == 'a' && s[s.len() - 1] == 'c' by {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(ab, #[trigger] s.subrange(0, i)) && matches(
                Re::Chr('c'),
                s.subrange(i, s.len() as int),
            );
        let u = s.subrange(0, i);
        let k = choose|k: int|
            0 <= k <= u.len() && matches(Re::Chr('a'), #[trigger] u.subrange(0, k)) && matches(
                Re::Star(Box::new(Re::Chr('b'))),
                u.subrange(k, u.len() as int),
            );
        assert(s.subrange(i, s.len() as int).len() == 1);
        assert(s.len() == i + 1);
        assert(s[s.len() - 1] == s.subrange(i, s.len() as int)[0]);
        assert(u.subrange(0, k).len() == 1);
        assert(k == 1);
        assert(i >= 1);
        assert(s[0] == u[0]);
        assert(u[0] == u.subrange(0, k)[0]);
    }
    // @hole-end R04.H3v
}
// Hint(1): the outer split's right side is `Chr('c')`, which matches one
//    string only; the left side is itself a `Cat`, whose split you take next.
// Hint(2): W2 takes a split out of a premise with `choose`; here the premise
//    is the antecedent of `assert forall ... implies ... by` (W1).

// item: R04.H4v
// pair: R04.H4d
/// **H4.** From prose: `prefix_match(r, s)` is true exactly when some prefix
/// of `s`, the empty prefix included, matches `r`. Replace the `uninterp`
/// declaration by an `open spec fn` with a body, then uncomment the three
/// checks below; their proofs are given and verify only with an adequate
/// definition. Which bounds may the prefix's end take, and which its start?
pub open spec fn prefix_match(r: Re, s: Seq<char>) -> bool {
    exists|i: int| 0 <= i <= s.len() && matches(r, #[trigger] s.subrange(0, i))
}
// Hint(1): `occurs` above chooses both ends of a substring; a prefix fixes one.
// Hint(2): the empty prefix is `s.subrange(0, 0)`, so the end's lower bound
//    decides the third check.
// cfree: { false }
// cfree: { true }
// Reference checks (enabled):
// reference-only: enabled supplied check
proof fn prefix_positive() {
    let s = seq!['a', 'b'];
    assert(s.subrange(0, 1) =~= seq!['a']);
    assert(prefix_match(Re::Chr('a'), s));
}
// reference-only: enabled supplied check
proof fn prefix_negative() {
    let s = seq!['a', 'b'];
    assert forall|i: int| 0 <= i <= s.len() implies !matches(Re::Chr('b'), #[trigger] s.subrange(0, i)) by {
        if i == 0 {
            assert(s.subrange(0, i) =~= Seq::<char>::empty());
        } else if i == 1 {
            assert(s.subrange(0, i) =~= seq!['a']);
        } else {
            assert(s.subrange(0, i) =~= s);
        }
    }
    assert(!prefix_match(Re::Chr('b'), s));
}
// reference-only: enabled supplied check
proof fn prefix_empty(s: Seq<char>) {
    assert(s.subrange(0, 0) =~= Seq::<char>::empty());
    assert(prefix_match(Re::Eps, s));
}

// item: R04.H5v
// pair: R04.H5d
/// **H5.** A mutant-kill witness: a mutant `find` returns `nullable(r)`
/// instead of `occurs(r, s)`. Prove that some regex and string tell the two
/// apart. Which regex is not nullable yet occurs in a string, and which facts
/// make each side's value known?
pub proof fn lemma_mutant_killed()
    ensures
        exists|r: Re, s: Seq<char>| nullable(r) != occurs(r, s),
{
    // @hole-begin R04.H5v
    let r = Re::Chr('a');
    let s = seq!['a'];
    assert(s.subrange(0, 1) =~= s);
    assert(matches(r, s.subrange(0, 1)));
    assert(occurs(r, s));
    assert(!nullable(r));
    // @hole-end R04.H5v
}
// Hint(1): a single character is the smallest regex that is not nullable.
// Hint(2): `occurs` is an existential: name its two indices by a subrange
//    fact, and mention the inner `matches` term.

} // verus!
