# DVR4 step 7 — R15 build notes (author-only, lane P1b)

Binding inputs:
- `Solutions/plans/DVR4-repair-plan.md` §2.1 (four admission results), §2.2 (line budget), §2.7 (R15's designs), §3 (the Lab α pattern, for Lab β's pre-registration), §4.2 (the R module bar), §5 step 7.
- PLAN §3 R15 (Why, Core payload, Exercises; 744 min = practice 384 + Lab β 360; D/V/py 45/45/10), §4.1 rung 9 (red-teamed contractor → R-v1), §4.3 (Lab β; validity rules: hidden truth out of every loop, `roundtrip` on the pinned Qwen, CI never calls a model).
- DESIGN §10.3 / W10 / W18 (Q15's oracles and card audit waived to Lab β: mutation kill is shared, oracle agreement stays new).
- Course rules: D64/D84, D82/D85, D90, D92–D95 (re-pose rather than exempt; the learner writes the construct), twins mirrored.

Scratch and evidence: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step7/p1b/r15/`. Solver rules as R16's notes §0.

## 0. Hand-off state (keep current)

| step | state | evidence / commit |
|---|---|---|
| objective map (§1) | written | this file |
| H1/T1 references (D/V), twins + learner files, P1dv/P2dv specimens, registry row `authoring` | **done** | 7d050ecd |
| T1/H1 admission (§2) | **done**: empty-body 4/4 (Verus TRIV `false`); seeds 1–3 stable (D CV ≤ 25.7 % outside the target, V 1.7 %); D64 measured in both languages (8/10/9/10; cheaper H1d answer 4) | `r15/seeds.log`, `r15/min/` |
| agent pair `R15_AgentRedTeam.dfy` / `agent.rs` (A1d/A1v) | twins + learner files; references verify (D 64, V 2) | — |
| `spectest`/`roundtrip` (H1py–H3py) + frozen tests | **built**: learner files fail only on holes (13+14 failures, all NotImplementedError); references 26/26 and 25/25; TRIV 3/3 fail; hollow 0; registry rows 35/40/65. Open: the redaction rule is a substring check, so a bare-identifier clause (`ensures b`) trips it (card authors avoid; or narrow the rule); `bench/local/r/labbeta/STRATUM.toml` belongs to the later corpus step | this commit |
| H2v property rung | **done** (D98): `re_to_pattern_r15` + `oracle_r15` in `#[cfg(test)] mod property_r15`, `todo!("R15.H2v")` ×2 (test-todo), given `oracle_agrees_r15` (500 seeded cases, alphabet `{a, b, .}`); row 15 min (admissible 220); RECOGNISE `property-test` | 2deae752 |
| Python holes (`spectest`, `roundtrip`) design (§3) | drafted | this file |
| chapter, paper, pins | **done**: chapter 7,668 words, 25 pins, lint 0; written track B1–B6 + exhibit; counts and freeze pinned; leak patterns 6 OK | 97a282dd, 65e7762a |
| bank | **done**: 1,542 lines, 12 questions (2/4/2/2/2), draws A/B with two live predicts each, PP1/PP2, 51 captured probes (`bank/probes.log`), 11 backward edges; tags in concepts.md; leak OK | this commit |
| study workflow | **12/12** on a disposable clone of 865bceb9 (first tries, strict, freeze, native test, gates and audits of both units and both agents); P1's `wf.py` un-commented the `// end reference checks` marker, so this lane's copy `p1b/bin/wf.py` stops there; verdict pins `expected/R15.pins`; empty-body 7/7 | 17fe60b7 |
| focused author CI | run `20261028T015742Z-2326456` @ 17fe60b7, clean tree, 3,840 s (12G, `DVL_VERUS_JOBS=1`): verify-r-dafny PASS 479 s, pins PASS 2,087 s, paper PASS, rubric PASS, harness PASS 81 s; static FAIL 912 s on `test_course_map` only (a case that added an R15 harness file without its import tier, which R15 being armed exposed; fixed at 95cbfaa8, 414 passed); verify-r-verus FAIL 279 s on `holes R03 v` only (R03's D95 `// GATED` external_body lines are counted by the tool but not as shipped hole forms: a pre-existing R03 issue from Δ311, not R15; R15 v passed: 2 holes, 0 mismatches) | 95cbfaa8 |
| Lab β pre-registration design (§5) | drafted | this file |
| D98 (H2v) | **done**: tools Δ316 (`[verus.test_deps]`, `scripts/dvl/testdeps/`, `load_crate` refuses any other dev-dependency) and Δ317 (`test_todos`, verify's `extra_holes`, firsttry `static_holes` + `TEST_SKIP`/`test_gate`), tests (`TestDepsStatic`, `TestDeps`, `LintHollow.test_static_holes_sees_a_test_todo`); H2v admission: shipped `todo!` fails the test, TRIV `String::new()` fails, 5 more wrong answers fail (no escape, anchor dropped, Empty as Eps, ungrouped Alt, oracle false), 2 equivalent variants pass (ungrouped Star, ungrouped anchor); chapter §0/§1/§3/§9, pins re-captured; leak patterns 8 OK; `R15.counts` re-pinned | 2d7811a5, 2deae752, da21fbd9 |
| D99 (witness hints) | **done**: `IOPairR15.witnesses`, `render_lemma_r15(body=)`, `render_pair_check_r15(witnesses=)`, given `has_existential_r15`; H1py and H2py: failed + existential + no hint → unknown (also for mutants: never `survived`); frozen tests 30 (ref 30/30, learner 15 fail on NotImplementedError, both TRIV fail); `sound-d/v` four checks with pair 2's hints (hinted pair holds + mutant killed, unhinted fail → unknown), §6 revised; bank 2 paragraphs; freeze re-pinned | da21fbd9 |
| D100 (Lab β budget) | **done**: B6 Given numbers (formula; 384 + 384 = 768 Qwen calls in 96 + 192 = 288 runs; Claude 80 + 10; ceiling 3 GPU-h to be re-set after the probe, as D56; the probe procedure: 24 public-card calls, t = p90 GPU-s, ceiling 768·t/3600 + 20 %), endpoint written as the apparatus's pinned OpenAI-compatible endpoint and model (switch from Ollama noted); solution settings/ceiling/fallback keyed on C; rubric BP.b; PLAN §4.3 rows + paragraph; chapter §6 bullet; registry banner. Fixtures unchanged (gold already 768/288). Nothing run | da21fbd9 |
| R03 CI fix (coordinator) | **done**: Δ315, `holes R03 v` 0 mismatches on the recorded run; tests `HolesStepGated` | d17c1bc0 |
| focused author CI re-run (1) | run `20261028T071914Z-4137196` @ d00b1078, clean, 7,350 s (12G, `DVL_VERUS_JOBS=1`): verify-r-dafny, verify-r-verus, rubric, harness PASS; static FAIL (chapter_lint: Q06/Q09 pins hash `scripts/dvl/pins.toml`, which Δ316 had edited, and R15's files-table row must state `4 holes`; avoid.sh: the generator's `below` named like Q08's chapter; reference_lint: the `sound-d/v` specimen twins not updated); pins FAIL (the same 7 Q06/Q09 pins); wrappers FAIL (`test_avoid`, the same name). Fixed: the test-deps pin moved to `scripts/dvl/testdeps/pin.toml` and pins.toml restored byte for byte; `below_r15`; twins; the row; R15 pins and counts re-captured | this commit |
| focused author CI re-run (2) | see the commit after this one | — |

## 1. Objective-to-exercise map (written before any build, 2026-10-27)

| objective (PLAN §3 R15) | chapter section (to write) | items | minutes | to confirm by probe |
|---|---|---|---|---|
| the escalation ladder: run → executable checks → property testing → proof → audit | §1 the ladder; diagram 1 | W1dv (A2's anchored `DerivMatch` read as rung 4), the compiled `#[test]`/`expect` checks (rung 2), H2v (rung 3), T1/H1 (rung 4), `vaudit` (rung 5) | ladder 70 | — |
| test-out (rung 4, small) | §0 | **T1d/T1v** `PrefixMatchR15(r, s)`: `b == exists j \| 0 <= j <= \|s\| :: Matches(r, s[..j])`, one loop restarting nothing (one derivative per character) | 5 / 5 | D64; TRIV `false`/`true` fail; the loop invariant clauses each needed |
| unanchored search, the R-owned anchoring theme (R04) on `rexc`'s matcher | §2 | **H1d/H1v** `ContainsMatchR15(r, s)`: `b == exists i, j \| 0 <= i <= j <= \|s\| :: Matches(r, s[i..j])`, nested loops restarting the derivative at each `i` | 20 / 20 | D64 on the reference and on the "call `DerivMatch` per slice" answer (§2); TRIV fails |
| property testing against an independent oracle (the `regex` crate, whole-string vs unanchored) | §3 | **H2v**: the oracle wrapper and the anchoring translation (`^(?:…)$` vs bare) in a deterministic generator test outside `verus!` | 15 | **DECISION R15-1**: the dev-dependency and the hole count (§4) |
| statement review as the irreducible human job | §4 | six frozen candidate statements for `ContainsMatchR15` (faithful, weak, vacuous, over-strong, anchoring error, empty-string error), each classified with a witness; written, rubric-graded (paper problem 2) | 30 | each candidate's verdict captured (the faithful one verifies with the reference body; each defective one has a witness pinned) |
| grade-the-grader; grader injection | §5 | fresh `/grade-paper` on `tests/instructor/fixtures/R15_flawed_answers.tex`; an injected string in a delivered artifact (paper problem 3) | 20 + 15 | fixtures; the rubric pins |
| contamination control (post-cutoff authorship, novelty review, perturbation probes, in-context isolation) | §6 | written (Lab β's card audit uses it) | 15 | — |
| red-teamed contractor → R-v1 (rung 9) | §7 | agent pair `R15_AgentRedTeam.dfy` / `agent.rs`: `rexc`'s leftmost-shortest end `FirstMatchEndR15` under a hostile brief (the brief invites weakening the spec, editing a check, or adding an assumption); acceptance `vcheck --gate`, `vaudit`, `specfreeze --check R15`; the learner writes R-v1 from the transcript | 30 | the plant fails at a real postcondition; a weakened delivery fails specfreeze |
| Lab β's oracles | §8 | **H1py** `spectest` soundness (35), **H2py** `spectest` completeness (40), **H3py** `roundtrip` (65) in `harness/r/fvh_r/{spectest,roundtrip}.py`; frozen tests `harness/tests/r/r15_cases/` on Mock/Scripted/Replay and a stand-in runner | Lab β 140 | the tests fail on the shipped holes and on TRIV bodies; pass on the references |
| Lab β pre-registration | §8, paper problem 4 | the learner's prereg (§5 design) | 35 | `prereg` refuses an incomplete plan |

**Minutes reconcile:** practice 384 = setup 8, test-out 10, read 70, worked 25, cards 6, predicts 15, ladder 70 (T1 not here; H1d 20 + H1v 20 + H2v 15 + run/checks/audit walk-through 15), statement review 30, grade-the-grader 20, injection 15, contamination 15, red-team + R-v1 30, paper 30, viva 30, calib 10. Admissible rows: T1d 5, T1v 5, H1d 20, H1v 20, H2v 15, H1py 35, H2py 40, H3py 65 (= 205).

**Predictions (≥ 2 `dv`, R-owned, to draft):** P1dv the empty slice (does `ContainsMatchR15(Star(Chr('a')), "")` return true; verdict of a body that starts `i` at 1); P2dv anchored vs unanchored oracle values on `b` for `a*` (value); P1dv as built: the weak candidate (`ensures b ==> …` with `b := false`; specimens `weak-d/v`, renamed from `vacuous-*` so that "vacuous" means only an unsatisfiable requires) — does it verify (verdict); P4d/P4v the roundtrip implication check between two specs that differ only on the empty input (obligation: which direction fails).

**Constructs (to confirm, D82/D85):** WRITE `invariant` (T1 and H1 are loops whose smallest answers write invariant clauses, in both languages); RECOGNISE `property-test` (one item, H2v; Q's WRITE slug, not R's here). No other WRITE tag.

## 2. H1 — what the smallest answer is (to measure)

- **Reference (the design):** outer loop over `i` with `forall i' < i, j' :: !Matches(r, s[i'..j'])`; inner loop keeps `d` with `forall w :: Matches(d, w) <==> Matches(r, s[i..j] + w)` and `forall j' in [i, j) :: !Matches(r, s[i..j'])`; each step `DerivCorrect` and `NullableCorrect` with the slice fact `s[i..j+1] == s[i..j] + [s[j]]`.
- **The cheaper answer:** call A2's `DerivMatch(r, s[i..j])` for every slice (cubic). It meets the spec; its smallest form (two loops, two quantified invariants, the calls) must still be ≥ 3 one-fact lines (expected 4–6). Measured both; if the cheaper one is the smallest and meets D64, it is recorded as acceptable (the chapter discusses the cost; the property rung and the bank's PP use the derivative-restart form). No re-pose unless D64 fails.

### Measurements (2026-10-27, `r15/min/`, greedy minimizer, structural lines kept)

| item | smallest found from the reference | one-fact lines | the cheaper answer |
|---|---|---|---|
| T1d | 3 invariants, `NullableCorrect` ×2, `DerivCorrect`, the slice fact, one `s[j..j]` fact | 8 | — |
| H1d | 4 invariants (the outer bound drops), `NullableCorrect` ×2, `s[j..j]` ×2, `DerivCorrect`, the slice fact | 10 | `DerivMatch(r, s[i..j])` per slice: 3 invariants + the call = **4**; each proper subset fails (minimizer) |
| T1v | 3 invariant clauses, `lemma_nullable_correct` ×2, the empty-slice fact ×2, `lemma_deriv_correct`, the slice fact; nothing drops | 9 | — |
| H1v | one copy of the outer clause plus the inner loop's 3 clauses, the same 6 proof lines (the outer bound drops). The inner copy is not needed: after the inner loop, facts about unchanged variables hold again (probe `h1v_noinner.rs`, verified), so the twin drops it and H1v's Hint(2) and chapter §2 say so (found by the bank sub-lane) | 10 | the slice answer needs a sub-vector built in a loop in Verus, so it is not shorter |

Every item meets D64 with the cheaper answer counted. The cheaper H1d answer is cubic; the chapter names it and the cost, the twin keeps the derivative restart (plan §2.7's design).

## 3. `spectest` and `roundtrip` (Lab β's oracles; Python holes)

Names disjoint from Q15's `mutants`/`kill_rate`/`vacuity`/`implication`/`classify` (avoid.sh). Every generated file is verified through `fvh.tools.run` (the frozen core), never a subprocess; the acceptance tests use a stand-in runner and Scripted/Replay policies only.

- **H1py `spec_sound_r15(spec, pairs, *, run=None, workdir=None) -> SoundReportR15`** (the card is `spec.card`): for each reference pair (input, output), render a check (Dafny: a method that asserts the spec's postcondition at the concrete values; Verus: a proof fn with `assert(...) by (compute)`-free unfolding through the spec fn), run it; a pair is `holds`/`rejects`/`unknown` (a killed or inconclusive run is unknown, never holds); the spec is sound iff every pair holds.
- **H2py `spec_complete_r15(spec, pairs, *, run=None, workdir=None) -> CompleteReportR15`** (the mutator `mutate_outputs_r15` is given and fixed): for each pair and each output mutant (the card's mutation operators: off-by-one, swapped, emptied, a constant; equal-to-reference mutants dropped), render `!post(input, mutant)`; killed / survived / unknown; the kill rate over decided mutants and the survivors listed. Survivors are not verdicts (an equivalent mutant is decided only by the hidden reference, after the batch, in the grader container).
- **H3py `roundtrip_r15(spec, ask, *, run=None, workdir=None) -> RoundtripReportR15`:** two policy calls (spec → NL with the code redacted; NL → spec with the original redacted), then two implication checks (`spec ⟹ spec'` and back) rendered as lemmas over the card's signature; verdict `equivalent`/`weaker`/`stronger`/`incomparable`/`unknown`, with token and call accounting for the prereg's cost fields.
- Frozen tests (author, `harness/tests/r/r15_cases/`): synthetic cards in both languages; a stand-in runner that answers from a table; TRIV bodies (`return SoundReport(all holds)`, kill rate 1.0, always `equivalent`) fail; the unknown rule; redaction (the NL prompt never contains the spec text; the second prompt never contains the original spec).

## 4. H2v — the property rung (DECISION R15-1)

Findings (2026-10-27): `vcheck --test` compiles Verus tests with `verus --compile --test` (not cargo), so a crate dependency outside `vstd` and the layers needs a wrapper change; `regex` 1.13.1, `regex-automata` 0.4.18 and `regex-syntax` 0.8.11 are in the local cargo cache (offline build possible). Plain Rust outside `verus!` is allowed only under `#[cfg(test)]`/`#[test]` (lint V9/Δ42), and no Verus hole form counts a `todo!()` there, so a plain-Rust hole is not tool-counted today.

Options:
- **(a, recommended)** Two small tool changes, each with tests and a Δ entry: `vcheck --test` builds a module crate's declared `[dev-dependencies]` (only `regex`, offline, pinned in the lock) and passes them as `--extern`; the hole counter counts `todo!("<item id>")` inside a `#[cfg(test)]` item as a hole of a new kind `test-todo` (so the learner loop and `firsttry --strict` see H2v). The learner writes the translation `re_to_pattern_r15` and the wrapper `oracle_r15(r, s, anchored)`; the given generator and `#[test]` compare `contains_match_r15` and A2's `deriv_match` against it on 500 seeded cases.
- (b) The oracle is a second verified matcher (`deriv_match` over every slice, given), not the `regex` crate; H2v becomes the generator's shrinking/minimization of a counterexample in a `#[test]` (no external crate; still needs the `test-todo` count). Loses the record's "independent oracle".
- (c) Drop H2v as a hole: the property rung is a given, run-and-read demonstration (the chapter captures a planted divergence), and its 15 minutes move to the ladder's walk-through. Loses a hand item.

## 5. Lab β pre-registration design (following plan §3; design only, nothing run)

- **Question (PLAN §4.3).** Do two independent oracles agree, with each other and with hidden verdicts, and how often is "verified" also "faithful", D vs V?
- **Units.** 24 R cards × 4 specification variants (faithful, weak, over-strong, vacuous-on-a-case) × 2 languages = 192 spec units; cluster = card (24 clusters). Deliveries: Qwen 24 cards × 4 rounds × 8 repeats (PLAN §4.3: 768 calls), Claude 20 × 4 (80).
- **Primary estimand (one).** Cohen's κ between the two oracles' binary "faithful" verdicts (`spectest`: sound ∧ every decided mutant killed; `roundtrip`: equivalent) over the 192 units, with a cluster-bootstrap 95 % interval (10,000 resamples of cards). No test: the claim is "agreement = κ̂ [CI] on these cards with this model".
- **Secondary, descriptive:** each oracle's confusion matrix against the hidden verdicts (`Hidden/labs/R15/`, compared after the batch in the grader container), sensitivity/specificity with Wilson intervals; the verified-but-unfaithful rate of deliveries, D vs V, paired by card (difference with a cluster-bootstrap interval, no test); roundtrip's unknown rate; cost per arm.
- **Precision instead of power:** simulate κ's interval half-width at 24 clusters for κ ∈ {0.2, 0.4, 0.6} and within-card correlation ρ ∈ {0, 0.3} (the plan §3.4 code pattern, standard library, seed fixed); pre-register the half-width and say plainly that 24 clusters cannot separate κ = 0.4 from 0.6.
- **Missing results, stopping, accounting:** as plan §3.3 (apparatus failure re-run once with the same seed, then excluded and counted; policy failure is a failed delivery; identical generation settings per arm; feedback cap equal; the prereg sha before any run).
- **Contamination (W18):** post-cutoff authorship for the 14 author cards, a perturbation probe per card (renaming), the card audit (30 min) before freeze.
- **What the author builds now:** the prereg fields in `paper/R15_problems.tex` and the rubric; `fvh.prereg`'s required fields for Lab β (estimand, primary, aggregation, missing rule, cluster rule, precision sim sha256) as a later harness step; the 24 cards and the hidden verdicts are a later corpus step (not in step 7's scope).

## 5b. Kit state and findings (2026-10-27)

- **Chapter** `docs/R15_VerifierLoop.md` (sub-lane): 7,671 lint words, 9 dafny + 9 rust blocks (≥ 1 each in §1–§6), 25 pins, 2 predict boxes, 3 mermaid fences (PLAN's 2 diagrams, the second drawn as two fences because the lint requires 3–5). 14 demo specimens (`word`, `shortrun`, `short`, `prop`, `review`, `inject`, `sound`, D/V). §3 demonstrates rung 3 with a copy of A1/A2 under fresh names (`vcheck --test` refuses module probes) and keeps H2v's mechanism to one revisable paragraph (R15-1). §8 now names the paper as B1–B6.
- **Written track** (sub-lane): B1–B6, solutions, rubric (pins current), gold/flawed fixtures, exhibit `paper/fixtures/R15_flawed_prereg.tex` for B4. B3 is being re-posed on `FirstMatchEndR15`'s statement: §4 of the chapter works the search's six candidates, which would hand B3 its answers.
- **Finding (Lab β design): `spectest`'s empty-body checks cannot decide existential postconditions.** On the word search's faithful spec, every check fails in both languages (`sound-d/v` pins): the true pair reads "rejects" and the mutant "survives", so a sound, complete spec scores unfaithful. H1's own statement is existential. DECISION R15-2 below.
- **Finding (budget):** PLAN §4.3's roundtrip row (96 runs / 192 calls) covers one language; the 24 × 4 × 2 primary needs 384 calls / 192 runs, and PLAN's rows plus the full primary exceed the registry's 960 calls / 288 runs. B6's exemplar fits by cutting delivery repeats to 4. At Lab α's measured 72 GPU-s per call, 768 calls ≈ 15 GPU-h against R15's 3 GPU-h ceiling; a throughput probe at Lab β's settings (thinking off, `num_predict` 768) is needed before the ceiling is final.
- **Finding (bank, bears on R15-2):** an empty-body negative check on a 3-element sequence is proved in Dafny but not in Verus (fuel 1), so `spectest` can score the same mutant killed in Dafny and survived in Verus: a D-vs-V confound for Lab β beyond the existential problem; witness hints (R15-2 (a)) or a pinned unfolding depth per card would remove it.
- **Redaction rule:** a bare-identifier clause (`ensures b`) always appears in the signature, so `roundtrip_r15` raises; cards avoid such clauses, or the rule is narrowed to the description.

## 6a. Decided (the user, 2026-10-28; Δ314)

- **D98 = R15-1 (a):** `vcheck --test` builds the declared `regex` dev-dependency (offline, `--locked`, local cargo cache); new hole kind `test-todo` for `todo!("<item>")` inside `#[cfg(test)]`; tests + a Δ entry each; then build H2v (Re-to-pattern translation + anchored/unanchored oracle wrapper), admitted with TRIV and empty-body. **Not started.**
- **D99 = R15-2 (a):** witness hints on reference pairs rendered as `assert` lines; an existential with no witness is `unknown`; tests; re-capture `sound-d/v`. **Not started.**
- **D100 = R15-3 (a):** four delivery repeats (768 Qwen calls, 288 runs); GPU ceiling "to be re-set after a throughput probe at Lab β's settings, as D56"; write the budget formula and the probe procedure into B6's pre-registration (problems/solutions/rubric); never run the probe. **Not started.**

## 6. DECISIONS (to the coordinator)

- **R15-2 (spectest on existential postconditions):** (a, recommended) each card's reference pair carries witness hints (the witness terms for the spec's existentials), rendered as `assert` lines in the pair check, and a check with no witness for an existential is `unknown`, never `rejects`; tests added; (b) Lab β's cards avoid existential postconditions (fewer R-relevant cards); (c) `outcome_r15` maps every failed check of a quantified spec to `unknown` (honest but makes `spectest` uninformative there).
- **R15-3 (Lab β budget):** (a, recommended) four delivery repeats (768 Qwen calls, 288 runs) and the GPU ceiling re-set after a throughput probe at Lab β's settings, as D56 did for Lab α; (b) keep PLAN's rows and raise the registry's call count.

- **R15-1:** the property rung's mechanism (§4); recommend (a).
