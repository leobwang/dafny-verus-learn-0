//! # R14 — SMT mechanics (Reference Solution)
//!
//! Imports: the given regex spine `rg_re_a1` (`Re`, `node_count`) and `rg_re_a2`
//! (`deriv`); nothing else: no earlier exercise file. R14 states its own copy of the
//! regex semantics, `matches_v`, with triggers chosen here.
//!
//! Done = `scripts/vcheck --gate verus/r/r14_smt` prints only the summary line and exits
//! 0, `scripts/vaudit verus/r/r14_smt` reports no finding, AND
//! `scripts/firsttry.sh R14 --report --strict` exits 0.
//!
//! This file ships with exactly 3 holes: H1–H3.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a2::*;

verus! {

/// R14's own semantics: A1's `matches`, with the triggers stated. A split is found only
/// through a term `s.subrange(0, i)` of the word being split. (A trigger on the recursive
/// call `matches_v(*a, s.subrange(0, i))` would name the fuel-indexed copy of `matches_v`
/// inside its own definition, and no proof outside could match it: §1 of the chapter.)
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

/// Given: `n` copies of `c`.
pub open spec fn power_word(c: char, n: nat) -> Seq<char>
    decreases n,
{
    if n == 0 {
        Seq::empty()
    } else {
        seq![c] + power_word(c, (n - 1) as nat)
    }
}

// item: R14.H1v
// uses: trigger
// pair: R14.H1d
/// **H1.** A word of `a` followed by a word of `b` matches `Cat(a, b)`.
///
/// Reference: the Cat existential is triggered by `s.subrange(0, i)`. With `s = u + v`,
/// asserting `s.subrange(0, u.len()) =~= u` and the matching equation for the rest puts
/// the trigger term in the proof and `u` in its equivalence class, so the known
/// `matches_v(a, u)` and `matches_v(b, v)` give the existential's body at `i = u.len()`.
pub proof fn lemma_cat_intro_v(a: Re, b: Re, u: Seq<char>, v: Seq<char>)
    requires
        matches_v(a, u),
        matches_v(b, v),
    ensures
        matches_v(Re::Cat(Box::new(a), Box::new(b)), u + v),
{
    let s = u + v;
    assert(s.subrange(0, u.len() as int) =~= u);
    assert(s.subrange(u.len() as int, s.len() as int) =~= v);
}

// item: R14.H2v
// uses: trigger
// pair: R14.H2d
/// **H2.** Every power of `c` matches `Star(Chr(c))`.
///
/// Reference: induction on `n`. The first chunk is `seq![c]`, the rest is `power_word(c, n - 1)`,
/// which the recursive call matches; the Star case's trigger needs the term
/// `matches_v(Re::Chr(c), s.subrange(0, 1))`, so the proof asserts it.
pub proof fn lemma_star_pow_v(c: char, n: nat)
    ensures
        matches_v(Re::Star(Box::new(Re::Chr(c))), power_word(c, n)),
    decreases n,
{
    if n > 0 {
        lemma_star_pow_v(c, (n - 1) as nat);
        let s = power_word(c, n);
        assert(s.subrange(0, 1) =~= seq![c]);
        assert(s.subrange(1, s.len() as int) =~= power_word(c, (n - 1) as nat));
        assert(matches_v(Re::Chr(c), s.subrange(0, 1)));
    }
}

// item: R14.H3v
// uses: nonlinear-arith, fuel
// pair: R14.H3d
/// **H3.** A derivative is at most twice the square of its regex's size.
///
/// Reference: structural induction; in the Alt, Cat and Star cases the induction
/// hypotheses bound each derivative by `2 x^2`, and what is left is a product inequality
/// (`2 + 2a^2 + b + 2b^2 <= 2(1 + a + b)^2` in the nullable Cat case), which
/// `by (nonlinear_arith)` proves in a helper of its own.
pub proof fn lemma_deriv_size_v(r: Re, c: char)
    ensures
        node_count(deriv(r, c)) <= 2 * node_count(r) * node_count(r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            lemma_deriv_size_v(*a, c);
            lemma_deriv_size_v(*b, c);
            lemma_square_growth(node_count(*a), node_count(*b));
        },
        Re::Cat(a, b) => {
            lemma_deriv_size_v(*a, c);
            lemma_deriv_size_v(*b, c);
            lemma_square_growth(node_count(*a), node_count(*b));
            // did: unfold node_count through the Alt and the Cat of the nullable case
            reveal_with_fuel(node_count, 3);
        },
        Re::Star(a) => {
            lemma_deriv_size_v(*a, c);
            lemma_square_growth(node_count(*a), 0);
        },
        _ => {},
    }
}

// reference-only: the learner's own helper, the product inequality every case needs.
pub proof fn lemma_square_growth(x: nat, y: nat)
    ensures
        2 + 2 * x * x + y + 2 * y * y <= 2 * (1 + x + y) * (1 + x + y),
        2 + 2 * x * x + x <= 2 * (1 + x) * (1 + x),
{
    // did: the two products, expanded by the nonlinear prover
    assert(2 + 2 * x * x + y + 2 * y * y <= 2 * (1 + x + y) * (1 + x + y)) by (nonlinear_arith);
    // did: the one-variable case
    assert(2 + 2 * x * x + x <= 2 * (1 + x) * (1 + x)) by (nonlinear_arith);
}

} // verus!
