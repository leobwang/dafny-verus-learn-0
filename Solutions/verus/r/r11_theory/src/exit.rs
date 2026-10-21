// Reference Solution.
/*! R11 — Theory: the closed-book checkpoint. Standalone A1–A4, fixed relative
certificate rules. Two tasks per language; attempt them with the book closed and
score them with scripts/firsttry.sh R11 --exit. Preserve models and domains.
*/
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;

verus! {

pub open spec fn character_leaves_r11(d: Derivation) -> nat
    decreases d,
{
    match d {
        Derivation::DEps | Derivation::DStarNil => 0,
        Derivation::DChr => 1,
        Derivation::DAltL(child) | Derivation::DAltR(child) => character_leaves_r11(*child),
        Derivation::DCat(_, left, right) | Derivation::DStarCons(_, left, right) => character_leaves_r11(*left) + character_leaves_r11(*right),
    }
}

// item: R11.X1v
// pair: R11.X1d
/// **X1.** A valid certificate has exactly one character leaf per scalar of
/// its word. Prove it by induction on the derivation.
proof fn certificate_length_r11(d: Derivation, r: Re, s: Seq<char>)
    requires
        valid_word_r10(d, r, s),
    ensures
        s.len() == character_leaves_r11(d),
    decreases d,
{
    // @hole-begin R11.X1v
    // did: unfold the fixed model for this constructor obligation.
    reveal_with_fuel(valid_word_r10, 2);
    // did: unfold the leaf count for this constructor.
    reveal_with_fuel(character_leaves_r11, 2);
    match d {
        Derivation::DAltL(child) => {
            certificate_length_r11(*child, *r->Alt_0, s);
        },
        Derivation::DAltR(child) => {
            certificate_length_r11(*child, *r->Alt_1, s);
        },
        Derivation::DCat(k, left, right) => {
            certificate_length_r11(*left, *r->Cat_0, s.take(k as int));
            certificate_length_r11(*right, *r->Cat_1, s.skip(k as int));
        },
        Derivation::DStarCons(k, left, right) => {
            certificate_length_r11(*left, *r->Star_0, s.take(k as int));
            certificate_length_r11(*right, r, s.skip(k as int));
        },
        _ => {},
    }
    // @hole-end R11.X1v
}

pub open spec fn uniform_word_r11(c: char, n: nat) -> Seq<char> {
    Seq::new(n, |i: int| c)
}

proof fn uniform_step_r11(c: char, n: nat)
    requires
        n > 0,
    ensures
        uniform_word_r11(c, n).take(1) == seq![c],
        uniform_word_r11(c, n).skip(1) == uniform_word_r11(c, (n - 1) as nat),
{
    assert(uniform_word_r11(c, n).take(1) =~= seq![c]);
    assert(uniform_word_r11(c, n).skip(1) =~= uniform_word_r11(c, (n - 1) as nat));
}

// item: R11.X2v
// pair: R11.X2d
// triv: { Derivation::DStarNil }
/// **X2.** Build, with a loop, a certificate of Star(Chr(c)) for the word of
/// n copies of c. Remove `external_body` and write the body.
fn repeat_certificate_r11(c: char, n: usize) -> (out: Derivation)
    ensures
        valid_word_r10(out, Re::Star(Box::new(Re::Chr(c))), uniform_word_r11(c, n as nat)),
{
    // ref-begin R11.X2v
    let mut done: usize = 0;
    let mut out = Derivation::DStarNil;
    proof {
        // did: unfold the fixed validity model at this executable constructor.
        reveal_with_fuel(valid_word_r10, 2);
    }
    while done < n
        invariant
            done <= n,
            valid_word_r10(out, Re::Star(Box::new(Re::Chr(c))), uniform_word_r11(c, done as nat)),
        decreases n - done,
    {
        proof {
            uniform_step_r11(c, done as nat + 1);
        }
        out = Derivation::DStarCons(1, Box::new(Derivation::DChr), Box::new(out));
        done = done + 1;
        proof {
            // did: unfold the fixed validity model at this executable constructor.
            reveal_with_fuel(valid_word_r10, 2);
        }
    }
    out
    // ref-end R11.X2v
}

// Given (not an item): the use-site check of X2, through its contract.
fn repeat_certificate_client_r11() {
    let out = repeat_certificate_r11('a', 2);
    proof {
        assert(uniform_word_r11('a', 2) =~= seq!['a', 'a']);
    }
    assert(valid_word_r10(out, Re::Star(Box::new(Re::Chr('a'))), seq!['a', 'a']));
}

} // verus!
