// Reference Solution.
/*! R11 metatheory contractor: prove the fixed forward replacement theorem.
Snapshot original models/rules before body edits; verify rule fidelity against
canonical A4 separately. A transport theorem about changed rules can be true
while those rules accept invalid certificates. No model edits are authorized.
*/
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;

verus! {

pub open spec fn rename_char_r11(c: char, from: char, to: char) -> char {
    if c == from {
        to
    } else {
        c
    }
}

pub open spec fn rename_word_r11(s: Seq<char>, from: char, to: char) -> Seq<char> {
    Seq::new(s.len(), |i: int| rename_char_r11(s[i], from, to))
}

pub open spec fn rename_pattern_r11(r: Re, from: char, to: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Eps,
        Re::Chr(c) => Re::Chr(rename_char_r11(c, from, to)),
        Re::Alt(a, b) => Re::Alt(Box::new(rename_pattern_r11(*a, from, to)), Box::new(rename_pattern_r11(*b, from, to))),
        Re::Cat(a, b) => Re::Cat(Box::new(rename_pattern_r11(*a, from, to)), Box::new(rename_pattern_r11(*b, from, to))),
        Re::Star(a) => Re::Star(Box::new(rename_pattern_r11(*a, from, to))),
    }
}

pub open spec fn rules_r11(d: ::rg_re_a4::Derivation, r: ::rg_re_a1::Re, s: Seq<char>) -> bool {
    ::rg_re_a4::valid_word_r10(d, r, s)
}

proof fn rename_split_r11(s: Seq<char>, k: int, from: char, to: char)
    requires
        0 <= k <= s.len(),
    ensures
        rename_word_r11(s, from, to).len() == s.len(),
        rename_word_r11(s, from, to).take(k) == rename_word_r11(s.take(k), from, to),
        rename_word_r11(s, from, to).skip(k) == rename_word_r11(s.skip(k), from, to),
{
    assert(rename_word_r11(s, from, to).take(k) =~= rename_word_r11(s.take(k), from, to));
    assert(rename_word_r11(s, from, to).skip(k) =~= rename_word_r11(s.skip(k), from, to));
}

// item: R11.A1v
proof fn rename_transport_r11(d: ::rg_re_a4::Derivation, r: ::rg_re_a1::Re, s: Seq<char>, from: char, to: char)
    requires
        rules_r11(d, r, s),
    ensures
        rules_r11(d, rename_pattern_r11(r, from, to), rename_word_r11(s, from, to)),
    decreases d,
{
    // @hole-begin R11.A1v
    // did: unfold canonical certificate rules for the current constructor.
    reveal_with_fuel(::rg_re_a4::valid_word_r10, 2);
    // did: unfold replacement only at the current pattern constructor.
    reveal_with_fuel(rename_pattern_r11, 2);
    match d {
        Derivation::DChr => {
            assert(rename_word_r11(s, from, to) =~= seq![rename_char_r11(r->Chr_0, from, to)]);
        },
        Derivation::DAltL(child) => {
            rename_transport_r11(*child, *r->Alt_0, s, from, to);
        },
        Derivation::DAltR(child) => {
            rename_transport_r11(*child, *r->Alt_1, s, from, to);
        },
        Derivation::DCat(k, left, right) => {
            rename_split_r11(s, k as int, from, to);
            rename_transport_r11(*left, *r->Cat_0, s.take(k as int), from, to);
            rename_transport_r11(*right, *r->Cat_1, s.skip(k as int), from, to);
        },
        Derivation::DStarCons(k, left, right) => {
            rename_split_r11(s, k as int, from, to);
            rename_transport_r11(*left, *r->Star_0, s.take(k as int), from, to);
            rename_transport_r11(*right, r, s.skip(k as int), from, to);
        },
        _ => {},
    }
    // @hole-end R11.A1v
}

} // verus!
