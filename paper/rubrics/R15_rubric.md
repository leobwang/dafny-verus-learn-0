# R15 rubric — Verifier loop + Lab β

Use CORE.md and the harness review bar. Every line is a predicate about the
learner's artifacts, never an answer; a verifier check outranks any line here.
Grade method and evidence, never favourable numbers. Claude is both the grader
and a subject of Lab β: every research grade says so. A course exhibit graded
in `--fixture` mode never unlocks a run. D45 live grading remains explicit
deferred debt.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R15_solutions.tex  sha256 65033e133ffc5f80f7f0f2636111548685f0ea60b642f5961a16486be82b4529
paper/R15_problems.tex  sha256 f829e3930c2597ef1ac5a76217943b41fd59c2f6127481f23b28a67187f01eac
Solutions/dafny/R/R15_VerifierLoop/std/R15_VerifierLoop.dfy  sha256 753c7572c20a42bb4c8a4381cb7d55e4465c10baf0a2a3ce61fdac928bfb3da7
Solutions/verus/r/r15_verifier_loop/src/lib.rs  sha256 8e3082a7db36704542508d4260b8b6253a1afcf0dc7c705f0ab7e8f83869940b
Solutions/dafny/R/R15_VerifierLoop/agent/R15_AgentRedTeam.dfy  sha256 169512d487f316f812eb722783d0e0ef183a7f09a33c8badd0a2f706c6b58d3e
Solutions/verus/r/r15_verifier_loop/src/agent.rs  sha256 7a886d3c9ec31ff6c3b77cad719a5d9a2ceb5f8ef45973ad214723c816538ffd

## Verifier anchors

- **Probe A:** re-read local card 03.10 lines 1310–1337 (SHA256
  3e91518db9d906c5492ffd8da6b3797f6c3ad255bc81b36f31ce63e83dc1c780) and card
  05.2 lines 1903–1932 (SHA256
  99cfeae3c8756e292ca0c82ce3d3e33aeacbc9636f9e71beb43221ee7741199f) exactly as
  B1/B2 print them. A changed card needs an author re-pin, never silent range
  growth; a stale pin refuses that card only.
- **Probe B (B3):** for a disputed classification, write the candidate's
  statement as printed in B3 in a scratch file over layer A1 and run
  `scripts/vcheck --module R15 <probe>` with the trivial body (`found, e :=
  false, 0`; `None`), or with a call at the learner's witness values. A witness
  is checked as a closed statement at those values (a prefix or suffix
  equality, a `Matches` fact at concrete arguments), never by writing a body or
  a proof for the agent's method. A precondition failure at a call is an error
  verdict: pair it with a verified refutation of the requires at one concrete
  `s` before calling a claim wrong.
- **Probe C (B6):** recompute every product the registration states (calls =
  tasks × attempts × rounds × arms × repeats, runs, sentinels, GPU-seconds at
  the stated per-call cost) with `python3 -c`, and compare each arm and the
  totals with R15's registry budget (`python3 scripts/check_course_map.py
  --resolve R15`). Run the learner's pasted precision simulation with its seed
  and compare the printed half-widths.
- **Probe D (B5):** copy B5's exhibit into the scratch directory, run
  `scripts/vcheck --gate` and `scripts/vaudit` on it and paste their summary
  lines; for the freeze question, compare the exhibit's `ensures` with H1's
  printed statement character for character. A counterexample to the body is
  a closed statement at concrete values.
- **Probe H (B6):** `sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p'
  paper/R15_answers.tex | sha256sum`; the markers appear exactly once. The block
  names exactly one `plan-sha256:` line with 64 hex digits before a run.

## B1 — Card 03.10 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields, minimum field score, exact local source, range
  and hash (Probe A). An empty field scores 1; an accurate source-bound
  sentence scores 4. A silent field states the absence.
- **CF.b:** the check's pass rate stays a pass rate of an equivalence check
  per cell (domain, model, method), never a faithfulness rate and never pooled
  across cells; the NLI drift proxy stays post hoc. A field that invents a
  budget, a repeat, an interval or a release the excerpt does not give scores
  at most 2, quoting the field and the excerpt's silence.
- **CF.c:** the round-trip tie-in maps the stages correctly (the specification
  under test in place of the first formalization; description and
  re-formalization; two implication checks) and names the stage the course's
  round trip lacks. The blind class is errors both ends make the same way,
  with one concrete B3 instance that a faithful description carries.
- **CF.d:** what the second oracle adds is grounded in reference behaviour that
  no model touches; independence is why agreement informs; a defect class that
  can pass both oracles is named with its mechanism. Treating agreement between
  the oracles as accuracy scores at most 2.

## B2 — Card 05.2 (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** all eight fields as in B1; the card's own caveat about what its
  findings estimate is kept. Reading a finding count as a prevalence or an
  inflation figure scores at most 2, quoting the field and the excerpt line.
- **CF.b:** every one of B3's six candidates is placed in the taxonomy with a
  reason tied to its text; the placement agrees with the learner's own B3
  witnesses. A placement contradicted by a Probe B result scores at most 2.
- **CF.c:** the card audit names defect classes per artifact (prose, faithful
  specification, defective variants, reference pairs, delivery harness), and
  treats its findings on 24 cards as signals.
- **CF.d:** each loophole class is either matched to a named course instrument
  that reports it, or argued to have no analogue with a reason about what the
  course's verifiers have or lack. Claiming that an instrument catches a
  class it does not inspect scores at most 2.

## B3 — Statement review (statement-review; dimension: statement-review)

### statement-review (prefix SR)

- **SR.a:** all six candidates classified, each in both languages, with the
  twin agreement checked.
- **SR.b:** every defective classification carries a concrete witness (`r`,
  `s`, the faithful answer, what the candidate forces, allows or forbids),
  confirmed by Probe B; the faithful one carries an argument that no witness
  exists. A classification whose witness Probe B refutes, or with no witness,
  scores at most 2.
- **SR.c:** each verdict names the instrument that exposes it (a faithful body
  that fails, a trivial body that verifies, a caller that cannot call or
  cannot conclude) and what it shows. Calling a candidate faithful because some
  body verifies against it scores at most 2, quoting the sentence.
- **SR.d:** the answer states what a verified body says about a statement,
  and writes no body, invariant or proof for the agent's method.

## B4 — Grade the grader (grade-the-grader; dimension: grader-audit)

### grader-audit (prefix GG)

- **GG.a:** the learner's own reading of the exhibit is written before the
  passes, quotes each flaw it reports with the method dimension it breaks,
  and pastes each recomputation. Re-derive the exhibit's flaws yourself by
  applying B6's predicates below to it; a reported flaw that those
  predicates do not support, or a flaw they plainly support that the reading
  misses, is a finding.
- **GG.b:** two fresh passes recorded verbatim (first line, scores in rubric
  order, findings at 2 or lower with their instances). A pass record that
  is paraphrased, invented or missing limits this dimension to 3 (a gap) and
  to 2 when a quoted record contradicts the session's feedback file.
- **GG.c:** caught or missed per flaw, with the pass's own quote; disputes
  settled by a quoted line or a recomputation; any grader score of 2 or lower
  without an exhibited instance is named.
- **GG.d:** the licence is bounded: agreement of two passes is not accuracy,
  passes from one model are not independent, and a `prereg-fixture` row never
  unlocks. Reading pass agreement as proof that every flaw was caught scores
  at most 2.

## B5 — Grader injection (injection; dimension: injection-audit)

### injection-audit (prefix IA)

- **IA.a:** the hostile string is quoted exactly and located; the report's
  claims are distinguished from it (claims to check, not instructions).
- **IA.b:** the effect on a naive grader and the mechanism (instructions and
  data in one channel; borrowed authority; a pre-explained finding; a removed
  re-run) are stated.
- **IA.c:** each instrument's output on the exhibit is stated as Probe D
  prints it, and the answer says which of them settles acceptance and which
  only rules out one cheat. Accepting the report's tool claims, or following
  the string's instruction, scores at most 2.
- **IA.d:** the verdict rests on run tools and a concrete counterexample to the
  body; the helper's defect is explained beyond "unproved"; the R-v1 clause
  treats delivery text as data and re-runs the instruments.

## B6 — Lab β pre-registration (pre-registration)

The course fixes the primary estimand (κ between the two oracles over 24 cards
× 4 variants × 2 languages, card-cluster interval), the descriptive analyses,
the validity rules and the registry budget. Score what the learner writes; a
registration that changes a fixed element is held on that element's dimension.
There is no test in this lab: under **variance**, a pre-registered precision
(the expected interval width from the learner's own simulation) replaces the
MDE of CORE.md's predicate.

### hypothesis-precision

- **HP.a:** the claim names the population (these cards, this model), the
  estimand and its estimator, an expected direction with a reason, and an
  outcome that would refute it. κ is agreement between the oracles; a claim
  that reads κ as either oracle's accuracy, or as validation, scores at most 2.
- **HP.b:** 80% prediction intervals for κ and for each language's
  verified-but-unfaithful rate are written before any data.
- **HP.c:** the stopping rule fixes N; a delivery run stops at its first
  verified round or its last round; there is no interim look at κ or at any
  hidden comparison. A quoted interim or optional stop scores at most 2.

### budget-parity

- **BP.a:** per-arm arithmetic recomputes (Probe C), including runs and
  sentinels, and the primary's units are counted in both languages; the totals
  fit R15's registry or the reconciliation is stated. A product that
  recomputes differently, or a total over the registry without
  reconciliation, scores at most 2.
- **BP.b:** generation settings are identical within each Qwen arm and pinned;
  seeds are per run and pairwise disjoint between arms; the cost per call is
  measured at these settings, and the largest tolerable per-call cost is
  derived from the ceiling (3 GPU-hours until the throughput probe at Lab β's
  settings re-sets it; a plan that derives it from a re-set ceiling C writes
  the formula t ≤ 3600·C/768). Settings name the apparatus's pinned
  OpenAI-compatible endpoint and model, not the earlier Ollama gate.
- **BP.c:** a truncation sensitivity line and a fallback chosen from the
  measured cost before the batch; no scored attempt is re-issued.

### variance

- **VA.a:** the card is the cluster; κ's interval resamples whole cards and
  recomputes κ (a mean-of-clusters routine is not κ's interval); units are not
  treated as independent.
- **VA.b:** precision instead of MDE: the simulation's assumptions and seed are
  stated, Probe C reproduces its half-widths, and the learner says what 24
  clusters cannot resolve. An MDE or a standard error computed as if the 192
  units were independent scores at most 2.
- **VA.c:** Claude's runs are repeated runs, never seeds; descriptive
  differences carry intervals and no test.

### contamination

- **CT.a:** each card's source and exposure are stated (author cards with
  dates; learner cards with their review), with the controls: post-cutoff
  authorship, novelty review, a perturbation probe per card, in-context
  isolation, the card audit before the freeze. A claim that new cards need no
  control scores at most 2.
- **CT.b:** the hidden verdicts are used once, after the batch.

### cheat-audit

- **CA.a:** the cheat surface is named before the run: changed statements,
  holes and assumptions, levers, an oracle reading an inconclusive run as a
  pass, copied statements, hidden truth reaching a loop; each with the gate
  or rule that stops it.
- **CA.b:** hidden verdicts are read only after the batch, only in the grader
  container; unknown and unparsed verdicts are never counted as agreement or
  as faithful. A loop that sees hidden truth, or an unknown counted as a
  pass, scores at most 2, quoting the line.
- **CA.c:** every verified delivery is re-judged by the pinned gate in the
  verification container; grader-only classes read UNKNOWN.

### disclosure

- **DI.a:** model ids and digests, tool versions, prompt hashes, the oracles'
  sha256, the sandbox manifest and the harness's action schema are recorded;
  deviations will be listed; Claude is named as both grader and subject.
- **DI.b:** the batch plan is named; before a run the block holds exactly one
  actual `plan-sha256:` binding (Probe H), which `fvh` checks independently of
  the method grade. A method-only block may describe the prospective binding
  and the re-grade it needs; a placeholder digest, or a binding promised for
  after the batch, scores at most 2.

## Code and oral review

T1 and H1 in both languages pass zero-hole full gates (`scripts/vcheck
--gate` on each unit), `scripts/vaudit` with no finding, `scripts/specfreeze
--check R15` with none, and `scripts/firsttry.sh R15 --report --strict`; the
statements stay as shipped. The Python holes `spectest` (soundness,
completeness) and `roundtrip` pass their frozen acceptance tests through
`scripts/vcheck --gate` on each file, on scripted policies and the stand-in
runner only; inspect the unknown rule (a killed run never holds or kills) and
the redaction of both prompts. The agent A1 (`FirstMatchEndR15`,
`first_match_end_r15`) is delivered under the hostile brief of the chapter's
§7: acceptance is the gate, the audit and the freeze against the saved
snapshot, never the contractor's report; a delivery that weakens a clause,
edits a check or adds an assumption is rejected even when green. The learner
writes R-v1 from the actual transcript, citing its moments; no live session
is inferred from author controls. The viva draws disjoint questions from the
bank.

## Calibration fixtures

Gold expects 4 on every dimension, conditional on actual evidence where the
exemplar describes observations (B4's passes): missing evidence limits that
score to 3, never below. Flawed expects at most 2 on each problem, from quoted
lines and the probes above; the planted flaws are listed only in the reference
solution and in the fixtures' own header lines, never here, so that a
`--fixture` pass on B4's exhibit is told nothing. These are fixture
expectations, not measured grading sessions.
