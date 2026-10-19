//! R01 — Hello, two verifiers (exercises). No earlier module or given layer is imported.
//! Five holes: two in T1v and H1v–H3v; Dafny holds the other five.
//! Record all six predictions before reading past their block or opening card demos.
//! Complete the closed-book census before the worked examples.
//! Each hole H1–H3 has a prompt with a guiding question and two hints below it.
//! Done: scripts/vcheck --gate verus/r/r01_hello; scripts/vaudit verus/r/r01_hello;
//! scripts/specfreeze --check R01; scripts/firsttry.sh R01 --report --strict all pass.
//! Green with a typed placeholder is not done. /tutor R01 after 20 stuck minutes.
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
    #[verifier::proof_note("R01.T1v")] assume(false);  // HOLE
}

#[verifier::external_body]  // HOLE: remove when implementing
pub fn count_first_two(s: &Vec<char>, c: char) -> (n: u32)
    requires
        s.len() >= 2,
    ensures
        n == count_char(s@.subrange(0, 2), c),
{
    unimplemented!()
}
// Uncomment as you go:
// fn census_check() {
//     let s = vec!['a', 'b'];
//     proof {
//         assert(s@.subrange(0, 2) =~= seq!['a', 'b']);
//         lemma_count_char_pair('a', 'b', 'a');
//     }
//     let n = count_first_two(&s, 'a');
//     assert(n == 1);
// }

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
#[verifier::external_body]  // HOLE: remove when implementing
pub fn midpoint(lo: u32, hi: u32) -> (m: u32)
    requires
        lo <= hi,
    ensures
        lo <= m <= hi,
        m as int == (lo as int + hi as int) / 2,
{
    unimplemented!()
}
// Hint(1): Verus checks every executable `u32` operation for overflow, not only the result.
// Hint(2): the precondition `lo <= hi` is the one given fact the body can spend:
//    which subtraction does it make legal?
// Uncomment as you go:
// fn midpoint_check() {
//     let m = midpoint(0xffff_fffe, 0xffff_ffff);
//     assert(m == 0xffff_fffe);
// }

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
    #[verifier::proof_note("R01.H2v")] assume(false);  // HOLE
}
// Hint(1): split on whether `s` is empty; `count_char`'s definition does the same.
// Hint(2): a call of this lemma on a shorter `s` is the hypothesis (W2's call);
//    the verifier also needs the sequence equality, stated with `=~=`, that
//    connects `s + t` to that call.
// Uncomment as you go:
// proof fn append_check() {
//     lemma_count_char_append(seq!['x'], seq!['y', 'x'], 'x');
// }

// item: R01.H3v
// uses: requires
// pair: R01.H3d
/// **H3.** Keep the body and the result clause; write the `requires` clause that
/// makes `(a + b) / 2` verify while all three given callers below still verify,
/// then delete the labelled `assume`. Which operation of the body owes a range
/// fact, and which caller rejects a clause that bounds each argument on its own?
pub fn mean_of_two(a: u32, b: u32) -> (m: u32)
    // HOLE: add a requires clause; preserve the body and callers.
    ensures
        m as int == (a as int + b as int) / 2,
{
    proof {
        #[verifier::proof_note("R01.H3v")] assume(false);  // HOLE: remove
    }
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
