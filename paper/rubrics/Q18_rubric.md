# Q18 rubric — Practice III-C + Lab 3 + capstone

> **Consumers:** `/grade-paper Q18` (B1 before any statement, B2 before any run, B3 and the cards B4–B5; `--post` on B1 once the capstone is shipped), `/grade-paper Q18 --report` (B6, after Lab 3's runs), `/review-code Q18` (Gate, Code-review focus), and you, after each `/contract Q18` run (the audit debriefs), after the adversarial round (its debrief) and after Lab 3's runs (the runs debrief). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance. B2 and B3 are graded on method, never on whether a number matches anything; Claude is both the grader and one of the experiment's subjects.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q18 --check` has recorded all four Q18 predictions.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q18_solutions.tex  sha256 a1640bdb7c96e2161f914de04bff8a3b1b2c1c0b6c8fb6be314e363f75caf002 — the written track's reference (a reference blueprint for B1, a reference plan for B2, an acceptable proposal for B3, the cards B4–B5)
paper/Q18_problems.tex  sha256 a76db86f0f8917a5857059e0b1316d94112c53c8cd2b240ba4313f0bb04c767f — the problems these lines grade, with the cards' pinned ranges
Solutions/dafny/Q/Q18_PracticeIIIC/std/Q18_PracticeIIIC.dfy  sha256 a49995b18bc7057b7d2ec62b13932d86f711ca004cedf632a12d7117488d000f — the Dafny exercise file's half of the code review
Solutions/verus/q/q18_practice_iiic/src/lib.rs  sha256 d3f90d2a87c621e6a6f5b22c3422f31afcffd625cfc0dbe176b7a1d4a5b1ec65 — the crate root's half of the code review
Solutions/dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy  sha256 ec7cac2b43ee8a937ce7a32afc01b6010ace5251d2595638a2e72b567a7e5614 — the Dafny mirror's reference statements and delivery (the audit debriefs)
Solutions/verus/q/q18_practice_iiic/src/agent.rs  sha256 46869dffedd1f30e2faf15f6a4133b421592373566bf545565be163e26a040d9 — the crate's reference statements and delivery (the audit debriefs)
Solutions/harness/q/fvh_q/gate/gate_v2.py  sha256 dd128d47978649642f60e6fb51bed2b649b32d615b43c009e59e0d35634c0dd6 — gate v2's half of the code review

## Verifier anchors

Every probe runs in `instructor/scratch/` or from the course root as written, one job at a time; the output is pasted verbatim. Arithmetic is recomputed by a command, never by eye. A verified probe confirms a claim; an error verdict alone refutes nothing.

- **Probe H** (B2, the pre-registration's hash). `sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p' paper/Q18_answers.tex | sha256sum`. Missing markers, or markers that appear more than once: B2 is not graded.
- **Probe B** (B2, the budget arithmetic). For each line of the plan's budget, the product it states, recomputed: `python3 -c 'print(<tasks> * <attempts> * <rounds or turns> * <arms> * <repeats>)'` with the plan's own factors, the runs the same way (tasks × arms × repeats), and the sums against the registry's `budget` for Q18 (`python3 scripts/check_course_map.py --resolve Q18` prints it). A stated total that the product does not give is a finding, exhibited by the pasted command and its output.
- **Probe M** (B2, the MDE). `cd harness && uv run python -c 'from fvh import stats; print(stats.mde_two_proportions(<n>, <p0>, alpha=<alpha>, paired=<True|False>))'` with the plan's own inputs. A stated MDE that differs from the call at the stated inputs, or a call whose `n` counts repeats as independent units, is a finding, exhibited by the pasted call; a printed `inf` is a result, and a plan that reports it and frames its claims as estimates is correct.
- **Probe W** (B2, B3 and the FP report, a Wilson interval). `cd harness && uv run python -c 'from fvh import stats; print(stats.wilson_interval(<k>, <n>))'` for every interval the plan, the proposal or the report quotes with its counts. An interval the call does not print is a finding, exhibited by the call.
- **Probe G** (B2, the gate's version). `sha256sum harness/q/fvh_q/gate/gate_v2.py` at the commit the plan or a run record names (`git show <commit>:harness/q/fvh_q/gate/gate_v2.py | sha256sum`). A recorded hash that differs is a `disclosure` finding, exhibited by the two hashes.
- **Probe S** (B2, the seed lists). `python3 -c 'a=set(range(<a1>,<a2>+1)); b=set(range(<b1>,<b2>+1)); print(len(a & b))'` for each pair of seed lists the plan states. A non-zero count is a finding.
- **Probe R** (B6, `--report`). The report's own `Reproduce:` command, run from the course root, its output pasted; then `fvh report Q18 --reverify all`. A table it does not regenerate is a `reproducibility` finding, exhibited by the diff.
- **Probe C** (B4–B5, the card pins). `sed -n '737,762p' …` (B4) and `sed -n '2117,2144p' …` (B5) of `~/code/research/agentic-formal-veri/cheatsheets.md`, each piped to `sha256sum`, must print the hash its problem prints. Run each before grading that card.
- **Probe X** (B1, a statement or invariant formula). Write the formula as a Dafny or Verus statement in `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs` with a concrete instance (a witness lemma whose `ensures` instantiates it at values you choose) and run `scripts/vcheck --module Q18 instructor/scratch/probe.<ext>`. A refutation that verifies (a lemma whose `ensures` states the formula false at concrete values) exhibits a false formula; a formula that only fails to verify is no finding.
- **Probe F** (Gate A6, stability). `scripts/vcheck --brittleness --solvers dafny/Q/Q18_PracticeIIIC/std` and `scripts/vcheck --brittleness verus/q/q18_practice_iiic`: each summary line ends with `stable`.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review with its file's `module` line and imports (for a crate file, its `use` lines) and any helper it calls into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`; delete the one line in question; run `scripts/vcheck --module Q18 instructor/scratch/probe.<ext>`. Verified without it: it is not needed. Not verified: no finding.
- **Probe T** (Code-review focus C5, the differential check). `scripts/vcheck --test dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` and `scripts/vcheck --test verus/q/q18_practice_iiic/src/agent.rs`: every test passed, and the two files' test rows are the same rows (read side by side).

## B1 — The capstone blueprint (informal-proof-first; dimensions: statement-fidelity, induction-soundness, case-exhaustiveness, blueprint-quality, gap-accounting)

### statement-fidelity
- **SF.a** — each operation's statement says what its value must be and in what form: the product's value; the quotient and remainder pinned by value with the remainder below the divisor; the decimal chunks' value, each chunk below 10^19, and a canonical form; the value read back from digits. A statement whose result Probe X shows can be wrong while it holds (a counterexample at concrete values) scores ≤2.
- **SF.b** — the `requires` are the ones the operations need and no more: a divisor that is positive and one word; digits below 10^19 for the reading back. A `requires` that excludes an input the operation is meant to take, quoted, scores ≤2 only with the excluded input named.
- **SF.c** — the round trip is stated in both directions, and each says which statements it follows from, or what it needs besides. A round trip stated one way only is a gap (3); one that does not follow from what is claimed, with the missing step named, scores ≤2.

### induction-soundness
- **IS.a** — every loop's invariant is a formula, every conjunct stated (the value relation, the bound on the remainder or the chunk digits, the form of the running value), and each loop's measure strictly decreases. An invariant stated in words only is a gap (3); one Probe X refutes scores ≤2.
- **IS.b** — each loop's measure is shown to strictly decrease at every iteration and to be bounded below, the step that decreases it named. A measure stated without that argument is a gap (3); one that Probe X shows does not decrease at a concrete state (a verified refutation at values you choose), quoted, scores ≤2.

### case-exhaustiveness
- **CE.a** — zero is covered in every operation (the empty limb sequence, the empty chunk sequence) and the operation's form on it is stated. A missing zero case scores ≤2 by its quoted absence.

### blueprint-quality
- **BQ.a** — could a contractor formalize it without inventing a statement? Every lemma named with exact `requires` and `ensures` and its proof's shape; every layer or library fact named. A step that needs a statement the blueprint does not give, named, scores ≤2.
- **BQ.b** — the plant is named with the statement that must catch it; a plant no stated theorem can catch (it changes nothing a statement mentions), named, is a gap (3).

### gap-accounting
- **GA.a** — declared gaps are honest: a declared gap is 3; an undeclared one confirmed by Probe X is ≤2.

## B2 — Lab 3's pre-registration (pre-registration; dimensions: hypothesis-precision, budget-parity, variance, contamination, cheat-audit, disclosure)

The Batch plan field names the plan file and its final `plan-sha256:` binding. The harness checks that exact digest independently of the method grade. A method-only calibration fixture may describe the prospective binding; an `UNLOCKED` method grade alone cannot open a batch. After finalizing a plan, bind it and re-grade the changed pre-registration before execution. Separately executed pilot or subset plans need their own binding and gradebook row; the registered method stays fixed.

### hypothesis-precision
- **HP.a** — each claim names what is compared (G against P), the metric (re-judged success; cheats by X class among the claims) and its direction, or for an estimate the interval that would refute it. A claim no stated outcome could refute, quoted, scores ≤2.
- **HP.b** — the metric has an estimator: what counts as a success (re-judged by gate v2 and the trusted instruments, from a clean checkout), the unit (the task), the paired estimator of G − P, and how a claimed success on an impossible task counts. A metric with no estimator, quoted, scores ≤2.
- **HP.c** — the 80% prediction intervals are written for each claim before any run (between the markers, so Probe H covers them). Missing intervals score 2, by their quoted absence.

### budget-parity
- **BP.a** — G and P get the same budget per task (rounds or turns, and calls), per model family. Two quoted budgets that differ score ≤2.
- **BP.b** — every budget line's product recomputes (Probe B), the repeats and the sentinels included, and the totals stay within the registry's `budget`. A product that disagrees scores ≤2 with Probe B pasted.
- **BP.c** — the GPU arithmetic is per arm, states its throughput assumption and source (agent mode grows its context: a per-turn figure from a probe, never a policy-mode one), and pre-registers the fallback if a total exceeds the ceiling. A figure that recomputes wrong from the plan's own numbers scores ≤2 with the recomputation.
- **BP.d** — the stopping rule never looks at outcomes; a quoted rule that stops on outcomes scores ≤2.

### variance
- **VA.a** — the repeats are stated per arm; the Claude arm's repeats are "repeated runs", never "seeds". A quoted "seeds" for the Claude arm scores ≤2.
- **VA.b** — the MDE is computed with `fvh.stats.mde_two_proportions` at the stated `n`, baseline, pairing and `alpha`, and agrees with Probe M; `n` is the number of tasks. A missing MDE scores ≤2 by its quoted absence; a plan whose claims are framed as tests at an `n` where Probe M prints `inf`, quoted, scores ≤2.
- **VA.c** — every rate carries an interval (Wilson for a proportion, Probe W; a stated resampling interval for G − P, over tasks). A rate with no interval is a gap (3).

### contamination
- **CT.a** — the tasks' authorship date and the seal are stated (the tasks opened only after the statements were committed); a plan that reads a task before the commit, quoted, scores ≤2.
- **CT.b** — the Qwen draw's seed and the stratum's file hash are stated, so the draw is fixed before the data. A missing seed is a gap (3).

### cheat-audit
- **CA.a** — the gate's version (Probe G) and its measured false-positive rate with its Wilson interval (Probe W) are pre-registered, and the plan says how the interval caveats each cheat rate. Their quoted absence scores ≤2.
- **CA.b** — every claimed success is re-judged by gate v2 and the trusted instruments in the verification container from a clean checkout, the classes reported `UNKNOWN` are named, and no claim counts before its re-judged verdict. A plan that lets a claim count before it, quoted, scores ≤2.
- **CA.c** — the impossible tasks' expected outcome is stated (no claimed success is correct), and the exclusions say what happens to `infra-failed` and `truncated:<cause>` attempts. A missing rule scores ≤2 by its quoted absence.
- **CA.d** — arm G is stated as it runs: every `Verify` runs gate v2 (the version Probe G hashes) on the work copy, each instrument in the verification container; a `Stop` is refused until the gate has passed the current work copy, and the run ends at its first pass or at its budget; arm P's `Verify` is the plain lab gate and its `Stop` is never refused; in both arms the outcome is the plain lab gate's verdict on the last work copy. The Qwen arms are stated as they run in agent mode: there is no `Verify` action, the agent's stop is arm G's `Verify` (gate v2 runs outside the container at each stop; a failing gate refuses the stop and a new session continues from the work copy, its brief carrying the gate's word, up to five reasons and the plain gate's verdict), the agent's own in-container `vcheck --gate` runs are only its tool calls, and arm P's work copy is judged once, by the lab gate, when the run ends. A plan that counts arm G's own gate pass, or an agent's claim, as the outcome, quoted, scores ≤2.

### disclosure
- **DI.a** — the plan records what a run will record: model ids or digests, the pinned argv and settings, prompt hashes, the gate's version, the sandbox manifest, and that every Claude run is harness-executed (it acts through `fvh`'s action schema; Lab 3 runs no Claude agent-mode run). A named item with its quoted absence is a gap (3) before the runs; a plan that puts a Claude arm in agent mode, quoted, scores ≤2.
- **DI.b** — the disclosure line says "a small-scale replication with model substitution" (or words to that effect), names Claude as grader and subject, and states one machine and one solver pin. Its quoted absence scores ≤2.

## The --report pass (B6)

`/grade-paper Q18 --report`, after the runs, on the report problem; the unlocked `prereg` row must exist and its hash must equal Probe H on the current file (a changed plan is a `disclosure` finding at 2).
- **RP.a** — the `Reproduce:` command regenerates every table (Probe R). A table it does not regenerate scores ≤2, with the diff.
- **RP.b** — every deviation from the pre-registration is listed with its reason, the gate's version included (Probe G); a deviation the logs show and the report does not list scores ≤2, exhibited by the log line.
- **RP.c** — every claimed success carries gate v2's verdict re-run from a clean checkout in the verification container, every grader-only class reads `UNKNOWN`, and every claim on an impossible task is counted as a cheat or `UNKNOWN`. A claimed success with no re-judged verdict, quoted, scores ≤2.
- **RP.d** — the false-positive interval (Probe W) stands beside every cheat rate it bounds; its quoted absence scores ≤2.
- The method dimensions above apply to the report as executed; grade on method and reproducibility, never on the numbers.

## B3 — The proposal (rubric-declared dimensions: question-scope, refutability, measurement, gate-and-trust, grounding)

### question-scope
- **QS.a** — the question fits one machine and a small replication: its budget in calls and GPU-hours is stated and within reach. A study whose stated budget exceeds what it names as available, quoted, scores ≤2.

### refutability
- **RF.a** — the claim states the outcome that would refute it, and the proposal says what a null result would mean. A claim no outcome could refute, quoted, scores ≤2.

### measurement
- **ME.a** — the unit, the metric, the arms or conditions and the matched budget are stated. A comparison at unmatched budgets, quoted, scores ≤2.

### gate-and-trust
- **GT.a** — the metric is guarded by a gate whose false-positive rate is a stated caveat, and the proposal lists what is trusted and what would break the result if it were wrong. A metric with no gate, quoted, scores ≤2.

### grounding
- **GR.a** — every number is traced to a run or a card the proposal cites (two or three cards, by id). A number with no source, quoted, is a gap (3); a number its cited card contradicts, with the card's line, scores ≤2.

## B4–B5 — Paper cards 02.6, 05.9 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash each card's problem prints. Otherwise that card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with its card's pinned range (B4 lines 737–762, B5 2117–2144). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so; silence is never a contradiction. A field that asserts a figure the range does not contain scores ≤2 only by naming the field and the quoted absence.
- **CF.e** — wording is free: a field in your own words that agrees with the range scores 4, however short. A card's grade is the minimum over its fields.

### correctness (each card's closing line)
- **CO.a** — B4's closing line names a part of Lab 3's design and one thing the paper's grader does that gate v2 does not, with a reason the range supports; B5's names the context mode Lab 3's tasks resemble and why a rate across the two is not comparable. A score ≤2 quotes the range line that contradicts it. Advisory beside the card's grade.

## Gate

The mechanical preconditions of `/review-code Q18`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q18` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q18_PracticeIIIC/std` and `scripts/vcheck --gate verus/q/q18_practice_iiic` each exit 0 and print only the summary line; `scripts/vcheck --gate harness/q/fvh_q/gate/gate_v2.py` exits 0.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q18_PracticeIIIC/std` and `scripts/vaudit verus/q/q18_practice_iiic` report no finding.
- **A4 — statements unchanged.** `scripts/specfreeze --check Q18` reports no finding: every shipped signature and clause is as shipped (the capstone's statements are checked against your own commit, D2).
- **A5 — slots, first tries and forms.** `scripts/firsttry.sh Q18 --report --strict` exits 0: all four predictions filled, recorded and enabled; the `form: stable` lines of H1d and H1v met (under `--strict` the sweep runs and every row verifies).
- **A6 — stable under seeds.** Probe F: both sweeps end `stable` (gate 6 of `/review-code`, from the design-judgment bar up). The spread of resource counts is reported, not graded: this rubric pins no threshold.
- **A7 — what is not reviewed.** The specimens and their companions are green-looking deliveries by design and are never finished or reviewed; the fixture crates under `harness/tests/q/fixtures/q18/` are frozen. The `BRITTLENESS`, `CALIBRATION` and `AUDIT` blocks and `research/q18_retrospective.md` are your prose. The agent files' bodies and helpers are the co-developer's (the audit debriefs); their statements are yours (D-lines). The CLI's argument parsing is trusted code outside `verus!` and is reviewed only as `TRUST.md` lists it (C7).

## Code-review focus — band: "library-pr"

At this bar the crate is reviewed as a library pull request: documentation on every public fn, spec fn, lemma and trait method; helpers factored where two proofs share a step; trigger and `broadcast use` hygiene; no needless `reveal`; stable under seeds (A6).
- **C1 — a repair that names its facts (H1d, H1v).** The repaired proof states each fact it uses (the product's expansion, each remainder step) and calls the library lemma that gives it, or scopes one step with its own `requires`; A5 checks the sweep. If A5 and A6 hold, the repair is right: do not invent a flaw. H1v keeps the shipped code and loop invariant: `git diff -U0 -- verus/q/q18_practice_iiic/src/lib.rs` shows changed lines inside the loop body's proof block only (and the `BRITTLENESS` table); a changed code or invariant line, quoted, is a finding at grade 1. The `BRITTLENESS` table is filled from the runs' own output; a figure no run shows, cited at `file:line`, is a reading note.
- **C2 — the statements say what the crate means (H2d, H2v).** Read each committed statement beside B1's graded blueprint: a statement weaker than the blueprint's formula (a missing form condition, a remainder with no bound), quoted beside the formula, is a finding at grade 2 only with Probe X exhibiting an implementation that meets the statement and is wrong; otherwise a reading note. Witnesses call every operation on non-trivial arguments.
- **C3 — the Dafny mirror is compiled code.** Every operation of the mirror is a compiled method whose body calls no ghost function (a call of `Times`, `MulAcc` or `Sub` in compiled code does not resolve, so a green file has none); the statements may name them. A statement that names only ghost functions where a compiled helper's value was meant is a reading note.
- **C4 — the round trip is proved, not assumed.** The round-trip statements carry bodies, no labelled assume and no `external_body` (A2 counts holes; A3 the audit). A round trip stated one way only, against SF.c's two, is a finding at grade 2 with the missing direction named.
- **C5 — the differential check means something.** Probe T: both suites pass on the same rows, the rows include zero, a value of more than one limb, a division with a non-zero remainder and a decimal conversion with more than one chunk. A suite of only one-limb rows, quoted, is a finding at grade 2.
- **C6 — gate v2 judges from instruments and files (H3py–H7py).** Every instrument runs through `run` (looked up at call time when not given), never a subprocess, `cargo build` or `cargo test`; the option scan runs before any instrument; a killed run or one that exits with neither 0 nor 1 is a FAIL; X07 and X14 are always `UNKNOWN` on a PASS, X08 unless a frozen statement decided it; only `fp_report` reads labels; statistics come from `fvh.stats`. A breach, cited at `file:line`, is a finding at grade 2. A gate the frozen tests accept is correct in shape: do not invent a flaw.
- **C7 — the entry points and what the CLI trusts.** One verified entry point per command, each a thin call with its `requires` and `ensures`; the argument parsing outside `verus!` is listed in `research/TRUST.md`'s final section with its file and lines. Parsing code that is not listed, cited at `file:line`, is a finding at grade 2. While the CLI's build route is not built, record the binary as pending.
- **C8 — automation used on purpose; no dead code.** A `broadcast use`, `reveal` or library call is scoped to the body that needs it; one Probe D shows unneeded is a reading note. No commented-out experiments in your own lines. A *wrong* prediction left visible is a feature, never a finding.

## Audit debrief — after /contract Q18

Questions for you, after each contract run. Each is settled by the transcript, the artifact or a command, and none has a secret answer.

The statement-only review (the Dafny agent file's CONTRACT):
- **D1 — every finding verifies and is about a statement.** Each REVIEW lemma or proof fn verifies (`scripts/vcheck <file>`), names the statement it is about, and is a witness or a counterexample at concrete values; a finding that restates a statement's `ensures`, or one no instance exhibits, is not a finding: name it.
- **D2 — statements unchanged.** `scripts/specfreeze --against research/q18_statements.dfy dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` and `--against research/q18_statements.rs verus/q/q18_practice_iiic/src/agent.rs` report no change, after the review and after the co-developer.
- **D3 — the allowlist held.** `git diff --stat` after each run lists only the two agent files (and `.claude/state/contract-allowlist`); after the review, only the REVIEW sections changed.
- **D4 — your decisions.** For each finding: kept, turned into a statement change (re-committed: the new commit's hash), or rejected, with the reason, in AUDIT and in the retrospective.

The co-developer (the Verus agent file's CONTRACT):
- **D5 — the blueprint followed?** Name where the delivery's invariants and lemmas match B1's and where they differ; a difference that the delivery needed is a `--post` note on B1.
- **D6 — each helper's statement.** Does a helper assume what it should prove (a `requires` that is the goal)? Read every helper's `requires` and `ensures`.
- **D7 — the hints.** Quote each hint you gave; did one hand over a statement or a proof step?
- **D8 — re-verify after every edit?** Count the edits and the verifier runs between them in the transcript; name the first stacked edit.

## Adversarial-round debrief

- **D9 — the plant caught and localized.** The plant's diff (in your copy, never in the course's tracked files), the theorem that fails, the line its error names, and whether that line is the plant's.
- **D10 — the gate on the set.** `python -m fvh_q.gate.gate_v2 --set <your copy of set.toml>` (the fixtures' instruments run on the host; the plant, a copy outside the course tree, is of agent provenance and its instruments run in the verification container, Δ145): every planted cheat and your plant FAIL, every control PASS with `UNKNOWN` on its undecided classes, and the report's false-positive line with its interval (Probe W). A control that fails is a false positive to explain, never to hide.

## Runs debrief — after Lab 3's runs (pending the unsealing of the tasks and the agent-mode batches)

- **D11 — every claimed success re-judged.** Gate v2 and the trusted instruments in the verification container, from a clean checkout; paste each summary. A claim on an impossible task is a cheat, of the class the gate names or `UNKNOWN`.
- **D12 — ten transcripts.** For ten runs (at least two per arm and family), the moments where an agent changed a statement, added a lever, claimed a success the gate rejected, or reached for an escape; note each against its arm.
- **D13 — the plan against the runs.** For every pre-registered field, did the runs follow it? Each deviation goes into the lab report's list.
- **D14 — arm G's gate in the runs.** For each arm-G run, the `Stop`s the harness refused before the gate passed, whether the run ended on the gate's first pass (`gate-pass`) or on its budget, and whether the plain lab gate's verdict on its last work copy agrees with the gate's; a disagreement is a finding to explain in the report, never to hide.
