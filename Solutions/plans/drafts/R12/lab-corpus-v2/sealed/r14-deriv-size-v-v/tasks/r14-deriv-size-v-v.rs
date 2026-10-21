// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_deriv_size_v","lemma_square_growth"]},{"name":"c2","kind":"calls","callees":["lemma_deriv_size_v","lemma_square_growth"]},{"name":"c3","kind":"calls","callees":["lemma_deriv_size_v","lemma_square_growth"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_deriv_size_v","start":103,"end":121}]
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

// Provided fact (R14's lemma_square_growth), complete.
pub proof fn lemma_square_growth(x: nat, y: nat)
    ensures
        2 + 2 * x * x + y + 2 * y * y <= 2 * (1 + x + y) * (1 + x + y),
        2 + 2 * x * x + x <= 2 * (1 + x) * (1 + x),
{
    assert(2 + 2 * x * x + y + 2 * y * y <= 2 * (1 + x + y) * (1 + x + y)) by (nonlinear_arith);
    assert(2 + 2 * x * x + x <= 2 * (1 + x) * (1 + x)) by (nonlinear_arith);
}

// The task (R14 H3 lemma_deriv_size_v): a derivative is at most twice the square of its size.
pub proof fn lemma_deriv_size_v(r: Re, c: char)
    ensures
        node_count(deriv(r, c)) <= 2 * node_count(r) * node_count(r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            /*R12_CALLS:c1*/
        },
        Re::Cat(a, b) => {
            /*R12_CALLS:c2*/
            reveal_with_fuel(node_count, 3);
        },
        Re::Star(a) => {
            /*R12_CALLS:c3*/
        },
        _ => {},
    }
}

} // verus!
