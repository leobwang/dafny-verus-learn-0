/*!
# Q04 — Proof craft, loops and libraries: the library file (Reference Solution)

Hole-free reference for `dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled and every check is live.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned (`expected/Q04.counts`,
`expected/Q04.freeze`, the card demo's `// EXPECT` line).
*/
module Q04_Library {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power
  import Mul = Std.Arithmetic.Mul

  // ===========================================================================
  // WRITE card (a success here, a pinned failure demo in specimens/Q04/)
  // ===========================================================================

  // item: Q04.C4d S5 write:library-call
  /** ### C4 — card: calling a standard-library lemma.
      Jurisdiction: a fact the library already proves. Name the lemma through
      its module (`Mul.LemmaMulInequality`), pass arguments that make its
      `requires` hold at the call, and its `ensures` holds after it. Success:
      `ScaleLe`. Failure: specimens/Q04/card-c4d.dfy.specimen (the same call
      with its precondition unmet). */
  lemma ScaleLe(a: nat, b: nat, w: nat)
    requires a <= b
    ensures a * w <= b * w
  {
    Mul.LemmaMulInequality(a, b, w);
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q04.H3d S5
  // uses: library-call
  // pair: Q04.H3v
  /** **H3.** A shifted value stays below the next power.

      Reference: three bridges move `Pow(n)`, `Pow(m)` and `Pow(n + m)` to
      `Power.Pow(BASE, …)`; `Power.LemmaPowAdds(BASE, n, m)` gives
      `Pow(n + m) == Pow(n) * Pow(m)`, `Power.LemmaPowPositive(BASE, m)` gives
      `Pow(m) > 0`, and `Mul.LemmaMulStrictInequality(x, Pow(n), Pow(m))`
      turns `x < Pow(n)` into `x * Pow(m) < Pow(n) * Pow(m)`. Without the last
      call the solver runs out of resource on the product. */
  lemma ShiftBound(x: nat, n: nat, m: nat)
    requires x < Pow(n)
    ensures x * Pow(m) < Pow(n + m)
  {
    PowIsStdPow(n);
    PowIsStdPow(m);
    PowIsStdPow(n + m);
    Power.LemmaPowAdds(BASE, n, m);
    Power.LemmaPowPositive(BASE, m);
    Mul.LemmaMulStrictInequality(x, Pow(n), Pow(m));
  }

  lemma ShiftBoundCheck(x: nat, n: nat)
    requires x < Pow(n)
  {
    ShiftBound(x, n, 3);
    assert x * Pow(3) < Pow(n + 3);
    ShiftBound(x, n, 0);
    assert x * Pow(0) < Pow(n + 0);
  }

  // item: Q04.H4d S4
  // uses: lemma-recursion
  // pair: Q04.H4v
  /** **H4.** `Cmp` (layer L3) agrees with the order of the values.

      Reference: recursion along `Cmp`'s own recursion, on the tails, when
      either sequence is non-empty. `ValidTail` gives valid tails (so the
      call applies) and heads below `BASE`; `ToNatHeadTail` writes each value
      as its head plus `BASE` times its tail's value. If the tails' values
      differ, they differ by at least 1, and `BASE` times that exceeds any
      difference of the heads, so the tails decide, as `Cmp` does; if they are
      equal, the heads decide. Two empty sequences compare equal. */
  lemma CmpCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures -1 <= Cmp(a, b) <= 1
            && (Cmp(a, b) < 0 <==> ToNat(a) < ToNat(b))
            && (Cmp(a, b) == 0 <==> ToNat(a) == ToNat(b))
    decreases |a| + |b|
  {
    if |a| != 0 || |b| != 0 {
      ValidTail(a);
      ValidTail(b);
      CmpCorrect(Tail(a), Tail(b));
      ToNatHeadTail(a);
      ToNatHeadTail(b);
    }
  }

  lemma CmpCorrectCheck(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b) && ToNat(a) < ToNat(b)
  {
    CmpCorrect(a, b);
    assert Cmp(a, b) == -1;
    CmpCorrect(b, a);
    assert Cmp(b, a) == 1;
    CmpCorrect(a, a);
    assert Cmp(a, a) == 0;
  }
}

/*
TOOLCHAIN LAB (learner-owned; no script reads it). Done by hand in your own
terminal, in a scratch directory under /tmp: never in the course tree and never
in a Claude session. The pinned binaries are under .toolchain/
(`scripts/get_toolchain.sh dafny --check` and `… verus --check` print their
paths). For each run, write the command, its exit code and the first line it
printed.
  1. Dafny and Z3: `dafny verify` on a one-lemma file, three ways:
     (a) as scripts/vcheck runs it (the bundled default solver);
     (b) with --solver-path naming the other Z3 bundled in the Dafny tree;
     (c) with --solver-path naming a path that does not exist.
  2. Verus and Z3: `verus` on a one-function file, then again with
     VERUS_Z3_PATH naming that other Z3.
  3. Verus and rustc: compare the `Toolchain:` line of `verus --version` with
     `rustc --version` and `rustup toolchain list`, run outside the course
     tree; then run `verus` once with RUSTUP_TOOLCHAIN naming your default
     toolchain.
  4. The two library tiers: read dafny/options/core.toml and std.toml, and the
     import lines of Q04_ProofCraft.dfy, this file, lib.rs and library.rs.
     Which standard-library module may no BigNat file import?
  Then read VERSIONS.md §1 (the pinned toolchains), and only that section.

  1a:
  1b:
  1c:
  2 (plain):
  2 (VERUS_Z3_PATH):
  3 (versions):
  3 (RUSTUP_TOOLCHAIN):
  4:
*/
