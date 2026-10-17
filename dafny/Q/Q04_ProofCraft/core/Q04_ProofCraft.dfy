/*!
# Q04 — Proof craft, loops and libraries (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) and L2
(`QG_L2_BigNat`), and nothing else: no earlier exercise file and no standard
library (this file's unit does not switch it on). Layer L3 and the standard
library enter in the library file, dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy,
which you work after this one. The layers are frozen and complete; read them,
never edit them.

How to work this file (the moderate tier puts the predictions first):
1. Predictions first: fill every slot of the prediction block below (the
   verdict answers go in slots/Q04.slots), of the Verus file's prediction
   block (verus/q/q04_proof_craft/src/lib.rs), of specimens/Q04/P*.specimen
   and of dafny/checks/Q04_checks.dfy, then record the first tries with
   `scripts/firsttry.sh Q04 --check`, before you run anything they are about.
2. Then the test-out, closed book: T1 (below) and the Verus file's T1, before
   any reading, without their hints. Run `scripts/firsttry.sh Q04 --check`
   again, which records your first try (it runs T1's commented checks in a
   scratch copy, and refuses while a Q04 prediction is unrecorded), and only
   then uncomment those checks. If both T1 pass on that first try, you may
   skip the chapter section on lemma recursion.
3. Replace each hole, then uncomment the checks beneath it.
4. Done = `scripts/vcheck --gate dafny/Q/Q04_ProofCraft/core` prints only
   the summary line and exits 0, `scripts/vaudit dafny/Q/Q04_ProofCraft/core`
   reports no finding, the same two hold for dafny/Q/Q04_ProofCraft/std,
   AND `scripts/firsttry.sh Q04 --report --strict` exits 0.
5. Stuck for 20 minutes? /tutor Q04.

This file ships with exactly 3 holes: T1 (test-out), H1 and H2, each counted
by `scripts/vcheck`. Q04 as a whole ships 11 holes: Dafny 5 (3 here, 2 in the
library file) and Verus 6 (src/lib.rs 2, src/library.rs 4), of which 2 are
test-out items (T1 in each language); 9 predictions (5 verdicts, 3 obligation
specimens, 1 value slot); and 4 exit items (the exit files ship 2 + 2 holes).
Commit every prediction BEFORE you run anything it is about, open later files,
or read CI, the registry or the plan: their checks and headers give some
predictions away.

Item kinds: P prediction (a slot) · T test-out (closed book, after the
predictions) · W worked example (given, finished) · C card (WRITE: a success
here and a failure demo in specimens/Q04/; RECOGNISE; false friends and
divergence, in the final sections) · H one-hole item · X exit item (the exit
files) · A agent run. Slots: a verdict switch `// SLOT: CHECK <item>` here
takes its answer in slots/Q04.slots (`P1dv = ???` → `P1dv = "<answer>"`); a
value or obligation slot is the `// SLOT:` line itself. Fill a slot, record
the first try, and only then enable it: `// SLOT: CHECK P1dv` becomes
`// CHECK P1dv`, `// SLOT: FAILS …` becomes `// FAILS …`, and a value slot
`// SLOT: <check>` becomes the live check.

The library and the toolchain lab: the library file's TOOLCHAIN LAB block, by
hand in your own terminal.

Exit (closed book): dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy and
verus/q/q04_proof_craft/src/exit.rs, scored once by
`scripts/firsttry.sh Q04 --exit` (threshold: 3 of the 4, at least 1 in each
language).

The agentic exercise (rung 4: the retriever race, `/contract Q04`) is at the
bottom of this file.
*/
module Q04_ProofCraft {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // ===========================================================================
  // The prediction block. Commit every prediction of this module before you
  // read past this block, and record the first tries:
  //     scripts/firsttry.sh Q04 --check
  // Verdict answers go in slots/Q04.slots; the other predictions live in
  // specimens/Q04/ (P4, P5, P9) and dafny/checks/Q04_checks.dfy (P2). The
  // Verus file's prediction block (verus/q/q04_proof_craft/src/lib.rs) holds
  // P6 and P7.
  // Verdict vocabulary for `D:<v> V:<v>` answers: `ok` (verifies), `fail` (a
  // verification error), `timeout` (out of resource or time), `err:<stage>`
  // (refused before verification; <stage> as scripts/vcheck prints it:
  // `parse` or `resolve`).
  // ===========================================================================

  // item: Q04.P1dv S1 verdict
  /** **P1.** Splitting a limb sum into a low limb and a carry. Each file
      holds one routine that splits the sum of two limbs:

        Dafny:
          method SplitSum(a: nat, b: nat) returns (lo: nat, hi: nat)
            requires a < BASE && b < BASE
            ensures lo + hi * BASE == a + b
          {
            var s := a + b;
            lo := s % BASE;
            hi := s / BASE;
          }

        Verus:
          fn split_sum(a: u64, b: u64) -> (r: (u64, u64))
              ensures
                  r.0 + r.1 * BASE == a + b,
          {
              let s: u128 = a as u128 + b as u128;
              (s as u64, (s >> 64) as u64)
          }

      Each sits in a module (Dafny) or a `verus!` block (Verus) of a file of
      its own that imports layer L1, and is checked with
      `scripts/vcheck --module Q04 <file>`. What does each check report?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P1dv

  // item: Q04.P3dv S3 verdict
  /** **P3.** A chain of false steps. Each file holds one chain from `x + 1`
      to `x + 4` in steps of one, every step an `==` that is false:

        Dafny:
          lemma Chain(x: int)
          {
            calc {
              x + 1;
            ==
              x + 2;
            ==
              x + 3;
            ==
              x + 4;
            }
          }

        Verus (with `use vstd::calc;`):
          proof fn chain(x: int) {
              calc! {
                  (==)
                  x + 1; {}
                  x + 2; {}
                  x + 3; {}
                  x + 4;
              }
          }

      Each file is checked alone, in a scratch directory, with
      `scripts/vcheck <file>`. How many errors does each report, and does
      the first error it reports name a line of the chain (a line of your
      file between the chain's opening and its closing brace)?
      Answer form: `D:<n> <yes|no> V:<n> <yes|no>`, each <n> a numeral. */
  // SLOT: CHECK P3dv

  // item: Q04.P8dv S5 verdict
  /** **P8.** Two names for one thing. Each file is checked with
      `scripts/vcheck --module Q04 <file>`:

        Dafny:
          module UsePowD {
            import opened QG_L1_BigNat
            import opened Std.Arithmetic.Power

            lemma UsePow()
              ensures Pow(1) == BASE
            {
            }
          }

        Verus:
          use vstd::prelude::*;
          use vstd::arithmetic::power::*;
          use qg_bignat_l3::*;

          verus! {

          pub open spec fn pow(b: int, e: nat) -> int {
              b + e
          }

          proof fn use_pow()
              ensures
                  pow(2, 3) == 5,
          {
          }

          } // verus!

      What does each check report?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P8dv

  // ===========================================================================
  // Test-out (closed book, before any reading, after the prediction block)
  // ===========================================================================

  // item: Q04.T1d S4
  // uses: lemma-recursion, forall
  // pair: Q04.T1v
  /** **T1.** (test-out) A value of zero means zero limbs: if `ToNat(s) == 0`,
      every limb of `s` is 0. Prove it by recursion on `s` (`decreases |s|`
      ships). What does `ToNat(s) == 0` tell you about `s[0]` and about the
      rest of the limbs, and how does a fact about `s[1..]` reach index `i` of
      `s`? */
  lemma ZeroValueZeroLimbs(s: seq<nat>)
    requires ToNat(s) == 0
    ensures forall i | 0 <= i < |s| :: s[i] == 0
    decreases |s|
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint(1): call the lemma on `s[1..]`, then prove the `forall` with a
  //    `forall` statement.
  // Hint(2): limb `i > 0` of `s` is limb `i - 1` of `s[1..]`: say so in an
  //    `assert`.

  lemma ZeroValueZeroLimbsCheck(s: seq<nat>)
    requires |s| == 2 && ToNat(s) == 0
  {
    // Uncomment as you go:
    // ZeroValueZeroLimbs(s);
    // assert s[1] == 0;
  }

  // ===========================================================================
  // Worked example
  // ===========================================================================

  // item: Q04.W1d S3
  /** **W1.** A `calc` chain: `Pow(n + 1)` is `Pow(n) * BASE`. Each line of a
      chain is an expression, each relation between two lines is one proof
      step, checked on its own, and a hint in braces after a relation serves
      that one step only. */
  lemma PowSucc(n: nat)
    ensures Pow(n + 1) == Pow(n) * BASE
  {
    calc {
      Pow(n + 1);
    ==  // the definition of Pow, at an argument above 0
      BASE * Pow(n + 1 - 1);
    ==  { assert n + 1 - 1 == n; }
      BASE * Pow(n);
    ==  // multiplication commutes
      Pow(n) * BASE;
    }
  }

  // ===========================================================================
  // WRITE cards (each: a success here, a pinned failure demo in specimens/Q04/)
  // ===========================================================================

  // item: Q04.C1d S3 write:calc
  /** ### C1 — card: `calc` chains.
      Jurisdiction: an equality (or `<=`, `<`) that takes several small steps;
      each step is checked on its own, and its hint serves that step only.
      Success: `ToNatTwoSteps` unfolds `ToNat` twice. Failure:
      specimens/Q04/card-c1d.dfy.specimen (a chain with one false step). */
  lemma ToNatTwoSteps(s: seq<nat>)
    requires |s| >= 2
    ensures ToNat(s) == s[0] + BASE * (s[1] + BASE * ToNat(s[2..]))
  {
    calc {
      ToNat(s);
    ==
      s[0] + BASE * ToNat(s[1..]);
    ==  { assert s[1..][1..] == s[2..]; }
      s[0] + BASE * (s[1] + BASE * ToNat(s[2..]));
    }
  }

  // item: Q04.C2d S2 write:forall
  /** ### C2 — card: the `forall` statement.
      Jurisdiction: a quantified goal whose instances each need a step of
      their own; the statement names the bound variable and its range, states
      what holds for it, and its body proves one instance. Success:
      `AppendZeroEach` calls L1's worked lemma once per sequence. Failure:
      specimens/Q04/card-c2d.dfy.specimen (the same, without the call). */
  lemma AppendZeroEach(ss: seq<seq<nat>>)
    ensures forall j | 0 <= j < |ss| :: ToNat(ss[j] + [0]) == ToNat(ss[j])
  {
    forall j | 0 <= j < |ss|
      ensures ToNat(ss[j] + [0]) == ToNat(ss[j])
    {
      ToNatAppendZero(ss[j]);
    }
  }

  // item: Q04.C3d S4 write:lemma-recursion
  /** ### C3 — card: a lemma that calls itself (induction by hand).
      Jurisdiction: a fact about a recursive definition, proved by calling the
      same lemma on the smaller argument the definition recurses on; its
      `decreases` says why the calls end. This unit leaves induction to you,
      so the call is the induction. Success: `FromNatShort`. Failure:
      specimens/Q04/card-c3d.dfy.specimen (the same lemma without its call). */
  lemma FromNatShort(n: nat)
    ensures |FromNat(n)| <= n
    decreases n
  {
    if n > 0 {
      FromNatShort(n / BASE);
    }
  }

  // ===========================================================================
  // RECOGNISE card
  // ===========================================================================

  // item: Q04.C7d S4 recognise:induction-auto
  /** ### C7 — card: `{:induction}` (recognise).
      `lemma {:induction n} L(n: nat) …` asks Dafny to attempt induction on
      `n` for that one lemma, in a unit that otherwise leaves induction to
      you, as this one does; `lemma {:induction false} L(…) …` switches the
      attempt off for one lemma in a unit that has it on. You will read it in
      other code. In this course you write the recursive call yourself (C3). */

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q04.H1d S4
  // uses: calc, lemma-recursion
  // pair: Q04.H1v
  /** **H1.** Powers add: `Pow(m + n) == Pow(m) * Pow(n)`. Method clause: a
      recursive call and a `calc` chain. On which argument does the lemma
      recurse, and which step of the chain needs the call? */
  lemma PowAdd(m: nat, n: nat)
    ensures Pow(m + n) == Pow(m) * Pow(n)
    decreases m
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint(1): for `m > 0`, unfold `Pow(m + n)` once, as W1 unfolds `Pow(n + 1)`.
  // Hint(2): the chain goes from `Pow(m + n)` through `BASE * Pow(m - 1 + n)`;
  //    the call on `m - 1` serves the next step, and the last steps regroup
  //    the product.

  lemma PowAddCheck(m: nat)
  {
    // Uncomment as you go:
    // PowAdd(m, 2);
    // assert Pow(m + 2) == Pow(m) * Pow(2);
  }

  // item: Q04.H2d S2
  // uses: forall
  /** **H2.** Every prefix of valid limbs is below its power: for each `k` up
      to `|s|`, `ToNat(s[..k]) < Pow(k)`. Method clause: one `forall`
      statement. Which given lemma bounds the value of one sequence, and what
      does it need of the prefix? */
  lemma PrefixBounds(s: seq<nat>)
    requires Valid(s)
    ensures forall k | 0 <= k <= |s| :: ToNat(s[..k]) < Pow(k)
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
  // Hint(1): a prefix of valid limbs is valid limbs of length `k`.
  // Hint(2): layer L2 bounds the value of valid limbs by the power of their
  //    length.

  lemma PrefixBoundsCheck(s: seq<nat>, k: nat)
    requires Valid(s) && k <= |s|
  {
    // Uncomment as you go:
    // PrefixBounds(s);
    // assert ToNat(s[..k]) < Pow(k);
  }

  // ===========================================================================
  // Final section: false friends. Record every prediction of this module
  // (scripts/firsttry.sh Q04 --check) before you read on or open its demos.
  // ===========================================================================

  // item: Q04.C8dv S3 diverge:q04-c8
  /** ### C8 — false-friends card, refreshed: four constructs that look alike
      in the two languages and do not work alike. One demo pair per row, in
      specimens/Q04/:
        row 1, `calc`: card-c8dv-1-d.dfy.specimen and card-c8dv-1-v.rs.specimen
        row 2, `forall`: card-c8dv-2-d.dfy.specimen and card-c8dv-2-v.rs.specimen
        row 3, lemma recursion: card-c8dv-3-d.dfy.specimen and
               card-c8dv-3-v.rs.specimen
        row 4, bringing in a library: card-c8dv-4-d.dfy.specimen and
               card-c8dv-4-v.rs.specimen
      Run each with `scripts/vcheck` and compare the two columns of a row. The
      chapter explains each difference. */
}

// =============================================================================
// ## Exercise (AGENTIC) — the retriever race (`/contract Q04`, rung 4)
// =============================================================================
// Files: dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy and
// verus/q/q04_proof_craft/src/agent.rs. Shipped state: green with holes, 3 tool-counted
// holes each: three goals whose proofs are short chains of standard-library lemma calls.
// The audit of each file shows one row per open goal. Check commands (the files' own
// headers give the exact shipped output):
//
//     scripts/vcheck dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy
//     scripts/vaudit dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy
//
// Steps (after this file and the library file are done):
// 1. Before the run: take each goal of both files through your own search ladder (IDE
//    hover and go-to-definition, a scoped grep of the pinned library source, the library's
//    documentation, a model, memory), timing it, and fill each file's SEARCH LOG block.
// 2. In a FRESH session, run /contract Q04 (one file per run: the Dafny file, then the
//    Verus file): the first live run of your contract v0.
// 3. Check the artifact yourself: the gate output, `git diff` (the three bodies only), the
//    `// found-by:` lines, `scripts/vaudit`.
// 4. Fill each file's COMPARISON block from the transcript.
// The lesson: the audit cannot see a method clause. A proof that is correct, green and
// audit-clean can still break the contract; the diff and the transcript show it.

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 45 · worked 30 · cards 8 · predicts 22 ·
  holes 54 · library + mismatch lab 20 · agent 15 · paper 15 · exit 22 ·
  calib 5 · total 251
*/
