# DV6 lab2 lane: Lab 2's public cards and Lab 1's draw under the user's decisions D27-D30

Author-only notes (reference class). The lane's brief: build D27 (a public Lab 2 delivery may
add proof annotations, never executable code; the lab gate checks the code unchanged; S1's kill
rate mutates the delivery's annotated code), D28 (the public forms also remove the
non-recursive definitions only the specification uses, sealed with the reference as
`definitions`; rebuild, re-run C1, C4, C6 and C7 on the same draw, re-seal Q15, re-confirm
`HIDDEN_CHECKS_HELD`'s Q15 manifest), D29 (keep `bench/local/q/lab2pub/` tracked with a NOTICE)
and D30 (Lab 1's draw excludes Lab 2's five Verus tasks), then attest the ten public cards
through the scan. Like Δ195-Δ233 this file names no reference statement, no weakened statement
and no sealed definition (counts only), and no key material. Memory share 16 GB: every solver
job one at a time through the wrappers inside `systemd-run --user --scope -p MemoryMax=16G -p
MemorySwapMax=0` (`free -g` 84-94 GB available at each start), the grader containers one at a
time (Dafny at its 11.5 GB bound, Verus `--mem-gb 16`). No job was killed. Scratch
`/tmp/dvl0-dv6-lab2/` (removed at the end); archive
`~/.cache/dafny-verus-learn-0/author-probes/dv6/lab2/` (drivers, counts, verdict-level
outputs and the pre-seal archive; no plaintext of the hidden truth: the brief keeps it in
scratch, so a later re-seal of Q15 starts by decrypting the archive, as this lane did).

## 1. What was built

| file | what |
|---|---|
| `scripts/dvl/labcode.py` (new) | D27: `card_rule` (the rule of a task form by its course path: `bench/local/q/lab2/` "spec", `lab2pub/` "annotations", anything else none), `skeleton` (a file's code skeleton: its tokens with the allowed additions erased), `code_findings` (`lab-code-changed`, `lab-code-unchecked`), `mutant_source` (S1's mutant source) |
| `scripts/vcheck` | `lab_gate(..., code=True)`: after the lever check, the code check on a Lab 2 card; `--lab-code own` waives it (refused without `--lab-task`); the usage text |
| `scripts/dvl/benchstrip.py` | D28 in both Lab 2 transforms (`split_definitions`; `Lab2Form.definitions` and `definition_names`); `definition_residue` (an independent check on a form alone); the Verus form drops the comment lines above a removed proof statement separated by one blank line (`_comment_above`; DV5e's integration item on vp2); docstrings and `TRANSFORM_NOTES` |
| `scripts/dvl/lab2pub.py` | the form header names what a delivery adds (definitions, Verus `pub open`, proof annotations, never executable code); `reference` returns the sealed definitions; `reference_toml` (the sealed `reference.toml` text, with `definitions`, `definition_names` and the kill fields); `draw_of_records` and `forms_date` (a rebuild on the recorded draw through `record`); `notice_text` and `build [--check]` writing or comparing NOTICE (D29); `STRATUM_HEAD`; the C6 line of the docstring |
| `scripts/dvl/bench.py`, `scripts/get_bench.sh` | D30: `lab_members(root, set, lab)` and `get_bench.sh --members SET --lab LAB [--seed S]` (the pool less every task another lab's `[[draw]]` took; sorted or in the seeded order) |
| `bench/local/q/lab2pub/` | the ten forms rebuilt on the same draw (new `form_sha256` values), `STRATUM.toml` (header, `forms_date = "2026-10-14"`), `NOTICE` regenerated |
| `bench/local/q/lab1/STRATUM.toml`, `paper/Q12_answers.tex` (B1's tasks-and-strata field), `docs/Q12_PracticeIC.md` §4.3 | D30's rule and the command |
| `docs/Q15_PracticeIIC.md` | §0 (the rule is fixed), §6.1's S1 row (mutants of the delivery's annotated code on a public card), §6.2 (the form with D28, what a delivery adds, the lab gate's code check and `--lab-code own`, S1's mutant source) |
| `Hidden/labs/Q15/verdicts.tar.age`, `sandbox/truth.toml` | re-sealed (§4) |
| `scripts/check_course_map.py` | `_Q15_MAN`, the DV6 manifest, and the comment that records the comparison |
| `sandbox/attested.toml`, `sandbox/README.md`'s attested row | the 78 entries re-scanned after the re-seal and the ten public cards attested (§6): 88 entries |
| `tests/wrappers/test_lab_code_static.py` (new, 16 cases) | §7 |
| `tests/bench/test_lab2_forms.py` (60 → 74 in `tests/bench`) | §7 |

## 2. D27: the code check and S1's mutant source

**The rule.** Every Lab 2 delivery may add the target's specification (and its other signature
clauses), one witness call (the witness's body is the delivery's), and declarations that are
not executable code: definitions (Verus spec fns; Dafny functions and predicates the code does
not reach) and lemmas (Verus proof fns; Dafny lemmas and ghost methods). On a public card it may
also add proof annotations: Verus `assert`, `assert … by`, `proof { … }`, proof macros, `let
ghost`/`let tracked`, `reveal`, `broadcast use` and every loop clause (invariants and the loop's
`decreases`); Dafny `assert` (with `by`), `calc`, `reveal`, ghost variables and their updates,
proof `forall` statements, lemma calls and every loop clause. Everything else must be the task
form's token for token (comments and layout aside). `code_findings` compares the two code
skeletons per declaration and names the declarations that differ, never code. A local card's
delivery that adds proof annotations gets a finding that says they are a public card's.

**Where.** `vcheck --gate --lab-task <form> <delivery>` applies it after the lever check, by the
form's course path (the verification container stages the form at `lab-task/<course path>`,
so the rule reaches the container route unchanged). `--lab-code own` waives it for an arm that
writes its own code (§9 item 3).

**S1's mutant source.** `labcode.mutant_source(form, delivery)`: on a public card the target's
body is the delivery's (annotations kept), on a local card the form's (equal to the delivery's,
since the code is unchanged); the text around the declaration is the delivery's. The chapter
(§6.1, §6.2) states it for the learner's S1 arm.

**Measured on the real tools** (16 GB scope): C6 below (the ten reference programs, which carry
the upstream proof annotations, pass the lab gate with the code check); a public reference
program with one executable literal changed: `failed` with `lab-code-changed` (and its
verification error); the same with `--lab-code own`: `failed` on the verification error alone;
a local reference program through the lab gate: `verified`; the same with one `assert true;`
added: `failed`, `lab-code-changed` (6 verified). Statically, every drawn answer with the
form's witness added is a delivery of its form; the 30 shipped Lab 2 forms pass against
themselves; the sealed local reference programs (20) pass under the local rule.

**The reference oracles' kill rate on the annotated code** (sealed in each public
`reference.toml`; host runs, one job at a time; the reference oracles' `mutants` over the
reference program's annotated body, each mutant run with the reference statement and, as a
baseline, with its requires alone):

| card | mutants | killed | survived | unknown | killed without the ensures | killed by the ensures only |
|---|---|---|---|---|---|---|
| vp1-he100 | 34 | 31 | 2 | 1 | 28 | 3 |
| vp2-he033 | 92 | 74 | 13 | 5 | 74 | 0 |
| vp3-he077 | 34 | 30 | 4 | 0 | 29 | 1 |
| vp4-he035 | 12 | 11 | 1 | 0 | 8 | 3 |
| vp5-he060 | 30 | 21 | 9 | 0 | 20 | 1 |
| dp1-he048 | 25 | 24 | 1 | 0 | 21 | 3 |
| dp2-he052 | 14 | 14 | 0 | 0 | 11 | 3 |
| dp3-he063 | 20 | 20 | 0 | 0 | 10 | 10 |
| dp4-he159 | 3 | 2 | 1 | 0 | 0 | 2 |
| dp5-he062 | 35 | 32 | 2 | 1 | 28 | 4 |
| all | 299 | 259 | 33 | 7 | 229 | 30 |

Every unmutated program verified under both specifications. dp3 and dp4 (no annotations; DV5e
measured 20/20 and 2/3 on the shipped code) are unchanged. On the eight annotated cards most
mutants fail whatever the ensures says (the invariants and assertions, which the mutation also
reaches, no longer hold): 229 of the 259 killed mutants are killed without the ensures, so on a
public card the kill rate mostly measures the annotations, not the specification (vp2: 74 of 74).
This is D27 as decided; what to do about it is §9 item 1.

## 3. D28: the forms, the sealed definitions and the re-run checks

**The rule as built** (`benchstrip.split_definitions`, both languages): a definition stays
when the code reaches it, when it is recursive and the specification reaches it, or when a kept
definition names it; a definition only the specification reaches and that is not recursive
leaves the form and is returned (its declaration's text; Verus made `pub open`) for the sealed
reference; Verus spec fns nothing kept names are removed as before (proof-only); Dafny
`<vc-helpers>` definitions as before. Recursion is a cycle in the definitions' call graph.
`definition_residue` checks a form alone: a non-recursive definition that no code names and no
recursive definition reaches is a finding (0 on the ten forms; on the DV5e forms it finds
exactly the twelve definitions the rebuild removed).

**The rebuild** (`lab2pub.record(draw_of_records(root) + forms_date)`): the same draw (the
`[[draw]]` records byte-identical, POOLS.toml unchanged), ten new forms, `STRATUM.toml`'s
`form_sha256` values and header. Six cards lost definitions (12 in all: Verus 2 cards × 1;
Dafny 4 cards, 1, 1, 5 and 3); vp1, vp4, vp5 and dp3 kept theirs (recursive or reached by the
code). vp2's form also loses the comment lines above its removed proof block (the DV5e
integration's item). The header now names the additions (§2) and, for Verus, that a spec fn
the specification names must be `pub open` (the grader's lemmas are public).

**C1** (static, `lab2pub.static_check`): 10 of 10 (the answer a delivery of the form by
`dvl.judge.lab_ok`; with D27 also by the code check, §2). **C4** (`vcheck --json` on each form):
10 of 10 reach the verify stage (dp1, dp2, dp4, dp5 verify as shipped; dp3 and the five Verus
forms fail, as at DV5e). **C6** (each reference program, the DV5e program under the new header,
through `vcheck --gate --lab-task <form>`: the lever check, the code check, the audit): 10 of 10
verified, 0 holes, verified counts 3-11. **C7**: §5. `lab2pub.py build --check`: 10 cards and
the NOTICE current.

## 4. The re-seal

Plaintext: the DV5e archive decrypted into scratch (its sha256 and manifest checked against
`truth.toml`; identical to DV5e's archived plaintext), the ten public cards' reference programs
(new header; the old programs' header lacked the form's last line) and `reference.toml`
(`lab2pub.reference_toml`: the statement, `definitions`, `definition_names`, `mutants`,
`mutant_source`, `killed_by_reference`, `survivors`, `unknown`, `killed_without_ensures`,
`unknown_without_ensures`, `killed_by_ensures_only`) rewritten, `SEALING.md` extended, the
manifest regenerated (the regeneration reproduces the DV5e manifest byte for byte on the DV5e
tree). `sandbox/seal_hidden.py Q15 --src`: 72 files, archive sha256 `711cc58b…07a1`, plaintext
manifest `186263f6…129e`; `truth.toml` re-pinned by the tool. The DV5e archive and pins are kept
in the archive's `preseal/`.

**`HIDDEN_CHECKS_HELD`.** The two manifests compared: 21 entries changed, all the ten public
cards' files and `SEALING.md`; the six prose references, `judge/oracles.py` and `DVLCANARY`
byte-identical; no file added or removed. `_Q15_MAN` now names the DV6 manifest, and the six
references were judged faithful against themselves again in the container (§5).
`check_course_map.py` OK.

## 5. The grader container (the new seal; one container at a time)

| run | result | wall |
|---|---|---|
| `manifest` | ok, 72 files | 0.5 s |
| `judge` cards, Dafny, 14 candidates | as recorded beforehand (`expected.json`, sha256 `ed8b6a59…0d87`): 5 reference programs faithful, 5 weakened statements weak, 4 deliveries that state their own (renamed) definitions faithful | 45 s |
| `judge` cards, Verus, 12 candidates | 5 faithful, 5 weak; 1 own-definitions delivery faithful (vp2) and 1 **undecided** (vp3; §9 item 2) | 56 s |
| `judge` prose, the six sealed references against themselves | 6 of 6 faithful (H3d, H4d, H5d; H3v, H4v, H5v) | 110 s, 65 s |
| `validate` (by `--cards`, per language and stratum) | 10 public and 20 local reference programs verified, 0 holes | 5-14 s each |

A host dry run of the same judging function on the staged plaintext (before the seal) agreed on
all 26 card rows. 71 sealed strings (the public references' clauses, split at clause lists, and
their definitions; the prose references' clauses; the canary token) searched in the 18 host
output files, also with whitespace removed: 0 hits. No container or run directory left.

## 6. Attestation (after the grading lane's D31 landed)

`mksandbox-run --author --attest-rescan` after the final seal: 78 of 78 re-attested under DV6
(the sealed twins now include the new public references). Then `--author --attest` on each of
the ten public cards: 10 attested under DV6, 0 refused (`refs = "68 twins, sha256
77a7234b…"`). `sandbox/attested.toml` holds 88 entries; every Lab 2 card's current sha256 is
attested (30 of 30). The header and `sandbox/README.md`'s attested row say so.

## 7. Tests

- `tests/wrappers/test_lab_code_static.py` (new, 16, static): on invented public cards in both
  languages an annotation-only delivery passes; one executable edit fails (the message names the
  declaration, not the code); an added exec fn or method fails; a changed function the code calls
  fails, a changed unused definition does not; a loop measure and the witness body are the
  delivery's; an unreadable pair is unchecked, never a pass; on invented local cards the
  specification and the witness pass and proof annotations fail with their own message; the rule
  by course path (container prefix included; Lab 1, the oracle layout and Lab 3 none); `lab_gate`
  fails a code change, `code=False` passes it, the audit does not run after it; the CLI refuses
  `--lab-code` without `--lab-task`; S1's mutant source is the delivery's annotated body on a
  public card and the shipped body on a local one; the 30 shipped Lab 2 forms pass against
  themselves.
- `tests/bench/test_lab2_forms.py`: D28 on invented text (Verus and Dafny: what is sealed, kept,
  published; the split rule; `definition_residue` on a kept and a planted definition; the
  comment above a removed proof step; truthcheck's `_renamed` renames the sealed definitions and
  keeps a candidate's word-for-word one); the shipped forms (no non-recursive specification-only
  definition; the header's additions; `forms_date`); NOTICE (each set's name, repository,
  commit, SPDX licence and check date from `bench/manifest.toml`, both licence texts, D28 and
  D29; with the sets installed, the file equals `notice_text`); D30 (`lab_members` gives 78
  HumanEval-Verus members, none of Lab 2's five, the pool's union; Lab 2's own and DafnyBench's
  whole pools; `get_bench.sh --members` prints them sorted and in the seeded order and needs
  `--lab`; the rule's sentences in the stratum file, the chapter and B1's field); with the sets
  installed, the sealed definitions travel with the reference (`reference` and
  `reference_toml` carry exactly the form's removed definitions, each word for word in the
  answer, none in the form) and each drawn answer keeps its form's code.
- The invented Verus fixtures were reshaped until the scan's `ScanIndex.hits` found no twin span
  in them (the first shapes matched Q02's and Q05's answers renamed); the two Python files keep
  one renamed hit each (a Python test method against a Dafny twin, a Python loop against the gate
  v2 twin: generic structure, as DV5e's review found for scripts).

Runs on the final tree: `tests/bench` 74 OK; `tests/wrappers` `test_lab_code_static.py` 16,
`test_practice_tools_static.py` 39 and `test_tools_static.py` 113 (1 skipped) OK;
`check_course_map.py` OK; `pins.py --ci --module Q15` (60 pins) and `--module Q12` (32) 0
problems; `update_rubric_pins.sh --check` 111 current; `specfreeze --check Q15` 0;
`chapter_lint --all` 18 chapters, 0 problems; the leak README's verifier, 18 modules over 1,634
public files, OK; `check_single_route.py` clean; `scripts/ci.sh --author --job static --job
harness --job hook-test` and the lab gate's tool tests: §10.

## 8. Deviations and readings

1. **The code check covers the local cards too** (the rule "spec": specification, witness,
   definitions and lemmas; no proof annotations). D27 names the public cards; the local stratum
   file already said a delivery "changes no code (arms S0 and S1)", and nothing enforced it. Any
   arm that changes code on any Lab 2 card is refused by the plain lab gate, which is what makes
   §9 item 3 a question for both strata.
2. **A lab gate input, not a plan field:** the rule is read from the task form's course path,
   so no frozen-core file changed; the waiver is a `vcheck` option the batch cannot pass yet
   (§9 item 3).
3. **What counts as code in Dafny:** a function or predicate the code reaches is code (Dafny 4
   compiles them), one it does not reach is a definition; a delivery may add either kind, and
   may change only those the code does not reach (the judge's host half still refuses a changed
   shipped definition as `task-form`).
4. **The kill-rate baseline** (requires alone) is this lane's addition to D27's measurement; it
   is reference-free and is recorded beside the rate in each sealed `reference.toml`.
5. **The plaintext stays in scratch** (the brief), unlike DV5e's `hidden-src/` copy, which is
   now one seal behind; a later re-seal decrypts the archive.
6. **`get_bench.sh --members`** is beyond D30's text (the rule and a test): it gives the learner
   the 78 members in their seed's order, which the learner-visible audit asked for (its Lab 1
   draw item); the pilot's procedure is still not written.

## 9. Open items

1. **DECISION NEEDED (the user; high: before Lab 2's runs on the public strata). S1's kill rate
   on a public card measures the annotations.** 229 of the 259 mutants the reference statement
   kills on the ten public cards are killed by the requires alone (the proof annotations no
   longer hold for the mutated code); on vp2 all 74 (§2). Options: (a) S1's feedback on a public
   card counts only the mutants that verify under the candidate's requires alone (each mutant
   run once more without the ensures: reference-free, about twice S1's runs per sample; the
   kill rate's denominator becomes the live mutants) (recommended: it keeps D27's mutant source
   and makes the rate about the specification again); (b) keep D27 as built and record the
   limit (the report gives S1 − S0 per stratum and says the public kill feedback is weak); (c)
   on a public card S1's feedback drops the kill rate and keeps the vacuity and witness checks.
   **(d), added by the DV6 fix round (before this goes to the user):** on a public card S1
   counts only the mutants whose code skeleton differs from the unmutated delivery's
   (`labcode.code_mutant(task, delivery, mutant_body)`: the delivery's skeleton with the
   proof annotations erased, `labcode.skeleton(…, annotations=True)`); a mutant that changes
   only an invariant, an assertion or another annotation tests no specification and is
   dropped before any run (no solver cost; reference-free; combinable with (a)). Measured
   statically (in memory, counts only) on the ten sealed reference programs' annotated bodies
   with the reference `mutants()`: 299 mutants, 107 change code, 192 change only annotations
   (vp2 92 → 10; dp3 and dp4 lose none). The killed / killed-without-ensures re-measure on the
   107 needs one solver run in the grader container (not run by the fix lane). Recommended
   with the fix lane's reading: (d) with (a), so the denominator is the code mutants that
   verify under the requires alone.
2. **DECISION NEEDED (the user; medium). A sealed definition used under a quantifier.** A
   faithful delivery that states its own (renamed) version of a sealed definition is judged
   faithful on five of the six cards that lost definitions, and `undecided` on vp3, where the
   reference's specification applies its one sealed definition inside an existential: the
   grader's empty lemmas cannot instantiate across two differently named functions (`undecided`
   counts as unfaithful for a card). A delivery that states the definition word for word, name
   included, keeps it and is judged faithful. Options: (a) keep in the form a definition the
   reference's specification applies under a quantifier, as a recursive one is kept (vp3's form
   gets its one definition back: rebuild, C1/C4/C6/C7, re-seal, `HIDDEN_CHECKS_HELD`'s
   manifest, re-attest) (recommended: the same reason as the recursive exception); (b) keep as
   built and record the limit (vp3's faithful deliveries over their own vocabulary are judged
   `undecided`; `/review-code`'s reader cannot rescue a batch verdict); (c) the grader's lemmas
   add each sealed definition's unfolding as a trigger hint (an image change and rebuild).
3. **DECISION NEEDED (the user, or the tools owner if delegated; high: before the vericoding arm
   runs). The vericoding arm and the code check.** The plain lab gate now refuses a delivery that
   changes a Lab 2 card's code; arm V writes its own code, and `fvh.batch` (and
   `fvh.report --reverify`, the agent route) passes only `lab_task` to the gate, so V's Verifies
   on any Lab 2 card fail. Options: (a) a per-arm plan field (`lab_code = "own"`) that the batch
   records in the run and passes through `ContainerRunner` as `--lab-code own`, so a re-verify
   repeats it (a stable-interface addition, DV4-PLAN §13) (recommended); (b) V gets its own task
   forms (each card with its body removed) in a third stratum directory, which the code check
   does not cover (a stratum file, a seal of nothing new, an attestation); (c) the gate checks
   the code only when the plan asks for it (S0 and S1 opt in), the reverse default.
4. **The tools owner (medium). S1's feedback route in a live batch.** A policy holds no tool,
   and `fvh.tools`' instruments have no mutant-kill run, so I found no route by which S1's
   reference-free feedback reaches the policy in `fvh run`; `labcode.mutant_source` gives its
   mutant source when one is built.
5. **The records and integration lanes (low).** QPLAN §25.6's **As built** (D27, D28, D29, the
   rebuilt forms, the sealed definitions and kill rates) and §22.6 (D30, `--members`); DV4-PLAN
   §7.1-§7.3 (`--members`, `lab_members`) and §13 (the stable-interface additions: `vcheck
   --lab-code own`, `dvl.labcode`, `get_bench.sh --members`); `CLAUDE.md`'s **Armed** line (the
   public-delivery rule is fixed; the ten public cards attested; 88 entries) and its `vcheck`
   usage (`--lab-code`); `README.md`'s Status (Lab 2's public runs no longer wait on a rule);
   `VERSIONS.md` §1.4's judging row (Q15's DV6 seal `711cc58b…07a1`, 72 files, oracles
   unchanged); DV5e's lab2pub notes §9 items 1-4 and 7 are closed by D27-D30 and §6, and its
   `hidden-src/` copy is one seal behind.
6. **The kits lane (low).** Rubric Q12's CT row could check B1 names the draw's members without
   Lab 2's five (D30); the Q15 fixtures' strata lines, if they quote the form's description.
7. **Carried (tools owner):** truthcheck's base check on obligation-free definitions (`context`),
   and `validate --truth-lang`'s argv limit (this lane validated by `--cards`).

## 10. CI on the final tree

`scripts/ci.sh --author --job static --job harness --job hook-test` (16 GB scope; log
`build/ci/20261014T160241Z-386182/`): static PASS (446 s), harness PASS (76 s: `tests/core`,
the adapter suite, `tests/sandbox`, `tests/bench`), hook-test FAIL (173 s): `test_hooks.sh` 6,811
passed, 1 failed, and the one failure is the grading lane's new `mksandbox-run --attest-rescan`
(D31), which the hook refuses as author-only while `test_hooks.sh`'s `AUTHOR_OPTS` does not
list it: not this lane's change (`get_bench.sh --members` raised nothing); for the grading lane
or the integration lane. `tests/wrappers/test_practice_tools_tool.py` (the lab gate on the real
tools) 12 OK. The full `--author` and study runs are the integration lane's.

## 11. DELTAS-ready text (for the integration lane to number)

### Δ2xx · Lab 2's public cards and Lab 1's draw under the user's decisions D27-D30: the lab gate's code check and S1's mutant source, the specification-only definitions sealed, the forms rebuilt and Q15 re-sealed, the NOTICE generated, Lab 1's draw without Lab 2's five; the ten public cards attested — adopted (DV6, 2026-10-14; applies the user's decisions D27-D30)
- **Status:** applies the user's decisions D27, D28, D29 and D30 (Δ232 items 1-4, each option (a)/(b) as recommended) and closes Δ233's attestation item for Lab 2's ten public cards (after D31's scan, built by the grading lane). Three readings it measured are the user's (the open items). Like Δ195-Δ233, it names no answer, no reference statement, no weakened statement and no sealed definition. Detail: `Solutions/plans/DV6-lab2-notes.md`.
- **Change:**
  - **D27, the code check.** `scripts/dvl/labcode.py` (new): `card_rule` (by the task form's course path: `bench/local/q/lab2/` the local rule, `lab2pub/` the public rule; any other form no check), `code_findings`, `skeleton`. A Lab 2 delivery keeps the task form's executable code token for token; it may add the target's specification, one witness call, definitions and lemmas, and on a public card proof annotations (loop clauses, assertions, `calc`, `reveal`, proof blocks, ghost variables, lemma calls; never executable code). `scripts/vcheck --gate --lab-task` applies it after the lever check (`lab_gate(…, code=True)`): `lab-code-changed`, or `lab-code-unchecked` for a pair it cannot compare, and the verdict failed; a local card's delivery that adds proof annotations is told they are a public card's. `--lab-code own` waives it for an arm that writes its own code. The local cards take the check too (their stratum already said a delivery changes no code). **S1's mutant source:** `labcode.mutant_source` (the delivery's annotated body on a public card, the shipped body on a local one); the Q15 chapter's §6.1 and §6.2 say it.
  - **D28, the definitions.** `scripts/dvl/benchstrip.py`'s Lab 2 transforms remove the definitions only the target's specification reaches that are not recursive and return them (`split_definitions`, `Lab2Form.definitions`; Verus made `pub open`); what the code reaches stays, and so does a recursive definition with all it names; `definition_residue` checks a form alone. `scripts/dvl/lab2pub.py`: the header names what a delivery adds (Verus: a spec fn it names is `pub open`); `reference` and `reference_toml` carry the sealed `definitions` and `definition_names`, which truthcheck's judge already renders renamed beside a delivery's own (`_renamed`). The ten forms rebuilt on the same draw (`record(draw_of_records(…))`, `forms_date`; the `[[draw]]` records unchanged): six cards lost 12 definitions; vp2's form also drops the comment above its removed proof block. C1, C4, C6 (now through the lab gate with the code check) and C7 re-run (Why).
  - **The re-seal.** `Hidden/labs/Q15/` re-sealed from the decrypted DV5e archive with the ten public cards' reference programs (new header) and `reference.toml` (the sealed definitions; the reference oracles' kill rate on the reference program's annotated body, with the reference statement and with its requires alone); `SEALING.md` extended; 72 files; `sandbox/truth.toml` re-pinned by the tool (archive `711cc58b…07a1`, manifest `186263f6…129e`). The manifests compared: only the public cards' files and `SEALING.md` changed, so `check_course_map.py`'s `HIDDEN_CHECKS_HELD` names the DV6 Q15 manifest (`_Q15_MAN`), and the six prose references were judged faithful against themselves again.
  - **D29, the NOTICE.** `lab2pub.notice_text` writes `bench/local/q/lab2pub/NOTICE` from `bench/manifest.toml` (each set's name, repository URL, commit and SPDX licence with its check date and method) and the installed `LICENSE` files (their text and sha256), with the change statement (D28 included); `lab2pub.py build [--check]` writes or compares it.
  - **D30, Lab 1's draw.** `scripts/dvl/bench.py`'s `lab_members` and `scripts/get_bench.sh --members SET --lab LAB [--seed S]`: a pool less every task another lab's `[[draw]]` took (HumanEval-Verus for Q12: 78 of 83), sorted or in the seeded order. `bench/local/q/lab1/STRATUM.toml`, B1's tasks-and-strata field in `paper/Q12_answers.tex` and `docs/Q12_PracticeIC.md` §4.3 say so.
  - **Attested.** After the re-seal, `mksandbox-run --author --attest-rescan` (78 of 78 re-attested under DV6), then the ten public cards attested under DV6 (0 refused): `sandbox/attested.toml` 88 entries, every Lab 2 card's sha256 among them; its header and `sandbox/README.md`'s row say so.
  - **Learner-visible text.** `docs/Q15_PracticeIIC.md` §0 (the rule is fixed), §6.1 (S1's row), §6.2 (the form, what a delivery adds, the code check, `--lab-code own`, S1's mutant source); `bench/local/q/lab2pub/STRATUM.toml`'s header.
- **Why:** the lane's runs (16 GB scope, one job at a time; archive `dv6/lab2/`): C1 10/10; C4 10/10 forms reach the verify stage; C6 the ten reference programs pass `vcheck --gate --lab-task` (verified 3-11, 0 holes); in the grader container on the new seal: manifest ok (72), the ten reference programs faithful and the ten weakened statements weak, deliveries that state their own renamed definitions faithful on 5 of 6 cards (vp3 `undecided`), the six prose references faithful against themselves, the 30 reference programs verified by `validate --cards`; a host dry run agreed on all 26 card rows; 0 of 71 sealed strings in the 18 host output files. On the real tools a public reference program with one executable edit fails with `lab-code-changed` (with `--lab-code own`, on its verification error alone) and a local one with an added assertion fails with it. The kill rate on the annotated code: 259 of 299 mutants killed, 229 of them also without the ensures (30 by the ensures alone). Tests: `tests/wrappers/test_lab_code_static.py` (new, 16), `tests/bench` 74 (14 new); `check_course_map.py` OK; `pins.py --ci --module Q15` and `Q12` 0 problems; rubric pins 111 current; `specfreeze --check Q15` 0; `chapter_lint --all` 0; `lab2pub.py build --check` current; the leak verifier OK (1,634 public files); `check_single_route.py` clean; CI as in the notes §10.
- **Touches:** Δ152, Δ182, Δ221, Δ224, Δ226, Δ228-Δ233; QPLAN §22.6, §25.5-§25.6; DV4-PLAN §7.1-§7.3, §13; `scripts/vcheck`, `scripts/dvl/{labcode,benchstrip,lab2pub,bench}.py`, `scripts/get_bench.sh`, `scripts/check_course_map.py`; `bench/local/q/lab2pub/`, `bench/local/q/lab1/STRATUM.toml`; `Hidden/labs/Q15/verdicts.tar.age`, `sandbox/{truth,attested}.toml`, `sandbox/README.md`; `docs/Q12_PracticeIC.md`, `docs/Q15_PracticeIIC.md`, `paper/Q12_answers.tex`; `tests/wrappers/test_lab_code_static.py`, `tests/bench/test_lab2_forms.py`; the Q15 code notes.
- **Owner:** DV6's lab2 lane; the user (the open items' decisions).
- **Open:** three decisions for the user (S1's kill rate on annotated code; a sealed definition under a quantifier, vp3; the vericoding arm and the code check, which needs a plan field the frozen core lacks); S1's feedback route in a live batch (the tools owner); the records (QPLAN §22.6, §25.6; DV4-PLAN §7, §13; `CLAUDE.md`, `README.md`, `VERSIONS.md` §1.4).
