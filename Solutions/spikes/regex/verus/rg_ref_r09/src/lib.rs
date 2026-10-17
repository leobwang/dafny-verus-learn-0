//! R09 references over layer A3 (PLAN §3 R09, §2.5 step 5): the counted repetition's
//! semantics lemma `lemma_rep_range`, the recursive-descent parser with positions (bounds are
//! single characters; `parse_counted` carries a completeness clause, so a parser that always
//! fails does not meet its contract), the exec lowering and `parse_and_match`.
//!
//! Reference material (DVR0, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a3::*;

verus! {

/// Counted repetition means "some number of copies between n and m".
pub proof fn lemma_rep_range(r: Re, n: nat, m: nat, s: Seq<char>)
    requires
        n <= m,
    ensures
        matches(rep_range(r, n, m), s) <==> exists|k: nat| n <= k <= m && #[trigger] matches(copies(r, k), s),
    decreases m,
{
    if m == 0 {
        assert(matches(copies(r, 0), s) == matches(Re::Eps, s));
    } else {
        let n1: nat = if n == 0 { 0 } else { (n - 1) as nat };
        let m1 = (m - 1) as nat;
        let inner = rep_range(r, n1, m1);
        let cat = Re::Cat(Box::new(r), Box::new(inner));
        assert(s.subrange(0, s.len() as int) =~= s);
        // the Cat part: r then between n1 and m1 copies <==> between n1+1 and m1+1 copies
        if matches(cat, s) {
            let i = choose|i: int|
                0 <= i <= s.len() && matches(r, #[trigger] s.subrange(0, i)) && matches(
                    inner,
                    s.subrange(i, s.len() as int),
                );
            lemma_rep_range(r, n1, m1, s.subrange(i, s.len() as int));
            let k = choose|k: nat| n1 <= k <= m1 && #[trigger] matches(copies(r, k), s.subrange(i, s.len() as int));
            assert(matches(copies(r, k + 1), s));
        }
        if exists|k: nat| n1 + 1 <= k <= m && #[trigger] matches(copies(r, k), s) {
            let k = choose|k: nat| n1 + 1 <= k <= m && #[trigger] matches(copies(r, k), s);
            let k1 = (k - 1) as nat;
            assert(copies(r, k) == Re::Cat(Box::new(r), Box::new(copies(r, k1))));
            let i = choose|i: int|
                0 <= i <= s.len() && matches(r, #[trigger] s.subrange(0, i)) && matches(
                    copies(r, k1),
                    s.subrange(i, s.len() as int),
                );
            lemma_rep_range(r, n1, m1, s.subrange(i, s.len() as int));
            assert(matches(inner, s.subrange(i, s.len() as int)));
            assert(matches(cat, s));
        }
        if n == 0 {
            if matches(Re::Eps, s) {
                assert(matches(copies(r, 0), s));
            }
            if matches(copies(r, 0), s) {
                assert(matches(Re::Eps, s));
            }
        }
    }
}

// ---------------------------------------------------------------------------------------------
// Parser
// ---------------------------------------------------------------------------------------------

/// A counted repetition of `x` at `s[j] == '{'`: `{d}`, `{d,}` or `{d,d}`.
pub fn parse_counted(s: &Vec<char>, j: usize, x: Rx) -> (res: Result<(Rx, usize), PErr>)
    requires
        j < s.len(),
        s@[j as int] == '{',
        rx_wf(x),
    ensures
        match res {
            Ok((y, k)) => j < k <= s.len() && rx_wf(y),
            Err(e) => e.pos <= s.len(),
        },
        forall|n: nat, m: Option<nat>, k: int|
            #[trigger] counted_at(s@, j as int, n, m, k) ==> res == Ok::<(Rx, usize), PErr>(
                (counted_rx(x, n, m), k as usize),
            ),
{
    let len = s.len();
    if j + 1 >= len {
        return Err(PErr { pos: j + 1, kind: ErrKind::UnexpectedEnd });
    }
    let d = s[j + 1];
    if !('0' <= d && d <= '9') {
        return Err(PErr { pos: j + 1, kind: ErrKind::UnexpectedChar });
    }
    let lo = (d as u32) - ('0' as u32);
    if j + 2 >= len {
        return Err(PErr { pos: j + 2, kind: ErrKind::UnexpectedEnd });
    }
    if s[j + 2] == '}' {
        return Ok((Rx::RepRange(Box::new(x), lo, lo), j + 3));
    }
    if s[j + 2] != ',' {
        return Err(PErr { pos: j + 2, kind: ErrKind::UnexpectedChar });
    }
    if j + 3 >= len {
        return Err(PErr { pos: j + 3, kind: ErrKind::UnexpectedEnd });
    }
    if s[j + 3] == '}' {
        return Ok((Rx::RepMin(Box::new(x), lo), j + 4));
    }
    let e = s[j + 3];
    if !('0' <= e && e <= '9') {
        return Err(PErr { pos: j + 3, kind: ErrKind::UnexpectedChar });
    }
    let hi = (e as u32) - ('0' as u32);
    if j + 4 >= len {
        return Err(PErr { pos: j + 4, kind: ErrKind::UnexpectedEnd });
    }
    if s[j + 4] != '}' {
        return Err(PErr { pos: j + 4, kind: ErrKind::UnexpectedChar });
    }
    if hi < lo {
        return Err(PErr { pos: j + 3, kind: ErrKind::BoundsOrder });
    }
    Ok((Rx::RepRange(Box::new(x), lo, hi), j + 5))
}

/// `alt := cat ('|' cat)*`
pub fn parse_alt(s: &Vec<char>, i: usize) -> (res: Result<(Rx, usize), PErr>)
    requires
        i <= s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
    decreases s.len() - i, 3nat,
{
    let (mut x, mut j) = match parse_cat(s, i) {
        Ok(p) => p,
        Err(e) => return Err(e),
    };
    while j < s.len() && s[j] == '|'
        invariant
            i <= j <= s.len(),
            rx_wf(x),
        decreases s.len() - j,
    {
        let (y, k) = match parse_cat(s, j + 1) {
            Ok(p) => p,
            Err(e) => return Err(e),
        };
        x = Rx::Alt(Box::new(x), Box::new(y));
        j = k;
    }
    Ok((x, j))
}

/// `cat := post*`
pub fn parse_cat(s: &Vec<char>, i: usize) -> (res: Result<(Rx, usize), PErr>)
    requires
        i <= s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
    decreases s.len() - i, 2nat,
{
    let mut x = Rx::Eps;
    let mut first = true;
    let mut j = i;
    while j < s.len() && s[j] != '|' && s[j] != ')'
        invariant
            i <= j <= s.len(),
            rx_wf(x),
        decreases s.len() - j,
    {
        let (y, k) = match parse_post(s, j) {
            Ok(p) => p,
            Err(e) => return Err(e),
        };
        x = if first { y } else { Rx::Cat(Box::new(x), Box::new(y)) };
        first = false;
        j = k;
    }
    Ok((x, j))
}

/// `post := atom op*`; consumes at least one char on success.
pub fn parse_post(s: &Vec<char>, i: usize) -> (res: Result<(Rx, usize), PErr>)
    requires
        i < s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        res is Ok ==> res->Ok_0.1 > i,
    decreases s.len() - i, 1nat,
{
    let (mut x, mut j) = match parse_atom(s, i) {
        Ok(p) => p,
        Err(e) => return Err(e),
    };
    while j < s.len() && (s[j] == '*' || s[j] == '+' || s[j] == '?' || s[j] == '{')
        invariant
            i < j <= s.len(),
            rx_wf(x),
        decreases s.len() - j,
    {
        let c = s[j];
        if c == '*' {
            x = Rx::Star(Box::new(x));
            j = j + 1;
        } else if c == '+' {
            x = Rx::Plus(Box::new(x));
            j = j + 1;
        } else if c == '?' {
            x = Rx::Opt(Box::new(x));
            j = j + 1;
        } else {
            let (y, k) = match parse_counted(s, j, x) {
                Ok(p) => p,
                Err(e) => return Err(e),
            };
            x = y;
            j = k;
        }
    }
    Ok((x, j))
}

/// `atom := '(' alt ')' | '\' any | literal`
pub fn parse_atom(s: &Vec<char>, i: usize) -> (res: Result<(Rx, usize), PErr>)
    requires
        i < s.len(),
    ensures
        ok_span(res, i, s.len() as nat),
        res is Ok ==> res->Ok_0.1 > i,
    decreases s.len() - i, 0nat,
{
    let c = s[i];
    if c == '(' {
        let (x, j) = match parse_alt(s, i + 1) {
            Ok(p) => p,
            Err(e) => return Err(e),
        };
        if j < s.len() && s[j] == ')' {
            Ok((x, j + 1))
        } else {
            Err(PErr { pos: i, kind: ErrKind::UnclosedParen })
        }
    } else if c == '\\' {
        if i + 1 < s.len() {
            Ok((Rx::Chr(s[i + 1]), i + 2))
        } else {
            Err(PErr { pos: i + 1, kind: ErrKind::UnexpectedEnd })
        }
    } else if c == '*' || c == '+' || c == '?' || c == '{' {
        Err(PErr { pos: i, kind: ErrKind::NothingToRepeat })
    } else if c == '|' || c == ')' || c == '}' {
        Err(PErr { pos: i, kind: ErrKind::UnexpectedChar })
    } else {
        Ok((Rx::Chr(c), i + 1))
    }
}

/// Parse a whole pattern.
pub fn parse(s: &Vec<char>) -> (res: Result<Rx, PErr>)
    ensures
        match res {
            Ok(x) => rx_wf(x),
            Err(e) => e.pos <= s.len(),
        },
{
    match parse_alt(s, 0) {
        Ok((x, j)) => if j == s.len() {
            Ok(x)
        } else {
            Err(PErr { pos: j, kind: ErrKind::UnexpectedChar })
        },
        Err(e) => Err(e),
    }
}

// ---------------------------------------------------------------------------------------------
// Exec lowering
// ---------------------------------------------------------------------------------------------

pub fn copies_exec(r: &Re, k: u32) -> (out: Re)
    ensures
        out == copies(*r, k as nat),
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Cat(Box::new(copy_re(r)), Box::new(copies_exec(r, k - 1)))
    }
}

pub fn rep_range_exec(r: &Re, n: u32, m: u32) -> (out: Re)
    ensures
        out == rep_range(*r, n as nat, m as nat),
    decreases m,
{
    if m == 0 {
        Re::Eps
    } else if n == 0 {
        Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(copy_re(r)), Box::new(rep_range_exec(r, 0, m - 1)))))
    } else {
        Re::Cat(Box::new(copy_re(r)), Box::new(rep_range_exec(r, n - 1, m - 1)))
    }
}

pub fn lower_exec(x: &Rx) -> (out: Re)
    ensures
        out == lower(*x),
    decreases x,
{
    match x {
        Rx::Empty => Re::Empty,
        Rx::Eps => Re::Eps,
        Rx::Chr(c) => Re::Chr(*c),
        Rx::Alt(a, b) => Re::Alt(Box::new(lower_exec(a)), Box::new(lower_exec(b))),
        Rx::Cat(a, b) => Re::Cat(Box::new(lower_exec(a)), Box::new(lower_exec(b))),
        Rx::Star(a) => Re::Star(Box::new(lower_exec(a))),
        Rx::Plus(a) => {
            let l = lower_exec(a);
            let l2 = copy_re(&l);
            Re::Cat(Box::new(l), Box::new(Re::Star(Box::new(l2))))
        },
        Rx::Opt(a) => Re::Alt(Box::new(Re::Eps), Box::new(lower_exec(a))),
        Rx::RepRange(a, n, m) => {
            let l = lower_exec(a);
            rep_range_exec(&l, *n, *m)
        },
        Rx::RepMin(a, n) => {
            let l = lower_exec(a);
            let p = copies_exec(&l, *n);
            Re::Cat(Box::new(p), Box::new(Re::Star(Box::new(l))))
        },
    }
}

/// Parse and match a whole string: `Ok(b)` with `b` the spec verdict of the parsed pattern.
pub fn parse_and_match(pat: &Vec<char>, s: &Vec<char>) -> (res: Result<bool, PErr>)
    ensures
        res is Ok ==> exists|x: Rx| #[trigger] rx_wf(x) && res->Ok_0 == matches(lower(x), s@),
{
    match parse(pat) {
        Ok(x) => {
            let r = lower_exec(&x);
            let b = deriv_match(&r, s);
            Ok(b)
        },
        Err(e) => Err(e),
    }
}

} // verus!
