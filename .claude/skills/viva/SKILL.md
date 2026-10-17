---
name: viva
description: "Oral exam for dafny-verus-learn-0: an R module viva, a Q tier-end viva, or a Q challenge defense, as the module's registry record says. Verifier-refereed predicts, graded SOLID/SHAKY/MISSED with a PASS/PASS-WITH-REVIEW/REVIEW outcome. Invoked as /viva <Qxx|Rxx> in a fresh session."
disable-model-invocation: true
---

Read `.claude/skills/instructor/CORE.md` first and operate under it: you are the INSTRUCTOR as EXAMINER.

# /viva <Qxx|Rxx> — the oral

## Preconditions

1. **Fresh session required.** If this session shows any earlier skill activity (CORE.md §Session check), refuse in one line ("viva needs a fresh session: coach and examiner never share a transcript") and stop, before resolving or building anything.
2. **Step 0** (CORE.md): `python3 scripts/check_course_map.py --resolve <ID>`; unknown id (exit 3) or `status = "planned"` → refuse in one line and stop; `scripts/vcheck --module <ID>` before the first probe.
3. **The record's `viva_mode` picks the exam:**
   - `module` → the module viva (6 questions from the module's bank; every R module);
   - `tier` → the tier viva (5 questions across the tier; the Q tier-end modules Q03, Q06, Q09, Q12, Q15 and Q18);
   - `defense` → the challenge defense (6 questions built from the learner's artifact; Q19–Q33);
   - `none` → refuse in one line, naming the module that examines this one when there is one: "Q02 has no viva of its own; its tier is examined by /viva Q03" (the record of the same `tier` whose `viva_mode` is `tier`). If no module of the tier has one (the Q01 survey), say the module has no viva.
4. Load `instructor/ledger.md`, and check `instructor/records/` for previous vivas of this module: every `<ID>_viva_*.md` and `<ID>_defense_*.md`, whatever its suffix. A re-viva MUST draw bank questions **disjoint** from every previous draw (the banks are built so that two disjoint draws exist).

## Exam discipline (every mode)

One question per message, no lecturing between questions. A brief neutral acknowledgment only ("noted; next:"). Grades are revealed at the END, never per question: mid-exam feedback distorts the remaining answers.

The **predict** question is the signature move in every mode: the learner commits a concrete outcome (a verdict kind and its location, a value, which labelled obligation fails, or a two-column `D:<v> V:<v>` outcome), THEN the verifier referees live through CORE.md's dispute recipe: write the probe to `instructor/scratch/`, run `scripts/vcheck`, paste the output verbatim, and the learner reconciles prediction and reality first. Grade against the live verdict kind under the asymmetry rule: an error at a location is not "the claim is false", and an inconclusive run decides nothing. If a bank probe's live output differs from the output the bank recorded, or the run is inconclusive when the bank recorded a verdict, say so, do not grade that predict, record the drift (a bank defect for the author), and ask the next disjoint predict question of the draw instead; if none remains, report the gap and grade the exam without it.

## Module viva — exactly 6 questions (`viva_mode = "module"`)

Load the record's `bank` (refuse if it is empty or absent).

1. **Reconstruct**: rebuild a definition, spec or argument from the module (bank type: reconstruct).
2. **Predict**: verifier-refereed, as above.
3. **Why**: mechanism, not recall (bank type: why).
4. **Connect**: a backward-edge question reaching into an earlier module of the same track (the bank marks these).
5. **Transfer**: apply the module's idea on unfamiliar ground (bank type: transfer).
6. **Ledger-generated**: build ONE fresh question from this module's entries in `instructor/ledger.md` (from the recorded concept–error pair; never re-ask a recorded question verbatim: the ledger stores errors, not questions). If the ledger has nothing for this module, substitute a second predict question.

## Tier viva — exactly 5 questions (`viva_mode = "tier"`)

The pool is the union of the `viva: yes` questions in the banks of every Q module that shares this record's `tier`. List those modules from the registry:

```
python3 -c 'import tomllib; t = "<tier>"; print([(m["id"], m["bank"]) for m in tomllib.load(open("MODULES.toml", "rb"))["module"] if m.get("track") == "Q" and m.get("tier") == t])'
```

Refuse in one line if any of those banks is missing: a partial pool is not the tier. Then draw **5 questions from 5 different strands** (each Q bank question names its strand, S1–S13, next to its tags), with at least one question from every module of the tier, at least one predict question, and at least one backward-edge question where the pool allows. Cite each by its scoped id (`Q05.K3`). There is no ledger-generated question: the tier exam samples the tier, and ledger items belong to `/review`.

When the bank tables its draws (A, B, C, …), sit the first one disjoint from every earlier tier viva, exactly as tabled. If the table is headed by an **Opening** paragraph (Q06's `AUDIT ROWS`, Q09's `EXPLAIN-BACK` blocks), run it first, as written there: it is ungraded, adds no ledger entry and is not one of the five. If the pool cannot supply a draw with 5 distinct strands that is disjoint from earlier tier vivas, or a tabled draw cannot run as printed (a probe it names is missing), say so and stop: a bank gap is reported, never patched by improvising or swapping questions between draws.

## Defense — exactly 6 questions built from the artifact (`viva_mode = "defense"`)

The defense examines the learner's own challenge artifact (the record's `exercises`) and its trust ledger (the `TRUST.md` the challenge chapter names). That is learner work and readable; the reference trees are not, and CORE.md's MAY NOT binds hardest here: no reference path opened, no held-out path named, never a grader or unseal command. Note whether the topic gate has passed (the gradebook's `challenge` row for this module); the defense does not re-run it.

Load the record's `bank`, the topic's defense sheet: six question templates, each with insight bullets (refuse if it is empty or absent). **Before asking anything**, instantiate every template on the artifact and write each instantiated question with its anchor bullets into the record file: anchors fixed before the answer cannot drift to fit it.

1. **Reconstruct a lemma**: a load-bearing lemma or invariant of the artifact: its statement, and why the architecture needs it.
2. **Predict what breaks**: name a hypothesis (`requires`, invariant conjunct, type constraint) of one of the learner's own lemmas; the learner predicts the verdict kind and location without it; then the verifier referees: copy that statement (their own code) into `instructor/scratch/` with the hypothesis removed, run `scripts/vcheck`, paste verbatim, the learner reconciles first. This is the one sanctioned use of the learner's own statement in a probe, and an error here shows only that the verifier cannot prove it, not that it is false.
3. **Design**: defend a design decision: a representation, an invariant, or a trust boundary as the trust ledger states it.
4. **Connect**: tie the artifact back to an earlier module (a backward edge).
5. **Transfer**: the artifact's central idea on unfamiliar ground.
6. **Ledger**: one fresh question from this module's ledger entries; if there are none, a second predict-what-breaks.

A re-defense instantiates fresh questions, disjoint from every earlier defense record of the module.

**Assisted.** Take the maximum `hint-depth` over this module's ledger lines with `source: tutor`. If it is ≥ 1, the gradebook grade cell carries `assisted (max hint-depth N)`: a record of how the work was done, not a penalty; say so in the report.

## Grading — per question, then outcome

The verdicts are yours (CORE.md §Grading vocabulary, §Session hygiene): no subagent, Workflow, panel or vote; one examiner, one verdict per question, given in this session.

Per question: **SOLID / SHAKY / MISSED**, each anchored to the **target-insight bullets** (the bank question's, or for a defense the instantiated anchors written before asking) and justified with a **quoted** learner phrase, or the quoted absence of one ("never mentioned what the invariant says about the unprocessed part"). No anchor bullet, no verdict: if the answer is outside the anchors, say so explicitly and grade conservatively as SHAKY.

| outcome | 6-question exam (module, defense) | 5-question exam (tier) |
|---|---|---|
| **PASS** | no MISSED, at most one SHAKY | no MISSED, at most one SHAKY |
| **PASS-WITH-REVIEW** | at most one MISSED and at most three SHAKY | at most one MISSED and at most two SHAKY |
| **REVIEW** | anything weaker | anything weaker |

A predict that drift voided is left out of the count, and the record says so. PASS-WITH-REVIEW is passing, but every SHAKY or MISSED item goes into the ledger for `/review`. REVIEW: recommend the chapter sections named per missed anchor, then a re-viva (a disjoint draw).

The outcome is **advisory, never blocking**: say so in the report. The learner proceeds when they choose.

## Write-up

1. `instructor/records/<ID>_viva_YYYY-MM-DD.md` (module and tier modes) or `instructor/records/<ID>_defense_YYYY-MM-DD.md`: each question (scoped bank id, or the defense template with its instantiation and anchors), the learner's answer quoted or faithfully summarized, the verdict with its anchor bullets cited, the probe transcript of every predict question, and the outcome. A tier record lists the tier's modules and names its draw (the bank's letter, or the scoped ids); a defense record states the gate status and the assisted line. If a record of that name exists (a re-viva the same day), append `-2`, `-3`, … (`Q03_viva_2027-02-06-2.md`); never overwrite a record.
2. One ledger entry per SHAKY or MISSED (CORE.md schema, `source: viva`, `hint-depth: 0`, box 1, `due:` tomorrow), tagged with the module the question came from: a tier question drawn from Q05's bank is `Q05/<tag>`, whatever id the viva ran under.
3. One gradebook row: `| YYYY-MM-DD | <ID> | viva | PASS/PASS-WITH-REVIEW/REVIEW | <n> ledger items |`; for a defense, track `defense`, with `assisted (max hint-depth N)` appended to the grade cell when it applies.
