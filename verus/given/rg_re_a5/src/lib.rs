//! RG_A5 — the VM, the emitter, the Pike runner and the re-supplied front end (PROVIDED,
//! frozen). Declared by R16, imported by R16 only.
//!
//! Do not open this crate before R09 is done: its last section re-supplies, complete and
//! proved, R09's exec parser and lowering, including the answers to R09's holes H1v
//! (`parse_counted`), H2v (`class_items`) and H3v (`repeat_expansion_budget_r09`). Finish
//! R09's holes and record their first tries (`scripts/firsttry.sh R09 --check`) first. It
//! imports A1b and A4, whose headers name the earlier answers they hold.
//!
//! Frozen infrastructure, not an exercise (PLAN.md §2.2, §2.4, §2.5 step 7). The VM: `Inst`
//! (`Char`, `Split`, `Jmp`, `Match`), the fuelled acceptance `accepts` (opaque: use the four
//! one-step lemmas and `lemma_accepts_inside`, never a reveal) and `accepts_from` (some
//! fuel). The emitter: `clen`, `emit` (the code for a regex placed at an address, falling
//! through to the address after it), `prog`, the opaque `code_at` and the layout lemmas of
//! each constructor's code; the exec emitter `emit_into` and `emit_prog`. The Pike runner
//! `pike_run` (`b == accepts_from(p@, 0, s@)`). The front end `frontend_r09` (R09's parser,
//! cost check and lowering). No correctness lemma of the emitter is here: stating and
//! proving them is R16's work.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a3::*;

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

/// The layout of the whole program: `r`'s code at 0, then `Match` at `clen(r)`.
pub proof fn lemma_prog_layout(r: Re)
    ensures
        prog(r).len() == clen(r) + 1,
        code_at(prog(r), 0, emit(r, 0)),
        prog(r)[clen(r) as int] == Inst::Match,
{
    reveal(code_at);
    lemma_emit_len(r, 0);
    assert forall|i: int| 0 <= i < emit(r, 0).len() implies prog(r)[0 + i] == #[trigger] emit(r, 0)[i] by {}
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
        out is None ==> clen(*r) + 1 >= usize::MAX,
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

// =============================================================================
// The Pike runner (re-supplied from the DVR0 spike, re-proved over the opaque `accepts`)
// =============================================================================

/// Some run from `pc` accepts `t`.
pub open spec fn live(p: Seq<Inst>, pc: int, t: Seq<char>) -> bool {
    exists|f: nat| #[trigger] accepts(p, pc, t, f)
}

/// A thread at `v` on input `t` is good: if it can accept, the whole run accepts (`g`).
pub open spec fn thread_ok(p: Seq<Inst>, v: int, t: Seq<char>, g: bool) -> bool {
    live(p, v, t) ==> g
}

/// `v`'s epsilon successors (in range) are in the set.
pub open spec fn succ_closed(p: Seq<Inst>, set: Seq<bool>, v: int) -> bool {
    match p[v] {
        Inst::Split(x, y) => (x < p.len() ==> set[x as int]) && (y < p.len() ==> set[y as int]),
        Inst::Jmp(x) => x < p.len() ==> set[x as int],
        _ => true,
    }
}

/// The thread list holds exactly the set's members.
pub open spec fn list_matches(p: Seq<Inst>, set: Seq<bool>, list: Seq<usize>) -> bool {
    &&& set.len() == p.len()
    &&& forall|k: int| 0 <= k < list.len() ==> (#[trigger] list[k]) < p.len() && set[list[k] as int]
    &&& forall|v: int| 0 <= v < p.len() && #[trigger] set[v] ==> exists|k: int| 0 <= k < list.len() && list[k] == v
}

pub open spec fn count_false(s: Seq<bool>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        count_false(s.drop_last()) + if s.last() { 0nat } else { 1nat }
    }
}

proof fn lemma_count_update(s: Seq<bool>, i: int)
    requires
        0 <= i < s.len(),
        !s[i],
    ensures
        count_false(s.update(i, true)) + 1 == count_false(s),
    decreases s.len(),
{
    let u = s.update(i, true);
    if i == s.len() - 1 {
        assert(u.drop_last() =~= s.drop_last());
    } else {
        assert(u.drop_last() =~= s.drop_last().update(i, true));
        lemma_count_update(s.drop_last(), i);
    }
}

/// Add the thread `pc` and its epsilon closure (Pike's `addthread`).
fn add_thread(
    p: &Vec<Inst>,
    pc: usize,
    set: &mut Vec<bool>,
    list: &mut Vec<usize>,
    Ghost(t): Ghost<Seq<char>>,
    Ghost(g): Ghost<bool>,
)
    requires
        pc < p.len(),
        list_matches(p@, old(set)@, old(list)@),
        thread_ok(p@, pc as int, t, g),
        forall|v: int| 0 <= v < p.len() && old(set)@[v] ==> thread_ok(p@, v, t, g),
    ensures
        list_matches(p@, final(set)@, final(list)@),
        final(set)@[pc as int],
        forall|v: int| 0 <= v < p.len() && old(set)@[v] ==> final(set)@[v],
        forall|v: int| 0 <= v < p.len() && final(set)@[v] ==> thread_ok(p@, v, t, g),
        forall|v: int|
            0 <= v < p.len() && final(set)@[v] && !old(set)@[v] ==> succ_closed(p@, final(set)@, v),
        count_false(final(set)@) <= count_false(old(set)@),
    decreases count_false(old(set)@),
{
    proof {
        reveal(accepts);
    }
    if set[pc] {
        return;
    }
    proof {
        lemma_count_update(set@, pc as int);
    }
    let ghost s0 = set@;
    set.set(pc, true);
    list.push(pc);
    proof {
        assert(list@[list@.len() - 1] == pc);
        assert forall|v: int| 0 <= v < p.len() && #[trigger] set@[v] implies exists|k: int|
            0 <= k < list@.len() && list@[k] == v by {
            if v != pc {
                let k = choose|k: int| 0 <= k < old(list)@.len() && old(list)@[k] == v;
                assert(list@[k] == v);
            }
        }
    }
    let plen = p.len();
    match &p[pc] {
        Inst::Split(x, y) => {
            let x = *x;
            let y = *y;
            let ghost s1 = set@;
            if x < plen {
                proof {
                    if live(p@, x as int, t) {
                        let f = choose|f: nat| #[trigger] accepts(p@, x as int, t, f);
                        assert(accepts(p@, pc as int, t, f + 1));
                    }
                }
                add_thread(p, x, set, list, Ghost(t), Ghost(g));
            }
            let ghost s2 = set@;
            if y < plen {
                proof {
                    if live(p@, y as int, t) {
                        let f = choose|f: nat| #[trigger] accepts(p@, y as int, t, f);
                        assert(accepts(p@, pc as int, t, f + 1));
                    }
                }
                add_thread(p, y, set, list, Ghost(t), Ghost(g));
            }
            proof {
                assert forall|v: int|
                    0 <= v < p.len() && set@[v] && !old(set)@[v] implies succ_closed(p@, set@, v) by {
                    if v != pc && !s1[v] && s2[v] {
                        assert(succ_closed(p@, s2, v));
                    }
                }
            }
        },
        Inst::Jmp(x) => {
            let x = *x;
            let ghost s1 = set@;
            if x < plen {
                proof {
                    if live(p@, x as int, t) {
                        let f = choose|f: nat| #[trigger] accepts(p@, x as int, t, f);
                        assert(accepts(p@, pc as int, t, f + 1));
                    }
                }
                add_thread(p, x, set, list, Ghost(t), Ghost(g));
            }
        },
        _ => {},
    }
}

/// In a closed set, a live thread reaches a live `Char` or `Match` thread of the set.
proof fn lemma_closure(p: Seq<Inst>, set: Seq<bool>, v: int, t: Seq<char>, f: nat) -> (res: (int, nat))
    requires
        set.len() == p.len(),
        0 <= v < p.len(),
        set[v],
        forall|w: int| 0 <= w < p.len() && set[w] ==> #[trigger] succ_closed(p, set, w),
        accepts(p, v, t, f),
    ensures
        0 <= res.0 < p.len(),
        set[res.0],
        p[res.0] is Char || p[res.0] is Match,
        accepts(p, res.0, t, res.1),
    decreases f,
{
    reveal(accepts);
    assert(succ_closed(p, set, v));
    match p[v] {
        Inst::Split(x, y) => {
            if accepts(p, x as int, t, (f - 1) as nat) {
                assert(x < p.len());
                lemma_closure(p, set, x as int, t, (f - 1) as nat)
            } else {
                assert(accepts(p, y as int, t, (f - 1) as nat));
                assert(y < p.len());
                lemma_closure(p, set, y as int, t, (f - 1) as nat)
            }
        },
        Inst::Jmp(x) => {
            assert(accepts(p, x as int, t, (f - 1) as nat));
            assert(x < p.len());
            lemma_closure(p, set, x as int, t, (f - 1) as nat)
        },
        _ => (v, f),
    }
}

fn falses(n: usize) -> (v: Vec<bool>)
    ensures
        v@.len() == n,
        forall|i: int| 0 <= i < n ==> !(#[trigger] v@[i]),
{
    let mut v: Vec<bool> = Vec::new();
    while v.len() < n
        invariant
            v@.len() <= n,
            forall|i: int| 0 <= i < v@.len() ==> !(#[trigger] v@[i]),
        decreases n - v.len(),
    {
        v.push(false);
    }
    v
}

/// The Pike VM: decides whether some run from address 0 accepts `s`.
#[verifier::loop_isolation(false)]
pub fn pike_run(p: &Vec<Inst>, s: &Vec<char>) -> (b: bool)
    ensures
        b == accepts_from(p@, 0, s@),
{
    proof {
        reveal(accepts);
    }
    let plen = p.len();
    let n = s.len();
    let ghost g = live(p@, 0, s@);
    if plen == 0 {
        assert(!g);
        return false;
    }
    let mut cset = falses(plen);
    let mut clist: Vec<usize> = Vec::new();
    assert(s@.subrange(0, n as int) =~= s@);
    add_thread(p, 0, &mut cset, &mut clist, Ghost(s@), Ghost(g));
    let mut i: usize = 0;
    while i < n
        invariant
            i <= n,
            list_matches(p@, cset@, clist@),
            forall|v: int| 0 <= v < plen && cset@[v] ==> thread_ok(p@, v, s@.subrange(i as int, n as int), g),
            g ==> exists|v: int| 0 <= v < plen && cset@[v] && live(p@, v, s@.subrange(i as int, n as int)),
            forall|v: int| 0 <= v < plen && cset@[v] ==> succ_closed(p@, cset@, v),
        decreases n - i,
    {
        let ghost t = s@.subrange(i as int, n as int);
        let ghost t1 = s@.subrange(i + 1, n as int);
        assert(t.drop_first() =~= t1);
        let c = s[i];
        let mut nset = falses(plen);
        let mut nlist: Vec<usize> = Vec::new();
        let mut k: usize = 0;
        while k < clist.len()
            invariant
                k <= clist.len(),
                list_matches(p@, nset@, nlist@),
                forall|v: int| 0 <= v < plen && nset@[v] ==> thread_ok(p@, v, t1, g),
                forall|v: int| 0 <= v < plen && nset@[v] ==> succ_closed(p@, nset@, v),
                forall|j: int|
                    0 <= j < k ==> match #[trigger] p@[clist@[j] as int] {
                        Inst::Char(d) => d == c && clist@[j] + 1 < plen ==> nset@[clist@[j] + 1],
                        _ => true,
                    },
            decreases clist.len() - k,
        {
            let q = clist[k];
            match &p[q] {
                Inst::Char(d) => {
                    if *d == c && q + 1 < plen {
                        proof {
                            assert(thread_ok(p@, q as int, t, g));
                            if live(p@, (q + 1) as int, t1) {
                                let f = choose|f: nat| #[trigger] accepts(p@, (q + 1) as int, t1, f);
                                assert(accepts(p@, q as int, t, f + 1));
                            }
                        }
                        add_thread(p, q + 1, &mut nset, &mut nlist, Ghost(t1), Ghost(g));
                    }
                },
                _ => {},
            }
            k = k + 1;
        }
        proof {
            if g {
                let v = choose|v: int| 0 <= v < plen && cset@[v] && live(p@, v, t);
                let f = choose|f: nat| #[trigger] accepts(p@, v, t, f);
                let (q, fq) = lemma_closure(p@, cset@, v, t, f);
                let j = choose|j: int| 0 <= j < clist@.len() && clist@[j] == q;
                assert(match p@[clist@[j] as int] {
                    Inst::Char(d) => d == c && clist@[j] + 1 < plen ==> nset@[clist@[j] + 1],
                    _ => true,
                });
                assert(accepts(p@, q + 1, t1, (fq - 1) as nat));
                assert(live(p@, q + 1, t1));
            }
        }
        cset = nset;
        clist = nlist;
        i = i + 1;
    }
    let ghost t = s@.subrange(n as int, n as int);
    assert(t =~= Seq::<char>::empty());
    let mut k: usize = 0;
    while k < clist.len()
        invariant
            k <= clist.len(),
            forall|j: int| 0 <= j < k ==> !(#[trigger] p@[clist@[j] as int] is Match),
        decreases clist.len() - k,
    {
        let q = clist[k];
        if let Inst::Match = &p[q] {
            proof {
                assert(accepts(p@, q as int, t, 1));
                assert(thread_ok(p@, q as int, t, g));
            }
            return true;
        }
        k = k + 1;
    }
    proof {
        if g {
            let v = choose|v: int| 0 <= v < plen && cset@[v] && live(p@, v, t);
            let f = choose|f: nat| #[trigger] accepts(p@, v, t, f);
            let (q, fq) = lemma_closure(p@, cset@, v, t, f);
            let j = choose|j: int| 0 <= j < clist@.len() && clist@[j] == q;
            assert(!(p@[clist@[j] as int] is Match));
        }
    }
    false
}

} // verus!

// =============================================================================
// The front end (re-supplied from R09: the parser, the cost check and the lowering)
// =============================================================================

verus! {

// The logical size of a lowering, computed over the syntax tree before any
// expansion is built.
pub open spec fn range_nodes_r09(lo: u32, hi: u32) -> nat {
    if range_valid(lo, hi) {
        (2 * ((hi as int) - (lo as int)) + 1) as nat
    } else {
        1
    }
}

pub open spec fn class_nodes_r09(xs: Seq<(u32, u32)>) -> nat
    decreases xs.len(),
{
    if xs.len() == 0 {
        1
    } else {
        1 + range_nodes_r09(xs[0].0, xs[0].1) + class_nodes_r09(xs.drop_first())
    }
}

pub open spec fn lowering_nodes_r09(t: Syn) -> nat
    decreases t,
{
    match t.node {
        SyntaxKind::Eps | SyntaxKind::Chr(_) => 1,
        SyntaxKind::Class(cc) => class_nodes_r09(cc.ranges_spec()),
        SyntaxKind::Alt(a, b) | SyntaxKind::Cat(a, b) => 1 + lowering_nodes_r09(*a) + lowering_nodes_r09(*b),
        SyntaxKind::Star(a) => 1 + lowering_nodes_r09(*a),
        SyntaxKind::Plus(a) => 2 + 2 * lowering_nodes_r09(*a),
        SyntaxKind::Opt(a) => 2 + lowering_nodes_r09(*a),
        SyntaxKind::Group(a) => lowering_nodes_r09(*a),
        SyntaxKind::RepRange(a, n, m) => 3 + (n as nat) * (lowering_nodes_r09(*a) + 1) + ((m as nat - n as nat) as nat) * (lowering_nodes_r09(*a) + 3),
    }
}

proof fn lemma_copies_nodes_r09(r: Re, k: nat)
    ensures
        node_count(copies(r, k)) == 1 + k * (node_count(r) + 1),
    decreases k,
{
    reveal_with_fuel(node_count, 2);
    reveal_with_fuel(copies, 2);
    let b = node_count(r) as int;
    if k > 0 {
        let km = (k - 1) as nat;
        lemma_copies_nodes_r09(r, km);
        let total = node_count(copies(r, k)) as int;
        let child = node_count(copies(r, km)) as int;
        assert(total == 1 + b + child);
        assert(total == 1 + k * (b + 1)) by (nonlinear_arith)
            requires
                total == 1 + b + child,
                child == 1 + km * (b + 1),
                k == km + 1,
        ;
    } else {
        assert(1 + k * (b + 1) == 1) by (nonlinear_arith)
            requires
                k == 0,
        ;
    }
}

proof fn lemma_optional_nodes_r09(r: Re, k: nat)
    ensures
        node_count(copies_up_to(r, k)) == 1 + k * (node_count(r) + 3),
    decreases k,
{
    reveal_with_fuel(node_count, 3);
    reveal_with_fuel(copies_up_to, 2);
    let b = node_count(r) as int;
    if k > 0 {
        let km = (k - 1) as nat;
        lemma_optional_nodes_r09(r, km);
        let total = node_count(copies_up_to(r, k)) as int;
        let child = node_count(copies_up_to(r, km)) as int;
        assert(total == 3 + b + child);
        assert(total == 1 + k * (b + 3)) by (nonlinear_arith)
            requires
                total == 3 + b + child,
                child == 1 + km * (b + 3),
                k == km + 1,
        ;
    } else {
        assert(1 + k * (b + 3) == 1) by (nonlinear_arith)
            requires
                k == 0,
        ;
    }
}

proof fn lemma_range_nodes_r09(lo: u32, hi: u32)
    requires
        range_valid(lo, hi),
    ensures
        node_count(range_re(lo, hi)) == range_nodes_r09(lo, hi),
    decreases hi - lo,
{
    reveal_with_fuel(node_count, 2);
    if lo < hi {
        lemma_range_nodes_r09((lo + 1) as u32, hi);
    }
}

proof fn lemma_class_nodes_r09(xs: Seq<(u32, u32)>)
    requires
        class_valid(xs),
    ensures
        node_count(class_re(xs)) == class_nodes_r09(xs),
    decreases xs.len(),
{
    if xs.len() > 0 {
        assert forall|i: int| 0 <= i < xs.drop_first().len() implies range_valid(xs.drop_first()[i].0, xs.drop_first()[i].1) by {
            assert(xs.drop_first()[i] == xs[i + 1]);
        }
        lemma_range_nodes_r09(xs[0].0, xs[0].1);
        lemma_class_nodes_r09(xs.drop_first());
    }
}

pub proof fn lemma_lowering_nodes_r09(t: Syn, len: nat)
    requires
        wf(t, len),
    ensures
        node_count(lower(t)) == lowering_nodes_r09(t),
    decreases t,
{
    reveal_with_fuel(node_count, 3);
    match t.node {
        SyntaxKind::Eps | SyntaxKind::Chr(_) => {},
        SyntaxKind::Class(cc) => {
            lemma_class_nodes_r09(cc.ranges_spec());
        },
        SyntaxKind::Alt(a, b) | SyntaxKind::Cat(a, b) => {
            lemma_lowering_nodes_r09(*a, len);
            lemma_lowering_nodes_r09(*b, len);
        },
        SyntaxKind::Star(a) | SyntaxKind::Plus(a) | SyntaxKind::Opt(a) | SyntaxKind::Group(a) => {
            lemma_lowering_nodes_r09(*a, len);
        },
        SyntaxKind::RepRange(a, n, m) => {
            lemma_lowering_nodes_r09(*a, len);
            lemma_copies_nodes_r09(lower(*a), n as nat);
            lemma_optional_nodes_r09(lower(*a), (m as nat - n as nat) as nat);
        },
    }
}

} // verus!

// The parser over positioned A3. Its contracts are safety and the literal
// guarantee; the grammar's fidelity is exercised by tools/R09/check_frontend.py.
use rg_re_a2::*;

verus! {

pub open spec fn no_special_from(s: Seq<char>, i: int) -> bool {
    forall|k: int| i <= k < s.len() ==> !is_meta(s[k])
}

pub proof fn lemma_literal_append_r09(a: Re, u: Seq<char>, c: char)
    requires
        matches(a, u),
    ensures
        matches(Re::Cat(Box::new(a), Box::new(Re::Chr(c))), u + seq![c]),
{
    let w = u + seq![c];
    reveal_with_fuel(matches, 2);
    assert(w.subrange(0, u.len() as int) =~= u);
    assert(w.subrange(u.len() as int, w.len() as int) =~= seq![c]);
    assert(exists|i: int| 0 <= i <= w.len() && matches(a, #[trigger] w.subrange(0, i)) && matches(Re::Chr(c), w.subrange(i, w.len() as int))) by {
        let i = u.len() as int;
        assert(matches(a, w.subrange(0, i)));
        assert(matches(Re::Chr(c), w.subrange(i, w.len() as int)));
    }
}

pub open spec fn counted_node(x: Syn, n: nat, m: nat, k: int) -> Syn {
    Syn { span: Span { lo: x.span.lo, hi: k as usize }, node: SyntaxKind::RepRange(Box::new(x), n as u32, m as u32) }
}

/// The parser around the holes: four mutually recursive functions, each
/// propagating a failure with `?`. Their contracts are safety (spans nest, an
/// error position is in range) plus the literal guarantee: an input with no
/// special character parses, spans the whole input, matches itself and has the
/// printed size. `parse_post` calls H1's `parse_counted`; `parse_atom` calls
/// H2's `class_items`; neither call needs more than their contracts.
pub fn parse_alt(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i <= s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        no_special_from(s@, i as int) ==> res is Ok && res->Ok_0.1 == s.len() && matches(lower(res->Ok_0.0), s@.subrange(i as int, s.len() as int)) && lowering_nodes_r09(res->Ok_0.0) == (if i == s.len() { 1int } else { 2 * (s.len() - i) - 1 }),
    decreases s.len() - i, 3nat,
{
    let (mut x, mut j) = parse_cat(s, i)?;
    while j < s.len() && s[j] == '|'
        invariant
            i <= j <= s.len(),
            wf(x, s.len() as nat),
            x.span.lo == i,
            x.span.hi == j,
            no_special_from(s@, i as int) ==> j == s.len() && matches(lower(x), s@.subrange(i as int, s.len() as int)) && lowering_nodes_r09(x) == (if i == s.len() { 1int } else { 2 * (s.len() - i) - 1 }),
        decreases s.len() - j,
    {
        let (y, k) = parse_cat(s, j + 1)?;
        x = Syn { node: SyntaxKind::Alt(Box::new(x), Box::new(y)), span: Span { lo: i, hi: k } };
        j = k;
    }
    Ok((x, j))
}

pub fn parse_cat(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i <= s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        no_special_from(s@, i as int) ==> res is Ok && res->Ok_0.1 == s.len() && matches(lower(res->Ok_0.0), s@.subrange(i as int, s.len() as int)) && lowering_nodes_r09(res->Ok_0.0) == (if i == s.len() { 1int } else { 2 * (s.len() - i) - 1 }),
    decreases s.len() - i, 2nat,
{
    let mut x = Syn { node: SyntaxKind::Eps, span: Span { lo: i, hi: i } };
    let mut j = i;
    let mut first = true;
    while j < s.len() && s[j] != ')' && s[j] != '|'
        invariant
            i <= j <= s.len(),
            wf(x, s.len() as nat),
            x.span.lo == i,
            x.span.hi == j,
            first <==> j == i,
            no_special_from(s@, i as int) ==> no_special_from(s@, j as int) && matches(lower(x), s@.subrange(i as int, j as int)) && lowering_nodes_r09(x) == (if j == i { 1int } else { 2 * (j - i) - 1 }),
        decreases s.len() - j,
    {
        let (y, k) = parse_post(s, j)?;
        proof {
            if no_special_from(s@, i as int) {
                reveal_with_fuel(lower, 2);
                reveal_with_fuel(lowering_nodes_r09, 2);
                assert(y == (Syn { node: SyntaxKind::Chr(s@[j as int]), span: Span { lo: j, hi: (j + 1) as usize } }) && k == j + 1);
                assert(s@.subrange(i as int, j + 1) =~= s@.subrange(i as int, j as int) + seq![s@[j as int]]);
                if first {
                    assert(s@.subrange(i as int, k as int) =~= seq![s@[j as int]]);
                    reveal_with_fuel(matches, 2);
                } else {
                    lemma_literal_append_r09(lower(x), s@.subrange(i as int, j as int), s@[j as int]);
                }
            }
        }
        x = if first {
            y
        } else {
            Syn { node: SyntaxKind::Cat(Box::new(x), Box::new(y)), span: Span { lo: i, hi: k } }
        };
        proof {
            if no_special_from(s@, i as int) {
                assert(no_special_from(s@, k as int));
                reveal_with_fuel(lower, 2);
                reveal_with_fuel(lowering_nodes_r09, 2);
                assert(matches(lower(x), s@.subrange(i as int, k as int)));
            }
        }
        first = false;
        j = k;
    }
    Ok((x, j))
}

pub fn parse_post(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i < s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        res is Ok ==> res->Ok_0.1 > i,
        no_special_from(s@, i as int) ==> res == Ok::<(Syn, usize), PErr>((Syn { node: SyntaxKind::Chr(s@[i as int]), span: Span { lo: i, hi: (i + 1) as usize } }, (i + 1) as usize)),
    decreases s.len() - i, 1nat,
{
    let (mut x, mut j) = parse_atom(s, i)?;
    while j < s.len() && (s[j] == '*' || s[j] == '+' || s[j] == '?' || s[j] == '{')
        invariant
            i < j <= s.len(),
            wf(x, s.len() as nat),
            x.span.lo == i,
            x.span.hi == j,
            no_special_from(s@, i as int) ==> x == (Syn { node: SyntaxKind::Chr(s@[i as int]), span: Span { lo: i, hi: (i + 1) as usize } }) && j == i + 1,
        decreases s.len() - j,
    {
        let c = s[j];
        if c == '{' {
            let (y, k) = parse_counted(s, j, x)?;
            x = y;
            j = k;
        } else {
            let node = if c == '*' {
                SyntaxKind::Star(Box::new(x))
            } else if c == '+' {
                SyntaxKind::Plus(Box::new(x))
            } else {
                SyntaxKind::Opt(Box::new(x))
            };
            x = Syn { node, span: Span { lo: i, hi: j + 1 } };
            j = j + 1;
        }
    }
    Ok((x, j))
}

pub fn parse_atom(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i < s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        res is Ok ==> res->Ok_0.1 > i,
        no_special_from(s@, i as int) ==> res == Ok::<(Syn, usize), PErr>((Syn { node: SyntaxKind::Chr(s@[i as int]), span: Span { lo: i, hi: (i + 1) as usize } }, (i + 1) as usize)),
    decreases s.len() - i, 0nat,
{
    let c = s[i];
    if c == '(' {
        let (x, j) = parse_alt(s, i + 1)?;
        if j < s.len() && s[j] == ')' {
            Ok((Syn { node: SyntaxKind::Group(Box::new(x)), span: Span { lo: i, hi: j + 1 } }, j + 1))
        } else {
            Err(PErr { pos: j, kind: ErrKind::UnclosedParen })
        }
    } else if c == '[' {
        let (xs, j) = class_items(s, i + 1, CharClass::class_empty())?;
        Ok((Syn { node: SyntaxKind::Class(xs), span: Span { lo: i, hi: j } }, j))
    } else if c == '\\' {
        if i + 1 < s.len() {
            Ok((Syn { node: SyntaxKind::Chr(s[i + 1]), span: Span { lo: i, hi: i + 2 } }, i + 2))
        } else {
            Err(PErr { pos: i + 1, kind: ErrKind::UnexpectedEnd })
        }
    } else if c == '*' || c == '+' || c == '?' || c == '{' || c == '}' || c == ']' || c == ')' || c == '|' {
        Err(PErr { pos: i, kind: ErrKind::UnexpectedChar })
    } else {
        Ok((Syn { node: SyntaxKind::Chr(c), span: Span { lo: i, hi: i + 1 } }, i + 1))
    }
}

pub fn parse(s: &Vec<char>) -> (res: Result<Syn, PErr>)
    ensures
        no_special_from(s@, 0) ==> res is Ok && matches(lower(res->Ok_0), s@) && lowering_nodes_r09(res->Ok_0) == (if s.len() == 0 { 1int } else { 2 * s.len() - 1 }),
        match res {
            Ok(t) => wf(t, s.len() as nat) && t.span.lo == 0 && t.span.hi == s.len(),
            Err(e) => e.pos <= s.len(),
        },
{
    let (x, j) = parse_alt(s, 0)?;
    proof {
        assert(s@.subrange(0, s.len() as int) =~= s@);
    }
    if j == s.len() {
        Ok(x)
    } else {
        Err(PErr { pos: j, kind: ErrKind::UnexpectedChar })
    }
}

} // verus!

use vstd::arithmetic::div_mod::{lemma_fundamental_div_mod, lemma_mod_bound};
use vstd::arithmetic::mul::lemma_mul_is_commutative;

verus! {

// The quotient guard: for a positive divisor, comparing a factor with a
// quotient decides the product comparison, without forming the product.
proof fn quotient_product_guard_r09(b: int, q: int, r: int, d: int)
    requires
        d > 0,
        0 <= r < d,
    ensures
        (b <= q) == (b * d <= q * d + r),
{
    assert((b <= q) == (b * d <= q * d + r)) by (nonlinear_arith)
        requires
            d > 0,
            0 <= r < d,
    ;
}

proof fn division_budget_guard_r09(base: int, space: int, copies: int)
    requires
        base >= 0,
        space >= 0,
        copies > 0,
    ensures
        (base <= space / copies) == (base * copies <= space),
{
    lemma_fundamental_div_mod(space, copies);
    lemma_mod_bound(space, copies);
    quotient_product_guard_r09(base, space / copies, space % copies, copies);
    lemma_mul_is_commutative(copies, space / copies);
}

// Checked addition: each guard comes before the subtraction or addition it
// protects, so no intermediate leaves u32.
fn checked_add_cost_r09(a: u32, b: u32, extra: u32, cap: u32) -> (res: Option<u32>)
    ensures
        match res {
            Some(n) => n <= cap && (n as int) == (a as int) + (b as int) + (extra as int),
            None => (a as int) + (b as int) + (extra as int) > (cap as int),
        },
{
    if extra > cap {
        return None;
    }
    if a > cap - extra {
        return None;
    }
    if b > cap - extra - a {
        return None;
    }
    Some(a + b + extra)
}

fn checked_class_cost_r09(cc: &CharClass, cap: u32) -> (res: Option<u32>)
    requires
        class_valid(cc.ranges_spec()),
    ensures
        match res {
            Some(n) => n <= cap && n == class_nodes_r09(cc.ranges_spec()),
            None => class_nodes_r09(cc.ranges_spec()) > cap,
        },
{
    let rs = cc.ranges();
    let ghost xs = cc.ranges_spec();
    proof {
        assert(class_nodes_r09(xs) >= 1);
    }
    if cap < 1 {
        return None;
    }
    let mut cost: u32 = 1;
    let mut i: usize = 0;
    proof {
        assert(xs.subrange(0, rs.len() as int) =~= xs);
    }
    while i < rs.len()
        invariant
            rs@ == xs,
            xs == cc.ranges_spec(),
            i <= rs.len(),
            cost <= cap,
            class_valid(xs),
            (cost as nat) + class_nodes_r09(xs.subrange(i as int, rs.len() as int)) == class_nodes_r09(xs) + 1,
        decreases rs.len() - i,
    {
        let (lo, hi) = rs[i];
        let width = hi - lo;
        let range: u32 = 2 * width + 1;
        proof {
            let suffix = xs.subrange(i as int, rs.len() as int);
            let tail = xs.subrange(i + 1, rs.len() as int);
            assert(suffix[0] == xs[i as int]);
            assert(suffix.drop_first() =~= tail);
            assert(class_nodes_r09(tail) >= 1);
            assert(range == range_nodes_r09(lo, hi));
        }
        cost = checked_add_cost_r09(cost, range, 1, cap)?;
        i = i + 1;
    }
    proof {
        assert(xs.subrange(rs.len() as int, rs.len() as int) =~= Seq::<(u32, u32)>::empty());
    }
    Some(cost)
}

proof fn lemma_repetition_cost_grows_r09(base: nat, n: nat, m: nat)
    requires
        n <= m,
        m > 0,
    ensures
        3 + n * (base + 1) + (m - n) * (base + 3) >= base,
{
    assert(3 + n * (base + 1) + (m - n) * (base + 3) >= base) by (nonlinear_arith)
        requires
            n <= m,
            m > 0,
            base >= 0,
            n >= 0,
    ;
}

/// The structural cost checker: each recursive result is unwrapped with `?`,
/// so a child over the cap returns `None` at once, and every sum goes through
/// the checked addition above. A zero upper count never visits its child.
pub fn checked_lowering_cost_r09(t: &Syn, len: usize, cap: u32) -> (res: Option<u32>)
    requires
        wf(*t, len as nat),
    ensures
        match res {
            Some(n) => n <= cap && n == lowering_nodes_r09(*t),
            None => lowering_nodes_r09(*t) > cap,
        },
    decreases *t,
{
    reveal_with_fuel(lowering_nodes_r09, 2);
    let result = match &t.node {
        SyntaxKind::Eps | SyntaxKind::Chr(_) => {
            if cap >= 1 {
                Some(1)
            } else {
                None
            }
        },
        SyntaxKind::Class(cc) => checked_class_cost_r09(cc, cap),
        SyntaxKind::Alt(a, b) | SyntaxKind::Cat(a, b) => {
            let left = checked_lowering_cost_r09(a, len, cap)?;
            let right = checked_lowering_cost_r09(b, len, cap)?;
            checked_add_cost_r09(left, right, 1, cap)
        },
        SyntaxKind::Star(a) => {
            let child = checked_lowering_cost_r09(a, len, cap)?;
            checked_add_cost_r09(child, 0, 1, cap)
        },
        SyntaxKind::Plus(a) => {
            let child = checked_lowering_cost_r09(a, len, cap)?;
            checked_add_cost_r09(child, child, 2, cap)
        },
        SyntaxKind::Opt(a) => {
            let child = checked_lowering_cost_r09(a, len, cap)?;
            checked_add_cost_r09(child, 0, 2, cap)
        },
        SyntaxKind::Group(a) => checked_lowering_cost_r09(a, len, cap),
        SyntaxKind::RepRange(a, n, m) => {
            if *m == 0 {
                proof {
                    let base = lowering_nodes_r09(**a) as int;
                    assert(3 + (*n as int) * (base + 1) + ((*m as int) - (*n as int)) * (base + 3) == 3) by (nonlinear_arith)
                        requires
                            *m == 0,
                            *n == 0,
                    ;
                    assert(lowering_nodes_r09(*t) == 3);
                }
                checked_add_cost_r09(0, 0, 3, cap)
            } else {
                proof {
                    lemma_repetition_cost_grows_r09(lowering_nodes_r09(**a), *n as nat, *m as nat);
                }
                let child = checked_lowering_cost_r09(a, len, cap)?;
                let result = repeat_expansion_budget_r09(child, *n, *m, cap);
                proof {
                    let base = lowering_nodes_r09(**a) as int;
                    assert(3 + (*n as int) * (base + 1) + ((*m as int) - (*n as int)) * (base + 3) == 3 + base * (*m as int) + (*n as int) + 3 * ((*m as int) - (*n as int))) by (nonlinear_arith);
                }
                proof {
                    assert(match result {
                        Some(n) => n <= cap && n == lowering_nodes_r09(*t),
                        None => lowering_nodes_r09(*t) > cap,
                    });
                }
                result
            }
        },
    };
    assert(match result {
        Some(n) => n <= cap && n == lowering_nodes_r09(*t),
        None => lowering_nodes_r09(*t) > cap,
    });
    result
}

} // verus!

use vstd::utf8::*;
use vstd::string::{StrSliceExecFns, StringSliceAdditionalSpecFns};

verus! {

// A scalar below the class domain becomes a char through the pinned UTF-8
// library contract: the encoded bytes are proved to decode to the one char.
fn scalar_char_r09(n: u32) -> (c: char)
    requires
        is_scalar(n),
    ensures
        c as u32 == n,
        c == n as char,
{
    let ghost wanted = n as char;
    proof {
        assert(wanted as u32 == n);
    }
    let mut bytes: Vec<u8> = Vec::new();
    if n <= 0x7f {
        bytes.push((n & 0x7f) as u8);
    } else if n <= 0x7ff {
        bytes.push(0xc0 | ((n >> 6) & 0x1f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    } else if n <= 0xffff {
        bytes.push(0xe0 | ((n >> 12) & 0xf) as u8);
        bytes.push(0x80 | ((n >> 6) & 0x3f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    } else {
        bytes.push(0xf0 | ((n >> 18) & 0x7) as u8);
        bytes.push(0x80 | ((n >> 12) & 0x3f) as u8);
        bytes.push(0x80 | ((n >> 6) & 0x3f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    }
    proof {
        assert(bytes@ =~= encode_scalar(n));
        assert(seq![wanted].drop_first() =~= Seq::<char>::empty());
        reveal_with_fuel(encode_utf8, 2);
        assert(encode_utf8(seq![wanted]) =~= encode_scalar(n));
        encode_utf8_valid_utf8(seq![wanted]);
    }
    let s = unsafe { str::from_utf8_unchecked(bytes.as_slice()) };
    proof {
        encode_utf8_decode_utf8(seq![wanted]);
        encode_utf8_decode_utf8(s@);
        assert(s@ =~= seq![wanted]);
    }
    s.get_char(0)
}

fn range_lower_exec_r09(lo: u32, hi: u32) -> (out: Re)
    requires
        range_valid(lo, hi),
    ensures
        out == range_re(lo, hi),
{
    let mut n = hi;
    proof {
        assert(is_scalar(hi));
    }
    let last = scalar_char_r09(hi);
    let mut out = Re::Chr(last);
    while n > lo
        invariant
            lo <= n <= hi,
            hi < CLASS_MAX,
            out == range_re(n, hi),
        decreases n - lo,
    {
        n = n - 1;
        proof {
            assert(is_scalar(n));
        }
        let c = scalar_char_r09(n);
        out = Re::Alt(Box::new(Re::Chr(c)), Box::new(out));
    }
    out
}

fn class_lower_exec_r09(cc: &CharClass) -> (out: Re)
    requires
        class_valid(cc.ranges_spec()),
    ensures
        out == class_re(cc.ranges_spec()),
{
    let rs = cc.ranges();
    let ghost xs = cc.ranges_spec();
    let mut i = rs.len();
    let mut out = Re::Empty;
    while i > 0
        invariant
            rs@ == xs,
            xs == cc.ranges_spec(),
            i <= rs.len(),
            class_valid(xs),
            out == class_re(xs.subrange(i as int, rs.len() as int)),
        decreases i,
    {
        i = i - 1;
        let (lo, hi) = rs[i];
        let first = range_lower_exec_r09(lo, hi);
        proof {
            let suffix = xs.subrange(i as int, rs.len() as int);
            assert(suffix[0] == xs[i as int]);
            assert(suffix.drop_first() =~= xs.subrange(i + 1, rs.len() as int));
        }
        out = Re::Alt(Box::new(first), Box::new(out));
    }
    proof {
        assert(xs.subrange(0, rs.len() as int) =~= xs);
    }
    out
}

fn copies_lower_exec_r09(r: &Re, k: u32) -> (out: Re)
    ensures
        out == copies(*r, k as nat),
{
    let mut i: u32 = 0;
    let mut out = Re::Eps;
    while i < k
        invariant
            i <= k,
            out == copies(*r, i as nat),
        decreases k - i,
    {
        let first = copy_re(r);
        out = Re::Cat(Box::new(first), Box::new(out));
        i = i + 1;
    }
    out
}

fn optional_lower_exec_r09(r: &Re, k: u32) -> (out: Re)
    ensures
        out == copies_up_to(*r, k as nat),
{
    let mut i: u32 = 0;
    let mut out = Re::Eps;
    while i < k
        invariant
            i <= k,
            out == copies_up_to(*r, i as nat),
        decreases k - i,
    {
        let first = copy_re(r);
        out = Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(first), Box::new(out))));
        i = i + 1;
    }
    out
}

fn repetition_lower_exec_r09(r: &Re, n: u32, m: u32) -> (out: Re)
    requires
        n <= m,
    ensures
        out == rep_range(*r, n as nat, m as nat),
{
    let fixed = copies_lower_exec_r09(r, n);
    let optional = optional_lower_exec_r09(r, m - n);
    Re::Cat(Box::new(fixed), Box::new(optional))
}

pub fn lowering_exec_r09(t: &Syn, len: usize) -> (out: Re)
    requires
        wf(*t, len as nat),
    ensures
        out == lower(*t),
    decreases *t,
{
    match &t.node {
        SyntaxKind::Eps => Re::Eps,
        SyntaxKind::Chr(c) => Re::Chr(*c),
        SyntaxKind::Class(cc) => class_lower_exec_r09(cc),
        SyntaxKind::Alt(a, b) => {
            let left = lowering_exec_r09(a, len);
            let right = lowering_exec_r09(b, len);
            Re::Alt(Box::new(left), Box::new(right))
        },
        SyntaxKind::Cat(a, b) => {
            let left = lowering_exec_r09(a, len);
            let right = lowering_exec_r09(b, len);
            Re::Cat(Box::new(left), Box::new(right))
        },
        SyntaxKind::Star(a) => {
            let child = lowering_exec_r09(a, len);
            Re::Star(Box::new(child))
        },
        SyntaxKind::Plus(a) => {
            let child = lowering_exec_r09(a, len);
            let second = copy_re(&child);
            Re::Cat(Box::new(child), Box::new(Re::Star(Box::new(second))))
        },
        SyntaxKind::Opt(a) => {
            let child = lowering_exec_r09(a, len);
            Re::Alt(Box::new(Re::Eps), Box::new(child))
        },
        SyntaxKind::Group(a) => lowering_exec_r09(a, len),
        SyntaxKind::RepRange(a, n, m) => {
            if *m == 0 {
                Re::Cat(Box::new(Re::Eps), Box::new(Re::Eps))
            } else {
                let child = lowering_exec_r09(a, len);
                repetition_lower_exec_r09(&child, *n, *m)
            }
        },
    }
}

// The cost is checked before the expansion is built.
pub fn frontend_r09(s: &Vec<char>, cap: u32) -> (res: Result<(Syn, Re), PErr>)
    ensures
        match res {
            Ok((tree, lowered)) => wf(tree, s.len() as nat) && tree.span.lo == 0 && tree.span.hi == s.len() && lowered == lower(tree) && node_count(lowered) <= cap,
            Err(e) => e.pos <= s.len(),
        },
        no_special_from(s@, 0) && (if s.len() == 0 { 1int } else { 2 * s.len() - 1 }) <= cap ==> res is Ok && matches(res->Ok_0.1, s@),
{
    let tree = parse(s)?;
    match checked_lowering_cost_r09(&tree, s.len(), cap) {
        None => Err(PErr { pos: 0, kind: ErrKind::ExpansionBudget }),
        Some(_) => {
            let lowered = lowering_exec_r09(&tree, s.len());
            proof {
                lemma_lowering_nodes_r09(tree, s.len() as nat);
            }
            Ok((tree, lowered))
        },
    }
}

} // verus!

use rg_re_a1b::*;

verus! {

/// Parse the counted suffix `{d}` or `{d,d}` that starts at `j`, after the operand `x`: on
/// success return the repetition node, spanning from `x.span.lo` to the end of the suffix, and
/// that end. A malformed suffix is an error at the first position that is wrong.
pub fn parse_counted(s: &Vec<char>, j: usize, x: Syn) -> (res: Result<(Syn, usize), PErr>)
    requires
        j < s.len(),
        s@[j as int] == '{',
        wf(x, s.len() as nat),
        x.span.hi == j,
        x.span.lo < j,
    ensures
        match res {
            Ok((y, k)) => j < k <= s.len() && wf(y, s.len() as nat) && y.span.lo == x.span.lo && y.span.hi == k,
            Err(e) => e.pos <= s.len(),
        },
        forall|n: nat, m: nat, k: int| #[trigger] counted_at(s@, j as int, n, m, k) ==> res == Ok::<(Syn, usize), PErr>((counted_node(x, n, m, k), k as usize)),
{
    let len = s.len();
    if j + 1 >= len {
        return Err(PErr { pos: j + 1, kind: ErrKind::UnexpectedEnd });
    }
    let d = s[j + 1];
    if d < '0' || d > '9' {
        return Err(PErr { pos: j + 1, kind: ErrKind::UnexpectedChar });
    }
    let lo = (d as u32) - ('0' as u32);
    if j + 2 >= len {
        return Err(PErr { pos: j + 2, kind: ErrKind::UnexpectedEnd });
    }
    if s[j + 2] == '}' {
        let start = x.span.lo;
        return Ok((Syn { node: SyntaxKind::RepRange(Box::new(x), lo, lo), span: Span { lo: start, hi: j + 3 } }, j + 3));
    }
    if s[j + 2] != ',' {
        return Err(PErr { pos: j + 2, kind: ErrKind::UnexpectedChar });
    }
    if j + 3 >= len {
        return Err(PErr { pos: j + 3, kind: ErrKind::UnexpectedEnd });
    }
    let e = s[j + 3];
    if e < '0' || e > '9' {
        return Err(PErr { pos: j + 3, kind: ErrKind::UnexpectedChar });
    }
    if j + 4 >= len {
        return Err(PErr { pos: j + 4, kind: ErrKind::UnexpectedEnd });
    }
    if s[j + 4] != '}' {
        return Err(PErr { pos: j + 4, kind: ErrKind::UnexpectedChar });
    }
    let hi = (e as u32) - ('0' as u32);
    if hi < lo {
        return Err(PErr { pos: j + 3, kind: ErrKind::BoundsOrder });
    }
    let start = x.span.lo;
    Ok((Syn { node: SyntaxKind::RepRange(Box::new(x), lo, hi), span: Span { lo: start, hi: j + 5 } }, j + 5))
}

/// Parse a class body from `i` up to and including its closing `]`, inserting each single
/// character or range `c-d` (either may be escaped) into the accumulator through A2's API. On
/// success return the class and the position after `]`.
pub fn class_items(s: &Vec<char>, i: usize, mut acc: CharClass) -> (res: Result<(CharClass, usize), PErr>)
    requires
        i <= s.len(),
        acc.valid() && class_valid(acc.ranges_spec()),
    ensures
        match res {
            Ok((xs, k)) => i < k <= s.len() && xs.valid() && class_valid(xs.ranges_spec()),
            Err(e) => e.pos <= s.len(),
        },
        forall|k: int| #[trigger] simple_class_body(s@, i as int, k) ==> res is Ok && res->Ok_0.1 == k + 1,
{
    let mut j = i;
    while j < s.len()
        invariant
            i <= j <= s.len(),
            acc.valid() && class_valid(acc.ranges_spec()),
            forall|k: int| #[trigger] simple_class_body(s@, i as int, k) ==> simple_class_body(s@, j as int, k),
        decreases s.len() - j,
    {
        if s[j] == ']' {
            return Ok((acc, j + 1));
        }
        let escaped = s[j] == '\\' && j + 1 < s.len();
        let c = if escaped {
            s[j + 1]
        } else {
            s[j]
        };
        let k = if escaped {
            j + 2
        } else {
            j + 1
        };
        if k < s.len() && k + 1 < s.len() && s[k] == '-' && s[k + 1] != ']' {
            let d = s[k + 1];
            if d < c {
                return Err(PErr { pos: k + 1, kind: ErrKind::ClassRange });
            }
            if (d as u32) >= CLASS_MAX {
                return Err(PErr { pos: k + 1, kind: ErrKind::ClassRange });
            }
            let next = acc.class_insert(c as u32, d as u32);
            proof {
                assert(acc.ranges_below(CLASS_MAX as int));
                assert(next.ranges_below(CLASS_MAX as int));
                next.lemma_view_ranges();
            }
            acc = next;
            j = k + 2;
        } else {
            if (c as u32) >= CLASS_MAX {
                return Err(PErr { pos: j, kind: ErrKind::ClassRange });
            }
            let next = acc.class_insert(c as u32, c as u32);
            proof {
                assert(acc.ranges_below(CLASS_MAX as int));
                assert(next.ranges_below(CLASS_MAX as int));
                next.lemma_view_ranges();
            }
            acc = next;
            j = k;
        }
    }
    Err(PErr { pos: j, kind: ErrKind::UnclosedClass })
}

/// Decide whether a counted repetition with `lo` fixed and `hi - lo` optional copies of a child
/// of cost `base` fits under `cap`, without any intermediate overflowing u32: return `Some` of
/// the exact cost when it fits, `None` when it does not.
pub fn repeat_expansion_budget_r09(base: u32, lo: u32, hi: u32, cap: u32) -> (res: Option<u32>)
    requires
        lo <= hi <= 9,
    ensures
        match res {
            Some(cost) => cost <= cap && (cost as int) == 3 + (base as int) * (hi as int) + (lo as int) + 3 * ((hi as int) - (lo as int)),
            None => 3 + (base as int) * (hi as int) + (lo as int) + 3 * ((hi as int) - (lo as int)) > (cap as int),
        },
{
    let overhead: u32 = 3 + lo + 3 * (hi - lo);
    if overhead > cap {
        return None;
    }
    proof {
        if hi > 0 {
            division_budget_guard_r09(base as int, (cap - overhead) as int, hi as int);
        }
    }
    if hi > 0 && base > (cap - overhead) / hi {
        return None;
    }
    let cost: u32 = base * hi + overhead;
    Some(cost)
}
} // verus!
