//! A3 syntax model (PROVIDED, frozen). R09–R16.
//! Do not open this crate before R03 and R06 are done: it imports A2, which re-supplies their
//! answers, and its class lowering reads classes through R03's API. R09 is its first module.
//! Positioned syntax and finite single-character-bound repetition.
//! No parser, executable lowering or lowering-correctness theorem is supplied.
//! Class nodes hold A2's `CharClass` (u32 code-point ranges), read through A2's
//! accessor `ranges`; classes lower only below 0xD800, where every code is a char.
use vstd::prelude::*;
use rg_re_a1::*;
pub use rg_re_a2::char_class::CharClass;

verus! {

pub const MAX_BOUND: u32 = 9;

pub const CLASS_MAX: u32 = 0xd800;

pub struct Span {
    pub lo: usize,
    pub hi: usize,
}

pub struct Syn {
    pub node: SyntaxKind,
    pub span: Span,
}

pub enum SyntaxKind {
    Eps,
    Chr(char),
    Class(CharClass),
    Alt(Box<Syn>, Box<Syn>),
    Cat(Box<Syn>, Box<Syn>),
    Star(Box<Syn>),
    Plus(Box<Syn>),
    Opt(Box<Syn>),
    RepRange(Box<Syn>, u32, u32),
    Group(Box<Syn>),
}

/// A range that lowers: non-empty and below CLASS_MAX.
pub open spec fn range_valid(lo: u32, hi: u32) -> bool {
    lo <= hi && hi < CLASS_MAX
}

/// A range listing that lowers.
pub open spec fn class_valid(xs: Seq<(u32, u32)>) -> bool {
    forall|i: int| 0 <= i < xs.len() ==> range_valid(xs[i].0, xs[i].1)
}

/// The one place a code becomes a char (spec only): `lo < CLASS_MAX`, so it is a char's code.
pub open spec fn range_re(lo: u32, hi: u32) -> Re
    decreases hi - lo,
{
    if !range_valid(lo, hi) {
        Re::Empty
    } else if lo == hi {
        Re::Chr(lo as char)
    } else {
        Re::Alt(Box::new(Re::Chr(lo as char)), Box::new(range_re((lo + 1) as u32, hi)))
    }
}

pub open spec fn class_re(xs: Seq<(u32, u32)>) -> Re
    decreases xs.len(),
{
    if xs.len() == 0 {
        Re::Empty
    } else {
        Re::Alt(Box::new(range_re(xs[0].0, xs[0].1)), Box::new(class_re(xs.drop_first())))
    }
}

pub open spec fn copies(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Cat(Box::new(r), Box::new(copies(r, (k - 1) as nat)))
    }
}

pub open spec fn copies_up_to(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(r), Box::new(copies_up_to(r, (k - 1) as nat)))))
    }
}

pub open spec fn rep_range(r: Re, n: nat, m: nat) -> Re {
    Re::Cat(Box::new(copies(r, n)), Box::new(copies_up_to(r, (m - n) as nat)))
}

pub open spec fn wf(t: Syn, len: nat) -> bool
    decreases t,
{
    &&& t.span.lo <= t.span.hi <= len
    &&& match t.node {
        SyntaxKind::Eps => t.span.lo == t.span.hi,
        SyntaxKind::Chr(_) => t.span.lo < t.span.hi,
        SyntaxKind::Class(xs) => t.span.lo < t.span.hi && xs.valid() && class_valid(xs.ranges_spec()),
        SyntaxKind::Alt(a, b) => wf(*a, len) && wf(*b, len) && a.span.lo == t.span.lo && a.span.hi < b.span.lo
            && b.span.hi == t.span.hi,
        SyntaxKind::Cat(a, b) => wf(*a, len) && wf(*b, len) && a.span.lo == t.span.lo && a.span.hi == b.span.lo
            && b.span.hi == t.span.hi,
        SyntaxKind::Star(a) | SyntaxKind::Plus(a) | SyntaxKind::Opt(a) => wf(*a, len) && a.span.lo == t.span.lo
            && a.span.hi < t.span.hi,
        SyntaxKind::RepRange(a, n, m) => wf(*a, len) && a.span.lo == t.span.lo && a.span.hi < t.span.hi && n <= m
            <= MAX_BOUND,
        SyntaxKind::Group(a) => wf(*a, len) && t.span.lo < a.span.lo && a.span.hi < t.span.hi,
    }
}

pub open spec fn lower(t: Syn) -> Re
    decreases t,
{
    match t.node {
        SyntaxKind::Eps => Re::Eps,
        SyntaxKind::Chr(c) => Re::Chr(c),
        SyntaxKind::Class(xs) => class_re(xs.ranges_spec()),
        SyntaxKind::Alt(a, b) => Re::Alt(Box::new(lower(*a)), Box::new(lower(*b))),
        SyntaxKind::Cat(a, b) => Re::Cat(Box::new(lower(*a)), Box::new(lower(*b))),
        SyntaxKind::Star(a) => Re::Star(Box::new(lower(*a))),
        SyntaxKind::Plus(a) => Re::Cat(Box::new(lower(*a)), Box::new(Re::Star(Box::new(lower(*a))))),
        SyntaxKind::Opt(a) => Re::Alt(Box::new(Re::Eps), Box::new(lower(*a))),
        SyntaxKind::RepRange(a, n, m) => rep_range(lower(*a), n as nat, m as nat),
        SyntaxKind::Group(a) => lower(*a),
    }
}

pub enum ErrKind {
    UnexpectedEnd,
    UnexpectedChar,
    UnclosedParen,
    UnclosedClass,
    NothingToRepeat,
    BoundsOrder,
    ClassRange,
    ExpansionBudget,
}

pub struct PErr {
    pub pos: usize,
    pub kind: ErrKind,
}

pub open spec fn is_meta(c: char) -> bool {
    c == '(' || c == ')' || c == '|' || c == '*' || c == '+' || c == '?' || c == '{' || c == '}' || c == '['
        || c == ']' || c == '\\'
}

pub open spec fn is_bound_char(c: char) -> bool {
    '0' <= c <= '9'
}

pub open spec fn bound_value(c: char) -> nat {
    (c as nat - '0' as nat) as nat
}

pub open spec fn counted_at(s: Seq<char>, j: int, n: nat, m: nat, k: int) -> bool {
    &&& 0 <= j < s.len() && s[j] == '{' && k <= s.len()
    &&& ((k == j + 3 && is_bound_char(s[j + 1]) && s[j + 2] == '}' && n == bound_value(s[j + 1]) && m == n) || (k
        == j + 5 && is_bound_char(s[j + 1]) && s[j + 2] == ',' && is_bound_char(s[j + 3]) && s[j + 4] == '}' && n
        == bound_value(s[j + 1]) && m == bound_value(s[j + 3]) && n <= m))
}

pub open spec fn ok_span(res: Result<(Syn, usize), PErr>, i: usize, len: nat) -> bool {
    match res {
        Ok((t, j)) => i <= j <= len && wf(t, len) && t.span.lo == i && t.span.hi == j,
        Err(e) => e.pos <= len,
    }
}

pub open spec fn simple_class_body(s: Seq<char>, i: int, k: int) -> bool {
    0 <= i <= k < s.len() && s[k] == ']' && forall|q: int|
        i <= q < k ==> s[q] != ']' && s[q] != '\\' && s[q] != '-' && (s[q] as u32) < CLASS_MAX
}

} // verus!
