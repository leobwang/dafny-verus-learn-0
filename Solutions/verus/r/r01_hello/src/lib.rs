//! R01 — Reference Solution (author-only).
//! Complete, silent twin with enabled checks and unchanged item order.
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {

pub open spec fn count_char(s: Seq<char>, c: char) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        (if s[0] == c { 1nat } else { 0nat }) + count_char(s.drop_first(), c)
    }
}

// R01.P1dv and R01.P2dv are in the Dafny prediction block; answers go in slots/R01.slots.
// R01.P4v and R01.P6v are prediction specimens. Do not run them before recording guesses.

// item: R01.T1v
// uses: ensures, assert, lemma-call
// pair: R01.T1d
/// Closed-book census: close both typed holes and keep the contracts. Record the first try.
pub proof fn lemma_count_char_pair(d: char, e: char, c: char)
    ensures
        count_char(seq![d, e], c) == (if d == c { 1nat } else { 0nat }) + (if e == c { 1nat } else { 0nat }),
{
    // @hole-begin R01.T1v
    assert(seq![d, e].drop_first() =~= seq![e]);
    assert(seq![e].drop_first() =~= Seq::<char>::empty());
    assert(count_char(Seq::<char>::empty(), c) == 0);
    assert(count_char(seq![e], c) == (if e == c { 1nat } else { 0nat }));
    // @hole-end R01.T1v
}

pub fn count_first_two(s: &Vec<char>, c: char) -> (n: u32)
    requires
        s.len() >= 2,
    ensures
        n == count_char(s@.subrange(0, 2), c),
{
    let a = if s[0] == c { 1u32 } else { 0u32 };
    let b = if s[1] == c { 1u32 } else { 0u32 };
    proof {
        assert(s@.subrange(0, 2) =~= seq![s@[0], s@[1]]);
        lemma_count_char_pair(s@[0], s@[1], c);
    }
    a + b
}
// Reference checks (enabled):
// reference-only: enabled shipped check
fn census_check() {
    let s = vec!['a', 'b'];
    proof {
        assert(s@.subrange(0, 2) =~= seq!['a', 'b']);
        lemma_count_char_pair('a', 'b', 'a');
    }
    let n = count_first_two(&s, 'a');
    assert(n == 1);
}

// item: R01.W1v
/// A first verified function: the non-empty-vector precondition makes the index legal.
pub fn last_char(s: &Vec<char>) -> (c: char)
    requires
        s.len() > 0,
    ensures
        c == s@[s.len() - 1],
{
    s[s.len() - 1]
}

// item: R01.W2v
/// Follow the recursive definition; state what the recursive proof call establishes.
pub proof fn lemma_count_char_bound(s: Seq<char>, c: char)
    ensures
        count_char(s, c) <= s.len(),
    decreases s.len(),
{
    if s.len() > 0 {
        assert(s.drop_first().len() == s.len() - 1);
        lemma_count_char_bound(s.drop_first(), c);
        assert(count_char(s.drop_first(), c) <= s.drop_first().len());
        assert(count_char(s, c) <= 1 + count_char(s.drop_first(), c));
    }
}

// item: R01.C1v write:ensures
// EXPECT: card-c1v.rs.specimen fails.
pub fn keep_char(c: char) -> (r: char)
    ensures
        r == c,
{
    c
}

// item: R01.C2v write:assert
// EXPECT: card-c2v.rs.specimen fails.
pub proof fn lemma_empty_prefix(s: Seq<char>)
    ensures
        Seq::<char>::empty() + s == s,
{
    assert(Seq::<char>::empty() + s =~= s);
}

// item: R01.C3v write:lemma-call
// EXPECT: card-c3v.rs.specimen fails.
pub proof fn lemma_count_within_length(s: Seq<char>, c: char)
    ensures
        count_char(s, c) <= s.len(),
{
    lemma_count_char_bound(s, c);
}

// Rosetta cards C4dv–C7dv are in the Dafny file beside the paired worked examples.

// ===========================================================================
// Holes
// ===========================================================================

// item: R01.H1v
// uses: ensures
// pair: R01.H1d
/// **H1.** Implement the midpoint of two ordered `u32` values, keeping both the
/// interval clause and the exact-average clause. Remove `external_body` and write
/// the body. Which operations does your body perform on `u32` values, and what
/// must be true of each result for every call the precondition admits?
pub fn midpoint(lo: u32, hi: u32) -> (m: u32)
    requires
        lo <= hi,
    ensures
        lo <= m <= hi,
        m as int == (lo as int + hi as int) / 2,
{
    // @impl-begin R01.H1v
    lo + (hi - lo) / 2
    // @impl-end R01.H1v
}
// Hint(1): Verus checks every executable `u32` operation for overflow, not only the result.
// Hint(2): the precondition `lo <= hi` is the one given fact the body can spend:
//    which subtraction does it make legal?
// Reference checks (enabled):
// reference-only: enabled shipped check
fn midpoint_check() {
    let m = midpoint(0xffff_fffe, 0xffff_ffff);
    assert(m == 0xffff_fffe);
}

// item: R01.H2v
// uses: assert, lemma-call
// pair: R01.H2d
/// **H2.** A character's count in a concatenation is the sum of its counts in the
/// two parts. Prove it by recursion on `s`, the way W2 recurses: Verus never
/// inducts for you, so each recursive call is yours. What is `s + t` once its
/// first element is dropped, and which call of this lemma then supplies the rest
/// of the sum?
pub proof fn lemma_count_char_append(s: Seq<char>, t: Seq<char>, c: char)
    ensures
        count_char(s + t, c) == count_char(s, c) + count_char(t, c),
    decreases s.len(),
{
    // @hole-begin R01.H2v
    if s.len() > 0 {
        assert((s + t).drop_first() =~= s.drop_first() + t);
        lemma_count_char_append(s.drop_first(), t, c);
    } else {
        assert(s + t =~= t);
    }
    // @hole-end R01.H2v
}
// Hint(1): split on whether `s` is empty; `count_char`'s definition does the same.
// Hint(2): a call of this lemma on a shorter `s` is the hypothesis (W2's call);
//    the verifier also needs the sequence equality, stated with `=~=`, that
//    connects `s + t` to that call.
// Reference checks (enabled):
// reference-only: enabled shipped check
proof fn append_check() {
    lemma_count_char_append(seq!['x'], seq!['y', 'x'], 'x');
}

// item: R01.H3v
// uses: requires
// pair: R01.H3d
/// **H3.** Keep the body and the result clause; write the `requires` clause that
/// makes `(a + b) / 2` verify while all three given callers below still verify,
/// then delete the labelled `assume`. Which operation of the body owes a range
/// fact, and which caller rejects a clause that bounds each argument on its own?
pub fn mean_of_two(a: u32, b: u32) -> (m: u32)
    // @hole-begin R01.H3v
    requires
        a as int + b as int <= u32::MAX,
    // @hole-end R01.H3v
    ensures
        m as int == (a as int + b as int) / 2,
{
    (a + b) / 2
}
// Hint(1): the failing obligation is the addition's; read its diagnostic first.
// Hint(2): run the three callers after each candidate clause: `mean_edge`
//    rejects any clause that is stronger than the addition needs.
fn mean_zero() {
    let m = mean_of_two(0, 0);
    assert(m == 0);
}

fn mean_small() {
    let m = mean_of_two(4, 6);
    assert(m == 5);
}

fn mean_edge() {
    let m = mean_of_two(0x7fff_ffff, 0x8000_0000);
    assert(m == 0x7fff_ffff);
}

// False-friends C8dv and division C9dv are paired specimens, read after predictions.
} // verus!
