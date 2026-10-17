//! # Q04 — the library module of the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q04_proof_craft/src/library.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise module; every hole is filled and every check is live. The twin of the H4v
//! annotation hole marks the learner's two regions with `@hole-begin` / `@hole-end`, and
//! the exec items declare their trivial bodies in `// triv:` lines.
//!
//! Silent under `scripts/vcheck --ref` on the crate.
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
/// **H1.** Weights add: `weight(m + n) == weight(m) * weight(n)`.
///
/// Reference: recursion on `m`. For `m == 0`, `weight(0) == 1`. Otherwise, with
/// `k == m - 1`, the call gives `weight(k + n) == weight(k) * weight(n)`, the two
/// `lemma_weight_succ` calls unfold `weight(m + n)` and `weight(m)` once each, and the
/// chain reassociates `BASE * (weight(k) * weight(n))`, which needs
/// `lemma_mul_is_associative` (the default solver treats a product of three terms as
/// opaque; without the call the chain fails).
pub proof fn lemma_weight_add(m: nat, n: nat)
    ensures
        weight(m + n) == weight(m) * weight(n),
    decreases m,
{
    if m == 0 {
        lemma_weight_zero();
        assert(m + n == n);
    } else {
        let k = (m - 1) as nat;
        lemma_weight_add(k, n);
        lemma_weight_succ(k + n);
        lemma_weight_succ(k);
        calc! {
            (==)
            weight(m + n); { assert(m + n == (k + n) + 1); }
            BASE * weight(k + n);
            (==) {}
            BASE * (weight(k) * weight(n));
            (==) { lemma_mul_is_associative(BASE as int, weight(k) as int, weight(n) as int); }
            (BASE * weight(k)) * weight(n);
            (==) {}
            weight(m) * weight(n);
        }
    }
}

proof fn weight_add_check(n: nat) {
    lemma_weight_add(n, 1);
    assert(weight(n + 1) == weight(n) * weight(1));
    lemma_weight_add(0, n);
    assert(weight(n) == weight(0) * weight(n));
}

// item: Q04.H3v S5
// uses: library-call
// pair: Q04.H3d
/// **H3.** A shifted value stays below the next weight.
///
/// Reference: H1v gives `weight(n + m) == weight(n) * weight(m)`; `lemma_weight_zero` and
/// `lemma_weight_mono(0, m)` give `weight(m) >= 1`; and the library's
/// `lemma_mul_strict_inequality` turns `x < weight(n)` into
/// `x * weight(m) < weight(n) * weight(m)`.
pub proof fn lemma_shift_bound(x: nat, n: nat, m: nat)
    requires
        x < weight(n),
    ensures
        x * weight(m) < weight(n + m),
{
    lemma_weight_add(n, m);
    lemma_weight_zero();
    lemma_weight_mono(0, m);
    lemma_mul_strict_inequality(x as int, weight(n) as int, weight(m) as int);
}

proof fn shift_bound_check(x: nat, n: nat)
    requires
        x < weight(n),
{
    lemma_shift_bound(x, n, 2);
    assert(x * weight(2) < weight(n + 2));
}

// item: Q04.H4v S5
// uses: broadcast-use
// pair: Q04.H4d
/// **H4.** Compare two BigNats.
///
/// Reference: two learner regions. The group line brings L3's bounds into the body: a
/// shorter canonical number is below `weight` of its length and a longer one at least
/// `weight` of its length minus one, which settles the two length cases; and the given
/// `lemma_lt_at` calls settle the last differing limb. The invariant's missing clause says
/// that the limbs scanned so far, from `i` to the top, agree; at the exit either `i == 0`
/// (all limbs agree, so the views are equal) or the limbs at `i - 1` differ, which with
/// the clause is exactly `lemma_lt_at`'s precondition.
pub fn cmp(a: &BigNat, b: &BigNat) -> (r: Ordering)
    requires
        a.wf(),
        b.wf(),
    ensures
        (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
        (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
        (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
{
    // @hole-begin Q04.H4v
    broadcast use group_bignat_bounds;  // did: the two length cases, through the bounds' triggers
    // @hole-end Q04.H4v

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
            // @hole-begin Q04.H4v
            forall|j: int| i <= j < n ==> a@[j] == b@[j],
            // @hole-end Q04.H4v
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
// triv: { Ordering::Equal }

fn cmp_check() {
    let a = BigNat { limbs: Vec::new() };
    let b = from_u64(5);
    let r = cmp(&a, &b);
    assert(r == Ordering::Less);
    let s = cmp(&b, &a);
    assert(s == Ordering::Greater);
    let t = cmp(&b, &b);
    assert(t == Ordering::Equal);
}

// item: Q04.H5v S5
// uses: nonlinear-arith
/// **H5.** A value times a limb fits in one more limb.
///
/// Reference: `lemma_weight_succ(n)` gives `weight(n + 1) == BASE * weight(n)`, and one
/// nonlinear assertion, given `x < weight(n)` and `d < BASE` in its `requires`, bounds the
/// product by `weight(n) * BASE`.
pub proof fn lemma_value_times_limb(x: nat, d: nat, n: nat)
    requires
        x < weight(n),
        d < BASE,
    ensures
        x * d < weight(n + 1),
{
    lemma_weight_succ(n);
    let w = weight(n);
    // did: the product bound x * d < w * BASE, from the two factor bounds
    assert(x * d < w * BASE) by (nonlinear_arith)
        requires
            x < w,
            d < BASE,
    ;
}

proof fn value_times_limb_check(x: nat, n: nat)
    requires
        x < weight(n),
{
    lemma_value_times_limb(x, 7, n);
    assert(x * 7 < weight(n + 1));
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
