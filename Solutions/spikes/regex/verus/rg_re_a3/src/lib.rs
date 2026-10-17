//! Regex layer A3 (declared by R09; PLAN §2.2, §2.5 step 5): the surface syntax `Rx` with
//! counted repetition `RepRange(r, n, m)` and `RepMin(r, n)`, its lowering to `Re` (`copies`,
//! `rep_range`, `lower`), well-formedness, the parse-error type and the parser's specification
//! helpers. Bounds are single characters '0'..'9' (no decimal digit-run parser in any R file,
//! PLAN §5.5). The parser, the exec lowering and `lemma_rep_range` are R09's references
//! (crate `rg_ref_r09`).
//!
//! Grammar (whole input):
//!   alt  := cat ('|' cat)*
//!   cat  := post*                       (empty = Eps)
//!   post := atom ('*' | '+' | '?' | '{' d '}' | '{' d ',' '}' | '{' d ',' d '}')*
//!   atom := '(' alt ')' | '\' any | any char outside the metacharacters
//! with d one character '0'..'9' and, in '{' d ',' d '}', the first bound <= the second.
//!
//! Reference material (DVR0, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;

verus! {

/// The largest repetition bound (bounds are single characters).
pub const MAX_BOUND: u32 = 9;

/// Surface syntax.
pub enum Rx {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Rx>, Box<Rx>),
    Cat(Box<Rx>, Box<Rx>),
    Star(Box<Rx>),
    Plus(Box<Rx>),
    Opt(Box<Rx>),
    /// `r{n,m}`, n <= m
    RepRange(Box<Rx>, u32, u32),
    /// `r{n,}`
    RepMin(Box<Rx>, u32),
}

/// `r` repeated exactly `k` times.
pub open spec fn copies(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Cat(Box::new(r), Box::new(copies(r, (k - 1) as nat)))
    }
}

/// `r` repeated between `n` and `m` times (`n <= m`), without associativity rewriting.
pub open spec fn rep_range(r: Re, n: nat, m: nat) -> Re
    decreases m,
{
    if m == 0 {
        Re::Eps
    } else if n == 0 {
        Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(r), Box::new(rep_range(r, 0, (m - 1) as nat)))))
    } else {
        Re::Cat(Box::new(r), Box::new(rep_range(r, (n - 1) as nat, (m - 1) as nat)))
    }
}

/// Lowering to the core AST.
pub open spec fn lower(x: Rx) -> Re
    decreases x,
{
    match x {
        Rx::Empty => Re::Empty,
        Rx::Eps => Re::Eps,
        Rx::Chr(c) => Re::Chr(c),
        Rx::Alt(a, b) => Re::Alt(Box::new(lower(*a)), Box::new(lower(*b))),
        Rx::Cat(a, b) => Re::Cat(Box::new(lower(*a)), Box::new(lower(*b))),
        Rx::Star(a) => Re::Star(Box::new(lower(*a))),
        Rx::Plus(a) => Re::Cat(Box::new(lower(*a)), Box::new(Re::Star(Box::new(lower(*a))))),
        Rx::Opt(a) => Re::Alt(Box::new(Re::Eps), Box::new(lower(*a))),
        Rx::RepRange(a, n, m) => rep_range(lower(*a), n as nat, m as nat),
        Rx::RepMin(a, n) => Re::Cat(Box::new(copies(lower(*a), n as nat)), Box::new(Re::Star(Box::new(lower(*a))))),
    }
}

/// Bounds respected throughout.
pub open spec fn rx_wf(x: Rx) -> bool
    decreases x,
{
    match x {
        Rx::Alt(a, b) => rx_wf(*a) && rx_wf(*b),
        Rx::Cat(a, b) => rx_wf(*a) && rx_wf(*b),
        Rx::Star(a) => rx_wf(*a),
        Rx::Plus(a) => rx_wf(*a),
        Rx::Opt(a) => rx_wf(*a),
        Rx::RepRange(a, n, m) => n <= m && m <= MAX_BOUND && rx_wf(*a),
        Rx::RepMin(a, n) => n <= MAX_BOUND && rx_wf(*a),
        _ => true,
    }
}

// ---------------------------------------------------------------------------------------------
// The parser's specification
// ---------------------------------------------------------------------------------------------

pub enum ErrKind {
    UnexpectedEnd,
    UnexpectedChar,
    UnclosedParen,
    NothingToRepeat,
    BoundsOrder,
}

/// A parse error and the position (in chars) where it was detected.
pub struct PErr {
    pub pos: usize,
    pub kind: ErrKind,
}

pub open spec fn is_meta(c: char) -> bool {
    c == '|' || c == '(' || c == ')' || c == '*' || c == '+' || c == '?' || c == '{' || c == '}'
        || c == '\\'
}

/// A repetition bound: one character '0'..'9', and its value.
pub open spec fn is_bound_char(c: char) -> bool {
    '0' <= c && c <= '9'
}

pub open spec fn bound_value(c: char) -> nat {
    (c as nat - '0' as nat) as nat
}

/// `s[j..k]` spells `{n}` (m == Some(n)), `{n,}` (m == None) or `{n,m}` with n <= m.
pub open spec fn counted_at(s: Seq<char>, j: int, n: nat, m: Option<nat>, k: int) -> bool {
    &&& 0 <= j && j + 1 < s.len() && k <= s.len()
    &&& s[j] == '{' && is_bound_char(s[j + 1]) && n == bound_value(s[j + 1])
    &&& ((k == j + 3 && s[j + 2] == '}' && m == Some(n))
        || (k == j + 4 && s[j + 2] == ',' && s[j + 3] == '}' && m is None)
        || (k == j + 5 && s[j + 2] == ',' && is_bound_char(s[j + 3]) && s[j + 4] == '}'
            && m == Some(bound_value(s[j + 3])) && n <= bound_value(s[j + 3])))
}

/// The node a counted repetition of `x` parses to.
pub open spec fn counted_rx(x: Rx, n: nat, m: Option<nat>) -> Rx {
    match m {
        Some(mm) => Rx::RepRange(Box::new(x), n as u32, mm as u32),
        None => Rx::RepMin(Box::new(x), n as u32),
    }
}

pub open spec fn ok_span(res: Result<(Rx, usize), PErr>, i: usize, n: nat) -> bool {
    match res {
        Ok((x, j)) => i <= j <= n && rx_wf(x),
        Err(e) => e.pos <= n,
    }
}

} // verus!
