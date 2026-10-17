/*!
# Q04 — Proof craft, loops and libraries (Reference Solution)

Hole-free reference for `dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live, and every verdict switch is enabled; the verdict
answers are in `Solutions/slots/Q04.slots`, their hashes in
`expected/Q04.pins`.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned: the count pins in
`expected/Q04.counts`, the statement freeze in `expected/Q04.freeze`, the
WRITE-card failure demos by their in-file `// EXPECT` lines, and the
false-friends demos by their sidecars under `expected/specimens/Q04/`.
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
  // CHECK P1dv

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
  // CHECK P3dv

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
  // CHECK P8dv

  // ===========================================================================
  // Test-out (closed book, before any reading, after the prediction block)
  // ===========================================================================

  // item: Q04.T1d S4
  // uses: lemma-recursion, forall
  // pair: Q04.T1v
  /** **T1.** (test-out) A value of zero means zero limbs: if `ToNat(s) == 0`,
      every limb of `s` is 0.

      Reference: induction on `s`, by a call on `s[1..]`. `ToNat(s) == 0`
      forces `s[0] == 0` and `ToNat(s[1..]) == 0` (a sum of two naturals is 0
      only when both are, and `BASE * t == 0` only when `t == 0`), so the call
      applies; the `forall` statement then covers index 0 from the first fact
      and every other index `i` from the call, through
      `s[i] == s[1..][i - 1]`. */
  lemma ZeroValueZeroLimbs(s: seq<nat>)
    requires ToNat(s) == 0
    ensures forall i | 0 <= i < |s| :: s[i] == 0
    decreases |s|
  {
    if |s| > 0 {
      ZeroValueZeroLimbs(s[1..]);
      forall i | 0 <= i < |s|
        ensures s[i] == 0
      {
        if i > 0 {
          assert s[i] == s[1..][i - 1];
        }
      }
    }
  }

  lemma ZeroValueZeroLimbsCheck(s: seq<nat>)
    requires |s| == 2 && ToNat(s) == 0
  {
    ZeroValueZeroLimbs(s);
    assert s[1] == 0;
    ZeroValueZeroLimbs([]);
    ZeroValueZeroLimbs([0, 0, 0]);
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
  /** **H1.** Powers add.

      Reference: recursion on `m`. For `m > 0` the chain unfolds `Pow(m + n)`
      once (`m + n > 0`), uses the call on `m - 1` for the inner power, then
      reassociates `BASE * (Pow(m - 1) * Pow(n))` and folds `BASE * Pow(m - 1)`
      back into `Pow(m)`. For `m == 0` both sides are `Pow(n)`. */
  lemma PowAdd(m: nat, n: nat)
    ensures Pow(m + n) == Pow(m) * Pow(n)
    decreases m
  {
    if m > 0 {
      calc {
        Pow(m + n);
      ==
        BASE * Pow(m - 1 + n);
      == { PowAdd(m - 1, n); }
        BASE * (Pow(m - 1) * Pow(n));
      ==
        (BASE * Pow(m - 1)) * Pow(n);
      ==
        Pow(m) * Pow(n);
      }
    }
  }

  lemma PowAddCheck(m: nat)
  {
    PowAdd(m, 2);
    assert Pow(m + 2) == Pow(m) * Pow(2);
    PowAdd(0, m);
    assert Pow(m) == Pow(0) * Pow(m);
  }

  // item: Q04.H2d S2
  // uses: forall
  /** **H2.** Every prefix of valid limbs is below its power.

      Reference: one `forall` statement over `k`; each instance is L2's
      `ToNatBound` on the prefix `s[..k]`, whose limbs are valid because they
      are limbs of `s`, and whose length is `k`. */
  lemma PrefixBounds(s: seq<nat>)
    requires Valid(s)
    ensures forall k | 0 <= k <= |s| :: ToNat(s[..k]) < Pow(k)
  {
    forall k | 0 <= k <= |s|
      ensures ToNat(s[..k]) < Pow(k)
    {
      ToNatBound(s[..k]);
    }
  }

  lemma PrefixBoundsCheck(s: seq<nat>, k: nat)
    requires Valid(s) && k <= |s|
  {
    PrefixBounds(s);
    assert ToNat(s[..k]) < Pow(k);
    PrefixBounds([]);
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
// — clearly marked: everything below answers the agentic file —
// =============================================================================
// The reference delivery of dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy (and of
// its Verus twin) is that file's own twin, Solutions/dafny/Q/Q04_ProofCraft/agent/
// Q04_AgentRetriever.dfy (Solutions/verus/q/q04_proof_craft/src/agent.rs): the three
// goals closed by library calls, each call with its `// found-by:` receipt, and the
// author's note on the soft spots a contractor tends to hit, in a closing section under
// this same heading. They live there, beside the statements they answer, so one copy is
// verified and kept.
