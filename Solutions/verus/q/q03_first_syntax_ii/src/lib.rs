//! # Q03 — First syntax II: modes, logic, tooling, trust (Reference Solution)
//!
//! Hole-free reference for `verus/q/q03_first_syntax_ii/src/lib.rs` (author-only; never
//! learner-visible). Same crate layout, imports, names, statements, item markers and
//! order as the exercise file. Every hole is filled, every check is live, and the verdict
//! switch is enabled; the verdict answer is in `Solutions/slots/Q03.slots`, its hash in
//! `expected/Q03.pins`.
//!
//! The file is silent: `scripts/vcheck --ref` on the crate prints only the summary line.
//! Every output the module quotes is pinned (`expected/Q03.counts`, `expected/Q03.freeze`,
//! the card demos' `// EXPECT` lines and sidecars).
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// =========================================================================================
// Test-out (closed book, before any reading)
// =========================================================================================

// item: Q03.T1v S7
// uses: ghost
// pair: Q03.T1d
/// **T1.** (test-out) The largest limb of a non-empty vector.
/// Method clause: keep the index of the current maximum in a `let ghost` variable.
///
/// Reference: the ghost index `w` is the witness of the `exists` postcondition; the
/// invariant `v@[w] == m` keeps it on the current maximum, and the `proof { }` block is
/// the only place a ghost variable may be assigned. `w` is erased from the compiled code.
pub fn max_limb(v: &Vec<u64>) -> (m: u64)
    requires
        v.len() > 0,
    ensures
        forall|i: int| 0 <= i < v.len() ==> v@[i] <= m,
        exists|i: int| 0 <= i < v.len() && v@[i] == m,
{
    let mut m = v[0];
    let ghost mut w: int = 0;
    let mut i: usize = 1;
    while i < v.len()
        invariant
            1 <= i <= v.len(),
            0 <= w < v.len(),
            v@[w] == m,
            forall|j: int| 0 <= j < i ==> v@[j] <= m,
        decreases v.len() - i,
    {
        if v[i] > m {
            m = v[i];
            proof {
                w = i as int;
            }
        }
        i = i + 1;
    }
    m
}

fn max_limb_check() {
    let mut v: Vec<u64> = Vec::new();
    v.push(7);
    let m = max_limb(&v);
    assert(m == 7);
}

// =========================================================================================
// The prediction block. Commit every prediction of this module before you read past this
// block, and record the first tries:
//     scripts/firsttry.sh Q03 --check
// The verdict answer goes in slots/Q03.slots. The Dafny file's prediction block holds the
// cross-language predictions (P1, P2, P5–P8); specimens/Q03/ holds P3, P10 and P11–P14.
// =========================================================================================

// item: Q03.P4v S7 verdict
// **P4.** Modes. Four separate crates. Each holds these two declarations:
/*
    fn triple(x: u64) -> (r: u64)
        requires
            x < 1000,
        ensures
            r == 3 * x,
    {
        x * 3
    }

    proof fn lemma_pos(x: int)
        requires
            x > 0,
        ensures
            2 * x > x,
    {
    }

  and one more function, which makes one call:

    [a] a proof fn calls the exec fn:
            proof fn call_a() {
                let y = triple(3);
            }
    [b] a spec fn calls the exec fn:
            spec fn call_b() -> u64 {
                triple(3)
            }
    [c] an exec fn calls the proof fn on `x as int`, outside any proof block:
            fn call_c(x: u64) {
                if x > 0 {
                    lemma_pos(x as int);
                }
            }
    [d] the same call inside a `proof { }` block:
            fn call_d(x: u64) {
                if x > 0 {
                    proof {
                        lemma_pos(x as int);
                    }
                }
            }
*/
// Which of the four crates does `scripts/vcheck` accept (verified)?
// Answer form: the accepted labels in label order, separated by single spaces, or `none`.
// CHECK P4v

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q03.W1v S7
/// **W1.** The mode triangle. A spec fn says what a value is, a proof fn proves a fact
/// about it, and an exec fn is specified through the spec fn and calls the proof fn
/// inside a `proof { }` block (ghost code inside exec code).
pub open spec fn succ_spec(x: int) -> int {
    x + 1
}

pub proof fn lemma_succ_gt(x: int)
    ensures
        succ_spec(x) > x,
{
}

pub fn succ(x: u64) -> (r: u64)
    requires
        x < u64::MAX,
    ensures
        r == succ_spec(x as int),
        r > x,
{
    proof {
        lemma_succ_gt(x as int);  // the fact `succ_spec(x as int) > x` is now known
    }
    x + 1
}

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q03/)
// =========================================================================================

// item: Q03.C1v S7 write:ghost
// C1 — card: ghost variables (`let ghost`, `Ghost<T>`).
// Jurisdiction: values the proof needs and the program never uses; they are checked,
// then erased. Success: `count_zero_limbs` keeps the limbs it has read in a ghost
// sequence, updated only inside `proof { }`. Failure: specimens/Q03/card-c1v.rs.specimen
// (a ghost value used by exec code).
pub open spec fn zero_count(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        zero_count(s.drop_last()) + if s.last() == 0 {
            1nat
        } else {
            0nat
        }
    }
}

pub fn count_zero_limbs(v: &Vec<u64>) -> (n: usize)
    ensures
        n == zero_count(v@),
{
    let mut n: usize = 0;
    let mut i: usize = 0;
    let ghost mut seen: Seq<u64> = Seq::empty();
    while i < v.len()
        invariant
            i <= v.len(),
            n <= i,
            seen == v@.subrange(0, i as int),
            n == zero_count(seen),
        decreases v.len() - i,
    {
        proof {
            assert(seen.push(v@[i as int]).drop_last() =~= seen);
            assert(seen.push(v@[i as int]) =~= v@.subrange(0, i as int + 1));
            seen = seen.push(v@[i as int]);
        }
        if v[i] == 0 {
            n = n + 1;
        }
        i = i + 1;
    }
    proof {
        assert(seen =~= v@);
    }
    n
}

// item: Q03.C2v S7 write:exec-check
// C2 — card: a runtime check that hands the verifier a fact.
// Jurisdiction: a precondition the caller cannot promise; test it in code and return the
// answer in an `Option`. Success: `safe_div`. Failure: specimens/Q03/card-c2v.rs.specimen
// (the unchecked division).
pub fn safe_div(a: u64, b: u64) -> (r: Option<u64>)
    ensures
        r.is_some() <==> b != 0,
        r.is_some() ==> r.unwrap() == a / b,
{
    if b != 0 {
        Some(a / b)
    } else {
        None
    }
}

// item: Q03.C3v S13 write:witness
// C3 — card: witnesses.
// Jurisdiction: an `exists` goal is proved by naming a term that works. Success:
// `lemma_exists_square_four` names 2. Failure: specimens/Q03/card-c3v.rs.specimen (the
// same proof fn, empty body).
pub open spec fn square(i: nat) -> nat {
    i * i
}

pub proof fn lemma_exists_square_four()
    ensures
        exists|i: nat| square(i) == 4,
{
    assert(square(2) == 4);
}

// item: Q03.C5v S7 write:modes
// C5 — card: spec, proof and exec modes.
// Jurisdiction: spec fns define (no code is run), proof fns prove (erased), exec fns run;
// ghost code reaches exec code only through `proof { }` blocks and ghost variables.
// Success: `half_spec`, `lemma_half_le` and `half`. Failure:
// specimens/Q03/card-c5v.rs.specimen (an exec variable assigned inside `proof { }`).
pub open spec fn half_spec(x: int) -> int {
    x / 2
}

pub proof fn lemma_half_le(x: int)
    requires
        x >= 0,
    ensures
        half_spec(x) <= x,
{
}

pub fn half(x: u64) -> (r: u64)
    ensures
        r == half_spec(x as int),
        r <= x,
{
    proof {
        lemma_half_le(x as int);
    }
    x / 2
}

// Rosetta card Q03.C9dv (quantifier triggers), Verus column. The card's marker and its
// Dafny column are in dafny/Q/Q03_FirstSyntaxII/core/Q03_FirstSyntaxII.dfy.
pub proof fn trigger_rosetta(s: Seq<u64>, k: int)
    requires
        forall|i: int| 0 <= i < s.len() ==> #[trigger] s[i] < 100,
        0 <= k < s.len(),
    ensures
        s[k] < 100,
{
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q03.H1v S7
// uses: invariant, ghost, modes
// pair: Q03.H1d
/// **H1.** Add one machine word to a BigNat, propagating the carry.
///
/// Reference: the ghost sequence `c` holds every carry, `c[0] == x` and `c[i]` the carry
/// into limb `i`. The invariant states the per-limb relation
/// `limb_at(a@, j) + c[j] == res@[j] + BASE * c[j + 1]` for every limb written so far,
/// which is exactly what the given `lemma_add_limb_lift` lifts to the value. The bounds
/// (`i <= n`, the lengths, `carry <= 1` after the first limb) keep the indices and the
/// arithmetic in range; `c[i] == carry` ties the ghost carries to the exec one, and
/// `c[0] == x` gives the lift's `c[0]`. Well-formedness of the result follows from
/// `a.wf()`: the top limb of `res` is `a`'s top limb plus a carry, or the final carry.
pub fn add_limb(a: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + x,
{
    let n = a.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut carry: u64 = x;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![x as nat];
    while i < n
        invariant
            n == a@.len(),
            // @hole-begin Q03.H1v
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == x,
            c[i as int] == carry,
            i > 0 ==> carry <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + c[j] == #[trigger] res@[j] + BASE * c[j + 1],
            // @hole-end Q03.H1v
        decreases n - i,
    {
        let li = a.limbs[i];
        if li <= u64::MAX - carry {
            res.push(li + carry);
            carry = 0;
        } else {
            res.push(li - (u64::MAX - carry) - 1);
            carry = 1;
        }
        i = i + 1;
        proof {
            c = c.push(carry as nat);
        }
    }
    if carry != 0 {
        res.push(carry);
        proof {
            c = c.push(0);
        }
    }
    let out = BigNat { limbs: res };
    proof {
        lemma_add_limb_lift(a@, out@, c);
    }
    out
}
// triv: { BigNat { limbs: Vec::new() } }

fn add_limb_check() {
    let a = BigNat { limbs: Vec::new() };
    let r = add_limb(&a, 5);
    assert(r.to_nat() == 5);
}

// item: Q03.H2v S7
// uses: modes, assert
// pair: Q03.H2d
/// **H2.** The BigNat of one machine word.
///
/// Reference: zero is the empty vector (canonical); any other word is the one limb `x`.
/// Its value needs two ghost steps in a `proof { }` block: the tail of a one-limb sequence
/// is empty, and the empty sequence has value 0, so `seq_to_nat` unfolds once to
/// `x + BASE * 0`.
pub fn from_u64(x: u64) -> (r: BigNat)
    ensures
        r.wf(),
        r.to_nat() == x,
{
    let mut v: Vec<u64> = Vec::new();
    if x != 0 {
        v.push(x);
        proof {
            assert(v@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(v@.drop_first()) == 0);
        }
    }
    BigNat { limbs: v }
}
// triv: { BigNat { limbs: Vec::new() } }

fn from_u64_check() {
    let r = from_u64(5);
    assert(r.to_nat() == 5);
    let z = from_u64(0);
    assert(z.to_nat() == 0);
}

// item: Q03.H3v S13
// uses: witness, assert
// pair: Q03.H3d
/// **H3.** Some canonical limb sequence has the value 5.
///
/// Reference: the witness is `seq![5u64]`. Its value needs the same two steps as in H2
/// (an empty tail, of value 0); the last `assert` states both conjuncts for the witness,
/// which puts its terms in front of the solver for the `exists`.
pub proof fn lemma_exists_canonical_five()
    ensures
        exists|s: Seq<u64>| seq_wf(s) && seq_to_nat(s) == 5,
{
    let w = seq![5u64];
    assert(w.drop_first() =~= Seq::<u64>::empty());
    assert(seq_to_nat(w.drop_first()) == 0);
    assert(seq_wf(w) && seq_to_nat(w) == 5);
}

// item: Q03.H4v S7
// uses: exec-check, modes
// pair: Q03.H4d
/// **H4.** A checked conversion from `u128` to a limb.
///
/// Reference: the runtime test against the literal 2^64 is exactly the spec's `x < BASE`
/// (a spec const, which exec code cannot read), and inside it the cast `x as u64` keeps
/// the value.
pub fn try_limb(x: u128) -> (r: Option<u64>)
    ensures
        r.is_some() <==> x < BASE,
        r.is_some() ==> r.unwrap() == x,
{
    if x < 0x1_0000_0000_0000_0000u128 {
        Some(x as u64)
    } else {
        None
    }
}
// triv: { None }

fn try_limb_check() {
    let r = try_limb(5);
    assert(r.is_some() && r.unwrap() == 5);
    let q = try_limb(0x1_0000_0000_0000_0000u128);
    assert(!q.is_some());
}

} // verus!
