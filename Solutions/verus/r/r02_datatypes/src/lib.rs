/*!
# R02 — Datatypes and recursion (Reference Solution)

Standalone R track. Import only the frozen A1 definitions; no earlier learner
file or later A1b fact is needed. The paired exercise is dafny/R/R02_Datatypes/core/R02_Datatypes.dfy.

Before reading the worked examples, attempt T1 closed book. Fill the five
predictions in slots/R02.slots, specimens/R02/P1d.dfy.specimen,
specimens/R02/P2v.rs.specimen and dafny/checks/R02_checks.dfy. Record the first
attempt using scripts/firsttry.sh R02 --check before running their scenarios.
Five typed holes ship in this language, ten across the pair. T1 starts empty
and has a commented use-site check: it is a separate code test-out.

File order: the test-out, the worked examples (W1, W2), the cards (C1 to C3,
C6), the given void_spec, the holes (H1 to H5) and H5's given client. Each
hole comes after the cards its `uses:` line names; chapter §2 teaches the
`choose` that H4 needs.

Done: every unit gates with zero tool-counted holes, vaudit is clean,
specfreeze --check R02 passes, and firsttry's strict report is OK. Preserve
given contracts and implementations. /tutor R02 is available after an attempt.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
verus! {

// item: R02.T1v
// uses: datatype-match, decreases
// pair: R02.T1d
/// Closed book: define pub open spec fn chr_count(r: Re) -> nat, counting Chr
/// leaves structurally. Write it here, uncomment its check, record the first try.
// reference-only: completed closed-book definition
pub open spec fn chr_count(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Chr(_) => 1,
        Re::Alt(a, b) => chr_count(*a) + chr_count(*b),
        Re::Cat(a, b) => chr_count(*a) + chr_count(*b),
        Re::Star(a) => chr_count(*a),
        _ => 0,
    }
}
// Reference checks (enabled):
// reference-only: enabled shipped check
proof fn chr_count_check() { assert(chr_count(Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Alt(Box::new(Re::Chr('b')), Box::new(Re::Eps))))))) == 2) by (compute_only); } // did: compute_only evaluates the finite constructor expression against the recursive count definition.

// =============================================================================
// Worked examples
// =============================================================================

// item: R02.W1v
/// Expose a concrete split witness and both slice facts.
pub proof fn lemma_matches_ab()
    ensures matches(Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Chr('b'))), seq!['a', 'b']),
{
    let s = seq!['a', 'b'];
    assert(s.subrange(0, 1) =~= seq!['a']);
    assert(s.subrange(1, s.len() as int) =~= seq!['b']);
    assert(matches(Re::Chr('a'), s.subrange(0, 1)));
    assert(matches(Re::Chr('b'), s.subrange(1, s.len() as int)));
    assert(exists|i: int| 0 <= i <= s.len()
        && matches(Re::Chr('a'), #[trigger] s.subrange(0, i))
        && matches(Re::Chr('b'), s.subrange(i, s.len() as int)));
}

// item: R02.W2v
/// A recursive exec fn over a borrowed tree, tied to its spec fn by its
/// postcondition; the bound keeps the u64 additions in range.
pub open spec fn star_count_spec(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Alt(a, b) => star_count_spec(*a) + star_count_spec(*b),
        Re::Cat(a, b) => star_count_spec(*a) + star_count_spec(*b),
        Re::Star(a) => 1 + star_count_spec(*a),
        _ => 0,
    }
}

pub fn star_count(r: &Re) -> (n: u64)
    requires
        star_count_spec(*r) < 1000,
    ensures
        n == star_count_spec(*r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            let x = star_count(a);
            let y = star_count(b);
            x + y
        },
        Re::Cat(a, b) => {
            let x = star_count(a);
            let y = star_count(b);
            x + y
        },
        Re::Star(a) => {
            let x = star_count(a);
            1 + x
        },
        _ => 0,
    }
}

// =============================================================================
// Cards
// =============================================================================

// item: R02.C1v write:datatype-match
// EXPECT: card-c1v.rs.specimen is rejected for missing match arms.
pub open spec fn regex_outer_tag(r: Re) -> nat {
    match r {
        Re::Empty => 0,
        Re::Eps => 1,
        Re::Chr(_) => 2,
        Re::Alt(_, _) => 3,
        Re::Cat(_, _) => 4,
        Re::Star(_) => 5,
    }
}

// item: R02.C2v write:decreases
// EXPECT: card-c2v.rs.specimen fails its strict-decrease obligation.
pub open spec fn outer_stars(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Star(a) => 1 + outer_stars(*a),
        _ => 0,
    }
}

// item: R02.C3v write:exists-witness
// EXPECT: card-c3v.rs.specimen fails: existence needs an actual candidate.
pub proof fn lemma_marked_position(s: Seq<char>, i: int)
    requires
        0 <= i < s.len() && s[i] == '#',
    ensures
        exists|k: int| 0 <= k < s.len() && s[k] == '#',
{
    assert(0 <= i < s.len() && s[i] == '#');
}

// item: R02.C6v recognise:box
/// Box owns one recursive child; the borrowed match in star_count binds a
/// reference to the box. Dereferencing a value in a spec does not copy it in exec.
pub fn boxed_regex(r: Re) -> (b: Box<Re>)
    ensures
        *b == r,
{
    Box::new(r)
}

/// Given structural specification for H5: no string is matched.
pub open spec fn void_spec(r: Re) -> bool
    decreases r,
{
    match r {
        Re::Empty => true,
        Re::Eps => false,
        Re::Chr(_) => false,
        Re::Alt(a, b) => void_spec(*a) && void_spec(*b),
        Re::Cat(a, b) => void_spec(*a) || void_spec(*b),
        Re::Star(_) => false,
    }
}

// =============================================================================
// Holes
// =============================================================================

// item: R02.H1v
// uses: datatype-match, exists-witness
// pair: R02.H1d
/// **H1.** The structural test `nullable` agrees with the semantics on the
/// empty string. Prove it by structural induction: a call of this lemma on a
/// child is that child's hypothesis (Verus never inducts for you). Which
/// constructors need their children's hypotheses, and which split of the
/// empty string does `Cat` need?
pub proof fn lemma_nullable_correct(r: Re)
    ensures
        nullable(r) <==> matches(r, Seq::<char>::empty()),
    decreases r,
{
    // @hole-begin R02.H1v
    let e = Seq::<char>::empty();
    assert(e.subrange(0, 0) =~= e);
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        _ => {},
    }
    // @hole-end R02.H1v
}
// Hint(1): match on r; the leaves and Star follow from the two definitions alone.
// Hint(2): the empty sequence has one split; the trigger of `matches`' Cat case is
//    `s.subrange(0, i)`, so state that subrange's value with `=~=`, as W1 does.

// item: R02.H2v
// uses: datatype-match
// pair: R02.H2d
/// **H2.** Reading a regex backwards keeps its node count, and every regex
/// has at least one node. Which cases of `backwards` rebuild a node with
/// recursive children, and what must be known about those children before
/// the counts can be compared?
pub proof fn lemma_node_count_backwards(r: Re)
    ensures
        node_count(r) >= 1 && node_count(backwards(r)) == node_count(r),
    decreases r,
{
    // @hole-begin R02.H2v
    match r {
        Re::Alt(a, b) => {
            lemma_node_count_backwards(*a);
            lemma_node_count_backwards(*b);
        },
        Re::Cat(a, b) => {
            lemma_node_count_backwards(*a);
            lemma_node_count_backwards(*b);
        },
        Re::Star(a) => {
            lemma_node_count_backwards(*a);
        },
        _ => {},
    }
    // @hole-end R02.H2v
}
// Hint(1): one arm per recursive constructor; `_ => {}` covers the leaves.
// Hint(2): the children are boxed: the hypothesis for a child is a call on `*a`.

// item: R02.H3v
// uses: datatype-match
// pair: R02.H3d
/// **H3.** Reading a regex backwards keeps its nullability. In which case
/// does `backwards` reorder the children, and why does `nullable` not notice
/// the order?
pub proof fn lemma_nullable_backwards(r: Re)
    ensures
        nullable(backwards(r)) == nullable(r),
    decreases r,
{
    // @hole-begin R02.H3v
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_backwards(*a);
            lemma_nullable_backwards(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_backwards(*a);
            lemma_nullable_backwards(*b);
        },
        _ => {},
    }
    // @hole-end R02.H3v
}
// Hint(1): the skeleton of H2 works here too.
// Hint(2): `nullable` of a `Cat` is a conjunction of the children's values.

// item: R02.H4v
// uses: exists-witness
// pair: R02.H4d
/// **H4.** Putting `Eps` in front changes no language. Each direction is
/// about the existential over split points in `matches`' `Cat` case: which
/// split proves the left side from `matches(r, s)`, and what does `Eps` force
/// about a split you take out of a match of `Cat(Eps, r)`?
pub proof fn lemma_cat_eps_left(r: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Eps), Box::new(r)), s) <==> matches(r, s),
{
    // @hole-begin R02.H4v
    let e = Re::Cat(Box::new(Re::Eps), Box::new(r));
    assert(s.subrange(0, 0) =~= Seq::<char>::empty());
    assert(s.subrange(0, s.len() as int) =~= s);
    if matches(e, s) {
        let i = choose|i: int|
            0 <= i <= s.len()
            && matches(Re::Eps, #[trigger] s.subrange(0, i))
            && matches(r, s.subrange(i, s.len() as int));
        assert(s.subrange(0, i).len() == 0);
    }
    // @hole-end R02.H4v
}
// Hint(1): one direction introduces the existential (name the split); the
//    other eliminates it (take the split out and read what `Eps` says about it).
// Hint(2): chapter §2.3's `choose` takes a split out of an existential; both
//    directions need the subranges at 0 stated with `=~=`.

// item: R02.H5v
// uses: datatype-match, decreases
// pair: R02.H5d
/// **H5.** Implement `is_void`, an executable emptiness test: it returns
/// `void_spec(*r)`, computed by recursion over the borrowed tree. Remove
/// `external_body`, write the body, and add the termination measure yourself.
/// Which constructors are void on their own, and how do `Alt` and `Cat`
/// combine their children's answers?
pub fn is_void(r: &Re) -> (b: bool)
    ensures
        b == void_spec(*r),
    decreases r,
{
    // @impl-begin R02.H5v
    match r {
        Re::Empty => true,
        Re::Eps => false,
        Re::Chr(_) => false,
        Re::Alt(a, b) => is_void(a) && is_void(b),
        Re::Cat(a, b) => is_void(a) || is_void(b),
        Re::Star(_) => false,
    }
    // @impl-end R02.H5v
}
// Hint(1): W2's `star_count` has the shape: match on `r`, one call per boxed child.
// Hint(2): the given `void_spec` is the table to implement; a recursive exec fn
//    needs its own `decreases`, as `star_count` has.

/// Given (not an item): H5's use-site check. It verifies against is_void's
/// contract now and must keep verifying once your body replaces the hole.
fn is_void_client() {
    let dead = Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Empty));
    let b = is_void(&dead);
    // void_spec unfolds one level per step: name the child's value first.
    assert(void_spec(Re::Empty));
    assert(b);
    let live = Re::Star(Box::new(Re::Empty));
    let c = is_void(&live);
    assert(!c);
}

} // verus!

#[test]
fn regex_sample_test() {
    assert!(!rg_re_a1::is_nullable(&rg_re_a1::Re::Chr('z')));
}
