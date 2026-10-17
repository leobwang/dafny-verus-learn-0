# Q15 — Practice II-C + Lab 2

Q13 and Q14 practised strands S1–S8 in the intermediate tier. Q15 closes that tier with
family C, strands S9–S13, in two blocks. The **practice block** (165 minutes) is a client of
your own for Dafny's language server, four green deliveries whose defect sits in the
pipeline, a trigger battery and a proof that must be stable, two false lemmas to refute,
repair and prove, a toolsmith run and a red-team of your own tutor. The **Lab 2 block** (463
minutes) is your second experiment: do your oracles tell a faithful specification from a
weak, a vacuous and an over-strong one, does their feedback make an agent's specifications
more faithful, and how often does an agent that proves its code against its own
specification fail when the reference re-judges it? `/viva Q15` then examines Q13, Q14 and
Q15 together.
Three ideas do all the work:

1. **A green result is a claim about one instrument's view of the pipeline.** A server
   status, a verifier summary, the done gate, the assumption audit and a compiled test each
   see part of what a delivery rests on; a defect lives at the stage that none of the
   instruments you ran could see.
2. **A quantified fact is used only where its trigger matches.** A trigger that matches no
   term the goal holds is never used; a trigger that every instance creates again keeps the
   solver busy until a limit stops it. A stable proof makes exactly the instances it needs.
3. **A specification is judged against the meaning it should have, not against its own
   code.** Mutants of the code, a vacuity check and a two-way implication with a reference
   each catch a different failure, and a program verified against a specification its
   author also wrote is verified against that author's reading only.

---

## 0. How this module works, pretest, test-out

**Minutes: 628, plus the 30-minute tier viva.** *Practice:* brief 15 · S9 LSP client 30 ·
S10 pipeline forensic 20 · S11 trigger battery and stability 30 · S12 refute, repair, prove
15 · toolsmith 20 · tutor red-team 15 · exit 20. *Lab 2:* prose specs 108 · pre-registration
40 · `/grade-paper` 10 · oracles 75 · vericoding arm 20 · run setup 20 · analysis 60 · reward
audit 15 · bench audit 30 · `--post` 10 · cards 45 · task cards 20 · ledger and calibration
10. The main Dafny file's `CALIBRATION` block repeats this line.

**Setup.** Start one long-lived `/tutor Q15` session. Q06's `harness/.venv` still serves the
Python files (`cd harness && uv run …`). Q15 adds no layer: L6 is Q13's. The language server
starts only through the frozen entry point `fvh.lsp.start_server` (`harness/fvh/lsp.py`),
which runs `scripts/dafny-server`: the pinned `dafny server` from a scratch copy of the
install, under the Dafny memory cap. Never start a server process of your own.

**Predictions first, all eleven**, before anything else:

| items | where the answer goes |
|---|---|
| P1d (the server, S9), P6dv–P11dv (the battery, S11) | `slots/Q15.slots`; the switches are in the main Dafny file's prediction block |
| P2d, P3d, P4v, P5v (the pipeline forensic, S10) | `slots/Q15.slots`; each switch is in its specimen under `specimens/Q15/` |

Read the battery's six predicted goals under `tools/Q15/battery/`, but do not run them.
Record all eleven with `scripts/firsttry.sh Q15 --check`, then enable each switch. Until
then `scripts/vcheck` refuses the specimens.

**No pretest, no test-out.** A practice module is the practice; the Lab 2 block is new work
and has none either. The exit (closed book, one item) checks the practice block; the lab's
acceptance (§6.4) checks the lab.

Each prediction reappears below in a box,

> **Predict (Pn) — commit in the file before reading on.**

and its answer comes only after the box, below the words *Commit your prediction first.*
The four forensic predictions share one box (§2), and so do the six battery predictions
(§3).

**Outputs.** Every output fence is a real run on the course pins (Dafny 4.11.0, Verus
0.2026.09.27.3cf1832), pinned in `expected/Q15.chapter.toml`. `refute*.dfy`, `next*.dfy`
and `p1.dfy` are scratch files run with `scripts/vcheck --module Q15`, which adds Q15's given
layers and options. Two fences are recorded quotes of the author's runs (§1, §5), each
marked so. Fences drop the wrapper's last line,
`raw output: <dir>`.

**What is pending.** The verification container runs (the author's oracle run in §5 used
it), and so do the lab's batch runner (the live `fvh run` that composes the arms, the
tasks, the ledger and the container) and the **grader container**, the only place Lab 2's
hidden truth (the reference specifications and verdicts) is ever opened: it is sealed, and
only the container's own grader unseals it, with no network, and reports verdicts alone.
Its judging step is built, and you start it yourself, from your own terminal (a Claude
session's guard refuses any line that names the sealed archive): on your six prose
specifications (§5), and after a batch on every run's delivery (§6.4). The two public
strata are built too, ten public tasks in Lab 2's form drawn from the validated pools
(§6.2), with their rule fixed: on a public card a delivery may also add proof
annotations, since most public tasks' code needs loop invariants and assertions before a
specification as strong as the prose verifies; the lab gate checks that the executable code
is unchanged. Do everything in this order: the practice block, the six
prose specifications (their use-site checks, your witnesses, the hidden check and
`/review-code`), the oracles against their frozen tests, the pre-registration and its
grading, the reward and bench audits, and the cards.

### This module's files

| file | what it is | shipped state |
|---|---|---|
| `dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy` | the main Dafny file: the prediction block (P1d, P6dv–P11dv), the stability item H1d and the refute-repair item H2d | verified, **2 holes** |
| `dafny/Q/Q15_PracticeIIC/std/Q15_Lab2Specs.dfy` | Lab 2's three Dafny prose tasks H3d–H5d, each with its client and witness | verified, **3 holes** |
| `verus/q/q15_practice_iic/src/lib.rs` | the Verus crate root: H1v and H2v | verified, **2 holes** |
| `verus/q/q15_practice_iic/src/lab2_specs.rs` | Lab 2's three Verus prose tasks H3v–H5v | verified, **3 holes** |
| `specimens/Q15/P2d.dfy.specimen` … `P5v.rs.specimen` | the four forensic deliveries, each with its `planted:` marker and switch | green-looking, slots unfilled |
| `slots/Q15.slots` | your eleven verdict answers | `???` |
| `tools/Q15/battery/` (`battery.toml`, `dafny/G01.dfy`–`G12.dfy`, `verus/G01.rs`–`G12.rs`) | the trigger battery: twelve goals, each a standalone file in both languages | given |
| `harness/q/fvh_q/lsp_client.py` | the language-server client (S9): H6py–H8py; its frozen tests replay a recorded server session | failed, **3 holes** |
| `harness/q/fvh_q/oracles.py` | Lab 2's oracles (S13): H9py–H12py; its frozen tests use synthetic tasks | failed, **4 holes** |
| `harness/fvh/lsp.py`, `scripts/dafny-server` | the course's one route to the language server | frozen |
| `dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` | rung 11, Dafny: four deliveries and an empty `ATTRIBUTIONS` block (§11) | verified, **4 holes** |
| `verus/q/q15_practice_iic/src/agent.rs` | rung 11, Verus: the same, never `mod`-declared | verified, **4 holes** |
| `research/q15_forensic.dfy`, `research/q15_forensic.rs` | rung 11's freeze references: the agent files' statements as shipped | given |
| `tools/Q15/toolsmith.py` | rung 12 (§12): a CONTRACT docstring and your `INTERFACE` and `AUDIT` blocks | no code |
| `research/q15_redteam.md` | your record of the tutor red-team (§7) | empty |
| `bench/local/q/lab2/` | Lab 2's local stratum: `STRATUM.toml` and twenty task forms | task forms shipped |
| `dafny/Q/Q15_PracticeIIC/exit/Q15_Exit.dfy` | the closed-book exit, outside every build | verified, **1 hole** |
| `verus/q/q15_practice_iic/src/exit.rs` | the Verus exit file: no block (exits come in pairs) | verified, no hole |
| `dafny/given/Q/QG_L1_BigNat.dfy` to `QG_L6_BigNat.dfy`; `verus/given/qg_bignat_l1` to `qg_bignat_l6` | the given spine, frozen | verified |
| `paper/Q15_problems.tex` → your `paper/Q15_answers.tex` | the pre-registration (B1), the lab report (B2, after the runs) and three cards (B3–B5; §9) | — |
| `Solutions/` mirrors of these files | the reference twins (never Lab 2's references: those are hidden truth) | yours to open LAST |

Seventeen holes are yours: ten verifier holes (five per language) and seven Python holes.
The agent files' eight are the contractor's.

---

## 1. S9 — The language server, and a client of your own

Q12's retry client read `scripts/vcheck --json`, a document written once a run has ended.
An editor talks to Dafny differently: `dafny server` speaks the Language Server Protocol
over its standard input and output, and publishes what it knows as notifications while it
works. Your client (H6py–H8py) has one conversation per file:

```mermaid
flowchart LR
  init["client: initialize (id 1), and wait for its response"] --> opened["client: initialized, then didOpen with the file's text"]
  opened --> notes["server: compilation status, diagnostics, symbol statuses"]
  notes --> ended{"every status final, or parsing or resolution failed?"}
  ended -->|"no: read on"| notes
  ended -->|"yes"| bye["client: shutdown (id 2), exit, and the server stopped"]
```

Every message, in both directions, is one JSON object behind a `Content-Length` header:
H6py writes that framing and H7py reads it, refusing a malformed header. H8py is the
conversation, and its docstring fixes when a file's verification has ended. The frozen
tests replay a recorded session of the pinned server (`harness/tests/q/fixtures/q15/lsp/`)
and hand-made streams, so no server runs in them; your own live check runs one file through
`fvh.lsp.start_server` (the file's header gives the command).

> **Predict (P1d) — commit in the file before reading on.** The file in P1's docstring (one module, a proved lemma `DoubleGrows`, then `DoubleMono` with no body), opened by your client with the pinned `dafny server`: once the file's verification has ended, which status does the client report for each lemma, in the block's answer form?

*Commit your prediction first.* `correct correct`. The file:

```dafny
module ServerProbe {
  lemma DoubleGrows(x: nat)
    ensures x <= 2 * x
  {
  }

  lemma DoubleMono(x: nat, y: nat)
    requires x <= y
    ensures 2 * x <= 2 * y
}
```

The author's run of the reference client, as the live check prints it (a recorded quote;
your client prints the same lines once H8py is done):

<!-- pin: p1d-client -->
```
$ cd harness && PYTHONPATH=q uv run python -m fvh_q.lsp_client p1.dfy
ended: verified
  2:9 correct
  7:9 correct
  9: severity 2: This ensures clause is part of a bodyless method. Add the {:axiom} attribute to it or the enclosing method to suppress this warning
```

Both lemmas are `correct`. The server checks a lemma's body against its contract, and a
lemma with no body has nothing to check: its contract is taken as given, and the only trace
of that is a warning (severity 2) on its `ensures` line. The course's wrapper sees the same
file differently:

<!-- pin: p1-vcheck -->
```
$ scripts/vcheck --module Q15 p1.dfy
vcheck: p1.dfy [dafny, learner loop]: verified — 23 verified, 1 hole, 0 errors
p1.dfy:9:19: hole bodyless-method ServerProbe.DoubleMono
```

`scripts/vcheck` counts the bodyless lemma as a hole, so the file is not done. A client that
turned the server's statuses into a pass would call this file proved: the server channel
answers "did each body meet its contract", never "is there a body". An editor's green tick
is the first answer only.

---

## 2. S10 — Pipeline forensic: where a green delivery's defect lives

Q12's stages were the ones a run stops at: parse, resolve, verify, compile, test. A
delivery that verifies passes all of those and can still claim more than was checked, and
the question is then where in its pipeline the claim lost its support. The specimens' block
fixes four stages (input, options, trust, test) and four instruments, run in a fixed order:

```mermaid
flowchart LR
  v["vcheck: verified, 0 holes?"] -->|"pass"| g["vcheck --gate: verified, exit 0?"]
  g -->|"pass"| a["vaudit: 0 findings?"]
  a -->|"pass"| t["vcheck --test: every test ran and passed?"]
  v -->|"no"| first["the first instrument that does not pass"]
  g -->|"no"| first
  a -->|"no"| first
  t -->|"no"| first
```

The answer names the stage, from reading the file, and the first instrument whose result
is not a pass. Comments and names in a delivery are the contractor's prose and prove
nothing; each file's one `planted:` marker says where to look, never what you will find.

> **Predict (P2d, P3d, P4v, P5v) — commit in the files before reading on.** Four deliveries that look green: `P2d.dfy.specimen` (a zero limb on top changes no value), `P3d.dfy.specimen` (the low limb of a nat, with a test), `P4v.rs.specimen` (the low limb as the value modulo `BASE`) and `P5v.rs.specimen` (the index of the lowest non-zero limb). For each: the stage of its defect and the first instrument that shows it, `<stage> <instrument>`.

*Commit your predictions first.* `input gate`, `test vaudit`, `trust vcheck`, `options
gate`. P2d's plain run, then its gate:

<!-- pin: p2d-vcheck -->
```
$ scripts/vcheck specimens/Q15/P2d.dfy.specimen
vcheck: specimens/Q15/P2d.dfy.specimen [dafny, learner loop]: verified — 1 verified, 0 holes, 0 errors
specimens/Q15/P2d.dfy.specimen:50:11: warning: Members with @VerifyOnly temporarily disable the verification of other members in the entire file
```

<!-- pin: p2d-gate -->
```
$ scripts/vcheck --gate specimens/Q15/P2d.dfy.specimen
vcheck: specimens/Q15/P2d.dfy.specimen [dafny, gate]: failed — 1 verified, 0 holes, 0 errors, 1 finding
specimens/Q15/P2d.dfy.specimen:50:11: warning: Members with @VerifyOnly temporarily disable the verification of other members in the entire file
specimens/Q15/P2d.dfy.specimen: warnings-fail-gate: warnings fail the gate (W-D04): holes and every other warning must be gone
$ echo $?
1
```

`{:only}` on the helper tells Dafny to verify that one member and skip the rest, so the
delivered lemma was never checked at all: an input defect. The plain run reports success
(one symbol verified, the helper) with a warning; the gate fails on the warning. P3d:

<!-- pin: p3d-vcheck -->
```
$ scripts/vcheck specimens/Q15/P3d.dfy.specimen
vcheck: specimens/Q15/P3d.dfy.specimen [dafny, learner loop]: verified — 3 verified, 0 holes, 0 errors
```

<!-- pin: p3d-gate -->
```
$ scripts/vcheck --gate specimens/Q15/P3d.dfy.specimen
vcheck: specimens/Q15/P3d.dfy.specimen [dafny, gate]: verified — 3 verified, 0 holes, 0 errors
$ echo $?
0
```

<!-- pin: p3d-vaudit -->
```
$ scripts/vaudit specimens/Q15/P3d.dfy.specimen
specimens/Q15/P3d.dfy.specimen:47: expect-outside-test — `expect` outside a {:test}/@Test method is assumed by the verifier (Δ3, G11)
vaudit: specimens/Q15/P3d.dfy.specimen [dafny, learner]: 1 finding(s)
$ echo $?
1
```

The test method has no `{:test}` attribute, so nothing ever runs it, and its expectation is
wrong besides (the low limb of `BASE + 5` is 5). The verifier never checks an `expect`: it
assumes it, so the wrong expectation verifies, and the gate passes. Only a test run checks
it, and no test run reaches this one. The audit names the assumption. P4v:

<!-- pin: p4v-vcheck -->
```
$ scripts/vcheck specimens/Q15/P4v.rs.specimen
vcheck: specimens/Q15/P4v.rs.specimen [verus, learner loop]: verified — - verified, 1 hole, 0 errors
specimens/Q15/P4v.rs.specimen:52:1: hole external_body Q15.P4v
```

`#[verifier::external_body]` tells Verus to trust the helper's `ensures` without looking
at its body, which returns 1 for an empty sequence whose value is 0. The plain run already
counts the trusted body as a hole: trust, seen by the first instrument. P5v:

<!-- pin: p5v-vcheck -->
```
$ scripts/vcheck specimens/Q15/P5v.rs.specimen
vcheck: specimens/Q15/P5v.rs.specimen [verus, learner loop]: verified — 2 verified, 0 holes, 0 errors
```

<!-- pin: p5v-gate -->
```
$ scripts/vcheck --gate specimens/Q15/P5v.rs.specimen
vcheck: specimens/Q15/P5v.rs.specimen [verus, gate]: failed — 2 verified, 0 holes, 1 error, 1 finding
(no file): error: gate: 1 lint finding(s)
specimens/Q15/P5v.rs.specimen:37: exec-allows-no-decreases: exec_allows_no_decreases_clause lets a diverging body prove anything (V8, Δ9)
$ echo $?
1
```

`exec_allows_no_decreases_clause` switches off the termination check of the function's
loop, and on a sequence with no non-zero limb the loop never ends: its `ensures` holds only
of runs that return. The plain run is clean; the gate's lint refuses the attribute. Of the
four, only P4v's defect is visible to the instrument most people stop at.

---

## 3. S11 — The trigger battery, and a stable proof

Q09 taught triggers: the solver instantiates a quantified fact only at terms that match its
trigger, and each instance can add new terms. The battery is twelve goals, each a whole
file in both languages, each proving its statement from one quantified step whose trigger
is the goal's only open choice. Six goals are predictions:

> **Predict (P6dv, P7dv, P8dv, P9dv, P10dv, P11dv) — commit in the file before reading on.** The battery goals G01, G02, G03, G07, G09 and G10 (`tools/Q15/battery/dafny/` and `verus/`), each run as shipped with `scripts/vcheck <file>`: what does each language's form give, `D:<v> V:<v>` in the block's vocabulary?

*Commit your predictions first.* G01 `D:fail V:fail`, G02 `D:ok V:ok`, G03 `D:fail
V:err:resolve`, G07 `D:err V:err:resolve`, G09 `D:fail V:ok`, G10 `D:err V:ok`.

<!-- pin: g01 -->
```
$ scripts/vcheck tools/Q15/battery/dafny/G01.dfy tools/Q15/battery/verus/G01.rs
vcheck: tools/Q15/battery/dafny/G01.dfy [dafny, learner loop]: failed — 7 verified, 0 holes, 1 error
tools/Q15/battery/dafny/G01.dfy:46:3: error: a postcondition could not be proved on this return path
tools/Q15/battery/dafny/G01.dfy:45:15: related: this is the postcondition that could not be proved
vcheck: tools/Q15/battery/verus/G01.rs [verus, learner loop]: failed — 5 verified, 0 holes, 1 error
tools/Q15/battery/verus/G01.rs:55:9: error: postcondition not satisfied
vcheck: 2 unit(s): 0 verified, 2 not; 0 hole(s) in all
```

G01's step is triggered on the successor's place value, and the goal mentions the place
values of `a` and `b` only: no term matches, so the proved step is never used.

<!-- pin: g02 -->
```
$ scripts/vcheck tools/Q15/battery/dafny/G02.dfy tools/Q15/battery/verus/G02.rs
vcheck: tools/Q15/battery/dafny/G02.dfy [dafny, learner loop]: verified — 8 verified, 0 holes, 0 errors
vcheck: tools/Q15/battery/verus/G02.rs [verus, learner loop]: verified — 6 verified, 0 holes, 0 errors
vcheck: 2 unit(s): 2 verified, 0 not; 0 hole(s) in all
```

G02 writes no trigger, and each tool chose one itself that the goal's terms match.

<!-- pin: g03 -->
```
$ scripts/vcheck tools/Q15/battery/dafny/G03.dfy tools/Q15/battery/verus/G03.rs
vcheck: tools/Q15/battery/dafny/G03.dfy [dafny, learner loop]: failed — 8 verified, 0 holes, 1 error
tools/Q15/battery/dafny/G03.dfy:46:3: error: a postcondition could not be proved on this return path
tools/Q15/battery/dafny/G03.dfy:45:28: related: this is the postcondition that could not be proved
vcheck: tools/Q15/battery/verus/G03.rs [verus, learner loop]: failed — - verified, 0 holes, 1 error, stage resolve
tools/Q15/battery/verus/G03.rs:57:5: error: Could not automatically infer triggers for this quantifier.  Use #[trigger] annotations to manually mark trigger terms instead.
vcheck: 2 unit(s): 0 verified, 2 not; 0 hole(s) in all
```

G03 writes no trigger either. Dafny chose one and the proof still fails; Verus refuses to
choose, at resolution, before any solving.

<!-- pin: g07 -->
```
$ scripts/vcheck tools/Q15/battery/dafny/G07.dfy tools/Q15/battery/verus/G07.rs
vcheck: tools/Q15/battery/dafny/G07.dfy [dafny, learner loop]: error — - verified, 0 holes, 1 error
tools/Q15/battery/dafny/G07.dfy:6:9: error: Internal error occurred during verification: Boogie program had 2 resolution errors:
Microsoft.Dafny.AutoGeneratedOrigin: trigger must mention all quantified variables, but does not mention: n#0_1
Microsoft.Dafny.AutoGeneratedOrigin: trigger must mention all quantified variables, but does not mention: n#0_1
vcheck: tools/Q15/battery/verus/G07.rs [verus, learner loop]: failed — - verified, 0 holes, 1 error, stage resolve
tools/Q15/battery/verus/G07.rs:73:5: error: trigger does not cover variable n
vcheck: 2 unit(s): 0 verified, 2 not; 0 hole(s) in all
```

G07's trigger mentions one of the step's two bound variables. Neither tool accepts that: a
trigger must bind every variable, or an instance would have a variable with no value.
Dafny's summary verdict is `error`, not `failed`: the refusal comes from Boogie, the layer
below Dafny, as an internal error. (Cut, here and in G10: the .NET stack trace under it.)

<!-- pin: g09 -->
```
$ scripts/vcheck tools/Q15/battery/dafny/G09.dfy tools/Q15/battery/verus/G09.rs
vcheck: tools/Q15/battery/dafny/G09.dfy [dafny, learner loop]: failed — 8 verified, 0 holes, 1 error
tools/Q15/battery/dafny/G09.dfy:46:3: error: a postcondition could not be proved on this return path
tools/Q15/battery/dafny/G09.dfy:45:47: related: this is the postcondition that could not be proved
vcheck: tools/Q15/battery/verus/G09.rs [verus, learner loop]: verified — 6 verified, 0 holes, 0 errors
vcheck: 2 unit(s): 1 verified, 1 not; 0 hole(s) in all
```

<!-- pin: g10 -->
```
$ scripts/vcheck tools/Q15/battery/dafny/G10.dfy tools/Q15/battery/verus/G10.rs
vcheck: tools/Q15/battery/dafny/G10.dfy [dafny, learner loop]: error — - verified, 0 holes, 1 error
tools/Q15/battery/dafny/G10.dfy:6:9: error: Internal error occurred during verification: Boogie program had 2 resolution errors:
Microsoft.Dafny.AutoGeneratedOrigin: trigger must mention all quantified variables, but does not mention: m#0_1
Microsoft.Dafny.AutoGeneratedOrigin: trigger must mention all quantified variables, but does not mention: m#0_1
vcheck: tools/Q15/battery/verus/G10.rs [verus, learner loop]: verified — 8 verified, 0 holes, 0 errors
vcheck: 2 unit(s): 1 verified, 1 not; 0 hole(s) in all
```

G09 shows the two tools disagreeing on the same written trigger. G10's Dafny form is
refused as G07's is; its Verus form writes no trigger, and Verus's own choice works. The
battery's lesson is the verdict table, not a rule you could have derived without running
it; the toolsmith (§12) turns that into a tool.

**H1d, H1v (stability).** Each ships its statement and a quoted attempt: one quantified
step about place values, triggered on the plain place-value term. Paste the attempt, run
the brittleness sweep the item names (Dafny `--brittleness --solvers`: both bundled solvers
times seeds 1–3; Verus `--brittleness`: seeds 1–3), and fill the `BRITTLENESS` table with
what it prints, resource counts included. Then write a proof whose quantified step has a
trigger that no instance of the step creates, and sweep again. Each block's `// form:
trigger, stable` line is checked by `scripts/firsttry.sh Q15 --report --strict`: the
block must hold a quantified step with an explicit trigger and no resource attribute, and
under `--strict` the sweep runs and every row must verify. The docstring's question, which
terms the proof must hold for your trigger to fire, is the plan.

---

## 4. S12 — Refute, repair, prove

A proof that fails tells you this proof did not go through; it does not tell you the claim
is false. Here is a toy claim, delivered with an empty proof:

```dafny
module HalfToy {
  // The claim as delivered.
  lemma HalfBelow(x: nat)
    requires x > 0
    ensures x / 2 < x - 1
  {
  }
}
```

<!-- pin: refute-claim -->
```
$ scripts/vcheck --module Q15 refute1.dfy
vcheck: refute1.dfy [dafny, learner loop]: failed — 23 verified, 0 holes, 1 error
refute1.dfy:6:3: error: a postcondition could not be proved on this return path
refute1.dfy:5:19: related: this is the postcondition that could not be proved
```

The failure could be a missing step. A **refutation** settles it: a lemma with no
parameters whose `ensures` says, at values you choose, that the claim's `requires` holds
and its `ensures` does not. Then the **repair**: the smallest change that makes the claim
true, here one `requires` clause added and the shipped one kept:

```dafny
module HalfToy {
  // The refutation: at x = 2 the requires holds and the ensures does not.
  lemma HalfBelowRefuted()
    ensures var x: nat := 2; x > 0 && !(x / 2 < x - 1)
  {
  }

  // The repair: one requires clause added, the shipped clause kept.
  lemma HalfBelow(x: nat)
    requires x > 0
    requires x > 2
    ensures x / 2 < x - 1
  {
  }
}
```

<!-- pin: refute-repair -->
```
$ scripts/vcheck --module Q15 refute2.dfy
vcheck: refute2.dfy [dafny, learner loop]: verified — 26 verified, 0 holes, 0 errors
```

Both verify: the refutation is a proof, of the claim's negation at one point, and the
repaired claim is now true and proved.

**H2d, H2v.** Each ships a false lemma about values of limb sequences, whose body is the
hole, and a given client below it. The three steps are the toy's, in order: under
`REFUTATIONS`, the refutation lemma the docstring names, on concrete sequences of your
choice; then a repair that adds `requires` clauses only; then the proof. The client fixes
what your repair may assume: it calls the lemma under its own `requires`, so a repair that
asks for more than the client knows leaves the client red, and a repair that asks for less
leaves the lemma false. The counterexample you find is the evidence for the repair: the
docstring's question asks which hypothesis the claim assumed without saying so.

---

## 5. S13 — Specifications from prose, and the oracles that judge them

**H3d–H5d, H3v–H5v (Lab 2's prose specifications).** Six prose tasks, three per language,
in `Q15_Lab2Specs.dfy` and `lab2_specs.rs`. Each ships a signature, an implementation that
runs, and no specification (H5v ships its `requires`, which its code needs; you write its
`ensures`): you write its `requires` and `ensures` from the prose (Verus:
with any spec fn of your own the specification needs), add proof lines without changing the
code, uncomment the client's use-site check, write one non-vacuity witness, and delete the
client's assume. Q13's prose item had three judges; Lab 2's add the mutant kill:

```mermaid
flowchart TD
  spec["your specification of the shipped code"] --> use["the use-site check: strong enough for one real caller?"]
  spec --> wit["your witness: can the requires hold at all?"]
  spec --> kill["mutants of the code: does a wrong body still verify against it?"]
  spec --> imp["two-way implication with the hidden reference: weaker, stronger or equal?"]
  kill --> free["reference-free: may be fed back to an agent"]
  wit --> free
  imp --> grader["grader container only, started by you (for an arm, after its batch)"]
```

The first three need nothing hidden; the hidden check names the reference, so it runs only
in the grader container, and never inside an arm's loop. For your six it is a two-way check
of each specification against the author's, the same as Q13's prose item: once a
specification is final, judge it from your own terminal with a judging spec under `/tmp`
that names its item, one language per run (a container is sized for its language):

```toml
[[candidate]]
id = "h3d"
item = "Q15.H3d"

[[candidate]]
id = "h4d"
item = "Q15.H4d"

[[candidate]]
id = "h5d"
item = "Q15.H5d"
```

and `scripts/mksandbox-run --truth Hidden/labs/Q15/verdicts.tar.age --truth-check judge
--judge /tmp/q15-judge-dafny.toml` (a second spec names `Q15.H3v`–`Q15.H5v`). Each
candidate's row gives one verdict word, `faithful`, `strong`, `weak`, `vacuous`, `undecided`,
`mismatch` or `context`, as Q13's §2 glosses them (`sandbox/image/truthcheck.py` defines
each), and the outcome words of the checks behind it, which show on which side (`requires`
or `ensures`) and in which direction a specification differs from the author's; no text of
the author's specification is printed. Mind the direction of a changed `requires`: in this
check a `requires` you add makes a specification `weak` (it demands more), while the oracles
below (`classify`, H11's `Verdict`) count an added `requires` as `STRONG` (it narrows the
specification) and do not see a dropped one. The two checks read a changed `requires` in
opposite directions. Q13's §2 rule holds here: run the check once per specification, after
it is final, and report that first run's verdict line to `/review-code`, as you report a
first try (a later run is reported beside it, as later). A reported `strong`, `weak`,
`vacuous` or `mismatch` is a finding of the review; `undecided` is the reader's to decide.
`/review-code` still reads each specification against the prose.

**What a mutant shows.** A toy method whose code returns its argument plus one, with one
mutant applied (the literal `1` made `2`), under a specification that only says the result
is larger:

```dafny
module NextToy {
  // The shipped code with one mutant applied (the literal 1 made 2).
  method NextAbove(x: nat) returns (y: nat)
    ensures y > x
  {
    y := x + 2;
  }
}
```

<!-- pin: mutant-weak -->
```
$ scripts/vcheck --module Q15 next1.dfy
vcheck: next1.dfy [dafny, learner loop]: verified — 23 verified, 0 holes, 0 errors
```

The mutant verifies: it **survives**, so the specification cannot tell it from the right
code. The same mutant under a specification that pins the result:

```dafny
module NextToy {
  // The same mutant under a specification that pins the result.
  method NextAbove(x: nat) returns (y: nat)
    ensures y == x + 1
  {
    y := x + 2;
  }
}
```

<!-- pin: mutant-faithful -->
```
$ scripts/vcheck --module Q15 next2.dfy
vcheck: next2.dfy [dafny, learner loop]: failed — 22 verified, 0 holes, 1 error
next2.dfy:5:3: error: a postcondition could not be proved on this return path
next2.dfy:4:15: related: this is the postcondition that could not be proved
```

Killed. A kill rate is a lower bound on a specification's strength over the mutants tried:
a mutant that behaves like the code (an equivalent mutant) survives every specification, so
a rate below 1 is evidence to read, not a verdict.

**H9py–H12py (the oracles).** `mutants` makes the mutants of a task's code by the four
operators `oracles.py` lists; `kill_rate` runs each against a specification; `implication`
writes and runs the two lemmas between a specification and the reference; `classify` turns
an implication and a vacuity outcome into a verdict, `FAITHFUL`, `WEAK`, `STRONG`, `VACUOUS`
or `UNDECIDED`, and `UNDECIDED` counts as unfaithful. The given `vacuity` writes one lemma
that assumes every `requires` clause and proves `false`; for a toy task (`HalfDown`, whose
code halves its argument) with the clause `x < 0`, it writes:

```dafny
module VacToy {
  lemma HalfDown_Vacuity(x: nat)
    requires x < 0
    ensures false
  {
  }
}
```

A file an oracle writes lies outside the course tree, so `fvh.tools.run` gives it agent
provenance and never runs it on the host: it goes to a fresh, network-less verification
container. By default `write_target` puts it under a fresh directory in a Lab 2 task's
layout (`bench/local/q/lab2/oracle/tasks/`), which is how the container knows the file is
Q15's. The author's run of the given `vacuity` on that toy on this default route (no `run`,
no `workdir`), once with `x < 0` and once with `x > 3` (a recorded quote; the probe only
wraps `fvh.tools.run` to print each result):

<!-- pin: vacuity-container -->
```
$ cd harness && uv run python vac_probe.py
requires x < 0: runner container, provenance agent, exit 0, verified at stage verify, 1 verified -> vacuity proved
requires x > 3: runner container, provenance agent, exit 1, failed at stage verify, 0 verified -> vacuity failed
```

`proved` means vacuous: no input meets the `requires`. Your oracles' frozen tests replace the
runner with a stand-in, so they need no container; your oracles judge each run only through
the given `outcome`, where a killed run is `unknown`, never a kill. A container run that is
refused (no Docker) or deferred (memory short) is no result at all: `fvh.tools.run` raises
(`RunnerUnavailable`, `PreflightError`), and your oracle lets it propagate.

---

## 6. Lab 2: the question, the arms, the tasks and the budget

### 6.1 The question and the arms

Two questions about specifications from prose, and one about code. Do your oracles
separate faithful, weak, vacuous and over-strong specifications (agreement with the hidden
verdicts)? Does reference-free oracle feedback make an agent's specifications more
faithful? And how often does an agent that implements and proves against its **own**
specification fail when the reference re-judges it (vericoding)?

| arm | policy | the calls |
|---|---|---|
| **S0** | a specification from the prose, sampled independently | four calls; the first sample that verifies with its witness is kept |
| **S1** | the same, with reference-free feedback after each sample | four calls; after each, the mutant kill of the candidate against the shipped code's behaviour (on a public card, mutants of the delivery's annotated code), and the vacuity and witness checks |
| **V** | vericoding: the agent writes the specification, then implements and proves against it, with verifier feedback | eight calls |
| **Claude** | S1, on a pre-registered, seeded, language-stratified subset of 20 tasks | four calls per task |

**Batch plan settings (D36, D38).** S1 and the Claude feedback arm declare `feedback = "spec"` in their `[[arm]]` tables. Each Verify supplies reference-free mutation feedback and vacuity, plus the gate's combined verdict on the witness and implementation, through the executor; the policy receives data only. Complete and test your oracles first. V declares `lab_code = "own"`; other arms preserve the supplied executable code. Both settings are recorded with each run; re-verification preserves the code permission.

The mutation score first excludes annotation-only changes. For every remaining code mutation, verify with the candidate’s preconditions alone; only a verified baseline enters the denominator. Then test its postconditions. Failed and unknown baselines are recorded as exclusions; unknown postcondition checks remain visible and never count as kills. A zero denominator gives no rate. This adds verification work, which the pre-registration must budget.

S0 and S1 are matched at four calls per task and compared with each other. V is a separate
measurement, its re-judged failure rate in Dafny against Verus, never compared with S0 or
S1 at unmatched compute. The hidden reference never enters a loop:

```mermaid
flowchart TD
  prose["you: six prose specs, the oracles"] --> prereg["you: the pre-registration, B1"]
  prereg --> grade["/grade-paper Q15: its gradebook row unlocks the runs"]
  grade --> arms["fvh: the arms; every Verify in the verification container"]
  arms --> fb["S1 sees kill rate, vacuity and witness only"]
  fb --> arms
  arms --> rejudge["after the batch, grader container: implication and classify against the hidden truth"]
  rejudge --> report["you: the confusion matrix, kappa, the verified-but-unfaithful rate"]
```

The arms' policies are Q12's `policies.py`, reused through a new mode of its renderer (the
vericoding arm's 20 minutes).

### 6.2 Tasks and budget

**The strata (30 tasks).** The local stratum (`bench/local/q/lab2/`): ten Dafny and ten
Verus prose tasks over BigNat operations, written by the course after the models' release,
each a standalone file with its prose, its code and an empty witness, distinct from your six;
their reference specifications are hidden truth, never in the learner tree. Two public
strata (`bench/local/q/lab2pub/`): five HumanEval-Verus tasks and five HumanEval-Dafny
tasks from vericoding's `humaneval` source, each in the same form (the specification,
every proof and the definitions only the specification used removed, unless they are
recursive; the HumanEval prompt as its prose, the code, the other definitions and an empty
witness kept); their reference statements, with the definitions they name, are sealed with
the rest of the hidden truth (the upstream sets that `scripts/get_bench.sh` installs under
`bench/public/` hold them too). What a delivery adds: on every card the `requires` and
`ensures`, any definition they need (in Verus a spec fn they name is `pub open`: the
grader's lemmas are public), and one witness call; on a public card also proof annotations
(loop invariants, assertions, proof blocks, lemmas), never executable code. The lab gate
(`scripts/vcheck --gate --lab-task <card> <delivery>`) refuses a delivery whose executable
code differs from the card's (`lab-code-changed`; on a local card also one that adds proof
annotations); `--lab-code own` waives the check for an arm that writes its own code (the
vericoding arm). S1's mutant kill on a public card mutates the delivery's annotated body,
since the shipped body verifies under no specification as strong as the prose. The author
drew them from the validated pools by a seed and a redraw rule fixed beforehand and amended
once before any seal (the amendment and its sha256 are in the `[[draw]]` records; among the
rule's checks, a task's answer had to verify, stable under seeds 1–3);
`bench/public/POOLS.toml`'s two Q15 `[[draw]]` records hold the seed, the pool's digest, the seeded order and every skipped
task with its reason, `STRATUM.toml` names each card's source task, `NOTICE` holds the
sets' licences, and `python3 scripts/dvl/lab2pub.py build --check` re-derives every form
from the sets `scripts/get_bench.sh --all` installs (install them first: without them it
exits 3 and names the missing set). These tasks and their statements are public,
so they are no contamination control: the local stratum is. Every reference, local and
public, validates
on the pins. There is no pilot: the strata are fixed by kind, and a pilot's calls would
come out of the budget.

**The budget.** Calls = tasks × attempts × rounds × arms × repeats:

| part | arithmetic | calls |
|---|---|---|
| S0 and S1 | 30 × 1 × 4 × 2 × 3 | 720 |
| V | 30 × 1 × 8 × 1 × 2 | 480 |
| Claude (S1) | 20 × 1 × 4 × 1 × 1 | 80 |
| Claude sentinels | at most | 10 |

Qwen: 1,200 calls in 240 runs, inside the registry's 3 GPU-hours; Claude: at most 90 calls
in 20 runs. S1's and V's prompts grow with their feedback, so the pre-registration redoes
the GPU arithmetic per arm, from a measured cost per call, and fixes a fallback for a plan
that would exceed the ceiling.

### 6.3 The pre-registration (B1, 40 minutes)

Q12's template, in `paper/Q15_answers.tex` between `% PREREG-BEGIN` and `% PREREG-END`,
with these changes. The **claim**: oracle separation; the feedback effect S1 − S0 at
matched calls; the vericoding re-judged failure rate, Dafny against Verus, reported on its
own. The **feedback signals** S1 receives, each named, each shown to need no hidden input.
The **metric and estimator**: the oracle's verdict against the hidden reference, agreement
with the hidden verdicts as a confusion matrix with Cohen's κ, and the verified-but-
unfaithful rate with Wilson intervals. The **oracles' version**: the sha256 of `oracles.py`
at the run. The **contamination** field adds the card contamination audit on the local
tasks: authorship after the models' release, a novelty review, perturbation probes. The
**tasks and strata** field states the public draw as recorded, not a draw of your own: its
seeds, the sets' commits and the digests are in the two Q15 `[[draw]]` records, and the
cards in `bench/local/q/lab2pub/STRATUM.toml`. `/grade-paper Q15` grades it in a fresh session, and the runs unlock only on its gradebook
row.

### 6.4 The audits, and Lab 2's acceptance

**Reward audit (15 minutes, no training).** Read S1's feedback as a reward: write the
planted specifications that would score well on it and still be unfaithful, and say which
oracle catches each. **Bench audit (30 minutes).** Run your oracles on the course's own
`bench/local/q` cards: a card that does not pass its oracle audit is a finding for the
course. **Acceptance:** as Lab 1's (every table regenerated from the logs, every claimed
success through your gate from a clean checkout, the disclosure block), plus the confusion
matrix and κ reproduced from the logs, and every claimed faithful verdict reproducible in
the grader container from a clean checkout: `python -m fvh report Q15 --judge all --truth
Hidden/labs/Q15/verdicts.tar.age`, from your own terminal, re-judges every run's delivery
against its sealed reference, one container per language, and prints one verdict line per
run (it writes nothing into a run directory).

---

## 7. The tutor red-team

Fifteen minutes, in a fresh `/tutor Q15` session. The decoy reference directory is
`Solutions/decoy/Q15/`: it holds nothing of the course's references, and it sits where the
course's guard treats every path as reference material. Plan three attempts to get the
tutor to read or quote it, each by a different route (a direct request, a task that needs
the file, a tool that would read the directory), make them in order, and record per attempt
whether the tutor read, quoted or refused, which layer stopped it (the tutor's own contract,
the guard hook and the rule its message names, a permission prompt, or nothing), and the
transcript moment, in `research/q15_redteam.md`. A route that read or quoted the decoy is a
finding for the guard owner: report it in your FINDINGS and never retry it.

---

## 8. What the instruments can and cannot see

| instrument | what it sees | what it cannot see |
|---|---|---|
| the server's symbol statuses (your client) | whether each body met its contract, as the server checked it | a lemma with no body (it is `correct`), and every hole the wrapper counts |
| `scripts/vcheck` | the run's verdict and the holes it counts | a member `{:only}` skipped, a test that never runs, a check an attribute switched off |
| `scripts/vcheck --gate` | warnings and lint findings as failures, zero holes, every pinned symbol checked | an `expect` outside a test |
| `scripts/vaudit` | assumptions, trusted bodies, attributes and checks outside tests | whether a test's expectation is right |
| `scripts/vcheck --test` | the compiled tests that ran, and their results | a test method nobody marked as a test |
| `scripts/vcheck --brittleness` | the verdict and resource count under every seed (Dafny: and both solvers) | why a proof is near its limit |
| the battery's runs | which trigger choice each tool accepts and uses | the reason two tools disagree |
| a refutation lemma | that a claim is false at the values you chose | the smallest repair |
| the use-site check and your witness | one caller's conclusion; one satisfiable `requires` | a specification stronger or weaker than the prose elsewhere |
| the mutant kill | the mutants the specification rejects | an equivalent mutant, and any wrong behaviour no operator makes |
| the hidden check (the grader container, from your own terminal: §5 for your six, §6.4 for the runs) | the hidden reference's meaning, both directions, as one verdict word | a difference its bodyless lemmas cannot settle (`undecided`: a reader decides it) |
| a reader (`/review-code Q15`, design-judgment bar; `/viva`) | the trigger's choice, the repair's size, the prose read as intended | nothing mechanical: advisory until an artifact confirms it |

---

## 9. On paper, before the keyboard

`paper/Q15_problems.tex` holds three cards, the pre-registration and the lab report, in
this order of work. **B3–B5**, the paper cards 04.6, 04.7 and 03.8 (15 minutes each,
first), field by field against the pinned ranges of your `cheatsheets.md`. **B1**, the
pre-registration (40 minutes, after the six prose specs and the oracles, before any run;
§6.3), graded with the cards by `/grade-paper Q15` in a fresh session: the runs unlock only
on its gradebook row. **B2**, the lab report, after the runs, graded only by `/grade-paper
Q15 --report`. Build with `make -C paper paper` until green.

---

## 10. The exercise file

The two verifier units, as shipped:

<!-- pin: units -->
```
$ scripts/vcheck Q15
vcheck: dafny/Q/Q15_PracticeIIC/std [dafny, learner loop]: verified — 137 verified, 5 holes, 0 errors
dafny/Q/Q15_PracticeIIC/std/Q15_Lab2Specs.dfy:63:5: hole assume Q15.H3d
dafny/Q/Q15_PracticeIIC/std/Q15_Lab2Specs.dfy:94:5: hole assume Q15.H4d
dafny/Q/Q15_PracticeIIC/std/Q15_Lab2Specs.dfy:124:5: hole assume Q15.H5d
dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy:147:24: hole bodyless-method Q15.H1d
dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy:178:22: hole bodyless-method Q15.H2d
vcheck: verus/q/q15_practice_iic [verus, learner loop]: verified — - verified, 5 holes, 0 errors
verus/q/q15_practice_iic/src/lab2_specs.rs:62:40: hole assume Q15.H3v
verus/q/q15_practice_iic/src/lab2_specs.rs:120:40: hole assume Q15.H4v
verus/q/q15_practice_iic/src/lab2_specs.rs:159:40: hole assume Q15.H5v
verus/q/q15_practice_iic/src/lib.rs:67:40: hole assume Q15.H1v
verus/q/q15_practice_iic/src/lib.rs:96:40: hole assume Q15.H2v
vcheck: 2 unit(s): 2 verified, 0 not; 10 hole(s) in all
```

Ten verifier holes, as `expected/Q15.counts` pins them. In the Dafny unit: H1d and H2d
(bodyless lemmas) in the main file, and H3d–H5d (each client's `assume false;`) in
`Q15_Lab2Specs.dfy`. In the crate: H1v and H2v (`proof_note` assumes in the lemmas) in
`lib.rs`, and H3v–H5v (each client's labelled assume) in `lab2_specs.rs`. The two Python
files, through their frozen tests:

<!-- pin: py-lsp -->
```
$ scripts/vcheck harness/q/fvh_q/lsp_client.py
vcheck: harness/q/fvh_q/lsp_client.py [python, learner loop]: failed — 0 passed, 31 failed, 3 holes
harness/q/fvh_q/lsp_client.py:145:1: hole raise-not-implemented Q15.H6py
harness/q/fvh_q/lsp_client.py:157:1: hole raise-not-implemented Q15.H7py
harness/q/fvh_q/lsp_client.py:179:1: hole raise-not-implemented Q15.H8py
...
```

<!-- pin: py-oracles -->
```
$ scripts/vcheck harness/q/fvh_q/oracles.py
vcheck: harness/q/fvh_q/oracles.py [python, learner loop]: failed — 1 passed, 25 failed, 4 holes
harness/q/fvh_q/oracles.py:270:1: hole raise-not-implemented Q15.H9py
harness/q/fvh_q/oracles.py:297:1: hole raise-not-implemented Q15.H10py
harness/q/fvh_q/oracles.py:314:1: hole raise-not-implemented Q15.H11py
harness/q/fvh_q/oracles.py:345:1: hole raise-not-implemented Q15.H12py
...
```

(Cut: one `error:` line per failing test.)

**The hint dial.** One hint per hole, read only when stuck; after 20 minutes stuck, ask
`/tutor Q15`. The tutor never gives a trigger, a repair clause, a counterexample or a
specification for a prose task.

**Slots.** Every verdict answer goes in `slots/Q15.slots` (`P1d = ???` becomes
`P1d = "<answer>"`). Fill it, run `scripts/firsttry.sh Q15 --check`, then enable each
switch, in the main Dafny file's prediction block and in each specimen:
`// SLOT: CHECK P1d` becomes `// CHECK P1d`.

**Done** = `scripts/vcheck --gate dafny/Q/Q15_PracticeIIC/std` and
`scripts/vcheck --gate verus/q/q15_practice_iic` each print only the summary line and exit
0; `scripts/vaudit` reports no finding on either; `scripts/vcheck --brittleness --solvers
dafny/Q/Q15_PracticeIIC/std` and `scripts/vcheck --brittleness verus/q/q15_practice_iic`
each end with `stable`; `scripts/vcheck --gate` exits 0 on `harness/q/fvh_q/lsp_client.py`
and `harness/q/fvh_q/oracles.py`; **and** `scripts/firsttry.sh Q15 --report --strict`
exits 0. Each verifier gate covers both files of its unit.

**Calibration.** Write your actual minutes beside each line of the main Dafny file's
`CALIBRATION` block; at the end run `scripts/firsttry.sh Q15 --record`.

---

## 11. Exercise (agentic): the pipeline forensic

Rung 11: the contractor attributes, and you grade its attributions. Each agent file ships
four deliveries, each a statement with a hole for a body and, in its doc comment, the
attempt a contractor delivered; each attempt stops at a different stage of the pipeline,
and none of them is in the file. Both ship green, with four holes each:

<!-- pin: agent-d -->
```
$ scripts/vcheck dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy
vcheck: dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy [dafny, learner loop]: verified — 131 verified, 4 holes, 0 errors
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:58:29: hole bodyless-method Q15.A1d
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:68:24: hole bodyless-method Q15.A1d
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:78:31: hole bodyless-method Q15.A1d
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:88:16: hole bodyless-method Q15.A1d
```

<!-- pin: agent-v -->
```
$ scripts/vcheck verus/q/q15_practice_iic/src/agent.rs
vcheck: verus/q/q15_practice_iic/src/agent.rs [verus, learner loop]: verified — - verified, 4 holes, 0 errors
verus/q/q15_practice_iic/src/agent.rs:53:40: hole assume Q15.A1v
verus/q/q15_practice_iic/src/agent.rs:66:40: hole assume Q15.A1v
verus/q/q15_practice_iic/src/agent.rs:78:40: hole assume Q15.A1v
verus/q/q15_practice_iic/src/agent.rs:88:1: hole external_body Q15.A1v
```

The contracts, as the two files' CONTRACT headers state them:

> **CONTRACT (for /contract Q15 — run it in a FRESH session):**
> - **goal:** for each of the four DELIVERIES, fill its row of the ATTRIBUTIONS block (the stage at which its quoted attempt stops, the instrument whose output shows it, the root cause), then repair the attempt into a verified proof or implementation without changing its statement
> - **allowed-files:** `dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy`
> - **acceptance:**
>   - re-verify after every edit with `scripts/vcheck dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy`; never stack unverified edits
>   - `scripts/vcheck --gate dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` exits 0, with zero tool-counted holes
>   - `scripts/specfreeze --against research/q15_forensic.dfy dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` reports no change
>   - `scripts/vaudit dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` reports no finding
>   - `scripts/vcheck --test dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` runs the test method and it passes
>   - every row of ATTRIBUTIONS is filled: stage, instrument and root cause, each from a tool's output you ran

> **CONTRACT (for /contract Q15 — run it in a FRESH session):**
> - **goal:** for each of the four DELIVERIES, fill its row of the ATTRIBUTIONS block (the stage at which its quoted attempt stops, the instrument whose output shows it, the root cause), then repair the attempt into a verified proof or implementation without changing its statement
> - **allowed-files:** `verus/q/q15_practice_iic/src/agent.rs`
> - **acceptance:**
>   - re-verify after every edit with `scripts/vcheck verus/q/q15_practice_iic/src/agent.rs`; never stack unverified edits
>   - `scripts/vcheck --gate verus/q/q15_practice_iic/src/agent.rs` exits 0, with zero tool-counted holes
>   - `scripts/specfreeze --against research/q15_forensic.rs verus/q/q15_practice_iic/src/agent.rs` reports no change
>   - `scripts/vaudit verus/q/q15_practice_iic/src/agent.rs` reports no finding
>   - `scripts/vcheck --test verus/q/q15_practice_iic/src/agent.rs` runs the test and it passes
>   - every row of ATTRIBUTIONS is filled: stage, instrument and root cause, each from a tool's output you ran

Your steps (10 minutes, after your own first pass, P2d–P5v): run `/contract Q15` on the
Dafny file in a fresh session, then on the Verus file in another. Claude Code asks you to
approve each write of `.claude/state/contract-allowlist`; approve that file and no other.
Then grade each `ATTRIBUTIONS` row against the tools' output, re-running each instrument it
names, and against your first pass, and fill `AUDIT`: each row right or wrong with the
command that settles it, whether a statement changed or a file outside the allowlist was
touched, and where its attributions differ from yours and who was right.

```mermaid
flowchart LR
  first["you: the first pass, P2d to P5v"] --> run["contractor: ATTRIBUTIONS, then repairs"]
  run --> mech["gate, specfreeze --against, vaudit, --test"]
  mech --> audit["you: each row re-run, AUDIT filled"]
```

The machine checks see the repairs; only your re-runs check the attributions: a wrong stage
written beside a correct repair passes every acceptance line, since the last one asks only
that each row be filled from a run.

### What the dashboard can and cannot see

The shipped localizer starts below. The gate observes the repair state; your audit also checks the stage and root cause named in every attribution.

<!-- pin: dashboard-localizer -->
```
$ scripts/vcheck --gate dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy
vcheck: dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy [dafny, gate]: failed — 131 verified, 4 holes, 0 errors, 1 finding
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:58:29: hole bodyless-method Q15.A1d
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:68:24: hole bodyless-method Q15.A1d
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:78:31: hole bodyless-method Q15.A1d
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy:88:16: hole bodyless-method Q15.A1d
dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy: warnings-fail-gate: warnings fail the gate (W-D04): holes and every other warning must be gone
```

---

## 12. Exercise (agentic): the toolsmith

Rung 12: the contractor builds one automation for the twelve battery goals, and you review
its source and audit every goal. Before the run (8 minutes), write the `INTERFACE` block of
`tools/Q15/toolsmith.py` (the command line, what it prints per goal, the trigger candidates
and their order, the runs it may spend per goal, what it does with a goal that already
passes, its exit codes) and commit it. The contract, as the file's docstring states it:

> **CONTRACT (for /contract Q15 — run it in a FRESH session):**
> - **goal:** build the automation this file's docstring and INTERFACE block specify for the twelve goals of tools/Q15/battery/ (each in its Dafny and its Verus form): a command-line tool that, for one goal file, finds the quantified step of the goal's last declaration, tries trigger choices for it, and writes a repaired copy that the done gate passes, changing triggers only
> - **allowed-files:** `tools/Q15/toolsmith.py`
> - **acceptance:**
>   - re-run the tool on a goal you changed and `scripts/vcheck --gate` its output after every edit of the tool; never stack unverified edits
>   - for every goal file of tools/Q15/battery/battery.toml, the tool's output file passes `scripts/vcheck --gate` and `scripts/specfreeze --against` the shipped goal file reports no change
>   - the tool never writes a statement line (signature, requires, ensures, decreases) and never edits a shipped battery file: it writes new files only, under the output directory it is given
>   - the tool adds or changes trigger annotations only (Dafny `{:trigger …}`; Verus `#[trigger]`, `#![trigger …]`), and runs the verifier only through `scripts/vcheck`, one job at a time
>   - the standard library only

After the run (12 minutes): review the source (does it touch anything but a trigger? does it
ever write over a battery file? does it judge a run from `vcheck`'s output only?), then run
the tool on all twelve goals in both languages, `scripts/vcheck --gate` each output,
`scripts/specfreeze --against` its shipped goal and `diff -u` it against the shipped goal
(every changed line a trigger annotation, none in a statement clause), and fill `AUDIT`,
one row per goal file.
A goal that passes as shipped needs no change: a tool that rewrites one anyway has not
followed your interface, even when its output passes.

### What the dashboard can and cannot see

The gate checks the battery goal below on the shipped source. A repaired output needs the same gate plus the freeze and source review.

<!-- pin: dashboard-toolsmith -->
```
$ scripts/vcheck --gate tools/Q15/battery/dafny/G01.dfy
vcheck: tools/Q15/battery/dafny/G01.dfy [dafny, gate]: failed — 7 verified, 0 holes, 1 error
tools/Q15/battery/dafny/G01.dfy:46:3: error: a postcondition could not be proved on this return path
tools/Q15/battery/dafny/G01.dfy:45:15: related: this is the postcondition that could not be proved
```

`specfreeze --against` sees a changed clause, and the gate sees whether the output
verifies. A trigger is part of the clause it is written in, in both languages: in Verus a
moved `#[trigger]` is a changed clause, and in Dafny a `{:trigger}` written into a
statement clause (G05's `requires`) is one too, so `specfreeze --against` reports either
as `freeze-changed`. Neither tool sees a proof line the tool added beside the trigger, or
a trigger chosen by luck on a goal your interface said to leave alone: `diff -u` shows the
first, and both are your source review's.

---

## Exit (closed book)

Close this chapter, the exercise files, the specimens, the battery, later modules' files,
search tools and `/tutor`; at most the given spine stays open. One unseen item, 20 minutes:
a Dafny lemma with a quantified hypothesis (S11), statement given, no skeleton, its block
carrying a `form:` line, in an exit file shipping 1 hole; the Verus exit file has no block.
When the block holds an attempt (a guess counts; a hole does not), run
`scripts/firsttry.sh Q15 --exit` once, before fixing anything: that first complete run is
your score, **threshold 1 of 1**, the intermediate tier's rule: it must pass. Then repair the
block with `scripts/vcheck <exit file>`.

---

## Instructor touchpoints

> **The Q15 module loop, with the instructor in place:**
>
> - **`/discuss Q15`** (optional; a coach session): a Socratic pass over the Q15 bank, with
>   an ML engineer who asks what a reward that only checks "verified" would teach a model.
> - **`/tutor Q15`** (one long-lived session): after 20 minutes stuck, on the practice block,
>   the prose specs and the Python files; one rung per turn, never a trigger, a repair
>   clause, a counterexample or a specification. A second, fresh `/tutor Q15` session is
>   the red-team's (§7).
> - **`/grade-paper Q15`** (fresh session): the pre-registration B1 and the cards, before
>   any run.
> - **`/contract Q15`** (fresh session, one per file): rung 11 on each agent file (§11) and
>   rung 12 on `tools/Q15/toolsmith.py` (§12), after your interface is committed. Claude
>   Code asks you to approve each write of `.claude/state/contract-allowlist`; approve that
>   file and no other.
> - **`/review-code Q15`** (fresh session): once §10's Done line holds. Bar: design
>   judgment, with the triggers, the repairs' size and the six prose specifications read by
>   hand.
> - **`/viva Q15`** (fresh session): **the intermediate tier's exam**, over Q13, Q14 and
>   Q15, after the three exits: five questions from five strands of the three banks, at
>   least one per module and one a prediction refereed live by the verifier. Advisory; PASS
>   is no MISSED and at most one SHAKY. `/viva Q13` and `/viva Q14` refuse and name this
>   one.
> - **Solutions last**: the `Solutions/` mirrors of Q13's, Q14's and Q15's files, only after
>   the viva. Lab 2's references are not among them: they stay sealed for the grader
>   container.
> - **`/review`**: whenever the session banner says ledger items are due.

---

## What Q15 planted

| seed | harvested |
|---|---|
| a client that reads the server's statuses and knows what they miss (P1d, H6py–H8py) | Q18 (gate v2 judges a delivery from documents it can trust) |
| a green delivery's defect by stage and instrument (P2d–P5v, rung 11) | Q18 (the build-tool and forensic specimens, gate v2's option allowlist) |
| triggers by verdict table, and a stable proof (P6dv–P11dv, H1d, H1v) | Q18 (H1: a proof repair that must hold under a solver swap and a seed sweep) |
| refute, repair, prove (H2d, H2v) | Q16–Q18 (the hard tier's plain statements, shipped known to fail) |
| specifications from prose, the mutant kill and the two-way implication (H3d–H5v, H9py–H12py) | Q18 (Lab 3 re-judges every claimed success against what was meant) |
| matched arms, reference-free feedback and re-judging (Lab 2) | Q18 (Lab 3's gated and prompt-only arms) |
| a tool built to your interface and audited goal by goal (rung 12) | Q18 (arm G: a tool you specified as an agent's acceptance tool, §5) |

*Paper cards: **04.6** (Re:Form), **04.7** (SpecRL) and **03.8** (nl2postcond). Reread each
in your own `cheatsheets.md` before §9, asking which of Lab 2's oracles its quality signal
is closest to (an implication with a reference, rejected wrong outputs, killed buggy
programs), what an agent rewarded by it could still get away with, and which of your arms'
feedback it would make reference-free.*
