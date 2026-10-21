// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_nullable_correct"]},{"name":"c2","kind":"calls","callees":["lemma_nullable_derivs_r13","lemma_deriv_correct"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_nullable_derivs_r13","start":189,"end":201}]
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

// Provided fact (rg_re_a1b::lemma_nullable_correct), complete, copied verbatim.
pub proof fn lemma_nullable_correct(r: Re)
    ensures
        nullable(r) <==> matches(r, Seq::<char>::empty()),
    decreases r,
{
    let e = Seq::<char>::empty();
    assert(e.subrange(0, 0) =~= e);
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        _ => {},
    }
}

// Provided definition (rg_re_a2::deriv), copied verbatim.
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

// Provided fact (rg_re_a2::lemma_deriv_correct), complete, copied verbatim.
pub proof fn lemma_deriv_correct(r: Re, c: char, s: Seq<char>)
    ensures
        matches(deriv(r, c), s) <==> matches(r, seq![c] + s),
    decreases r,
{
    let w = seq![c] + s;
    assert(w.len() == s.len() + 1);
    match r {
        Re::Chr(d) => {
            assert(w[0] == c);
        },
        Re::Alt(a, b) => {
            lemma_deriv_correct(*a, c, s);
            lemma_deriv_correct(*b, c, s);
        },
        Re::Cat(a, b) => {
            let da = deriv(*a, c);
            let cat = Re::Cat(Box::new(da), b);
            lemma_nullable_correct(*a);
            assert(w.subrange(0, 0) =~= Seq::<char>::empty());
            assert(w.subrange(0, w.len() as int) =~= w);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    0 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        *b,
                        w.subrange(i, w.len() as int),
                    );
                if i == 0 {
                    lemma_deriv_correct(*b, c, s);
                } else {
                    lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                    assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                    assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                    assert(matches(da, s.subrange(0, i - 1)));
                    assert(matches(cat, s));
                }
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(cat, s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        *b,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
            if nullable(*a) && matches(deriv(*b, c), s) {
                lemma_deriv_correct(*b, c, s);
                assert(matches(*a, w.subrange(0, 0)));
            }
        },
        Re::Star(a) => {
            let da = deriv(*a, c);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    1 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        r,
                        w.subrange(i, w.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                assert(matches(da, s.subrange(0, i - 1)));
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(deriv(r, c), s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        r,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
        },
        _ => {},
    }
}
// Provided definition (r13_pipelines::derivs, given), copied verbatim.
/// Given: the derivative by every character of `u`, in order.
pub open spec fn derivs(r: Re, u: Seq<char>) -> Re
    decreases u.len(),
{
    if u.len() == 0 {
        r
    } else {
        derivs(deriv(r, u[0]), u.drop_first())
    }
}

// The task (R13.H3 lemma_nullable_derivs_r13): a word matches exactly when its derivatives end in a nullable regex.
pub proof fn lemma_nullable_derivs_r13(r: Re, u: Seq<char>)
    ensures
        nullable(derivs(r, u)) == matches(r, u),
    decreases u.len(),
{
    if u.len() == 0 {
        /*R12_CALLS:c1*/
        assert(u =~= Seq::<char>::empty());
    } else {
        /*R12_CALLS:c2*/
        assert(seq![u[0]] + u.drop_first() =~= u);
    }
}
} // verus!
