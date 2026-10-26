# DVR4 step 3 — R08 rebuild build notes (author-only)

Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2.1–§2.3 (the step-matcher interface, D-R08 (a)), §4.2 (the R module bar), §5 step 3; PLAN §3 R08 (Why, Core payload, Exercises) and PLAN §10's 354-minute record. Scratch: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step3/s3-scratch/r08/` (archived from `/tmp/dvl0-dvr4-s3`); probes and run logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-s3/r08/`.

## Objective-to-hole table (written before the code)

PLAN §3's objectives for R08 and the item that carries each. "Line budget" is plan §2.2's counter (proof lines of the reference body); a reference under 3 lines is redesigned.

| objective (PLAN §3 R08) | item | what the learner proves or reads | minutes D/V | line budget (reference) |
|---|---|---|---|---|
| the derivative matcher as a refinement of the step-matcher interface | W1d/W1v (worked) | the derivative engine: Config = Re, Step = Deriv, Final = Nullable; each law one call to A2/A1b; `Run` is the interface's, verified once | worked (30 min record line) | — |
| a second refinement over A2's class API, whose obligation is semantic | **H1d/H1v** `WordStepLaw` / `lemma_word_step_law` | the class-word engine's step law: case split alive / dead / exhausted, and the index shift `([c] + w)[i + 1] == w[i]` inside a `forall` | 10 / 10 | 6–12 |
| an engine's own lemma that a refinement obligation rests on | **H2d/H2v** `PartsLaw` / `lemma_parts_law` | structural induction; moving an index across `Parts(a) + Parts(b)` both ways (existential witnesses) | 15 / 15 | 15–30 |
| the interface obligation of the alternative-set engine (semantic: it composes `PartsLaw` and A2's `DerivCorrect`) | **H3d/H3v** `AltFeedLaw` / `lemma_alt_feed_law` | induction on the state's length; an existential split over `head + tail`; a local reveal of the opaque `Res` | 15 / 15 | 15–30 |
| opacity repairs | **H4d/H4v** `AltFinalLaw` / `lemma_alt_final_law` | reveal the opaque `Res` in exactly this lemma; induction on the state; `NullableCorrect` per element | 5 / 5 | 5–15 |
| what a refinement may change (weaken `requires`, strengthen `ensures`) and the obligations it generates | C4dv (divergence card), the refinement lab (30 min) | facts, not predictions | — | — |
| a refinement that fails for a semantic reason | A1d/A1v (agent, rung 5) | a pruning engine that drops `Eps` alternatives as if they were `Empty`: zero holes, a real postcondition failure in its pruning lemma; the faithful repair edits only the engine | agent 25 | — |

Item ids follow file order (difficulty ramp): plan §2.3's table lists the same four obligations as H1 `PartsLaw`, H2 alternative-set `StepLaw`, H3 class-word `StepLaw`, H4 `FinalLaw`. Here H1 is the class-word step law, H2 `PartsLaw`, H3 the alternative-set step law, H4 the final law. Content, minutes (45 per language) and objectives are the plan's; only the labels moved, so that the shortest obligation comes first and every hole follows the cards it uses.

## Design decisions found by probes (2026-10-18)

- **A refining lemma cannot recurse.** The interface's lemmas and functions inherit a decreases clause over the abstract `Config`, and Dafny refuses a decreases clause on a refining declaration (`decreases clause on refining method not supported`). Recursive `Step`/`Final` are therefore given helpers (`FeedAll`, `AnyNullable`), and each engine discharges the interface's laws by calling its own named lemmas (`FeedLaw(st, c, w) { AltFeedLaw(st, c, w); }`). The class-word engine does the same for uniformity. A bodyless refining lemma that restates the `ensures` is counted twice (once at the abstract declaration), so the holes are the engine's own lemmas, which live in the learner file.
- **The inline existential in an `ensures` was not matched**; the same statement through a named `AnyMatches` predicate verifies. The alternative-set engine therefore states its model through `AnyMatches(st, w)` (given, transparent) and an engine-level opaque `Res`.
- **Verus.** Associated types and proof fns in a trait work on the pinned Verus (the plan's [probe]). Exec state and spec model differ (a `Vec<Re>` cannot be built in spec mode), so the trait carries `type Model` and `spec fn model(st) -> Model`; the laws are stated over models. `start` and `step` take their argument by value (no class copies). `#[verifier::opaque]` on a trait-impl spec fn is accepted and revealed as `reveal(<AltEngine as StepMatcher>::res)`.

## Further probe findings and design changes (2026-10-18, as built)

- **H1 (the plan's class-word step law) falls to automation** in both languages (Dafny even as shipped; Verus in E1, the sequence broadcast groups): the index shift inside a `forall` is found by the solver. H1 is rebuilt as the start fact of a **range-star engine** (language: every character in one of a list of ranges; state: one A2 class built with `ClassRange`/`ClassUnion`): `RangesClassLaw` / `lemma_ranges_set_law`, an induction with a witness shift (reference 12 lines, 10 minutes). Dafny's default induction proves it, so the shipped `{:induction false}` is the named lever (registry fallback "printed induction-disabled levers"); the empty body fails as shipped under seeds 1–3 and in every Verus mode. The objective ("a second refinement over A2's class API") is unchanged.
- **Names.** `Run`/`run` and `Step` are curated Lean names (avoid.sh); `State`/`advance` collide with Q declarations once a chapter or bank shows them. The interface uses `MatchWord`/`match_word`, `Config`, `Feed`/`feed`, `FeedLaw`.
- **Dafny ignores `opaque` on a refining declaration** (an `opaque ghost predicate Res` that refines the abstract one stays transparent: every law verifies with no reveal). The alternative-set engine therefore puts the opacity on its own predicate `AltRes` (Verus: the free `alt_res`); the chapter shows both behaviours with pinned captures. With the reveals removed, H3 and H4's references fail in both languages.
- **A refining lemma may recurse** when a concrete-typed parameter shrinks (the inherited default decreases is the parameter tuple; abstract-typed parameters carry no order); recursion on the state alone fails ("decreases clause might not decrease"), and an explicit `decreases` on a refining lemma is a resolve error (P3's answer). Verus checks each function's own `decreases`.
- **Agent and the freeze.** A definition's body is part of its statement for `specfreeze`, so a repair of a planted defect inside a Dafny function or a Verus spec fn fails `specfreeze --against <snapshot>` exactly as a changed `Lang` does. The agent is built so the freeze separates them: Dafny `Prune` is a function with the promise `ensures forall w :: Matches(out, w) <==> Matches(r, w)`, and the module freeze pin (from the twin) lists `Prune`'s body under `open_bodies`; Verus's model of a state is its language (`words_of`), the laws are definitions, and the rule lives in the executable `prune_exec` with the same promise. The acceptance line is `scripts/specfreeze --check R08`. Checked: the faithful repairs pass `--check` with 0 findings; a changed `lang` / `Lang` gives one `freeze-changed` per language.

## DVR4 step 5: the systemic pass (lane P1, 2026-10-25)

Binding inputs: plan §4.2's bar as R02 met it; the course-wide rules (D64/D84: every hole's smallest proof has at least three one-fact lines unless an exception is recorded; D82/D85: every WRITE tag names a step a smallest proof needs; twins mirrored). Scratch: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p1/r08/`. Every solver job ran one at a time under a 6G outer scope after `free -g` showed at least 20G available (`bin/memgate.sh`); there was no exit 137 or 143.

### 1. Objective-to-exercise map (before any change)

The step-3 table above stands: objectives, items (W1, H1–H4, C3–C5, A1) and minutes (H1 10, H2 15, H3 15, H4 5 per language) are unchanged by this pass. The registry tags at the start: `write_d = ["refines", "reveal"]`, `write_v = ["trait-spec", "reveal"]`, `recognise_d = ["abstract-module"]`, `recognise_v = ["open-spec"]`.

### 2. Measurements (`r08/min`)

The twins now carry `@hole-begin/@hole-end` markers for H1–H4 in each language. Smallest proofs found by the greedy minimizer (structural lines kept; bindings not counted; `:|`/`choose`, calls, `reveal` and asserts counted):

| item | one-fact lines (smallest found) | of which |
|---|---|---|
| H1d `RangesClassLaw` | 3 | the recursive call, two witness picks |
| H1v `lemma_ranges_set_law` | 4 | the call, two picks, one index shift |
| H2d `PartsLaw` | 9 | two calls, three picks, four asserts |
| H2v `lemma_parts_law` | 8 | two calls, three picks, three asserts |
| H3d `AltFeedLaw` | 11 | `reveal`, three calls, five picks, two asserts |
| H3v `lemma_alt_feed_law` | 12 | `reveal`, three calls, five picks, three asserts |
| H4d `AltFinalLaw` | 3 | `reveal`, two calls |
| H4v `lemma_alt_final_law` | 4 | `reveal`, two calls, the index-shift `assert forall` (without it the body fails) |

Every hole meets D64. The twins keep a few readable asserts the minimizer drops (H1d 2, H2d 2, H3d 4, H4d 1, H1v 1, H2v 2), as in R05–R07.

**reveal is genuine** (D82/D85): dropping `reveal AltRes();` / `reveal(alt_res);` fails in H3 and H4 in both languages, so the tag names a step two smallest proofs need per language.

**refines / trait-spec had no hole instance** (brought to the coordinator, 2026-10-25; settled by D92, §4 below): H1–H4 are each engine's own lemmas, none is declared in `RG_A2_StepMatcher` or the trait, and no smallest proof uses the refinement (the interface's laws are discharged in the given engine bodies by one call each). Options: (a) RECOGNISE both, write lists `["reveal"]` (recommended); (b) re-pose a hole so the learner writes the refinement or impl; (c) keep them under a recorded exception.

### 3. Admission (2026-10-25)

- Seeds 1–3 stable for all four twins (core d/v, agent d/v). Widest spreads advisory: Dafny 25.7 % on a declaration outside the files; Verus 20.4 % at `lib.rs:450`; the Verus agent 0 %.
- `firsttry.sh R08 --empty-body` 8/8; `--lint-hollow` OK (21 files).
- `specfreeze --check R08` 0; `vcheck --shipped` 0 against `expected/R08.counts`; `reference_lint` 0; `chapter_lint` 0 (5,708 words, 27 pins, 5 predict boxes, 3 diagrams); `pins.py --ci --module R08` 44/44.
- Layout: both hand files, the twins, the agents and the specimens are one statement per line.
- Chapter: every prediction (P1d, P2v, P3dv, P4v, P5dv) is answered by a pinned capture after its box.
- Bank: 12 questions at the Q06 schema, 12 Reread lines (each names a chapter heading exactly), two parallel problems, every tag known.
- Leak patterns: 8 OK on the current twins (the verifier over 2,731 public files; its only public hits were the minimizer's git-ignored `instructor/scratch/probe.dfy`, cleared).

### 4. D92: H1 and H4 re-posed as refinements the learner writes (the user, 2026-10-25)

**Decision.** H1 and H4 become "write the engine": in Dafny the whole `module … refines RG_A2_StepMatcher`, in Verus the whole `impl StepMatcher for …`. The learner supplies the types and the definitions (each the given part of the same role) and the three law bodies, which call a given lemma or the item's own lemma. Two genuine items per language, so no exception; A2's interface byte-identical; only R08's files change.

**Shape (both languages, mirrored).**
- Each engine's parts are given in a plain module / free items over concrete types: Dafny `R08_RangeStarParts` (`StarState`, `InSomeRange`, `RangesClass`, `RangesLang`, `StarRes`, `StarStart`, `StarFeed`, `StarFinal`) and `R08_AltSetParts` (`Parts`, `AnyMatches`, `FeedAll`, `AnyNullable`, the opaque `AltRes`); Verus `range_lang`, `star_model`, `star_res`, `star_start_spec`, `star_feed_spec`, `star_final_spec`, `star_start`, `star_feed`, `star_is_final`, and `alt_res`, `parts_exec`, `alt_feed`, `alt_is_final`.
- **H1**: the lemma `RangesClassLaw` (its own module `R08_RangeStarClassFact`) / `lemma_ranges_set_law` is the hole form; after it, the learner region is the engine (`R08_RangeStarEngine refines …` / `impl StepMatcher for RangeStarEngine`) and its client, which ships commented under `Uncomment as you go:` (`MatchRanges` / `match_range_star`, promising `RangesLang` / `range_lang`).
- H2 and H3 move into the plain module `R08_AltSetLaws` (Verus: free fns as before); their `uses:` lose `refines`/`trait-spec` (they never needed them) and keep `reveal` on H3.
- **H4**: the lemma `AltFinalLaw` (module `R08_AltSetFinalFact`) / `lemma_alt_final_law` is the hole form; the learner region is the engine (`R08_AltSetEngine refines …` / `impl StepMatcher for AltSetEngine`) and its client (`MatchAlternatives` / `match_alt`). The start law reveals `AltRes` and calls H2, the step law calls H3, the final law calls the lemma (a refining lemma cannot recurse on the abstract-typed state: P3, chapter §3).
- Why the learner writes the whole module and not bodies in a shipped skeleton: a refining module that inherits a bodyless law is counted by vcheck as a hole at the interface's line (probe `r08/d92/p-ship.dfy`: 7 holes, 3 of them at `RG_A2_MatcherStatement.dfy:29/33/37`), and a Verus impl cannot ship partial. With the module absent the shipped files count 4 holes each, as before.
- Tags: `write_d = ["refines", "reveal"]`, `write_v = ["trait-spec", "reveal"]` unchanged and now honest: refines/trait-spec on H1 and H4, reveal on H3 and H4, per language.

**Probes** (`r08/d92`; one job at a time, 6G scope, memgate ≥20G; no exit 137/143):

| variant | Dafny | Verus |
|---|---|---|
| twin | verified, 58 verified | verified, 38 verified |
| engine region removed (client kept) | resolve: `module R08_RangeStarEngine does not exist` / `… R08_AltSetEngine …` | resolve: `the trait bound RangeStarEngine: StepMatcher is not satisfied` (and AltSetEngine) |
| `refines` dropped / inherent impl | resolve: `unresolved identifier: MatchWord` (both engines) | resolve: `inherent associated types are unstable` + the trait bound |
| each whole declaration of the engine removed (types, definitions, laws, `forall`/`assert forall` blocks) | every one fails: 11 + 10 variants (a removed law leaves the inherited one bodyless: 1 hole, refused by the gate) | every one fails: 17 + 15 variants |

**Smallest proofs found** (the greedy minimizer over both regions, structural lines kept; counted lines: calls, picks, reveals, asserts; bindings not counted):

| item | the lemma | the laws | in all | declarations (each needed) |
|---|---|---|---|---|
| H1d | 3 (call, two picks) | 3 (StartLaw's call, FeedLaw's two asserts) | 6 | 2 types, 5 definitions, 3 laws |
| H1v | 4 (call, two picks, one assert) | 4 (the call, `cw[0]`, two `assert forall` blocks) | 8 | 3 types, 6 spec fns, 3 exec fns, 3 laws |
| H4d | 3 (reveal, two calls) | 4 (reveal, three calls) | 7 | 2 types, 5 definitions, 3 laws |
| H4v | 4 (reveal, two calls, the `assert forall`) | 4 (reveal, three calls) | 8 | 3 types, 6 spec fns, 3 exec fns, 3 laws |

Every proper subset fails (minimizer, both orders of the line pass; the declaration test above). `reveal` is kept in H3 (both languages) and in both of H4's regions (both languages), so it stays genuine on two items per language.

**Tooling for the re-pose.**
- The engine region holds the client too: the region mode of the empty-body gate counts a resolve error as no verdict, so with a live client outside the region the blanked twin "errors"; inside the region, the blanked twin resolves and fails on the lemma, and the probes above show that the engine is needed. `firsttry.sh R08 --empty-body` 8/8.
- `scripts/reference_lint.py`: a twin-only declaration inside a `@hole-begin`/`@hole-end` region is allowed only when its item's admissible row says `writes = "module"` (the coordinator, 2026-10-25: narrowed from every region). R08.H1d/H4d/H1v/H4v carry it. `check_course_map.py` accepts `writes` as an optional key after `fallback`, only with the value "module" and only on an H item of Dafny or Verus. Without the key, each of the ~30 engine declarations would need its own `reference-only` marker. Tests:
  - `tests/wrappers/test_tools_static.py`: a twin-only declaration inside an ordinary region is still refused; one outside every region is still refused; one inside the region of a `writes = "module"` item is allowed.
  - `scripts/test_course_map.py`: another value, `writes` on a T item, and `writes` after `exception` are each refused.
- `--strict` already requires every commented check uncommented, so a finished file runs the clients, which pin each engine's `Lang`.

**Minutes.** H1 10 → 15 and H4 5 → 10 in each language (the refinement adds about five minutes of one-line declarations to each lemma); the refinement lab 30 → 10, because its "write the refinement you would like" half is now H1 and H4. R08 stays 354 minutes; hand holes 110 (55 per language). Registry, chapter §0 and PLAN §3/§10 updated.

**Not touched (reported).** Lab α's `bench/local/r/labalpha/r08-alt-final-law-d` and `r08-alt-feed-law-d` task files still hold the old given alternative-set engine, including its start law `reveal AltRes(); PartsLaw(p, w);`, which the learner now writes in H4. It is covered by the declared later-tier overlap; the Lab α lane decides whether to re-cut.

**Admission after D92 (2026-10-25).**
- Seeds 1–3 stable on the new core twins: Dafny's widest spread is 25.7 % (a declaration outside the files, advisory), Verus's 8.3 %. The agent twins are unchanged (§3).
- `firsttry.sh R08 --empty-body` 8/8: each hole's empty body fails, and each twin without its learner regions fails. `--lint-hollow` OK (22 files).
- `specfreeze --pin`: 282 statements; the engines the learner writes are not frozen, and their clients check `Lang`. `--check` gives 0.
- Counts re-pinned; `vcheck --shipped` 0: 4 holes per hand file, as before.
- `reference_lint` 0 over all 311 twins. `chapter_lint` 0: 30 pins, 6,507 words. `pins.py --ci --module R08` 47/47.
- Leak patterns: 8 OK over 2,731 public files. Rubric pins are refreshed, and the rubric's hole paragraph describes the refinements.
- Course map OK; avoid.sh OK.
- Study workflow 12/12 on a disposable clone of `b306db7a` plus this diff: first tries, strict, freeze, the check unit, then gate and audit for both units and both agents.
- Chapter: §4 and §6 are rewritten around the two refinements, with three new pins. `plain-d` shows that without `refines`, `MatchWord` does not resolve. `refining-d` shows the same declarations with `refines` verify. `noimpl-v` shows that without the impl, the trait bound fails. §0, §8 (lab, 10 minutes) and §10 are updated. The bank's reread titles, the K4 insight and PP2's diagnostic are updated.

**Focused author CI** (`scripts/ci.sh --author --job static --job harness --job wrappers --job rubric`, run `20261025T230157Z-2368857`, authoring @ `1f6e1497`, clean tree, 12G scope, `DVL_VERUS_JOBS=1`, 4,109 s):
- static PASS (899 s), rubric PASS, harness PASS (86 s).
- wrappers FAIL, on one test only. `tests/wrappers` ran 637 OK. In `tests/ci`, 89 of 90 passed; the 90th, `test_ci_tool.ArmedRoot.test_ci_never_reaches_a_study_run`, stopped at ci.sh's memory preflight ("30 GB available, 31 GB needed"), with host memory shared with DV7's CI. That is the environment, not a verdict.
- Rerun alone at 32 GB available, under the same 12G scope: OK (23 s).
