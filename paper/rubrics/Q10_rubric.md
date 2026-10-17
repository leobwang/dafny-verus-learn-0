# Q10 rubric — Practice I-A

> **Consumers:** `/grade-paper Q10` (B1, B2) and `/review-code Q10` (Gate, Code-review focus). Q10 has no agentic file, so there is no audit debrief. Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q10 --check` has recorded both Q10 predictions.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q10_solutions.tex  sha256 5a186cb91a5b1e07dbd7bf71ca50d6569af65921d62ae78c979a9dabb324a8fa — the written track's reference (B1, B2)
paper/Q10_problems.tex  sha256 69e52eaca20c247a11b443900fcff989c7790909600100ae4b3df45a4a848aed — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q10_PracticeIA/std/Q10_PracticeIA.dfy  sha256 17fd0aa9fb4f8e1b2fc858879858b9c13541ed5e48a12cc84559156e2a3463ab — the Dafny half of the code review
Solutions/verus/q/q10_practice_ia/src/lib.rs  sha256 006d1fcc2d99483dfabaa35a22f786aaafab46bd0740f66211218da5ffd4f391 — the Verus half of the code review

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. A verified probe confirms a claim (verdict kind 1). An error verdict alone refutes nothing about a proof; for B1, a claim about what `scripts/vcheck` reports is settled by that report, pasted.

- **Probe A** (B1, each loop's verdict). Copy each of B1's four files verbatim from `paper/Q10_problems.tex` into `instructor/scratch/` (`a.dfy`, `b.dfy`, `c.dfy`, `d.rs`) and run `scripts/vcheck --module Q10 instructor/scratch/<file>` on each, one at a time. The summary line gives the verdict and, for a refusal, the stage; the error lines give the failing obligation and its location.
- **Probe A′** (B1, a reason). A reason that names a missing fact is confirmed when adding that fact, and nothing else, to a scratch copy makes the file verify (or moves its failure to another obligation the reason also names); paste both runs. A reason about non-termination is confirmed by a concrete input, stated with the values each loop variable takes, on which the guard never becomes false.
- **Probe C** (B2, the card pin). `sed -n '888,913p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B2 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review, with its file's `module` line and imports (for a crate file, its `use` lines, `use qg_bignat_l5::*;` among them), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`; delete the one line in question; run `scripts/vcheck --module Q10 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.
- **Probe E** (Code-review focus, a library fact re-proved). A scoped search of the pinned library source for the shape of your helper's conclusion, pasted with its hits: Dafny, `unzip -p .toolchain/dafny-4.11.0/dafny/DafnyStandardLibraries.doo program | grep -n -A4 '<pattern>'`; Verus, `grep -rn -A6 '<pattern>' ~/.cargo/registry/src/*/vstd-0.0.0-2026-09-20-0158/arithmetic/`. A hit whose `ensures` gives your helper's conclusion under hypotheses your call site meets is the evidence for C4; the finding quotes the search, never the lemma's name alone.

## B1 — Loop measures (concept; dimension: correctness)

### correctness
- **CO.a** — each loop's verdict, and for a refusal its stage, agrees with Probe A's output for that file. A verdict claim scores ≤2 only with Probe A's pasted summary line that contradicts it. A claim the answer hedges ("probably") is graded as the claim it makes.
- **CO.b** — for each loop that does not verify, the obligation the answer names is the one Probe A's error line reports, or one that Probe A′ shows also fails. Naming an obligation that holds scores ≤2 only with a run of a scratch copy that settles it.
- **CO.c** — each reason is a cause, not a restatement of the verdict ("it fails because it cannot be proved" is no reason). A reason scores ≤2 only with Probe A′'s evidence against it: the added fact that does not repair the file, or the input the reason claims and that terminates. A different true reason from the reference's is correct: do not invent a flaw.
- **CO.d** — the answer says what measure Dafny uses when none is written, in terms of the guard, and for each Dafny loop whether that measure is the loop's problem. A score ≤2 names the loop where the answer's measure claim and Probe A's termination result disagree.

## B2 — Paper card 02.11 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B2 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 888–913). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cost, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a figure given to the wrong prompt variant, the wrong codebase or the wrong sample count contradicts the table or sentence it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

### correctness (the ninth line)
- **CO.e** — the ninth line says which of *where* and *what* the verifier's message gave for H3 and which the learner supplied, and its claim about the message agrees with a run of the shipped attempt (the attempt quoted in H3's docstring, copied into a scratch copy of the exercise file and run with `scripts/vcheck`; paste the error lines). A score ≤2 quotes the error line the claim misreads. Advisory beside the card's grade: it does not lower a field's score.

## Gate

The mechanical preconditions of `/review-code Q10`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q10` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q10_PracticeIA/std` and `scripts/vcheck --gate verus/q/q10_practice_ia` each exit 0 and print only the summary line.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q10_PracticeIA/std` and `scripts/vaudit verus/q/q10_practice_ia` report no finding.
- **A4 — statements unchanged.** `scripts/specfreeze --check Q10` reports no finding. It accepts added `ensures` clauses on `Shift` (Dafny) and `high_limb` (Verus), the two open statements that `expected/Q10.freeze` lists under `open_specs`, and nothing else.
- **A5 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q10 --report --strict` exits 0: both predictions filled, recorded and enabled; every shipped commented check uncommented (`ToU64Check`, `NormLenCheck`, `norm_len_check`, `ring_check`); H1d's `form: no-call:ToNat` line met; and, after the exit's scored run, the exit files repaired.
- **A6 — what is not reviewed.** The `CALIBRATION` block is your prose, read by no tool. No brittleness gate applies at this bar.

## Code-review focus — band: "design-lite"

At this bar, the conventions of the earlier bars bind (the proof reads, it has the shape its statement suggests, library facts are called by name), plus the design calls a filled hole still makes: the case split or induction matches the recursion, an invariant or measure is named where one is used, and no detour goes around the given representation.
- **C1 — the method clause of H1d.** `ToU64`'s code decides from the number of limbs and the limbs themselves and does not call `ToNat` (its docstring's clause; the block's `form: no-call:ToNat` line, which A5 checks). If A5 passes, no compiled call remains: read the case analysis, and do not invent a flaw. A call inside an `assert` is not code.
- **C2 — the attempts kept (H3d, H3v).** Each body holds every line of the attempt its docstring quotes, unchanged and in order, with additions only. Compare the body with the docstring line by line; a changed or dropped line of the attempt is a finding (cite both). If every line is there, the repair is in the item's form: do not invent a flaw.
- **C3 — invariants say what the scan established (H4d, H4v).** Each invariant clause speaks about `n`, `i` and the limbs below `i`, and each is needed: Probe D on a clause that verifies without it shows a dead clause, a reading note. A clause Probe D shows needed stands.
- **C4 — library facts called, never re-proved (H5d, H5v).** The body calls the library lemma that states the step, with arguments that meet its `requires`; a helper of your own whose conclusion a lemma of `Std.Arithmetic` or `vstd::arithmetic` gives is a finding, evidenced by Probe E. If Probe E finds no such lemma, the helper stands: do not invent a flaw.
- **C5 — the ring buffer stays a ring buffer (H6v, H7v).** The code computes a storage position by a comparison, as `slot` does, with no `%`, and no addition or subtraction that can leave `usize` (the verifier's overflow checks are the anchor: A2 green settles it). A detour around the given representation, such as rebuilding `buf` or moving elements, is a finding at this bar, cited at `file:line`.
- **C6 — statements as given.** Only `Shift` and `high_limb` gained clauses (A4 is the anchor). A statement too strong for the body fails A2; one too weak fails its client; if A2 is green and the clients' assumes are gone, the statement is strong enough for them: do not invent a flaw. Whether an added clause says more than the docstring asks is a reading note.
- **C7 — no dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.
