//! RG_A5 — the VM and the emitter (PROVIDED, frozen). Declared by R16, imported by R16 only.
//!
//! Frozen infrastructure, not an exercise (PLAN.md §2.2, §2.5 step 7; DVR4 step 7's
//! reconciliation). The VM: `Inst` (`Char`, `Split`, `Jmp`, `Match`), the fuelled acceptance
//! `accepts` (opaque: use the four one-step lemmas and `lemma_accepts_inside`, never a reveal)
//! and `accepts_from` (some fuel). The emitter: `clen`, `emit` (the code for a regex placed
//! at an address, falling through to the address after it), `prog`, the opaque `code_at`
//! and the layout lemmas of each constructor's code; the exec emitter `emit_into` and
//! `emit_prog`. No correctness lemma of the emitter is here: stating and proving them is
//! R16's work.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;

verus! {

pub enum Inst {
    Char(char),
    Split(usize, usize),
    Jmp(usize),
    Match,
}

/// Fuelled acceptance (one instruction per unit of fuel): some run of at most `fuel` steps from
/// `pc` reaches `Match` with the whole input consumed. `Split` forks the thread, `Jmp` moves
/// it, `Char` consumes one matching char, and a thread outside the program dies.
#[verifier::opaque]
pub open spec fn accepts(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat) -> bool
    decreases fuel,
{
    if fuel == 0 || pc < 0 || pc >= p.len() {
        false
    } else {
        match p[pc] {
            Inst::Char(c) => s.len() > 0 && s[0] == c && accepts(p, pc + 1, s.drop_first(), (fuel - 1) as nat),
            Inst::Split(x, y) => accepts(p, x as int, s, (fuel - 1) as nat) || accepts(p, y as int, s, (fuel - 1) as nat),
            Inst::Jmp(x) => accepts(p, x as int, s, (fuel - 1) as nat),
            Inst::Match => s.len() == 0,
        }
    }
}


/// Some run from `pc` accepts `s` (some fuel suffices).
pub open spec fn accepts_from(p: Seq<Inst>, pc: int, s: Seq<char>) -> bool {
    exists|f: nat| #[trigger] accepts(p, pc, s, f)
}

/// One step of `accepts` at `Char`: one matching character consumed, one unit of fuel spent.
pub proof fn lemma_accepts_char(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat)
    requires
        0 <= pc < p.len(),
        p[pc] is Char,
    ensures
        accepts(p, pc, s, fuel) <==> fuel > 0 && s.len() > 0 && s[0] == p[pc]->Char_0
            && accepts(p, pc + 1, s.drop_first(), (fuel - 1) as nat),
{
    reveal_with_fuel(accepts, 1);
}

/// One step of `accepts` at `Split`: either branch, one unit of fuel spent.
pub proof fn lemma_accepts_split(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat)
    requires
        0 <= pc < p.len(),
        p[pc] is Split,
    ensures
        accepts(p, pc, s, fuel) <==> fuel > 0 && (accepts(p, p[pc]->Split_0 as int, s, (fuel - 1) as nat)
            || accepts(p, p[pc]->Split_1 as int, s, (fuel - 1) as nat)),
{
    reveal_with_fuel(accepts, 1);
}

/// One step of `accepts` at `Jmp`: the target, one unit of fuel spent.
pub proof fn lemma_accepts_jmp(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat)
    requires
        0 <= pc < p.len(),
        p[pc] is Jmp,
    ensures
        accepts(p, pc, s, fuel) <==> fuel > 0 && accepts(p, p[pc]->Jmp_0 as int, s, (fuel - 1) as nat),
{
    reveal_with_fuel(accepts, 1);
}

/// One step of `accepts` at `Match`: the input is used up (and some fuel is left).
pub proof fn lemma_accepts_match(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat)
    requires
        0 <= pc < p.len(),
        p[pc] is Match,
    ensures
        accepts(p, pc, s, fuel) <==> fuel > 0 && s.len() == 0,
{
    reveal_with_fuel(accepts, 1);
}

/// Length of the code for `r`.
pub open spec fn clen(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Empty => 1,
        Re::Eps => 0,
        Re::Chr(_) => 1,
        Re::Alt(a, b) => clen(*a) + clen(*b) + 2,
        Re::Cat(a, b) => clen(*a) + clen(*b),
        Re::Star(a) => clen(*a) + 2,
    }
}

/// The code for `r` placed at address `pc`; it falls through to `pc + clen(r)`.
pub open spec fn emit(r: Re, pc: int) -> Seq<Inst>
    decreases r,
{
    match r {
        Re::Empty => seq![Inst::Jmp(pc as usize)],
        Re::Eps => seq![],
        Re::Chr(c) => seq![Inst::Char(c)],
        Re::Alt(a, b) => {
            let l2 = pc + 1 + clen(*a) + 1;
            let end = l2 + clen(*b);
            seq![Inst::Split((pc + 1) as usize, l2 as usize)] + emit(*a, pc + 1) + seq![
                Inst::Jmp(end as usize),
            ] + emit(*b, l2)
        },
        Re::Cat(a, b) => emit(*a, pc) + emit(*b, pc + clen(*a)),
        Re::Star(a) => {
            let end = pc + clen(*a) + 2;
            seq![Inst::Split((pc + 1) as usize, end as usize)] + emit(*a, pc + 1) + seq![
                Inst::Jmp(pc as usize),
            ]
        },
    }
}

pub proof fn lemma_emit_len(r: Re, pc: int)
    ensures
        emit(r, pc).len() == clen(r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            lemma_emit_len(*a, pc + 1);
            lemma_emit_len(*b, pc + 1 + clen(*a) + 1);
        },
        Re::Cat(a, b) => {
            lemma_emit_len(*a, pc);
            lemma_emit_len(*b, pc + clen(*a));
        },
        Re::Star(a) => {
            lemma_emit_len(*a, pc + 1);
        },
        _ => {},
    }
}

/// `code` sits in `p` at address `pc`.
#[verifier::opaque]
pub open spec fn code_at(p: Seq<Inst>, pc: int, code: Seq<Inst>) -> bool {
    0 <= pc && pc + code.len() <= p.len() && forall|i: int| 0 <= i < code.len() ==> p[pc + i] == #[trigger] code[i]
}

/// The first instruction of a one-instruction code.
pub proof fn lemma_sub_one(p: Seq<Inst>, r: Re, pc: int)
    requires
        code_at(p, pc, emit(r, pc)),
        r is Empty || r is Chr,
    ensures
        p[pc] == emit(r, pc)[0],
        0 <= pc < p.len(),
{
    reveal(code_at);
    assert(p[pc + 0] == emit(r, pc)[0]);
}

/// Code at `pc` splits at a concatenation.
pub proof fn lemma_code_at_add(p: Seq<Inst>, pc: int, x: Seq<Inst>, y: Seq<Inst>)
    requires
        code_at(p, pc, x + y),
    ensures
        0 <= pc,
        pc + x.len() + y.len() <= p.len(),
        code_at(p, pc, x),
        code_at(p, pc + x.len(), y),
{
    reveal(code_at);
    assert forall|i: int| 0 <= i < x.len() implies p[pc + i] == #[trigger] x[i] by {
        assert(p[pc + i] == (x + y)[i]);
    }
    assert forall|i: int| 0 <= i < y.len() implies p[pc + x.len() + i] == #[trigger] y[i] by {
        assert(p[pc + (x.len() + i)] == (x + y)[x.len() + i]);
    }
}

/// A one-instruction code.
pub proof fn lemma_code_at_one(p: Seq<Inst>, pc: int, i: Inst)
    requires
        code_at(p, pc, seq![i]),
    ensures
        0 <= pc < p.len(),
        p[pc] == i,
{
    reveal(code_at);
    assert(p[pc + 0] == seq![i][0]);
}

/// Where the pieces of an `Alt`'s code sit.
pub proof fn lemma_sub_alt(p: Seq<Inst>, a: Re, b: Re, pc: int)
    requires
        code_at(p, pc, emit(Re::Alt(Box::new(a), Box::new(b)), pc)),
    ensures
        0 <= pc,
        pc + clen(a) + clen(b) + 2 <= p.len(),
        p[pc] == Inst::Split((pc + 1) as usize, (pc + 2 + clen(a)) as usize),
        code_at(p, pc + 1, emit(a, pc + 1)),
        p[pc + 1 + clen(a)] == Inst::Jmp((pc + 2 + clen(a) + clen(b)) as usize),
        code_at(p, pc + 2 + clen(a), emit(b, pc + 2 + clen(a))),
{
    let l2 = pc + 2 + clen(a);
    let ca = emit(a, pc + 1);
    let cb = emit(b, l2);
    let h = seq![Inst::Split((pc + 1) as usize, l2 as usize)];
    let j = seq![Inst::Jmp((l2 + clen(b)) as usize)];
    lemma_emit_len(a, pc + 1);
    lemma_emit_len(b, l2);
    assert(emit(Re::Alt(Box::new(a), Box::new(b)), pc) == h + ca + j + cb);
    lemma_code_at_add(p, pc, h + ca + j, cb);
    lemma_code_at_add(p, pc, h + ca, j);
    lemma_code_at_add(p, pc, h, ca);
    lemma_code_at_one(p, pc, h[0]);
    lemma_code_at_one(p, pc + 1 + clen(a), j[0]);
    assert(seq![h[0]] == h);
    assert(seq![j[0]] == j);
}

/// Where the pieces of a `Cat`'s code sit.
pub proof fn lemma_sub_cat(p: Seq<Inst>, a: Re, b: Re, pc: int)
    requires
        code_at(p, pc, emit(Re::Cat(Box::new(a), Box::new(b)), pc)),
    ensures
        0 <= pc,
        pc + clen(a) + clen(b) <= p.len(),
        code_at(p, pc, emit(a, pc)),
        code_at(p, pc + clen(a), emit(b, pc + clen(a))),
{
    lemma_emit_len(a, pc);
    lemma_emit_len(b, pc + clen(a));
    lemma_code_at_add(p, pc, emit(a, pc), emit(b, pc + clen(a)));
}

/// Where the pieces of a `Star`'s code sit.
pub proof fn lemma_sub_star(p: Seq<Inst>, a: Re, pc: int)
    requires
        code_at(p, pc, emit(Re::Star(Box::new(a)), pc)),
    ensures
        0 <= pc,
        pc + clen(a) + 2 <= p.len(),
        p[pc] == Inst::Split((pc + 1) as usize, (pc + clen(a) + 2) as usize),
        code_at(p, pc + 1, emit(a, pc + 1)),
        p[pc + 1 + clen(a)] == Inst::Jmp(pc as usize),
{
    let ca = emit(a, pc + 1);
    let h = seq![Inst::Split((pc + 1) as usize, (pc + clen(a) + 2) as usize)];
    let j = seq![Inst::Jmp(pc as usize)];
    lemma_emit_len(a, pc + 1);
    assert(emit(Re::Star(Box::new(a)), pc) == h + ca + j);
    lemma_code_at_add(p, pc, h + ca, j);
    lemma_code_at_add(p, pc, h, ca);
    lemma_code_at_one(p, pc, h[0]);
    lemma_code_at_one(p, pc + 1 + clen(a), j[0]);
    assert(seq![h[0]] == h);
    assert(seq![j[0]] == j);
}

/// An accepting thread has fuel left and its address lies inside the program.
pub proof fn lemma_accepts_inside(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat)
    requires
        accepts(p, pc, s, fuel),
    ensures
        fuel > 0,
        0 <= pc < p.len(),
{
    reveal_with_fuel(accepts, 1);
}


/// The whole program for `r`: its code at 0, then `Match`.
pub open spec fn prog(r: Re) -> Seq<Inst> {
    emit(r, 0).push(Inst::Match)
}

// ---------------------------------------------------------------------------------------------
// Exec emitter
// ---------------------------------------------------------------------------------------------

/// `clen` with overflow detection.
pub fn clen_checked(r: &Re) -> (n: Option<usize>)
    ensures
        n is Some ==> n->Some_0 as nat == clen(*r),
        n is None ==> clen(*r) > usize::MAX,
    decreases r,
{
    match r {
        Re::Empty => Some(1),
        Re::Eps => Some(0),
        Re::Chr(_) => Some(1),
        Re::Alt(a, b) => match (clen_checked(a), clen_checked(b)) {
            (Some(x), Some(y)) => match x.checked_add(y) {
                Some(z) => z.checked_add(2),
                None => None,
            },
            _ => None,
        },
        Re::Cat(a, b) => match (clen_checked(a), clen_checked(b)) {
            (Some(x), Some(y)) => x.checked_add(y),
            _ => None,
        },
        Re::Star(a) => match clen_checked(a) {
            Some(x) => x.checked_add(2),
            None => None,
        },
    }
}

proof fn lemma_app3(o: Seq<Inst>, x: Seq<Inst>, y: Seq<Inst>)
    ensures
        (o + x) + y == o + (x + y),
{
    assert((o + x) + y =~= o + (x + y));
}

proof fn lemma_push(o: Seq<Inst>, i: Inst)
    ensures
        o.push(i) == o + seq![i],
{
    assert(o.push(i) =~= o + seq![i]);
}

/// Append the code for `r` at address `out.len()`.
pub fn emit_into(r: &Re, out: &mut Vec<Inst>)
    requires
        old(out).len() + clen(*r) < usize::MAX,
    ensures
        final(out)@ == old(out)@ + emit(*r, old(out).len() as int),
    decreases r,
{
    let ghost o = out@;
    let pc = out.len();
    match r {
        Re::Empty => {
            out.push(Inst::Jmp(pc));
            proof { lemma_push(o, Inst::Jmp(pc)); }
        },
        Re::Eps => {
            assert(o + emit(*r, pc as int) =~= o);
        },
        Re::Chr(c) => {
            out.push(Inst::Char(*c));
            proof { lemma_push(o, Inst::Char(*c)); }
        },
        Re::Alt(a, b) => {
            let la = clen_checked(a).unwrap();
            let lb = clen_checked(b).unwrap();
            let l2 = pc + 1 + la + 1;
            let end = l2 + lb;
            let pc1 = pc + 1;
            let ghost h = seq![Inst::Split(pc1, l2)];
            let ghost j = seq![Inst::Jmp(end)];
            let ghost ca = emit(**a, pc + 1 as int);
            let ghost cb = emit(**b, l2 as int);
            out.push(Inst::Split(pc1, l2));
            proof { lemma_push(o, Inst::Split(pc1, l2)); }
            emit_into(a, out);
            proof { lemma_emit_len(**a, pc + 1 as int); }
            let ghost o2 = out@;
            out.push(Inst::Jmp(end));
            proof { lemma_push(o2, Inst::Jmp(end)); }
            emit_into(b, out);
            proof {
                lemma_app3(o, h, ca);
                lemma_app3(o, h + ca, j);
                lemma_app3(o, h + ca + j, cb);
                assert(emit(*r, pc as int) == h + ca + j + cb);
            }
        },
        Re::Cat(a, b) => {
            emit_into(a, out);
            proof { lemma_emit_len(**a, pc as int); }
            emit_into(b, out);
            proof { lemma_app3(o, emit(**a, pc as int), emit(**b, pc + clen(**a))); }
        },
        Re::Star(a) => {
            let la = clen_checked(a).unwrap();
            let end = pc + la + 2;
            let pc1 = pc + 1;
            let ghost h = seq![Inst::Split(pc1, end)];
            let ghost j = seq![Inst::Jmp(pc)];
            let ghost ca = emit(**a, pc + 1 as int);
            out.push(Inst::Split(pc1, end));
            proof { lemma_push(o, Inst::Split(pc1, end)); }
            emit_into(a, out);
            proof { lemma_emit_len(**a, pc + 1 as int); }
            let ghost o2 = out@;
            out.push(Inst::Jmp(pc));
            proof {
                lemma_push(o2, Inst::Jmp(pc));
                lemma_app3(o, h, ca);
                lemma_app3(o, h + ca, j);
                assert(emit(*r, pc as int) == h + ca + j);
            }
        },
    }
}

/// The whole program, or `None` when it would not fit the address space.
pub fn emit_prog(r: &Re) -> (out: Option<Vec<Inst>>)
    ensures
        out is Some ==> out->Some_0@ == prog(*r) && clen(*r) + 1 < usize::MAX,
{
    match clen_checked(r) {
        Some(n) => {
            if n >= usize::MAX - 1 {
                return None;
            }
            let mut v: Vec<Inst> = Vec::new();
            emit_into(r, &mut v);
            v.push(Inst::Match);
            assert(v@ =~= prog(*r));
            Some(v)
        },
        None => None,
    }
}

} // verus!
