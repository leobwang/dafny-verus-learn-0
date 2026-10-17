//! # Q04 — the library module of the Verus half (Exercises)
//!
//! The module `library` of the crate `q04_proof_craft` (the crate root, src/lib.rs,
//! declares it with `mod library;`). Imports: the vstd prelude, vstd's `calc!` macro, the
//! multiplication lemmas of `vstd::arithmetic::mul`, the given BigNat spine (`use
//! qg_bignat_l3::*;`) and `core::cmp::Ordering`. This is the crate's library file: only
//! here does Q04's Verus half call `vstd::arithmetic` lemmas or bring in a lemma group.
//!
//! How to work this file:
//! 1. Work it after src/lib.rs (commit every Q04 prediction first, and do src/lib.rs's T1
//!    and H2, which call L3's lemmas by name, before the group here).
//! 2. Replace each hole, then uncomment the checks beneath it.
//! 3. Done = `scripts/vcheck --gate verus/q/q04_proof_craft` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q04_proof_craft` reports no finding, AND
//!    `scripts/firsttry.sh Q04 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q04.
//!
//! This file ships with exactly 4 holes, H1, H3, H4 and H5, each counted by
//! `scripts/vcheck` on the crate. Item kinds and the slot protocol: the header of
//! dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::calc;
use qg_bignat_l3::*;
use core::cmp::Ordering;

verus! {

// =========================================================================================
// WRITE cards (each: a success here, a pinned failure demo in specimens/Q04/)
// =========================================================================================

// item: Q04.C4v S5 write:library-call
// C4 — card: calling a `vstd::arithmetic` lemma.
// Jurisdiction: a fact the library already proves. Call the proof fn (`use
// vstd::arithmetic::mul::*;` brings its name), with arguments that make its `requires`
// hold at the call; its `ensures` holds after it. The library states its lemmas over
// `int`, so `nat` arguments are cast. Success: `lemma_scale_le`. Failure:
// specimens/Q04/card-c4v.rs.specimen (the same call with its precondition unmet).
pub proof fn lemma_scale_le(a: nat, b: nat, w: nat)
    requires
        a <= b,
    ensures
        a * w <= b * w,
{
    lemma_mul_inequality(a as int, b as int, w as int);
}

// item: Q04.C5v S5 write:broadcast-use
// C5 — card: `broadcast use`, scoped to one proof.
// Jurisdiction: facts a group of lemmas gives whenever their trigger terms appear, so that
// no call names them. First the named calls, then the group: `broadcast use` at the top of
// a body brings the group into that body only. Success: `lemma_weight_order_by_name` and
// `lemma_weight_order_by_group` (L3's bounds group). Failure:
// specimens/Q04/card-c5v.rs.specimen (the group version without its `broadcast use` line).
pub proof fn lemma_weight_order_by_name(k: nat, m: nat, n: nat)
    requires
        k <= m,
        m <= n,
    ensures
        weight(k) <= weight(n),
{
    lemma_weight_mono(k, m);
    lemma_weight_mono(m, n);
}

pub proof fn lemma_weight_order_by_group(k: nat, m: nat, n: nat)
    requires
        k <= m,
        m <= n,
    ensures
        weight(k) <= weight(n),
{
    broadcast use group_bignat_bounds;  // did: weight(k) <= weight(n), through lemma_weight_mono's triggers
}

// item: Q04.C6v S5 write:nonlinear-arith
// C6 — card: `assert … by (nonlinear_arith) requires …`.
// Jurisdiction: a product fact the default solver does not attempt (it treats a product
// of two variables as opaque). First by hand with one library lemma, then with the
// nonlinear prover, which works apart from the rest of the proof: the assertion's
// `requires` lists the facts of the context it needs. Success: `lemma_product_le_by_hand` and
// `lemma_product_le_by_nl`. Failure: specimens/Q04/card-c6v.rs.specimen (the nonlinear
// assertion without its `requires`).
pub proof fn lemma_product_le_by_hand(x: nat, y: nat, xb: nat, yb: nat)
    requires
        x <= xb,
        y <= yb,
    ensures
        x * y <= xb * yb,
{
    lemma_mul_upper_bound(x as int, xb as int, y as int, yb as int);
}

pub proof fn lemma_product_le_by_nl(x: nat, y: nat, xb: nat, yb: nat)
    requires
        x <= xb,
        y <= yb,
    ensures
        x * y <= xb * yb,
{
    // did: the product bound, from the two factor bounds
    assert(x * y <= xb * yb) by (nonlinear_arith)
        requires
            x <= xb,
            y <= yb,
    ;
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q04.H1v S5
// uses: calc, lemma-recursion, library-call
// pair: Q04.H1d
/// **H1.** Weights add: `weight(m + n) == weight(m) * weight(n)`. Method clause: as the
/// Dafny file's H1, a recursive call and a `calc!` chain; L3's two weight equations
/// (`lemma_weight_zero`, `lemma_weight_succ`) are the only facts about `weight` it may
/// use, and `vstd::arithmetic` lemmas may close a step. Which step of the chain is not
/// about `weight` at all?
pub proof fn lemma_weight_add(m: nat, n: nat)
    ensures
        weight(m + n) == weight(m) * weight(n),
    decreases m,
{
    #[verifier::proof_note("Q04.H1v")] assume(false);  // HOLE: replace this line
}
// Hint(1): name `k == (m - 1) as nat` with a `let`; the call on `k` and the two weight
//    equations at `k + n` and at `k` give every fact about `weight` the chain needs.
// Hint(2): the default solver does not regroup a product of three terms: one step of the
//    chain needs a lemma of `vstd::arithmetic::mul` as its hint.

proof fn weight_add_check(n: nat) {
    // Uncomment as you go:
    // lemma_weight_add(n, 1);
    // assert(weight(n + 1) == weight(n) * weight(1));
}

// item: Q04.H3v S5
// uses: library-call
// pair: Q04.H3d
/// **H3.** A value below `weight(n)`, shifted up by `m` limbs, stays below
/// `weight(n + m)`. Method clause: `vstd::arithmetic` lemmas, L3's lemmas called by name
/// (no `broadcast use`), and H1 above. What does the proof need to know about `weight(m)`
/// before a library fact about products applies?
pub proof fn lemma_shift_bound(x: nat, n: nat, m: nat)
    requires
        x < weight(n),
    ensures
        x * weight(m) < weight(n + m),
{
    #[verifier::proof_note("Q04.H3v")] assume(false);  // HOLE: replace this line
}
// Hint(1): H1 turns `weight(n + m)` into a product.
// Hint(2): a product inequality of `vstd::arithmetic::mul` needs a positive factor; two of
//    L3's lemmas, called by name, show that `weight(m)` is one.

proof fn shift_bound_check(x: nat, n: nat)
    requires
        x < weight(n),
{
    // Uncomment as you go:
    // lemma_shift_bound(x, n, 2);
    // assert(x * weight(2) < weight(n + 2));
}

// item: Q04.H4v S5
// uses: broadcast-use
// pair: Q04.H4d
/// **H4.** Compare two BigNats: the result agrees with the order of their values. The
/// code is given: a shorter canonical number is the smaller; for equal lengths a loop
/// scans down from the top limb while the limbs agree, then one comparison decides. The
/// loop's `decreases`, the invariant clauses about the index and the lengths, and the
/// `lemma_lt_at` calls are given too. Write the invariant's remaining clause and the one
/// line that brings L3's bounds group into this function. What do the limbs scanned so far
/// have in common, and which given facts settle the two length cases?
pub fn cmp(a: &BigNat, b: &BigNat) -> (r: Ordering)
    requires
        a.wf(),
        b.wf(),
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    #[verifier::proof_note("Q04.H4v")] assume(false);  // HOLE: delete this line; write the group line here and the invariant's remaining clause below
    let n = a.limbs.len();
    let m = b.limbs.len();
    if n < m {
        return Ordering::Less;
    }
    if n > m {
        return Ordering::Greater;
    }
    let mut i = n;
    while i > 0 && a.limbs[i - 1] == b.limbs[i - 1]
        invariant
            i <= n,
            n == a@.len(),
            n == b@.len(),
        decreases i,
    {
        i = i - 1;
    }
    if i == 0 {
        proof {
            assert(a@ =~= b@);
        }
        Ordering::Equal
    } else if a.limbs[i - 1] < b.limbs[i - 1] {
        proof {
            lemma_lt_at(a@, b@, (i - 1) as int);
        }
        Ordering::Less
    } else {
        proof {
            lemma_lt_at(b@, a@, (i - 1) as int);
        }
        Ordering::Greater
    }
}
// Hint(1): the group line is `broadcast use <group>;`, first in the body; L3's group is
//    named in L3's file.
// Hint(2): the missing clause is a `forall` over the indices from `i` to the top.

fn cmp_check() {
    // Uncomment as you go:
    // let a = BigNat { limbs: Vec::new() };
    // let b = from_u64(5);
    // let r = cmp(&a, &b);
    // assert(r == Ordering::Less);
}

// item: Q04.H5v S5
// uses: nonlinear-arith
/// **H5.** A value times a limb fits in one more limb: if `x < weight(n)` and `d < BASE`,
/// then `x * d < weight(n + 1)`. Which product bound does the proof need, and which facts
/// must its `requires` hand to the nonlinear prover?
pub proof fn lemma_value_times_limb(x: nat, d: nat, n: nat)
    requires
        x < weight(n),
        d < BASE,
    ensures
        x * d < weight(n + 1),
{
    #[verifier::proof_note("Q04.H5v")] assume(false);  // HOLE: replace this line
}
// Hint(1): one weight equation writes `weight(n + 1)` as a product.
// Hint(2): give `weight(n)` a name with `let`, so that the nonlinear assertion's
//    `requires` can speak about it.

proof fn value_times_limb_check(x: nat, n: nat)
    requires
        x < weight(n),
{
    // Uncomment as you go:
    // lemma_value_times_limb(x, 7, n);
    // assert(x * 7 < weight(n + 1));
}

// =========================================================================================
// Final section: divergence card. Record every prediction of this module
// (scripts/firsttry.sh Q04 --check) before you read on or open its demos.
// =========================================================================================

// item: Q04.C9dv S5 diverge:q04-c9
// C9 — divergence card: how each language makes its standard library available. Demos:
//    specimens/Q04/card-c9dv-d.dfy.specimen and specimens/Q04/card-c9dv-v.rs.specimen;
//    run each with `scripts/vcheck` and compare. The chapter explains the difference.

} // verus!
