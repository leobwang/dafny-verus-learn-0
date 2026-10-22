// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_star_pow_v"]},{"name":"h1"}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_star_pow_v","start":93,"end":105}]
use vstd::prelude::*;

verus! {

// Provided definitions: rg_re_a1 (Re, nullable, node_count) and rg_re_a2 (deriv), copied
// verbatim; matches_v and power_word are R14's own (r14_smt), verbatim.
pub enum Re {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Re>, Box<Re>),
    Cat(Box<Re>, Box<Re>),
    Star(Box<Re>),
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

pub open spec fn node_count(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Empty => 1,
        Re::Eps => 1,
        Re::Chr(_) => 1,
        Re::Alt(a, b) => 1 + node_count(*a) + node_count(*b),
        Re::Cat(a, b) => 1 + node_count(*a) + node_count(*b),
        Re::Star(a) => 1 + node_count(*a),
    }
}

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

pub open spec fn matches_v(r: Re, s: Seq<char>) -> bool
    decreases r, s.len(),
{
    match r {
        Re::Empty => false,
        Re::Eps => s.len() == 0,
        Re::Chr(c) => s.len() == 1 && s[0] == c,
        Re::Alt(a, b) => matches_v(*a, s) || matches_v(*b, s),
        Re::Cat(a, b) => exists|i: int|
            0 <= i <= s.len() && matches_v(*a, #[trigger] s.subrange(0, i)) && matches_v(
                *b,
                s.subrange(i, s.len() as int),
            ),
        Re::Star(a) => s.len() == 0 || exists|i: int|
            0 < i <= s.len() && matches_v(*a, #[trigger] s.subrange(0, i)) && matches_v(
                r,
                s.subrange(i, s.len() as int),
            ),
    }
}

pub open spec fn power_word(c: char, n: nat) -> Seq<char>
    decreases n,
{
    if n == 0 {
        Seq::empty()
    } else {
        seq![c] + power_word(c, (n - 1) as nat)
    }
}

// The task (R14 H2 lemma_star_pow_v): every power of c matches Star(Chr(c)).
pub proof fn lemma_star_pow_v(c: char, n: nat)
    ensures
        matches_v(Re::Star(Box::new(Re::Chr(c))), power_word(c, n)),
    decreases n,
{
    if n > 0 {
        /*R12_CALLS:c1*/
        let s = power_word(c, n);
        assert(s.subrange(0, 1) =~= seq![c]);
        assert(s.subrange(1, s.len() as int) =~= power_word(c, (n - 1) as nat));
        assert(/*R12_HINT:h1*/ true);
    }
}

} // verus!
