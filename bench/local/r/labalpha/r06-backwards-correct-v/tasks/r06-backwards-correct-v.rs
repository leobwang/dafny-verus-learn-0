// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["r","s"],"kind":"calls","callees":["lemma_backwards_sound"]},{"name":"c2","identifiers":["r","s","backwards","backwards_str"],"kind":"calls","callees":["lemma_backwards_sound","lemma_backwards_involution","lemma_backwards_str_involution"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_backwards_correct","start":200,"end":209}]
use vstd::prelude::*;

verus! {

// Provided definitions: rg_re_a1 (layer A1), copied verbatim.
pub enum Re {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Re>, Box<Re>),
    Cat(Box<Re>, Box<Re>),
    Star(Box<Re>),
}

pub open spec fn matches(r: Re, s: Seq<char>) -> bool
    decreases r, s.len(),
{
    match r {
        Re::Empty => false,
        Re::Eps => s.len() == 0,
        Re::Chr(c) => s.len() == 1 && s[0] == c,
        Re::Alt(a, b) => matches(*a, s) || matches(*b, s),
        Re::Cat(a, b) => exists|i: int|
            0 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                *b,
                s.subrange(i, s.len() as int),
            ),
        Re::Star(a) => s.len() == 0 || exists|i: int|
            1 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            ),
    }
}

/// The regex read backwards.
pub open spec fn backwards(r: Re) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Eps,
        Re::Chr(c) => Re::Chr(c),
        Re::Alt(a, b) => Re::Alt(Box::new(backwards(*a)), Box::new(backwards(*b))),
        Re::Cat(a, b) => Re::Cat(Box::new(backwards(*b)), Box::new(backwards(*a))),
        Re::Star(a) => Re::Star(Box::new(backwards(*a))),
    }
}

/// The string read backwards.
pub open spec fn backwards_str(s: Seq<char>) -> Seq<char>
    decreases s.len(),
{
    if s.len() == 0 {
        Seq::empty()
    } else {
        backwards_str(s.subrange(1, s.len() as int)) + seq![s[0]]
    }
}

// Provided facts, complete (not tasks).

// R06 lemma_backwards_str_append (R06 decomposer reference), complete.
pub proof fn lemma_backwards_str_append(u: Seq<char>,v: Seq<char>)
    ensures backwards_str(u+v) == backwards_str(v)+backwards_str(u),
    decreases u.len(),
{
    if u.len() == 0 {
        assert(u+v =~= v);
    } else {
        assert((u+v).subrange(1,(u+v).len() as int) =~= u.subrange(1,u.len() as int)+v);
        assert((u+v)[0] == u[0]);
        lemma_backwards_str_append(u.subrange(1,u.len() as int),v);
        assert((backwards_str(v)+backwards_str(u.subrange(1,u.len() as int)))+seq![u[0]] =~= backwards_str(v)+(backwards_str(u.subrange(1,u.len() as int))+seq![u[0]]));
    }
}

// R06 lemma_backwards_str_involution (R06 decomposer reference), complete.
pub proof fn lemma_backwards_str_involution(s: Seq<char>)
    ensures backwards_str(backwards_str(s)) == s,
    decreases s.len(),
{
    if s.len() > 0 {
        let tail=s.subrange(1,s.len() as int);
        lemma_backwards_str_append(backwards_str(tail),seq![s[0]]);
        assert(seq![s[0]].subrange(1,1) =~= Seq::<char>::empty());
        assert(backwards_str(Seq::<char>::empty()) =~= Seq::<char>::empty());
        assert(backwards_str(seq![s[0]]) == backwards_str(seq![s[0]].subrange(1,1))+seq![s[0]]);
        assert(backwards_str(seq![s[0]]) =~= seq![s[0]]);
        lemma_backwards_str_involution(tail);
        assert(s =~= seq![s[0]]+tail);
    }
}

// R06 lemma_backwards_involution (R06 decomposer reference), complete.
pub proof fn lemma_backwards_involution(r: Re)
    ensures backwards(backwards(r)) == r,
    decreases r,
{
    match r {
        Re::Alt(a,b) => { lemma_backwards_involution(*a);lemma_backwards_involution(*b); },
        Re::Cat(a,b) => { lemma_backwards_involution(*a);lemma_backwards_involution(*b); },
        Re::Star(a) => { lemma_backwards_involution(*a); },
        _ => { },
    }
}

/// rg_re_a1b::lemma_star_one, complete.
pub proof fn lemma_star_one(a: Re, u: Seq<char>)
    requires
        matches(a, u),
    ensures
        matches(Re::Star(Box::new(a)), u),
{
    if u.len() > 0 {
        assert(u.subrange(0, u.len() as int) =~= u);
        assert(u.subrange(u.len() as int, u.len() as int) =~= Seq::<char>::empty());
        assert(matches(Re::Star(Box::new(a)), Seq::<char>::empty()));
    }
}

/// rg_re_a1b::lemma_star_concat, complete.
pub proof fn lemma_star_concat(a: Re, u: Seq<char>, v: Seq<char>)
    requires
        matches(Re::Star(Box::new(a)), u),
        matches(Re::Star(Box::new(a)), v),
    ensures
        matches(Re::Star(Box::new(a)), u + v),
    decreases u.len(),
{
    let st = Re::Star(Box::new(a));
    let t = u + v;
    if u.len() == 0 {
        assert(t =~= v);
    } else {
        let i = choose|i: int|
            1 <= i <= u.len() && matches(a, #[trigger] u.subrange(0, i)) && matches(
                st,
                u.subrange(i, u.len() as int),
            );
        lemma_star_concat(a, u.subrange(i, u.len() as int), v);
        assert(t.subrange(0, i) =~= u.subrange(0, i));
        assert(t.subrange(i, t.len() as int) =~= u.subrange(i, u.len() as int) + v);
    }
}

// R06 lemma_backwards_sound (R06 decomposer reference), complete.
pub proof fn lemma_backwards_sound(r: Re,s: Seq<char>)
    requires matches(r,s),
    ensures matches(backwards(r),backwards_str(s)),
    decreases r,s.len(),
{
    match r {
        Re::Empty => { },
        Re::Eps => { assert(s =~= Seq::<char>::empty()); },
        Re::Chr(c) => {
            assert(s.len() == 1 && s[0] == c);
            assert(s.subrange(1,s.len() as int) =~= Seq::<char>::empty());
            assert(backwards_str(Seq::<char>::empty()) =~= Seq::<char>::empty());
            assert(backwards_str(s) == backwards_str(s.subrange(1,s.len() as int))+seq![s[0]]);
            assert(backwards_str(s) =~= seq![c]);
        },
        Re::Alt(a,b) => {
            if matches(*a,s) { lemma_backwards_sound(*a,s); }
            else { lemma_backwards_sound(*b,s); }
        },
        Re::Cat(a,b) => {
            let i=choose|i:int| 0 <= i <= s.len() && matches(*a,#[trigger] s.subrange(0,i)) && matches(*b,s.subrange(i,s.len() as int));
            let u=s.subrange(0,i);let v=s.subrange(i,s.len() as int);
            lemma_backwards_sound(*a,u);lemma_backwards_sound(*b,v);
            assert(s =~= u+v);
            lemma_backwards_str_append(u,v);
            let w=backwards_str(s);let j=backwards_str(v).len() as int;
            assert(w.subrange(0,j) =~= backwards_str(v));
            assert(w.subrange(j,w.len() as int) =~= backwards_str(u));
        },
        Re::Star(a) => {
            if s.len() > 0 {
                let i=choose|i:int| 1 <= i <= s.len() && matches(*a,#[trigger] s.subrange(0,i)) && matches(r,s.subrange(i,s.len() as int));
                let u=s.subrange(0,i);let v=s.subrange(i,s.len() as int);
                lemma_backwards_sound(*a,u);
                lemma_star_one(backwards(*a),backwards_str(u));
                lemma_backwards_sound(r,v);
                lemma_star_concat(backwards(*a),backwards_str(v),backwards_str(u));
                assert(s =~= u+v);
                lemma_backwards_str_append(u,v);
            } else {
                assert(backwards_str(s) =~= Seq::<char>::empty());
            }
        },
    }
}

// The task.
pub proof fn lemma_backwards_correct(r: Re,s: Seq<char>)
    ensures matches(backwards(r),backwards_str(s)) <==> matches(r,s),
{
    if matches(r,s) {
        /*R12_CALLS:c1*/
    }
    if matches(backwards(r),backwards_str(s)) {
        /*R12_CALLS:c2*/
    }
}

} // verus!
