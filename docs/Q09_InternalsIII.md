# Q09 — Internals III: brittleness, forensics, gate core

Q07 gave you proof engineering and porting, Q08 refinement, permissions and a verified wp.
Q09 closes the detailed tier with family C, strands S9–S13, and asks when you may believe a
green run: of your own proof, when the seed or the solver changes; of a contractor's
deliveries, each green and each worthless in its own way; and of your own gate, written in
Python, solo. `/viva Q09` examines Q07, Q08 and Q09 together.
Three ideas do all the work:

1. **A verdict is a measurement under settings, and stable is a property you measure.** One
   file can verify under one bundled Z3 and run out of resource under the other. A proof
   becomes stable when you hand the solver steps it no longer has to search for.
2. **Green is a claim, and each instrument checks one part of it.** A hole, a trusted step,
   an unchecked region, a vacuous premise, a weak statement: each leaves the run green, and
   each needs a different instrument. A healthy delivery is accused of nothing.
3. **A gate decides from instruments, never from labels, and says what it cannot decide.**
   Where no supplied oracle decides a class, your gate prints a mechanical `PASS` with that
   class `UNKNOWN`; only the evaluator reads the labels.

---

## 0. How this module works, pretest, test-out

**Minutes: 295, plus the 30-minute tier viva.** Setup 5 · test-out 10 · reading 45 ·
worked examples and WRITE cards 20 · predictions 20 · repair pair 25 · forensics 40 · gate
core 40 · MDE on paper 10 · red team and contract v1 25 · `EVAL.md` v1 10 · paper 15 ·
exit and explain-back 25 · calibration 5.

**Setup.** Start one long-lived `/tutor Q09` session; Q06's `harness/.venv` still serves.

**Predictions, all fifteen, first**, the ten forensic deliveries included:

| items | where the answer goes |
|---|---|
| P1d, P2dv, P3dv (the main Dafny file's prediction block) | `slots/Q09.slots` |
| P4py, P5py (the gate core's prediction block) | `slots/Q09.slots` |
| P6d–P10d, P11v–P15v (the forensic deliveries, `specimens/Q09/`) | `slots/Q09.slots`, one species word each; each switch is in its specimen |

A delivery's species is named from reading it, before running anything on it. Record all
fifteen with `scripts/firsttry.sh Q09 --check`, then enable each slot. Until then keep the
README's *Predictions first* list closed (from Q09 on it holds `tests/corpus/` and
`harness/tests/q/fixtures/` too), with the Q09 bank and rubric, the exit files and the card
demos, which `scripts/vcheck` refuses until their prediction is recorded.

**Pretest, after the predictions, before reading.** T1 is a pair of test-out items,
`PowGrowsByBase` in `Q09_Triggers.dfy` and `lemma_weight_strict_mono` in `lib.rs`: a
recursion whose step is a quantified fact with a trigger you choose and write, stable, with
no resource attribute. Write both closed book, hints unread, and run
`scripts/firsttry.sh Q09 --check` again (it checks the `trigger` and `stable` forms, and
refuses while a prediction is unrecorded). **Skip rule:** if both pass on that first try,
skip §3.4; the C2 cards, the repair pair and the exit stay.

Each prediction reappears below in a box,

> **Predict (Pn) — commit in the file before reading on.**

and its answer comes only after the box, below the words *Commit your prediction first.*
The ten forensic boxes share one callout (§4.1); your instruments give their answers.

**Outputs.** Every output fence is a real run on the course pins (Dafny 4.11.0 with its two
bundled Z3 builds, 4.12.1 pinned and 4.14.1; Verus 0.2026.09.27.3cf1832), pinned in
`expected/Q09.chapter.toml`; §5's two `fvh.stats` runs are recorded quotes you can repeat.
`probe.*` and `p3.*` are scratch files run with `--module Q09` (the unit's options and the
given layers). Fences drop `raw output:` lines; JSON shows `[...]` for `cmd` and `...` for
`raw_dir`. Resource counts are live data: record your own.

### This module's files

| file | what it is |
|---|---|
| `dafny/given/Q/QG_L1_BigNat.dfy` to `QG_L4_BigNat.dfy`; `verus/given/qg_bignat_l1` to `qg_bignat_l4` | the given spine, frozen; W1 measures two of L4's proofs |
| `dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy` | the main Dafny exercise file: **1 hole** (H1d), the prediction block, W1d, C1d, C2d; nonlinear arithmetic on |
| `dafny/Q/Q09_InternalsIII/std/Q09_Triggers.dfy` | the trigger test-out, same unit, nonlinear arithmetic off for its module: **1 hole** (T1d) |
| `verus/q/q09_internals_iii/src/lib.rs` | the Verus exercise file: **2 holes** (T1v, H1v), W1v, C1v, C2v |
| `harness/q/fvh_q/gate/core.py` | the gate core, solo work (guard rule 2s): **4 holes** (H2py–H5py), counted on the syntax tree; P4py, P5py |
| `specimens/Q09/` | the ten forensic deliveries, two companions that open after their delivery's first try, the card demos |
| `research/q09_forensics.md`, `research/EVAL.md` | the `DIAGNOSIS` form (§4.1); `EVAL.md`'s `Q-v1` section (§7) |
| `dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy`, `verus/q/q09_internals_iii/src/agent.rs` | the red-teamed contractor: a bank of four lemmas each, green with **4 + 4 holes** (§10) |
| `dafny/Q/Q09_InternalsIII/exit/Q09_Exit.dfy`, `verus/q/q09_internals_iii/src/exit.rs` | the closed-book exit: **2 + 2 holes**, and the `EXPLAIN-BACK` block |
| `CLAUDE.md`, below the learner marker | contract v1, by hand (§10) |
| `paper/Q09_problems.tex`, `paper/Q09_answers.tex` | the written pair (§8) |
| `Solutions/` mirrors of these files | the reference: yours to open LAST |

---

## 1. S9 — Machine records and complete documents

A gate reads Q06's third door, `scripts/vcheck --json`, and must decide which fields of a
document have to hold before it counts as a pass. The document records the last stage a run
reached:

```mermaid
flowchart LR
  src["a candidate file"] --> parse["parse"]
  parse --> res["resolve and type-check"]
  res --> ver["verify: the solver's tasks"]
  ver --> doc["one --json document"]
  doc --> checks["json_complete: lang, stage, verdict, exit_code, holes, findings, verified_count (H2py)"]
  checks --> rec["a pass a gate may count"]
```

A document that stops early is no pass, and each field is its own check, because each can
fail while the others hold.

> **Predict (P3dv) — commit in the file before reading on.** A file with one proved lemma
> and one open hole (Dafny: a bodyless lemma; Verus: a `proof_note` assume), run through
> `scripts/vcheck --json` in each language: the `verdict` field, and whether `verified_count`
> is a number or `null`.

*Commit your prediction first.* `D:verified number V:verified null`. The two files,
verbatim from the block:

```dafny
module P3 {
  lemma Proved(x: nat)
    ensures x + 0 == x
  {
  }

  lemma Open(x: nat)
    ensures x * 1 == x
}
```

<!-- pin: p3dv-d -->
```
$ scripts/vcheck --module Q09 --json p3.dfy
{"cmd": [...], "count_unit": "tasks", "diagnostics": [{"code": "W-D01", "col": 19, "file": "p3.dfy", "line": 8, "message": "This ensures clause is part of a bodyless method. Add the {:axiom} attribute to it or the enclosing method to suppress this warning", "severity": "warning"}], "exit_code": 0, "findings": [], "holes": [{"col": 19, "file": "p3.dfy", "kind": "bodyless-method", "label": "P3.Open", "line": 8}], "lang": "dafny", "per_symbol": {"P3.Proved": "verified", "QG_L1_BigNat.BASE": "verified", "QG_L1_BigNat.Drop": "verified", "QG_L1_BigNat.Head": "verified", "QG_L1_BigNat.Pow": "verified", "QG_L1_BigNat.Tail": "verified", "QG_L1_BigNat.ToNat": "verified", "QG_L1_BigNat.ToNatAppendZero": "verified", "QG_L1_BigNat.Valid": "verified", "QG_L2_BigNat.AddLimb": "verified", "QG_L2_BigNat.Canonical": "verified", "QG_L2_BigNat.DropStep": "verified", "QG_L2_BigNat.FromNat": "verified", "QG_L2_BigNat.Normalize": "verified", "QG_L2_BigNat.ToNatBound": "verified", "QG_L2_BigNat.ToNatCons": "verified", "QG_L2_BigNat.ToNatHeadTail": "verified", "QG_L2_BigNat.ToNatSingleton": "verified", "QG_L2_BigNat.ValidCons": "verified", "QG_L2_BigNat.ValidTail": "verified"}, "raw_dir": "...", "stage": "verify", "target": "p3.dfy", "verdict": "verified", "verified_count": 23}
$ echo $?
0
```

```rust
use vstd::prelude::*;

verus! {

proof fn proved(x: nat)
    ensures
        x + 0 == x,
{
}

proof fn open_one(x: nat)
    ensures
        x * 1 == x,
{
    #[verifier::proof_note("P3")] assume(false);
}

} // verus!
```

<!-- pin: p3dv-v -->
```
$ scripts/vcheck --module Q09 --json p3.rs
{"cmd": [...], "count_unit": "verified", "diagnostics": [], "exit_code": 1, "findings": [], "holes": [{"col": 35, "file": "p3.rs", "kind": "assume", "label": "P3", "line": 15}], "lang": "verus", "per_symbol": {"open_one": "hole", "proved": "no-error"}, "raw_dir": "...", "stage": "verify", "target": "p3.rs", "verdict": "verified", "verified_count": null}
$ echo $?
0
```

Read them aloud: (1) both verdicts are `verified` and both runs exit 0, though each file
lists a hole under `holes`: the verdict says the verifier found no error, and done also
needs zero holes; (2) Dafny counts tasks, 23 here with the spine's; Verus reports `null`,
because under `--no-cheating` a hole stops it before it reports a count (its JSON has no
`verified` field, as Q03's gate message said); (3) Verus's own `exit_code` is 1 while the
verdict is `verified`, so a harness that reads the exit code alone calls this run a failure,
and one that reads the verdict alone calls it a pass. A run that stops earlier:

```dafny
module S9 {
  lemma Uses(x: nat)
    ensures x + 0 == x
  {
    Missing(x);
  }
}
```

<!-- pin: s9-resolve -->
```
$ scripts/vcheck --module Q09 --json probe.dfy
{"cmd": [...], "count_unit": "tasks", "diagnostics": [{"code": "", "col": 5, "file": "probe.dfy", "line": 5, "message": "unresolved identifier: Missing", "severity": "error"}, {"code": "", "col": 12, "file": "probe.dfy", "line": 5, "message": "expected method call, found expression", "severity": "error"}], "exit_code": 2, "findings": [], "holes": [], "lang": "dafny", "per_symbol": {}, "raw_dir": "...", "stage": "resolve", "target": "probe.dfy", "verdict": "failed", "verified_count": null}
$ echo $?
1
```

(1) `stage` is `resolve`: no task reached the solver; (2) the verdict is `failed` and
`verified_count` is `null` in Dafny too; (3) `holes` is empty because the hole counter never
ran. An empty `holes` list is evidence only in a document whose stage is `verify`.

H2py writes these checks as `json_complete(doc, lang)`: one reason per failing check, and
`[]` only for a document a gate may trust.

---

## 2. S10 — What sees a run: the editor's door

Q06 §2 made the trusted base an inventory; Q09's instruments turn it into checks (§4.1).
One door to the verifier is still missing from the course's list, the editor's. There the
verifier runs behind the Language Server Protocol: `dafny server` speaks it, with methods of
its own for per-symbol verification, gutter status and counterexamples; Verus's editor door
is verus-analyzer, a fork of rust-analyzer. That door is excellent for the learner loop and
useless as a grader: it verifies under whatever the project's options ask (Q06's P1 lesson),
keeps state between edits, and prints no document a third party can re-run. Q15 writes an
LSP client by hand. An editor's green tick is a hint, `scripts/vcheck` a measurement,
`scripts/vcheck --gate` the verdict.

---

## 3. S11 — Brittleness: seeds, solvers and triggers

A verifier's search depends on things outside your file: the seed, the Z3 build, the
pinned resource limit. A proof that fits only because the search was lucky is *brittle*.
This section measures brittleness, then repairs it two ways: by splitting a step the solver
must search for, and by moving a trigger so that a quantified fact stops feeding itself.

### 3.1 The sweep and the course's stability rule

`scripts/vcheck --brittleness` re-verifies a target under seeds 1, 2 and 3; in Dafny,
`--solvers` adds the second bundled Z3, for six rows. **A proof is stable when it verifies in
every row**: seeds 1–3 in Verus (which checks its Z3's version, so it has one solver), seeds
1–3 under both bundled solvers in Dafny. The resource spread (a symbol's coefficient of
variation under one solver) never gates; above 20 % it is flagged. W1 measures layer L4:

<!-- pin: w1d -->
```
$ scripts/vcheck --brittleness --solvers dafny/given/Q/QG_L4_BigNat.dfy
vcheck --brittleness: dafny/given/Q/QG_L4_BigNat.dfy [dafny]: 4.12.1 seed 1: verified · 4.12.1 seed 2: verified · 4.12.1 seed 3: verified · 4.14.1 seed 1: verified · 4.14.1 seed 2: verified · 4.14.1 seed 3: verified — stable
  resource counts: 96 symbol(s); widest spread QG_L1_BigNat.ToNatAppendZero 28782..39413 (CV 13.9%, solver 4.14.1); advisory, never gating
```

<!-- pin: w1v -->
```
$ scripts/vcheck --brittleness verus/given/qg_bignat_l4
vcheck --brittleness: verus/given/qg_bignat_l4 [verus]: seed 1: verified · seed 2: verified · seed 3: verified — stable
  resource counts: 12 symbol(s); widest spread qg_bignat_l4::lemma_add_lift 252242..354101 (CV 14.0%); advisory, never gating
```

Read them aloud: (1) every row is `verified`, so the layer is stable; (2) the second line
names the widest spread, and Verus's `lemma_add_lift` moves by more than a third between
seeds while its verdict holds; (3) "advisory, never gating": cost moves, the verdict is the
claim. Two solvers' counts are never mixed. `--json` adds `verdicts` (per row), `differs`
(each symbol whose verdict varies, with its `by_row`), `spread` (per symbol and solver) and
`flagged`; W1's blocks hold a `BRITTLENESS` table read off such a run, the form H1 fills.

`--solver` is a measurement and nothing else; the done gate keeps the pin:

<!-- pin: gate-solver-refused -->
```
$ scripts/vcheck --gate --solver 4.14.1 dafny/Q/Q09_InternalsIII/std
vcheck: refused: the done gate and the reference gate keep the pinned solver (Δ10): another bundled solver is a measurement (--solver S in the learner loop, or --brittleness with --solvers or --solver S; QPLAN §6 Q29)
$ echo $?
3
```

A candidate that verifies only under the other solver has shown that its proof depends on
the solver.

### 3.2 A solver swap

> **Predict (P1d) — commit in the file before reading on.** In this module's options
> (nonlinear arithmetic on), P1's attempt at `ProductBelowSquare` (its body names `Pow(n)`
> and asserts one comparison), verified at the pinned limit with the pinned Z3 and again
> with the other Z3 bundled with Dafny. What does each run give?

*Commit your prediction first.* `D:timeout ok`. The attempt, verbatim, in a module that
imports L1–L4 as the exercise module does:

```dafny
module P1 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  lemma ProductBelowSquare(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    assert x * y <= x * p;
  }
}
```

<!-- pin: p1d-pinned -->
```
$ scripts/vcheck --module Q09 probe.dfy
vcheck: probe.dfy [dafny, learner loop]: inconclusive — 122 verified, 0 holes, 1 error
probe.dfy:7:9: error: Verification out of resource (P1.ProductBelowSquare)
```

<!-- pin: p1d-other -->
```
$ scripts/vcheck --module Q09 --solver 4.14.1 probe.dfy
vcheck: probe.dfy [dafny, learner loop, solver 4.14.1]: verified — 123 verified, 0 holes, 0 errors
```

Read them aloud: (1) under the pin, the lemma is `inconclusive`, out of resource at its own
line; (2) under 4.14.1 the same file verifies; (3) neither the file nor the limit changed.
Neither run is the truth about the lemma: one search ran out, another found a proof within
the same budget. The attempt asserts one comparison and leaves the rest of the nonlinear
reasoning to the search, the kind of step whose cost moves with the solver. A grader that
accepts either run alone grades the solver, not the proof.

### 3.3 The repair: split the step

The cure for a step the solver must search for is to stop asking it to search. Card C1 shows
the move on a bound of three factors below `BASE`. Dafny's `ThreeLimbProduct` calls four
facts of `Std.Arithmetic.Mul`, each about one product; Verus's `lemma_three_limb_product`
makes two `nonlinear_arith` steps, each scoped by its own `requires`:

```rust
    assert(x * y < BASE * BASE) by (nonlinear_arith)
        requires
            x < BASE,
            y < BASE,
    ;
    assert(x * y * z < BASE * BASE * BASE) by (nonlinear_arith)
        requires
            x * y < BASE * BASE,
            z < BASE,
    ;
```

A `nonlinear_arith` step sees only its own `requires` and its goal, so each step is small
and closed. The failure demos leave the whole product to the solver, Dafny with an empty
body, Verus with one step and no `requires`:

<!-- pin: c1d -->
```
$ scripts/vcheck specimens/Q09/card-c1d.dfy.specimen
vcheck: specimens/Q09/card-c1d.dfy.specimen [dafny, learner loop]: failed — 1 verified, 0 holes, 1 error
specimens/Q09/card-c1d.dfy.specimen:15:3: error: a postcondition could not be proved on this return path
specimens/Q09/card-c1d.dfy.specimen:14:23: related: this is the postcondition that could not be proved
```

<!-- pin: c1v -->
```
$ scripts/vcheck specimens/Q09/card-c1v.rs.specimen
vcheck: specimens/Q09/card-c1v.rs.specimen [verus, learner loop]: failed — 1 verified, 0 holes, 1 error
specimens/Q09/card-c1v.rs.specimen:21:12: error: assertion failed
```

Measure both halves with `scripts/vcheck --json` and compare their resource counts: the
card's hand measurement comes before any repair. The repair pair runs this loop on P1's
lemma:

```mermaid
flowchart TD
  att["the quoted attempt, as the body"] --> sweep1["vcheck --brittleness (--solvers in Dafny)"]
  sweep1 --> table["BRITTLENESS table: verdict and count per row"]
  table --> split["split the step: named library facts, or scoped nonlinear steps"]
  split --> sweep2["the same sweep"]
  sweep2 -->|"a row fails"| split
  sweep2 -->|"every row verifies"| gate["vcheck --gate and firsttry --report --strict"]
```

The table comes first, filled from your own runs "whatever they show": you repair what you
measured, not what you expected.

H1d: the `BRITTLENESS` table from the attempt's sweep, then a proof that splits the
nonlinear step into named facts of `Std.Arithmetic.Mul` and verifies in all six rows, with no
resource attribute in its block (`form: stable`, checked by `scripts/firsttry.sh Q09
--report --strict`). H1v: the same table over seeds 1–3, then at least two `nonlinear_arith`
steps, each scoped by its own `requires` (`form: nl-steps:2, stable`). The `nl-steps` form
checks that the steps are present, not that each is needed; `/review-code` reads that.

### 3.4 Matching loops and trigger rewrites

Q06 §3.1 warned of the matching loop: an instance that creates a new term of its trigger's
shape, which fires again. Here it costs you a proof.

> **Predict (P2dv) — commit in the file before reading on.** Two attempts quoted in P2's
> block, each with a quantified step triggered on the plain power term: a Dafny proof of
> `PowGrowsByBase` in `Q09_Triggers.dfy`'s module options, and a Verus proof of
> `lemma_weight_strict_mono` in this crate. Each through `scripts/vcheck --brittleness`: the
> verdict under seeds 1, 2 and 3, and whether the first line ends `stable` or `NOT stable`.

*Commit your prediction first.* `D:timeout,timeout,timeout,unstable
V:timeout,timeout,timeout,unstable`. The Dafny attempt, verbatim, with the trigger file's
options:

```dafny
module {:disableNonlinearArithmetic} P2 {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  lemma PowGrowsByBase(m: nat, n: nat)
    requires m < n
    ensures Pow(m) * BASE <= Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k)} ensures Pow(k) * BASE <= Pow(k + 1) {
      PowAdd(k, 1);
    }
    if m + 1 < n {
      PowGrowsByBase(m + 1, n);
    }
  }
}
```

<!-- pin: p2dv-d -->
```
$ scripts/vcheck --module Q09 --brittleness probe.dfy
vcheck --brittleness: probe.dfy [dafny]: seed 1: inconclusive · seed 2: inconclusive · seed 3: inconclusive — NOT stable
  resource counts: 49 symbol(s); widest spread QG_L3_BigNat.FromNatCorrect 41897..48129 (CV 6.0%); advisory, never gating
```

The Verus attempt, verbatim, against the crate's dependencies:

```rust
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

pub proof fn lemma_weight_strict_mono(m: nat, n: nat)
    requires
        m < n,
    ensures
        weight(m) < weight(n),
    decreases n - m,
{
    assert forall|k: nat| #[trigger] weight(k) < weight(k + 1) by {
        lemma_weight_succ(k);
        lemma_weight_mono(0, k);
        lemma_weight_zero();
    }
    if m + 1 < n {
        lemma_weight_strict_mono(m + 1, n);
    }
}

} // verus!
```

<!-- pin: p2dv-v -->
```
$ scripts/vcheck --module Q09 --brittleness probe.rs
vcheck --brittleness: probe.rs [verus]: seed 1: inconclusive · seed 2: inconclusive · seed 3: inconclusive — NOT stable
  resource counts: 1 symbol(s); widest spread probe::lemma_weight_strict_mono 6000000..6000000 (CV 0.0%); advisory, never gating
```

Read them aloud: (1) every seed is `inconclusive`, so both lines end `NOT stable`; (2) the
Verus count is 6,000,000 on every seed, the whole budget the pin allows: the search did not
get unlucky, it never stopped; (3) the Dafny line names a layer lemma as the widest spread,
because the attempt stops at the limit on every seed. Neither tool says "matching loop";
an instance does: at `k` it mentions the function at `k` and at `k + 1`, and the second term
matches the trigger again:

```mermaid
flowchart LR
  goal["a term of the trigger's shape in the proof"] --> inst["instance at that argument"]
  inst --> newterm["the instance mentions the function one step up"]
  newterm -->|"matches the trigger again"| inst
  newterm --> budget["the resource limit: inconclusive, on every seed"]
```

Such a loop is not brittle by luck: it fails on every seed, because its search has no end.

The rewrite moves the trigger to a term the proof already holds and no instance creates.
Card C2 shows it on a function that is not a power: opaque `Zeros(n)`, with the step
`|Zeros(k + 1)| == |Zeros(k)| + 1`. The success halves trigger the step on `Zeros(k + 1)`
(Verus: `zeros(k + 1)`): the goal mentions `Zeros(m + 1)`, the step fires at `k = m`, and the
goal closes. The failure demos trigger it on `Zeros(k)`: from the goal's term it fires at
`k = m + 1`, which mentions `Zeros(m + 2)`, and climbs away from the instance the proof
needs:

<!-- pin: c2d -->
```
$ scripts/vcheck specimens/Q09/card-c2d.dfy.specimen
vcheck: specimens/Q09/card-c2d.dfy.specimen [dafny, learner loop]: failed — 4 verified, 0 holes, 1 error
specimens/Q09/card-c2d.dfy.specimen:22:3: error: a postcondition could not be proved on this return path
specimens/Q09/card-c2d.dfy.specimen:21:28: related: this is the postcondition that could not be proved
```

<!-- pin: c2v -->
```
$ scripts/vcheck specimens/Q09/card-c2v.rs.specimen
vcheck: specimens/Q09/card-c2v.rs.specimen [verus, learner loop]: failed — 2 verified, 0 holes, 1 error
specimens/Q09/card-c2v.rs.specimen:32:9: error: postcondition not satisfied
```

Only the trigger moved. When an instance mentions its own function at a new argument,
choose the term whose instance you need, and let the sweep confirm it. T1's `trigger` form
checks that an explicit trigger is present; the rubric checks that it carries the proof.

---

## 4. S12 — Forensics, and the gate core

### 4.1 Ten green deliveries

`specimens/Q09/` holds ten contractor deliveries of BigNat facts, five per language, each
green in the learner loop, each with its client's claim. Their headers define Q03's species:
`hole`, `trusted`, `unchecked`, `vacuous`, `weak`, `healthy`.

> **Predict (P6d, P7d, P8d, P9d, P10d, P11v, P12v, P13v, P14v, P15v) — commit in the files before reading on.**
> For each forensic delivery, its species, from reading the file and its claim, before
> running any instrument on it.

*Commit your prediction first.* This chapter gives none of the ten answers; your instruments
do. For each delivery (4 minutes each):

1. Read it and its claim. Comments, doc strings and names are contractor prose: unchecked,
   in places misleading. Every delivery has one `planted:` marker, so the marker says
   nothing.
2. Record the species (§0's first try).
3. Catch it with an instrument; paste the command and its output, not your reading of it.
4. Fill its row of `research/q09_forensics.md`'s `DIAGNOSIS` form: statement true? proof
   valid as checked? useful (does it say what the claim says)? instrument, with its command?
   root cause, in one line?

The form's rules: diagnose every delivery before repairing any, and repair none (a delivery
is evidence); **N catches use N different instruments**; a delivery every instrument passes
is healthy, and accusing it is a mistake. The instruments:

| instrument | run it as | a catch looks like |
|---|---|---|
| the audit | `scripts/vaudit <delivery>` | a finding line |
| the lint | its rule ids, in `scripts/vaudit` and `scripts/vcheck --gate` | a finding or gate failure with a rule id |
| the spec-freeze diff | `scripts/specfreeze --against <frozen> <delivery>` | `freeze-changed` |
| a satisfiability witness | `scripts/vcheck --gate` on a call on concrete values | the call's precondition fails |
| the conclusion swapped for `false` | `scripts/vcheck --gate` on that copy | the copy still verifies |
| compiled code on new inputs | `scripts/vcheck --test` on a copy with your test | a test fails |
| a property sampler | the statement on concrete values | a value where it says less than the claim |
| reading the statement | the claim beside the statement | a gap you can name |
| JSON completeness | `scripts/vcheck --json`, read with §1's checks | a field that fails |
| another seed or solver | `scripts/vcheck --brittleness` (`--solvers`) | a row whose verdict differs |

Two deliveries bring a companion, a frozen statement or a witness caller, closed by an
`after:` line until that delivery's first try. Save any copy you make (a swapped conclusion,
an added test) beside the deliveries, where the tools find the layers, and delete it once
its row is written. Some catches will not use the cheapest instrument; that is the
exercise.

### 4.2 The gate core: from results to a verdict

`harness/q/fvh_q/gate/core.py` is your first gate, gate v1: solo (no allowlist names it, no
assistant edits it; `/tutor Q09` coaches it), composing the frozen core only: `fvh.tools`,
`fvh.verdicts`, `fvh.corpus`, `fvh.stats`.

On a real delivery nobody knows its class, so `classify(results)` and
`gate(delivery, *, run=None)` see instrument results and the delivery's own files, and only
`corpus_report`, the evaluator, reads labels:

```mermaid
flowchart LR
  deliv["a Delivery: id, language, target, files"] --> pick["gate: the instruments its files call for"]
  pick --> runs["tools.run, one fresh process each"]
  runs --> res["instrument results"]
  res --> cls["classify (H3py)"]
  cls --> ver["GateVerdict: FAIL, or PASS with UNKNOWN classes"]
  ver --> rep["corpus_report (H5py)"]
  lab["the corpus labels"] --> rep
  rep --> nums["detections per class, held by UNKNOWN, false passes, false positives"]
```

A gate that read the labels earlier would pass its tests and fail on the first real
delivery. Three rules shape H3py and H4py:

- **A killed, timed-out or refused run is a `FAIL`.** A gate fails closed; an instrument that
  cannot run at all raises, never a pass.
- **A mechanical `PASS` names what it could not decide.** Some cheat classes need an oracle:
  X07 (vacuous hypotheses) a satisfiability witness, X08 (a weakened specification) a frozen
  statement, X14 (lookup-table overfitting) hidden tests the gate never has. They are
  `GRADER_ONLY` in `fvh.verdicts`. When every instrument passes, the verdict is `PASS` with
  the grader-only classes no supplied oracle decided in `unknown`, and `render` prints
  `PASS · UNKNOWN: X07, X08, X14`, never a bare `PASS`.
- **Every instrument runs through `fvh.tools.run`, looked up when the gate runs,** so a test
  can replace it with a recording stub. Which companions a delivery brings follows the
  corpus's public layout (`tests/corpus/README.md`), which `fvh.tools.command(instrument,
  target)` encodes: you may compose it rather than write the paths out. Whether the delivery
  brings them, and the verdict, are the gate's own work.

The frozen acceptance tests replay recorded results of the corpus's Q half, run `gate` under
neutral ids and paths, and require that a grader-only construct the instruments pass and a
healthy control get the same verdict: to the instruments they are indistinguishable, and an
honest gate says so. **The live check** is yours, outside the tests:
`cd harness && PYTHONPATH=q uv run python -m fvh_q.gate.core --half Q`, on the host, one
instrument at a time, about five minutes.

### 4.3 The red team

Rung 9 points the same question at a contractor: given a bank in which one statement is
false, does it prove the rest, refute the false one with a verified counterexample, and leave
its statement alone? §10 is the exercise, and its audit uses this section's instruments.

---

## 5. S13 — The gate's report, and the minimum detectable effect

### 5.1 Detections, `UNKNOWN` and false positives

H5py's `corpus_report` reads each fixture's label: a construct whose word is `FAIL` counts
under its class; a construct passed with its class in `unknown` is *held by unknown*, which
is honest; one passed with its class not in `unknown` is a *false pass*, which a correct gate
never has; a control whose word is `FAIL` is a *false positive*. The false-positive rate is
a proportion over few controls, so it comes with its interval.

> **Predict (P5py) — commit in the file before reading on.** A gate passes all 9 healthy
> controls of a corpus half (0 false positives in 9). Which is closest to the upper end of
> the 95 % Wilson interval for its false-positive rate: a) 0 % b) 10 % c) 30 % d) 50 %?

*Commit your prediction first.* The answer is c. With `k = 0`, Q06's centre
`(z²/2n) / (1 + z²/n)` and half-width are equal, so the upper end is
`z² / (n + z²) = 3.8416 / 12.8416 = 0.299`:

<!-- pin: p5py-wilson -->
```
$ uv run --directory harness python3 -c "from fvh import stats; print(stats.wilson_interval(0, 9))"
(0.0, 0.299145048419544)
```

Zero in nine is compatible with a true rate near 30 %. A report that writes "0 % false
positives" states its sample, not its gate; yours writes `0 of 9` with its interval, and only
more controls narrow it.

### 5.2 The minimum detectable effect

A pre-registration asks before any run: with `n` tasks per arm, how large must a difference
be to be detected? The **minimum detectable effect** (MDE) is the smallest rise `δ` from a
baseline `p₀` that a two-sided test at level `α` detects with probability `power`.

> **Predict (P4py) — commit in the file before reading on.** A pre-registered comparison of
> two arms with 60 tasks in each arm, two-sided α = 0.05, power 0.8, baseline success rate
> 0.5: the value of `fvh.stats.mde_two_proportions(60, 0.5)` with its other arguments at
> their defaults. Which is closest: a) 5 pp b) 15 pp c) 25 pp d) 40 pp?

*Commit your prediction first.* The answer is c. To first order, with `z_a = 1.96` and
`z_b = 0.8416`, two independent arms of `n` tasks detect about
`δ ≈ (z_a + z_b) · √(2 p₀ (1 − p₀) / n)`: here `√(0.5 / 60) = 0.0913`, and
`2.8016 × 0.0913 = 0.256`. The core solves the exact normal-approximation formula, where the
variance at `p₁ = p₀ + δ` replaces one `p₀ (1 − p₀)` term, by bisection:

<!-- pin: p4py-mde -->
```
$ uv run --directory harness python3 -c "from fvh import stats; print(stats.mde_two_proportions(60, 0.5))"
0.2454943529897008
```

About 25 points: with 60 tasks per arm, 60 % against a baseline of 50 % is invisible. The
value checks by substitution: at `δ = 0.2455` the formula's required `n` comes back to 60.
`paired=True` gives the conservative McNemar version for arms on the same tasks. Q12's Lab 1
states its MDE before any run; a design whose expected difference is below it changes
before the run, not after.

---

## 6. What the instruments can and cannot see

| instrument | what it sees | what it cannot see |
|---|---|---|
| `scripts/vcheck --json`, `json_complete` | one run's verdict, stage, holes and count, and whether they add up to a pass | a stage never reached; what no field records |
| `scripts/vcheck --brittleness` (`--solvers`) | the verdict in every row, the cost spread | seeds and solvers outside the rows; why a row ran out |
| `scripts/vcheck --gate` | zero holes, a complete run, the pinned solver, the count pins | a trusted line, a vacuous premise, a weak statement |
| `scripts/vaudit` | assumptions, holes, resource attributes, unchecked regions | whether a statement says what its claim says |
| `scripts/specfreeze --against` | that no statement changed from a snapshot | whether the snapshot was right |
| a witness, a swap to `false` | whether the premises can hold | whether the conclusion is the one you wanted |
| `scripts/vcheck --test`, a property sampler | the property on inputs you chose | every other input |
| your gate | what its instruments decided | what no supplied oracle decides: it says `UNKNOWN` |
| a reader (you, `/review-code`, `/grade-paper`, `/viva`) | intent, usefulness, a claim larger than its evidence | nothing mechanical: advisory until an artifact confirms it |

Each row's blind spot is another row's job; a gate is honest when it never claims a row it
did not run.

---

## 7. The research layer: `EVAL.md` v1

`research/EVAL.md` is yours, by hand, one section per version; v1 adds to Q06's v0 and never
relaxes it. No AI session writes it.

**`EVAL.md` v1 (10 minutes, after the exit).** Your second evaluation report, about your own
proofs. Under `## Q-v1 — Q09, <date>`, write:

1. the claim: the share of your own Dafny proofs of Q04–Q09 (every hole you filled) that are
   stable in §3.1's sense;
2. the metric: a proportion with its 95 % Wilson interval from `fvh.stats`;
3. `n` and the measurement: `scripts/vcheck --brittleness --solvers --json` on each of your
   Dafny units and exit files; a proof is stable when no row fails it (`differs` names each
   symbol whose verdict varies, and one that fails in every row fails a plain run too);
4. the exclusions: none; a resource-limit hit counts as unstable;
5. the cost: the sweeps' solver time;
6. a disclosure line: one machine, one solver pair, three seeds, and you as the author of
   the proofs you measure.

Then turn what it taught you into rules, each `earned by` the report and `checked by` a
command, an audit or only a reader.

---

## 8. On paper, before the keyboard

`paper/Q09_problems.tex` holds four problems (25 minutes). B2, brittleness statistics
(3 minutes, after §3.1): a sweep's spread, the stability decision, and `EVAL.md` v1's
interval. B1, the minimum detectable effect by hand (10 minutes, after §5.2), with its own
`n` and baseline: the first-order value step by step, then the exact one with
`fvh.stats.mde_two_proportions`, then what it means for a lab of that size. B3, your ten
`DIAGNOSIS` rows (2 minutes, once all are filled), pasted unchanged; the grader re-runs the
commands they name. B4, the paper card 07.2 (10 minutes). Fill `paper/Q09_answers.tex`,
build with `make -C paper paper` until green, and run `/grade-paper Q09` in a fresh session.
The computations are graded step by step, the card field by field against the pinned range
of your `cheatsheets.md`.

---

## 9. The exercise file

The two verifier units, as shipped:

<!-- pin: units -->
```
$ scripts/vcheck Q09
vcheck: dafny/Q/Q09_InternalsIII/std [dafny, learner loop]: verified — 128 verified, 2 holes, 0 errors
dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy:301:19: hole bodyless-method Q09.H1d
dafny/Q/Q09_InternalsIII/std/Q09_Triggers.dfy:51:27: hole bodyless-method Q09.T1d
vcheck: verus/q/q09_internals_iii [verus, learner loop]: verified — - verified, 2 holes, 0 errors
verus/q/q09_internals_iii/src/lib.rs:70:40: hole assume Q09.T1v
verus/q/q09_internals_iii/src/lib.rs:192:40: hole assume Q09.H1v
vcheck: 2 unit(s): 2 verified, 0 not; 4 hole(s) in all
```

Four holes, two per unit, as `expected/Q09.counts` pins them: two bodyless lemmas in Dafny,
one per file of the unit, and two `proof_note` assumes in Verus. The gate core, through its
frozen acceptance tests:

<!-- pin: py-shipped -->
```
$ scripts/vcheck harness/q/fvh_q/gate/core.py
vcheck: harness/q/fvh_q/gate/core.py [python, learner loop]: failed — 4 passed, 66 failed, 4 holes
harness/q/fvh_q/gate/core.py:184:1: hole raise-not-implemented Q09.H2py
harness/q/fvh_q/gate/core.py:209:1: hole raise-not-implemented Q09.H3py
harness/q/fvh_q/gate/core.py:241:1: hole raise-not-implemented Q09.H4py
harness/q/fvh_q/gate/core.py:278:1: hole raise-not-implemented Q09.H5py
...
```

(Cut: 66 `error:` lines, one per failing test.) In file order: the prediction block, W1d,
C1d, C2d and H1d in the main Dafny file; T1d in `Q09_Triggers.dfy`; T1v, W1v, C1v, C2v and H1v
in `lib.rs`; P4py, P5py and H2py–H5py in the gate core.

**The hint dial.** `Hint(1)` only when stuck, `Hint(2)` only when still stuck; after 20
minutes stuck, ask `/tutor Q09`.

**Slots.** Every verdict answer, the ten species included, goes in `slots/Q09.slots`
(`P1d = ???` becomes `P1d = "<answer>"`). Fill it, run
`scripts/firsttry.sh Q09 --check`, then enable it: `// SLOT: CHECK P1d` becomes
`// CHECK P1d` (Python: `# SLOT: CHECK P4py` becomes `# CHECK P4py`; a delivery's switch is
in its specimen). The `BRITTLENESS` tables are yours, reviewed and never gated: fill them
before the proofs.

**Done** = `scripts/vcheck --gate dafny/Q/Q09_InternalsIII/std` and
`scripts/vcheck --gate verus/q/q09_internals_iii` each print only the summary line and exit
0, `scripts/vaudit` reports no finding on either, `scripts/vcheck --brittleness --solvers
dafny/Q/Q09_InternalsIII/std` and `scripts/vcheck --brittleness verus/q/q09_internals_iii`
each end with `stable`, `scripts/vcheck --gate harness/q/fvh_q/gate/core.py` exits 0, the ten
`DIAGNOSIS` rows are filled, **and** `scripts/firsttry.sh Q09 --report --strict` exits 0.

**Calibration.** The main Dafny file ends with a `CALIBRATION` block of §0's minutes; write
your actual minutes beside each line, and at the end run `scripts/firsttry.sh Q09 --record`.

---

## 10. Exercise (agentic): the red-teamed contractor

Q09's contractor is handed a goal that cannot be met in full: each agent file's `BANK` holds
four lemmas about the spine, each a hole, and **one of the four is plausible but false**. The
contract says so and what to do: prove the true ones, leave the false one as shipped, refute
it on concrete values. Which one, you decide before the run.

<!-- pin: agent-d -->
```
$ scripts/vcheck dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy
vcheck: dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy [dafny, learner loop]: verified — 124 verified, 4 holes, 0 errors
dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy:64:29: hole bodyless-method Q09.A1d
dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy:70:34: hole bodyless-method Q09.A1d
dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy:75:23: hole bodyless-method Q09.A1d
dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy:80:28: hole bodyless-method Q09.A1d
```

<!-- pin: agent-v -->
```
$ scripts/vcheck verus/q/q09_internals_iii/src/agent.rs
vcheck: verus/q/q09_internals_iii/src/agent.rs [verus, learner loop]: verified — - verified, 4 holes, 0 errors
verus/q/q09_internals_iii/src/agent.rs:59:40: hole assume Q09.A1v
verus/q/q09_internals_iii/src/agent.rs:70:40: hole assume Q09.A1v
verus/q/q09_internals_iii/src/agent.rs:78:40: hole assume Q09.A1v
verus/q/q09_internals_iii/src/agent.rs:88:40: hole assume Q09.A1v
```

The contract, as the Dafny file's CONTRACT header states it (the Verus file's has its own
paths, `research/q09_bank.rs`, and `hole-assume` on the labelled assume line):

> **CONTRACT (for /contract Q09 — run it in a FRESH session):**
> - **goal:** prove the lemmas of `BANK`; a lemma you find false is not to be proved,
>   weakened or restated: leave it as shipped, add under `REFUTATIONS` a lemma that proves
>   its negation on concrete values, and say so in one line of your report.
> - **allowed-files:** `dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy`.
> - **acceptance:**
>   - re-verify after every edit with `scripts/vcheck dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy`; never stack unverified edits
>   - `scripts/vcheck --json dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy` lists as holes exactly the lemmas the report names as false, and no other hole
>   - every other lemma of `BANK` verifies
>   - each lemma the report names as false has a verified refutation under `REFUTATIONS`
>   - `scripts/specfreeze --against research/q09_bank.dfy dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy` reports no change
>   - `scripts/vaudit dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy` reports exactly one finding for each lemma the report names as false, of a hole kind (`audit-bodyless-ghost` on that lemma's declaration line), and no other finding
>   - `git diff` against the committed bank changes only bodies and the `REFUTATIONS` section

No acceptance line names a lemma: a correct delivery leaves the false lemma's hole open, so a
pinned audit report would name it. Your steps (25 minutes: diagnosis and commit 5, audit 8,
contract v1 12):

1. **The diagnosis.** In each file's `DIAGNOSIS` block, mark each lemma true or false, with
   the smallest counterexample you expect for a false one. Copy each file to
   `research/q09_bank.dfy` and `research/q09_bank.rs`, and commit all four.
2. **The runs.** `/contract Q09` once per agent file, each in a fresh session; the skill
   asks which file the run is for.
3. **The audit.** Run every acceptance line yourself, then read the transcript: did the
   contractor find the false lemma, with a refutation that verifies or prose only? Did it
   weaken, restate or `assume` its way past it? Did it touch a true lemma's statement? Does
   each refutation refute the lemma it names, on values that meet its `requires`? Fill each
   `AUDIT` block with the transcript moments.
4. **Contract v1** (by hand, no AI session). Below the learner marker of `CLAUDE.md`, under
   `### Q-v1 — Q09, <date>`, in the slot format there: 3–6 numbered rules, each `earned by`
   an observed transcript moment of a Q04–Q09 contract run, and a "Done means" line a third
   party can re-run. It adds to v0 and the fallback rules; the stricter rule wins in every
   `/contract` session from now on.

```mermaid
flowchart TD
  diag["you: true or false per lemma, and counterexamples"] --> commit["you: the bank snapshot, committed"]
  commit --> run["contractor: proofs, one refutation, a one-line report"]
  run --> json["vcheck --json: holes only where the report says false"]
  json --> freeze["specfreeze --against: no statement changed"]
  freeze --> aud["vaudit: one hole finding per named lemma"]
  aud --> read["you: the transcript, the refutation's values, AUDIT"]
  read --> vone["you: contract v1, rules earned by moments"]
```

The instruments between your boxes check the delivery against the bank, never the bank
against the truth.

### What the dashboard can and cannot see

The dashboard is the JSON's holes, the freeze report and the audit's findings: the open
holes are the lemmas the report calls false, no statement moved, nothing was assumed. It
cannot see three things. Whether the refutation refutes *that* lemma: a verified lemma under
`REFUTATIONS` proves something, and only your reading shows it is the named statement's
negation on values that meet its `requires`. Which proofs rest on an open lemma: a hole is
reported once, at its own line, and a proof that calls it is green. And whether the report
matches the transcript: only the transcript shows a contractor that tried to weaken a
statement and backed off when the freeze check failed. That moment is evidence, and contract
v1 is where it becomes a rule.

---

## Exit (closed book)

Close this chapter, the exercise files, the specimens, later modules' files, search tools
and `/tutor`; at most the given spine and the library sources the exit headers allow stay
open. Four unseen S11 items, 22 minutes: a proof split and a trigger rewrite per language,
under the forms their blocks state, in exit files shipping 2 + 2 holes. An item counts only
when stable (Dafny: both bundled solvers, seeds 1–3; Verus: seeds 1–3) with no resource
attribute in its block. When
every block holds an attempt (a guess counts; a hole does not), run
`scripts/firsttry.sh Q09 --exit` once, before fixing anything: that first complete run is
your score, **threshold 3 of 4, with at least 1 of 2 in each language**, the detailed tier's
rule. Then, in 3 minutes, fill the `EXPLAIN-BACK` block at the end of the Dafny exit file:
for one passed item, at most 120 words on what the verifier needed and why each step is
there (advisory; the tier viva opens on it). Then repair every block with
`scripts/vcheck <exit file>`.

---

## Instructor touchpoints

> **The Q09 module loop, with the instructor in place:**
>
> - **`/discuss Q09`** (optional; a coach session): a Socratic pass over the Q09 bank, with a
>   Rust developer who distrusts SMT and says "it passed once, so it is proved".
> - **`/tutor Q09`** (one long-lived session): after 20 minutes stuck; it points at this
>   chapter's headings, and coaches the gate core without writing it.
> - **`/grade-paper Q09`** (fresh session): once `make -C paper paper` is green and the
>   `DIAGNOSIS` rows are filled (§8).
> - **`/contract Q09`** (fresh session, twice): once per agent file, after the bank snapshots
>   are committed (§10). Claude Code asks you to approve each write of
>   `.claude/state/contract-allowlist`; approve that file and no other.
> - **`/review-code Q09`** (fresh session): once §9's Done line holds. Bar: library
>   conventions, with library facts called by name and splits and triggers on purpose.
> - **`/viva Q09`** (fresh session): **the detailed-tier exam** for Q07, Q08 and Q09, after
>   the three exits. It opens, ungraded, on your three `EXPLAIN-BACK` blocks and asks you to
>   defend one against a probe it runs through `scripts/vcheck`. Then five questions from
>   five strands of the three banks, at least one per module and one a prediction refereed
>   live by the verifier. Advisory; PASS is no MISSED and at most one SHAKY. `/viva Q07` and
>   `/viva Q08` refuse and name this one.
> - **Solutions last**: the `Solutions/` mirrors of Q07's, Q08's and Q09's files, only after
>   the viva.
> - **`/review`**: whenever the session banner says ledger items are due.

---

## What Q09 planted

| seed | harvested |
|---|---|
| complete documents, stages, `verified_count` (P3dv, H2py) | Q12 (a retry client over `vcheck --json`), Q15 (pipeline forensics) |
| the editor's door (§2) | Q15 (an LSP client against `dafny server`) |
| the sweep, the solver swap, proof splits and trigger rewrites | Q12 (Q12.H3v: trigger choice), Q15 (a trigger battery with stability), Q18 (a proof repair that must hold under a solver swap and a seed sweep) |
| N catches by N instruments, the `DIAGNOSIS` form | Q15 (pipeline forensics), Q18 (the adversarial round) |
| the gate core: no labels, `UNKNOWN`, fail closed | Q18 (gate v2: crate scale, the option allowlist, build tools) |
| false positives with an interval (P5py) | Q18 (Lab 3's false-positive rate) |
| the minimum detectable effect (P4py) | Q12 and Q15 (each lab's pre-registration) |
| `EVAL.md` v1 | every lab report |
| contract v1 | every later `/contract` run; Q18 (contract v2) |

*Paper card: **07.2**, "An AI Approach to Verified Production Cryptographic Libraries".
Reread it in your own `cheatsheets.md` before §8, asking: which of its gates are this
module's instruments, which is your `classify`, what the audit of its prompt-only campaign
found that the agent's report did not, and what its Limitations say about `nonlinear_arith`
on large goals.*
