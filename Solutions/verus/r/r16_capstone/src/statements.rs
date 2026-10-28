// Reference Solution.
//! # R16 — Capstone: the statements (exercises)
//!
//! The file in which you state what it means for the emitter to be correct. You write the
//! two definitions below (H1), have them reviewed statement-only (`/review R16
//! --statements`), then commit them: from that commit on they are frozen. The registry
//! lists this file under R16's `statements` (pending until your commit),
//! `scripts/specfreeze --check R16` compares every later change with your committed
//! statements, and Lab γ's crate tasks unpack only after it.
//!
//! The paired statement file is dafny/R/R16_Capstone/std/R16_Statements.dfy. The proofs
//! (H2, H3), the whole-program theorem and `rexc_match` (H5) are in lib.rs; nothing else
//! goes in this file.
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a5::*;

verus! {

// item: R16.H1v
// pair: R16.H1d
/// **H1.** State the emitter's two correctness facts for the code of `r` placed at `pc`
/// inside a larger program `p`, with whatever code follows it left free. Completeness: when
/// `r` matches `u` and the code after `r`'s accepts `v` from its first address, the code of
/// `r` accepts `u + v` from `pc`. Soundness, the converse: when `r`'s code accepts `w` from
/// `pc`, `w` splits into a part `r` matches and a rest the following code accepts. Use A5's
/// `code_at`, `emit`, `clen` and `accepts_from` (never the fuelled `accepts`). Replace each
/// `uninterp` declaration by an `open spec fn` with a body. Why must neither statement say
/// that the program ends after `r`'s code, and which bound on `pc` do `emit`'s `usize`
/// targets need?
pub open spec fn emit_complete_statement(p: Seq<Inst>, r: Re, pc: int, u: Seq<char>, v: Seq<char>) -> bool {
    code_at(p, pc, emit(r, pc)) && pc + clen(r) < usize::MAX && matches(r, u)
        && accepts_from(p, pc + clen(r), v) ==> accepts_from(p, pc, u + v)
}

pub open spec fn emit_sound_statement(p: Seq<Inst>, r: Re, pc: int, w: Seq<char>) -> bool {
    code_at(p, pc, emit(r, pc)) && pc + clen(r) < usize::MAX && accepts_from(p, pc, w)
        ==> exists|k: int|
        0 <= k <= w.len() && #[trigger] matches(r, w.subrange(0, k))
            && accepts_from(p, pc + clen(r), w.subrange(k, w.len() as int))
}
// Hint(1): each statement is one implication over all programs `p` that hold `emit(r, pc)` at `pc`; the continuation is whatever starts at `pc + clen(r)`, and `emit` casts addresses to `usize`.
// Hint(2): completeness concatenates (`u + v`); soundness picks a split point `k` of `w` with `0 <= k <= w.len()`, `r` matching `w.subrange(0, k)` and the continuation accepting the rest.
// cfree: { true }

} // verus!
