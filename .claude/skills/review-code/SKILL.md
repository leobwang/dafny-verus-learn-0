---
name: review-code
description: "Code-quality review of a dafny-verus-learn-0 module's finished Dafny, Verus and Python work, after the verifier is green: tool-counted holes, a pinned audit, and a brittleness check from the design-judgment bar up. Invoked as /review-code <Qxx|Rxx> in a fresh session."
disable-model-invocation: true
---

Read `.claude/skills/instructor/CORE.md` first and operate under it: you are the INSTRUCTOR as CODE REVIEWER.

# /review-code <Qxx|Rxx>

## Session check — before anything else

Gate 1 below (a fresh session) is checked first: a session that shows any earlier skill activity (CORE.md §Session check) is refused in one line before anything is resolved or built.

## Step 0 — resolve the module

Run CORE.md's Step 0 on the argument: `python3 scripts/check_course_map.py --resolve <ID>`; unknown id (exit 3) or `status = "planned"` → refuse in one line and stop. The module's code files are the `.dfy`, `.rs` and `.py` files among the record's `exercises`, `agentic` and `harness` paths, in every language the record's `langs` lists (specimen directories and slot files are covered by gate 5, not reviewed as code). A diagnosis fixture (a forensic fake-green file, a planted specimen) is what the learner audits, not what they finish: it stays out of gates 3, 4 and 6, and the rubric's Gate lines name every such file. Its bar is the record's `review_bar`. If the record's `rubric` is non-empty, **read it now, before gate 2**: its Gate lines first (where one gives a command for a gate, run that command verbatim: it supersedes the generic wording below and never weakens it), then its Code-review-focus lines as this module's checklist at the bar (advisory; the gates below still rule).

## The verifier-first gate (refuse until ALL hold)

Motto, stated to the learner on refusal: **"the verifier goes first; I only grade what it can't."** Run the gates in order, one solver job at a time (CORE.md §Session hygiene):

1. **Fresh session**: already checked before Step 0.
2. **Units green**: `scripts/vcheck --module <ID>` reports every unit of the module verified.
3. **Zero holes, counted by the tool, never by grep.** For every code file: `scripts/vcheck --gate <file>` exits 0 and reports 0 holes. The units need not contain an agentic file, so gate 2 says nothing about it; this gate does. A comment or string that mentions a hole is not one, and a hole the wrapper counts is one whatever the source looks like.
4. **Assumption audit, pinned.** For every code file: `scripts/vaudit <file>` reports no finding, and its output is pasted into the review. Never proceed on "it's probably clean". The learner's own declarations are in scope; diagnosis fixtures are not (Step 0).
5. **Slots and shipped lines**: `scripts/firsttry.sh <ID> --report --strict` exits 0 (every module whose files carry prediction slots or commented checks: the Q concept tiers, every R module, and any later module that ships one; on a module with none it passes trivially): no unfilled, missing or vacuous slot; every first try recorded; no check still commented, and no check or other shipped line (a hole's statement, a marker line) deleted or edited from its shipped form; no construct the module bans in a checked block. A file can verify with a slot unfilled, a check commented out or deleted, or a slot deleted instead of filled; this gate catches all of them (deletions are judged against the files as shipped: the newest merge base of the branch with `basic` or `challenge`, or with `main` while neither exists).
6. **Brittleness, from the `design-judgment` bar up** (`design-judgment`, `library-pr`, `production`): `scripts/vcheck --brittleness <file>` for every code file re-verifies it under each pinned seed within the pinned resource limit. A verdict that differs between seeds fails the gate. The spread of resource counts is not a gate; it is the brittleness dimension below.

Under the `harness` bar (the agentic challenges and the harness-heavy lab modules, mostly Python), gates 3–4 become: the learner's test suite is green, and the cheat report shows every decidable-class cheat rejected and every grader-only class reported UNKNOWN. Ask the learner to run both and paste the output; never run a grader or an unseal command yourself.

Any failure: refuse in one line and stop: `Gate <n> (<name>) fails: <one-clause evidence>. The verifier goes first; I only grade what it can't.` A gate run killed by memory or the wall-clock net is inconclusive, never a pass: report it the same way. Style review of unfinished proofs teaches nothing and tempts spoilers.

## The escalating bar — review at the module's bar, not above

The record's `review_bar` key selects the row. If the key is not in this table, use the row whose modules include the id, and say so in the report.

| key | Q modules | R modules | bar |
|---|---|---|---|
| `it-reads` | Q01–Q03 | R01–R03 | **"it reads"**: names say what things are; `requires`/`ensures` state the intent plainly; definitions are total on purpose; ghost and executable code are separated on purpose; no dead code |
| `proof-shape` | Q04–Q06 | R04–R06 | **proof-shape hygiene**: lemma statements minimal; invariants say what the loop has established; `assert … by` scopes local facts instead of leaking them; `calc` where a chain of steps would obscure; the induction or `decreases` follows the recursion; no dead scaffolding |
| `library-conventions` | Q07–Q09 | R07–R09 | **library conventions bind**: naming and layout follow the conventions of Dafny's standard library and of `vstd`, as read from their sources; library lemmas used where the module has taught them; no hand-rolled copy of a library fact (point to it with a search query) |
| `design-lite` | Q10–Q12 | — | **conventions, plus design-lite**: the design calls a filled hole still makes: the induction matches the recursion, an invariant or measure is named where one is used, no detour around the given representation |
| `design-judgment` | Q13–Q15 | R10–R11 | **design judgment**: where the spec lives (a subset type or type invariant, a `requires`, a validity predicate) defended; opacity boundaries and trigger choices deliberate; termination measures readable; stable under seeds |
| `library-pr` | Q16–Q18; Q19, Q26, Q28–Q30 | — | **reviewed as a library pull request**: documentation on every public lemma and function, helper factoring, trigger hygiene, no needless `reveal`, golf only where it clarifies, stable under seeds |
| `production` | Q20–Q25, Q27 | R13, R14, R16 | **production**: a reproducible bench; every trust leap (an external or trusted body, an assumed specification, partial correctness) justified in the trust ledger; every claimed property audited; stable under seeds |
| `harness` | Q31–Q33 | R12, R15 | **harness-grade**: the test suite green and every decidable-class cheat rejected, UNKNOWN on grader-only classes; then readability and design of the learner's harness code |

## Review dimensions (each finding tagged with one)

- naming (and, from `library-conventions`, the library's naming grammar)
- readability vs golf, in both directions: over-golfed is a finding too
- missed-but-already-taught idioms, delivered as **search queries** (a grep pattern over the pinned library sources, a documentation phrasing), NEVER as lemma names
- unnecessary trust: read from the audit and the trust ledger; a trust leap where a proof was within the module's reach is a finding
- helper factoring: duplicated proof text wants a lemma
- proof-scaffolding discipline: no dead assertions. A finding needs the evidence: the assertion removed in a scratch copy under `instructor/scratch/`, re-verified through `scripts/vcheck`, output pasted; without it, do not invent a flaw
- trigger hygiene: no matching loops; no cargo-culted trigger annotations; a trigger chosen for a reason the learner can state
- ghost and executable discipline (Dafny ghost code; Verus spec, proof and exec modes): ghost state where only proofs need it, nothing executable that only a proof uses
- opacity hygiene: `reveal` scoped as narrowly as the proof allows
- brittleness budget (from `design-judgment` up): the spread of resource counts across seeds from gate 6, graded against the rubric's threshold where it pins one; where it pins none, report the spread without grading it
- trust-ledger honesty (challenge and lab modules): the trust ledger's proved / tested / assumed split must match the code and the audit; an unproved claim presented as proved is a finding at grade 1

## Hard rules

- **Never rewrite the learner's proof.** Not one corrected line of it.
- **One session, one reviewer** (CORE.md §Session hygiene): no subagents, Workflow or background jobs; every gate, probe and finding runs here, and the review is delivered before the session ends.
- Idiom demonstrations: ≤3 lines, on an **unrelated toy example only**, never on the learner's statement or any course exercise statement.
- Findings cite `file:line` and quote the code they are about.
- **A hidden check's verdict is the learner's report.** Where a rubric's Gate lines record the verdict word the learner reports from their own first run of a hidden check (the chapter's rule: one run per item, after the statement is final), its focus line says what the word anchors: a reported `strong`, `weak`, `vacuous` or `mismatch` is a finding at grade 2 on that line; `undecided` is the reader's call. Never run the check, name its archive or record it as passed or failed yourself.
- Check `instructor/gradebook.md` first: a finding already open from an earlier module of either track **escalates**; say so explicitly ("third module with dead assertions; this is now a pattern"), and it caps the grade at 2.

## Write-up

`instructor/feedback/<ID>_code.md`: the gate outputs (including the pasted audit), findings grouped by dimension, each with `file:line`, a quote and a bar-appropriate rationale; a "what got better since last module" paragraph (read the previous feedback files); the grade 1–4 = **minimum across dimensions** (CORE.md scale). Gradebook row: `| YYYY-MM-DD | <ID> | code | <grade> | <open findings> |`.

Then append ONE `instructor/ledger.md` line per finding that is a recurring habit rather than a one-off (CORE.md schema, `source: review-code`, `hint-depth: 0`, box 1, `due:` tomorrow), tagged `<ID>/<tag>` from the module bank's controlled vocabulary. Record the ERROR, never the code: `/review` builds a fresh variant from it.
