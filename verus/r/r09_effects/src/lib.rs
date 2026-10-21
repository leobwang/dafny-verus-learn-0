//! # R09 — Effects (exercises)
//!
//! Standalone R track. Import only the frozen layers A1, A1b, A2 and A3; no earlier
//! learner file is needed. The paired exercise is
//! dafny/R/R09_Effects/std/R09_Effects.dfy.
//!
//! Before reading the chapter, attempt T1 closed book: the given reader W1 sits
//! directly above it. Fill the five predictions (slots/R09.slots,
//! specimens/R09/P2v.rs.specimen, specimens/R09/P4v.rs.specimen and
//! dafny/checks/R09_checks.dfy) and record the first attempts with
//! scripts/firsttry.sh R09 --check before running their scenarios. Six typed holes
//! ship in this crate, twelve across the pair.
//!
//! File order: the test-out (W1, T1), the mirror, the worked examples and the
//! given infrastructure (the size model, W3 the parser around the holes, the
//! division guard, W2 the checked cost, the scalar conversion, the lowering, the
//! frontend, W4 the repetition helpers), the holes H1 to H5 with the given clients
//! of T1 and H5, then the recognise cards. Positions count Unicode scalars,
//! classes lie below 0xD800 and counted bounds are one character '0' to '9'.
//!
//! Done: the crate gates with zero tool-counted holes, vaudit is clean,
//! specfreeze --check R09 passes and firsttry's strict report is OK. Preserve the
//! given contracts and implementations. /tutor R09 is available after an attempt.
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a3::*;

// =============================================================================
// Test-out (closed book): W1 is given; T1 is the hole
// =============================================================================

verus! {

/// A cursor over a mutable text: both fields can change, so a promise that the
/// text's view is unchanged is a real obligation.
pub struct EffectCursorR09 {
    pub text: Vec<char>,
    pub position: usize,
}

// item: R09.W1v
/// The single-bound reader: an accepted character gives its value, a rejected
/// one gives an error at the position the caller supplies.
fn read_bound_r09(c: char, pos: usize, len: usize) -> (res: Result<u32, PErr>)
    requires
        pos <= len,
    ensures
        match res {
            Ok(n) => is_bound_char(c) && n == bound_value(c),
            Err(e) => !is_bound_char(c) && e.pos == pos,
        },
{
    if c < '0' || c > '9' {
        Err(PErr { pos, kind: ErrKind::UnexpectedChar })
    } else {
        Ok((c as u32) - ('0' as u32))
    }
}

// item: R09.T1v
// pair: R09.T1d
// uses: error-propagation, old
/// **T1.** Closed book: read one bound at the cursor and move the cursor one
/// scalar on, whatever the character. Remove `external_body` and propagate W1's
/// failure with `?`. Which state must already be updated when `?` returns early,
/// and which position must the error carry?
#[verifier::external_body]
fn read_bound_cursor_r09(cur: &mut EffectCursorR09) -> (res: Result<u32, PErr>)
    requires
        old(cur).position < old(cur).text.len(),
    ensures
        final(cur).text@ == old(cur).text@,
        final(cur).position == old(cur).position + 1,
        match res {
            Ok(n) => is_bound_char(old(cur).text@[old(cur).position as int]) && n == bound_value(old(cur).text@[old(cur).position as int]),
            Err(e) => !is_bound_char(old(cur).text@[old(cur).position as int]) && e.pos == old(cur).position,
        },
{
    unimplemented!()
}
// Hint(1): `?` returns the error at once: every `ensures` clause, the cursor's included, must hold there.
// Hint(2): read the character and the old position into locals before you write `cur.position`.
// Uncomment as you go:
// fn read_bound_cursor_check() {
//     let mut text: Vec<char> = Vec::new();
//     text.push('4');
//     text.push('}');
//     let mut cur = EffectCursorR09 { text, position: 0 };
//     let r = read_bound_cursor_r09(&mut cur);
//     assert(r == Ok::<u32, PErr>(4));
//     assert(cur.position == 1);
// }

} // verus!

// =============================================================================
// The fidelity triangle's third corner: a transcribed mirror of the parser's
// contract. Both implications verify; they relate two statements and say
// nothing about whether either is the grammar intended.
// =============================================================================

verus! {

// Existing guarantees only: these predicates do not define the full grammar.
pub open spec fn original_contract_r09(s: Seq<char>, r: Result<Syn, PErr>) -> bool {
    &&& match r {
        Ok(t) => wf(t, s.len()) && t.span.lo == 0 && t.span.hi == s.len(),
        Err(e) => e.pos <= s.len(),
    }
    &&& no_special_from(s, 0) ==> r is Ok && matches(lower(r->Ok_0), s) && lowering_nodes_r09(r->Ok_0) == (if s.len() == 0 { 1int } else { 2 * s.len() - 1 })
}

pub open spec fn transcribed_mirror_r09(s: Seq<char>, r: Result<Syn, PErr>) -> bool {
    match r {
        Err(e) => e.pos <= s.len() && !no_special_from(s, 0),
        Ok(t) => wf(t, s.len()) && t.span.lo == 0 && t.span.hi == s.len() && (no_special_from(s, 0) ==> matches(lower(t), s) && lowering_nodes_r09(t) == (if s.len() == 0 { 1int } else { 2 * s.len() - 1 })),
    }
}

// Both implications are relative to this mirror, not to independent intent.
proof fn both_mirror_implications_r09(s: Seq<char>, r: Result<Syn, PErr>)
    ensures
        original_contract_r09(s, r) ==> transcribed_mirror_r09(s, r),
        transcribed_mirror_r09(s, r) ==> original_contract_r09(s, r),
{
    match r {
        Ok(_) => {},
        Err(_) => {},
    }
}

fn parse_relative_mirror_r09(s: &Vec<char>) -> (r: Result<Syn, PErr>)
    ensures
        original_contract_r09(s@, r) && transcribed_mirror_r09(s@, r),
{
    let r = parse(s);
    proof {
        both_mirror_implications_r09(s@, r);
    }
    r
}

} // verus!

// =============================================================================
// Worked examples and the given infrastructure
// =============================================================================

verus! {

// The logical size of a lowering, computed over the syntax tree before any
// expansion is built.
pub open spec fn range_nodes_r09(lo: u32, hi: u32) -> nat {
    if range_valid(lo, hi) {
        (2 * ((hi as int) - (lo as int)) + 1) as nat
    } else {
        1
    }
}

pub open spec fn class_nodes_r09(xs: Seq<(u32, u32)>) -> nat
    decreases xs.len(),
{
    if xs.len() == 0 {
        1
    } else {
        1 + range_nodes_r09(xs[0].0, xs[0].1) + class_nodes_r09(xs.drop_first())
    }
}

pub open spec fn lowering_nodes_r09(t: Syn) -> nat
    decreases t,
{
    match t.node {
        SyntaxKind::Eps | SyntaxKind::Chr(_) => 1,
        SyntaxKind::Class(cc) => class_nodes_r09(cc.ranges_spec()),
        SyntaxKind::Alt(a, b) | SyntaxKind::Cat(a, b) => 1 + lowering_nodes_r09(*a) + lowering_nodes_r09(*b),
        SyntaxKind::Star(a) => 1 + lowering_nodes_r09(*a),
        SyntaxKind::Plus(a) => 2 + 2 * lowering_nodes_r09(*a),
        SyntaxKind::Opt(a) => 2 + lowering_nodes_r09(*a),
        SyntaxKind::Group(a) => lowering_nodes_r09(*a),
        SyntaxKind::RepRange(a, n, m) => 3 + (n as nat) * (lowering_nodes_r09(*a) + 1) + ((m as nat - n as nat) as nat) * (lowering_nodes_r09(*a) + 3),
    }
}

proof fn lemma_copies_nodes_r09(r: Re, k: nat)
    ensures
        node_count(copies(r, k)) == 1 + k * (node_count(r) + 1),
    decreases k,
{
    reveal_with_fuel(node_count, 2);
    reveal_with_fuel(copies, 2);
    let b = node_count(r) as int;
    if k > 0 {
        let km = (k - 1) as nat;
        lemma_copies_nodes_r09(r, km);
        let total = node_count(copies(r, k)) as int;
        let child = node_count(copies(r, km)) as int;
        assert(total == 1 + b + child);
        assert(total == 1 + k * (b + 1)) by (nonlinear_arith)
            requires
                total == 1 + b + child,
                child == 1 + km * (b + 1),
                k == km + 1,
        ;
    } else {
        assert(1 + k * (b + 1) == 1) by (nonlinear_arith)
            requires
                k == 0,
        ;
    }
}

proof fn lemma_optional_nodes_r09(r: Re, k: nat)
    ensures
        node_count(copies_up_to(r, k)) == 1 + k * (node_count(r) + 3),
    decreases k,
{
    reveal_with_fuel(node_count, 3);
    reveal_with_fuel(copies_up_to, 2);
    let b = node_count(r) as int;
    if k > 0 {
        let km = (k - 1) as nat;
        lemma_optional_nodes_r09(r, km);
        let total = node_count(copies_up_to(r, k)) as int;
        let child = node_count(copies_up_to(r, km)) as int;
        assert(total == 3 + b + child);
        assert(total == 1 + k * (b + 3)) by (nonlinear_arith)
            requires
                total == 3 + b + child,
                child == 1 + km * (b + 3),
                k == km + 1,
        ;
    } else {
        assert(1 + k * (b + 3) == 1) by (nonlinear_arith)
            requires
                k == 0,
        ;
    }
}

proof fn lemma_range_nodes_r09(lo: u32, hi: u32)
    requires
        range_valid(lo, hi),
    ensures
        node_count(range_re(lo, hi)) == range_nodes_r09(lo, hi),
    decreases hi - lo,
{
    reveal_with_fuel(node_count, 2);
    if lo < hi {
        lemma_range_nodes_r09((lo + 1) as u32, hi);
    }
}

proof fn lemma_class_nodes_r09(xs: Seq<(u32, u32)>)
    requires
        class_valid(xs),
    ensures
        node_count(class_re(xs)) == class_nodes_r09(xs),
    decreases xs.len(),
{
    if xs.len() > 0 {
        assert forall|i: int| 0 <= i < xs.drop_first().len() implies range_valid(xs.drop_first()[i].0, xs.drop_first()[i].1) by {
            assert(xs.drop_first()[i] == xs[i + 1]);
        }
        lemma_range_nodes_r09(xs[0].0, xs[0].1);
        lemma_class_nodes_r09(xs.drop_first());
    }
}

pub proof fn lemma_lowering_nodes_r09(t: Syn, len: nat)
    requires
        wf(t, len),
    ensures
        node_count(lower(t)) == lowering_nodes_r09(t),
    decreases t,
{
    reveal_with_fuel(node_count, 3);
    match t.node {
        SyntaxKind::Eps | SyntaxKind::Chr(_) => {},
        SyntaxKind::Class(cc) => {
            lemma_class_nodes_r09(cc.ranges_spec());
        },
        SyntaxKind::Alt(a, b) | SyntaxKind::Cat(a, b) => {
            lemma_lowering_nodes_r09(*a, len);
            lemma_lowering_nodes_r09(*b, len);
        },
        SyntaxKind::Star(a) | SyntaxKind::Plus(a) | SyntaxKind::Opt(a) | SyntaxKind::Group(a) => {
            lemma_lowering_nodes_r09(*a, len);
        },
        SyntaxKind::RepRange(a, n, m) => {
            lemma_lowering_nodes_r09(*a, len);
            lemma_copies_nodes_r09(lower(*a), n as nat);
            lemma_optional_nodes_r09(lower(*a), (m as nat - n as nat) as nat);
        },
    }
}

} // verus!

// The parser over positioned A3. Its contracts are safety and the literal
// guarantee; the grammar's fidelity is exercised by tools/R09/check_frontend.py.
use rg_re_a2::*;

verus! {

pub open spec fn no_special_from(s: Seq<char>, i: int) -> bool {
    forall|k: int| i <= k < s.len() ==> !is_meta(s[k])
}

pub proof fn lemma_literal_append_r09(a: Re, u: Seq<char>, c: char)
    requires
        matches(a, u),
    ensures
        matches(Re::Cat(Box::new(a), Box::new(Re::Chr(c))), u + seq![c]),
{
    let w = u + seq![c];
    reveal_with_fuel(matches, 2);
    assert(w.subrange(0, u.len() as int) =~= u);
    assert(w.subrange(u.len() as int, w.len() as int) =~= seq![c]);
    assert(exists|i: int| 0 <= i <= w.len() && matches(a, #[trigger] w.subrange(0, i)) && matches(Re::Chr(c), w.subrange(i, w.len() as int))) by {
        let i = u.len() as int;
        assert(matches(a, w.subrange(0, i)));
        assert(matches(Re::Chr(c), w.subrange(i, w.len() as int)));
    }
}

pub open spec fn counted_node(x: Syn, n: nat, m: nat, k: int) -> Syn {
    Syn { span: Span { lo: x.span.lo, hi: k as usize }, node: SyntaxKind::RepRange(Box::new(x), n as u32, m as u32) }
}

// item: R09.W3v
/// The parser around the holes: four mutually recursive functions, each
/// propagating a failure with `?`. Their contracts are safety (spans nest, an
/// error position is in range) plus the literal guarantee: an input with no
/// special character parses, spans the whole input, matches itself and has the
/// printed size. `parse_post` calls H1's `parse_counted`; `parse_atom` calls
/// H2's `class_items`; neither call needs more than their contracts.
pub fn parse_alt(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i <= s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        no_special_from(s@, i as int) ==> res is Ok && res->Ok_0.1 == s.len() && matches(lower(res->Ok_0.0), s@.subrange(i as int, s.len() as int)) && lowering_nodes_r09(res->Ok_0.0) == (if i == s.len() { 1int } else { 2 * (s.len() - i) - 1 }),
    decreases s.len() - i, 3nat,
{
    let (mut x, mut j) = parse_cat(s, i)?;
    while j < s.len() && s[j] == '|'
        invariant
            i <= j <= s.len(),
            wf(x, s.len() as nat),
            x.span.lo == i,
            x.span.hi == j,
            no_special_from(s@, i as int) ==> j == s.len() && matches(lower(x), s@.subrange(i as int, s.len() as int)) && lowering_nodes_r09(x) == (if i == s.len() { 1int } else { 2 * (s.len() - i) - 1 }),
        decreases s.len() - j,
    {
        let (y, k) = parse_cat(s, j + 1)?;
        x = Syn { node: SyntaxKind::Alt(Box::new(x), Box::new(y)), span: Span { lo: i, hi: k } };
        j = k;
    }
    Ok((x, j))
}

pub fn parse_cat(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i <= s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        no_special_from(s@, i as int) ==> res is Ok && res->Ok_0.1 == s.len() && matches(lower(res->Ok_0.0), s@.subrange(i as int, s.len() as int)) && lowering_nodes_r09(res->Ok_0.0) == (if i == s.len() { 1int } else { 2 * (s.len() - i) - 1 }),
    decreases s.len() - i, 2nat,
{
    let mut x = Syn { node: SyntaxKind::Eps, span: Span { lo: i, hi: i } };
    let mut j = i;
    let mut first = true;
    while j < s.len() && s[j] != ')' && s[j] != '|'
        invariant
            i <= j <= s.len(),
            wf(x, s.len() as nat),
            x.span.lo == i,
            x.span.hi == j,
            first <==> j == i,
            no_special_from(s@, i as int) ==> no_special_from(s@, j as int) && matches(lower(x), s@.subrange(i as int, j as int)) && lowering_nodes_r09(x) == (if j == i { 1int } else { 2 * (j - i) - 1 }),
        decreases s.len() - j,
    {
        let (y, k) = parse_post(s, j)?;
        proof {
            if no_special_from(s@, i as int) {
                reveal_with_fuel(lower, 2);
                reveal_with_fuel(lowering_nodes_r09, 2);
                assert(y == (Syn { node: SyntaxKind::Chr(s@[j as int]), span: Span { lo: j, hi: (j + 1) as usize } }) && k == j + 1);
                assert(s@.subrange(i as int, j + 1) =~= s@.subrange(i as int, j as int) + seq![s@[j as int]]);
                if first {
                    assert(s@.subrange(i as int, k as int) =~= seq![s@[j as int]]);
                    reveal_with_fuel(matches, 2);
                } else {
                    lemma_literal_append_r09(lower(x), s@.subrange(i as int, j as int), s@[j as int]);
                }
            }
        }
        x = if first {
            y
        } else {
            Syn { node: SyntaxKind::Cat(Box::new(x), Box::new(y)), span: Span { lo: i, hi: k } }
        };
        proof {
            if no_special_from(s@, i as int) {
                assert(no_special_from(s@, k as int));
                reveal_with_fuel(lower, 2);
                reveal_with_fuel(lowering_nodes_r09, 2);
                assert(matches(lower(x), s@.subrange(i as int, k as int)));
            }
        }
        first = false;
        j = k;
    }
    Ok((x, j))
}

pub fn parse_post(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i < s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        res is Ok ==> res->Ok_0.1 > i,
        no_special_from(s@, i as int) ==> res == Ok::<(Syn, usize), PErr>((Syn { node: SyntaxKind::Chr(s@[i as int]), span: Span { lo: i, hi: (i + 1) as usize } }, (i + 1) as usize)),
    decreases s.len() - i, 1nat,
{
    let (mut x, mut j) = parse_atom(s, i)?;
    while j < s.len() && (s[j] == '*' || s[j] == '+' || s[j] == '?' || s[j] == '{')
        invariant
            i < j <= s.len(),
            wf(x, s.len() as nat),
            x.span.lo == i,
            x.span.hi == j,
            no_special_from(s@, i as int) ==> x == (Syn { node: SyntaxKind::Chr(s@[i as int]), span: Span { lo: i, hi: (i + 1) as usize } }) && j == i + 1,
        decreases s.len() - j,
    {
        let c = s[j];
        if c == '{' {
            let (y, k) = parse_counted(s, j, x)?;
            x = y;
            j = k;
        } else {
            let node = if c == '*' {
                SyntaxKind::Star(Box::new(x))
            } else if c == '+' {
                SyntaxKind::Plus(Box::new(x))
            } else {
                SyntaxKind::Opt(Box::new(x))
            };
            x = Syn { node, span: Span { lo: i, hi: j + 1 } };
            j = j + 1;
        }
    }
    Ok((x, j))
}

pub fn parse_atom(s: &Vec<char>, i: usize) -> (res: Result<(Syn, usize), PErr>)
    requires
        i < s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        res is Ok ==> res->Ok_0.1 > i,
        no_special_from(s@, i as int) ==> res == Ok::<(Syn, usize), PErr>((Syn { node: SyntaxKind::Chr(s@[i as int]), span: Span { lo: i, hi: (i + 1) as usize } }, (i + 1) as usize)),
    decreases s.len() - i, 0nat,
{
    let c = s[i];
    if c == '(' {
        let (x, j) = parse_alt(s, i + 1)?;
        if j < s.len() && s[j] == ')' {
            Ok((Syn { node: SyntaxKind::Group(Box::new(x)), span: Span { lo: i, hi: j + 1 } }, j + 1))
        } else {
            Err(PErr { pos: j, kind: ErrKind::UnclosedParen })
        }
    } else if c == '[' {
        let (xs, j) = class_items(s, i + 1, CharClass::class_empty())?;
        Ok((Syn { node: SyntaxKind::Class(xs), span: Span { lo: i, hi: j } }, j))
    } else if c == '\\' {
        if i + 1 < s.len() {
            Ok((Syn { node: SyntaxKind::Chr(s[i + 1]), span: Span { lo: i, hi: i + 2 } }, i + 2))
        } else {
            Err(PErr { pos: i + 1, kind: ErrKind::UnexpectedEnd })
        }
    } else if c == '*' || c == '+' || c == '?' || c == '{' || c == '}' || c == ']' || c == ')' || c == '|' {
        Err(PErr { pos: i, kind: ErrKind::UnexpectedChar })
    } else {
        Ok((Syn { node: SyntaxKind::Chr(c), span: Span { lo: i, hi: i + 1 } }, i + 1))
    }
}

pub fn parse(s: &Vec<char>) -> (res: Result<Syn, PErr>)
    ensures
        no_special_from(s@, 0) ==> res is Ok && matches(lower(res->Ok_0), s@) && lowering_nodes_r09(res->Ok_0) == (if s.len() == 0 { 1int } else { 2 * s.len() - 1 }),
        match res {
            Ok(t) => wf(t, s.len() as nat) && t.span.lo == 0 && t.span.hi == s.len(),
            Err(e) => e.pos <= s.len(),
        },
{
    let (x, j) = parse_alt(s, 0)?;
    proof {
        assert(s@.subrange(0, s.len() as int) =~= s@);
    }
    if j == s.len() {
        Ok(x)
    } else {
        Err(PErr { pos: j, kind: ErrKind::UnexpectedChar })
    }
}

} // verus!

use vstd::arithmetic::div_mod::{lemma_fundamental_div_mod, lemma_mod_bound};
use vstd::arithmetic::mul::lemma_mul_is_commutative;

verus! {

// The quotient guard: for a positive divisor, comparing a factor with a
// quotient decides the product comparison, without forming the product.
proof fn quotient_product_guard_r09(b: int, q: int, r: int, d: int)
    requires
        d > 0,
        0 <= r < d,
    ensures
        (b <= q) == (b * d <= q * d + r),
{
    assert((b <= q) == (b * d <= q * d + r)) by (nonlinear_arith)
        requires
            d > 0,
            0 <= r < d,
    ;
}

proof fn division_budget_guard_r09(base: int, space: int, copies: int)
    requires
        base >= 0,
        space >= 0,
        copies > 0,
    ensures
        (base <= space / copies) == (base * copies <= space),
{
    lemma_fundamental_div_mod(space, copies);
    lemma_mod_bound(space, copies);
    quotient_product_guard_r09(base, space / copies, space % copies, copies);
    lemma_mul_is_commutative(copies, space / copies);
}

// Checked addition: each guard comes before the subtraction or addition it
// protects, so no intermediate leaves u32.
fn checked_add_cost_r09(a: u32, b: u32, extra: u32, cap: u32) -> (res: Option<u32>)
    ensures
        match res {
            Some(n) => n <= cap && (n as int) == (a as int) + (b as int) + (extra as int),
            None => (a as int) + (b as int) + (extra as int) > (cap as int),
        },
{
    if extra > cap {
        return None;
    }
    if a > cap - extra {
        return None;
    }
    if b > cap - extra - a {
        return None;
    }
    Some(a + b + extra)
}

fn checked_class_cost_r09(cc: &CharClass, cap: u32) -> (res: Option<u32>)
    requires
        class_valid(cc.ranges_spec()),
    ensures
        match res {
            Some(n) => n <= cap && n == class_nodes_r09(cc.ranges_spec()),
            None => class_nodes_r09(cc.ranges_spec()) > cap,
        },
{
    let rs = cc.ranges();
    let ghost xs = cc.ranges_spec();
    proof {
        assert(class_nodes_r09(xs) >= 1);
    }
    if cap < 1 {
        return None;
    }
    let mut cost: u32 = 1;
    let mut i: usize = 0;
    proof {
        assert(xs.subrange(0, rs.len() as int) =~= xs);
    }
    while i < rs.len()
        invariant
            rs@ == xs,
            xs == cc.ranges_spec(),
            i <= rs.len(),
            cost <= cap,
            class_valid(xs),
            (cost as nat) + class_nodes_r09(xs.subrange(i as int, rs.len() as int)) == class_nodes_r09(xs) + 1,
        decreases rs.len() - i,
    {
        let (lo, hi) = rs[i];
        let width = hi - lo;
        let range: u32 = 2 * width + 1;
        proof {
            let suffix = xs.subrange(i as int, rs.len() as int);
            let tail = xs.subrange(i + 1, rs.len() as int);
            assert(suffix[0] == xs[i as int]);
            assert(suffix.drop_first() =~= tail);
            assert(class_nodes_r09(tail) >= 1);
            assert(range == range_nodes_r09(lo, hi));
        }
        cost = checked_add_cost_r09(cost, range, 1, cap)?;
        i = i + 1;
    }
    proof {
        assert(xs.subrange(rs.len() as int, rs.len() as int) =~= Seq::<(u32, u32)>::empty());
    }
    Some(cost)
}

proof fn lemma_repetition_cost_grows_r09(base: nat, n: nat, m: nat)
    requires
        n <= m,
        m > 0,
    ensures
        3 + n * (base + 1) + (m - n) * (base + 3) >= base,
{
    assert(3 + n * (base + 1) + (m - n) * (base + 3) >= base) by (nonlinear_arith)
        requires
            n <= m,
            m > 0,
            base >= 0,
            n >= 0,
    ;
}

// item: R09.W2v
/// The structural cost checker: each recursive result is unwrapped with `?`,
/// so a child over the cap returns `None` at once, and every sum goes through
/// the checked addition above. A zero upper count never visits its child.
fn checked_lowering_cost_r09(t: &Syn, len: usize, cap: u32) -> (res: Option<u32>)
    requires
        wf(*t, len as nat),
    ensures
        match res {
            Some(n) => n <= cap && n == lowering_nodes_r09(*t),
            None => lowering_nodes_r09(*t) > cap,
        },
    decreases *t,
{
    reveal_with_fuel(lowering_nodes_r09, 2);
    let result = match &t.node {
        SyntaxKind::Eps | SyntaxKind::Chr(_) => {
            if cap >= 1 {
                Some(1)
            } else {
                None
            }
        },
        SyntaxKind::Class(cc) => checked_class_cost_r09(cc, cap),
        SyntaxKind::Alt(a, b) | SyntaxKind::Cat(a, b) => {
            let left = checked_lowering_cost_r09(a, len, cap)?;
            let right = checked_lowering_cost_r09(b, len, cap)?;
            checked_add_cost_r09(left, right, 1, cap)
        },
        SyntaxKind::Star(a) => {
            let child = checked_lowering_cost_r09(a, len, cap)?;
            checked_add_cost_r09(child, 0, 1, cap)
        },
        SyntaxKind::Plus(a) => {
            let child = checked_lowering_cost_r09(a, len, cap)?;
            checked_add_cost_r09(child, child, 2, cap)
        },
        SyntaxKind::Opt(a) => {
            let child = checked_lowering_cost_r09(a, len, cap)?;
            checked_add_cost_r09(child, 0, 2, cap)
        },
        SyntaxKind::Group(a) => checked_lowering_cost_r09(a, len, cap),
        SyntaxKind::RepRange(a, n, m) => {
            if *m == 0 {
                proof {
                    let base = lowering_nodes_r09(**a) as int;
                    assert(3 + (*n as int) * (base + 1) + ((*m as int) - (*n as int)) * (base + 3) == 3) by (nonlinear_arith)
                        requires
                            *m == 0,
                            *n == 0,
                    ;
                    assert(lowering_nodes_r09(*t) == 3);
                }
                checked_add_cost_r09(0, 0, 3, cap)
            } else {
                proof {
                    lemma_repetition_cost_grows_r09(lowering_nodes_r09(**a), *n as nat, *m as nat);
                }
                let child = checked_lowering_cost_r09(a, len, cap)?;
                let result = repeat_expansion_budget_r09(child, *n, *m, cap);
                proof {
                    let base = lowering_nodes_r09(**a) as int;
                    assert(3 + (*n as int) * (base + 1) + ((*m as int) - (*n as int)) * (base + 3) == 3 + base * (*m as int) + (*n as int) + 3 * ((*m as int) - (*n as int))) by (nonlinear_arith);
                }
                proof {
                    assert(match result {
                        Some(n) => n <= cap && n == lowering_nodes_r09(*t),
                        None => lowering_nodes_r09(*t) > cap,
                    });
                }
                result
            }
        },
    };
    assert(match result {
        Some(n) => n <= cap && n == lowering_nodes_r09(*t),
        None => lowering_nodes_r09(*t) > cap,
    });
    result
}

} // verus!

use vstd::utf8::*;
use vstd::string::{StrSliceExecFns, StringSliceAdditionalSpecFns};

verus! {

// A scalar below the class domain becomes a char through the pinned UTF-8
// library contract: the encoded bytes are proved to decode to the one char.
fn scalar_char_r09(n: u32) -> (c: char)
    requires
        is_scalar(n),
    ensures
        c as u32 == n,
        c == n as char,
{
    let ghost wanted = n as char;
    proof {
        assert(wanted as u32 == n);
    }
    let mut bytes: Vec<u8> = Vec::new();
    if n <= 0x7f {
        bytes.push((n & 0x7f) as u8);
    } else if n <= 0x7ff {
        bytes.push(0xc0 | ((n >> 6) & 0x1f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    } else if n <= 0xffff {
        bytes.push(0xe0 | ((n >> 12) & 0xf) as u8);
        bytes.push(0x80 | ((n >> 6) & 0x3f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    } else {
        bytes.push(0xf0 | ((n >> 18) & 0x7) as u8);
        bytes.push(0x80 | ((n >> 12) & 0x3f) as u8);
        bytes.push(0x80 | ((n >> 6) & 0x3f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    }
    proof {
        assert(bytes@ =~= encode_scalar(n));
        assert(seq![wanted].drop_first() =~= Seq::<char>::empty());
        reveal_with_fuel(encode_utf8, 2);
        assert(encode_utf8(seq![wanted]) =~= encode_scalar(n));
        encode_utf8_valid_utf8(seq![wanted]);
    }
    let s = unsafe { str::from_utf8_unchecked(bytes.as_slice()) };
    proof {
        encode_utf8_decode_utf8(seq![wanted]);
        encode_utf8_decode_utf8(s@);
        assert(s@ =~= seq![wanted]);
    }
    s.get_char(0)
}

fn range_lower_exec_r09(lo: u32, hi: u32) -> (out: Re)
    requires
        range_valid(lo, hi),
    ensures
        out == range_re(lo, hi),
{
    let mut n = hi;
    proof {
        assert(is_scalar(hi));
    }
    let last = scalar_char_r09(hi);
    let mut out = Re::Chr(last);
    while n > lo
        invariant
            lo <= n <= hi,
            hi < CLASS_MAX,
            out == range_re(n, hi),
        decreases n - lo,
    {
        n = n - 1;
        proof {
            assert(is_scalar(n));
        }
        let c = scalar_char_r09(n);
        out = Re::Alt(Box::new(Re::Chr(c)), Box::new(out));
    }
    out
}

fn class_lower_exec_r09(cc: &CharClass) -> (out: Re)
    requires
        class_valid(cc.ranges_spec()),
    ensures
        out == class_re(cc.ranges_spec()),
{
    let rs = cc.ranges();
    let ghost xs = cc.ranges_spec();
    let mut i = rs.len();
    let mut out = Re::Empty;
    while i > 0
        invariant
            rs@ == xs,
            xs == cc.ranges_spec(),
            i <= rs.len(),
            class_valid(xs),
            out == class_re(xs.subrange(i as int, rs.len() as int)),
        decreases i,
    {
        i = i - 1;
        let (lo, hi) = rs[i];
        let first = range_lower_exec_r09(lo, hi);
        proof {
            let suffix = xs.subrange(i as int, rs.len() as int);
            assert(suffix[0] == xs[i as int]);
            assert(suffix.drop_first() =~= xs.subrange(i + 1, rs.len() as int));
        }
        out = Re::Alt(Box::new(first), Box::new(out));
    }
    proof {
        assert(xs.subrange(0, rs.len() as int) =~= xs);
    }
    out
}

fn copies_lower_exec_r09(r: &Re, k: u32) -> (out: Re)
    ensures
        out == copies(*r, k as nat),
{
    let mut i: u32 = 0;
    let mut out = Re::Eps;
    while i < k
        invariant
            i <= k,
            out == copies(*r, i as nat),
        decreases k - i,
    {
        let first = copy_re(r);
        out = Re::Cat(Box::new(first), Box::new(out));
        i = i + 1;
    }
    out
}

fn optional_lower_exec_r09(r: &Re, k: u32) -> (out: Re)
    ensures
        out == copies_up_to(*r, k as nat),
{
    let mut i: u32 = 0;
    let mut out = Re::Eps;
    while i < k
        invariant
            i <= k,
            out == copies_up_to(*r, i as nat),
        decreases k - i,
    {
        let first = copy_re(r);
        out = Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(first), Box::new(out))));
        i = i + 1;
    }
    out
}

fn repetition_lower_exec_r09(r: &Re, n: u32, m: u32) -> (out: Re)
    requires
        n <= m,
    ensures
        out == rep_range(*r, n as nat, m as nat),
{
    let fixed = copies_lower_exec_r09(r, n);
    let optional = optional_lower_exec_r09(r, m - n);
    Re::Cat(Box::new(fixed), Box::new(optional))
}

fn lowering_exec_r09(t: &Syn, len: usize) -> (out: Re)
    requires
        wf(*t, len as nat),
    ensures
        out == lower(*t),
    decreases *t,
{
    match &t.node {
        SyntaxKind::Eps => Re::Eps,
        SyntaxKind::Chr(c) => Re::Chr(*c),
        SyntaxKind::Class(cc) => class_lower_exec_r09(cc),
        SyntaxKind::Alt(a, b) => {
            let left = lowering_exec_r09(a, len);
            let right = lowering_exec_r09(b, len);
            Re::Alt(Box::new(left), Box::new(right))
        },
        SyntaxKind::Cat(a, b) => {
            let left = lowering_exec_r09(a, len);
            let right = lowering_exec_r09(b, len);
            Re::Cat(Box::new(left), Box::new(right))
        },
        SyntaxKind::Star(a) => {
            let child = lowering_exec_r09(a, len);
            Re::Star(Box::new(child))
        },
        SyntaxKind::Plus(a) => {
            let child = lowering_exec_r09(a, len);
            let second = copy_re(&child);
            Re::Cat(Box::new(child), Box::new(Re::Star(Box::new(second))))
        },
        SyntaxKind::Opt(a) => {
            let child = lowering_exec_r09(a, len);
            Re::Alt(Box::new(Re::Eps), Box::new(child))
        },
        SyntaxKind::Group(a) => lowering_exec_r09(a, len),
        SyntaxKind::RepRange(a, n, m) => {
            if *m == 0 {
                Re::Cat(Box::new(Re::Eps), Box::new(Re::Eps))
            } else {
                let child = lowering_exec_r09(a, len);
                repetition_lower_exec_r09(&child, *n, *m)
            }
        },
    }
}

// The cost is checked before the expansion is built.
fn frontend_r09(s: &Vec<char>, cap: u32) -> (res: Result<(Syn, Re), PErr>)
    ensures
        match res {
            Ok((tree, lowered)) => wf(tree, s.len() as nat) && tree.span.lo == 0 && tree.span.hi == s.len() && lowered == lower(tree) && node_count(lowered) <= cap,
            Err(e) => e.pos <= s.len(),
        },
        no_special_from(s@, 0) && (if s.len() == 0 { 1int } else { 2 * s.len() - 1 }) <= cap ==> res is Ok && matches(res->Ok_0.1, s@),
{
    let tree = parse(s)?;
    match checked_lowering_cost_r09(&tree, s.len(), cap) {
        None => Err(PErr { pos: 0, kind: ErrKind::ExpansionBudget }),
        Some(_) => {
            let lowered = lowering_exec_r09(&tree, s.len());
            proof {
                lemma_lowering_nodes_r09(tree, s.len() as nat);
            }
            Ok((tree, lowered))
        },
    }
}

} // verus!

use rg_re_a1b::*;

verus! {

// Replacing the right operand by a language-equal one: the hypothesis, read at
// every split point, makes the two existentials of `matches`' Cat case agree.
proof fn lemma_cat_right_context_r09(a: Re, b: Re, c: Re, s: Seq<char>)
    requires
        forall|t: Seq<char>| matches(b, t) == matches(c, t),
    ensures
        matches(Re::Cat(Box::new(a), Box::new(b)), s) == matches(Re::Cat(Box::new(a), Box::new(c)), s),
{
    assert forall|i: int| 0 <= i <= s.len() implies matches(b, #[trigger] s.subrange(i, s.len() as int)) == matches(c, s.subrange(i, s.len() as int)) by {
    }
}

// item: R09.W4v
/// Two worked interfaces for H4. `lemma_copies_join_r09` joins a block of `a`
/// copies and a block of `b` copies into one block of `a + b` copies, in both
/// directions; `lemma_copies_optional_r09` says what an optional block matches:
/// some count of copies up to its bound. Each is proved by induction on a count.
proof fn lemma_copies_join_r09(r: Re, a: nat, b: nat, s: Seq<char>)
    ensures
        matches(copies(r, a + b), s) == matches(Re::Cat(Box::new(copies(r, a)), Box::new(copies(r, b))), s),
    decreases a,
{
    if a == 0 {
        lemma_cat_eps_left(copies(r, b), s);
    } else {
        let aa = (a - 1) as nat;
        lemma_cat_assoc(r, copies(r, aa), copies(r, b), s);
        let x = copies(r, aa + b);
        let y = Re::Cat(Box::new(copies(r, aa)), Box::new(copies(r, b)));
        assert forall|t: Seq<char>| matches(x, t) == matches(y, t) by {
            lemma_copies_join_r09(r, aa, b, t);
        }
        lemma_cat_right_context_r09(r, x, y, s);
    }
}

proof fn lemma_copies_optional_r09(r: Re, j: nat, s: Seq<char>)
    ensures
        matches(copies_up_to(r, j), s) == (exists|k: nat| k <= j && #[trigger] matches(copies(r, k), s)),
    decreases j,
{
    if j > 0 {
        let jm = (j - 1) as nat;
        let u = copies_up_to(r, jm);
        if matches(copies_up_to(r, j), s) {
            if s.len() != 0 {
                assert(!matches(Re::Eps, s));
                assert(matches(Re::Cat(Box::new(r), Box::new(u)), s));
                let i = choose|i: int| 0 <= i <= s.len() && matches(r, #[trigger] s.subrange(0, i)) && matches(u, s.subrange(i, s.len() as int));
                lemma_copies_optional_r09(r, jm, s.subrange(i, s.len() as int));
                let k = choose|k: nat| k <= jm && #[trigger] matches(copies(r, k), s.subrange(i, s.len() as int));
                assert(copies(r, k + 1) == Re::Cat(Box::new(r), Box::new(copies(r, k))));
                assert(matches(copies(r, k + 1), s));
            } else {
                assert(matches(copies(r, 0), s));
            }
        }
        if exists|k: nat| k <= j && #[trigger] matches(copies(r, k), s) {
            let k = choose|k: nat| k <= j && #[trigger] matches(copies(r, k), s);
            if k > 0 {
                let km = (k - 1) as nat;
                assert(copies(r, k) == Re::Cat(Box::new(r), Box::new(copies(r, km))));
                let i = choose|i: int| 0 <= i <= s.len() && matches(r, #[trigger] s.subrange(0, i)) && matches(copies(r, km), s.subrange(i, s.len() as int));
                lemma_copies_optional_r09(r, jm, s.subrange(i, s.len() as int));
                assert(exists|kk: nat| kk <= jm && #[trigger] matches(copies(r, kk), s.subrange(i, s.len() as int)));
                assert(matches(Re::Cat(Box::new(r), Box::new(u)), s));
            } else {
                assert(copies(r, 0) == Re::Eps);
            }
            assert(matches(copies_up_to(r, j), s));
        }
    } else {
        assert(copies(r, 0) == Re::Eps);
        if exists|k: nat| k <= j && #[trigger] matches(copies(r, k), s) {
            let k = choose|k: nat| k <= j && #[trigger] matches(copies(r, k), s);
            assert(k == 0);
        }
    }
}

} // verus!

// =============================================================================
// Holes
// =============================================================================

verus! {

// item: R09.H1v
// pair: R09.H1d
/// **H1.** Parse the counted suffix `{d}` or `{d,d}` that starts at `j`, after
/// the operand `x`: on success return the repetition node, spanning from
/// `x.span.lo` to the end of the suffix, and that end. A malformed suffix is an
/// error at the first position that is wrong. Remove `external_body` and write
/// the body. Which index does each guard protect, and which clause rules out a
/// body that rejects every suffix?
#[verifier::external_body]
pub fn parse_counted(s: &Vec<char>, j: usize, x: Syn) -> (res: Result<(Syn, usize), PErr>)
    requires
        j < s.len(),
        s@[j as int] == '{',
        wf(x, s.len() as nat),
        x.span.hi == j,
        x.span.lo < j,
    ensures
        match res {
            Ok((y, k)) => j < k <= s.len() && wf(y, s.len() as nat) && y.span.lo == x.span.lo && y.span.hi == k,
            Err(e) => e.pos <= s.len(),
        },
        forall|n: nat, m: nat, k: int| #[trigger] counted_at(s@, j as int, n, m, k) ==> res == Ok::<(Syn, usize), PErr>((counted_node(x, n, m, k), k as usize)),
{
    unimplemented!()
}
// Hint(1): read A3's `counted_at`: it fixes every character of both forms and the end k.
// Hint(2): test the length before each `s[j + d]`; `is_bound_char` and `bound_value` are A3's, and `x` moves into the node.

// item: R09.H2v
// pair: R09.H2d
/// **H2.** Parse a class body from `i` up to and including its closing `]`,
/// inserting each single character or range `c-d` (either may be escaped) into
/// the accumulator through A2's API. On success return the class and the
/// position after `]`. Remove `external_body` and write the body. What must the
/// loop keep true of the accumulator, and which A2 facts carry the class-domain
/// bound through an insertion?
#[verifier::external_body]
pub fn class_items(s: &Vec<char>, i: usize, mut acc: CharClass) -> (res: Result<(CharClass, usize), PErr>)
    requires
        i <= s.len(),
        acc.valid() && class_valid(acc.ranges_spec()),
    ensures
        match res {
            Ok((xs, k)) => i < k <= s.len() && xs.valid() && class_valid(xs.ranges_spec()),
            Err(e) => e.pos <= s.len(),
        },
        forall|k: int| #[trigger] simple_class_body(s@, i as int, k) ==> res is Ok && res->Ok_0.1 == k + 1,
{
    unimplemented!()
}
// Hint(1): the loop needs the accumulator's two facts and a `simple_class_body` fact about j.
// Hint(2): `class_insert` keeps `ranges_below(CLASS_MAX as int)` when the inserted range lies below it;
//    `lemma_view_ranges` turns that into `class_valid` of the listing.

// item: R09.H3v
// pair: R09.H3d
/// **H3.** Decide whether a counted repetition with `lo` fixed and `hi - lo`
/// optional copies of a child of cost `base` fits under `cap`, without any
/// intermediate overflowing u32: return `Some` of the exact cost when it fits,
/// `None` when it does not. Remove `external_body` and write the body. Which
/// part of the cost can be checked by subtraction, and how can a product be
/// compared with the space left without computing it first?
#[verifier::external_body]
fn repeat_expansion_budget_r09(base: u32, lo: u32, hi: u32, cap: u32) -> (res: Option<u32>)
    requires
        lo <= hi <= 9,
    ensures
        match res {
            Some(cost) => cost <= cap && (cost as int) == 3 + (base as int) * (hi as int) + (lo as int) + 3 * ((hi as int) - (lo as int)),
            None => 3 + (base as int) * (hi as int) + (lo as int) + 3 * ((hi as int) - (lo as int)) > (cap as int),
        },
{
    unimplemented!()
}
// Hint(1): with lo <= hi <= 9 the overhead 3 + lo + 3 * (hi - lo) is small; compare it with cap first.
// Hint(2): the given `division_budget_guard_r09` relates `base <= space / copies` to the product; zero copies need no division.

// item: R09.H4v
// pair: R09.H4d
/// **H4.** A finite repetition `rep_range(r, n, m)`, a block of `n` copies
/// followed by an optional block of up to `m - n`, matches exactly the strings
/// that some number of copies between `n` and `m` matches. In each direction,
/// which split of `s` and which count do you take out of the hypothesis with
/// `choose`, and which W4 helper turns them into the other side?
proof fn lemma_repetition_interval_r09(r: Re, n: nat, m: nat, s: Seq<char>)
    requires
        n <= m,
    ensures
        matches(rep_range(r, n, m), s) == (exists|k: nat| n <= k <= m && #[trigger] matches(copies(r, k), s)),
{
    #[verifier::proof_note("R09.H4v")] assume(false);
}
// Hint(1): `rep_range` is a Cat, so a match of it hands you a split; the exists over k hands you a count.
// Hint(2): `lemma_copies_optional_r09` works on the suffix after the split; `lemma_copies_join_r09` with
//    counts n and k - n joins the blocks.

// item: R09.H5v
// pair: R09.H5d
// uses: error-propagation, old
/// **H5.** Parse the counted suffix at the cursor with H1's `parse_counted`, as
/// a transaction: on success move the cursor to the end of the suffix and return
/// the node; on failure leave the cursor where it was. Remove `external_body` and
/// write the body. Compare T1: which state change must come after the `?`, not
/// before it?
#[verifier::external_body]
fn counted_cursor_r09(cur: &mut EffectCursorR09, x: Syn) -> (res: Result<Syn, PErr>)
    requires
        old(cur).position < old(cur).text.len(),
        old(cur).text@[old(cur).position as int] == '{',
        wf(x, old(cur).text.len() as nat),
        x.span.hi == old(cur).position,
        x.span.lo < old(cur).position,
    ensures
        final(cur).text@ == old(cur).text@,
        old(cur).position <= final(cur).position <= final(cur).text.len(),
        match res {
            Ok(y) => wf(y, final(cur).text.len() as nat) && y.span.lo == x.span.lo && y.span.hi == final(cur).position && old(cur).position < final(cur).position,
            Err(e) => final(cur).position == old(cur).position && e.pos <= final(cur).text.len(),
        },
        forall|n: nat, m: nat, k: int| #[trigger] counted_at(old(cur).text@, old(cur).position as int, n, m, k) ==> res == Ok::<Syn, PErr>(counted_node(x, n, m, k)) && final(cur).position == k,
{
    unimplemented!()
}
// Hint(1): `?` returns the same error; nothing has moved yet if you have not written `cur.position`.
// Hint(2): `parse_counted`'s contract already gives the node and its end; the cursor update is one assignment.

/// Given (not items): live use-site checks of T1 and H5. They verify against
/// the contracts now and must keep verifying once your bodies replace the holes.
fn read_bound_cursor_client() {
    let mut text: Vec<char> = Vec::new();
    text.push('7');
    text.push('x');
    let mut cur = EffectCursorR09 { text, position: 0 };
    let first = read_bound_cursor_r09(&mut cur);
    assert(first == Ok::<u32, PErr>(7));
    assert(cur.position == 1);
    let second = read_bound_cursor_r09(&mut cur);
    assert(second is Err && second->Err_0.pos == 1);
    assert(cur.position == 2);
}

fn counted_cursor_client() {
    let mut text: Vec<char> = Vec::new();
    text.push('a');
    text.push('{');
    text.push('2');
    text.push('}');
    let x = Syn { node: SyntaxKind::Chr('a'), span: Span { lo: 0, hi: 1 } };
    let ghost expected = counted_node(x, 2, 2, 4);
    let mut cur = EffectCursorR09 { text, position: 1 };
    assert(counted_at(cur.text@, 1, 2, 2, 4));
    let r = counted_cursor_r09(&mut cur, x);
    assert(r == Ok::<Syn, PErr>(expected));
    assert(cur.position == 4);
}

} // verus!

// =============================================================================
// Recognise cards
// =============================================================================

// item: R09.C3v recognise:mut-ref
// A mutable borrow gives temporary mutation access; old and final describe the two states.
// item: R09.C6v recognise:result
// Result carries either a payload or a positioned error, not a Boolean success flag.
