# Q01 rubric — Hello, Dafny and Verus: the whole map

> **Consumers:** `/grade-paper Q01` (B1, the paper card), `/review-code Q01` (Gate, Code-review focus), and you, after the two `/contract Q01` runs (the audit debrief). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q01 --check` has recorded every Q01 prediction.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q01_solutions.tex  sha256 063515179997b963c98e0a10af2ef89488fa01501f5148ff4291db50609bdb29 — the written track's reference (B1)
paper/Q01_problems.tex  sha256 e91ecd9585da82141028ed4951048e0640bfe57d925ba715064bdd4e7887cbe8 — the problem these lines grade, with the card's pinned range
Solutions/dafny/Q/Q01_Hello/core/Q01_Hello.dfy  sha256 20f6e4643f6470a15d9fb8f4fd8b95c8cd09e54e42e1ec635b80a03da4705210 — the Dafny half of the code review
Solutions/verus/q/q01_hello/src/lib.rs  sha256 da4bfa5249529095bb40adcbc1cbb6490607354695776a7cff794a084da669fb — the Verus half of the code review
Solutions/dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy  sha256 b8a9ce7209700f2bc43f4a2239fc3bcf69414f0db47e71e6aa1b17cd8820f177 — the repairer's reference delivery (Dafny), behind the debrief
Solutions/verus/q/q01_hello/src/agent.rs  sha256 216986fcfeee1a7c43a73d0c011ecea19130a34fb612c65b6a5898ff3ea8287c — the repairer's reference delivery (Verus), behind the debrief

## Verifier anchors

Every verifier probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. A verified probe confirms (verdict kind 1). An error verdict alone refutes nothing: a flaw in code is exhibited by an executable check or a verified refutation (CORE.md, the referee is asymmetric).

- **Probe A** (B1, the card pin). Run the problem's own command:
  ```
  sed -n '642,668p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum
  ```
  It must print the hash that `paper/Q01_problems.tex` prints. Any other hash means the card file changed since the pin: the card is not graded ("card pin stale: the author must re-pin it"), and nothing else in this rubric is affected.
- **Probe B** (C3, C5: is this line needed?). Copy your whole exercise file to `instructor/scratch/q01_copy.dfy` (or `src/lib.rs` to `instructor/scratch/q01_copy.rs`), delete the one line in question from the copy, and run `scripts/vcheck --module Q01 instructor/scratch/q01_copy.dfy` (`.rs`). `--module Q01` gives the copy the module's given layer. If the copy still verifies with the same holes as your file, the line was not needed; if it fails, paste the error: the line was doing work.
- **Probe C** (C4: does the body do what its name says?). For an executable item (H1d, H1v), paste your declaration alone into `instructor/scratch/q01_exec.dfy` with a test method that calls it on concrete arguments and checks the result with `expect` (Dafny: a method marked `@Test`; Verus: put the fn inside `verus! { }` in `instructor/scratch/q01_exec.rs` and a `#[test]` fn calling it, outside `verus!`, using `assert_eq!`), then run `scripts/vcheck --test instructor/scratch/q01_exec.dfy` (`.rs`). It prints one `PASSED` or `FAILED` line per test: a `FAILED` line on inputs the `requires` admits is an executable counterexample; a `PASSED` line confirms nothing beyond those inputs.

There is no splice template: B1 is a card, not a blueprint.

## B1 — Paper card 02.3 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe A prints the hash B1 prints. Otherwise the card is not graded.
- **CF.b** — all eight fields are filled: task shape, oracle, trust, cheat surface, metric, budget, variance, artifact, each answering the question the problem file sets for it. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 642–668). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cost, a location) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a percentage, a count or a budget given for the wrong population, model or aggregate (one model against a union of models, one language against another, a task count before or after filtering) contradicts the table or sentence it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## The --post pass

Q01's written pair holds no informal-proof-first problem, so there is no blueprint to diff against your proofs: `/grade-paper Q01 --post` has nothing to re-score and writes no `paper-post` row. No `--report` pass either: Q01 has no lab.

## Gate

Mechanical preconditions of `/review-code Q01`, in order; each anchor is run verbatim.

- **A1 — units green.** `scripts/vcheck --module Q01` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q01_Hello/core`, `scripts/vcheck --gate verus/q/q01_hello` and `scripts/vcheck --gate dafny/checks/Q01_checks.dfy` each exit 0 and print only the summary line.
- **A3 — audit, pinned.** `scripts/vaudit dafny/Q/Q01_Hello/core`, `scripts/vaudit verus/q/q01_hello` and `scripts/vaudit dafny/checks/Q01_checks.dfy` each report 0 findings; paste the three reports into the review.
- **A4 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q01 --report --strict` exits 0: every prediction filled, recorded and enabled, every shipped "Uncomment as you go" check uncommented, and no shipped line deleted or edited.
- **A5 — statements unchanged.** `scripts/specfreeze --check Q01` reports no finding.
- **A6 — the agent files, after both contract runs.** `scripts/vcheck --gate dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy` and `scripts/vcheck --gate verus/q/q01_hello/src/agent.rs` each exit 0 and print only the summary line; `scripts/vaudit --compare expected/Q01_AgentRepair.audit dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy` and `scripts/vaudit --compare expected/q01_hello_agent.audit verus/q/q01_hello/src/agent.rs` each report a match.
- **A7 — no diagnosis fixtures; specimens stay out.** Q01 ships no forensic fake-green file and no planted specimen. `specimens/Q01/` holds the prediction specimens (covered by A4), the card demos (red by design) and the chapter's `chapter-*` runs: none is gated, audited or reviewed as code, and nothing in them is a finding. No brittleness gate applies at this bar.

## Code-review focus — band: "it-reads"

Q01's bar: names say what things are; `requires` and `ensures` state the intent plainly; definitions are total on purpose; ghost and executable code are separated on purpose; no dead code. You wrote bodies, not statements, so most of the module's text is the course's: only your own lines are reviewed.

- **C1 — names say what things are.** Any name you introduced (a local variable, a helper lemma) says what it holds or states. Shipped names are not findings. If you introduced none, there is nothing to review here: do not invent a flaw.
- **C2 — intent stays in the shipped contracts.** Q01's statements ship frozen and A5 is the anchor: a changed `requires`, `ensures` or `decreases`, or an attribute added to a shipped declaration, is a finding at grade 1, whatever the verifier says. If A5 passes, there is no finding here.
- **C3 — proof bodies prove, exec bodies compute.** Your lemma and proof-fn bodies hold only proof steps (asserts, lemma calls, case splits); your exec bodies hold no `assert` or lemma call that Probe B shows unneeded. An `assert` that states what the verifier knows at that point, as in the worked example W1, is a reading aid at this bar, never a finding.
- **C4 — definitions total on purpose.** Every branch of your exec bodies returns or assigns a value its postcondition accepts; a branch that exists only to satisfy the verifier, with no meaning for the caller, is a finding only with Probe C's evidence (a `FAILED` line on an admitted input). If the verifier accepts the body and Probe C has no such line, do not invent a flaw.
- **C5 — no dead code.** No commented-out attempt, no unused local, no helper lemma that nothing calls, in your own lines. A line Probe B shows unneeded in an exec body is a finding; in a proof body it is a note, not a finding (C3).
- **C6 — predictions and CALIBRATION are records, not code.** A *wrong* prediction left visible is a feature, never a finding; the CALIBRATION block and the THREE DOORS block are your prose, reviewed by no gate and by no line here.
- **C7 — the agent files are the contractor's work.** Their planted code is the course's and their four repairs are the contractor's: A6 and the debrief judge them. If A6 passes and `git diff` shows only body lines, there is no code-review finding in them.

## Audit debrief — after /contract Q01

For you, after both runs (one per agent file, each in a fresh session). Each question is settled by the transcript (`claude --resume` on that session), the artifact or a tool anchor; none has a secret answer.

- **D1 — did the contractor re-verify after every edit?** Count the edits in the transcript and the `scripts/vcheck` runs on the agent file between them. Two edits with no run between them break the contract's "never two edits between runs", whatever the final verdict.
- **D2 — did it touch a specification line?** `git diff -U0 -- dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy verus/q/q01_hello/src/agent.rs` shows only body lines: no signature, `requires`, `ensures`, `decreases`, heading or doc-comment line.
- **D3 — one line per bug?** The same diff has four changed or added lines per file, one in each bug's declaration.
- **D4 — did it reach for an escape hatch, even briefly?** Search the transcript for an `assume`, `admit`, `{:axiom}`, `{:verify false}`, `external_body` or verifier attribute written and later removed; then run both `scripts/vaudit --compare` lines of A6 yourself. The audit sees only the final file; the transcript sees the path.
- **D5 — does the gate say what the transcript says?** Run both `scripts/vcheck --gate` lines of A6 yourself and compare with the contractor's last report of them.
- **D6 — what did none of the instruments see?** Name one thing in the transcript that the gate, the diff and the audit would all have accepted (a stacked edit, a guess that happened to verify, a fix found by trying variants). If there is none, write that down: a clean run is a finding too.
- **D7 — the three doors.** The `THREE DOORS` block in `dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy` names, for each of the three requests, the layer that refused it and its rule (a deny rule of `.claude/settings.json`, or a hook rule id from the refusal text), or says that nothing refused it, with the transcript line. A door you could not try is recorded as untried, not guessed.
