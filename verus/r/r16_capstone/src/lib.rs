//! # R16 — Capstone (exercises)
//!
//! Standalone R track. Import only the frozen layers A1, A1b, A2 and A5 and your own
//! statement file statements.rs; no earlier learner file is needed. The paired exercise is
//! dafny/R/R16_Capstone/std/R16_Capstone.dfy.
//!
//! Attempt T1 closed book before reading the chapter. Then work on paper first (the
//! chapter's §2: the blueprint is graded before you formalize), write and freeze your
//! statements (H1, in statements.rs), and only then prove them here. Eight typed items ship
//! in this crate: T1, H1 (in statements.rs), H2, H3, H4, H5, H6 and H7; H4 (jump threading)
//! is the gated optimizer.
//!
//! File order: the test-out T1, completeness H2 (`lemma_emit_complete`, then your helper
//! lemmas), soundness H3 (`lemma_emit_sound`, then helpers), the optimizer H4 (the given
//! `hop` and `shortcut`, `lemma_shortcut_correct`, then helpers) and `rexc`
//! H5 (the whole-program theorem and `rexc_match`, with its given use-site check), then
//! rexc's second engine (the given `lazy_match`, its correctness H6 and its exec matcher H7,
//! each yours to give a measure, with the given cross-check). A5's
//! `accepts` is opaque: use its one-step lemmas (`lemma_accepts_char`, `_split`, `_jmp`,
//! `_match`) and `lemma_accepts_inside`, never a reveal.
//!
//! Done: the crate gates with zero tool-counted holes, vaudit is clean,
//! specfreeze --check R16 passes and firsttry's strict report is OK.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a5::*;

pub mod statements;
use crate::statements::*;

verus! {

// =============================================================================
// Test-out (closed book)
// =============================================================================

// item: R16.T1v
// uses: lemma-recursion
// pair: R16.T1d
/// **T1.** Closed book: the code A5 emits for `r` is at most two instructions per node of
/// `r`. Which constructors emit more instructions than they have children, and what does
/// the verifier need to know about each child?
pub proof fn lemma_emit_size_r16(r: Re)
    ensures
        clen(r) <= 2 * node_count(r),
    decreases r,
{
    #[verifier::proof_note("R16.T1v")] assume(false);
}
// Hint(1): induction on `r`, one call per child; Verus proves no lemma by induction on its own.
// Hint(2): `clen` and `node_count` unfold one level per constructor; the leaves need no call.

// =============================================================================
// Completeness
// =============================================================================

// item: R16.H2v
// uses: lemma-recursion, lexicographic-decreases
// pair: R16.H2d
/// **H2.** Prove your frozen completeness statement. Write the body of `lemma_emit_complete`,
/// then your helper lemmas below it. `accepts_from` hides the fuel, so the induction runs on a
/// fuelled helper: from an accepting run of the continuation with fuel `f`, build one of `r`'s
/// code with some fuel `f2`. Which constructor's case recurses on the same regex, and what then
/// becomes smaller? Which addresses does each layout lemma name?
pub proof fn lemma_emit_complete(p: Seq<Inst>, r: Re, pc: int, u: Seq<char>, v: Seq<char>)
    ensures
        emit_complete_statement(p, r, pc, u, v),
{
    #[verifier::proof_note("R16.H2v")] assume(false);
}

// Your helper lemmas (H2), here.
// Hint(1): a fuelled helper by induction on `r`, with `Star` by induction on the length of the word: the first pass through `a` reads a non-empty chunk (A1's `matches` gives it), and the rest is a shorter match of `Star(a)`.
// Hint(2): `lemma_sub_alt`, `lemma_sub_cat` and `lemma_sub_star` name each child's address and the jumps between them; `lemma_accepts_split` and `lemma_accepts_jmp` take one step each, so the fuel grows by one per instruction you pass.

// =============================================================================
// Soundness
// =============================================================================

// item: R16.H3v
// uses: lemma-recursion, lexicographic-decreases
// pair: R16.H3d
/// **H3.** Prove your frozen soundness statement. Write the body of `lemma_emit_sound`, then
/// your helper lemmas below it. Here the induction runs on the fuel of the given run: from a
/// run of `r`'s code with fuel `f`, find the split point `k` and a run of the continuation with
/// no more fuel. Which cases spend no fuel before they recurse, and on what? How does a `Split`
/// decide which branch to follow?
pub proof fn lemma_emit_sound(p: Seq<Inst>, r: Re, pc: int, w: Seq<char>)
    ensures
        emit_sound_statement(p, r, pc, w),
{
    #[verifier::proof_note("R16.H3v")] assume(false);
}

// Your helper lemmas (H3), here.
// Hint(1): a fuelled helper by induction on the regex first and the fuel second: `Cat` and the entry of `Alt` and `Star` recurse on a smaller regex, `Star`'s back edge and an `Empty`'s self-jump on the same regex with less fuel.
// Hint(2): `lemma_accepts_split` says which of the two branches holds the run (test one with `if`); A1b's `lemma_star_concat` joins a word of `a` and a word of `Star(a)` once the first is shown to be a word of `Star(a)`.

// =============================================================================
// The optimizer (gated)
// =============================================================================

/// One-hop jump threading: a jump whose target is a jump goes straight to the second jump's
/// target. Every other instruction, and a jump whose target is not a jump (or is outside the
/// program), is unchanged. A self-loop stays one.
pub open spec fn hop(p: Seq<Inst>, ins: Inst) -> Inst {
    match ins {
        Inst::Jmp(a) => if (a as int) < p.len() && p[a as int] is Jmp {
            Inst::Jmp(p[a as int]->Jmp_0)
        } else {
            ins
        },
        _ => ins,
    }
}

pub open spec fn shortcut(p: Seq<Inst>) -> Seq<Inst> {
    Seq::new(p.len(), |i: int| hop(p, p[i]))
}

// item: R16.H4v
// uses: lemma-recursion
// pair: R16.H4d
/// **H4.** Prove that threading every jump changes no state's language, in both directions,
/// from every address. Write the body of `lemma_shortcut_correct`, then your helper lemmas
/// below it. A threaded jump skips one instruction of the original, so one direction spends
/// more fuel than the other. Which direction is that, and what does `lemma_accepts_inside` give
/// you before you look at the instruction at `pc`?
pub proof fn lemma_shortcut_correct(p: Seq<Inst>, pc: int, w: Seq<char>)
    ensures
        accepts_from(shortcut(p), pc, w) == accepts_from(p, pc, w),
{
    #[verifier::proof_note("R16.H4v")] assume(false);
}

// Your helper lemmas (H4), here.
// Hint(1): one fuelled helper per direction, each by induction on the fuel, with one case per instruction kind at `pc`; the threaded jump is the only case where the two programs differ.
// Hint(2): from the original to the threaded program, a jump to a jump spends two steps of the original for one of the threaded; the other way, the skipped jump costs one more step of the original, taken at the jump's own target.

// =============================================================================
// rexc: the whole-program theorem and the matcher
// =============================================================================

// item: R16.H5v
// pair: R16.H5d
/// **H5.** The compiled program, `emit(r, 0)` followed by `Match`, accepts exactly the words
/// `r` matches (`lemma_emit_correct`; use only your two statements, through
/// `lemma_emit_complete` and `lemma_emit_sound`, and A5's lemmas). Then `rexc_match`: emit
/// the program with A5's `emit_prog`, run it with `pike_run`, and answer; `None` only when
/// the program does not fit the address space. Which continuation does each direction of
/// the theorem need, and which fact links `pike_run`'s answer to `matches`?
pub proof fn lemma_emit_correct(r: Re, s: Seq<char>)
    requires
        clen(r) + 1 < usize::MAX,
    ensures
        accepts_from(prog(r), 0, s) == matches(r, s),
{
    #[verifier::proof_note("R16.H5v")] assume(false);
}

pub fn rexc_match(r: &Re, s: &Vec<char>) -> (res: Option<bool>)
    ensures
        res is Some ==> res->Some_0 == matches(*r, s@),
        res is None ==> clen(*r) + 1 >= usize::MAX,
{
    proof {
        #[verifier::proof_note("R16.H5v")] assume(false);  // HOLE: replace this block
    }
    None
}
// Hint(1): A5's `lemma_prog_layout` places `emit(r, 0)` at address 0 and `Match` at `clen(r)`; the continuation is that one instruction.
// Hint(2): `lemma_accepts_match` accepts only the empty word, so the split your soundness statement returns must be the whole word; `emit_prog` and `pike_run` already state the program and the answer, so `rexc_match` needs one call of the theorem.
// Uncomment as you go:
// fn rexc_match_check() {
//     let mut s: Vec<char> = Vec::new();
//     s.push('a');
//     let res = rexc_match(&Re::Chr('a'), &s);
//     assert(s@ =~= seq!['a']);
//     assert(res == Some(true));
//     let none = rexc_match(&Re::Empty, &s);
//     assert(none == Some(false));
// }

// =============================================================================
// rexc's second engine: derivatives
// =============================================================================

/// A second matcher, for rexc's cross-check against the VM: A2's derivatives, except that an
/// alternation is split instead of built (both branches are matched against the same word).
/// Splitting makes the regex smaller with the word unchanged; deriving makes the word shorter
/// and the regex possibly larger (`deriv(Star(a), c)` is `Cat(deriv(a, c), Star(a))`).
pub open spec fn lazy_match(r: Re, w: Seq<char>) -> bool
    decreases w.len(), r,
{
    if w.len() == 0 {
        nullable(r)
    } else {
        match r {
            Re::Alt(a, b) => lazy_match(*a, w) || lazy_match(*b, w),
            _ => lazy_match(deriv(r, w[0]), w.drop_first()),
        }
    }
}

// item: R16.H6v
// uses: lemma-recursion, lexicographic-decreases
// pair: R16.H6d
/// **H6.** Prove that the lazy engine decides `matches`. Write the body of `lemma_lazy_match`,
/// and give the lemma the measure its recursion needs (it ships without one). Which of your
/// recursive calls keep the word and shrink the regex, which shorten the word and may grow
/// the regex, and why does no single number built from `w.len()` and `node_count(r)` go
/// down at both?
pub proof fn lemma_lazy_match(r: Re, w: Seq<char>)
    ensures
        lazy_match(r, w) == matches(r, w),
{
    #[verifier::proof_note("R16.H6v")] assume(false);
}
// Hint(1): follow `lazy_match`'s own cases: the empty word, an alternation, and every other regex at a non-empty word.
// Hint(2): A1b's `lemma_nullable_correct` settles the empty word and A2's `lemma_deriv_correct` the derivative step; the measure compares the word's length first and the regex second.

// item: R16.H7v
// uses: lexicographic-decreases
// pair: R16.H7d
/// **H7.** Compile the lazy engine: a recursive exec fn that answers whether `r` matches the
/// suffix of `s` from `i`, splitting an alternation and deriving otherwise, as `lazy_match`
/// does. Write its body and give it the measure it needs (it ships without one). What
/// decreases when the function moves to `i + 1`, what when it splits, and in which order
/// must the measure compare them?
pub fn lazy_match_exec(r: &Re, s: &Vec<char>, i: usize) -> (b: bool)
    requires
        i <= s.len(),
    ensures
        b == matches(*r, s@.subrange(i as int, s@.len() as int)),
{
    proof {
        #[verifier::proof_note("R16.H7v")] assume(false);  // HOLE: replace this block
    }
    false
}
// Hint(1): one case per branch of `lazy_match`; A1's `is_nullable` and A2's `deriv_exec` are exec, `lazy_match` and `matches` are spec only.
// Hint(2): `lemma_nullable_correct` and `lemma_deriv_correct` give the two facts the cases need; a recursive call on a branch keeps `i`, one on the derivative moves to `i + 1`.

/// The use-site check: rexc's two engines agree on every regex and word.
pub fn cross_check_r16(r: &Re, s: &Vec<char>) -> (agree: bool)
    ensures
        agree,
{
    let lazy = lazy_match_exec(r, s, 0);
    assert(s@.subrange(0, s@.len() as int) =~= s@);
    match rexc_match(r, s) {
        Some(b) => b == lazy,
        None => true,
    }
}

} // verus!
