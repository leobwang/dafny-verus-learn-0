/*!
# Q15 — Practice II-C (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) to L6
(`QG_L6_BigNat`), all opened; nothing else: no earlier exercise file. The
layers are frozen and complete; read them, never edit them. Nonlinear
arithmetic is on in this module.

How to work this file (the intermediate practice tier):
1. Predictions first: fill every slot of the prediction block below (the
   answers go in slots/Q15.slots), and the four forensic specimens' slots
   (specimens/Q15/), then record the first tries with
   `scripts/firsttry.sh Q15 --check`, before you run anything they are
   about. P1 is about the language server; P6-P11 are about the trigger
   battery under tools/Q15/battery/: read those goals, do not run them yet.
2. Each item ships its statement and nothing else: no skeleton. Each item
   allows at most one lemma of your own: write it in the item's `HELPERS`
   area, above the item, with a statement of your own and its proof.
3. Done = `scripts/vcheck --gate dafny/Q/Q15_PracticeIIC/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q15_PracticeIIC/std`
   reports no finding, `scripts/vcheck --brittleness --solvers
   dafny/Q/Q15_PracticeIIC/std` ends with `stable`, AND
   `scripts/firsttry.sh Q15 --report --strict` exits 0.
4. Stuck for 20 minutes? /tutor Q15.

This file ships with exactly 2 holes (H1 and H2), each counted by
`scripts/vcheck`. The unit's other file, Q15_Lab2Specs.dfy, ships 3 (Lab 2's
prose specifications). Q15 as a whole ships 17 holes (Dafny 5, Verus 5 in
verus/q/q15_practice_iic/, Python 7 in harness/q/fvh_q/lsp_client.py and
oracles.py); 11 predictions (7 in the block below, 4 in the specimens); and
1 exit item (the Dafny exit file ships 1 hole; the Verus exit file ships
none). Commit every prediction BEFORE you run anything it is about, open
later files, or read CI, the registry or the plan: their checks and headers
give some predictions away.

Item kinds: P prediction (a slot) · H one-hole item · X exit item (the exit
files) · A agent item (the agent files, tools/Q15/toolsmith.py, Lab 2's
runs). Slots: a verdict switch `// SLOT: CHECK <item>` here or in a specimen
takes its answer in slots/Q15.slots (`P1d = ???` → `P1d = "<answer>"`).
Fill the slot, record the first try, and only then enable it:
`// SLOT: CHECK P1d` becomes `// CHECK P1d`.

Exit (closed book, timed): dafny/Q/Q15_PracticeIIC/exit/Q15_Exit.dfy, scored
once by `scripts/firsttry.sh Q15 --exit` (threshold: the 1 item must pass).
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
  // SLOT: CHECK P1d

  // item: Q15.P6dv S11 verdict
  /** **P6.** Trigger battery, goal G01 (tools/Q15/battery/dafny/G01.dfy and
      tools/Q15/battery/verus/G01.rs, each a whole file that stands alone):
      run as shipped with `scripts/vcheck <file>`, what does each form give?
      Answer form: `D:<v> V:<v>`, each v one of `ok` (the summary says
      verified), `fail` (failed, with no stage named before verification),
      `timeout` (inconclusive, or out of resource), `err:<stage>` (failed at
      a stage before verification: the stage the summary names) or `err`
      (the summary's verdict is `error`). */
  // SLOT: CHECK P6dv

  // item: Q15.P7dv S11 verdict
  /** **P7.** Trigger battery, goal G02 (tools/Q15/battery/dafny/G02.dfy and
      verus/G02.rs), as shipped. Answer form as P6's. */
  // SLOT: CHECK P7dv

  // item: Q15.P8dv S11 verdict
  /** **P8.** Trigger battery, goal G03 (tools/Q15/battery/dafny/G03.dfy and
      verus/G03.rs), as shipped. Answer form as P6's. */
  // SLOT: CHECK P8dv

  // item: Q15.P9dv S11 verdict
  /** **P9.** Trigger battery, goal G07 (tools/Q15/battery/dafny/G07.dfy and
      verus/G07.rs), as shipped. Answer form as P6's. */
  // SLOT: CHECK P9dv

  // item: Q15.P10dv S11 verdict
  /** **P10.** Trigger battery, goal G09 (tools/Q15/battery/dafny/G09.dfy and
      verus/G09.rs), as shipped. Answer form as P6's. */
  // SLOT: CHECK P10dv

  // item: Q15.P11dv S11 verdict
  /** **P11.** Trigger battery, goal G10 (tools/Q15/battery/dafny/G10.dfy and
      verus/G10.rs), as shipped. Answer form as P6's. */
  // SLOT: CHECK P11dv

  // ===========================================================================
  // Holes
  // ===========================================================================

  // HELPERS (Q15.H1d): at most one lemma of your own, here.

  // item: Q15.H1d S11
  // uses: trigger-rewrite
  // pair: Q15.H1v
  // form: trigger, stable
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
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
  // Hint: an instance of the step at k mentions Pow(k) and Pow(k + 1); with
  //    the trigger on the term the instance creates, every instance makes
  //    the next one.

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
    ensures ToNat(a) < ToNat(b)
  // HOLE: this lemma has no body; repair its requires, then write `{ … }`.
  // Hint: the top limb dominates only when no lower limb can carry into it.

  // REFUTATIONS (Q15.H2d): your `CmpTopRefuted`, here.

  method CmpTopCheck(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b) && |a| == |b| && |a| > 0 && a[|a| - 1] < b[|b| - 1]
  {
    // Uncomment as you go:
    // CmpTop(a, b);
    // assert ToNat(a) < ToNat(b);
    // CmpTopRefuted();
  }
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 15 · LSP client 30 · pipeline forensic 20 · trigger battery and
  stability 30 · refute, repair, prove 15 · toolsmith 20 · tutor red-team 15 ·
  exit 20 · Lab 2: prose specs 108 · pre-registration 40 · /grade-paper 10 ·
  oracles 75 · vericoding arm 20 · run setup 20 · analysis 60 · reward audit
  15 · bench audit 30 · --post 10 · cards 45 · task cards 20 · ledger and
  calibration 10 · total 628 (+ tier viva 30)
Then run `scripts/firsttry.sh Q15 --record`.
*/
