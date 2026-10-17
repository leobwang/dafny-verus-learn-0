//! # Q08 — Internals II: refinement, permissions, verified wp (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l4` (`use
//! qg_bignat_l4::*;` brings all four layers' names), the vstd prelude, vstd's
//! multiplication lemmas (`vstd::arithmetic::mul`) and `core::cmp::Ordering`, nothing
//! else: no earlier exercise crate. The layers are frozen and complete; read them, never
//! edit them. The crate's second file is src/perm.rs (the module `perm`, declared below),
//! which also uses vstd's permissioned cells.
//!
//! How to work this file (the order is the module's, for both files):
//! 1. Predictions first: P2 and P6 (the prediction block below; their answers go in
//!    slots/Q08.slots), with every other prediction of the module (the Dafny file's
//!    prediction block, dafny/Q/Q08_InternalsII/std/Q08_InternalsII.dfy); record the first
//!    tries with `scripts/firsttry.sh Q08 --check` before you run anything they are about.
//! 2. Test-out next, closed book: T1 (below) before any reading, without its hints.
//!    `scripts/firsttry.sh Q08 --check` records its first try (it runs T1's commented check
//!    in a scratch copy), and refuses to while any prediction of the module is unrecorded.
//!    Only then uncomment the check.
//! 3. Then read the chapter, the worked examples and the cards. A card's failure demo is a
//!    specimen: open it only after step 1.
//! 4. Replace each hole, then uncomment the checks beneath it; then src/perm.rs.
//! 5. Done = `scripts/vcheck --gate verus/q/q08_internals_ii` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q08_internals_ii` reports no finding, AND
//!    `scripts/firsttry.sh Q08 --report --strict` exits 0. The crate's gate covers this
//!    file and src/perm.rs together.
//! 6. Stuck for 20 minutes? /tutor Q08.
//!
//! This file ships with exactly 3 holes: T1 (test-out), H3 and H4, each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one
//! counted diagnostic); src/perm.rs ships 2. Commit every prediction BEFORE you run
//! anything it is about, open later files, or read CI, the registry or the plan: their
//! checks and headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header
//! (dafny/Q/Q08_InternalsII/std/Q08_InternalsII.dfy). Exit (closed book): src/exit.rs here
//! and the Dafny exit file, scored once by `scripts/firsttry.sh Q08 --exit`; src/exit.rs
//! and src/agent.rs are never part of this crate's build.
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
// SLOT: CHECK P2v

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
// SLOT: CHECK P6v

// =========================================================================================
// Test-out (closed book: after every prediction of this module is recorded, before any
// reading; `scripts/firsttry.sh Q08 --check` refuses T1's first try until then)
// =========================================================================================

// item: Q08.T1v S6
// uses: trait-spec
/// **T1.** (test-out) Specify a trait method. `Toggle::flip` ships with no specification.
/// Write its postcondition so that the implementation for `Lamp` and the generic client
/// `flip_twice` both verify, then delete the client's labelled assume (the hole). Which
/// states does the postcondition relate, and what may it mention?
pub trait Toggle {
    spec fn on(&self) -> bool;

    fn flip(&mut self);
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
    proof {
        #[verifier::proof_note("Q08.T1v")] assume(false);  // HOLE: delete this proof block once `flip` is specified
    }
    t.flip();
    t.flip();
}
// Hint(1): a postcondition of a `&mut self` method can speak of `old(self)` and
//    `final(self)`.
// Hint(2): the trait knows `on()` and nothing about `Lamp`'s field.

fn flip_check() {
    // Uncomment as you go:
    // let mut l = Lamp { lit: false };
    // l.flip();
    // assert(l.lit);
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
/// **H3v.** Specify an odometer. `advance` ships with its precondition only and `current`
/// with no specification. Write the rest of both methods' specifications so that the
/// implementation for `Odo` verifies against them, the generic client `advance_twice`
/// verifies once its labelled assume (the hole) is deleted, and the check below verifies
/// once uncommented. What must hold after the first `advance` for the second one to be
/// allowed?
pub trait Odometer: Sized {
    spec fn reading(&self) -> nat;

    spec fn ok(&self) -> bool;

    fn advance(&mut self, by: u64)
        requires
            old(self).ok(),
    ;

    fn current(&self) -> (r: BigNat);
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
    proof {
        #[verifier::proof_note("Q08.H3v")] assume(false);  // HOLE: delete this proof block once both methods are specified
    }
    o.advance(a);
    o.advance(b);
}
// Hint(1): the client calls `advance` twice; read the second call's precondition.
// Hint(2): `current` copies the limbs of `total`: when is the copy a canonical BigNat?

fn current_check<O: Odometer>(o: &O)
    requires
        o.ok(),
{
    // Uncomment as you go:
    // let r = o.current();
    // assert(r.wf() && r.to_nat() == o.reading());
}

// item: Q08.H4v S6
// uses: trait-spec
/// **H4v.** Multiply through the trait: return a valid `T` worth `v.value() * k.value()`,
/// by repeated `plus`, using `NatLike`'s operations only (the function is generic: it
/// cannot see any implementation). How do you count to `k` when `k` is a `T`, and what
/// does the accumulator hold after `i` steps?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn scale<T: NatLike>(v: &T, k: &T) -> (r: T)
    requires
        v.valid(),
        k.valid(),
    ensures
        r.valid(),
        r.value() == v.value() * k.value(),
{
    unimplemented!()
}
// Hint(1): count with a `T` that starts at `T::zero()` and grows by `T::from_word(1)`;
//    `compare` tells you when to stop. Test its result with `matches!`: `==` on an
//    `Ordering` tells the verifier nothing.
// Hint(2): one step adds `v.value()` to the accumulator: `vstd::arithmetic::mul` has the
//    distributivity fact that makes that `v.value() * (i + 1)`.

fn scale_check() {
    // Uncomment as you go:
    // let v = from_u64(6);
    // let k = from_u64(7);
    // let r = scale(&v, &k);
    // assert(r.to_nat() == 42);
}

// =========================================================================================
// Final section: divergence card. Record every prediction of this module
// (scripts/firsttry.sh Q08 --check) before you read on or open its demos.
// =========================================================================================

// item: Q08.C5dv S7 diverge:q08-c5
// C5 — divergence card. Demos: specimens/Q08/card-c5dv-d.dfy.specimen and
// specimens/Q08/card-c5dv-v.rs.specimen.

} // verus!
