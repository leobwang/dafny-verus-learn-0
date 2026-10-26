//! # R12 — Driving the verifier + Lab α (Exercises)
//!
//! The native holes are hint-site forms, the same kind of object Lab α's engine fills by
//! search: each proof fn ships its skeleton, and the learner writes only what goes at its
//! sites. An `expr` site replaces its `R12_HINT` marker and `true` with one boolean expression over
//! the identifiers its `R12_HINT_SITES` entry lists; a `calls` site replaces
//! its `R12_CALLS` marker with calls to the proof fns it lists. Everything else is frozen.
//!
//! Imports: the given regex spine `rg_re_a1` (`Re`, `matches`) and `rg_re_a3` (`copies`,
//! `copies_up_to`); no earlier exercise file.
//!
//! Done = `scripts/vcheck --gate verus/r/r12_driving` prints only the summary line and exits
//! 0, `scripts/vaudit verus/r/r12_driving` reports no finding, AND
//! `scripts/firsttry.sh R12 --report --strict` exits 0.
//!
//! This file ships with exactly 3 holes: T1, H1 and H2.
// R12_HINT_SITES: [{"name":"t1","identifiers":["u","v"]},{"name":"h1a","identifiers":["r","n","m","u","v","i"],"kind":"calls","callees":["lemma_copies_append_r12"]},{"name":"h1b","identifiers":["u","v","i"]},{"name":"h2a","identifiers":["matches","Re","Box","copies_up_to","r","j","w"]},{"name":"h2b","identifiers":["r","j","k","w","i"],"kind":"calls","callees":["lemma_up_to_mono_r12"]}]
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a3::*;

verus! {

// item: R12.T1v
// pair: R12.T1d
/// **T1.** A word of `a` followed by a word of `b` matches `Cat(a, b)`. The failing
/// obligation is `matches`'s Cat existential: which subrange of `u + v` is its trigger
/// term, and how do you name the split with extensional equalities only?
// Hint(1): site t1 is one boolean expression over u and v.
// Hint(2): two subranges of u + v, each =~= one of the words.
pub proof fn lemma_cat_witness_r12(a: Re, b: Re, u: Seq<char>, v: Seq<char>)
    requires
        matches(a, u),
        matches(b, v),
    ensures
        matches(Re::Cat(Box::new(a), Box::new(b)), u + v),
{
    #[verifier::proof_note("R12.T1v")] assume(false);  // HOLE: delete this line
    assert(/*R12_HINT:t1*/ true);
}
// Uncomment as you go:
// proof fn cat_witness_check_r12() {
//     assert(matches(Re::Chr('a'), seq!['a']));
//     assert(matches(Re::Chr('b'), seq!['b']));
//     lemma_cat_witness_r12(Re::Chr('a'), Re::Chr('b'), seq!['a'], seq!['b']);
//     assert(seq!['a'] + seq!['b'] =~= seq!['a', 'b']);
//     assert(matches(Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Chr('b'))), seq!['a', 'b']));
// }

// item: R12.H1v
// pair: R12.H1d
/// **H1.** `n` copies then `m` copies make `n + m` copies. The skeleton chooses the
/// split `i` of `u`. Which call does the tail need (site h1a), and which equality turns
/// the provided Cat witness into `u + v` (h1b)?
// Hint(1): h1a is one call of lemma_copies_append_r12 itself, on a smaller n.
// Hint(2): h1b is an extensional equality built from the two subranges of u and v.
pub proof fn lemma_copies_append_r12(r: Re, n: nat, m: nat, u: Seq<char>, v: Seq<char>)
    requires
        matches(copies(r, n), u),
        matches(copies(r, m), v),
    ensures
        matches(copies(r, n + m), u + v),
    decreases n,
{
    #[verifier::proof_note("R12.H1v")] assume(false);  // HOLE: delete this line
    if n > 0 {
        let i = choose|i: int|
            0 <= i <= u.len() && matches(r, #[trigger] u.subrange(0, i)) && matches(
                copies(r, (n - 1) as nat),
                u.subrange(i, u.len() as int),
            );
        /*R12_CALLS:h1a*/
        lemma_cat_witness_r12(r, copies(r, (n - 1 + m) as nat), u.subrange(0, i), u.subrange(i, u.len() as int) + v);
        assert(/*R12_HINT:h1b*/ true);
    } else {
        assert(u =~= Seq::<char>::empty());
        assert(u + v =~= v);
    }
}

// item: R12.H2v
// pair: R12.H2d
/// **H2.** A word of at most `j` copies is a word of at most `k >= j` copies. For a
/// non-empty word, which branch of `copies_up_to(r, j)`'s `Alt` holds (site h2a), and
/// which bounds does the induction call need (h2b)?
// Hint(1): h2a names a matches fact about the Alt's second operand.
// Hint(2): h2b lowers both bounds by one, on the tail chosen by the skeleton.
pub proof fn lemma_up_to_mono_r12(r: Re, j: nat, k: nat, w: Seq<char>)
    requires
        j <= k,
        matches(copies_up_to(r, j), w),
    ensures
        matches(copies_up_to(r, k), w),
    decreases j,
{
    #[verifier::proof_note("R12.H2v")] assume(false);  // HOLE: delete this line
    if w.len() == 0 {
        if k > 0 {
            assert(matches(Re::Eps, w));
        }
    } else {
        if j == 0 {
            assert(copies_up_to(r, j) == Re::Eps);
        }
        assert(j > 0);
        assert(!matches(Re::Eps, w));
        assert(/*R12_HINT:h2a*/ true);
        let i = choose|i: int|
            0 <= i <= w.len() && matches(r, #[trigger] w.subrange(0, i)) && matches(
                copies_up_to(r, (j - 1) as nat),
                w.subrange(i, w.len() as int),
            );
        /*R12_CALLS:h2b*/
        lemma_cat_witness_r12(r, copies_up_to(r, (k - 1) as nat), w.subrange(0, i), w.subrange(i, w.len() as int));
        assert(w.subrange(0, i) + w.subrange(i, w.len() as int) =~= w);
    }
}

} // verus!
