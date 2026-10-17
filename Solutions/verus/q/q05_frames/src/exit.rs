//! # Q05 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q05_frames/src/exit.rs` (author-only; never
//! learner-visible). Same imports, given definitions, statements, item markers and order
//! as the exit file; each block's body is filled. Silent under the gate.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

// Given (not items): an account type and its failure, for X1.
pub struct Short;

pub struct Account {
    pub bal: u64,
    pub cap: u64,
}

// Given (not items): a one-digit parser and its errors, for X2.
pub enum ParseError {
    Empty,
    NotDigit,
    Overflow,
}

pub open spec fn is_digit(c: u8) -> bool {
    48 <= c <= 57
}

/// Parse a field of exactly one decimal digit.
pub fn parse_digit(t: &[u8]) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok <==> (t@.len() == 1 && is_digit(t@[0])),
        r is Ok ==> r->Ok_0 == t@[0] - 48,
{
    if t.len() != 1 {
        return Err(ParseError::Empty);
    }
    if t[0] < 48 || t[0] > 57 {
        return Err(ParseError::NotDigit);
    }
    Ok((t[0] - 48) as u64)
}

// item: Q05.X1v S6
// uses: mut-ref, result
// need: pub fn transfer(from: &mut Account, to: &mut Account, k: u64) -> (r: Result<(), Short>)
// need: r is Ok <==> (k <= old(from).bal && old(to).bal + k <= old(to).cap)
/// **X1.** Move `k` units from `from` to `to`: `Ok` exactly when `from` holds `k` and `to`
/// has room for them, with `k` moved; on `Err`, both accounts unchanged.
///
/// Reference: test both conditions first (the room as `k <= to.cap - to.bal`, which cannot
/// overflow under the invariant `to.bal <= to.cap`), then change both balances; the `Err`
/// branch touches nothing.
pub fn transfer(from: &mut Account, to: &mut Account, k: u64) -> (r: Result<(), Short>)
    requires
        old(from).bal <= old(from).cap,
        old(to).bal <= old(to).cap,
    ensures
        final(from).cap == old(from).cap,
        final(to).cap == old(to).cap,
        final(from).bal <= final(from).cap,
        final(to).bal <= final(to).cap,
        r is Ok <==> (k <= old(from).bal && old(to).bal + k <= old(to).cap),
        r is Ok ==> final(from).bal == old(from).bal - k && final(to).bal == old(to).bal + k,
        r is Err ==> final(from).bal == old(from).bal && final(to).bal == old(to).bal,
{
    if k <= from.bal && k <= to.cap - to.bal {
        from.bal = from.bal - k;
        to.bal = to.bal + k;
        Ok(())
    } else {
        Err(Short)
    }
}
// triv: { Err(Short) }

// item: Q05.X2v S6
// uses: error-propagation
// need: pub fn parse_pair(a: &[u8], b: &[u8]) -> (r: Result<(u64, u64), ParseError>)
// need: r is Ok <==> (a@.len() == 1 && is_digit(a@[0]) && b@.len() == 1 && is_digit(b@[0]))
/// **X2.** Parse two one-digit fields with the given `parse_digit`, propagating the first
/// failure with `?`.
///
/// Reference: two `?` steps and an `Ok`; `parse_digit`'s postcondition states exactly when
/// each step succeeds.
pub fn parse_pair(a: &[u8], b: &[u8]) -> (r: Result<(u64, u64), ParseError>)
    ensures
        r is Ok <==> (a@.len() == 1 && is_digit(a@[0]) && b@.len() == 1 && is_digit(b@[0])),
{
    let x = parse_digit(a)?;
    let y = parse_digit(b)?;
    Ok((x, y))
}
// triv: { Err(ParseError::Empty) }

} // verus!
