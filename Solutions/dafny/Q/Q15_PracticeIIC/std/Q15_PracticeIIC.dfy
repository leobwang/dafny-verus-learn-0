/*!
# Q15 — Practice II-C (Reference Solution)

Hole-free reference for `dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live, and every verdict switch is enabled; the verdict
answers are in `Solutions/slots/Q15.slots`, their hashes in
`expected/Q15.pins`. Each item uses at most the one lemma of its own the tier
allows, in its `HELPERS` area (H2's proof needs none); H2's refutation sits
under REFUTATIONS. The
`cfree:` lines are the construct-free answers the author measured.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line.
*/
module Q15_PracticeIIC {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat

  // ===========================================================================
  // The prediction block. Commit every prediction of this module before you
  // read past this block, and record the first tries:
  //     scripts/firsttry.sh Q15 --check
  // The verdict answers go in slots/Q15.slots. The Verus crate has no
  // prediction block of its own.
  // ===========================================================================

  // item: Q15.P1d S9 verdict
  /** **P1.** The language server and a hole. A Dafny file holds one module
      with two lemmas, in this order:

          lemma DoubleGrows(x: nat)
            ensures x <= 2 * x
          {
          }

          lemma DoubleMono(x: nat, y: nat)
            requires x <= y
            ensures 2 * x <= 2 * y

      The first is proved; the second has no body. Your client
      (harness/q/fvh_q/lsp_client.py, H6-H8) opens it with the pinned
      `dafny server` and returns the per-symbol verification statuses the
      server publishes once the file's verification has ended. What does it
      report for the two lemmas? Answer form: `<first> <second>`, each one
      of `correct`, `error`, `queued`, `running`, `stale` (the status names
      of lsp_client.py's STATUS_NAMES) or `absent` (the lemma has no status
      in the report). */
  // CHECK P1d

  // item: Q15.P6dv S11 verdict
  /** **P6.** Trigger battery, goal G01 (tools/Q15/battery/dafny/G01.dfy and
      tools/Q15/battery/verus/G01.rs, each a whole file that stands alone):
      run as shipped with `scripts/vcheck <file>`, what does each form give?
      Answer form: `D:<v> V:<v>`, each v one of `ok` (the summary says
      verified), `fail` (failed, with no stage named before verification),
      `timeout` (inconclusive, or out of resource), `err:<stage>` (failed at
      a stage before verification: the stage the summary names) or `err`
      (the summary's verdict is `error`). */
  // CHECK P6dv

  // item: Q15.P7dv S11 verdict
  /** **P7.** Trigger battery, goal G02 (tools/Q15/battery/dafny/G02.dfy and
      verus/G02.rs), as shipped. Answer form as P6's. */
  // CHECK P7dv

  // item: Q15.P8dv S11 verdict
  /** **P8.** Trigger battery, goal G03 (tools/Q15/battery/dafny/G03.dfy and
      verus/G03.rs), as shipped. Answer form as P6's. */
  // CHECK P8dv

  // item: Q15.P9dv S11 verdict
  /** **P9.** Trigger battery, goal G07 (tools/Q15/battery/dafny/G07.dfy and
      verus/G07.rs), as shipped. Answer form as P6's. */
  // CHECK P9dv

  // item: Q15.P10dv S11 verdict
  /** **P10.** Trigger battery, goal G09 (tools/Q15/battery/dafny/G09.dfy and
      verus/G09.rs), as shipped. Answer form as P6's. */
  // CHECK P10dv

  // item: Q15.P11dv S11 verdict
  /** **P11.** Trigger battery, goal G10 (tools/Q15/battery/dafny/G10.dfy and
      verus/G10.rs), as shipped. Answer form as P6's. */
  // CHECK P11dv

  // ===========================================================================
  // Holes
  // ===========================================================================

  // HELPERS (Q15.H1d): at most one lemma of your own, here.

  // item: Q15.H1d S11
  // uses: trigger-rewrite
  // pair: Q15.H1v
  // form: trigger, stable
  // cfree: { assert Pow(n + 3) == BASE * Pow(n + 2); }
  // cfree: { assert Pow(n + 3) == BASE * Pow(n + 2); assert Pow(n + 2) == BASE * Pow(n + 1); assert Pow(n + 1) == BASE * Pow(n); }
  /** **H1.** Stability. Three places up the powers of BASE. This attempt
      gives the proof one quantified step, whose trigger is the plain power
      term:

          {
            forall k: nat {:trigger Pow(k)} ensures Pow(k + 1) == BASE * Pow(k) {
            }
          }

      Paste it as the body and run `scripts/vcheck --brittleness --solvers
      dafny/Q/Q15_PracticeIIC/std`; fill the BRITTLENESS table below from what
      the sweep prints. Then prove the lemma with a quantified step whose
      trigger no instance of the step creates. The proof must be stable
      under the same sweep and carry no resource attribute. Which terms must
      the proof hold for your trigger to fire? */
  lemma PowThreeUp(n: nat)
    ensures Pow(n + 3) == BASE * BASE * BASE * Pow(n)
  {
    forall k: nat {:trigger Pow(k + 1)} ensures Pow(k + 1) == BASE * Pow(k) {
    }
    var m1, m2 := n + 1, n + 2;
    assert Pow(m2 + 1) == BASE * Pow(m2);
    assert Pow(m1 + 1) == BASE * Pow(m1);
    assert Pow(n + 1) == BASE * Pow(n);
  }

  // BRITTLENESS (learner-owned): the attempt, then your proof, from the sweep.
  //   row (solver, seed)   attempt: verdict, resource count   yours: verdict, resource count
  //   4.12.1 seed 1
  //   4.12.1 seed 2
  //   4.12.1 seed 3
  //   4.14.1 seed 1
  //   4.14.1 seed 2
  //   4.14.1 seed 3

  // HELPERS (Q15.H2d): at most one lemma of your own, here.

  // item: Q15.H2d S12
  // uses: witness, lemma-call
  // pair: Q15.H2v
  /** **H2.** Refute, repair, prove. The lemma below ships false. First,
      under REFUTATIONS, write a lemma `CmpTopRefuted` (no parameters) whose
      `ensures` says, on concrete sequences you choose, that `CmpTop`'s
      `requires` holds and its `ensures` does not; prove it. Then repair
      `CmpTop` with the smallest change that makes it true: add `requires`
      clauses only (its shipped clauses stay as they are), so that the given
      client `CmpTopCheck` verifies with its use-site check uncommented.
      Then prove it. Which hypothesis of the counterexample is the one the
      claim silently assumed? */
  lemma CmpTop(a: seq<nat>, b: seq<nat>)
    requires |a| == |b| && |a| > 0 && a[|a| - 1] < b[|b| - 1]
    requires Valid(a)
    ensures ToNat(a) < ToNat(b)
  {
    if |a| > 1 {
      CmpTop(a[1..], b[1..]);
    }
  }

  // REFUTATIONS (Q15.H2d): your `CmpTopRefuted`, here.

  // reference-only: the refutation the item asks for
  lemma CmpTopRefuted()
    ensures var a, b := [2 * BASE, 0], [0, 1];
            |a| == |b| && |a| > 0 && a[|a| - 1] < b[|b| - 1] && ToNat(b) < ToNat(a)
  {
  }

  method CmpTopCheck(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b) && |a| == |b| && |a| > 0 && a[|a| - 1] < b[|b| - 1]
  {
    CmpTop(a, b);
    assert ToNat(a) < ToNat(b);
    CmpTopRefuted();
  }
}

