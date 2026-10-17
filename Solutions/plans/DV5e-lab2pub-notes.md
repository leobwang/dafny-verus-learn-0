# DV5e lab2pub lane: Lab 2's public task forms, their draw and their reference statements

Author-only notes (reference class). The lane's brief: QPLAN §25.6's public strata (five
HumanEval-Verus and five vericoding `humaneval` Dafny tasks in Lab 2's form: the specification
removed, the prose and the code kept, an empty witness), as a second transform beside
`verus-strip-proofs`; tests that no form keeps its specification or a proof body; the draws
pre-registered from `bench/public/POOLS.toml` with a brittleness check and a redraw rule (Δ225);
the reference statements stored only in the hidden truth; the judging step run on each reference
against itself and on one weakened statement per task, with no model call. Like Δ195–Δ225 this
file names no reference statement and no weakened statement (the Lab 2 references, public or
local, stay out of `Solutions/`: Q15 code notes §14); the weakenings are given by kind. Memory
share 16 GB: every solver job one at a time through the wrappers inside `systemd-run --user
--scope -p MemoryMax=16G -p MemorySwapMax=0`, `free -g` 92–97 GB available at each start; the
containers one at a time (Dafny at its 11.5 GB bound, Verus `--mem-gb 16`). No job was killed.
Scratch `/tmp/dvl0-dv5e-lab2pub/` (removed at the end); archive
`~/.cache/dafny-verus-learn-0/author-probes/dv5e/lab2pub/`.

## 1. What was built

| file | what |
|---|---|
| `scripts/dvl/benchstrip.py` | the second transform, `verus-lab2-form` and `dafny-lab2-form` (`lab2_form_verus`, `lab2_form_dafny`, `lab2_form`, both registered in `TRANSFORMS`/`TRANSFORM_NOTES`); `lab2_publish_verus` (kept spec fns made `pub open`); `spec_residue` (an independent check that a form keeps no specification and no proof); `_apply_char_edits` (removed items leave one blank line) |
| `scripts/dvl/lab2pub.py` (new) | the public strata: the stratum's members from POOLS.toml (vericoding's `dafny/humaneval` by the set's subset index), `draw_order` (seeded), the static checks C0–C3 (`static_check`), the forms with their headers (`make_form`), the reference statement (`reference`: the answer's declaration as `dvl.judge.candidate` reads it), `base_answer`, `build [--check]` (re-derive every form from the installed sets against its recorded sha256), the author-only `record` (the draw into POOLS.toml, the stratum file and the forms) |
| `scripts/dvl/bench.py` | `load_draws`, `write_draws`, `DRAW_KEYS`; `write_pools` writes the `[[draw]]` tables after the `[[pool]]`s and, by default, keeps the file's own, so `--pin-pool` no longer drops a lab's draws; the file header and the pool-pin comment name them |
| `bench/public/POOLS.toml` | two `[[draw]]` records (Q15 verus, Q15 dafny): set, subset, the set's and the tool pins' digests, `pool_sha256`, the stratum's member count, seed, the seeded order's sha256, how many members the walk took, the rule, the pre-registration's and the amendment's sha256, date, the drawn tasks, the cards, every skipped member with its reason |
| `bench/local/q/lab2pub/` (new; learner-owned, tracked) | `STRATUM.toml` (lab Q15, stratum `public`; per card id, language, name, set, task, HumanEval problem, the answer's and the form's sha256), `NOTICE` (both MIT licence files and the change statement), ten forms `<card>/tasks/<card>.{rs,dfy}` |
| `Hidden/labs/Q15/verdicts.tar.age`, `sandbox/truth.toml` | re-sealed by `sandbox/seal_hidden.py` (72 files, was 52: ten `tasks/<card>/` pairs; `judge/oracles.py` re-copied from the twin, now `6cb4f036…a259` after D22's gloss change, code unchanged; `SEALING.md` extended). Archive sha256 `fe3156a9…89ed`, plaintext manifest `627dab2b…d1be` |
| `tests/bench/test_lab2_forms.py` (new, 23 cases) | §6 |

## 2. The form (`verus-lab2-form`, `dafny-lab2-form`)

One target declaration per file (Verus: the only exec fn; Dafny: the only method). Removed: the
target's `requires` and `ensures` (Verus also `recommends`, `returns`, `default_ensures`); every
proof (Verus: as `verus-strip-proofs`, except that a proof fn always goes whole and a kept line
that still names one refuses the file; Dafny: lemmas, `assert` (with `by` blocks), `calc`,
`reveal`, ghost variables, proof `forall` statements, lemma calls, loop invariants); the
definitions only the proofs used (Verus: spec fns that no kept line and no clause of the
target's specification names; Dafny: `<vc-helpers>` functions and predicates no kept line
names). Kept: every other definition (the task's vocabulary, as a local card keeps its
definitions), the target's signature with its `decreases` (Dafny also `modifies` and `reads`),
the code, each loop's `decreases` (Dafny also a loop's `modifies`), every comment outside the
removed spans. Verus: kept spec fns become `pub open` (§4). Added: an empty witness and, for
Dafny, the HumanEval prompt as a comment above the method (vericoding's Dafny files carry no
prose: the prompt is the one the HumanEval-Verus set ships for the same problem). Refused
(`StripError`): more than one target declaration, a target with no ensures, an `assume` in the
body, a `forall` statement that is not a proof, a kept line naming a removed lemma or proof fn.
`spec_residue` is independent of the transform's plan: on a form, any `requires`/`ensures` of
the target, any proof fn or lemma, `assert`, `calc`, `reveal`, `invariant`, `assume`, ghost
variable, Verus `proof_residue`, and a `<vc-helpers>` declaration that keeps a contract.

Over the pools (static, no solver): HumanEval-Verus 49 of 83 pose one task (34 have 2–5 exec
fns, 1 no `### ID` block); vericoding `dafny/humaneval` 82 of 143 pass C0–C2 (52 rows come from
`jetbrains/verified_cogen`, which records no licence; 7 have 2–3 methods; 2 keep a helper's
contract).

## 3. The draw

**Pre-registered** before any order was computed (`draw/PREREG.txt`, sha256 `3a823649…a92a`,
2026-10-13T21:08Z, read-only): the pools by their `pool_sha256`; seeds
`dv5e-lab2pub-2026-10-13/humaneval-verus` and `dv5e-lab2pub-2026-10-13/vericoding-dafny-humaneval`;
the order (members sorted, `random.Random(seed).shuffle`); verus first, then dafny; five each;
the sequential rule (a member failing a check is skipped with its reason, the next taken):
C0 licence (MIT or Apache-2.0 provenance), C1 form (the transform poses it, `spec_residue` empty,
the grader's host half reads it, the answer is a delivery of the form by `dvl.judge.lab_ok`),
C2 prose, C3 a HumanEval problem no earlier accepted task's, C4 the form reaches the verify
stage, **C5 the answer passes `vcheck --gate` and `vcheck --brittleness` shows seeds 1, 2, 3
verified and stable** (Δ225's flip), C6 the reference program with the author's witness call
passes the gate, C7 the grader judges it faithful. A job killed by memory or the net is re-run
once, then skipped as `retry` (none happened).

**The first walk** (`draw/walk1.jsonl`) accepted vp1–vp5 and five Dafny tasks through C6; the
host run of the grader's own judging function (truthcheck's `_judge_one` with the sealed
oracles, each lemma through `vcheck --gate` on the host; `draw/hostjudge1-*.json`) then gave:
three Verus references `undecided` against themselves (every lemma `unknown`), two Dafny
`context`. Causes, reproduced: (a) the grader's lemmas are `pub proof fn`s and Verus refuses a
public function whose clauses name a private spec fn, and those files' spec fns are private; (b)
the grader's base lemma over a card's definitions runs no verification task when the
definitions carry no proof obligation, so the gate's nothing-verified rule fails it.

**Amendment** (`draw/AMENDMENT.txt`, sha256 `3180f7e4…36ef`, written before any seal or
container run, read-only): (1) the Verus form makes its kept spec fns `pub open`, and the
reference program starts from the answer with the same change (`lab2pub.base_answer`, used by
C1 and C5) — a defect of the form that every delivery would meet; (2) the walk re-run from the
start of both orders under the same seeds and rule; the two Dafny `context` members skipped at
C7 (a property of the grader's base check, not of the form: a tools-owner item, §8); (3) C7 for
the accepted set confirmed in the grader container.

**The second walk** (`draw/walk2.jsonl`; recorded in POOLS.toml):

| stratum | members | walked | drawn (card: task, HumanEval problem) | skipped |
|---|---|---|---|---|
| verus | 83 | 9 | vp1-he100 `human_eval_100.rs`; vp2-he033 `human_eval_033.rs`; vp3-he077 `human_eval_077.rs`; vp4-he035 `human_eval_035.rs`; vp5-he060 `human_eval_060.rs` | 4 at C1 (2 or 3 exec fns): 074, 054, 018, 120 |
| dafny | 143 | 10 | dp1-he048 `DH0050.dfy`; dp2-he052 `DH0055.dfy`; dp3-he063 `DH0065.dfy`; dp4-he159 `DH0160.dfy`; dp5-he062 `DH0064.dfy` | DH0094, DH0020 at C7 (`context`); DH0041, DH0034 at C0 (verified_cogen); DH0063 at C3 (HumanEval/60 is vp5's) |

Order digests: verus `379be75f…2273`, dafny `fe8bf1e7…b129`. C4: every form reaches the verify
stage. C5: every drawn answer passes the gate and verifies under seeds 1, 2, 3, `stable`, no
spread flagged. C6: the ten reference programs pass `vcheck --gate` (verified counts 3–11, 0
holes). C7: §5.

## 4. The reference statements and the seal

Each reference is the public answer's target declaration as `dvl.judge.candidate` reads it (the
grader's own extraction), written to `tasks/<card>/reference.toml` (id, lang, name, task form,
source set and task, the answer's sha256, requires, ensures, the reference oracles' mutant count,
and the kill rate where it applies, §7) beside the reference program `tasks/<card>/<card>.<ext>`
(the answer, Verus spec fns `pub open`, the form's header, the author's witness call). They are
sealed with Lab 2's hidden truth (`Hidden/labs/Q15/`), never in `Solutions/` or a learner file:
the references are public answers' statements, so the seal keeps them out of every loop rather
than secret. **The plaintext of the Q15 archive is now `dv5e/lab2pub/hidden-src/labs/Q15/`**
(72 files; it supersedes `dv5d/judge/hidden-src/labs/Q15/` for any later re-seal). The previous
archive and pin are kept in `preseal/`. `truthcheck manifest Q15` round-trips (72 files).

## 5. The judging evidence (no model call)

Candidates (`scratch/cands/`, expectations `draw/judge-expected.json` written before the
runs): each reference program (expected faithful) and one statement per task weakened in the
declaration's header only (expected weak): a conjunct or clause dropped (vp1, vp2, vp4, dp3,
dp5), an `==`/`<==>` made an implication (vp3, dp1, dp2), a match arm's value constraint
dropped (vp5), a result predicate replaced by a length fact it implies (dp4).

| run (grader container, final image) | result | wall |
|---|---|---|
| `judge` Q15 (Dafny), 10 candidates | **10 of 10 as expected**: 5 faithful (both lemmas proved, vacuity failed), 5 weak (spec ⇒ ref failed, ref ⇒ spec proved) | 32 s |
| `judge` Q15 (Verus, 16 GB), 10 candidates | **10 of 10 as expected**, the same pattern | 46 s |
| `validate` Q15, the ten public cards (one run per language) | 10 of 10 verified, 0 holes | 5 s, 7 s |
| `validate` Q15, the twenty local cards (one run per language) | 20 of 20 verified, 0 holes (no regression from the re-seal) | 10 s (Dafny) |

The host run of the same function on the final draw agreed on all 20 (`draw/hostjudge2-*.json`).
Verdict-only output: 30 strings (the reference clauses of at least 12 characters, split at the
Verus clause lists too, and the archive's canary token), searched (also with whitespace removed)
in all 18 host output files of the lane's container runs: 0 hits. No run directory and no `dvl`
container left.

## 6. Tests and checks

`tests/bench/test_lab2_forms.py`, 23 cases: the Verus and the Dafny form on invented text
(specification and proofs gone, code, measure, vocabulary and prompt kept, a spec fn the ensures
names kept and published, a proof-only one dropped, the witness added, the grader reads no
requires or ensures; refusals: two exec fns or methods, a kept lemma call, an `assume`, a
non-proof `forall`, no ensures; `lab2_publish_verus`'s cases; both registered with suffixes);
**the shipped forms** (tracked, so always run): five and five, ids and problems distinct, each
form's sha256 as recorded, `spec_residue` empty, the grader reads no requires or ensures, the
empty witness present, the header names the card, `lab_cards` lists them, nothing but the forms,
`STRATUM.toml` and `NOTICE` in the directory; **the draw records**: one per stratum, the
stratum file is their result, drawn ⊆ pool, drawn and skipped disjoint and together the walked
prefix of the seeded order, the verus order re-computed from POOLS.toml alone, the dafny order
when vericoding is installed; the pool file keeps its draws through a re-pin and a draw replaces
its own; with both sets installed, every form re-derives byte for byte (`lab2pub.py build
--check`) and every drawn task passes C0–C3.

Runs on the final tree: `tests/bench` 57 OK (34 before); `tests/sandbox` 171 OK; `scripts/ci.sh
--author --job harness` PASS (71 s: core 549, adapter 50, sandbox 171, bench 57); `scripts/ci.sh
--job static` PASS (446 s); `check_course_map.py` OK; the leak README's verifier OK (18 modules,
1,631 public files); `lab2pub.py build --check` 10 current.

## 7. What the forms are like (measured)

- **As shipped** (`vcheck --json`, `scratch/forms-shipped.txt`): Dafny dp1, dp2, dp4, dp5 verify;
  dp3 fails (its loop measure needs the requires the form removed). Verus all five fail
  (overflow and precondition obligations the removed requires and invariants discharged).
- **With the reference statement and no proof** (the S arms' delivery shape; `scratch/noproof/`):
  **2 of 10 pass the gate (dp3, dp4)**; the other 8 fail: their code needs proof annotations
  (loop invariants, assertions) that the form removed. Unlike the local cards (Verus loop-free by
  design, every reference program the form plus the specification and a witness), the public
  references verify only with the upstream proofs.
- **The reference oracles' kill rate** (host runs, where it applies): dp3 20 of 20 mutants
  killed; dp4 2 of 3 (the survivor swaps `<=` for `<` at a point where both branches agree: an
  equivalent mutant). For the 8 others no kill rate is recorded: every program the oracles would
  render from the shipped code fails the gate whatever the specification, so the rate would
  measure nothing (`reference.toml`'s `kill` field says so).
- **Vocabulary**: the forms keep the definitions the specification uses, as the local cards do.
  In two Dafny cards (dp2, dp4) the reference's ensures is one call of a predicate the form
  ships, and in two more (dp1, dp5) one such call with a relation or a length fact, so the
  specification task there is mostly to choose and apply it (§9 item 2). The Verus cards' spec
  fns are building blocks (a sum, a count, a cube), not the whole statement.

## 8. Deviations and readings

1. **The pre-registered rule was amended once** (§3), before any seal or container run; the
   amendment and the first walk are archived. The draw's members changed only in the dafny
   stratum (two members skipped at C7, two later members taken).
2. **Where the cards live:** `bench/local/q/lab2pub/` although the tasks are public: the
   grader's host half (`dvl.judge.lab_cards`), `build_truth` and truthcheck's `validate` find a
   lab's cards only through `bench/local/<t>/<dir>/STRATUM.toml` with `<card>/tasks/<card>.<ext>`
   (truthcheck's path rule, inside the image). The stratum file says the tasks are public and no
   contamination control.
3. **The forms are tracked** (ten files derived from two fetch-mode sets, both MIT, with
   `NOTICE`): §9 item 3. C0 admitted only MIT or Apache-2.0 provenance for that reason.
4. **The Dafny prose** is HumanEval's prompt as the HumanEval-Verus set ships it (vericoding's
   Dafny files carry none); QPLAN §25.6 names no prose source for them. Its Python signature and
   examples come with it. QPLAN's "(Apache-2.0)" for the source fits the JetBrains rows, which
   C0 excluded; the drawn rows are vericoding's own translations (MIT).
5. **The draw is the author's**, fixed with its sealed references; the learner's
   pre-registration (B1) names it (POOLS.toml's `[[draw]]`, the stratum file's sha256) rather
   than drawing its own seed as Lab 1 does (QPLAN §25.6: the strata fixed by kind, no pilot).
6. The witnesses of the reference programs are the author's (one call each); the forms ship them
   empty.

## 9. Open items

1. **DECISION NEEDED (the user; high: before Lab 2's runs).** The S arms on the public cards: 8
   of the 10 forms do not verify with the reference statement alone (§7), while S0 takes "the
   first sample that verifies with its witnesses kept" and S1's mutant kill renders mutants of
   the shipped code. Options: (a) on a public card a delivery may add proof annotations (loop
   invariants, assertions, proof blocks, lemmas; never executable code), the lab gate checks the
   code unchanged, and S1's kill rate mutates the delivery's annotated code (recommended: the
   question stays "is the specification faithful", the strata are reported separately);
   (b) on a public card the S arms are judged on the specification alone (the delivery must
   resolve and its witness and vacuity checks run; the body's verification and the kill rate are
   not used); (c) redraw both public strata from tasks whose form verifies with its reference and
   no proof (none of HumanEval-Verus's pool can: the pool rule requires its proof-free task form
   to fail the gate, so that stratum would need another source).
2. **DECISION NEEDED (the user; medium).** The definitions the forms keep. Options: (a) keep them
   as built (the local cards' rule; four Dafny references rest on one shipped predicate); (b)
   also remove the definitions only the specification uses that are not recursive, sealing them
   with the reference as its `definitions` (the grader renames them and Dafny/Verus unfold them, so
   a faithful delivery that states its own is still judged; recursive ones stay, since the
   grader's empty lemmas cannot equate two recursive definitions) (recommended: the prose, not
   the vocabulary, carries the specification); (c) remove every specification-only definition
   (deliveries over recursive definitions would be judged `undecided`). (b) and (c) rebuild the
   forms and re-run C1, C4, C6 and C7 on the same draw.
3. **DECISION NEEDED (the user; medium).** Ten files derived from fetch-mode sets are tracked in
   the course tree. Options: (a) keep them tracked with `NOTICE` (both licences, the change
   statement; C0 admitted only MIT or Apache-2.0 provenance) (recommended: every tool reads lab
   cards from the tree, and the forms are what the learner works on); (b) gitignore the forms and
   have the learner build them after `get_bench.sh` (`lab2pub.py build`, which refuses a form
   whose source or result differs from the recorded sha256), tracking only the stratum file and
   the draw; (c) move humaneval-verus and vericoding to `vendor` (DELTAS entry and leak scan).
4. **DECISION NEEDED (the user; medium).** Lab 1's HumanEval-Verus pool (83) contains Lab 2's five
   Verus tasks, and Lab 1's task forms keep the specification: a Lab 1 draw that takes one shows
   its Lab 2 reference. Options: (a) Lab 1's draw excludes the five (its pre-registration rule
   and Q12's chapter say so; Lab 1 runs first) (recommended); (b) leave the pools overlapping and
   record it as a contamination case in Lab 2's report; (c) redraw Lab 2's Verus stratum after
   Lab 1's draw, from members Lab 1 did not take.
5. **The tools owner (medium).** truthcheck's base check judges a card `context` when its
   definitions carry no proof obligation (the empty base lemma runs no verification task; the
   gate's nothing-verified rule): two Dafny draws were skipped for it, and a learner delivery over
   such a card would meet it. A fix is in the image (`sandbox/image/truthcheck.py`, then a
   rebuild by digest).
6. **The tools owner (low).** `mksandbox-run --truth-check validate --truth-lang L` on Q15 is now
   refused (its argv names all 15 cards of a language: 18 words, over the manifest's 16); validate
   by `--cards` in batches (as §5 did) or lift the rule.
7. **The attestation lane (D25; medium, before any agent-mode Lab 2 run).** Attest the ten cards
   of `bench/local/q/lab2pub/` through the recalibrated scan (Δ219's preflight refuses an
   unattested card).
8. **The records lane (low).** VERSIONS.md §1.4's judging row (Q15 is 72 files now; Q15's sealed
   oracles `6cb4f036…a259`, Q13's and Q17's still `e168aaed…`, code equal); `CLAUDE.md`'s Not-built
   line (drop "Lab 2's public task forms"); QPLAN §25.6 (the public strata as built: the form, the
   prose source, the provenance rule, the draw and its record), §30 Q57's disposition; DV4-PLAN
   §7.1–§7.2 (`[[draw]]`, `lab2pub.py`); the DV5d judging notes' "Q15 52" (§1) is history.
9. **The kits lane (medium).** The learner-visible sentences that call the public strata pending:
   `bench/local/q/lab2/STRATUM.toml`'s composition comment, `docs/Q15_PracticeIIC.md`'s Lab 2
   strata paragraph, and B1's template text, then the chapter pins and the leak verifier; the
   Q15 calibration fixtures' strata lines if they name the public cards.

## 10. DELTAS-ready text (for the integration lane to number)

### Δ2xx · Lab 2's public task forms as built: the second transform, the pre-registered draw and its records, the references sealed and judged — adopted (DV5e, 2026-10-13)
- **Status:** closes Δ221's and Δ225's open item (the kits lane's, high: Lab 2's public task forms and their reference statements; the draws with a brittleness check and a redraw rule). Like Δ195–Δ225 it names no answer, no reference statement and no weakened statement. Detail: `Solutions/plans/DV5e-lab2pub-notes.md`.
- **Change:**
  - **The second transform** (`scripts/dvl/benchstrip.py`: `verus-lab2-form`, `dafny-lab2-form`, registered beside `verus-strip-proofs`): Lab 2's form of a complete file with one target declaration: its `requires` and `ensures` removed, every proof and the definitions only proofs use removed, the code, the other definitions and the comments kept, an empty witness added; Verus kept spec fns made `pub open` (the grader's lemmas are public and Verus refuses a public function that names a private one); Dafny the HumanEval prompt added as a comment. `spec_residue` checks a form independently of the transform.
  - **The public strata** (`scripts/dvl/lab2pub.py`, new): the stratum's members from `bench/public/POOLS.toml`, the seeded order, checks C0–C3, the forms, the reference statement (the answer's declaration as the grader's host half reads it), `build [--check]`, the author-only `record`. **`bench/local/q/lab2pub/`** (new, tracked): `STRATUM.toml` (lab Q15, stratum `public`), `NOTICE`, ten forms vp1–vp5 (HumanEval-Verus) and dp1–dp5 (vericoding's own `humaneval` translations, MIT).
  - **The draw records:** `bench/public/POOLS.toml` gains `[[draw]]` tables (seed, rule, the pre-registration's and the amendment's sha256, the seeded order's sha256, the drawn tasks and every skipped member with its reason); `scripts/dvl/bench.py`'s `write_pools` keeps them through `--pin-pool` (`load_draws`, `write_draws`).
  - **The rule** (pre-registered before any order was computed, amended once before any seal): members sorted and shuffled by the seed; walk the order and take a member when C0 licence (MIT or Apache-2.0 provenance), C1 form, C2 prose, C3 a distinct HumanEval problem, C4 the form resolves, **C5 the answer passes the gate and verifies under seeds 1, 2 and 3, stable** (Δ225's flip), C6 the reference program with its witness passes the gate and C7 the grader judges it faithful all pass; else skip it with its reason and take the next.
  - **Sealed:** `Hidden/labs/Q15/` re-sealed with the ten references and reference programs (72 files; `judge/oracles.py` re-copied from the twin after D22, code unchanged); `sandbox/truth.toml` re-pinned by the tool.
- **Why:** the draw (16 GB scope, one job at a time, no job killed): HumanEval-Verus walked 9 of 83 (4 skipped: more than one exec fn), vericoding `dafny/humaneval` walked 10 of 143 (2 skipped for provenance with no recorded licence, 1 for a repeated HumanEval problem, 2 because the grader's base check runs no verification task over their definitions); every drawn answer verified under the three pinned seeds. The amendment: the first walk's host run of the grader's own judging function found three Verus references `undecided` against themselves (private spec fns that public lemmas cannot name). In the grader container: the ten reference programs faithful against their sealed references and the ten weakened statements weak (20 of 20 as recorded beforehand); the ten new and the twenty local reference programs verified by `truthcheck validate`; the reference clauses and the canary absent from every host output. Measured: 2 of the 10 forms verify with the reference statement and no proof (the others need the upstream proof annotations), against every local card. Tests: `tests/bench` 57 (23 new, among them the check that no shipped form keeps its specification or a proof body); `ci.sh --author --job harness` and `--job static` PASS; the leak verifier OK (1,631 public files).
- **Touches:** Δ152, Δ208, Δ219–Δ221, Δ225; QPLAN §25.6, §30 Q57; DV4-PLAN §7.1–§7.2; `CLAUDE.md`'s Not-built line; VERSIONS.md §1.4; `scripts/dvl/{benchstrip,bench,lab2pub}.py`, `bench/public/POOLS.toml`, `bench/local/q/lab2pub/`, `Hidden/labs/Q15/`, `sandbox/truth.toml`, `tests/bench/test_lab2_forms.py`.
- **Owner:** DV5e's lab2pub lane.
- **Open:** four decisions for the user (the S arms on public cards whose code needs proof annotations; the definitions the forms keep; tracked derived files; Lab 1's overlap with Lab 2's Verus tasks); truthcheck's base check on obligation-free definitions and `validate --truth-lang`'s argv limit (tools owner); the ten cards' attestation (D25's lane); the records and the learner-visible "pending" sentences (records and kits lanes).
