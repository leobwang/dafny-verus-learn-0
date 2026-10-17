/*!
# Q04 — Proof craft, loops and libraries: the library file (Exercises)

Imports: the given BigNat spine, layers L1–L3 (`QG_L1_BigNat`, `QG_L2_BigNat`,
`QG_L3_BigNat`), and two modules of Dafny's standard library,
`Std.Arithmetic.Power` and `Std.Arithmetic.Mul`. This file is the unit
dafny/Q/Q04_ProofCraft/std, whose dfyconfig.toml switches the standard library
on. The layers are frozen and complete; read them, never edit them.

How to work this file:
1. Work it after dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy: commit every
   Q04 prediction first (that file's header), and do its H1, powers by hand,
   before any library call here.
2. Replace each hole, then uncomment the checks beneath it.
3. Fill the TOOLCHAIN LAB block at the end of this file, by hand in your own
   terminal.
4. Done = `scripts/vcheck --gate dafny/Q/Q04_ProofCraft/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q04_ProofCraft/std`
   reports no finding, AND `scripts/firsttry.sh Q04 --report --strict` exits 0.
5. Stuck for 20 minutes? /tutor Q04.

This file ships with exactly 2 holes, H3 and H4, each counted by
`scripts/vcheck`. Item kinds and the slot protocol: the header of
Q04_ProofCraft.dfy.
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
  /** **H3.** A value below `Pow(n)`, shifted up by `m` limbs, stays below
      `Pow(n + m)`. Method clause: standard-library lemmas and L3's bridge
      `PowIsStdPow` only, no lemma of your own. Which facts about
      `Power.Pow(BASE, …)` and about products does the proof need, and what
      must each call's `requires` be given? */
  lemma ShiftBound(x: nat, n: nat, m: nat)
    requires x < Pow(n)
    ensures x * Pow(m) < Pow(n + m)
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
  // Hint(1): move every power that appears to `Power.Pow(BASE, …)` with the
  //    bridge, one call per power.
  // Hint(2): the Power module has a lemma for the power of a sum and one for
  //    positivity; the Mul module orders products.

  lemma ShiftBoundCheck(x: nat, n: nat)
    requires x < Pow(n)
  {
    // Uncomment as you go:
    // ShiftBound(x, n, 3);
    // assert x * Pow(3) < Pow(n + 3);
  }

  // item: Q04.H4d S4
  // uses: lemma-recursion
  // pair: Q04.H4v
  /** **H4.** `Cmp` (layer L3) agrees with the order of the values: it is -1,
      0 or 1, negative exactly when `ToNat(a) < ToNat(b)`, and 0 exactly when
      the values are equal. Prove it by recursion along `Cmp`'s own recursion
      (`decreases |a| + |b|` ships). Once the call on the tails tells you how
      the tails' values compare, what do you know about the whole values? */
  lemma CmpCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures -1 <= Cmp(a, b) <= 1
            && (Cmp(a, b) < 0 <==> ToNat(a) < ToNat(b))
            && (Cmp(a, b) == 0 <==> ToNat(a) == ToNat(b))
    decreases |a| + |b|
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint(1): the recursive call needs valid tails, and the comparison needs
  //    heads below `BASE`: one L2 lemma gives both, once per sequence.
  // Hint(2): write each value as its head plus `BASE` times its tail's value
  //    (an L2 lemma, once per sequence).

  lemma CmpCorrectCheck(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b) && ToNat(a) < ToNat(b)
  {
    // Uncomment as you go:
    // CmpCorrect(a, b);
    // assert Cmp(a, b) == -1;
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
