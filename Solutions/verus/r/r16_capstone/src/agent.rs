// Reference Solution.
//! R16 capstone agent file (rung 14: reviewer, co-developer, adversary). A second optimizer
//! for rexc's VM: `shortcut_split_r16` threads every jump and both targets of every split
//! through one jump. Its statement, `lemma_shortcut_split_correct_r16`, is frozen: both
//! directions, from every address. The shipped optimizer holds one planted defect (chapter
//! §8). Snapshot this file under research/R16/ before any contractor edit. The contractor
//! (/contract R16, a fresh session, contract R-v1) may edit only the optimizer (`thru_r16`,
//! `hop_split_r16`, `shortcut_split_r16`) and write the body of
//! `lemma_shortcut_split_correct_r16` and its helper lemmas; the statement, the imports and
//! this header stay. A delivery that weakens the statement fails specfreeze --check R16, and
//! your trust-report must say FAIL on it. Acceptance: scripts/vcheck --gate on this file
//! exits 0 with zero holes, scripts/vaudit reports no finding, and scripts/specfreeze --check
//! R16 reports none.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a5::*;

verus! {

/// Where a thread at address `a` may go at once: through one jump, if `a` holds one;
/// otherwise `a` itself.
pub open spec fn thru_r16(p: Seq<Inst>, a: usize) -> usize {
    if (a as int) < p.len() {
        match p[a as int] {
            Inst::Jmp(b) => b,
            _ => a,
        }
    } else {
        a
    }
}

pub open spec fn hop_split_r16(p: Seq<Inst>, ins: Inst) -> Inst {
    match ins {
        Inst::Jmp(a) => Inst::Jmp(thru_r16(p, a)),
        Inst::Split(x, y) => Inst::Split(thru_r16(p, x), thru_r16(p, y)),
        _ => ins,
    }
}

pub open spec fn shortcut_split_r16(p: Seq<Inst>) -> Seq<Inst> {
    Seq::new(p.len(), |i: int| hop_split_r16(p, p[i]))
}

// item: R16.A1v
// @hole-begin R16.A1v
proof fn lemma_thru_forward_r16(p: Seq<Inst>, a: usize, w: Seq<char>, f: nat) -> (g: nat)
    requires
        accepts(p, a as int, w, f),
    ensures
        g <= f,
        accepts(p, thru_r16(p, a) as int, w, g),
{
    if (a as int) < p.len() && p[a as int] is Jmp {
        lemma_accepts_jmp(p, a as int, w, f);
        (f - 1) as nat
    } else {
        f
    }
}

proof fn lemma_thru_back_r16(p: Seq<Inst>, a: usize, w: Seq<char>, g: nat) -> (f: nat)
    requires
        accepts(p, thru_r16(p, a) as int, w, g),
    ensures
        accepts(p, a as int, w, f),
{
    if (a as int) < p.len() && p[a as int] is Jmp {
        lemma_accepts_jmp(p, a as int, w, g + 1);
        g + 1
    } else {
        g
    }
}

proof fn lemma_to_split_r16(p: Seq<Inst>, pc: int, w: Seq<char>, f: nat) -> (g: nat)
    requires
        accepts(p, pc, w, f),
    ensures
        accepts(shortcut_split_r16(p), pc, w, g),
    decreases f,
{
    let q = shortcut_split_r16(p);
    lemma_accepts_inside(p, pc, w, f);
    match p[pc] {
        Inst::Match => {
            lemma_accepts_match(p, pc, w, f);
            lemma_accepts_match(q, pc, w, 1);
            1
        },
        Inst::Char(c) => {
            lemma_accepts_char(p, pc, w, f);
            let g1 = lemma_to_split_r16(p, pc + 1, w.drop_first(), (f - 1) as nat);
            lemma_accepts_char(q, pc, w, g1 + 1);
            g1 + 1
        },
        Inst::Split(x, y) => {
            lemma_accepts_split(p, pc, w, f);
            let b = if accepts(p, x as int, w, (f - 1) as nat) { x } else { y };
            let f1 = lemma_thru_forward_r16(p, b, w, (f - 1) as nat);
            let g1 = lemma_to_split_r16(p, thru_r16(p, b) as int, w, f1);
            lemma_accepts_split(q, pc, w, g1 + 1);
            g1 + 1
        },
        Inst::Jmp(a) => {
            lemma_accepts_jmp(p, pc, w, f);
            let f1 = lemma_thru_forward_r16(p, a, w, (f - 1) as nat);
            let g1 = lemma_to_split_r16(p, thru_r16(p, a) as int, w, f1);
            lemma_accepts_jmp(q, pc, w, g1 + 1);
            g1 + 1
        },
    }
}

proof fn lemma_from_split_r16(p: Seq<Inst>, pc: int, w: Seq<char>, f: nat) -> (g: nat)
    requires
        accepts(shortcut_split_r16(p), pc, w, f),
    ensures
        accepts(p, pc, w, g),
    decreases f,
{
    let q = shortcut_split_r16(p);
    lemma_accepts_inside(q, pc, w, f);
    match p[pc] {
        Inst::Match => {
            lemma_accepts_match(q, pc, w, f);
            lemma_accepts_match(p, pc, w, 1);
            1
        },
        Inst::Char(c) => {
            lemma_accepts_char(q, pc, w, f);
            let g1 = lemma_from_split_r16(p, pc + 1, w.drop_first(), (f - 1) as nat);
            lemma_accepts_char(p, pc, w, g1 + 1);
            g1 + 1
        },
        Inst::Split(x, y) => {
            lemma_accepts_split(q, pc, w, f);
            let b = if accepts(q, thru_r16(p, x) as int, w, (f - 1) as nat) { x } else { y };
            let g1 = lemma_from_split_r16(p, thru_r16(p, b) as int, w, (f - 1) as nat);
            let g2 = lemma_thru_back_r16(p, b, w, g1);
            lemma_accepts_split(p, pc, w, g2 + 1);
            g2 + 1
        },
        Inst::Jmp(a) => {
            lemma_accepts_jmp(q, pc, w, f);
            let g1 = lemma_from_split_r16(p, thru_r16(p, a) as int, w, (f - 1) as nat);
            let g2 = lemma_thru_back_r16(p, a, w, g1);
            lemma_accepts_jmp(p, pc, w, g2 + 1);
            g2 + 1
        },
    }
}
// @hole-end R16.A1v

pub proof fn lemma_shortcut_split_correct_r16(p: Seq<Inst>, pc: int, w: Seq<char>)
    ensures
        accepts_from(shortcut_split_r16(p), pc, w) == accepts_from(p, pc, w),
{
    // @hole-begin R16.A1v
    if accepts_from(p, pc, w) {
        let f = choose|f: nat| #[trigger] accepts(p, pc, w, f);
        let g = lemma_to_split_r16(p, pc, w, f);
    }
    if accepts_from(shortcut_split_r16(p), pc, w) {
        let f = choose|f: nat| #[trigger] accepts(shortcut_split_r16(p), pc, w, f);
        let g = lemma_from_split_r16(p, pc, w, f);
    }
    // @hole-end R16.A1v
}

} // verus!
