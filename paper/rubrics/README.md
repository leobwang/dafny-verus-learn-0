# paper/rubrics/ — module rubrics

One rubric per module, `paper/rubrics/<ID>_rubric.md`; the registry's `rubric` field names it (`""` = none). Every core module (Q01–Q18, R01–R16) has one: each has a written track, paper cards at least, and the rubric also serves `/review-code` (its Gate and Code-review-focus lines) and the debrief after `/contract`. A challenge module has one only where it has a written item (a blueprint or a sketch); its defense sheet and its gate do the rest. A module with `paper = true` must have one.

- **Learner-visible by design.** Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a **verifier anchor**: a command whose output settles the question. An anchor restates only material already printed in the problem file or in the exercise comments. A rubric "verifies that a bridging lemma is *stated*" without ever stating one.
- **Advisory.** A verifier check outranks any rubric line, and you may dispute a finding at the level of its labelled line. Every line has a label for that reason.
- **Consumers:** `/grade-paper`, `/review-code`, and you, after `/contract` (the audit debrief).
- **Never contradict the tool-counted rule.** No rubric line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.

## Layout, in order

1. **Title and header.** `# <ID> rubric — <registry title>`, then a blockquote naming the consumers, the stance ("every line is a predicate about your artifacts, never an answer") and the advisory status.
2. **Pins.** One line per pinned source, under the heading line `Solution pins (scripts/ci.sh compares on every change; stale pins fail):`, each in the form `<repo path>  sha256 <64-hex | PENDING>[ — note]`. A rubric's author cannot read the reference, so a new pin says `PENDING`; `scripts/update_rubric_pins.sh` (not built yet; phase DV1b), run by the author or by `scripts/ci.sh` where no permission layer applies, fills in the hash, and its `--check` mode fails on a pending, stale or missing target (a renamed target must fail loudly). Pins may also target learner files.
3. **`## Verifier anchors`.** Named probes (`Probe A`, `Probe A′`, `Probe B`, …), each tied to a problem or an item, each with a run recipe for `instructor/scratch/` through `scripts/vcheck`. The answer key of a hand calculation is an **executable check** (a Dafny `@Test` method with `expect`, a Verus `#[test]` outside `verus!`, or a Verus spec value `by (compute_only)`), never a verifier-only `assert`. An anchor that can only fail to verify refutes nothing (the asymmetry rule of `CORE.md`). This section also holds **splice templates**: a probe into which you paste your own helper statement, to check that it is general enough to formalize.
4. **One section per written problem**: `## B<n> — <title> (<type>; dimension: <label>)`, one `###` per dimension, with labelled predicate lines. A predicate that can drive a score ≤2 says exactly what must be exhibited (an executable counterexample, a verified refutation, a quoted line, a recomputation).
5. **`## The --post pass`**: what the post pass diffs (the paper decomposition against your verified proof) and the gradebook delta.
6. **Research problems** (paper cards, pre-registrations, lab reports): predicates per dimension of `CORE.md`'s research table (`card-fidelity`; `hypothesis-precision`, `budget-parity`, `variance`, `contamination`, `cheat-audit`, `disclosure`; `reproducibility` for reports), plus `## The --report pass`. They grade method and reproducibility, never whether a number matches.
7. **`## Gate`**: the mechanical preconditions of code review, each with its tool anchor: zero holes counted by `scripts/vcheck --gate`, a pasted `scripts/vaudit` report, `scripts/firsttry.sh <ID> --report --strict` wherever the module ships prediction slots or commented checks, and `scripts/vcheck --brittleness` from the `design-judgment` bar up. It also names every diagnosis fixture (a forensic fake-green file, a planted specimen) that the hole, audit and brittleness gates skip, because the learner audits it rather than finishes it.
8. **`## Code-review focus — band: "<review_bar>"`**: lines `C1`…`Cn` at the module's bar, with explicit "do not invent a flaw" clauses ("if every check passes, the order is correct: do not invent a flaw"; "a *wrong* prediction left visible is a feature, never a finding").
9. **`## Audit debrief — after /contract <ID>`**: questions `D1`…`Dn` for you. Each is settled by the transcript, the artifact or a tool anchor, and none has a secret answer.
10. **Optional gate banner**, a fixed first line: `GATE <ID>: OPEN — …` or `GATE <ID>: HELD — <dimension> at <score>`. Still advisory: a dispute that produces a machine-checked instance wins.

## Label grammar

- **Dimension predicates**: `<PREFIX>.<letter>`, with the prefixes `SF` statement-fidelity, `IS` induction-soundness, `CE` case-exhaustiveness, `BQ` blueprint-quality, `GA` gap-accounting, `RC` recomputation, `CO` correctness, `CF` card-fidelity, `HP` hypothesis-precision, `BP` budget-parity, `VA` variance, `CT` contamination, `CA` cheat-audit, `DI` disclosure, `RP` reproducibility. A rubric-declared dimension declares its own prefix in its `###` heading.
- **Numbered lines**: `- **<L><n> — <title>.**`, with `A` for Gate lines, `C` for Code-review-focus lines and `D` for Audit-debrief lines. Written problems are the `B<n>` section headings (`P<n>` is a predict item).
- **Probes**: `Probe <letter>`, optionally primed (`Probe A′`).

## An invented skeleton (no predicate states an answer)

```markdown
# Q04 rubric — Proof craft, loops and libraries
> Consumers: /grade-paper, /review-code, the /contract debrief. Every line is a predicate about your artifacts, never an answer.
> Advisory: a verifier check outranks any line here; dispute a finding by its label.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
<reference twin path>  sha256 PENDING

## Verifier anchors
- **Probe A** (B1): paste your helper's statement into `instructor/scratch/probe.dfy` below the given definitions; run `scripts/vcheck instructor/scratch/probe.dfy`. The anchor is the verdict and its location, never a solutions file.

## B1 — a loop by hand (informal-proof-first; dimension: induction-soundness)
### induction-soundness
- **IS.a** — the invariant is stated as a formula over the loop variables. A score ≤2 exhibits a reachable state where the stated invariant fails after one iteration, run through compiled code.

## Gate
- **A1 — holes.** `scripts/vcheck --gate <each exercise file>` reports 0 holes (tool-counted).

## Code-review focus — band: "proof-shape"
- **C1 — invariants say what the loop has established.** Anchor: the verifier accepts the loop with no extra `assert`. If it does, do not invent a flaw.

## Audit debrief — after /contract Q04
- **D1 — did the contractor touch a spec line?** Settled by `git diff -U0 -- <agentic file>`.
```
