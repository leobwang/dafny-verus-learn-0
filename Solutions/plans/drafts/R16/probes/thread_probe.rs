#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;

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


pub open spec fn accepts_from(p: Seq<Inst>, pc: int, s: Seq<char>) -> bool {
    exists|f: nat| #[trigger] accepts(p, pc, s, f)
}

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

pub proof fn lemma_accepts_jmp(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat)
    requires
        0 <= pc < p.len(),
        p[pc] is Jmp,
    ensures
        accepts(p, pc, s, fuel) <==> fuel > 0 && accepts(p, p[pc]->Jmp_0 as int, s, (fuel - 1) as nat),
{
    reveal_with_fuel(accepts, 1);
}

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
            lemma_accepts_char(p, pc, s1 + s2, f + 1);
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
        lemma_accepts_split(p, pc, s1 + s2, f + 1);
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
        lemma_accepts_jmp(p, pc + 1 + clen(a), y + s2, fy + 1);
        // one iteration of the body, continuing at the back edge
        let fx = lemma_complete(p, a, pc + 1, x, y + s2, fy + 1);
        lemma_split_add(s1, i, s2);
        lemma_accepts_split(p, pc, s1 + s2, fx + 1);
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
    lemma_accepts_split(p, pc, s, f);
    if accepts(p, pc + 1, s, (f - 1) as nat) {
        let (j, f1) = lemma_sound(p, a, pc + 1, s, (f - 1) as nat);
        lemma_accepts_jmp(p, pc + 1 + clen(a), s.subrange(j, s.len() as int), f1);
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
    lemma_accepts_split(p, pc, s, f);
    if accepts(p, pc + 1, s, (f - 1) as nat) {
        // one iteration of the body, then the back edge
        let (j1, f1) = lemma_sound(p, a, pc + 1, s, (f - 1) as nat);
        let t = s.subrange(j1, s.len() as int);
        lemma_accepts_jmp(p, pc + 1 + clen(a), t, f1);
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

/// Fuel-free completeness (the frozen statement's shape).
pub proof fn lemma_emit_complete(p: Seq<Inst>, r: Re, pc: int, u: Seq<char>, v: Seq<char>)
    requires
        code_at(p, pc, emit(r, pc)),
        pc + clen(r) < usize::MAX,
        matches(r, u),
        accepts_from(p, pc + clen(r), v),
    ensures
        accepts_from(p, pc, u + v),
{
    let f = choose|f: nat| #[trigger] accepts(p, pc + clen(r), v, f);
    let f2 = lemma_complete(p, r, pc, u, v, f);
}

/// Fuel-free soundness (the frozen statement's shape).
pub proof fn lemma_emit_sound(p: Seq<Inst>, r: Re, pc: int, w: Seq<char>)
    requires
        code_at(p, pc, emit(r, pc)),
        pc + clen(r) < usize::MAX,
        accepts_from(p, pc, w),
    ensures
        exists|k: int| 0 <= k <= w.len() && #[trigger] matches(r, w.subrange(0, k))
            && accepts_from(p, pc + clen(r), w.subrange(k, w.len() as int)),
{
    let f = choose|f: nat| #[trigger] accepts(p, pc, w, f);
    let (k, f2) = lemma_sound(p, r, pc, w, f);
    assert(accepts(p, pc + clen(r), w.subrange(k, w.len() as int), f2));
}

/// The emitter is correct: the VM accepts exactly the words of `r`.
pub proof fn lemma_emit_correct(r: Re, s: Seq<char>)
    requires
        clen(r) + 1 < usize::MAX,
    ensures
        accepts_from(prog(r), 0, s) == matches(r, s),
{
    reveal(code_at);
    let p = prog(r);
    lemma_emit_len(r, 0);
    assert(code_at(p, 0, emit(r, 0))) by {
        assert forall|i: int| 0 <= i < emit(r, 0).len() implies p[0 + i] == #[trigger] emit(r, 0)[i] by {}
    }
    if accepts_from(p, 0, s) {
        lemma_emit_sound(p, r, 0, s);
        let k = choose|k: int| 0 <= k <= s.len() && #[trigger] matches(r, s.subrange(0, k))
            && accepts_from(p, clen(r) as int, s.subrange(k, s.len() as int));
        let rest = s.subrange(k, s.len() as int);
        let f = choose|f: nat| #[trigger] accepts(p, clen(r) as int, rest, f);
        lemma_accepts_match(p, clen(r) as int, rest, f);
        assert(s.subrange(0, k) =~= s);
    }
    if matches(r, s) {
        let e = Seq::<char>::empty();
        lemma_accepts_match(p, clen(r) as int, e, 1);
        lemma_emit_complete(p, r, 0, s, e);
        assert(s + e =~= s);
    }
}


pub proof fn lemma_accepts_inside(p: Seq<Inst>, pc: int, s: Seq<char>, fuel: nat)
    requires
        accepts(p, pc, s, fuel),
    ensures
        fuel > 0,
        0 <= pc < p.len(),
{
    reveal_with_fuel(accepts, 1);
}

pub open spec fn hop(p: Seq<Inst>, ins: Inst) -> Inst {
    match ins {
        Inst::Jmp(a) => if (a as int) < p.len() && p[a as int] is Jmp { Inst::Jmp(p[a as int]->Jmp_0) } else { ins },
        _ => ins,
    }
}

pub open spec fn shortcut(p: Seq<Inst>) -> Seq<Inst> {
    Seq::new(p.len(), |i: int| hop(p, p[i]))
}

pub proof fn lemma_to_shortcut(p: Seq<Inst>, pc: int, w: Seq<char>, f: nat) -> (g: nat)
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

pub proof fn lemma_from_shortcut(p: Seq<Inst>, pc: int, w: Seq<char>, f: nat) -> (g: nat)
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

pub proof fn lemma_shortcut_correct(p: Seq<Inst>, pc: int, w: Seq<char>)
    ensures
        accepts_from(shortcut(p), pc, w) == accepts_from(p, pc, w),
{
    if accepts_from(p, pc, w) {
        let f = choose|f: nat| #[trigger] accepts(p, pc, w, f);
        let g = lemma_to_shortcut(p, pc, w, f);
    }
    if accepts_from(shortcut(p), pc, w) {
        let f = choose|f: nat| #[trigger] accepts(shortcut(p), pc, w, f);
        let g = lemma_from_shortcut(p, pc, w, f);
    }
}

} // verus!
