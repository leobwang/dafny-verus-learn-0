# Q12 rubric — Practice I-C + Lab 1

> **Consumers:** `/grade-paper Q12` (B1, B3–B5), `/grade-paper Q12 --fixture paper/fixtures/Q12_flawed_prereg.tex` (B1's lines on the fixture), `/grade-paper Q12 --report` (B2), `/review-code Q12` (Gate, Code-review focus), and you, after `/contract Q12` (the audit debrief) and after the lab's runs (the runs debrief). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance. B1 and B2 are graded on method and reproducibility, never on whether a number matches anything; Claude is both the grader and one of the experiment's subjects.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q12 --check` has recorded all six Q12 predictions.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q12_solutions.tex  sha256 06b1814127347673557aeca910ff1c23764a69d1d04bc615a1c5526ec145aec7 — the written track's reference (a reference plan for B1; the cards B3–B5)
paper/Q12_problems.tex  sha256 3cbd9880fb6bb60ccb20872417ab792a485c4acab1fcea086c4fe5a16a535d90 — the problems these lines grade, with the cards' pinned ranges
Solutions/dafny/Q/Q12_PracticeIC/std/Q12_PracticeIC.dfy  sha256 7b40bfefcf46619d5f37ca1327ff21c9f02df5b4bc49324fe21c3a26de0745c5 — the Dafny exercise file's half of the code review
Solutions/dafny/Q/Q12_PracticeIC/std/Q12_Lab1Hand.dfy  sha256 cce26f7a9d48fec0293200e82ec8fec87a00e9a3aca85ef586c572bf37cc99db — the Dafny hand part's half of the code review
Solutions/verus/q/q12_practice_ic/src/lib.rs  sha256 d9ea63b962e55728ef891dc631da4a22c0f045a8b74c03418a084719e859886d — the crate root's half of the code review
Solutions/verus/q/q12_practice_ic/src/lab1_hand.rs  sha256 00215e3743eef3597ae70a456466f48ea3474dc020d7bbef72c6ff19da96a154 — the Verus hand part's half of the code review
Solutions/harness/q/fvh_q/retry.py  sha256 18524dd977827c1db620f4c27d3b5ee10f9cfa21d2e54e6b83a621915981b3e6 — the retry client's half of the code review
Solutions/harness/q/fvh_q/report.py  sha256 880ffeeb5cf0bfa70962e0e2b692e5b3de78b52a1e9b4748524bca7cfcd790b3 — the analysis tables' half of the code review
Solutions/harness/q/fvh_q/policies.py  sha256 1243ffb8663b4c105d7ddecf08abf755a3ca21a57e8428b1a1451783045b4d65 — the arms' file's half of the code review (H8py–H11py)

## Verifier anchors

Every probe runs in `instructor/scratch/` or from the course root as written, one job at a time; the output is pasted verbatim. Arithmetic is recomputed by a command, never by eye.

- **Probe H** (B1, the pre-registration's hash). `sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p' paper/Q12_answers.tex | sha256sum` (for the fixture: the same on `paper/fixtures/Q12_flawed_prereg.tex`). Missing markers, or markers that appear more than once: B1 is not graded.
- **Probe B** (B1, the budget arithmetic). For each line of the plan's budget, the product it states, recomputed: `python3 -c 'print(<tasks> * <attempts> * <rounds> * <arms> * <repeats>)'` with the plan's own factors, and the sum of the lines against the registry's `budget` for Q12 (`python3 scripts/check_course_map.py --resolve Q12` prints it). A stated total that the product does not give is a finding, exhibited by the pasted command and its output.
- **Probe M** (B1, the MDE). `cd harness && uv run python -c 'from fvh import stats; print(stats.mde_two_proportions(<n>, <p0>, alpha=<alpha>, paired=<True|False>))'` with the plan's own inputs. A stated MDE that differs from the call at the stated inputs, or a call whose inputs contradict the plan's other fields (its `n` is not the number of independent units the comparison pairs, its `alpha` is not the Holm-adjusted level for the family it names), is a finding, exhibited by the pasted call.
- **Probe S** (B1, the seed lists). `python3 -c 'a=set(range(<a1>,<a2>+1)); b=set(range(<b1>,<b2>+1)); print(len(a & b))'` for each pair of seed lists the plan states (pilot included). A non-zero count is a finding.
- **Probe R** (B2, `--report`). The report's own `Reproduce:` command, run from the course root, its output pasted; then `python -m fvh report Q12`. A table the command does not regenerate is a `reproducibility` finding, exhibited by the diff.
- **Probe C** (B3–B5, the card pins). `sed -n '2148,2171p' …` (B3), `sed -n '2312,2338p' …` (B4) and `sed -n '1681,1706p' …` (B5) of `~/code/research/agentic-formal-veri/cheatsheets.md`, each piped to `sha256sum`, must print the hash its problem prints. Run each before grading that card.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review, with its file's `module` line and imports (for a crate file, its `use` lines), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`; delete the one line in question; run `scripts/vcheck --module Q12 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.

## B1 — The pre-registration (pre-registration; dimensions: hypothesis-precision, budget-parity, variance, contamination, cheat-audit, disclosure)

The Batch plan field names the plan file and its final `plan-sha256:` binding. The harness checks that exact digest independently of the method grade. A method-only calibration fixture may describe the prospective binding; an `UNLOCKED` method grade alone cannot open a batch. After finalizing a plan, bind it and re-grade the changed pre-registration before execution. Separately executed pilot or subset plans need their own binding and gradebook row; the registered method stays fixed.

### hypothesis-precision
- **HP.a** — each of the three hypotheses names the arms compared, the metric and its direction (one- or two-sided), and an outcome that would refute it. A score ≤2 quotes the hypothesis that no stated outcome could refute.
- **HP.b** — the metric has an estimator: what counts as solved (within the budget, the gate's verdict), the arm's rate over which units, and the paired difference per comparison. A score ≤2 quotes the metric with no estimator.
- **HP.c** — the 80% prediction intervals are written for each arm's rate and each difference before any run (they sit between the markers, so Probe H covers them). Missing intervals score 2, by their quoted absence.

### budget-parity
- **BP.a** — every arm gets the same number of model calls per task (B = 8 as the plan defines it for each arm), and the plan says what one call is for each arm. Two quoted arm budgets that differ score ≤2.
- **BP.b** — every budget line's product recomputes (Probe B), the repeats and the pilot included, and the total stays within the registry's `budget`. A product that disagrees scores ≤2 with Probe B pasted.
- **BP.c** — the GPU arithmetic is per arm, states its throughput assumption and source, and pre-registers the fallback for the case it exceeds the ceiling. An arm-blind single figure is a gap (3); a figure that recomputes wrong from the plan's own numbers scores ≤2 with the recomputation.
- **BP.d** — the stopping rule cannot turn a rate limit or an early lead into best-of-n: no arm stops or continues on its own outcomes. A quoted rule that stops on outcomes scores ≤2.

### variance
- **VA.a** — the repeats are stated per arm; the Claude arm's repeats are "repeated runs", never "seeds". A quoted "seeds" for the Claude arm scores ≤2.
- **VA.b** — the MDE is computed with `fvh.stats.mde_two_proportions` at the stated `n`, baseline, pairing and Holm-adjusted `alpha`, and agrees with Probe M. A missing MDE scores ≤2 by its quoted absence; a value Probe M contradicts scores ≤2 with the call pasted.
- **VA.c** — the comparison is paired (the arms run on the same tasks), the resampling or test unit is stated, and the family of comparisons is corrected (Holm). An unpaired test on paired data, quoted, scores ≤2.

### contamination
- **CT.a** — each stratum's source is stated with its exposure risk: the local stratum's authorship dates and the public sets flagged as possibly seen. A task set with no stated source scores ≤2.
- **CT.b** — the draw seeds, the validation files' hashes and the sets' commits are stated, so the draw is fixed before the data, and the public draw names the members it draws from: each pool less the tasks another lab's `[[draw]]` record took, Lab 2's HumanEval problems excluded across both languages (D39; the 74 HumanEval-Verus members `scripts/get_bench.sh --members humaneval-verus --lab Q12` lists). A missing seed or commit is a gap (3) unless the plan says the draw is open, which scores ≤2 with the quoted line; a draw from the whole HumanEval-Verus pool, quoted, scores ≤2 (its task forms keep the specification, so a Lab 2 problem drawn in either language exposes a later Lab 2 reference).

### cheat-audit
- **CA.a** — the cheat surface is named before the run: the instruments every claimed success passes (the learner's Q09 gate core in the verification container, the lab gate's lever check and its assumption audit (`scripts/vaudit`'s rules, D24), the spec freeze) and the classes reported `UNKNOWN`. A plan that lets a claimed success count before the gate's verdict, quoted, scores ≤2.
- **CA.b** — the exclusions say what happens to an `infra-failed` attempt and to a `truncated:<cause>` attempt, each with its counting rule. A missing truncation rule scores ≤2 by its quoted absence.

### disclosure
- **DI.a** — the plan records what a run will record: model ids or digests, the pinned argv and settings, prompt hashes once the policy file is final, the sandbox manifest. A named item with its quoted absence is a gap (3) before the runs; it becomes a finding in the report.
- **DI.b** — the disclosure line says "a small-scale replication with model substitution" (or words to that effect), names Claude as grader and subject, and states one machine and one solver pin. Its quoted absence scores ≤2.

## The --report pass (B2)

`/grade-paper Q12 --report`, after the runs, on the report problem; the unlocked `prereg` row must exist and its hash must equal Probe H on the current file (a changed plan is a `disclosure` finding at 2).
- **RP.a** — the `Reproduce:` command regenerates every table (Probe R). A table it does not regenerate scores ≤2, with the diff.
- **RP.b** — every deviation from the pre-registration is listed with its reason; a deviation the logs show and the report does not list scores ≤2, exhibited by the log line.
- **RP.c** — every claimed success carries the gate's verdict, and every grader-only class reads `UNKNOWN`. A claimed success the gate rejects, output pasted, scores ≤2.
- **RP.d** — the prediction intervals are scored, results are intervals, and the hand part's rate sits beside the arms' on the shared local tasks as description only. A causal claim from the hand-part comparison, quoted, scores ≤2.
- The method dimensions above apply to the report as executed; grade on method and reproducibility, never on the numbers.

## B3–B5 — Paper cards 05.10, 06.1, 04.8 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash each card's problem prints. Otherwise that card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with its card's pinned range (B3 lines 2148–2171, B4 2312–2338, B5 1681–1706). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain scores ≤2 only by naming the field and the quoted absence.
- **CF.e** — figures stay attached to what the range attaches them to: a rate given to the wrong model, sample count, benchmark or method (generation against repair, search against sampling, a union against a single system) contradicts the table or sentence it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short. A card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

### correctness (each card's closing line)
- **CO.a** — the closing line names one of A1, A2, A3 and what the paper's budget counts (samples, attempts, tokens), and its claim agrees with the card's range: a score ≤2 quotes the range line that contradicts it. A different arm with a reason the range supports is correct: do not invent a flaw. Advisory beside the card's grade.

## Gate

The mechanical preconditions of `/review-code Q12`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q12` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q12_PracticeIC/std` and `scripts/vcheck --gate verus/q/q12_practice_ic` each exit 0 and print only the summary line; `scripts/vcheck --gate harness/q/fvh_q/retry.py` and `scripts/vcheck --gate harness/q/fvh_q/report.py` each exit 0, and so does `scripts/vcheck --gate harness/q/fvh_q/policies.py` (the arms, H8py–H11py).
- **A3 — audit.** `scripts/vaudit dafny/Q/Q12_PracticeIC/std` and `scripts/vaudit verus/q/q12_practice_ic` report no finding.
- **A4 — statements and imports unchanged.** `scripts/specfreeze --check Q12` reports no finding: no statement changed, and the two Dafny modules keep their frozen import lists.
- **A5 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q12 --report --strict` exits 0: all six predictions filled, recorded and enabled in their specimens; every shipped commented check uncommented; and, after the exit's scored run, the exit files repaired.
- **A6 — what is not reviewed.** The stage specimens are red or refused by design (their outputs are pinned) and are never finished or reviewed. The `HAND`, `CALIBRATION`, `INTERFACE` and `AUDIT` blocks and `research/q12_grade_the_grader.md` are your prose. `tools/Q12/holecount.py` is the contractor's (the audit debrief), and `tools/Q12/test_holecount.py` is yours but outside the code review. No brittleness gate applies at this bar.

## Code-review focus — band: "design-lite"

At this bar, the conventions of the earlier bars bind, plus the design calls a filled hole still makes: the induction matches the recursion, a measure or trigger is named where it is used, no detour goes around the given representation, and Python reads the way the frozen core does.
- **C1 — fuel scoped, triggers chosen (H3d, H3v).** H3d's unfolding is raised on the one lemma that needs it, by no more than it needs (Probe D on a lower count is the anchor); H3v's proof names the terms the triggers wait for. A wider scope, cited at `file:line` with Probe D verifying the narrower one, is a reading note, never below 3.
- **C2 — the hand part's inductions match their recursions (H4d–H7d, H4v).** Each recursive lemma calls itself on the argument its definition recurs on. If the gate is green, the induction is sound: do not invent a flaw in its shape.
- **C3 — exec code against the representation (H5v–H7v).** The functions read the limbs and length through the given representation; a detour that rebuilds a value (a conversion to a number and back) is a finding at this bar, cited at `file:line`.
- **C4 — the client judges from documents (H1py, H2py).** Every pass decision reads the result's own fields through `fvh.tools`, and a killed, timed-out or incomplete result is a failed try; a subprocess, a text search of a source file, or a default that turns a missing field into a pass, cited at `file:line`, is a finding at grade 2.
- **C5 — statistics composed, never re-derived (H12py, H13py).** Intervals and tests come from `fvh.stats` calls; an interval or a p-value computed by your own arithmetic, cited at `file:line`, is a finding at grade 2. A table whose rows the frozen tests accept is correct in shape: do not invent a flaw.
- **C6 — no dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.
- **C7 — the arms spend their budget and read only observations (H8py–H11py).** Each arm makes at most one model call per `propose` and none once the budget or its seeds are used up, so no arm spends more than B calls on a task; what a prompt carries comes only from the protocol's state and the candidate's own gate document (`state.last_verify`, `focus.verify`), never from a file, the clock or an earlier prompt; and every prompt is `render`'s (H11py), the same for the same arguments. A second call in one `propose`, a call after the budget is spent, or a prompt built outside `render`, cited at `file:line`, is a finding at grade 2. An arm the frozen tests accept is correct in its protocol: do not invent a flaw.

## Audit debrief — after /contract Q12

Questions for you, after the toolwright run. Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — did the tests stay yours?** `git diff <your commit of the tests> -- tools/Q12/test_holecount.py` is empty.
- **D2 — documents only?** Read `tools/Q12/holecount.py`: no `subprocess`, no course tool, no `open` of a path that is not a document named on its command line or standard input, no regex over source text. A line that does any of these is a breach that every test may pass; name it.
- **D3 — a missing key.** Run the tool on a document with one field removed (a copy in `instructor/scratch/`): does it fail loudly, or print a zero? A zero for a missing count is a finding against the delivery.
- **D4 — two documents outside the tests.** The two runs the `AUDIT` block asks for, pasted; one of them on a file where the source text and the document disagree (a hole in a comment, say).
- **D5 — did it re-run the tests after every edit?** Count the edits and the test runs between them in the transcript; name the first stacked edit.
- **D6 — which moment earns a rule?** Name one transcript moment that deserves a rule in your contract, in the rule format of `CLAUDE.md`'s contract slot.

## Runs debrief — after Lab 1's runs (`python -m fvh run Q12`, then `fvh report Q12 --reverify`)

- **D7 — every claimed success re-judged.** `fvh report Q12 --reverify` re-runs your gate on each claimed success from a clean checkout; paste its summary.
- **D8 — ten transcripts.** For ten runs (at least two per arm and two of the Claude arm), the moments where an arm's candidate changed a statement, added a lever, or claimed a success the gate rejected; note each against the arm.
- **D9 — the plan against the runs.** For every pre-registered field, did the runs follow it? Each deviation goes into B2's list.
