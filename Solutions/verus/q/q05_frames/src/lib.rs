//! # Q05 — Frames, ownership, modes, wp→VC (Reference Solution)
//!
//! Hole-free reference for `verus/q/q05_frames/src/lib.rs` (author-only; never
//! learner-visible). Same crate layout, imports, names, statements, item markers and order
//! as the exercise file. Every hole is filled and every check is live. The Verus exec
//! items declare their `// triv:` bodies for the empty-body gate's TRIV mode.
//!
//! The file is silent: `scripts/vcheck --ref` on the crate prints only the summary line.
//! Every output the module quotes is pinned (`expected/Q05.counts`, `expected/Q05.freeze`,
//! the card demos' `// EXPECT` lines and sidecars).
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

// =========================================================================================
// The prediction block. The predictions of Q05 are in the Dafny file's prediction block
// (dafny/Q/Q05_Frames/std/Q05_Frames.dfy: P1dv, P2dv, P3dv, P9dv, which cover both
// languages), in specimens/Q05/ (P4d, P5v, P6d) and in dafny/checks/Q05_checks.dfy
// (P8d). Commit every one of them before you read past this block, and record the first
// tries:
//     scripts/firsttry.sh Q05 --check
// =========================================================================================

// =========================================================================================
// Test-out (closed book, after the predictions are committed and before any reading)
// =========================================================================================

// item: Q05.T1v S7
// uses: lexicographic-decreases
// pair: Q05.T1d
// ### T1v · S7 — Write `pub open spec fn odometer(lo: nat, hi: nat) -> nat`, the number of
//    steps an odometer with the digits `hi lo` takes to reach `0 0` when each step
//    decrements `lo` or, at `lo == 0`, decrements `hi` and resets `lo` to 9. Write it by
//    recursion, with whatever Verus needs to accept it. Closed book: no chapter, no hints,
//    no tutor, and only once every prediction of Q05 is recorded. Then run
//    `scripts/firsttry.sh Q05 --check`: it records your first try (it runs the check below
//    in a scratch copy). Only then uncomment the check.
// (Reference) The pair `hi, lo` goes down at every step, compared left to right; neither
// argument alone does, since a reset raises `lo` to 9.
// reference-only: the learner writes this spec fn (a prompt-as-heading block)
pub open spec fn odometer(lo: nat, hi: nat) -> nat
    decreases hi, lo,
{
    if lo > 0 {
        1 + odometer((lo - 1) as nat, hi)
    } else if hi > 0 {
        1 + odometer(9, (hi - 1) as nat)
    } else {
        0
    }
}

// reference-only: the learner uncomments this check
proof fn odometer_check() {
    // did: evaluates odometer on the literals
    assert(odometer(2, 1) == 12) by (compute_only);
}

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q05.W1v S6
/// **W1.** A type the module owns, changed in place through `&mut self`. In a
/// postcondition, `old(self)` is the value before the call and `final(self)` the value
/// after it; a caller learns about `*self` after the call exactly what the postcondition
/// says, here that `hits` is 0 and `cap` is unchanged.
pub struct Counter {
    pub hits: u64,
    pub cap: u64,
}

impl Counter {
    pub fn reset(&mut self)
        ensures
            final(self).hits == 0,
            final(self).cap == old(self).cap,
    {
        self.hits = 0;
    }
}

fn counter_demo() {
    let mut c = Counter { hits: 3, cap: 9 };
    c.reset();
    assert(c.hits == 0 && c.cap == 9);  // both facts come from `reset`'s postcondition
}

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q05/)
// =========================================================================================

// item: Q05.C3v S6 write:error-propagation
// C3 — card: `?` over `Result`.
// Jurisdiction: a call that may fail. `let x = f()?;` binds the value of an `Ok` and
// otherwise returns the `Err` at once, as the caller's own result. Success:
// `first_is_zero`. Failure: specimens/Q05/card-c3v.rs.specimen (a postcondition the early
// return breaks).
pub struct NoLimb;

pub fn first_limb(v: &Vec<u64>) -> (r: Result<u64, NoLimb>)
    ensures
        r is Ok <==> v.len() > 0,
        r is Ok ==> r->Ok_0 == v@[0],
{
    if v.len() > 0 {
        Ok(v[0])
    } else {
        Err(NoLimb)
    }
}

pub fn first_is_zero(v: &Vec<u64>) -> (r: Result<bool, NoLimb>)
    ensures
        r is Ok <==> v.len() > 0,
        r is Ok ==> (r->Ok_0 <==> v@[0] == 0),
{
    let x = first_limb(v)?;
    Ok(x == 0)
}

// item: Q05.C4v S7 write:lexicographic-decreases
// C4 — card: lexicographic `decreases`.
// Jurisdiction: a recursion or a loop in which no single quantity goes down at every step,
// but a tuple does, compared left to right: `decreases a, b` holds at a step when `a` goes
// down (whatever `b` does), or `a` stays and `b` goes down. Success: `ack` (a recursion)
// and `walk_pairs` (a loop). Failure: specimens/Q05/card-c4v.rs.specimen.
pub open spec fn ack(m: nat, n: nat) -> nat
    decreases m, n,
{
    if m == 0 {
        n + 1
    } else if n == 0 {
        ack((m - 1) as nat, 1)
    } else {
        ack((m - 1) as nat, ack(m, (n - 1) as nat))
    }
}

/// Walk the pairs `(i, j)` with `j < i`, from `i = n` down: one pair per pass, `j` counting
/// up from 0 below `i`.
pub fn walk_pairs(n: u64) -> (r: (u64, u64))
    ensures
        r.0 == 0,
{
    let mut i = n;
    let mut j: u64 = 0;
    while i > 0
        invariant
            j <= i,
            i > 0 ==> j < i,
        decreases i, i - j,
    {
        if j + 1 < i {
            j = j + 1;
        } else {
            i = i - 1;
            j = 0;
        }
    }
    (i, j)
}

// item: Q05.C5v S6 write:mut-ref
// C5 — card: `&mut self` and `&mut` parameters, `old(…)` and `final(…)`.
// Jurisdiction: a value changed in place. The postcondition relates `final(x)`, the value
// after the call, to `old(x)`, the value before; it is all a caller learns about `*x`.
// Success: `Counter::bump` and `swap_limbs`. Failure: specimens/Q05/card-c5v.rs.specimen.
impl Counter {
    pub fn bump(&mut self)
        requires
            old(self).hits < old(self).cap,
        ensures
            final(self).hits == old(self).hits + 1,
            final(self).cap == old(self).cap,
    {
        self.hits = self.hits + 1;
    }
}

pub fn swap_limbs(a: &mut u64, b: &mut u64)
    ensures
        *final(a) == *old(b),
        *final(b) == *old(a),
{
    let t = *a;
    *a = *b;
    *b = t;
}

// item: Q05.C6v S6 write:result
// C6 — card: a `Result` return whose postcondition says what each variant means.
// Jurisdiction: a fallible result. The postcondition states when the call returns `Ok`
// (here exactly when the index is in range) and what an `Ok` holds; the caller matches on
// the variant and gets the matching facts. Success: `get_limb`. Failure:
// specimens/Q05/card-c6v.rs.specimen.
pub struct OutOfRange;

pub fn get_limb(v: &Vec<u64>, i: usize) -> (r: Result<u64, OutOfRange>)
    ensures
        r is Ok <==> i < v.len(),
        r is Ok ==> r->Ok_0 == v@[i as int],
{
    if i < v.len() {
        Ok(v[i])
    } else {
        Err(OutOfRange)
    }
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q05.H1v S6
// uses: mut-ref
/// **H1v.** Multiply a BigNat by `BASE` in place.
///
/// Reference: one more limb, 0, at the least significant end shifts every limb up one
/// place, which multiplies the value by `BASE`; `Vec::insert(0, 0)` does it in place. The
/// zero BigNat (no limb) stays as it is: `[0]` would not be canonical, and `BASE * 0` is
/// 0. The assertion shows the verifier that the tail of the new limbs is the old limbs, so
/// `seq_to_nat` unfolds once to `0 + BASE * old value`; the top limb is unchanged, so the
/// result stays canonical.
pub fn shift_up(a: &mut BigNat)
    requires
        old(a).wf(),
    ensures
        final(a).wf(),
        final(a).to_nat() == BASE * old(a).to_nat(),
{
    if a.limbs.len() > 0 {
        a.limbs.insert(0, 0);
        proof {
            assert(a@.drop_first() =~= old(a)@);
        }
    }
}
// triv: { }

fn shift_up_check() {
    let mut a = BigNat { limbs: Vec::new() };
    shift_up(&mut a);
    assert(a.wf() && a.to_nat() == 0);
}

// Given (not items): a bounded stack of limbs the module owns.
pub struct Full;

pub struct LimbStack {
    pub v: Vec<u64>,
    pub cap: usize,
}

impl View for LimbStack {
    type V = Seq<u64>;

    open spec fn view(&self) -> Seq<u64> {
        self.v@
    }
}

impl LimbStack {
    pub open spec fn inv(&self) -> bool {
        self.v@.len() <= self.cap
    }

    pub fn new(cap: usize) -> (r: Self)
        ensures
            r.inv(),
            r@ == Seq::<u64>::empty(),
            r.cap == cap,
    {
        LimbStack { v: Vec::new(), cap }
    }
}

// item: Q05.H2v S6
// uses: mut-ref, result
/// **H2v.** Push `x` when there is room.
///
/// Reference: the room test `self.v.len() < self.cap` decides the variant, as the third
/// postcondition says; on `Ok` the push keeps the invariant because the length was below
/// the capacity, and on `Err` nothing is touched, so `final(self)@ == old(self)@` holds
/// with no further proof.
impl LimbStack {
    pub fn try_push(&mut self, x: u64) -> (r: Result<(), Full>)
        requires
            old(self).inv(),
        ensures
            final(self).inv(),
            final(self).cap == old(self).cap,
            r is Ok <==> old(self)@.len() < old(self).cap,
            r is Ok ==> final(self)@ == old(self)@.push(x),
            r is Err ==> final(self)@ == old(self)@,
    {
        if self.v.len() < self.cap {
            self.v.push(x);
            Ok(())
        } else {
            Err(Full)
        }
    }
}
// triv: { Err(Full) }

fn try_push_check() {
    let mut s = LimbStack::new(1);
    let r = s.try_push(7);
    assert(r is Ok && s@ =~= seq![7u64]);
    let q = s.try_push(8);
    assert(q is Err && s@ =~= seq![7u64]);
}

// Given (not items): bit counts.
pub open spec fn bit_count(x: nat) -> nat
    decreases x,
{
    if x == 0 {
        0
    } else {
        x % 2 + bit_count(x / 2)
    }
}

pub open spec fn ones(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        bit_count(s[0] as nat) + ones(s.drop_first())
    }
}

// item: Q05.H4v S7
// uses: lexicographic-decreases
// pair: Q05.H4d
/// **H4v.** Count the one bits of every limb.
///
/// Reference: one loop over the pair (index, current limb): a pass either takes one bit
/// off `x` or loads the next limb. The invariant adds the count so far, the bits still in
/// `x` and the bits of the limbs not yet loaded: `c + bit_count(x) + ones(v[i..]) ==
/// ones(v)`; it also carries the bound `ones(v) <= u64::MAX`, from which `c + x % 2` cannot
/// overflow. Loading a limb raises `x`, so the measure is the pair `v.len() - i, x`.
pub fn count_ones(v: &Vec<u64>) -> (c: u64)
    requires
        ones(v@) <= u64::MAX,
    ensures
        c == ones(v@),
{
    let mut i: usize = 0;
    let mut x: u64 = 0;
    let mut c: u64 = 0;
    proof {
        assert(v@.subrange(0, v.len() as int) =~= v@);
    }
    while x > 0 || i < v.len()
        invariant
            i <= v.len(),
            c + bit_count(x as nat) + ones(v@.subrange(i as int, v.len() as int)) == ones(v@),
            ones(v@) <= u64::MAX,
        decreases v.len() - i, x,
    {
        if x > 0 {
            c = c + x % 2;
            x = x / 2;
        } else {
            proof {
                assert(v@.subrange(i as int, v.len() as int).drop_first()
                    =~= v@.subrange(i + 1, v.len() as int));
            }
            x = v[i];
            i = i + 1;
        }
    }
    c
}
// triv: { 0 }

fn count_ones_check() {
    let v: Vec<u64> = Vec::new();
    let c = count_ones(&v);
    assert(c == 0);
}

// Given (not items): decimal digits.
pub enum ParseError {
    Empty,
    NotDigit,
    Overflow,
}

pub open spec fn is_digit(c: u8) -> bool {
    48 <= c <= 57
}

pub open spec fn all_digits(s: Seq<u8>) -> bool {
    forall|i: int| 0 <= i < s.len() ==> is_digit(#[trigger] s[i])
}

pub open spec fn dec_value(s: Seq<u8>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        dec_value(s.drop_last()) * 10 + (s.last() - 48) as nat
    }
}

pub fn digit(c: u8) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok <==> is_digit(c),
        r is Ok ==> r->Ok_0 == c - 48,
        r is Err ==> r->Err_0 == ParseError::NotDigit,
{
    if 48 <= c && c <= 57 {
        Ok((c - 48) as u64)
    } else {
        Err(ParseError::NotDigit)
    }
}

pub fn mul10_add(acc: u64, d: u64) -> (r: Result<u64, ParseError>)
    requires
        d < 10,
    ensures
        r is Ok <==> acc * 10 + d <= u64::MAX,
        r is Ok ==> r->Ok_0 == acc * 10 + d,
        r is Err ==> r->Err_0 == ParseError::Overflow,
{
    if acc <= (u64::MAX - d) / 10 {
        Ok(acc * 10 + d)
    } else {
        Err(ParseError::Overflow)
    }
}

// item: Q05.H5v S6
// uses: error-propagation, result
// pair: Q05.H5d
/// **H5v.** Parse a decimal numeral into a `u64`.
///
/// Reference: the empty string is the one case the loop cannot see, so it returns
/// `Err(Empty)` first. The loop keeps the prefix read so far all digits with value `v`;
/// `digit(s[i])?` returns `NotDigit` at once on a non-digit (then `s` is not all digits),
/// and `mul10_add(v, d)?` returns `Overflow` exactly when the prefix one longer has a value
/// above `u64::MAX`, which is the witness `k` the last postcondition asks for. The first
/// assertion relates that prefix to the one before it, so `dec_value` unfolds once.
pub fn parse_decimal(s: &[u8]) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok ==> s@.len() > 0 && all_digits(s@) && r->Ok_0 == dec_value(s@),
        (r is Err && r->Err_0 == ParseError::Empty) <==> s@.len() == 0,
        r is Err && r->Err_0 == ParseError::NotDigit ==> !all_digits(s@),
        r is Err && r->Err_0 == ParseError::Overflow ==> exists|k: int|
            0 < k <= s@.len() && all_digits(s@.subrange(0, k)) && #[trigger] dec_value(
                s@.subrange(0, k),
            ) > u64::MAX,
{
    if s.len() == 0 {
        return Err(ParseError::Empty);
    }
    let mut v: u64 = 0;
    let mut i: usize = 0;
    while i < s.len()
        invariant
            0 < s@.len(),
            i <= s@.len(),
            all_digits(s@.subrange(0, i as int)),
            v == dec_value(s@.subrange(0, i as int)),
        decreases s.len() - i,
    {
        let d = digit(s[i])?;
        proof {
            assert(s@.subrange(0, i + 1).drop_last() =~= s@.subrange(0, i as int));
            assert(dec_value(s@.subrange(0, i + 1)) == v * 10 + d);
        }
        v = mul10_add(v, d)?;
        i = i + 1;
    }
    proof {
        assert(s@.subrange(0, s@.len() as int) =~= s@);
    }
    Ok(v)
}
// triv: { Err(ParseError::Empty) }

fn parse_decimal_check() {
    let v: Vec<u8> = Vec::new();
    let r = parse_decimal(v.as_slice());
    assert(r is Err);
}

// =========================================================================================
// Final section: divergence card. Record every prediction of this module
// (scripts/firsttry.sh Q05 --check) before you read on or open its demos.
// =========================================================================================

// item: Q05.C8dv S6 diverge:q05-c8
// C8 — divergence card. Demos: specimens/Q05/card-c8dv-d.dfy.specimen and
// specimens/Q05/card-c8dv-v.rs.specimen.

} // verus!

// =========================================================================================
// — clearly marked: everything below answers the agentic file —
// =========================================================================================
// The reference delivery of verus/q/q05_frames/src/agent.rs is that file's own twin,
// Solutions/verus/q/q05_frames/src/agent.rs, with the Dafny half's
// (Solutions/dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy): the repaired wiring, the
// receipts as captured, the diagnosis and the author's note on the soft spots.
