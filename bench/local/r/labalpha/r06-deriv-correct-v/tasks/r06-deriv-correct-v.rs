// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b","c","s"],"kind":"calls","callees":["lemma_deriv_correct"]},{"name":"c2","identifiers":["a"],"kind":"calls","callees":["lemma_nullable_fact"]},{"name":"c3","identifiers":["b","c","s"],"kind":"calls","callees":["lemma_deriv_correct"]},{"name":"c4","identifiers":["a","c","s","i","subrange"],"kind":"calls","callees":["lemma_deriv_correct"]},{"name":"h1","identifiers":["matches","da","s","i","subrange"]},{"name":"h2","identifiers":["matches","cat","s"]},{"name":"c5","identifiers":["a","c","s","j","subrange"],"kind":"calls","callees":["lemma_deriv_correct"]},{"name":"h3","identifiers":["matches","a","w","j","subrange"]},{"name":"c6","identifiers":["b","c","s"],"kind":"calls","callees":["lemma_deriv_correct"]},{"name":"h4","identifiers":["matches","a","w","subrange"]},{"name":"c7","identifiers":["a","c","s","i","subrange"],"kind":"calls","callees":["lemma_deriv_correct"]},{"name":"h5","identifiers":["matches","da","s","i","subrange"]},{"name":"c8","identifiers":["a","c","s","j","subrange"],"kind":"calls","callees":["lemma_deriv_correct"]},{"name":"h6","identifiers":["matches","a","w","j","subrange"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_deriv_correct","start":96,"end":174}]
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

pub open spec fn nullable(r: Re) -> bool
    decreases r,
{
    match r {
        Re::Empty => false,
        Re::Eps => true,
        Re::Chr(_) => false,
        Re::Alt(a, b) => nullable(*a) || nullable(*b),
        Re::Cat(a, b) => nullable(*a) && nullable(*b),
        Re::Star(_) => true,
    }
}

// R06's given one-character derivative (not a task).
pub open spec fn deriv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv(*a, c)), Box::new(deriv(*b, c))),
        Re::Cat(a, b) => if nullable(*a) {
            Re::Alt(Box::new(Re::Cat(Box::new(deriv(*a, c)), b)), Box::new(deriv(*b, c)))
        } else {
            Re::Cat(Box::new(deriv(*a, c)), b)
        },
        Re::Star(a) => Re::Cat(Box::new(deriv(*a, c)), Box::new(Re::Star(a))),
    }
}

// Provided facts, complete (not tasks).

// rg_re_a1b::lemma_nullable_correct, complete (renamed lemma_nullable_fact).
pub proof fn lemma_nullable_fact(r: Re)
    ensures
        nullable(r) <==> matches(r, Seq::<char>::empty()),
    decreases r,
{
    let e = Seq::<char>::empty();
    assert(e.subrange(0, 0) =~= e);
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_fact(*a);
            lemma_nullable_fact(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_fact(*a);
            lemma_nullable_fact(*b);
        },
        _ => {},
    }
}

// The task.
pub proof fn lemma_deriv_correct(r: Re,c: char,s: Seq<char>)
    ensures matches(deriv(r,c),s) <==> matches(r,seq![c]+s),
    decreases r,
{
    let w = seq![c] + s;
    assert(w.len() == s.len() + 1);
    match r {
        Re::Chr(d) => {
            assert(w[0] == c);
        },
        Re::Alt(a, b) => {
            /*R12_CALLS:c1*/
        },
        Re::Cat(a, b) => {
            let da = deriv(*a, c);
            let cat = Re::Cat(Box::new(da), b);
            /*R12_CALLS:c2*/
            assert(w.subrange(0, 0) =~= Seq::<char>::empty());
            assert(w.subrange(0, w.len() as int) =~= w);
            if matches(r, w) {
                let i = choose|i: int|
                    0 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        *b,
                        w.subrange(i, w.len() as int),
                    );
                if i == 0 {
                    /*R12_CALLS:c3*/
                } else {
                    /*R12_CALLS:c4*/
                    assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                    assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                    assert(/*R12_HINT:h1*/ true);
                    assert(/*R12_HINT:h2*/ true);
                }
            }
            if matches(cat, s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        *b,
                        s.subrange(j, s.len() as int),
                    );
                /*R12_CALLS:c5*/
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(/*R12_HINT:h3*/ true);
            }
            if nullable(*a) && matches(deriv(*b, c), s) {
                /*R12_CALLS:c6*/
                assert(/*R12_HINT:h4*/ true);
            }
        },
        Re::Star(a) => {
            let da = deriv(*a, c);
            if matches(r, w) {
                let i = choose|i: int|
                    1 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        r,
                        w.subrange(i, w.len() as int),
                    );
                /*R12_CALLS:c7*/
                assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                assert(/*R12_HINT:h5*/ true);
            }
            if matches(deriv(r, c), s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        r,
                        s.subrange(j, s.len() as int),
                    );
                /*R12_CALLS:c8*/
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(/*R12_HINT:h6*/ true);
            }
        },
        _ => {},
    }
}

} // verus!
