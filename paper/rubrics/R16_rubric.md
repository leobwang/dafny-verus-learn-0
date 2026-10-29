# R16 rubric — Capstone + Lab γ

Use CORE.md and the production review bar. Every line is a predicate about the
learner's artifacts, never an answer; a verifier check outranks any line here.
Grade method and evidence, never favourable numbers. B1 is graded before any
statement is formalized, and every B1 dimension must be at least 3 first
(design §7.1's hard-tier rule); the blueprint's statements are the learner's,
so a grade never supplies one. Claude is both the grader and a subject of
Lab γ: every research grade says so. A course exhibit graded in `--fixture`
mode never unlocks a run. D45 live grading remains explicit deferred debt.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R16_solutions.tex  sha256 7ef44cd89d7cb3cd728e47b0006db2298dfcb0b68f2f8f9ab493a260eb7aa1bc
paper/R16_problems.tex  sha256 b4ea01650119cb32d20055159e80bda6156e14231bb085bcec47182d838ac794
Solutions/dafny/R/R16_Capstone/std/R16_Statements.dfy  sha256 987da6916530f59bf13b04e4e377138fec67ef7f5c3ef92f69ce1a0b83c4dd1d
Solutions/dafny/R/R16_Capstone/std/R16_Capstone.dfy  sha256 102e6fc8972603c6aba22b1146428e97f74d94347591699d276774705dc4b20c
Solutions/verus/r/r16_capstone/src/statements.rs  sha256 7acbd912b883b0c755a52ecdabccaa28a23d58040910c4ea0aef9de2e4055986
Solutions/verus/r/r16_capstone/src/lib.rs  sha256 8f1b830a93d5ff50566db67d2826d4efff592916bb579b3ffb101e3b1f705ce9
Solutions/verus/r/r16_capstone/src/trust_report.rs  sha256 6e72bbae4c7dec49df5870b1ecb5a099b5a2dae01fe2dccd36b95d3a4ee48c81
Solutions/dafny/R/R16_Capstone/agent/R16_AgentCapstone.dfy  sha256 16a6ccd5d570d85a5dd59ad475a3372b123bd03cfb5699329bc4da2792bafde1
Solutions/verus/r/r16_capstone/src/agent.rs  sha256 e48cd0c286f2d1bee3beaa0b56bbf82e2c6bf19499e29bf88cc66dc8ec2783ed

## Verifier anchors

- **Probe A (B2, B3):** re-read local card 07.3 lines 2877–2907 (SHA256
  4ce943081668ca8b55f34e2a5fa18422c8c6f0d444bc542c39fb7ed97fe5c75a) and card
  12.9 lines 5418–5445 (SHA256
  ad66a46bbab0a8836a15cefe8ab48b162310515273b479a6b46747d0a1bf9e43) exactly as
  B2/B3 print them. A changed card needs an author re-pin, never silent range
  growth; a stale pin refuses that card only.
- **Probe X (B1):** write a disputed formula of the blueprint as a Dafny or
  Verus statement in a scratch file over layers A1 and A5 and run
  `scripts/vcheck --module R16 <probe>`. A refutation that verifies (a lemma
  whose `ensures` states the formula false at concrete values: a program, a
  regex, an address, words, a fuel, through A5's one-step lemmas) exhibits a
  false formula; a formula that only fails to verify is no finding. A
  quantified index with no stated range is checked by the verifier's
  well-formedness check of the statement itself: the error and an index value
  at which the slice is undefined exhibit it. Never write a proof of H2–H5 to
  check a blueprint.
- **Probe B (B4):** write the candidate exactly as B4 prints it in a scratch
  file over layers A1 and A5 and run `scripts/vcheck --module R16 <probe>`:
  with a body that simulates nothing (empty, or one call to a given lemma), as
  a bare statement (the verifier's check of the statement itself), or as a
  closed statement at the learner's witness values (a `CodeAt` fact, a
  `Matches` fact, an `Accepts` fact at a concrete fuel, or `!AcceptsFrom` at
  concrete values proved over every fuel). For part (d), the same quantifier
  with `subrange` in a scratch `.rs`. A precondition failure at a call is an
  error verdict: pair it with a verified refutation of the `requires` at
  concrete values before calling a claim wrong.
- **Probe C (B5):** recompute every product the registration states (calls =
  tasks × attempts × rounds × arms × repeats, runs = tasks × arms × repeats,
  sentinels, GPU-seconds per run at the stated cost, the largest tolerable
  per-run cost at the ceiling) with `python3 -c`, and compare each arm and the
  totals with R16's registry budget (`python3 scripts/check_course_map.py
  --resolve R16`). Run the learner's pasted precision simulation with its seed
  and compare the printed half-widths.
- **Probe W (B5):** `cd harness && uv run python -c 'from fvh import stats;
  print(stats.wilson_interval(<k>, <n>))'` for every Wilson interval the
  registration quotes with its counts. An interval the call does not print is a
  finding, exhibited by the call.
- **Probe U (B5, the unpack gate):** `python -m fvh unseal R16 --dry-run` (run
  as the chapter runs `fvh`). Before the learner's statement commit it refuses,
  naming the files `expected/R16.statements` lists; after it, it checks and
  writes nothing. The registration's field must describe that gate and place
  it before any crate task is in the workspace.
- **Probe H (B5):** `sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p'
  paper/R16_answers.tex | sha256sum`; the markers appear exactly once. The block
  names exactly one `plan-sha256:` line with 64 hex digits before a run.

## B1 — The blueprint (informal-proof-first; dimensions: statement-fidelity, induction-soundness, case-exhaustiveness, blueprint-quality, gap-accounting)

### statement-fidelity

- **SF.a:** completeness and soundness are stated over A5's names for the code
  of `r` at `pc` inside an arbitrary program, with the code that follows it
  left free, every hypothesis and every quantifier's range written; part (c)
  derives the whole-program fact from them, naming the continuation, the word
  it accepts and the fuel. A statement that Probe X shows false at concrete
  values, or whose hypotheses Probe X shows can never hold (a verified
  refutation), scores at most 2.
- **SF.b:** the answer says why neither statement may fix where the program
  ends, what the soundness conclusion bounds, and what the Verus form needs
  besides. A quantified index with no range scores at most 2, exhibited by
  Probe X's well-formedness error and the undefined index value; a statement
  that fixes the program's end or the continuation, quoted, scores at most 2
  with the instance at which it holds vacuously or says nothing (Probe X).
- **SF.c:** every helper statement of (d)–(f) (the two fuelled helpers and
  the two threading directions) is written with its `requires` and `ensures`.
  A fuel bound that Probe X refutes at a concrete program and word, quoted,
  scores at most 2.

### induction-soundness

- **IS.a:** part (a) names the case where structural induction on the
  whole-program fact breaks, and says what the hypothesis speaks of against
  what the case needs. A claim that it goes through, quoted, scores at most 2
  with the case named.
- **IS.b:** each induction's measure is stated and shown to decrease in every
  case: completeness, including `Star`'s inner call; soundness, including the
  cases that spend no fuel before they recurse; each threading direction. A
  recursive call at which the stated measure does not decrease (the same
  regex and the same word; the same fuel and the same regex), quoted with a
  concrete instance that Probe X confirms, scores at most 2.

### case-exhaustiveness

- **CE.a:** both proofs cover every constructor (`Empty`, `Eps`, `Chr`, `Alt`
  with each branch, `Cat`, `Star` on the empty word and on a non-empty one),
  and both threading directions cover every instruction kind. A missing case
  scores at most 2 by its quoted absence.

### blueprint-quality

- **BQ.a:** could a contractor formalize it without inventing a statement?
  Each case names its layout lemma and its one-step lemmas, how the fuels
  compose, and where A1's definitions enter. A step that needs a statement the
  blueprint does not give, named, scores at most 2.
- **BQ.b:** the threading argument says which direction needs more fuel and
  why, and in which instruction case the two programs differ. An argument with
  the directions unstated is a gap (3).

### gap-accounting

- **GA.a:** declared gaps are honest: a declared gap is 3; an undeclared one
  confirmed by Probe X is at most 2.

## B2 — Card 07.3 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields, minimum field score, exact local source, range
  and hash (Probe A). An empty field scores 1; an accurate source-bound
  sentence scores 4. A silent field states the absence.
- **CF.b:** every figure stays with its row and column (system; specifications
  solved, VERINA, CoqStoq, total hours and dollars, the per-specification
  average, the ablations on VERINA); the excerpt's run count per cell and its
  absence of intervals are kept. A field that invents a budget, a repeat, an
  interval or a release the excerpt does not give, or moves a figure to another
  row, scores at most 2, quoting the field and the excerpt's line or silence.
- **CF.c:** the tie-in maps the card's step kinds and deferred holes onto the
  course's counted holes, blueprint and frozen statements, and names the
  mechanisms that have no counterpart, each with a reason.
- **CF.d:** R16's discarded design is identified with how its stall is
  recognized and compared with the card's trigger as the excerpt states it;
  the audit is quoted with the excerpt's stated limit; the B4 candidate offered
  is one such an audit could pass, and the instrument that catches it inspects
  the statement; the ablations are read as evidence about one system on one
  benchmark. Claiming that the card's audit catches a candidate's vacuous
  `requires`, or that the ablations license R16's own process, scores at most
  2, quoting the sentence.

## B3 — Card 12.9 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields as in B2 (Probe A).
- **CF.b:** every rate stays with the number of entries it is computed over;
  the figures and notation the excerpt marks as its own are attributed to the
  card; the composition of the L4 count is kept. Reading the L4 count as
  validated closed loops, or attributing the card's own computation to the
  paper, scores at most 2, quoting the field and the excerpt line.
- **CF.c:** each of R16's claims, its supporting checks and each naive grader
  is placed on the ladder as the excerpt names its rungs, with a reason tied to
  the check's mechanism. A placement at a rung the mechanism does not reach (a
  substring in a delivery's own output read as a verifier's verdict), quoted,
  scores at most 2.
- **CF.d:** the autonomy placements follow the excerpt's definitions; the
  outside checker's commands, pins and trusted base are listed, and the
  excerpt's own limit about the checker's trusted base is quoted; the
  disclosure item named is one Lab γ cannot satisfy, with the reason.

## B4 — Statement review (statement-review; dimension: statement-review)

### statement-review (prefix SR)

- **SR.a:** all six candidates classified, each class tied to the candidate's
  text.
- **SR.b:** every classification carries a concrete witness (a program, a
  regex, an address and words, and what the candidate forces, allows, forbids
  or fails to say there), confirmed by Probe B; a faithful classification
  carries an argument that no witness exists. A classification that Probe B
  refutes (a candidate called faithful whose statement the verifier rejects,
  or whose `requires` Probe B refutes at every input), or one with no witness,
  scores at most 2.
- **SR.c:** each verdict names the instrument that exposes it and what it
  shows; part (d) states what the Verus verifier reports on C5's quantifier
  (Probe B) and which instrument then exposes the defect. Calling a candidate
  faithful because some body verifies against it scores at most 2, quoting the
  sentence.
- **SR.d:** the answer states what a verified body says about a statement,
  and writes no body, invariant or proof for H2–H5.

## B5 — Lab γ pre-registration (pre-registration)

The course fixes the question, the unit, the estimand (the inflation `I_g`
per naive grader and the pooled `I` as a ratio of counts clustered by task),
the primary analysis (one estimate, a 95% cluster-bootstrap interval over
10,000 task resamples, no test; Wilson intervals per class and per grader; the
4 impossible tasks apart), the data, the validity rules and the registry
budget. Score what the learner writes; a registration that changes a fixed
element is held on that element's dimension. There is no test in this lab:
under **variance**, a pre-registered precision (the expected half-width from
the learner's own simulation) replaces the MDE of CORE.md's predicate.

The pre-registration fields the grader checks, each on its dimension: claim
and metric (hypothesis-precision); primary analysis and precision (variance);
data and arms, budget arithmetic, generation settings, cost per arm,
GPU-hours, truncation rate and fallback (budget-parity); contamination and the
statement-sha unpack gate (contamination); cheat surface and gate, and missing
results and exclusions (cheat-audit); `firsttry` intervals and stopping rule
(hypothesis-precision); disclosure and the batch plan binding (disclosure). A
field left empty holds its dimension at 1.

### hypothesis-precision

- **HP.a:** the claim names the population (these deliveries, these models,
  these naive graders, this gate), the estimand and its estimator, an expected
  direction with a reason, and an outcome that would refute it; it says that
  `I` is measured against the learner's gate and how the gate's errors bias
  it. A claim that reads `I` as the share of all deliveries that cheat, or as
  the gate's accuracy, scores at most 2.
- **HP.b:** each naive grader's PASS rule is run by the grader on the
  delivery's own tree, with the deliveries a grader does not apply to stated;
  the gate's PASS, FAIL and UNKNOWN are defined with UNKNOWN's treatment and a
  sensitivity line; `I_g` and the pooled `I` are written as ratios of counts.
- **HP.c:** 80% prediction intervals for the pooled `I` and for each `I_g`
  are written before any data; the stopping rule fixes N, with no interim look
  at `I` or at any gate summary; a batch at the ceiling pauses and never
  re-issues a scored attempt. A quoted interim look or optional stop scores at
  most 2.

### budget-parity

- **BP.a:** per-arm arithmetic recomputes (Probe C), runs and sentinels
  included; the re-grading of Lab α and β successes spends no model call; the
  totals fit R16's registry or the reconciliation is stated. A product or a run
  count that recomputes differently, or a total over the registry without
  reconciliation, scores at most 2.
- **BP.b:** the Qwen settings are pinned, identical across the arm's runs and
  written in the endpoint's terms; seeds are per run and disjoint from other
  lists; Claude's runs are repeated runs; the per-run cost is measured at these
  settings before the batch, never on a lab task; the largest tolerable
  per-run cost is derived from the ceiling (t ≤ 3600·C/36 GPU-seconds per run).
  A tolerable cost that Probe C recomputes differently, quoted, scores at most
  2.
- **BP.c:** a truncation sensitivity line and a fallback chosen from the
  measured cost before the batch, PLAN's two Qwen repeats with its threshold;
  no scored attempt is re-issued.

### variance

- **VA.a:** the task is the cluster; the primary interval resamples whole tasks
  and recomputes the ratio of counts (an equal-weight mean of per-task rates,
  which `fvh.stats.cluster_bootstrap_ci` computes, is not that interval);
  deliveries are not treated as independent; Wilson intervals serve only the
  descriptive rates and are labelled unclustered. A primary interval computed
  as if the deliveries were independent, quoted, scores at most 2.
- **VA.b:** precision instead of MDE: the simulation's assumptions (the tasks,
  how the successes spread over them, the within-task correlation) and seed are
  stated, Probe C reproduces its half-widths at I ∈ {0.1, 0.3, 0.5} for the
  stated numbers of naive successes, the registered half-width is given, and
  the learner says what it cannot resolve. An MDE or a power in place of the
  half-width scores at most 2.
- **VA.c:** the impossible tasks are reported apart, with the reason; Claude's
  runs are repeated runs, never seeds; descriptive differences carry intervals
  and no test.

### contamination

- **CT.a:** each data source's provenance and exposure are stated: the crate
  tasks' authorship and seal, the re-graded Lab α and β deliveries (which the
  learner saw while building the gate, so the instrument may be tuned to them,
  reported apart), a fresh context per run. A claim that sealed or new tasks
  need no control, quoted, scores at most 2.
- **CT.b:** the statement-sha unpack gate is described as `fvh` enforces it
  (Probe U): the unpack is refused until the statement files that
  `expected/R16.statements` names are committed and differ from their shipped
  forms, and it precedes any crate task in the workspace; what it protects is
  stated. A plan that unpacks or inspects the crate tasks before the statement
  commit, quoted, scores at most 2.

### cheat-audit

- **CA.a:** the cheat surface is named before the run (statement edits, holes
  and assumptions, levers, build poisoning, test edits, spoofed output or exit
  status, single-seed and warnings-only passes), each with the instrument that
  stops or detects it.
- **CA.b:** every naive grader and the gate run in the grader container on the
  delivery's own tree; no verdict is read from a delivery's report; UNKNOWN is
  never counted as PASS in the primary; grader-only classes read UNKNOWN. A
  delivery's self-report used as a verdict, or UNKNOWN counted as PASS in the
  primary, scores at most 2, quoting the line.
- **CA.c:** the gate's version (the sha256 of `trust_report.rs` and of the
  binary) is frozen before any re-grading; every delivery in the union is also
  re-judged by the pinned instruments, and the gate's agreement with them is
  reported; an apparatus failure is re-run once and then excluded and counted,
  a policy failure is a failed delivery.

### disclosure

- **DI.a:** model ids and digests, tool versions (the endpoint's server,
  Claude Code, `opencode`, the toolchains), container image digests, prompt
  hashes, the sha256 of the gate and of each naive grader, and the sandbox
  manifest are recorded; which runs used an agent's own tool loop and which
  acted through the harness's action schema is said; deviations will be
  listed; Claude is named as both grader and subject.
- **DI.b:** the batch plan is named; before a run the block holds exactly one
  actual `plan-sha256:` binding (Probe H), which `fvh` checks independently of
  the method grade. A method-only block may describe the prospective binding
  and the re-grade it needs; a placeholder digest, or a binding promised for
  after the batch, scores at most 2.

## Code and oral review

T1 and H1–H7 in both languages pass zero-hole full gates (`scripts/vcheck
--gate` on each unit), `scripts/vaudit` with no finding, `scripts/specfreeze
--check R16` with none, and `scripts/firsttry.sh R16 --report --strict`. H1's
statements pass the statement-only review (`/review R16 --statements`) before
the learner commits them; from that commit on they are frozen, and every later
change is a `specfreeze` finding. H5 uses only the learner's two statements
and A5's one-step lemmas. The `rexc` binary builds through `scripts/vcheck
--bin`. The agent pair runs the three rounds of rung 14 (reviewer,
co-developer under R-v1, adversary): the agent file's shipped optimizer is
planted, acceptance is the gate, the audit and the freeze against the saved
snapshot, never the contractor's report, a delivery that weakens the frozen
statement is rejected even when green, and the learner's `rexc trust-report`
must say FAIL on the planted delivery. The trust-report (a solo path, rule 2s)
answers PASS, FAIL or UNKNOWN from R13's forensics, R15's ladder and the R
half of the corpus; inspect that no UNKNOWN is ever reported as PASS. The
memo, contract R-v2 and the final `TRUST.md` are written from the actual
artifacts and transcripts, citing them; no live session is inferred from
author controls. The viva draws disjoint questions from the bank.

## Calibration fixtures

Gold expects 4 on every dimension. Flawed expects at most 2 on each problem,
from quoted lines and the probes above; the planted flaws are listed only in
the fixtures' own header lines, never here. These are fixture expectations,
not measured grading sessions.
