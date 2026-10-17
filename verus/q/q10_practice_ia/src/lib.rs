//! # Q10 — Practice I-A: the Verus half (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l5` (`use
//! qg_bignat_l5::*;` brings all five layers' names) and the vstd prelude, nothing else:
//! no earlier exercise crate. The layers are frozen and complete; read them, never edit
//! them.
//!
//! How to work this file:
//! 1. Predictions first: both predictions of the module are in the Dafny file's prediction
//!    block (dafny/Q/Q10_PracticeIA/std/Q10_PracticeIA.dfy; their answers go in
//!    slots/Q10.slots); record the first tries with `scripts/firsttry.sh Q10 --check`
//!    before you run anything they are about.
//! 2. Replace each hole, then uncomment the checks beneath it. Every statement is given;
//!    each item has one hole. The ring buffer (W1, then H6 and H7) comes last.
//! 3. Done = `scripts/vcheck --gate verus/q/q10_practice_ia` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q10_practice_ia` reports no finding, AND
//!    `scripts/firsttry.sh Q10 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q10.
//!
//! This file ships with exactly 7 holes (H1 to H7), each counted by `scripts/vcheck`
//! (Verus runs with `--no-cheating`, which turns each hole into one counted diagnostic).
//! Commit every prediction BEFORE you run anything it is about, open later files, or read
//! CI, the registry or the plan: their checks and headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header. Exit (closed book,
//! timed): src/exit.rs here and the Dafny exit file, scored once by
//! `scripts/firsttry.sh Q10 --exit`; src/exit.rs is never part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l5::*;

verus! {

// =========================================================================================
// Holes
// =========================================================================================

// item: Q10.H1v S1
// uses: exec-check, lemma-call
// pair: Q10.H1d
/// **H1.** A canonical BigNat as one word: `Some` of its value when the value fits in one
/// limb, `None` when it does not. The given client `round_trip` below checks it on every
/// word. Why does no canonical BigNat of two or more limbs fit, and what must the verifier
/// be told in each case?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn to_u64(a: &BigNat) -> (r: Option<u64>)
    requires
        a.wf(),
    ensures
        r is Some <==> a.to_nat() < BASE,
        r is Some ==> r->0 as nat == a.to_nat(),
{
    unimplemented!()
}
// Hint(1): split on the number of limbs. With one limb, the verifier must see that the
//    view without its first limb is empty, and what that empty view is worth.
// Hint(2): with two or more, layer L3 bounds a canonical value from below by a weight;
//    L3's monotonicity and its two equations of `weight` compare that weight with `BASE`.

/// The given client: a word's BigNat converts back to the word.
pub fn round_trip(x: u64) -> (r: Option<u64>)
    ensures
        r == Some(x),
{
    let b = from_u64(x);
    to_u64(&b)
}

// item: Q10.H2v S2
// uses: ensures
/// **H2.** Specify the top limb. `high_limb` returns the most significant limb of `a`, or
/// 0 for the empty number. Its body is given and it ships with no `ensures`. Write its
/// `ensures` so that the body verifies against it and the given client `high_client`
/// verifies once its labelled assume (the hole) is deleted. What does a canonical BigNat's
/// top limb tell you about its length?
pub fn high_limb(a: &BigNat) -> (r: u64)
    requires
        a.wf(),
{
    if a.limbs.len() == 0 {
        0
    } else {
        a.limbs[a.limbs.len() - 1]
    }
}
// Hint(1): read `high_client`: from `h == 0` it concludes that the value is zero. Which
//    fact about the view makes the value zero?
// Hint(2): `wf` says the top limb of a non-empty view is not zero.

/// The given client: with `high_limb` specified, it verifies with no assume.
pub fn high_client(a: &BigNat)
    requires
        a.wf(),
{
    proof {
        #[verifier::proof_note("Q10.H2v")] assume(false);  // HOLE: delete this proof block once `high_limb` is specified
    }
    let h = high_limb(a);
    if h == 0 {
        assert(a.to_nat() == 0);
    }
}

// item: Q10.H3v S3
// uses: assert, lemma-call
// pair: Q10.H3d
/// **H3.** The top limb's place value: an assertion repair. This attempt does not verify
/// (run it to see where it fails):
///
///     lemma_seq_to_nat_append(s.drop_last(), seq![s.last()]);
///     assert(seq![s.last()].drop_first() =~= Seq::<u64>::empty());
///     assert(seq_to_nat(seq![s.last()].drop_first()) == 0);
///
/// Repair it: copy it into the body in place of the hole, add what the verifier is
/// missing, and change no line of the attempt. L4's append lemma speaks about a
/// concatenation: what must the verifier know about that concatenation and `s`?
pub proof fn lemma_top_limb(s: Seq<u64>)
    requires
        s.len() > 0,
    ensures
        seq_to_nat(s) == seq_to_nat(s.drop_last()) + weight((s.len() - 1) as nat) * s.last(),
{
    #[verifier::proof_note("Q10.H3v")] assume(false);  // HOLE: replace this line
}
// Hint(1): two sequences that hold the same elements are not the same term to the
//    verifier until an assertion says so.
// Hint(2): `=~=` is extensional equality.

// item: Q10.H4v S4
// uses: invariant
// pair: Q10.H4d
/// **H4.** The forward-scan normalize. `norm_len` scans the limbs once, from the lowest
/// up, and remembers in `n` one past the last non-zero limb it has seen, so that every limb
/// from `n` on is zero. The code and the loop's `decreases` are given: write the loop
/// invariant. What has the scan established about the limbs below `i`?
pub fn norm_len(v: &Vec<u64>) -> (n: usize)
    ensures
        n <= v@.len(),
        n == 0 || v@[n - 1] != 0,
        forall|j: int| n <= j < v@.len() ==> v@[j] == 0,
{
    #[verifier::proof_note("Q10.H4v")] assume(false);  // HOLE: delete this line, then write the loop invariant
    let mut n: usize = 0;
    let mut i: usize = 0;
    while i < v.len()
        decreases v@.len() - i,
    {
        if v[i] != 0 {
            n = i + 1;
        }
        i = i + 1;
    }
    n
}
// Hint(1): at the exit `i == v@.len()`: write each postcondition with `i` in place of the
//    length, and keep the bounds of `n` and `i`.
// Hint(2): `invariant` goes before `decreases`, one clause per line, each ending in a
//    comma.

fn norm_len_check() {
    // Uncomment as you go:
    // let mut v: Vec<u64> = Vec::new();
    // v.push(3);
    // v.push(0);
    // assert(v@[0] == 3 && v@[1] == 0);
    // let n = norm_len(&v);
    // assert(n == 1);
}

// item: Q10.H5v S5
// uses: library-call
// pair: Q10.H5d
/// **H5.** Search, then name: a remainder of a remainder. Taking `x` modulo
/// `weight(n + 1)` and then modulo `weight(n)` is the same as taking it modulo
/// `weight(n)`. Find the lemma of `vstd::arithmetic` that does the work, and call it with
/// arguments that meet its `requires`.
pub proof fn lemma_mod_weight_succ(x: nat, n: nat)
    ensures
        x % weight(n + 1) % weight(n) == x % weight(n),
{
    #[verifier::proof_note("Q10.H5v")] assume(false);  // HOLE: replace this line
}
// Hint(1): L3's second equation writes `weight(n + 1)` as a product: look for a lemma about
//    a remainder by a product. A vstd lemma takes `int` arguments: cast with `as int`.
// Hint(2): its `requires` asks for positive factors (layer L5 gives one of them), and its
//    product may come in the other order than L3's.

// =========================================================================================
// The ring buffer
// =========================================================================================

// item: Q10.W1v S1
/// **W1.** A ring buffer of words. `buf` is the storage, `head` the position of the first
/// element and `len` the number of elements; the elements wrap around the end of `buf`.
/// `inv` keeps `head` and `len` inside the storage, `slot(i)` is the storage position of
/// element `i` (the wrap is a comparison, not a remainder), and the view `self@` is the
/// sequence of the `len` elements in order. `new` is given and verified.
pub struct Ring {
    pub buf: Vec<u64>,
    pub head: usize,
    pub len: usize,
}

impl Ring {
    pub open spec fn inv(&self) -> bool {
        self.buf@.len() > 0 && self.head < self.buf@.len() && self.len <= self.buf@.len()
    }

    pub open spec fn slot(&self, i: int) -> int {
        if self.head + i < self.buf@.len() {
            self.head + i
        } else {
            self.head + i - self.buf@.len()
        }
    }

    pub open spec fn view(&self) -> Seq<u64> {
        Seq::new(self.len as nat, |i: int| self.buf@[self.slot(i)])
    }

    pub fn new(cap: usize) -> (r: Ring)
        requires
            cap > 0,
        ensures
            r.inv(),
            r.buf@.len() == cap,
            r.len == 0,
            r@ == Seq::<u64>::empty(),
    {
        let mut buf: Vec<u64> = Vec::new();
        let mut k: usize = 0;
        while k < cap
            invariant
                k <= cap,
                buf@.len() == k,
            decreases cap - k,
        {
            buf.push(0);
            k = k + 1;
        }
        let r = Ring { buf, head: 0, len: 0 };
        proof {
            assert(r@ =~= Seq::<u64>::empty());
        }
        r
    }

    // item: Q10.H6v S1
    // uses: exec-check
    /// **H6.** Read element `i` of the buffer. Compute its storage position the way `slot`
    /// does, with a comparison and no remainder, and so that no subtraction or addition in
    /// the code can overflow or go below zero. Which comparison is safe to compute?
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn get(&self, i: usize) -> (r: u64)
        requires
            self.inv(),
            i < self.len,
        ensures
            r == self@[i as int],
    {
        unimplemented!()
    }
    // Hint(1): `self.head + i < self.buf.len()` may overflow in exec code; an equivalent
    //    comparison subtracts instead, on the side that cannot go below zero.
    // Hint(2): in the wrapped case the position is `i` minus the number of slots from
    //    `head` to the end of the storage.

    // item: Q10.H7v S1
    // uses: mut-ref, assert
    /// **H7.** Append one element. The free position is the slot just past the last
    /// element; write `x` there and grow `len`. Then say what the new view is. Which slots
    /// does the write leave untouched?
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn push_back(&mut self, x: u64)
        requires
            old(self).inv(),
            old(self).len < old(self).buf@.len(),
        ensures
            final(self).inv(),
            final(self)@ == old(self)@.push(x),
    {
        unimplemented!()
    }
    // Hint(1): compute the free position as `get` computes element `i`'s, for `i == len`;
    //    `self.buf.set(idx, x)` writes it.
    // Hint(2): keep the old view in a `let ghost` before the write, and finish with an
    //    extensional equality between the new view and the old one pushed with `x`.
}

/// A check of the ring buffer's operations.
fn ring_check() {
    // Uncomment as you go:
    // let mut q = Ring::new(3);
    // q.push_back(7);
    // assert(q@.len() == 1);
    // let a = q.get(0);
    // assert(a == 7);
}

} // verus!
