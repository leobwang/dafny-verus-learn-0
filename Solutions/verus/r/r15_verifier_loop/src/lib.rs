// Reference Solution.
//! # R15 — Verifier loop (Exercises)
//!
//! Standalone R track. Import only the frozen layers A1 to A4; no earlier learner file is
//! needed. The paired exercise is dafny/R/R15_VerifierLoop/std/R15_VerifierLoop.dfy.
//!
//! This crate is rung 4 of the escalation ladder (the chapter's §1): a proof of the same
//! matcher that rungs 1 to 3 only ran, checked and tested. Record the predictions first
//! (scripts/firsttry.sh R15 --check), then attempt T1 closed book. Two typed holes ship in
//! this crate.
//!
//! File order: the test-out T1 (a prefix search), then H1 (a search anywhere in the
//! string), each followed by its use-site checks, commented under `Uncomment as you go:`,
//! and a given compiled test (`scripts/vcheck --test` runs it once your bodies are done).
//!
//! Done: scripts/vcheck --gate verus/r/r15_verifier_loop exits 0 with zero holes,
//! scripts/vaudit verus/r/r15_verifier_loop reports no finding, scripts/specfreeze --check
//! R15 reports none, and scripts/firsttry.sh R15 --report --strict exits 0.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;

// =============================================================================
// Test-out (closed book)
// =============================================================================

verus! {

// item: R15.T1v
// uses: invariant
// pair: R15.T1d
// triv: { false }
/// **T1.** Closed book: does some prefix of `s` match `r`? One derivative per character,
/// as A2's `deriv_match` does, but the answer may come early. What does the loop's regex
/// `d` promise about the slices `s[j..k]` that are still ahead, and what does the loop
/// know about the prefixes it has passed?
pub fn prefix_match_r15(r: &Re, s: &Vec<char>) -> (b: bool)
    ensures
        b == exists|j: int| 0 <= j <= s.len() && #[trigger] matches(*r, s@.subrange(0, j)),
{
    // ref-begin R15.T1v
    let mut d = copy_re(r);
    let mut j: usize = 0;
    while j < s.len()
        invariant
            0 <= j <= s.len(),
            forall|k: int|
                j <= k <= s.len() ==> (#[trigger] matches(d, s@.subrange(j as int, k)) <==> matches(
                    *r,
                    s@.subrange(0, k),
                )),
            forall|k: int| 0 <= k < j ==> !#[trigger] matches(*r, s@.subrange(0, k)),
        decreases s.len() - j,
    {
        proof {
            lemma_nullable_correct(d);
            assert(s@.subrange(j as int, j as int) =~= Seq::<char>::empty());
        }
        if is_nullable(&d) {
            return true;
        }
        let c = s[j];
        proof {
            assert forall|k: int| j + 1 <= k <= s.len() implies (#[trigger] matches(
                deriv(d, c),
                s@.subrange(j + 1, k),
            ) <==> matches(*r, s@.subrange(0, k))) by {
                lemma_deriv_correct(d, c, s@.subrange(j + 1, k));
                assert(seq![c] + s@.subrange(j + 1, k) =~= s@.subrange(j as int, k));
            }
        }
        d = deriv_exec(&d, c);
        j = j + 1;
    }
    proof {
        lemma_nullable_correct(d);
        assert(s@.subrange(j as int, j as int) =~= Seq::<char>::empty());
    }
    is_nullable(&d)
    // ref-end R15.T1v
}
// Hint(1): a loop over `j` with two invariants: one relating `d` on the slices ahead to `r` on the prefixes, one ruling out the prefixes already passed.
// Hint(2): A1b's `lemma_nullable_correct` reads `nullable(d)` as a match of the empty slice; A2's `lemma_deriv_correct(d, c, s@.subrange(j + 1, k))` moves the first invariant one character on.
// Reference checks (enabled):
// reference-only: enabled shipped check
fn prefix_check_r15() {
    let mut s: Vec<char> = Vec::new();
    s.push('a');
    s.push('b');
    let b = prefix_match_r15(&Re::Chr('a'), &s);
    assert(s@.subrange(0, 1) =~= seq!['a']);
    assert(matches(Re::Chr('a'), s@.subrange(0, 1)));
    assert(b);
    let c = prefix_match_r15(&Re::Empty, &s);
    assert(!c);
}
// end reference checks

// =============================================================================
// The search anywhere
// =============================================================================

// item: R15.H1v
// uses: invariant
// pair: R15.H1d
// triv: { false }
/// **H1.** Does some slice `s[i..j]` match `r` (an unanchored search)? The chapter's rungs
/// 1 to 3 ran, checked and tested this matcher; here you prove it. The empty slices count.
/// What must the outer loop know about the start positions it has passed, and what does
/// the inner loop's regex promise about the slices that begin at `i`?
pub fn contains_match_r15(r: &Re, s: &Vec<char>) -> (b: bool)
    ensures
        b == exists|i: int, j: int|
            0 <= i <= j <= s.len() && #[trigger] matches(*r, s@.subrange(i, j)),
{
    // ref-begin R15.H1v
    let mut i: usize = 0;
    while i <= s.len()
        invariant
            0 <= i <= s.len(),
            forall|i2: int, j2: int|
                0 <= i2 < i && i2 <= j2 <= s.len() ==> !#[trigger] matches(*r, s@.subrange(i2, j2)),
        decreases s.len() + 1 - i,
    {
        let mut d = copy_re(r);
        let mut j: usize = i;
        while j < s.len()
            invariant
                0 <= i <= j <= s.len(),
                forall|k: int|
                    j <= k <= s.len() ==> (#[trigger] matches(d, s@.subrange(j as int, k)) <==> matches(
                        *r,
                        s@.subrange(i as int, k),
                    )),
                forall|k: int| i <= k < j ==> !#[trigger] matches(*r, s@.subrange(i as int, k)),
            decreases s.len() - j,
        {
            proof {
                lemma_nullable_correct(d);
                assert(s@.subrange(j as int, j as int) =~= Seq::<char>::empty());
            }
            if is_nullable(&d) {
                return true;
            }
            let c = s[j];
            proof {
                assert forall|k: int| j + 1 <= k <= s.len() implies (#[trigger] matches(
                    deriv(d, c),
                    s@.subrange(j + 1, k),
                ) <==> matches(*r, s@.subrange(i as int, k))) by {
                    lemma_deriv_correct(d, c, s@.subrange(j + 1, k));
                    assert(seq![c] + s@.subrange(j + 1, k) =~= s@.subrange(j as int, k));
                }
            }
            d = deriv_exec(&d, c);
            j = j + 1;
        }
        proof {
            lemma_nullable_correct(d);
            assert(s@.subrange(j as int, j as int) =~= Seq::<char>::empty());
        }
        if is_nullable(&d) {
            return true;
        }
        if i == s.len() {
            return false;
        }
        i = i + 1;
    }
    false
    // ref-end R15.H1v
}
// Hint(1): nested loops: restart the derivative at every start `i`; the inner loop is T1's loop on the slices that begin at `i`. The outer loop's last start is `s.len()`: leave before `i + 1` can overflow.
// Hint(2): the outer invariant rules out every slice that starts before `i`. Inside the inner loop Verus knows only that loop's invariant; after it exits, facts about the variables it does not change (`i`, `r`, `s`) hold again.
// Reference checks (enabled):
// reference-only: enabled shipped check
fn contains_check_r15() {
    let mut s: Vec<char> = Vec::new();
    s.push('b');
    s.push('a');
    let b = contains_match_r15(&Re::Chr('a'), &s);
    assert(s@.subrange(1, 2) =~= seq!['a']);
    assert(matches(Re::Chr('a'), s@.subrange(1, 2)));
    assert(b);
    let c = contains_match_r15(&Re::Empty, &s);
    assert(!c);
}
// end reference checks

} // verus!

// Given (not an item): the compiled use-site check of T1 and H1. It runs your bodies;
// `scripts/vcheck --test` executes it once they are done.
#[test]
fn search_sample_test() {
    let ab = Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Chr('b')));
    assert!(prefix_match_r15(&ab, &vec!['a', 'b', 'x']));
    assert!(!prefix_match_r15(&ab, &vec!['x', 'a', 'b']));
    assert!(contains_match_r15(&ab, &vec!['x', 'a', 'b']));
    assert!(!contains_match_r15(&ab, &vec!['b', 'a']));
}
