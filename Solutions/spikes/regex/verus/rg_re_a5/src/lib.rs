//! Regex spike, layer A5 (R16): a Pike-style VM (`Char`/`Split`/`Jmp`/`Match`) with fuelled
//! nondeterministic acceptance, the emitter `Re -> code at an offset` (`emit`; design `compile`,
//! renamed, PLAN §5.5), and its simulation
//! proof, generalized over the continuation: soundness and completeness (nullable `Star`
//! bodies included: the DVR0 risk), then the whole-program theorem and an exec emitter (`emit_into`, `emit_prog`).
//!
//! Reference material (DVR0 spike, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a3::*;
use rg_re_a4::*;

verus! {

pub enum Inst {
    Char(char),
    Split(usize, usize),
    Jmp(usize),
    Match,
}

/// Fuelled acceptance (one `step` per unit of fuel): some run of at most `fuel` steps from
/// `pc` reaches `Match` with the whole input consumed. `Split` forks the thread, `Jmp` moves
/// it, `Char` consumes one matching char, and a thread outside the program dies.
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

/// Splitting a word and re-attaching its tail to a suffix.
pub proof fn lemma_split_add(s1: Seq<char>, i: int, s2: Seq<char>)
    requires
        0 <= i <= s1.len(),
    ensures
        s1.subrange(0, i) + (s1.subrange(i, s1.len() as int) + s2) == s1 + s2,
{
    assert(s1.subrange(0, i) + (s1.subrange(i, s1.len() as int) + s2) =~= s1 + s2);
}

/// A word of `a` followed by a word of `a*` is a word of `a*`.
pub proof fn lemma_star_cons(a: Re, x: Seq<char>, y: Seq<char>)
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

/// Completeness, generalized over the continuation: a word of `r` followed by an input the
/// continuation accepts is accepted from the start of `r`'s code.
pub proof fn lemma_complete(p: Seq<Inst>, r: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
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
            f + 1
        },
        Re::Alt(a, b) => lemma_complete_alt(p, *a, *b, pc, s1, s2, f),
        Re::Cat(a, b) => lemma_complete_cat(p, *a, *b, pc, s1, s2, f),
        Re::Star(a) => lemma_complete_star(p, *a, pc, s1, s2, f),
        Re::Empty => 0,
    }
}

pub proof fn lemma_complete_alt(p: Seq<Inst>, a: Re, b: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
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
        assert(accepts(p, pc + 1 + clen(a), s2, f + 1));
        let f1 = lemma_complete(p, a, pc + 1, s1, s2, f + 1);
        assert(accepts(p, pc, s1 + s2, f1 + 1));
        f1 + 1
    } else {
        let f1 = lemma_complete(p, b, pc + 2 + clen(a), s1, s2, f);
        assert(accepts(p, pc, s1 + s2, f1 + 1));
        f1 + 1
    }
}

pub proof fn lemma_complete_cat(p: Seq<Inst>, a: Re, b: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
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
        0 <= i <= s1.len() && matches(a, #[trigger] s1.subrange(0, i)) && matches(
            b,
            s1.subrange(i, s1.len() as int),
        );
    let x = s1.subrange(0, i);
    let y = s1.subrange(i, s1.len() as int);
    let fb = lemma_complete(p, b, pc + clen(a), y, s2, f);
    let fa = lemma_complete(p, a, pc, x, y + s2, fb);
    lemma_split_add(s1, i, s2);
    fa
}

pub proof fn lemma_complete_star(p: Seq<Inst>, a: Re, pc: int, s1: Seq<char>, s2: Seq<char>, f: nat) -> (f2: nat)
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
        f + 1
    } else {
        let i = choose|i: int|
            1 <= i <= s1.len() && matches(a, #[trigger] s1.subrange(0, i)) && matches(
                r,
                s1.subrange(i, s1.len() as int),
            );
        let x = s1.subrange(0, i);
        let y = s1.subrange(i, s1.len() as int);
        // the remaining iterations, from the loop head
        let fy = lemma_complete(p, r, pc, y, s2, f);
        // the back edge
        assert(accepts(p, pc + 1 + clen(a), y + s2, fy + 1));
        // one iteration of the body, continuing at the back edge
        let fx = lemma_complete(p, a, pc + 1, x, y + s2, fy + 1);
        lemma_split_add(s1, i, s2);
        assert(accepts(p, pc, s1 + s2, fx + 1));
        fx + 1
    }
}

/// Soundness, generalized over the continuation: an accepting run from the start of `r`'s
/// code consumes a word of `r`, then reaches the continuation with no more fuel.
pub open spec fn sound_post(p: Seq<Inst>, r: Re, pc: int, s: Seq<char>, f: nat, res: (int, nat)) -> bool {
    &&& 0 <= res.0 <= s.len()
    &&& res.1 <= f
    &&& matches(r, s.subrange(0, res.0))
    &&& accepts(p, pc + clen(r), s.subrange(res.0, s.len() as int), res.1)
}

pub proof fn lemma_sound(p: Seq<Inst>, r: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
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
            let _ = lemma_sound(p, r, pc, s, (f - 1) as nat);
            (0, 0)
        },
        Re::Chr(c) => {
            lemma_sub_one(p, r, pc);
            assert(s.subrange(1, s.len() as int) =~= s.drop_first());
            assert(s.subrange(0, 1)[0] == c);
            (1, (f - 1) as nat)
        },
        Re::Alt(a, b) => lemma_sound_alt(p, *a, *b, pc, s, f),
        Re::Cat(a, b) => lemma_sound_cat(p, *a, *b, pc, s, f),
        Re::Star(a) => lemma_sound_star(p, *a, pc, s, f),
    }
}

pub proof fn lemma_sound_alt(p: Seq<Inst>, a: Re, b: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
    requires
        code_at(p, pc, emit(Re::Alt(Box::new(a), Box::new(b)), pc)),
        pc + clen(Re::Alt(Box::new(a), Box::new(b))) < usize::MAX,
        accepts(p, pc, s, f),
    ensures
        sound_post(p, Re::Alt(Box::new(a), Box::new(b)), pc, s, f, res),
    decreases Re::Alt(Box::new(a), Box::new(b)), f, 0nat,
{
    lemma_sub_alt(p, a, b, pc);
    if accepts(p, pc + 1, s, (f - 1) as nat) {
        let (j, f1) = lemma_sound(p, a, pc + 1, s, (f - 1) as nat);
        assert(accepts(p, pc + 1 + clen(a), s.subrange(j, s.len() as int), f1));
        (j, (f1 - 1) as nat)
    } else {
        lemma_sound(p, b, pc + 2 + clen(a), s, (f - 1) as nat)
    }
}

pub proof fn lemma_sound_cat(p: Seq<Inst>, a: Re, b: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
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

pub proof fn lemma_sound_star(p: Seq<Inst>, a: Re, pc: int, s: Seq<char>, f: nat) -> (res: (int, nat))
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
    if accepts(p, pc + 1, s, (f - 1) as nat) {
        // one iteration of the body, then the back edge
        let (j1, f1) = lemma_sound(p, a, pc + 1, s, (f - 1) as nat);
        let t = s.subrange(j1, s.len() as int);
        assert(accepts(p, pc + 1 + clen(a), t, f1));
        // the remaining iterations, with strictly less fuel (same regex)
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

/// The whole program for `r`: its code at 0, then `Match`.
pub open spec fn prog(r: Re) -> Seq<Inst> {
    emit(r, 0).push(Inst::Match)
}

pub open spec fn vm_accepts(r: Re, s: Seq<char>) -> bool {
    exists|f: nat| #[trigger] accepts(prog(r), 0, s, f)
}

/// The emitter is correct: the VM accepts exactly the words of `r`.
pub proof fn lemma_vm_correct(r: Re, s: Seq<char>)
    requires
        clen(r) + 1 < usize::MAX,
    ensures
        vm_accepts(r, s) == matches(r, s),
{
    reveal(code_at);
    let p = prog(r);
    lemma_emit_len(r, 0);
    assert(code_at(p, 0, emit(r, 0))) by {
        assert forall|i: int| 0 <= i < emit(r, 0).len() implies p[0 + i] == #[trigger] emit(r, 0)[i] by {}
    }
    let e = Seq::<char>::empty();
    if vm_accepts(r, s) {
        let f = choose|f: nat| #[trigger] accepts(p, 0, s, f);
        let (j, f2) = lemma_sound(p, r, 0, s, f);
        let rest = s.subrange(j, s.len() as int);
        assert(rest.len() == 0);
        assert(s.subrange(0, j) =~= s);
    }
    if matches(r, s) {
        let f = lemma_complete(p, r, 0, s, e, 1);
        assert(s + e =~= s);
        assert(accepts(p, 0, s, f));
    }
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
