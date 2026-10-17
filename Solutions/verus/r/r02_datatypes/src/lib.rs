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
    requires star_count_spec(*r) < 1000,
    ensures n == star_count_spec(*r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => { let x = star_count(a); let y = star_count(b); x + y },
        Re::Cat(a, b) => { let x = star_count(a); let y = star_count(b); x + y },
        Re::Star(a) => { let x = star_count(a); 1 + x },
        _ => 0,
    }
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

// item: R02.H1v
// uses: datatype-match, exists-witness
// pair: R02.H1d
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

// item: R02.H2v
// uses: datatype-match
// pair: R02.H2d
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

// item: R02.H3v
// uses: datatype-match
// pair: R02.H3d
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
        Re::Star(a) => {
            lemma_nullable_backwards(*a);
        },
        _ => {},
    }
    // @hole-end R02.H3v
}

// item: R02.H4v
// uses: exists-witness
// pair: R02.H4d
pub proof fn lemma_cat_eps_left(r: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Eps), Box::new(r)), s) <==> matches(r, s),
{
    // @hole-begin R02.H4v
    let e = Re::Cat(Box::new(Re::Eps), Box::new(r));
    assert(s.subrange(0, s.len() as int) =~= s);
    if matches(r, s) {
        assert(s.subrange(0, 0) =~= Seq::<char>::empty());
        assert(matches(Re::Eps, s.subrange(0, 0)));
    }
    if matches(e, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(Re::Eps, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            );
        assert(s.subrange(0, i).len() == 0);
    }
    // @hole-end R02.H4v
}

// item: R02.H5v
// uses: datatype-match, decreases
// pair: R02.H5d
pub fn is_void(r: &Re) -> (b: bool)
    ensures b == void_spec(*r),
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


// item: R02.C1v write:datatype-match
// EXPECT: card-c1v.rs.specimen is rejected for missing match arms.
pub open spec fn regex_outer_tag(r: Re) -> nat {
    match r {
        Re::Empty => 0, Re::Eps => 1, Re::Chr(_) => 2,
        Re::Alt(_, _) => 3, Re::Cat(_, _) => 4, Re::Star(_) => 5,
    }
}

// item: R02.C2v write:decreases
// EXPECT: card-c2v.rs.specimen fails its strict-decrease obligation.
pub open spec fn outer_stars(r: Re) -> nat
    decreases r,
{ match r { Re::Star(a) => 1 + outer_stars(*a), _ => 0, } }

// item: R02.C3v write:exists-witness
// EXPECT: card-c3v.rs.specimen fails: existence needs an actual candidate.
pub proof fn lemma_marked_position(s: Seq<char>, i: int)
    requires 0 <= i < s.len() && s[i] == '#',
    ensures exists|k: int| 0 <= k < s.len() && s[k] == '#',
{ assert(0 <= i < s.len() && s[i] == '#'); }

// item: R02.C6v recognise:box
/// Box owns one recursive child; the borrowed match in star_count binds a
/// reference to the box. Dereferencing a value in a spec does not copy it in exec.
pub fn boxed_regex(r: Re) -> (b: Box<Re>)
    ensures *b == r,
{ Box::new(r) }

} // verus!

#[test]
fn regex_sample_test() { assert!(!rg_re_a1::is_nullable(&rg_re_a1::Re::Chr('z'))); }
