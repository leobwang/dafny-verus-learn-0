//! # Q08 — Internals II: refinement, permissions, verified wp (Reference Solution)
//!
//! Hole-free reference for `verus/q/q08_internals_ii/src/lib.rs` (author-only; never
//! learner-visible). Same crate layout, imports, names, statements, item markers and order
//! as the exercise file. Every hole is filled, every check is live, and every verdict
//! switch is enabled; the statement holes (T1v, H3v) carry their specifications and their
//! clients carry no assume. The Verus exec items declare their `// triv:` bodies for the
//! empty-body gate's TRIV mode.
//!
//! The file is silent: `scripts/vcheck --ref` on the crate prints only the summary line.
//! Every output the module quotes is pinned (`expected/Q08.counts`, `expected/Q08.freeze`,
//! the card demos' `// EXPECT` lines and sidecars).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use core::cmp::Ordering;
use qg_bignat_l4::*;

mod perm;

verus! {

// =========================================================================================
// The prediction block. Commit every prediction of this module before you read past this
// block (the test-out T1 included), and record the first tries:
//     scripts/firsttry.sh Q08 --check
// The verdict answers go in slots/Q08.slots. The Dafny file's prediction block
// (dafny/Q/Q08_InternalsII/std/Q08_InternalsII.dfy) holds P1, P3, P4 and P5.
// Verdict vocabulary for `V:<v>` answers: `ok` (verifies), `fail` (a verification error),
// `timeout` (out of resource or time), `err:<stage>` (refused before verification;
// <stage> as scripts/vcheck prints it: `parse` or `resolve`).
// =========================================================================================

// item: Q08.P2v S8 verdict
// **P2.** A permission used twice, and a ghost value used twice. Two files of their own,
// each with `use vstd::prelude::*;` (the first also with `use vstd::cell::pcell::*;`) and,
// inside `verus! { }`:
/*
    [a] proof fn consume(tracked p: PointsTo<u64>) {
        }

        fn twice() {
            let (cell, Tracked(perm)) = PCell::new(5u64);
            proof {
                consume(perm);
                consume(perm);
            }
        }

    [b] proof fn look(g: Seq<u64>) {
        }

        fn twice_ghost() {
            let ghost s: Seq<u64> = seq![1u64, 2u64];
            proof {
                look(s);
                look(s);
            }
        }
*/
// What does `scripts/vcheck` say about each file?
// Answer form: `V:<v> <v>` ([a], then [b]), with the verdict vocabulary above.
// CHECK P2v

// item: Q08.P6v S6 verdict
// **P6.** What a caller may assume. A trait whose `bump` promises only that the count goes
// up, and its implementation on a struct, which promises more:
/*
    pub trait Counter: Sized {
        spec fn count(&self) -> nat;

        fn bump(&mut self)
            requires
                old(self).count() < 100,
            ensures
                final(self).count() > old(self).count(),
        ;
    }

    pub struct Small {
        pub n: u64,
    }

    impl Counter for Small {
        open spec fn count(&self) -> nat {
            self.n as nat
        }

        fn bump(&mut self)
            ensures
                final(self).n == old(self).n + 1,
        {
            self.n = self.n + 1;
        }
    }

  and two callers, each in a file of its own beside the code above:

    [a] fn caller_a(s: &mut Small)
            requires
                old(s).count() == 5,
            ensures
                final(s).count() == 6,
        {
            s.bump();
        }

    [b] fn caller_b<C: Counter>(c: &mut C)
            requires
                old(c).count() == 5,
            ensures
                final(c).count() == 6,
        {
            c.bump();
        }
*/
// What does `scripts/vcheck` say about each file?
// Answer form: `V:<v> <v>` ([a], then [b]), with the verdict vocabulary above.
// CHECK P6v

// =========================================================================================
// Test-out (closed book: after every prediction of this module is recorded, before any
// reading; `scripts/firsttry.sh Q08 --check` refuses T1's first try until then)
// =========================================================================================

// item: Q08.T1v S6
// uses: trait-spec
/// **T1.** (test-out) Specify a trait method.
///
/// Reference: `flip` turns the light over, so its postcondition relates the state after
/// the call to the state before: `final(self).on() == !old(self).on()`. The implementation
/// for `Lamp` meets it (its `on` is the field), and the generic client, which knows only
/// that postcondition, gets back to the start after two calls. With no postcondition the
/// client fails (it knows nothing after a call); one about `Lamp`'s field cannot be stated
/// in the trait, which knows only `on()`. The client's labelled assume is deleted.
pub trait Toggle {
    spec fn on(&self) -> bool;

    fn flip(&mut self)
        ensures
            final(self).on() == !old(self).on(),
    ;
}

pub struct Lamp {
    pub lit: bool,
}

impl Toggle for Lamp {
    open spec fn on(&self) -> bool {
        self.lit
    }

    fn flip(&mut self) {
        self.lit = !self.lit;
    }
}

pub fn flip_twice<T: Toggle>(t: &mut T)
    ensures
        final(t).on() == old(t).on(),
{
    t.flip();
    t.flip();
}

fn flip_check() {
    // reference-only: live in the twin, commented in the learner crate
    let mut l = Lamp { lit: false };
    l.flip();
    assert(l.lit);
}

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q08.W1v S6
/// **W1.** A generic client of L4's `NatLike`. `twice_plus_one` works for every type that
/// implements the trait, so it may use only what the trait's specifications say: `plus`
/// gives a valid result worth the sum of two valid arguments, and `from_word` a valid one
/// worth the word. Nothing about `BigNat`, limbs or `to_nat` is visible here.
pub fn twice_plus_one<T: NatLike>(v: &T) -> (r: T)
    requires
        v.valid(),
    ensures
        r.valid(),
        r.value() == 2 * v.value() + 1,
{
    let d = v.plus(v);
    // d.valid() and d.value() == v.value() + v.value(), from plus's postcondition
    let one = T::from_word(1);
    d.plus(&one)
}

// =========================================================================================
// WRITE card (a success here, a pinned failure demo in specimens/Q08/)
// =========================================================================================

// item: Q08.C2v S6 write:trait-spec
// C2 — card: specifications on trait methods.
// Jurisdiction: an interface with several implementations. A trait method carries its
// `requires` and `ensures`, stated over the trait's own spec fns; each implementation
// defines those spec fns (here with `open spec fn`) and must meet the trait's
// specification; a generic client, written for every implementation at once, may rely on
// the trait's `requires` and `ensures` and on nothing else. Success: `Dial`, `Knob` and
// `leave_zero`. Failure: specimens/Q08/card-c2v.rs.specimen (a client that relies on more
// than the trait promises).
pub trait Dial: Sized {
    spec fn pos(&self) -> nat;

    fn turn(&mut self)
        requires
            old(self).pos() < 9,
        ensures
            final(self).pos() == old(self).pos() + 1,
    ;

    fn at_zero(&self) -> (b: bool)
        ensures
            b == (self.pos() == 0),
    ;
}

pub struct Knob {
    pub p: u8,
}

impl Dial for Knob {
    open spec fn pos(&self) -> nat {
        self.p as nat
    }

    fn turn(&mut self) {
        self.p = self.p + 1;
    }

    fn at_zero(&self) -> (b: bool) {
        self.p == 0
    }
}

/// A generic client: whatever the implementation, a dial below 9 ends away from zero.
pub fn leave_zero<D: Dial>(d: &mut D)
    requires
        old(d).pos() < 9,
    ensures
        final(d).pos() > 0,
{
    if d.at_zero() {
        d.turn();
    }
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q08.H3v S6
// uses: trait-spec
/// **H3v.** Specify an odometer.
///
/// Reference: `advance` keeps the odometer well formed and adds `by` to the reading;
/// `current` needs a well-formed odometer and returns a canonical BigNat worth the
/// reading. The client's second `advance` needs `ok()` again, which only the first call's
/// postcondition can supply, so `final(self).ok()` is part of `advance`'s contract; the
/// implementation of `current` copies canonical limbs, which needs `ok()` as its
/// precondition.
pub trait Odometer: Sized {
    spec fn reading(&self) -> nat;

    spec fn ok(&self) -> bool;

    fn advance(&mut self, by: u64)
        requires
            old(self).ok(),
        ensures
            final(self).ok(),
            final(self).reading() == old(self).reading() + by,
    ;

    fn current(&self) -> (r: BigNat)
        requires
            self.ok(),
        ensures
            r.wf(),
            r.to_nat() == self.reading(),
    ;
}

pub struct Odo {
    pub total: BigNat,
}

impl Odometer for Odo {
    open spec fn reading(&self) -> nat {
        self.total.to_nat()
    }

    open spec fn ok(&self) -> bool {
        self.total.wf()
    }

    fn advance(&mut self, by: u64) {
        let step = from_u64(by);
        self.total = big_add(&self.total, &step);
    }

    fn current(&self) -> (r: BigNat) {
        let mut v: Vec<u64> = Vec::new();
        let n = self.total.limbs.len();
        let mut i: usize = 0;
        while i < n
            invariant
                i <= n,
                n == self.total@.len(),
                v@ =~= self.total@.subrange(0, i as int),
            decreases n - i,
        {
            v.push(self.total.limbs[i]);
            i = i + 1;
        }
        proof {
            assert(self.total@.subrange(0, n as int) =~= self.total@);
        }
        BigNat { limbs: v }
    }
}

/// The given generic client: the specifications must let it verify with no assume.
pub fn advance_twice<O: Odometer>(o: &mut O, a: u64, b: u64)
    requires
        old(o).ok(),
    ensures
        final(o).ok(),
        final(o).reading() == old(o).reading() + a + b,
{
    o.advance(a);
    o.advance(b);
}

fn current_check<O: Odometer>(o: &O)
    requires
        o.ok(),
{
    // reference-only: live in the twin, commented in the learner crate
    let r = o.current();
    assert(r.wf() && r.to_nat() == o.reading());
}

// item: Q08.H4v S6
// uses: trait-spec
/// **H4v.** Multiply through the trait.
///
/// Reference: count `i` from zero up to `k` with `plus` and `from_word(1)`, adding `v` to
/// an accumulator at each step; `compare` decides when to stop, and since `==` on
/// `Ordering` says nothing to the verifier, the loop condition tests the result with
/// `matches!`. The invariant keeps every value valid and the accumulator worth
/// `v.value() * i.value()`; one step adds `v.value()`, which distributivity
/// (`lemma_mul_is_distributive_add`) turns into `v.value() * (i.value() + 1)`. The loop
/// ends because `k.value() - i.value()` goes down, and at the end `i.value() == k.value()`
/// (the comparison is not `Less` and the invariant keeps `i` at most `k`).
pub fn scale<T: NatLike>(v: &T, k: &T) -> (r: T)
    requires
        v.valid(),
        k.valid(),
    ensures
        r.valid(),
        r.value() == v.value() * k.value(),
{
    let one = T::from_word(1);
    let mut acc = T::zero();
    let mut i = T::zero();
    while matches!(i.compare(k), Ordering::Less)
        invariant
            v.valid(),
            k.valid(),
            one.valid(),
            one.value() == 1,
            i.valid(),
            acc.valid(),
            i.value() <= k.value(),
            acc.value() == v.value() * i.value(),
        decreases k.value() - i.value(),
    {
        acc = acc.plus(v);
        proof {
            lemma_mul_is_distributive_add(v.value() as int, i.value() as int, 1);
        }
        i = i.plus(&one);
    }
    acc
}
// triv: { T::zero() }

fn scale_check() {
    // reference-only: live in the twin, commented in the learner crate
    let v = from_u64(6);
    let k = from_u64(7);
    let r = scale(&v, &k);
    assert(r.to_nat() == 42);
}

// =========================================================================================
// Final section: divergence card. Record every prediction of this module
// (scripts/firsttry.sh Q08 --check) before you read on or open its demos.
// =========================================================================================

// item: Q08.C5dv S7 diverge:q08-c5
// C5 — divergence card. Demos: specimens/Q08/card-c5dv-d.dfy.specimen and
// specimens/Q08/card-c5dv-v.rs.specimen.

} // verus!
