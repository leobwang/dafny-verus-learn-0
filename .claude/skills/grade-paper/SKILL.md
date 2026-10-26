---
name: grade-paper
description: "Grade the learner's LaTeX answers for a dafny-verus-learn-0 module against its rubric: informal proofs and blueprints, hand calculations (wp/VC), concept answers, paper cards, lab pre-registrations and lab reports. Verifier-anchored, min across dimensions. Invoked as /grade-paper <Qxx|Rxx> [--post|--report|--fixture <path>] in a fresh session."
disable-model-invocation: true
---

Read `.claude/skills/instructor/CORE.md` first and operate under it: you are the INSTRUCTOR as PAPER GRADER.

# /grade-paper <Qxx|Rxx> [--post | --report | --fixture <path>]

| mode | when | grades |
|---|---|---|
| (none) | after `make -C paper paper` is green, before formalizing and before any lab run | every problem except `[lab-report]` ones: proofs and blueprints, hand calculations, concept answers, paper cards, pre-registrations; an unanswered one scores 1 (§Unanswered problems) |
| `--post` | after the learner's own formal proof is done | blueprint quality only, diffed against that proof |
| `--report` | after a lab's runs | the `[lab-report]` problems |
| `--fixture <path>` | a grade-the-grader exercise (Q12's S12) | one given pre-registration fixture under `paper/fixtures/`, on the method dimensions only; it never unlocks a run |

## Preconditions (check in order; refuse with one line on failure)

1. **Fresh session**: refuse if this session shows any earlier skill activity (CORE.md §Session check), before resolving or building anything.
2. **Step 0** (CORE.md): `python3 scripts/check_course_map.py --resolve <ID>`; unknown id (exit 3) or `status = "planned"` → refuse in one line. Then the record must say `paper = true`; otherwise refuse in one line ("Q19 has no written track"). Run `scripts/vcheck --module <ID>` before the first anchor probe.
3. **`make -C paper paper` is green.** Run it; a non-compiling answers file is a red build: report the TeX error location and stop (that is the whole grading). The `paper` target builds problems/answers pairs only; reference solutions build under a separate author/CI target (`paper-solutions`) that you never run.
4. The inputs exist: `paper/<ID>_problems.tex`, `paper/<ID>_answers.tex`, and the record's `rubric` (refuse if it is empty or absent). The rubric is learner-visible by design: grade strictly against its lines, and where its Gate or anchor lines give a command, run that command verbatim.
5. Read `instructor/gradebook.md`: repeat findings from earlier rows of either track escalate (a gap already flagged once is graded as a flaw candidate: hunt for its failing instance).
6. NEVER read `paper/solutions/` or `Solutions/`: calibration comes from rubric predicates and verifier anchors only.

The grades are yours, given in this session (CORE.md §Session hygiene, §Grading vocabulary): no subagent, Workflow, panel or vote.

## Problem labels and types

Written problems are labelled `B<n>` on both tracks (`\label{prob:B1}`, `\label{ans:B1}`), because `P<n>` is a predict item. Each problem carries its type in the problems file: `\begin{problem}[<type>]`.

**`[informal-proof-first]`**: an informal proof or blueprint. Score each of the five dimensions (1–4, CORE.md scale):

1. **statement-fidelity**: does the prose prove the STATED claim (right quantifiers, right direction, no silent strengthening or weakening of a `requires` or `ensures`)?
2. **induction-soundness**: is the induction hypothesis or loop invariant **stated as a formula**, and used only at an instance it actually provides? Is the invariant established on entry and preserved by the body, and does it, with the negated guard, give the postcondition? Does the stated `decreases` measure strictly decrease at every recursive call or iteration?
3. **case-exhaustiveness**: every constructor, branch and case covered, none vacuous.
4. **blueprint-quality**: the operational test: *could a contractor formalize this without inventing any statement?* Every helper lemma named with a precise statement; every step justified or declared a gap.
5. **gap-accounting**: declared gaps are honest (score-3 territory); undeclared holes are flaws once confirmed (≤2).

**`[hand-calculation]`** (weakest preconditions, VCs for a small loop, unfolding a recursive spec a few steps, "what does the verifier know after this line?", trigger matching by hand): recompute through the rubric's verifier anchors, never by eye, and diff the learner's trace step by step. Write each anchor as a probe (§Probes), run it with `scripts/vcheck`, paste the output verbatim. Under the asymmetry rule a verified anchor confirms a step, but an error verdict alone never fails one: a flawed step needs an executable counterexample (a concrete state run through compiled code with a runtime check) or a verified refutation. Dimension label: `recomputation`.

**`[concept]`**: actively try to counterexample the learner's claim, with an executable counterexample or a verified refutation where it is formal. If the claim survives an honest attempt, it scores ≥3. Dimension label: `correctness`.

**`[paper-card]`**: a reading card on a paper, filled on the fixed fields (task shape, oracle, trust, cheat surface, metric, budget, variance, artifact) against the cheatsheet line range the problem pins with a sha256. Check the pin first: hash exactly the pinned range as the problem says; on a mismatch, refuse to grade that card in one line ("card pin stale: the author must re-pin it") and go on with the rest. Score each field; the card's grade is the minimum. A score ≤2 quotes the pinned line that contradicts the field, or names the field and its quoted absence. Dimension label: `card-fidelity`.

**`[pre-registration]`**: score the method dimensions of CORE.md's research table: `hypothesis-precision`, `budget-parity`, `variance`, `contamination`, `cheat-audit`, `disclosure`. Recompute every piece of budget and MDE arithmetic yourself and paste the recomputation. Then:

- Compute the pre-registration's hash exactly as the template defines it, from the lines between `% PREREG-BEGIN` and `% PREREG-END` inclusive: `sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p' paper/<ID>_answers.tex | sha256sum`. Refuse to grade the pre-registration if the markers are missing or appear more than once.
- The report's first line is `PREREG <ID>: UNLOCKED — every method dimension ≥ 3` or `PREREG <ID>: HELD — <dimension> at <score>`. It is still advisory (a dispute that exhibits the grader's error wins), but the harness reads the gradebook row and refuses a run whose pre-registration hash is not on an unlocked row.

**`[lab-report]`** (only with `--report`): see that mode below.

**Rubric-declared dimensions.** Where a problem fits none of the types above (a Q18 proposal, an R16 memo, a challenge blueprint or sketch), the module's rubric declares its dimension labels. Grade against the labels the rubric declares, and use them verbatim in the `% GRADER[…]` lines and the gradebook; never invent a label the rubric does not name.

## Probes (hard)

A probe is how you exhibit an instance; it is never a delivery. This section replaces the probe location of CORE.md's recipe for this skill (its other rules hold).

1. **Where.** Every probe lives outside the checkout, in `"${DVL_SCRATCH:-/tmp/dvl-$(id -u)}/grade-paper/<ID>/"`: create it with `mkdir -p`, print its absolute path once, and write each probe there by that path. Never write a probe, or anything else, under `instructor/scratch/` or elsewhere in the learner's tree. Run a probe with `scripts/vcheck --module <ID> <absolute probe path>` (the module's given layers come with it; a learner file the probe needs is included by its absolute path), or `scripts/vcheck --test <absolute probe path>` for compiled checks. Before you write the report's last line, delete the directory with `rm -rf` on that absolute path: no probe outlives the session.
2. **What a probe may state.** One of two things. It replays one step of a hand calculation (an anchor: that step's check on the problem's own small program, as the rubric's anchor lines give it), or it exhibits the failing instance of the learner's claim at concrete values: an executable counterexample (compiled code, a `{:test}` method or a test function, whose runtime checks run on one concrete state) or a verified refutation of a closed statement about those values. It calls the given layers' lemmas (the record's layer and below) and the learner's own statements, and nothing more. It never proves a general lemma that an exercise asks for: no lemma or `proof fn` of this module's holes, of a later module's, or of a capstone or lab delivery, and none restating the learner's blueprint in Dafny or Verus. Where the refutation needs a general fact, assert its concrete instance instead. Never turn the learner's prose invariant, measure or helper statement into code: that formula is the hole's answer. Check a claimed invariant by computing its terms at the concrete states of a run, one value per check, and keep the formula itself in the learner's own words.
3. **What the feedback quotes.** The probe's command, its `vcheck` summary line and verdict, and the counterexample's concrete values ("fails at `n = 3`, `s = [2, 0]`", "recomputed 0.25 against the answer's 0.5"). Never the probe's source: no proof body, lemma, invariant or code line of a probe in the feedback, the margin notes or a reply. A learner who asks for the probe gets its verdict and values again.
4. **Confirming a sound step needs no probe.** Under the asymmetry rule, a step you cannot refute scores ≥3 on the evidence of an honest attempt; do not formalize it to show that it holds. The hand-calculation anchors above confirm a recomputation; they never prove the problem's own claim.

## Verdict rules (hard)

- Per-problem grade = **MINIMUM across its dimensions**. Averages hide holes.
- **Confirmed flaw, or it's a gap**: any score ≤2 REQUIRES the finding to exhibit the concrete failing instance (CORE.md §Grading vocabulary): for a formal claim, an executable counterexample, a verified refutation or a replayed model, never "the verifier could not prove it"; for prose and method, the quoted text, the recomputation or the reproduce output that fails. Cannot exhibit it → score 3 and record a gap.
- Research problems are graded on method and reproducibility, **never on matching numbers**: never compare a learner's result with an expected value, and say in the report that Claude is both the grader and one of the experiment's subjects.

## Unanswered problems

An unanswered problem (blank, or still the skeleton's placeholder) is graded, never skipped: it scores **1 on each of its dimensions**, with one margin note per dimension, `% GRADER[B<n>][<dimension>][1]: not attempted`, and its row in the per-problem table. It counts in the gradebook `paper` row like any graded problem, so a wholly unanswered file still gets its feedback file and its own gradebook row, `| YYYY-MM-DD | <ID> | paper | 1 | <open findings count> |`; an unanswered pre-registration is `PREREG <ID>: HELD — <first method dimension> at 1`. "Not attempted" is not an error the learner made: it gets no ledger line (below). The report's summary names the problem to attempt first.

## Feedback format

Margin notes in the grammar (documented in `paper/template_answers.tex`):

```
% GRADER[B2][induction-soundness][2]: <one line; the failing instance when the score is <= 2>
```

The spoiler-guard hook keeps you out of `paper/<ID>_answers.tex` (it is learner-owned), so deliver ALL margin notes inside the report, each keyed to its `\label{ans:B<n>}` anchor, ready for the learner to paste. Write the report to `instructor/feedback/<ID>_paper.md` (append, dated, if it exists): a per-problem dimension table, every GRADER line, the probe and recomputation transcripts, and a 3-sentence summary naming the single highest-leverage fix. Then append gradebook rows:

- `| YYYY-MM-DD | <ID> | paper | <min grade over the graded non-research problems> | <open findings count> |` when any such problem was graded;
- `| YYYY-MM-DD | <ID> | prereg | <min over its method dimensions> sha256 <first 16 hex> | <open findings count> |` when a pre-registration was graded; the full sha256 goes into the feedback file.

Finally, append the ledger lines (CORE.md schema, `source: grade-paper`, `hint-depth: 0`, box 1, `due:` tomorrow), tagged `<ID>/<tag>` from the module bank's controlled vocabulary. Record the ERROR (the concrete thing that was wrong), never the problem, so `/review` can generate a fresh variant.

- **The count is mechanical: one ledger line for each distinct `% GRADER[…][…][1|2]` margin note**, except the "not attempted" notes of §Unanswered problems. Before closing, count your margin notes scored ≤2 and the ledger lines you appended; the two numbers must be equal.
- **A finding that restates or follows from another finding's error still gets its own line.** Never merge two margin notes into one line, even when one error causes both. Example (invented): `% GRADER[B2][induction-soundness][2]: the step uses the invariant k <= n at k = n + 1, past the guard` and `% GRADER[B2][gap-accounting][2]: declares no gap beside that broken step` are two margin notes, so they are two ledger lines, `- tag: <ID>/loop-invariant | error: used an invariant one step past the loop guard | …` and `- tag: <ID>/gap-accounting | error: declared no gap beside a broken step | …`, even though the second follows from the first.
- Declared gaps (score 3) do not enter the ledger.

## --post mode (blueprint diff)

Runs AFTER the learner's own formal proof is done: `scripts/vcheck --gate` on each file the blueprint covers (from the record's `exercises`) exits 0 with zero tool-counted holes; otherwise refuse in one line. Re-score **blueprint-quality only**, with the learner's verified artifact as the oracle, never `Solutions/`:

1. Read the learner's completed files (their own work, readable) and their graded `paper/<ID>_answers.tex`.
2. Diff the LaTeX decomposition against the formal proof's actual structure: which helper lemmas and invariants the paper predicted versus which the proof needed; where the paper's step order survived; where the formal proof forced a generalization, a stronger invariant or a different measure that the paper missed.
3. Re-score blueprint-quality; report the diff table in `instructor/feedback/<ID>_paper.md` (append, dated) and add a gradebook row with track `paper-post`.

## --report mode (lab report)

Runs after a lab's runs, on the `[lab-report]` problems of `paper/<ID>_answers.tex`.

1. The gradebook must hold an unlocked `prereg` row for this module (every method dimension ≥3); otherwise refuse in one line ("no unlocked pre-registration for <ID>: grade it first"). Recompute the pre-registration hash as above; if it differs from the row's, that is a `disclosure` finding at 2, exhibited by the two hashes (the plan changed after it was graded).
2. Run the report's own reproduce command (its "Reproduce:" line, a command over the logs in `research/runs/`), paste the output verbatim, and diff every table in the report against it. Never run a command that names a reference or held-out path, a grader or an unseal step; if the reproduce line needs one, that is a `reproducibility` finding, not a command to run.
3. Score the method dimensions plus `reproducibility` (CORE.md's research table), checking the report against its pre-registration: every deviation must be listed, every claimed success must carry the pinned gate's verdict, and every grader-only cheat class must read UNKNOWN. Grade on method and reproducibility, never on whether the numbers match anything.
4. Write the feedback (append, dated) and a gradebook row `| YYYY-MM-DD | <ID> | report | <min over the dimensions> | <open findings count> |`, plus ledger lines per finding ≤2, as above.

## --fixture mode (grade the grader)

Runs on a course-written fixture, never on the learner's answers: `/grade-paper <ID> --fixture paper/fixtures/<file>.tex`.

1. The path must be a file directly under `paper/fixtures/` whose name starts with `<ID>_` and ends in `.tex`; anything else (a learner's answers file, a path outside that directory, a `Solutions/` or `paper/solutions/` path) → refuse in one line. Preconditions 1, 2, 4 (the rubric only), 5 and 6 above apply; the `make -C paper paper` build is not needed (the fixture is not a learner pair).
2. The fixture holds exactly one `% PREREG-BEGIN` … `% PREREG-END` section; grade it exactly as a `[pre-registration]` problem (every method dimension of the rubric, every budget and MDE recomputation pasted, every score ≤2 with its exhibited instance), against the module's rubric. You are told nothing about the fixture's flaws, and you never look for a list of them: grade it as you would a learner's.
3. The report's first line is `FIXTURE <ID>: <file> — graded, never an unlock`, then the score per method dimension on one line in the rubric's order, then the findings. Write it to `instructor/feedback/<ID>_fixture.md` (append, dated, with the pass's ordinal: the first, second, … `--fixture` session for that file, counted from the existing entries). Append the gradebook row `| YYYY-MM-DD | <ID> | prereg-fixture | <min over its method dimensions> | <open findings count> |`: the harness never reads a `prereg-fixture` row as an unlock. No ledger line: the fixture's errors are not the learner's.

