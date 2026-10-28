// Reference Solution.
//! # R16 — Capstone (exercises)
//!
//! Standalone R track. Import only the frozen layers A1, A1b and A5 and your own statement
//! file statements.rs; no earlier learner file is needed. The paired exercise is
//! dafny/R/R16_Capstone/std/R16_Capstone.dfy.
//!
//! Attempt T1 closed book before reading the chapter. Then work on paper first (the
//! chapter's §2: the blueprint is graded before you formalize), write and freeze your
//! statements (H1, in statements.rs), and only then prove them here. Six typed items ship in
//! this crate: T1, H1 (in statements.rs), H2, H3, H4 and H5; H4 (jump threading) is the
//! gated optimizer.
//!
//! File order: the test-out T1, completeness H2 (`lemma_emit_complete`, then your helper
//! lemmas), soundness H3 (`lemma_emit_sound`, then helpers), the optimizer H4 (the given
//! `hop` and `shortcut`, `lemma_shortcut_correct`, then helpers) and `rexc`
//! H5 (the whole-program theorem and `rexc_match`, with its given use-site check). A5's
//! `accepts` is opaque: use its one-step lemmas (`lemma_accepts_char`, `_split`, `_jmp`,
//! `_match`) and `lemma_accepts_inside`, never a reveal.
//!
//! Done: the crate gates with zero tool-counted holes, vaudit is clean,
//! specfreeze --check R16 passes and firsttry's strict report is OK.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
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
    // @hole-begin R16.T1v
    match r {
        Re::Alt(a, b) => {
            lemma_emit_size_r16(*a);
            lemma_emit_size_r16(*b);
        },
        Re::Cat(a, b) => {
            lemma_emit_size_r16(*a);
            lemma_emit_size_r16(*b);
        },
        Re::Star(a) => {
            lemma_emit_size_r16(*a);
        },
        _ => {},
    }
    // @hole-end R16.T1v
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
    // @hole-begin R16.H2v
    if code_at(p, pc, emit(r, pc)) && pc + clen(r) < usize::MAX && matches(r, u) && accepts_from(p, pc + clen(r), v) {
        let f = choose|f: nat| #[trigger] accepts(p, pc + clen(r), v, f);
        let f2 = lemma_complete(p, r, pc, u, v, f);
    }
    // @hole-end R16.H2v
}

// @hole-begin R16.H2v
proof fn lemma_split_add(s1: Seq<char>, i: int, s2: Seq<char>)
    requires
        0 <= i <= s1.len(),
    ensures
        s1.subrange(0, i) + (s1.subrange(i, s1.len() as int) + s2) == s1 + s2,
{
    assert(s1.subrange(0, i) + (s1.subrange(i, s1.len() as int) + s2) =~= s1 + s2);
}

proof fn lemma_complete(p: Seq<Inst>, r: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
    requires
        code_at(p, pc, emit(r, pc)),
        pc + clen(r) < usize::MAX,
        matches(r, s1),
        accepts(p, pc + clen(r), s2, f),
    ensures
        accepts(p, pc, s1 + s2, f2),
    decreases r, s1.len(), 1nat,
{
    match r {
        Re::Eps => {
            assert(s1 + s2 =~= s2);
            f
        },
        Re::Chr(_) => {
            lemma_sub_one(p, r, pc);
            assert((s1 + s2).drop_first() =~= s2);
            assert((s1 + s2)[0] == s1[0]);
            lemma_accepts_char(p, pc, s1 + s2, f + 1);
            f + 1
        },
        Re::Alt(a, b) => lemma_complete_alt(p, *a, *b, pc, s1, s2, f),
        Re::Cat(a, b) => lemma_complete_cat(p, *a, *b, pc, s1, s2, f),
        Re::Star(a) => lemma_complete_star(p, *a, pc, s1, s2, f),
        Re::Empty => 0,
    }
}

proof fn lemma_complete_alt(p: Seq<Inst>, a: Re, b: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
    requires
        code_at(p, pc, emit(Re::Alt(Box::new(a), Box::new(b)), pc)),
        pc + clen(Re::Alt(Box::new(a), Box::new(b))) < usize::MAX,
        matches(Re::Alt(Box::new(a), Box::new(b)), s1),
        accepts(p, pc + clen(Re::Alt(Box::new(a), Box::new(b))), s2, f),
    ensures
        accepts(p, pc, s1 + s2, f2),
    decreases Re::Alt(Box::new(a), Box::new(b)), s1.len(), 0nat,
{
    lemma_sub_alt(p, a, b, pc);
    if matches(a, s1) {
        lemma_accepts_jmp(p, pc + 1 + clen(a), s2, f + 1);
        let f1 = lemma_complete(p, a, pc + 1, s1, s2, f + 1);
        lemma_accepts_split(p, pc, s1 + s2, f1 + 1);
        f1 + 1
    } else {
        let f1 = lemma_complete(p, b, pc + 2 + clen(a), s1, s2, f);
        lemma_accepts_split(p, pc, s1 + s2, f1 + 1);
        f1 + 1
    }
}

proof fn lemma_complete_cat(p: Seq<Inst>, a: Re, b: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
    requires
        code_at(p, pc, emit(Re::Cat(Box::new(a), Box::new(b)), pc)),
        pc + clen(Re::Cat(Box::new(a), Box::new(b))) < usize::MAX,
        matches(Re::Cat(Box::new(a), Box::new(b)), s1),
        accepts(p, pc + clen(Re::Cat(Box::new(a), Box::new(b))), s2, f),
    ensures
        accepts(p, pc, s1 + s2, f2),
    decreases Re::Cat(Box::new(a), Box::new(b)), s1.len(), 0nat,
{
    lemma_sub_cat(p, a, b, pc);
    let i = choose|i: int|
        0 <= i <= s1.len() && matches(a, #[trigger] s1.subrange(0, i)) && matches(b, s1.subrange(i, s1.len() as int));
    let x = s1.subrange(0, i);
    let y = s1.subrange(i, s1.len() as int);
    let fb = lemma_complete(p, b, pc + clen(a), y, s2, f);
    let fa = lemma_complete(p, a, pc, x, y + s2, fb);
    lemma_split_add(s1, i, s2);
    fa
}

proof fn lemma_complete_star(p: Seq<Inst>, a: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
    requires
        code_at(p, pc, emit(Re::Star(Box::new(a)), pc)),
        pc + clen(Re::Star(Box::new(a))) < usize::MAX,
        matches(Re::Star(Box::new(a)), s1),
        accepts(p, pc + clen(Re::Star(Box::new(a))), s2, f),
    ensures
        accepts(p, pc, s1 + s2, f2),
    decreases Re::Star(Box::new(a)), s1.len(), 0nat,
{
    let r = Re::Star(Box::new(a));
    lemma_sub_star(p, a, pc);
    if s1.len() == 0 {
        assert(s1 + s2 =~= s2);
        lemma_accepts_split(p, pc, s1 + s2, f + 1);
        f + 1
    } else {
        let i = choose|i: int|
            1 <= i <= s1.len() && matches(a, #[trigger] s1.subrange(0, i)) && matches(r, s1.subrange(i, s1.len() as int));
        let x = s1.subrange(0, i);
        let y = s1.subrange(i, s1.len() as int);
        let fy = lemma_complete(p, r, pc, y, s2, f);
        lemma_accepts_jmp(p, pc + 1 + clen(a), y + s2, fy + 1);
        let fx = lemma_complete(p, a, pc + 1, x, y + s2, fy + 1);
        lemma_split_add(s1, i, s2);
        lemma_accepts_split(p, pc, s1 + s2, fx + 1);
        fx + 1
    }
}
// @hole-end R16.H2v
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
    // @hole-begin R16.H3v
    if code_at(p, pc, emit(r, pc)) && pc + clen(r) < usize::MAX && accepts_from(p, pc, w) {
        let f = choose|f: nat| #[trigger] accepts(p, pc, w, f);
        let (k, f2) = lemma_sound(p, r, pc, w, f);
        assert(accepts(p, pc + clen(r), w.subrange(k, w.len() as int), f2));
    }
    // @hole-end R16.H3v
}

// @hole-begin R16.H3v
proof fn lemma_star_cons(a: Re, x: Seq<char>, y: Seq<char>)
    requires
        matches(a, x),
        matches(Re::Star(Box::new(a)), y),
    ensures
        matches(Re::Star(Box::new(a)), x + y),
{
    let st = Re::Star(Box::new(a));
    if x.len() > 0 {
        assert(x.subrange(0, x.len() as int) =~= x);
        assert(x.subrange(x.len() as int, x.len() as int) =~= Seq::<char>::empty());
        assert(matches(st, x.subrange(x.len() as int, x.len() as int)));
        assert(matches(st, x));
        lemma_star_concat(a, x, y);
    } else {
        assert(x + y =~= y);
    }
}

spec fn sound_post(p: Seq<Inst>, r: Re, pc: int, s: Seq<char>, f: nat, res: (int, nat)) -> bool {
    &&& 0 <= res.0 <= s.len()
    &&& res.1 <= f
    &&& matches(r, s.subrange(0, res.0))
    &&& accepts(p, pc + clen(r), s.subrange(res.0, s.len() as int), res.1)
}

proof fn lemma_sound(p: Seq<Inst>, r: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
    requires
        code_at(p, pc, emit(r, pc)),
        pc + clen(r) < usize::MAX,
        accepts(p, pc, s, f),
    ensures
        sound_post(p, r, pc, s, f, res),
    decreases r, f, 1nat,
{
    assert(s.subrange(0, s.len() as int) =~= s);
    assert(s.subrange(0, 0) =~= Seq::<char>::empty());
    match r {
        Re::Eps => (0, f),
        Re::Empty => {
            lemma_sub_one(p, r, pc);
            lemma_accepts_jmp(p, pc, s, f);
            let _ = lemma_sound(p, r, pc, s, (f - 1) as nat);
            (0, 0)
        },
        Re::Chr(c) => {
            lemma_sub_one(p, r, pc);
            lemma_accepts_char(p, pc, s, f);
            assert(s.subrange(1, s.len() as int) =~= s.drop_first());
            assert(s.subrange(0, 1)[0] == c);
            (1, (f - 1) as nat)
        },
        Re::Alt(a, b) => lemma_sound_alt(p, *a, *b, pc, s, f),
        Re::Cat(a, b) => lemma_sound_cat(p, *a, *b, pc, s, f),
        Re::Star(a) => lemma_sound_star(p, *a, pc, s, f),
    }
}

proof fn lemma_sound_alt(p: Seq<Inst>, a: Re, b: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
    requires
        code_at(p, pc, emit(Re::Alt(Box::new(a), Box::new(b)), pc)),
        pc + clen(Re::Alt(Box::new(a), Box::new(b))) < usize::MAX,
        accepts(p, pc, s, f),
    ensures
        sound_post(p, Re::Alt(Box::new(a), Box::new(b)), pc, s, f, res),
    decreases Re::Alt(Box::new(a), Box::new(b)), f, 0nat,
{
    lemma_sub_alt(p, a, b, pc);
    lemma_accepts_split(p, pc, s, f);
    if accepts(p, pc + 1, s, (f - 1) as nat) {
        let (j, f1) = lemma_sound(p, a, pc + 1, s, (f - 1) as nat);
        lemma_accepts_jmp(p, pc + 1 + clen(a), s.subrange(j, s.len() as int), f1);
        (j, (f1 - 1) as nat)
    } else {
        lemma_sound(p, b, pc + 2 + clen(a), s, (f - 1) as nat)
    }
}

proof fn lemma_sound_cat(p: Seq<Inst>, a: Re, b: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
    requires
        code_at(p, pc, emit(Re::Cat(Box::new(a), Box::new(b)), pc)),
        pc + clen(Re::Cat(Box::new(a), Box::new(b))) < usize::MAX,
        accepts(p, pc, s, f),
    ensures
        sound_post(p, Re::Cat(Box::new(a), Box::new(b)), pc, s, f, res),
    decreases Re::Cat(Box::new(a), Box::new(b)), f, 0nat,
{
    lemma_sub_cat(p, a, b, pc);
    let (j1, f1) = lemma_sound(p, a, pc, s, f);
    let t = s.subrange(j1, s.len() as int);
    let (j2, f2) = lemma_sound(p, b, pc + clen(a), t, f1);
    let j = j1 + j2;
    let w = s.subrange(0, j);
    assert(w.subrange(0, j1) =~= s.subrange(0, j1));
    assert(w.subrange(j1, w.len() as int) =~= t.subrange(0, j2));
    assert(t.subrange(j2, t.len() as int) =~= s.subrange(j, s.len() as int));
    assert(matches(a, w.subrange(0, j1)));
    (j, f2)
}

proof fn lemma_sound_star(p: Seq<Inst>, a: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
    requires
        code_at(p, pc, emit(Re::Star(Box::new(a)), pc)),
        pc + clen(Re::Star(Box::new(a))) < usize::MAX,
        accepts(p, pc, s, f),
    ensures
        sound_post(p, Re::Star(Box::new(a)), pc, s, f, res),
    decreases Re::Star(Box::new(a)), f, 0nat,
{
    let r = Re::Star(Box::new(a));
    lemma_sub_star(p, a, pc);
    assert(s.subrange(0, s.len() as int) =~= s);
    assert(s.subrange(0, 0) =~= Seq::<char>::empty());
    lemma_accepts_split(p, pc, s, f);
    if accepts(p, pc + 1, s, (f - 1) as nat) {
        let (j1, f1) = lemma_sound(p, a, pc + 1, s, (f - 1) as nat);
        let t = s.subrange(j1, s.len() as int);
        lemma_accepts_jmp(p, pc + 1 + clen(a), t, f1);
        let (j2, f2) = lemma_sound(p, r, pc, t, (f1 - 1) as nat);
        let j = j1 + j2;
        assert(s.subrange(0, j) =~= s.subrange(0, j1) + t.subrange(0, j2));
        assert(t.subrange(j2, t.len() as int) =~= s.subrange(j, s.len() as int));
        lemma_star_cons(a, s.subrange(0, j1), t.subrange(0, j2));
        (j, f2)
    } else {
        (0, (f - 1) as nat)
    }
}
// @hole-end R16.H3v
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
    // @hole-begin R16.H4v
    if accepts_from(p, pc, w) {
        let f = choose|f: nat| #[trigger] accepts(p, pc, w, f);
        let g = lemma_to_shortcut(p, pc, w, f);
    }
    if accepts_from(shortcut(p), pc, w) {
        let f = choose|f: nat| #[trigger] accepts(shortcut(p), pc, w, f);
        let g = lemma_from_shortcut(p, pc, w, f);
    }
    // @hole-end R16.H4v
}

// @hole-begin R16.H4v
proof fn lemma_to_shortcut(p: Seq<Inst>, pc: int, w: Seq<char>, f: nat) -> (g: nat)
    requires
        accepts(p, pc, w, f),
    ensures
        accepts(shortcut(p), pc, w, g),
    decreases f,
{
    let q = shortcut(p);
    lemma_accepts_inside(p, pc, w, f);
    match p[pc] {
        Inst::Match => {
            lemma_accepts_match(p, pc, w, f);
            lemma_accepts_match(q, pc, w, 1);
            1
        },
        Inst::Char(c) => {
            lemma_accepts_char(p, pc, w, f);
            let g1 = lemma_to_shortcut(p, pc + 1, w.drop_first(), (f - 1) as nat);
            lemma_accepts_char(q, pc, w, g1 + 1);
            g1 + 1
        },
        Inst::Split(x, y) => {
            lemma_accepts_split(p, pc, w, f);
            let g1 = if accepts(p, x as int, w, (f - 1) as nat) {
                lemma_to_shortcut(p, x as int, w, (f - 1) as nat)
            } else {
                lemma_to_shortcut(p, y as int, w, (f - 1) as nat)
            };
            lemma_accepts_split(q, pc, w, g1 + 1);
            g1 + 1
        },
        Inst::Jmp(a) => {
            lemma_accepts_jmp(p, pc, w, f);
            let g1 = if (a as int) < p.len() && p[a as int] is Jmp {
                lemma_accepts_jmp(p, a as int, w, (f - 1) as nat);
                lemma_to_shortcut(p, p[a as int]->Jmp_0 as int, w, (f - 2) as nat)
            } else {
                lemma_to_shortcut(p, a as int, w, (f - 1) as nat)
            };
            lemma_accepts_jmp(q, pc, w, g1 + 1);
            g1 + 1
        },
    }
}

proof fn lemma_from_shortcut(p: Seq<Inst>, pc: int, w: Seq<char>, f: nat) -> (g: nat)
    requires
        accepts(shortcut(p), pc, w, f),
    ensures
        accepts(p, pc, w, g),
    decreases f,
{
    let q = shortcut(p);
    lemma_accepts_inside(q, pc, w, f);
    match p[pc] {
        Inst::Match => {
            lemma_accepts_match(q, pc, w, f);
            lemma_accepts_match(p, pc, w, 1);
            1
        },
        Inst::Char(c) => {
            lemma_accepts_char(q, pc, w, f);
            let g1 = lemma_from_shortcut(p, pc + 1, w.drop_first(), (f - 1) as nat);
            lemma_accepts_char(p, pc, w, g1 + 1);
            g1 + 1
        },
        Inst::Split(x, y) => {
            lemma_accepts_split(q, pc, w, f);
            let g1 = if accepts(q, x as int, w, (f - 1) as nat) {
                lemma_from_shortcut(p, x as int, w, (f - 1) as nat)
            } else {
                lemma_from_shortcut(p, y as int, w, (f - 1) as nat)
            };
            lemma_accepts_split(p, pc, w, g1 + 1);
            g1 + 1
        },
        Inst::Jmp(a) => {
            lemma_accepts_jmp(q, pc, w, f);
            if (a as int) < p.len() && p[a as int] is Jmp {
                let g1 = lemma_from_shortcut(p, p[a as int]->Jmp_0 as int, w, (f - 1) as nat);
                lemma_accepts_jmp(p, a as int, w, g1 + 1);
                lemma_accepts_jmp(p, pc, w, g1 + 2);
                g1 + 2
            } else {
                let g1 = lemma_from_shortcut(p, a as int, w, (f - 1) as nat);
                lemma_accepts_jmp(p, pc, w, g1 + 1);
                g1 + 1
            }
        },
    }
}
// @hole-end R16.H4v
// Hint(1): one fuelled helper per direction, each by induction on the fuel, with one case per instruction kind at `pc`; the threaded jump is the only case where the two programs differ.
// Hint(2): from the original to the threaded program, a jump to a jump spends two steps of the original for one of the threaded; the other way, rebuild the skipped jump with `lemma_accepts_jmp(p, a as int, w, g1 + 1)`.

// =============================================================================
// rexc: the whole-program theorem and the matcher
// =============================================================================

// item: R16.H5v
// pair: R16.H5d
// triv: { None }
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
    // @hole-begin R16.H5v
    let p = prog(r);
    lemma_prog_layout(r);
    let end = clen(r) as int;
    if accepts_from(p, 0, s) {
        lemma_emit_sound(p, r, 0, s);
        let k = choose|k: int| 0 <= k <= s.len() && #[trigger] matches(r, s.subrange(0, k)) && accepts_from(p, end, s.subrange(k, s.len() as int));
        let rest = s.subrange(k, s.len() as int);
        let f = choose|f: nat| #[trigger] accepts(p, end, rest, f);
        lemma_accepts_match(p, end, rest, f);
        assert(s.subrange(0, k) =~= s);
    }
    if matches(r, s) {
        let e = Seq::<char>::empty();
        lemma_accepts_match(p, end, e, 1);
        lemma_emit_complete(p, r, 0, s, e);
        assert(s + e =~= s);
    }
    // @hole-end R16.H5v
}

pub fn rexc_match(r: &Re, s: &Vec<char>) -> (res: Option<bool>)
    ensures
        res is Some ==> res->Some_0 == matches(*r, s@),
        res is None ==> clen(*r) + 1 >= usize::MAX,
{
    // ref-begin R16.H5v
    match emit_prog(r) {
        Some(p) => {
            let b = pike_run(&p, s);
            proof {
                lemma_emit_correct(*r, s@);
            }
            Some(b)
        },
        None => None,
    }
    // ref-end R16.H5v
}
// Hint(1): A5's `lemma_prog_layout` places `emit(r, 0)` at address 0 and `Match` at `clen(r)`; the continuation is that one instruction.
// Hint(2): `lemma_accepts_match` accepts only the empty word, so the split your soundness statement returns must be the whole word; `emit_prog` and `pike_run` already state the program and the answer, so `rexc_match` needs one call of the theorem.
// Reference checks (enabled):
// reference-only: enabled shipped check
fn rexc_match_check() {
    let mut s: Vec<char> = Vec::new();
    s.push('a');
    let res = rexc_match(&Re::Chr('a'), &s);
    assert(s@ =~= seq!['a']);
    assert(res == Some(true));
    let none = rexc_match(&Re::Empty, &s);
    assert(none == Some(false));
}
// end reference checks

} // verus!
